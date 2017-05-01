# -*- coding: utf-8 -*-
import socket
import ssl
from threading import Thread

from connection import Connection


class WebSocketServer:
    server_socket = None

    connections = []

    def __init__(self, listen_ip, port):
        self.server_socket = socket.socket()
        if port == 443:
            ctx = ssl.create_default_context()
            self.server_socket = ssl.wrap_socket(self.server_socket,
                                                 server_side=True,
                                                 certfile="server.crt",
                                                 keyfile="server.key")
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((listen_ip, port))
        self.start()

    def listen(self):
        self.server_socket.listen()
        while True:
            conn, address = self.server_socket.accept()
            print('Connection attempt recieved at ' + address[0])
            self.connections.append(Connection(conn))

    def connection_handler(self):
        while True:
            for c in self.connections:
                try:
                    c.single_action()
                except socket.error:
                    pass

    def start(self):
        Thread(target=self.listen).start()
        print('Starting connection handler')
        Thread(target=self.connection_handler).start()
