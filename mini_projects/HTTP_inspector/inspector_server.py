import socket
import threading
import time
import functools
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
        message = client_socket.recv(4096).decode(FORMAT)
        if not message:
            return

        lines = message.splitlines()
        if not len(lines):
            return

        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) >= 2:
            method = parts[0]
            url = parts[1]
            http_version = parts[2] if len(parts) > 2 else "HTTP/1.1"

            print("=" * 40)
            print(f"🔍 [INSPECTED REQUEST LINE]")
            print(f"   🔹 Method: {method}")
            print(f"   🔹 URL/Path: {url}")
            print(f"   🔹 Version: {http_version}")
            print("=" * 40)

        print("📋 [HTTP HEADERS]")
        for line in lines[1:]:
            if line.strip() == "":
                break
            print(f"   🔸 {line}")
        print("=" * 40)

        response_body = (
            "<html>"
            "<head><title>HTTP Inspector</title></head>"
            "<body style='font-family: sans-serif; text-align: center; margin-top: 50px;'>"
            "   <h1 style='color: #2e7d32;'>Hello! 👋</h1>"
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
    print(f"🚀 Server is listening! Open http://127.0.0.1:{PORT} in Firefox")
    client_id = 0
    while True:
        client, addr = server.accept()
        client_id += 1
        thread = threading.Thread(target=handle_client, args=(client, addr, client_id))
        thread.start()


if __name__ == "__main__":
    start()