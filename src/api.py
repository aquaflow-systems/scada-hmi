import asyncio
import contextlib
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from src.modbus_poller import STAGE_ENDPOINTS, ModbusPoller

BROADCAST_SECONDS = 1.0
STATIC_DIR = Path(__file__).parent / "static"
CERTS_DIR = "/certs"

poller = ModbusPoller(certs_dir=CERTS_DIR)
connected_clients: set[WebSocket] = set()


async def broadcast_loop() -> None:
    while True:
        if connected_clients:
            state = poller.read_all()
            dead = []
            for ws in connected_clients:
                try:
                    await ws.send_json(state)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                connected_clients.discard(ws)
        await asyncio.sleep(BROADCAST_SECONDS)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    poller.start()
    task = asyncio.create_task(broadcast_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="scada-hmi", lifespan=lifespan)


@app.get("/state")
def get_all_state() -> dict:
    return poller.read_all()


@app.get("/state/{stage}")
def get_stage_state(stage: str) -> dict:
    if stage not in STAGE_ENDPOINTS:
        raise HTTPException(status_code=404, detail=f"unknown stage '{stage}'")
    return poller.read_all().get(stage, {})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_json(poller.read_all())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
