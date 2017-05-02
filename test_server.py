# -*- coding: utf-8 -*-
import signal
import sys

from web_socket_server import WebSocketServer


def message_handler(msg, connection):
    print('msg received from', connection, ':', msg)


def signal_handler(signal, frame):
    print("Caught Ctrl+C, shutting down...")
    s.stop()
    sys.exit()


if __name__ == '__main__':
    s = WebSocketServer('0.0.0.0', 80, debug=False)
    s.start(message_handler, worker_thread_count=20)

    signal.signal(signal.SIGINT, signal_handler)