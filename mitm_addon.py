# mitm_addon.py
import asyncio
import time
import json
import urllib.request
import logging
from mitmproxy import http, ctx
from pathlib import Path

import inspector_tools
from database.db_manager import (
    init_db, open_pool, close_pool,
    save_raw_requests, create_intercept_entry,
    wait_for_user_action, get_modified_request_bytes,
    get_dashboard_status
)
from inspector_tools import HTTPRequest
from inspector_tools.model_loader import ModelLoader
from inspector_tools.ml_analysis.analyzer import SecurityAnalyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("LLMinspector")

RISK_SCORE_THRESHOLD = 0.5


class LLMInspectorAddon:
    def __init__(self):
        model_dir_path = Path(__file__).parent / "models"
        self.model_loader = ModelLoader(model_dir_path)
        self.model_loader.load_models()

    async def running(self):
        logger.info("🚀 LLMinspector MITM Engine is running on port 8080...")
        try:
            await open_pool()
            await init_db()
            logger.info("🔌 Database connected for MITM Addon.")
        except Exception as e:
            logger.error(f"Database connection error in MITM: {e}")

    async def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.method == "CONNECT":
            return

        raw_headers = "\r\n".join(f"{k}: {v}" for k, v in flow.request.headers.items())
        fake_raw_msg = f"{flow.request.method} {flow.request.path} {flow.request.http_version}\r\n{raw_headers}\r\n\r\n{flow.request.text or ''}"
        req = HTTPRequest(fake_raw_msg)


        security_analyzer = SecurityAnalyzer(self.model_loader)
        security_context = security_analyzer.analyze(req)

        is_secure = security_context.risk_score < RISK_SCORE_THRESHOLD
        sec_info_dict = {
            "risk_score": getattr(security_context, "risk_score", 0.0),
            "matched_patterns": getattr(security_context, "matched_patterns", []),
            "flags": getattr(security_context, "flags", {}),
        }

        logging_obj = inspector_tools.logger.JSONLogger("requests_log.json")
        logging_obj.log_request(req)

        is_paused = await get_dashboard_status()
        if is_paused:
            logger.info("⚡ [BYPASS] Proxy is PAUSED. Forwarding without intercepting.")
            return

        request_id = await save_raw_requests(req, raw_bytes=fake_raw_msg.encode("utf-8"))
        logger.info(f"💾 [DB] Saved raw request with ID: {request_id}")

        queue_id = await create_intercept_entry(request_id)
        logger.info(f"⏸️ [INTERCEPT] Request #{request_id} queued. Holding task...")


        try:
            risk_level = "High" if not is_secure else "Low"
            notify_payload = {
                "id": request_id,
                "time": time.strftime("%H:%M:%S"),
                "method": req.method,
                "path": req.path,
                "http_version": req.http_version,
                "query_params": req.query_params,
                "target_host": req.target_host,
                "target_port": req.target_port,
                "headers": dict(req.headers),
                "body": req.body,
                "status": 200,
                "risk": risk_level,
                "security_details": sec_info_dict,
            }
            def send_notify():
                url = "http://dashboard_api:8000/api/v1/internal/notify-packet"
                body = json.dumps(notify_payload).encode("utf-8")
                req_api = urllib.request.Request(
                    url, data=body, method="POST", headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req_api, timeout=2.0) as resp:
                    pass

            await asyncio.to_thread(send_notify)
        except Exception as notify_err:
            logger.error(f"[!] Failed to notify dashboard_api: {notify_err}")

        action = await wait_for_user_action(request_id, timeout=300.0)
        logger.info(f"🟢 [INTERCEPT] Task unblocked for Request #{request_id}. Action: '{action}'")

        if action == "dropped":
            logger.info(f"🚫 [DROPPED] Request #{request_id} was dropped by user.")
            flow.response = http.Response.make(
                403, b"Request dropped by Interceptor.", {"Content-Type": "text/plain"}
            )
            return

        modified_bytes = await get_modified_request_bytes(request_id)
        if modified_bytes:
            logger.info(f"✏️ [MODIFIED] Applying user modifications to Request #{request_id}")
            modified_req = HTTPRequest(modified_bytes.decode("utf-8", errors="replace"))

            if modified_req.body:
                flow.request.text = modified_req.body


addons = [
    LLMInspectorAddon()
]