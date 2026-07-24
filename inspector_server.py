import functools
import socket
import threading
import time
from typing import Any, Callable

from database import *
from inspector_tools import HTTPRequest, JSONLogger, Security_Analyzer

PORT = 8080
FORMAT = "utf-8"
SERVER_IP = "0.0.0.0"
RED = "\033[91m"
RESET = "\033[0m"


file_logger = JSONLogger("requests_log.json")
security_analyze = Security_Analyzer()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((SERVER_IP, PORT))


def auto_release_tester(
    req_id: int, action: str = "forwarded", delay_seconds: float = 3.0
):
    """
    Simulates user action on the dashboard after a specified delay.
    Runs in a background thread within the same process memory space.
    """

    def _task():
        time.sleep(delay_seconds)
        print(
            f"\n[TEST SIMULATOR] Simulating user action on Request #{req_id} ->"
            f" Action: '{action}'"
        )
        released = release_intercepted_request(req_id, action)
        print(
            f"[TEST SIMULATOR] Signal delivered to event registry: {released}\n"
        )

    threading.Thread(target=_task, daemon=True).start()


def track_uptime(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        addr = args[1] if len(args) > 1 else kwargs.get("addr", ("Unknown", 0))
        client_id = args[2] if len(args) > 2 else kwargs.get("client_id", 0)
        start_time = time.time()

        result = func(*args, **kwargs)

        uptime = time.time() - start_time
        print(
            f"[UPTIME] Client {client_id} [Port: {addr[1]}] disconnected."
            f" Active for: {uptime:.2f}s\n"
        )
        return result

    return wrapper


@track_uptime
def handle_client(client_socket, addr, client_id):
    print(
        f"\n[NEW CONNECTION] Client {client_id} connected from port: {addr[1]}"
    )
    try:
        client_socket.settimeout(3.0)

        raw_bytes = b""

        while b"\r\n\r\n" not in raw_bytes:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            raw_bytes += chunk

            if len(raw_bytes) > 8192:
                print(f"[!] Client {client_id} sent abnormally large headers.")
                client_socket.sendall(
                    b"HTTP/1.1 431 Request Header Fields Too Large\r\n\r\nHeaders exceeded maximum allowed size."
                )
                return

        if not raw_bytes:
            return

        message = raw_bytes.decode(FORMAT, errors="replace")

        req = HTTPRequest(message)

        print("=" * 50)
        print(f"[MINI-BURP INSPECTOR - CLIENT {client_id}]")
        print(f"    ▶ Method:       {req.method}")
        print(f"    ▶ Path:         {req.path}")
        print(f"    ▶ Cookie:       {req.cookies}")
        print(f"    ▶ Query Params: {req.query_params}")
        print(f"    ▶ Host Header:  {req.headers.get('host', 'Unknown')}")
        print(
            "    ▶ User-Agent:  "
            f" {req.headers.get('user-agent', 'Unknown')[:60]}..."
        )
        if req.body:
            print(f"    ▶ Body Data:    {req.body}")
        print(f"{RED}" + "=" * 50 + f"{RESET}")

        file_logger.log_request(req)
        security_result = security_analyze.analyze(req)

        if not security_result["is_secure"]:
            clean_patterns = ", ".join(security_result["matched_patterns"])

            print(f"{RED}[🚨 SECURITY ALERT] Malicious Request Detected!{RESET}")
            print(
                f"{RED}    ▶ Attack Type:     "
                f" {security_result['attack_type']}{RESET}"
            )
            print(
                f"{RED}    ▶ Matched Patterns: {clean_patterns}{RESET}"
            )
            print(f"{RED}" + "=" * 50 + f"{RESET}")

        # 1. Save raw request to database
        request_id = save_raw_requests(req, raw_bytes=raw_bytes)
        print(f"💾 [DB] Saved raw request with ID: {request_id}")

        # 2. Insert entry into intercept queue
        queue_id = create_intercept_entry(request_id)
        print(
            f"⏸️ [INTERCEPT] Request #{request_id} queued (Queue ID: {queue_id})."
            " Holding thread..."
        )

        # 🧪 DISABLED FOR MANUAL TESTING:
        # auto_release_tester(request_id, action="forwarded", delay_seconds=15)

        # 3. Block client thread until released by user (or timeout after 5 mins)
        action = wait_for_user_action(request_id, timeout=300.0)
        print(
            f"🟢 [INTERCEPT] Thread unblocked for Request #{request_id}. Action:"
            f" '{action}'"
        )

        # 4. Handle user action: close socket if request was dropped
        if action == "dropped":
            print(
                f"🚫 [DROPPED] Request #{request_id} was dropped by user."
                " Closing socket."
            )
            client_socket.sendall(
                b"HTTP/1.1 403 Forbidden\r\n\r\nRequest dropped by Interceptor."
            )
            return

        # 5. Fetch modified bytes if available in database
        modified_bytes = get_modified_request_bytes(request_id)
        payload_to_send = (
            modified_bytes if modified_bytes is not None else raw_bytes
        )

        # 5. Fetch modified bytes if available in database
        modified_bytes = get_modified_request_bytes(request_id)

        if modified_bytes:
            payload_to_send = modified_bytes
            modified_req = HTTPRequest(modified_bytes.decode(FORMAT, errors="replace"))
            target = (modified_req.target_host, modified_req.target_port)
        else:
            payload_to_send = raw_bytes
            target = (req.target_host, req.target_port)

        if target == (SERVER_IP, PORT) or target == ("127.0.0.1", PORT):
            print(f"[!] Blocked an infinite loop request to ourselves: {target}")
            client_socket.sendall(
                b"HTTP/1.1 400 Bad Request\r\n\r\nCannot proxy to myself."
            )
            return

        # 6. Forward final payload (original or modified) to target server
        mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mitm_socket.connect(target)
        mitm_socket.sendall(payload_to_send)

        mitm_socket.settimeout(2.0)

        try:
            while True:
                response_chunk = mitm_socket.recv(4096)

                if not response_chunk:
                    break

                client_socket.sendall(response_chunk)

        except socket.timeout:
            pass
        finally:
            mitm_socket.close()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()


def start():
    # Open connection pool and initialize database schema
    open_pool()
    init_db()

    server.listen()
    print(f"🚀 Server is listening! Open http://127.0.0.1:{PORT}")
    client_id = 0
    try:
        while True:
            client, addr = server.accept()
            client_id += 1
            thread = threading.Thread(
                target=handle_client, args=(client, addr, client_id)
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        close_pool()  # Ensure database pool is safely closed on server shutdown


if __name__ == "__main__":
    start()