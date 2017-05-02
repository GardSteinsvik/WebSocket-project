# -*- coding: utf-8 -*-
import socket
import ssl
from queue import Queue
from threading import Thread

from web_socket import WebSocket


class WebSocketServer:
    server_socket = None

    threads = []

    is_kill = False

    queue = Queue()

    def __init__(self, listen_ip, port, ping_interval_seconds=20, ping_pong_keep_alive_interval=3):
        self.server_socket = socket.socket()
        if port == 443:
            self.server_socket = ssl.wrap_socket(self.server_socket,
                                                 server_side=True,
                                                 certfile="server.crt",
                                                 keyfile="server.key",
                                                 ssl_version=ssl.PROTOCOL_SSLv23)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((listen_ip, port))
        self.ping_interval_seconds = ping_interval_seconds
        self.ping_pong_keep_alive_interval = ping_pong_keep_alive_interval

    def listen(self):
        self.server_socket.setblocking(0)
        self.server_socket.listen()
        while not self.is_kill:
            try:
                conn, address = self.server_socket.accept()
                print('Connection attempt recieved at ' + address[0])
                self.queue.put(WebSocket(conn, ping_interval_seconds=self.ping_interval_seconds,
                                         ping_pong_keep_alive_interval=self.ping_pong_keep_alive_interval))
            except socket.error:
                pass  # no connection yet

    def worker(self, func):
        while not self.is_kill:
            self.single_action(func)

    def single_action(self, func):
        c = self.queue.get()
        try:
            msg = c.recv()
            if msg:
                func(msg, c)
        except socket.error:
            # no data received yet
            pass
        if c.is_alive:
            self.queue.put(c)

    def start(self, func, thread_count):
        Thread(target=self.listen).start()
        print('Starting connection handler')
        for i in range(thread_count):
            t = Thread(target=self.worker, args=(func,))
            t.start()

    def stop(self):
        self.is_kill = True
        print('Stopping server...')
        for t in self.threads:
            t.join()
