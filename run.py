# -*- coding: utf-8 -*-
import signal
import sys

from web_socket_server import WebSocketServer


def connection_handler(msg, connection):
    print('msg recieved:', msg)


def signal_handler(signal, frame):
    print("Caught Ctrl+C, shutting down...")
    s.stop()
    sys.exit()


if __name__ == '__main__':
    s = WebSocketServer('0.0.0.0', 80, debug=True)
    s.start(connection_handler, worker_thread_count=20)

    signal.signal(signal.SIGINT, signal_handler)
