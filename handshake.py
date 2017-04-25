import socket
import re
from base64 import b64encode
from hashlib import sha1

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

wsAnswer = \
    'HTTP/1.1 101 Switching Protocols' \
    'Upgrade: Websocket' \
    'Connection: Upgrade' \
    'Sec-WebSocket-Accept: {0}\r\n\r\n'


def dohandshake(header):

    for line in header.split('\r\n')[1:]:
        name, value = line.split(': ', 1)

        if name.lower() == "sec-websocket-key":
            rKey = b64encode(sha1(value + GUID).digest())
            wsAnswer = wsAnswer.format(rKey)

    #send(wsAnswer) Ikke implementert TODO:
    return True
