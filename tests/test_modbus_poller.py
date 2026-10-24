from unittest.mock import MagicMock

from src.modbus_poller import ModbusPoller


class FakeResult:
    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):
        return self._error


def test_poll_stage_updates_state_on_success():
    fake_client = MagicMock()
    fake_client.connected = True
    fake_client.read_holding_registers.return_value = FakeResult([742, 953, 60, 700, 1])

    poller = ModbusPoller(clients={"dosing": fake_client})
    poller._poll_stage("dosing")

    assert poller.state["dosing"]["ph_value"] == 7.42
    assert poller.state["dosing"]["pump_state"] is True


def test_poll_stage_keeps_previous_state_on_error():
    fake_client = MagicMock()
    fake_client.connected = True
    fake_client.read_holding_registers.return_value = FakeResult(error=True)

    poller = ModbusPoller(clients={"dosing": fake_client})
    poller.state["dosing"] = {"ph_value": 7.0}

    poller._poll_stage("dosing")

    assert poller.state["dosing"] == {"ph_value": 7.0}


def test_poll_stage_handles_exception_gracefully():
    fake_client = MagicMock()
    fake_client.connected = True
    fake_client.read_holding_registers.side_effect = RuntimeError("boom")

    poller = ModbusPoller(clients={"dosing": fake_client})
    poller.state["dosing"] = {"ph_value": 7.0}

    poller._poll_stage("dosing")

    assert poller.state["dosing"] == {"ph_value": 7.0}


def test_poll_stage_ignores_unknown_stage():
    poller = ModbusPoller(clients={})
    poller._poll_stage("not-a-stage")
