from _sha1 import sha1
from base64 import b64encode

from frame_handler import unmask


class WebSocket:

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    handshake_ans = \
        'HTTP/1.1 101 Switching Protocols\n' \
        'Upgrade: Websocket\n' \
        'Connection: Upgrade\n' \
        'Sec-WebSocket-Accept: {0}\r\n\r\n'
    conn = None
    hands_shook = False

    def __init__(self, conn):
        self.conn = conn
        self.recv()

    def do_handshake(self, headers):
        sec_web_key = 'Sec-WebSocket-Key'

        if sec_web_key in headers.keys():
            value = headers[sec_web_key]
            h = value + self.GUID
            s = sha1(h.encode()).digest()
            r_key = b64encode(s).decode()
            ws_answer = self.handshake_ans.format(r_key)
            self.send_msg(ws_answer)
            self.hands_shook = True
            return True

        return False

    def send_msg(self, msg):
        self.conn.send(msg.encode())

    def recv(self):
        msg = self.conn.recv(1024)
        # if handshake not already done
        if not self.hands_shook:
            headers = self.parse_as_headers(msg)
            if not self.do_handshake(headers):
                # not a valid handshake as first request
                # close connection
                print('Not a valid handshake request received as first message. Closing connection...')
                self.conn.close()
                print('Socket closed')
            else:
                print('Valid handshake completed')
        else:
            msg = unmask(msg)
            print('last_frame:', msg.is_close_fin, '\nclose:', msg.is_close)
            if msg.is_close:
                print('Connection closing')
                self.conn.close()
            if msg.is_close_fin:
                return msg.is_close_fin + self.recv()
            return msg.return_data

    @staticmethod
    def parse_as_headers(data):
        """
        Parses data as a list of headers and returns the headers as a dictionary.
        :param data: data received from client
        :return: Headers as a dictionary
        """
        print(data)
        data = data.strip()

        headers = {}
        for l in data.split(b'\r\n')[1:]:
            key, value = l.split(b': ')
            headers[key.decode('utf-8').strip()] = value.decode('utf-8').strip()

        return headers
