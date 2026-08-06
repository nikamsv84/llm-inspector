import asyncio
import functools
import logging
import time
from typing import Any, Callable
import urllib.request
import json
from dashboard.api import notify_new_packet

# Import async database helper functions
from database.db_manager import (
    close_pool,
    create_intercept_entry,
    get_dashboard_status, 
    get_modified_request_bytes,
    init_db,
    open_pool,
    release_intercepted_request,
    save_raw_requests,
    wait_for_user_action,
    get_pending_intercepts
)
from inspector_tools import HTTPRequest, JSONLogger, Security_Analyzer

PORT = 8080
FORMAT = "utf-8"
SERVER_IP = "0.0.0.0"
RED = "\033[91m"
RESET = "\033[0m"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

file_logger = JSONLogger("requests_log.json")
security_analyze = Security_Analyzer()


async def auto_release_tester(
        req_id: int, action: str = "forwarded", delay_seconds: float = 3.0
) -> None:
    """
    Simulates user action on the dashboard after a specified delay using asyncio.
    """
    await asyncio.sleep(delay_seconds)
    print(
        f"\n[TEST SIMULATOR] Simulating user action on Request #{req_id} ->"
        f" Action: '{action}'"
    )
    released = await release_intercepted_request(req_id, action)
    print(f"[TEST SIMULATOR] Signal delivered to event registry: {released}\n")


