# -*- coding: utf-8 -*-
from web_socket import WebSocket


class Connection:
    def __init__(self, conn):
        self.sock = WebSocket(conn)

    def single_action(self):
        msg = '0'
        while msg:
            msg = self.sock.recv()
            print(msg)
