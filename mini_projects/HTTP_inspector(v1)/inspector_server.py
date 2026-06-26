import socket
import threading
import time
import functools
import HTTPRequest
from typing import Callable, Any

PORT = 8080
FORMAT = "utf-8"

SERVER_IP = "0.0.0.0"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

        req = HTTPRequest.HTTPRequest(message)

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
        print("=" * 50)

        response_body = (
            "<html>"
            "<head><title>HTTP Inspector</title></head>"
            "<body style='font-family: sans-serif; text-align: center; margin-top: 50px;'>"
            "   <h1 style='color: #2e7d32;'>Hello!👋</h1>"
            "   <p style='color: #555;'>Your HTTP Inspector successfully captured this request.</p>"
            "   <p>Check your server terminal to see the raw headers sent by your browser.</p>"
            "</body>"
            "</html>"
        )

        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(response_body.encode(FORMAT))}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        full_response = response_headers + response_body
        client_socket.sendall(full_response.encode(FORMAT))

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