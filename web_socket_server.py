import socket

from connection import Connection


class WebSocketServer:

    sock = None

    def __init__(self, listen_ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((listen_ip, port))

    def listen(self):
        self.sock.listen()
        while True:
            conn, address = self.sock.accept()
            print('Connection attempt recieved at ' + address[0])
            print(conn)
            print(address)
            connection = Connection(conn)
            connection.start()
