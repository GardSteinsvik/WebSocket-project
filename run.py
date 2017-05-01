# -*- coding: utf-8 -*-
import signal
import sys
import time
from threading import Thread

from web_socket_server import WebSocketServer


def create_server(port):
    server = WebSocketServer('0.0.0.0', port)
    server_thread = Thread(target=server.listen)
    server_thread.start()


if __name__ == '__main__':
    create_server(80)
    create_server(443)

    def signal_handler(signal, frame):
        print("Caught Ctrl+C, shutting down...")
        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        time.sleep(100)
