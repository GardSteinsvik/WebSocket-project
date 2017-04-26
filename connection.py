from base64 import b64encode
from hashlib import sha1
from threading import Thread


class Connection:
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    answer = \
        'HTTP/1.1 101 Switching Protocols\n' \
        'Upgrade: Websocket\n' \
        'Connection: Upgrade\n' \
        'Sec-WebSocket-Accept: {0}\r\n\r\n'

    conn = None
    t = None
    hands_shook = False

    def __init__(self, conn):
        self.conn = conn

    def do_handshake(self, header):
        ws_answer = self.answer
        valid_handshake_req = False
        for line in header.split('\r\n')[1:]:
            name, value = line.split(': ', 1)

            if name.lower() == "sec-websocket-key":
                h = value.strip() + self.GUID
                s = sha1(h.encode()).digest()
                r_key = b64encode(s).decode()
                ws_answer = ws_answer.format(r_key)
                valid_handshake_req = True

        if valid_handshake_req:
            self.send(ws_answer)
            self.hands_shook = True
            return True
        return False

    def send(self, msg):
        self.conn.send(msg.encode())

    def thread_handler(self):
        while True:
            b = self.conn.recv(1024)
            # msg = unmask(b)
            msg = b.decode()
            # if handshake not already done
            if not self.hands_shook:
                splits = msg.split('\r\n\r\n')

                header = splits[0]
                # if msg not valid handshake
                if not self.do_handshake(header):
                    # not a valid handshake as first request
                    # close connection
                    print('Not a valid handshake request recieved as first message. Closing connection...')
                    self.conn.close()
                    break

    def start(self):
        self.t = Thread(target=self.thread_handler)
        self.t.start()
