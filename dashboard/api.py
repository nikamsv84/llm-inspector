from fastapi import  FastAPI
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict
from webview import *
from database.db_manager import (
    init_db,
    get_pending_intercepts,
    open_pool,
    close_pool,
)
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


app = FastAPI(title="Dashboard")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "name_of_project": "Dashboard",
    }

@app.get("/api/v1/stats")
def summery_of_packets():
    open_pool()
    init_db()
    pending_intercepts = get_pending_intercepts()
    num_pending_intercepts = len(pending_intercepts)
    return {
        "pending_intercepts": num_pending_intercepts,
    }

