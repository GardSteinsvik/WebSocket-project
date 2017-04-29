import socket

from connection import Connection


class WebSocketServer:

    sock = None

    def __init__(self, listen_ip, port):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((listen_ip, port))

    def listen(self):
        self.sock.listen()
        while True:
            conn, address = self.sock.accept()
            print('Connection attempt recieved at ' + address[0])
            connection = Connection(conn)
            connection.start()
