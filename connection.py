# -*- coding: utf-8 -*-
from threading import Thread

from web_socket import WebSocket


class Connection:

    def __init__(self, conn):
        self.sock = WebSocket(conn)

    def thread_handler(self):
        msg = '0'
        while msg:
            msg = self.sock.recv()
            print(msg)

    def start(self):
        Thread(target=self.thread_handler).start()
