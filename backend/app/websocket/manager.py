import socketio
from fastapi import WebSocket


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


class TelemetryManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}

    async def connect(self, order_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(order_id, set()).add(websocket)

    def disconnect(self, order_id: str, websocket: WebSocket) -> None:
        if order_id in self.connections:
            self.connections[order_id].discard(websocket)

    async def broadcast(self, order_id: int | str, payload: dict) -> None:
        key = str(order_id)
        for websocket in list(self.connections.get(key, set())):
            await websocket.send_json(payload)
        await sio.emit("telemetry", payload, room=f"order:{key}")
        await sio.emit("operations", payload)


telemetry_manager = TelemetryManager()


@sio.event
async def connect(sid, environ, auth):
    await sio.emit("connected", {"ok": True}, to=sid)


@sio.event
async def subscribe(sid, data):
    order_id = str(data.get("order_id", "operations"))
    await sio.enter_room(sid, f"order:{order_id}")
