from base64 import b64encode
from hashlib import sha1
from threading import Thread

from frame_handler import unmask


def parse_data(data):
    """
    Returns headers and payload as two variables.
    :param data: data received from client
    :return: Headers as dictionary and unmasked payload as two variables.
    """
    header_split = b'\r\n\r\n'
    print(data)
    header_lines, payload = data.split(header_split, 1)

    if payload:
        payload = unmask(payload)

    headers = {}
    for l in header_lines.split(b'\r\n')[1:]:
        key, value = l.split(b': ')
        headers[key.decode('utf-8').strip()] = value.decode('utf-8').strip()

    return headers, payload


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

    def do_handshake(self, headers):
        sec_web_key = 'Sec-WebSocket-Key'

        if sec_web_key in headers.keys():
            value = headers[sec_web_key]
            h = value + self.GUID
            s = sha1(h.encode()).digest()
            r_key = b64encode(s).decode()
            ws_answer = self.answer.format(r_key)
            self.send(ws_answer)
            self.hands_shook = True
            return True

        return False

    def send(self, msg):
        self.conn.send(msg.encode())

    def thread_handler(self):
        while True:
            data = self.conn.recv(1024)
            headers, payload = parse_data(data)
            # if handshake not already done
            if not self.hands_shook:

                # if msg not valid handshake
                if not self.do_handshake(headers):
                    # not a valid handshake as first request
                    # close connection
                    print('Not a valid handshake request recieved as first message. Closing connection...')
                    self.conn.close()
                    break
                else:
                    print('Valid handshake completed')

    def start(self):
        self.t = Thread(target=self.thread_handler)
        self.t.start()
