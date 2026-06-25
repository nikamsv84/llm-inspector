import socket
HEADER = 64
PORT = 1500
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'
server_ip = "127.0.1.1"
addr = (server_ip, PORT)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(addr)

def send_message(message):
    '''calculating the length that should be send in the first 64 bytes
    (server should know that how many bytes shout it read )'''
    msg_len = len(message)
    send_length = str(msg_len).encode(FORMAT)
    send_length += b" "*(HEADER - len(send_length))
    sending_message = str(message).encode(FORMAT)
    client.send(send_length)
    client.send(sending_message)

send_message("hello server")
send_message("this is a working message")
input("press the ENTER to leave session")
send_message(DISCONNECT_MESSAGE)





