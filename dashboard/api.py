from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from webview import *
from database.db_manager import (
    init_db,
    get_pending_intercepts,
    open_pool,
    close_pool,
    get_dashboard_status,
    toggle_status
)

#websocket management->
from contextlib import asynccontextmanager

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass
manager = ConnectionManager()

#pydentic schemas->
class InterceptItem(BaseModel):
    queue_id: int
    request_id: int
    method: str
    host: str
    port: int
    path: str
    headers: dict[str, Any] | str
    raw_bytes: str | None = None

    model_config = ConfigDict(from_attributes=True)

class InterceptActionRequest(BaseModel):
    action: str
    modified_method: Optional[str] = None
    modified_path: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    await init_db()
    yield
    await close_pool()

app = FastAPI(title="Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # یا ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#websocket endpoint->
@app.websocket("/ws/packets")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def notify_new_packet(packet_data: dict):
    await manager.broadcast(packet_data)
#headerBar endpoints:
@app.get("/api/v1/system/status")
async def system_status():
    pending_intercepts = await get_pending_intercepts()
    return {
        "status": await get_dashboard_status(),
        "pending_intercepts": len(pending_intercepts),
    }

@app.post("/api/v1/system/toggle-pause")
async def toggle_system_pause():
    new_is_paused = await toggle_status()
    return {
        "status": new_is_paused,
        "message": "Pause Capture" if new_is_paused else "Resume Capture",
    }


@app.post("/api/v1/internal/notify-packet")
async def internal_notify_packet():
    pending_intercepts = await get_pending_intercepts()
    count = len(pending_intercepts)

    await manager.broadcast({
        "pending_intercepts": count
    })
    return {"status": "ok", "pending_intercepts": count}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "name_of_project": "Dashboard",
    }



