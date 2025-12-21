import socket

HOST = "127.0.0.1"  # replace with server IP
PORT = 5000

payload = "move 0,540\n"  # left-middle, center-middle for 1920x1080

with socket.create_connection((HOST, PORT)) as s:
    s.sendall(payload.encode("utf-8"))