def track_uptime(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        writer: asyncio.StreamWriter = args[1] if len(args) > 1 else kwargs.get("writer")
        client_id: int = args[2] if len(args) > 2 else kwargs.get("client_id", 0)

        addr = writer.get_extra_info("peername") if writer else ("Unknown", 0)
        start_time = time.time()

        try:
            return await func(*args, **kwargs)
        finally:
            uptime = time.time() - start_time
            print(
                f"[UPTIME] Client {client_id} [Port: {addr[1]}] disconnected."
                f" Active for: {uptime:.2f}s\n"
            )

    return wrapper


@track_uptime
async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_id: int
) -> None:
    addr = writer.get_extra_info("peername")
    print(f"\n[NEW CONNECTION] Client {client_id} connected from port: {addr[1]}")

    try:
        raw_bytes = b""

        # Read HTTP headers asynchronously
        while b"\r\n\r\n" not in raw_bytes:
            try:
                # Read with a timeout of 3 seconds for header completion
                chunk = await asyncio.wait_for(reader.read(4096), timeout=3.0)
            except asyncio.TimeoutError:
                break

            if not chunk:
                break
            raw_bytes += chunk

            if len(raw_bytes) > 8192:
                print(f"[!] Client {client_id} sent abnormally large headers.")
                writer.write(
                    b"HTTP/1.1 431 Request Header Fields Too Large\r\n\r\nHeaders exceeded maximum allowed size."
                )
                await writer.drain()
                return

        if not raw_bytes:
            return

        message = raw_bytes.decode(FORMAT, errors="replace")
        req = HTTPRequest(message)

        print("=" * 50)
        print("=" * 50)
        print(f"[MINI-BURP INSPECTOR - CLIENT {client_id}]")
        print(f"    ▶ Method:       {req.method}")
        print(f"    ▶ Path:         {req.path}")
        print(f"    ▶ Target:       {req.target_host}:{req.target_port}")
        print(f"    ▶ Cookie:       {req.cookies}")
        print(f"    ▶ Query Params: {req.query_params}")

        print(f"    ▶ All Headers:  {dict(req.headers)}")

        if req.body:
            print(f"    ▶ Body Data:    {req.body}")
        print("=" * 50)

        file_logger.log_request(req)
        security_result = security_analyze.analyze(req)

        if not security_result["is_secure"]:
            clean_patterns = ", ".join(security_result["matched_patterns"])
            print(f"{RED}[🚨 SECURITY ALERT] Malicious Request Detected!{RESET}")
            print(f"{RED}    ▶ Attack Type:      {security_result['attack_type']}{RESET}")
            print(f"{RED}    ▶ Matched Patterns: {clean_patterns}{RESET}")
            print(f"{RED}" + "=" * 50 + f"{RESET}")


        # Check Dashboard Pause Status (Bypass Logic)
        is_paused = await get_dashboard_status()
        request_id = None

        if is_paused:
            print(f"⚡ [BYPASS] Proxy is PAUSED. Bypassing intercept queue for Client {client_id}.")
        else:
            # 1. Save raw request to database asynchronously
            request_id = await save_raw_requests(req, raw_bytes=raw_bytes)
            print(f"💾 [DB] Saved raw request with ID: {request_id}")

            # 2. Insert entry into intercept queue asynchronously
            queue_id = await create_intercept_entry(request_id)
            print(
                f"⏸️ [INTERCEPT] Request #{request_id} queued (Queue ID: {queue_id})."
                " Holding task..."
            )
            try:
                risk_level = "High" if not security_result["is_secure"] else "Low"

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
                print(f"[!] Failed to notify dashboard_api: {notify_err}")

            # 3. Non-blocking wait for user action (up to 5 mins)
            action = await wait_for_user_action(request_id, timeout=300.0)
            print(
                f"🟢 [INTERCEPT] Task unblocked for Request #{request_id}. Action: '{action}'"
            )

            # 4. Handle dropped request
            if action == "dropped":
                print(
                    f"🚫 [DROPPED] Request #{request_id} was dropped by user."
                    " Closing socket."
                )
                writer.write(
                    b"HTTP/1.1 403 Forbidden\r\n\r\nRequest dropped by Interceptor."
                )
                await writer.drain()
                return

        modified_bytes = None
        if request_id is not None:
            modified_bytes = await get_modified_request_bytes(request_id)

        if modified_bytes:
            payload_to_send = modified_bytes
            modified_req = HTTPRequest(modified_bytes.decode(FORMAT, errors="replace"))
            target = (modified_req.target_host, modified_req.target_port)
        else:
            payload_to_send = raw_bytes
            target = (req.target_host, req.target_port)

        # Prevent infinite loop back to our own proxy
        if target in [(SERVER_IP, PORT), ("127.0.0.1", PORT), ("localhost", PORT)]:
            print(f"[!] Blocked an infinite loop request to ourselves: {target}")
            writer.write(
                b"HTTP/1.1 400 Bad Request\r\n\r\nCannot proxy to myself."
            )
            await writer.drain()
            return

        # 6. Forward payload asynchronously to Target Server
        try:
            target_reader, target_writer = await asyncio.open_connection(
                target[0], target[1]
            )
            target_writer.write(payload_to_send)
            await target_writer.drain()

            # Proxy response back to client asynchronously
            while True:
                try:
                    response_chunk = await asyncio.wait_for(
                        target_reader.read(4096), timeout=2.0
                    )
                    if not response_chunk:
                        break
                    writer.write(response_chunk)
                    await writer.drain()
                except asyncio.TimeoutError:
                    break

            target_writer.close()
            await target_writer.wait_closed()

        except Exception as net_err:
            print(f"[!] Target connection error ({target}): {net_err}")
            writer.write(
                b"HTTP/1.1 502 Bad Gateway\r\n\r\nFailed to connect to target server."
            )
            await writer.drain()

    except Exception as e:
        print(f"Error handling client {client_id}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    # 1. Open connection pool and initialize database schema asynchronously
    await open_pool()
    await init_db()

    client_id_counter = 0

    # Callback factory to pass client_id to handle_client
    async def client_cb(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        nonlocal client_id_counter
        client_id_counter += 1
        await handle_client(reader, writer, client_id_counter)

    # 2. Start Asyncio Socket Server
    server = await asyncio.start_server(client_cb, SERVER_IP, PORT)
    print(f"🚀 Server is listening! Open http://127.0.0.1:{PORT}")

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            pass
        finally:
            print("\n🛑 Shutting down server...")
            await close_pool()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully.")