import socket
import threading
import time
import functools
from inspector_tools import HTTPRequest, JSONLogger, Security_Analyzer
from typing import Callable, Any

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


def track_uptime(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        addr = args[1] if len(args) > 1 else kwargs.get("addr", ("Unknown", 0))
        client_id = args[2] if len(args) > 2 else kwargs.get("client_id", 0)
        start_time = time.time()

        result = func(*args, **kwargs)

        uptime = time.time() - start_time
        print(f"[UPTIME] Client {client_id} [Port: {addr[1]}] disconnected. Active for: {uptime:.2f}s\n")
        return result

    return wrapper


@track_uptime
def handle_client(client_socket, addr, client_id):
    print(f"\n[NEW CONNECTION] Client {client_id} connected from port: {addr[1]}")
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
                return

        if not raw_bytes:
            return

        message = raw_bytes.decode(FORMAT, errors="replace")

        req = HTTPRequest(message)

        print("=" * 50)
        print(f"[MINI-BURP INPSECTOR - CLIENT {client_id}]")
        print(f"    ▶ Method:       {req.method}")
        print(f"    ▶ Path:         {req.path}")
        print(f"    ▶ cookie:         {req.cookies}")
        print(f"    ▶ Query Params: {req.query_params}")
        print(f"    ▶ Host Header:  {req.headers.get('host', 'Unknown')}")
        print(f"    ▶ User-Agent:   {req.headers.get('user-agent', 'Unknown')[:60]}...")
        if req.body:
            print(f"    ▶ Body Data:    {req.body}")
        print(f"{RED}" + "=" * 50 + f"{RESET}")
        file_logger.log_request(req)
        security_result = security_analyze.analyze(req)

        if not security_result["is_secure"]:

            clean_patterns = ", ".join(security_result["matched_patterns"])

            print(f"{RED}[🚨 SECURITY ALERT] Malicious Request Detected!{RESET}")
            print(f"{RED}    ▶ Attack Type:      {security_result['attack_type']}{RESET}")
            print(f"{RED}    ▶ Matched Patterns: {clean_patterns}{RESET}")
            print(f"{RED}" + "=" * 50 + f"{RESET}")



        target = (req.target_host, req.target_port)
        if target == (SERVER_IP, PORT) or target == ("127.0.0.1", PORT):
            print(f"[!] Blocked an infinite loop request to ourselves: {target}")
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\nCannot proxy to myself.")
            return
        #server represents the act of client here:
        mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



        mitm_socket.connect(target)
        mitm_socket.sendall(raw_bytes)

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
    server.listen()
    print(f"Server is listening! Open http://127.0.0.1:{PORT}")
    client_id = 0
    while True:
        client, addr = server.accept()
        client_id += 1
        thread = threading.Thread(target=handle_client, args=(client, addr, client_id))
        thread.start()


if __name__ == "__main__":
    start()