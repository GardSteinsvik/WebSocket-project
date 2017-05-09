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
        """
        Does checks to see if connection is still alive and sends a ping if no activity.
        """
        now = time.time()

        if now - self.time_at_last_activity > self.ping_interval_seconds:
            self.send_ping()
            self.time_at_last_activity = now

        if self.time_rec_next_pong_to_live > self.ping_pong_keep_alive_interval:
            self.time_rec_next_pong_to_live = now + self.ping_pong_keep_alive_interval
            self.send_close('Connection closed due to inactivity')
            self.close()

    def close(self, ):
        """
        Closes the connection and sets a value that lets the server-threads know that it is closed.
        :return:
        """
        self.is_alive = False
        self.conn.close()

    def do_handshake(self, headers):
        """
        Parses the incoming headers and responds with a handshake if the incoming headers are correct
        :param headers: Dictionary of headers received from the client. Keys in lower case
        :return: True if the handshake-request was valid, False otherwise
        """
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
        """
        Sends the given frame to the client
        :param msg: A frame
        """
        self.conn.send(msg)

    def send_text(self, msg):
        self.send_msg(frame_handler.build_frame(msg, frame_handler.OPCODE_TEXT))

    def request_close(self):
        """
        Sends a close-request with the code '1000' to the client
        """
        self.server_requested_close = True
        self.send_close('1000')

    def recv(self):
        """
        Receives and parses a message from the client.
        :return: The decoded message payload if one was received and it was not a control-frame. None if not.
        """
        if self.hands_shook:
            self.keep_alive()

        # raises error and returns if no data received. Error is handled byte the server
        bytes_rec = self.conn.recv(65536)
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
                return self.handle_close(payload)

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
        else:  # if handshake has not been done
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
        """
        Handles a pong-request. Nothing has to be done here.
        """
        if self.debug:
            print('Received pong')
        pass

    def send_ping(self):
        """
        Sends a ping-request to the client
        """
        if self.debug:
            print('Sending ping')
        self.send_msg(frame_handler.build_frame('phony', opcode=frame_handler.OPCODE_PING))

    def send_close(self, msg):
        """
        Sends a close-request to the client
        """
        if self.debug:
            print('Sending close')
        self.send_msg(frame_handler.build_frame(msg, frame_handler.OPCODE_CLOSE))

    def handle_ping(self, message):
        """
        Handles a ping-request from the client
        """
        pong_msg = frame_handler.build_frame(message, frame_handler.OPCODE_PONG)
        self.send_msg(pong_msg)

    def handle_close(self, msg):
        """
        Sends a close-request to the client
        """
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
