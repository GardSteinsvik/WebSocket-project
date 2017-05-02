import time
from _sha1 import sha1
from base64 import b64encode

import frame_handler
from buffer import Buffer

ping_interval_seconds = 5
ping_pong_keepalive_interval = 3


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

    def __init__(self, conn):
        self.conn = conn
        self.conn.setblocking(0)

    def keep_alive(self):
        now = time.time()
        # print(now - self.time_at_last_activity)
        if now - self.time_at_last_activity > ping_interval_seconds:
            self.send_ping()
            self.time_at_last_activity = now

        if self.time_rec_next_pong_to_live > ping_pong_keepalive_interval:
            self.time_rec_next_pong_to_live = now + ping_pong_keepalive_interval
            print('Request closed due to inactivity')
            self.request_close()

    def close(self, reason):
        self.is_alive = False
        self.conn.close()
        print('Closing connection. Reason:', reason)

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
        self.send_close('')

    def recv(self):
        if self.hands_shook:
            self.keep_alive()

        bytes_rec = self.conn.recv(1024)  # raises error if no data received. This is handled elsewhere
        self.time_at_last_activity = time.time()
        if not bytes_rec:
            return

        if self.hands_shook:
            # print('bytes recieved:', bytes_rec)
            try:
                if self.buffer:
                    print(self.buffer.datatype)
                    msg = frame_handler.unmask(bytes_rec, self.buffer.datatype)
                else:
                    msg = frame_handler.unmask(bytes_rec)
            except:
                return

            print(vars(msg))

            payload = msg.return_data

            if msg.is_pong:
                return self.handle_pong()

            if msg.is_ping:
                return self.handle_ping(payload)

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

            if msg.is_close:
                return self.handle_close(payload, 'Client close request')
        else:  # if handshake not done
            headers = self.parse_as_headers(bytes_rec)
            if not self.do_handshake(headers):
                # not a valid handshake as first request
                # close connection
                print('Not a valid handshake request received as first message. Closing connection...')
                self.close('Not a valid handshake request recieved')
            else:
                print('Valid handshake completed')

    def handle_pong(self):
        # print('Recieved pong')
        pass

    def send_ping(self):
        # print('Sending ping')
        self.send_msg(frame_handler.build_frame('phony', opcode=frame_handler.OPCODE_PING))

    def send_close(self, msg):
        self.send_msg(frame_handler.build_frame(msg, frame_handler.OPCODE_CLOSE))

    def handle_ping(self, message):
        pong_msg = frame_handler.build_frame(message, frame_handler.OPCODE_PONG)
        self.send_msg(pong_msg)
        return self.recv()

    def handle_close(self, msg, reason):
        if not self.server_requested_close:
            self.send_close(msg)
        self.close(reason)
        return msg

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
