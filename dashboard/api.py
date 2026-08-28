from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from fastapi.middleware.cors import CORSMiddleware
from database.db_manager import (
    init_db,
    get_pending_intercepts,
    open_pool,
    close_pool,
    get_dashboard_status,
    toggle_status,
    save_modified_request,
    release_intercepted_request

)

# در dashboard/api.py
class PacketNotifyPayload(BaseModel):
    id: int
    time: str
    method: str
    path: str
    http_version: Optional[str] = "HTTP/1.1"
    query_params: Optional[Dict[str, Any]] = {}
    target_host: Optional[str] = ""
    target_port: Optional[int] = 80
    headers: Optional[Dict[str, Any]] = {}
    body: Optional[str] = ""
    status: int
    risk: str
    security_details: Optional[Dict[str, Any]] = {}

class InterceptActionPayload(BaseModel):
    request_id: int
    action: str
    modified_data: dict = None


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
status_manager = ConnectionManager()
packet_manager = ConnectionManager()

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#websocket endpoint->
@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await status_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        status_manager.disconnect(websocket)

@app.websocket("/ws/packets")
async def packets_ws(websocket: WebSocket):
    await packet_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        packet_manager.disconnect(websocket)

async def notify_new_packet(packet_data: dict):
    await packet_manager.broadcast(packet_data)

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
async def internal_notify_packet(packet: PacketNotifyPayload):
    pending_intercepts = await get_pending_intercepts()
    count = len(pending_intercepts)
    await packet_manager.broadcast({
        "type": "new_packet",
        "packet": packet.model_dump()
    })

    await status_manager.broadcast({
        "pending_intercepts": count
    })
    return {"status": "ok", "pending_intercepts": count}


from database.db_manager import get_request_by_id
import json


@app.get("/api/v1/requests/{request_id}")
async def get_request_details(request_id: int):
    req = await get_request_by_id(request_id)
    if not req:
        return {"error": "Request not found"}

    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}

    security_details = req.get("security_details", {})
    if isinstance(security_details, str):
        try:
            security_details = json.loads(security_details)
        except Exception:
            security_details = {}

    return {
        "id": req["id"],
        "method": req["method"],
        "path": req["path"],
        "http_version": req.get("http_version", "HTTP/1.1"),
        "target_host": req.get("target_host", ""),
        "target_port": req.get("target_port", 80),
        "query_params": req.get("query_params", {}),
        "headers": headers,
        "body": req.get("body", ""),
        "risk": req.get("risk", "Low"),  
        "security_details": security_details
    }


@app.post("/api/v1/intercept/release")
async def release_intercept(payload: InterceptActionPayload):
    request_id = payload.request_id
    action = payload.action

    if action == "modified" and payload.modified_data:
        mod_data = payload.modified_data
        headers = mod_data.get("headers", {})
        body = mod_data.get("body", "")

        method = mod_data.get("method", "POST")
        path = mod_data.get("path", "/")

        host = headers.get("host") or headers.get("Host") or "localhost"

        raw_http = f"{method} {path} HTTP/1.1\r\n"
        for k, v in headers.items():
            if k.lower() not in ['host', 'content-length']:
                raw_http += f"{k}: {v}\r\n"

        raw_http += f"Host: {host}\r\n"

        if body:
            body_bytes = body.encode('utf-8')
            raw_http += f"Content-Length: {len(body_bytes)}\r\n"
        else:
            body_bytes = b""

        raw_http += "\r\n"

        raw_bytes = raw_http.encode('utf-8') + body_bytes

        await save_modified_request(
            request_id=request_id,
            method=method,
            path=path,
            headers=headers,
            raw_bytes=raw_bytes
        )
    success = await release_intercepted_request(request_id, "forwarded" if action == "modified" else action)

    if success:
        return {"status": "ok", "message": f"Request {request_id} {action}"}
    return {"status": "error", "message": "Failed to release request"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "name_of_project": "Dashboard",
    }



