# -*- coding: utf-8 -*-
import socket
import ssl
from threading import Thread

from web_socket import WebSocket


class WebSocketServer:
    server_socket = None
    connections = []

    def __init__(self, listen_ip, port):
        self.server_socket = socket.socket()
        if port == 443:
            self.server_socket = ssl.wrap_socket(self.server_socket,
                                                 server_side=True,
                                                 certfile="server.crt",
                                                 keyfile="server.key",
                                                 ssl_version=ssl.PROTOCOL_SSLv23)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((listen_ip, port))

    def listen(self):
        self.server_socket.listen()
        while True:
            conn, address = self.server_socket.accept()
            print('Connection attempt recieved at ' + address[0])
            self.connections.append(WebSocket(conn))

    def connection_handler(self, func):
        while True:
            i = 0
            for c in self.connections:
                if not c.is_alive:
                    self.connections.pop(i)
                    print('Removed connection. Reason: not alive')
                    continue
                try:
                    msg = c.recv()
                    if msg:
                        func(msg)
                except socket.error:
                    # no data received yet
                    pass

    def start(self, func):
        Thread(target=self.listen).start()
        print('Starting connection handler')
        Thread(target=self.connection_handler, args=(func,)).start()
