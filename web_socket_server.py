import socket


class WebSocketServer:

    sock = None
    connections = {}

    def __init__(self, listen_ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((listen_ip, port))

    def listen(self):
        self.sock.listen()
        while True:
            conn, address = self.sock.accept()


