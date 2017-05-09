# -*- coding: utf-8 -*-
import signal
import sys

import frame_handler
from web_socket_server import WebSocketServer

connections = []


def message_handler(msg, connection):
    """
    This is the method that is called each time a message is received.
    :param msg: The message that is received
    :param connection: The connection that received the message
    """
    for conn in connections:
        if not conn.is_alive:
            connections.remove(conn)
            print('Removed dead conn')
            continue
        if conn != connection:
            conn.send_text(msg)


def connection_handler(conn, addr):
    print('New connection from ' + str(addr))
    connections.append(conn)


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
    s.start(message_handler, connection_handler, worker_thread_count=20)

    signal.signal(signal.SIGINT, signal_handler)
