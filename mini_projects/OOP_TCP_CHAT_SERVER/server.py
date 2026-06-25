import socket
import threading

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

def handle_client(client_socket, addr, client_id):
    print(f"[NEW CONNECTION] Client {client_id} connected from port: {addr[1]}")
    connect = True
    while connect:
        try:
            message_length = client_socket.recv(HEADER).decode(FORMAT)
            if message_length:
                message_length = int(message_length)
                message = client_socket.recv(message_length).decode(FORMAT)
                print(f"{message}->{client_id} [portnum:{addr[1]}]")
                if message == DISCONNECT_MESSAGE:
                    connect = False

        except Exception as e:
            print("we had an error....")
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
