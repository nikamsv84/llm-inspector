import socket
import threading
import time
import functools
from typing import Callable, Any

HEADER = 64
port = 1500
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
#ip address of the server
server_ip = socket.gethostbyname(socket.gethostname())
#creating a socket for our program
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#connecting the server and port to the socket
server.bind((server_ip, port))


def track_uptime(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        addr = args[1] if len(args) > 1 else kwargs.get("addr", ("Unknown", 0))
        client_id = args[2] if len(args) > 2 else kwargs.get("client_id", 0)

        start_time = time.time()

        result = func(*args, **kwargs)

        uptime = time.time() - start_time
        print(f"\n[UPTIME] Client {client_id} [Port: {addr[1]}] disconnected. Active for: {uptime:.2f}s")

        return result

    return wrapper

@track_uptime
def handle_client(client_socket, addr, client_id):
    print(f"[NEW CONNECTION] Client {client_id} connected from port: {addr[1]}")
    connected = True
    while connected:
        try:
            message_length = client_socket.recv(HEADER).decode(FORMAT)
            if message_length:
                message_length = int(message_length)
                message = client_socket.recv(message_length).decode(FORMAT)
                print(f"{message}->{client_id} [portnum:{addr[1]}]")
                if message == DISCONNECT_MESSAGE:
                    connected = False

        except Exception as e:
            print(f"Error {e}")
            break
    client_socket.close()


def start():
    server.listen()
    print("server is listening")
    client_id = 0
    while True:
        client, addr = server.accept()
        client_id += 1
        thread = threading.Thread(target=handle_client, args=(client,addr, client_id))
        thread.start()
        print(f"we have {threading.active_count()-1} active connections")

if __name__ == "__main__":
    start()
