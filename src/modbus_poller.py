import logging
import threading
import time
from pathlib import Path

from plc_fleet.registers import decode_registers, register_count
from pymodbus.client import ModbusTcpClient, ModbusTlsClient

logger = logging.getLogger(__name__)

POLL_SECONDS = 1.0

STAGE_ENDPOINTS = {
    "raw_water": {"host": "plc-raw-water", "port": 502, "use_tls": True},
    "dosing": {"host": "plc-dosing", "port": 502, "use_tls": False},
    "filtration": {"host": "plc-filtration", "port": 502, "use_tls": True},
    "disinfection": {"host": "plc-disinfection", "port": 502, "use_tls": True},
    "distribution": {"host": "plc-distribution", "port": 502, "use_tls": True},
}


def make_client(endpoint: dict, certs_dir: str | None):
    if endpoint["use_tls"]:
        certs_path = Path(certs_dir)
        return ModbusTlsClient(
            host=endpoint["host"],
            port=endpoint["port"],
            certfile=str(certs_path / "ca.crt"),
            server_hostname=endpoint["host"],
        )
    return ModbusTcpClient(host=endpoint["host"], port=endpoint["port"])


class ModbusPoller:
    def __init__(self, certs_dir: str | None = None, clients: dict | None = None):
        self.certs_dir = certs_dir
        self._clients = (
            clients
            if clients is not None
            else {
                stage: make_client(endpoint, certs_dir)
                for stage, endpoint in STAGE_ENDPOINTS.items()
            }
        )
        self.state: dict[str, dict] = {stage: {} for stage in STAGE_ENDPOINTS}
        self._stop_event = threading.Event()

    def _poll_stage(self, stage: str) -> None:
        client = self._clients.get(stage)
        if client is None:
            return
        try:
            if not client.connected:
                client.connect()

            count = register_count(stage)
            result = client.read_holding_registers(address=0, count=count, slave=1)

            if result.isError():
                logger.warning("error reading registers for stage %s", stage)
                return

            self.state[stage] = decode_registers(stage, result.registers)
        except Exception:
            logger.exception("failed to poll stage %s", stage)

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            for stage in self._clients:
                self._poll_stage(stage)
            time.sleep(POLL_SECONDS)

    def start(self) -> None:
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()

    def read_all(self) -> dict:
        return self.state
