import time
from _sha1 import sha1
from base64 import b64encode

import frame_handler
from buffer import Buffer


class WebSocket:
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    handshake_ans = \
        'HTTP/1.1 101 Switching Protocols\n' \
        'Upgrade: Websocket\n' \
        'Connection: Upgrade\n' \
        'Sec-WebSocket-Accept: {0}\r\n\r\n'
    conn = None
    hands_shook = False
    time_at_last_activity = 0
    time_rec_next_pong_to_live = 0

    is_alive = True

    server_requested_close = False

    buffer = None

    ping_interval_seconds = 20
    ping_pong_keep_alive_interval = 3

    def __init__(self, conn, ping_interval_seconds, ping_pong_keep_alive_interval, debug=False):
        self.conn = conn
        self.conn.setblocking(0)
        self.ping_interval_seconds = ping_interval_seconds
        self.ping_pong_keep_alive_interval = ping_pong_keep_alive_interval
        self.debug = debug

    def keep_alive(self):
        now = time.time()

        if now - self.time_at_last_activity > self.ping_interval_seconds:
            self.send_ping()
            self.time_at_last_activity = now

        if self.time_rec_next_pong_to_live > self.ping_pong_keep_alive_interval:
            self.time_rec_next_pong_to_live = now + self.ping_pong_keep_alive_interval
            self.send_close('Connection closed due to inactivity')
            self.close()

    def close(self,):
        self.is_alive = False
        self.conn.close()

    def do_handshake(self, headers):
        sec_web_key = 'Sec-WebSocket-Key'.lower()

        if sec_web_key in headers.keys():
            value = headers[sec_web_key].strip()
            h = value + self.GUID
            s = sha1(h.encode()).digest()
            r_key = b64encode(s).decode().strip()
            ws_answer = self.handshake_ans.format(r_key)
            self.send_msg(ws_answer.encode('utf-8'))
            self.hands_shook = True
            return True

    def send_msg(self, msg):
        self.conn.send(msg)

    def request_close(self):
        self.server_requested_close = True
        self.send_close('1000')

    def recv(self):
        if self.hands_shook:
            self.keep_alive()

        bytes_rec = self.conn.recv(65536)  # raises error and returns if no data received. Error is handled elsewhere
        self.time_at_last_activity = time.time()
        if not bytes_rec:
            return

        if self.hands_shook:
            try:
                if self.buffer:
                    msg = frame_handler.unmask(bytes_rec, self.buffer.datatype)
                else:
                    msg = frame_handler.unmask(bytes_rec)
            except ValueError as er:
                self.send_close(er)
                self.close()
                return

            payload = msg.return_data

            if msg.is_pong:
                return self.handle_pong()

            if msg.is_ping:
                return self.handle_ping(payload)

            if msg.is_close:
                return self.handle_close(payload, '1000')

            if msg.is_close_fin:
                if msg.is_continuation:
                    self.buffer.append(payload)
                    return_data = self.buffer.get_data()
                    self.buffer = None
                    return return_data
                else:
                    return payload
            else:
                if msg.is_continuation:
                    self.buffer.append(payload)
                else:
                    self.buffer = Buffer(msg.is_text)
                    self.buffer.append(payload)
        else:  # if handshake not done
            headers = self.parse_as_headers(bytes_rec)
            if not self.do_handshake(headers):
                # not a valid handshake as first request
                # close connection
                if self.debug:
                    print('Not a valid handshake request received as first message. Closing connection...')
                self.close()
            else:
                if self.debug:
                    print('Valid handshake completed')

    def handle_pong(self):
        if self.debug:
            print('Recieved pong')
        pass

    def send_ping(self):
        if self.debug:
            print('Sending ping')
        self.send_msg(frame_handler.build_frame('phony', opcode=frame_handler.OPCODE_PING))

    def send_close(self, msg):
        if self.debug:
            print('Sending close')
        self.send_msg(frame_handler.build_frame(msg, frame_handler.OPCODE_CLOSE))

    def handle_ping(self, message):
        pong_msg = frame_handler.build_frame(message, frame_handler.OPCODE_PONG)
        self.send_msg(pong_msg)

    def handle_close(self, msg, reason):
        if not self.server_requested_close:
            self.send_close(msg)
        self.close()

    @staticmethod
    def parse_as_headers(data):
        """
        Parses data as a list of headers and returns the headers as a dictionary.
        :param data: data received from client
        :return: Headers as a dictionary with keys in lower-case
        """
        data = data.strip()

        def parse_val(val):
            return val.decode('utf-8').strip()

        headers = {}
        for l in data.split(b'\r\n')[1:]:
            key, value = l.split(b': ')
            headers[parse_val(key).lower()] = parse_val(value)

        return headers
