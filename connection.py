from base64 import b64encode
from hashlib import sha1
from threading import Thread

import time


class Connection:
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    answer = \
        'HTTP/1.1 101 Switching Protocols' \
        'Upgrade: Websocket' \
        'Connection: Upgrade' \
        'Sec-WebSocket-Accept: {0}\r\n\r\n'

    conn = None
    t = None

    def __init__(self, conn):
        self.conn = conn

    def do_handshake(self, header):
        global answer
        ws_answer = answer
        valid_req = False
        for line in header.split('\r\n')[1:]:
            name, value = line.split(': ', 1)

            if name.lower() == "sec-websocket-key":
                r_key = b64encode(sha1(value + self.GUID).digest())
                ws_answer = ws_answer.format(r_key)
                valid_req = True

        if valid_req:
            self.send(ws_answer)
            return True
        return False

    def send(self, msg):
        pass

    def thread_handler(self):
        print('Connection thread started')
        time.sleep(1)

    def start(self):
        self.t = Thread(target=self.thread_handler)
        self.t.start()

    def start_connection(self, req_header):
        if self.do_handshake(req_header):
            self.start()
            return True
        return False
