# -*- coding: utf-8 -*-
import signal
import sys

from web_socket_server import WebSocketServer


def message_handler(msg, connection):
    """
    This is the method that is called each time a message is received.
    :param msg: The message that is received
    :param connection: The connection that received the message
    """
    print('msg received from', connection, ':', msg)


def signal_handler(signal, frame):
    """
    Stops the server before the application is shut down.
    """
    print("Caught Ctrl+C, shutting down...")
    s.stop()
    sys.exit()


if __name__ == '__main__':
    s = WebSocketServer('0.0.0.0', 80)
    # starts the server. This call is non-blocking
    s.start(message_handler, worker_thread_count=20)

    signal.signal(signal.SIGINT, signal_handler)
