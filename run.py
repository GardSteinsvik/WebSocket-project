# -*- coding: utf-8 -*-
import signal
import sys
import time

from web_socket_server import WebSocketServer


def create_server(port):
    server = WebSocketServer('0.0.0.0', port)
    return server


def connection_handler(msg):
    print('msg recieved:', msg)


if __name__ == '__main__':
    s = create_server(80, )
    s.start(connection_handler)

    def signal_handler(signal, frame):
        print("Caught Ctrl+C, shutting down...")
        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        time.sleep(100)
