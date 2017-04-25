import signal
import sys
import time
from threading import Thread

from web_socket_server import WebSocketServer
from web_socket import WebSocket

if __name__ == '__main__':
    server = WebSocketServer('0.0.0.0', 8000)
    server_thread = Thread(target=server.listen, args=[5])
    server_thread.start()


    def signal_handler(signal, frame):
        print("Caught Ctrl+C, shutting down...")
        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        time.sleep(100)
