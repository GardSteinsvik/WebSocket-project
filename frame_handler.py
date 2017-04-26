# -*- coding: utf-8 -*-
import struct

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xa


def mask(data):

    payload = bytearray(data.encode('utf-8'))

    message = []

    # Adding fin
    b1 = 0x80
    b1 |= OPCODE_TEXT
    print(chr(b1))
    message.append(chr(b1))

    b2 = 0
    payload_length = len(payload)

    if payload_length < 126:
        b2 |= payload_length
        print(chr(b2).encode('utf-8'))
        message.append(chr(b2))
    elif payload_length < ((2 ** 16) - 1):
        b2 |= 126
        message.append(chr(b2))
        # packing to unsigned short
        l = struct.pack(">H", payload_length)
        message.append(l)
    else:
        b2 |= 127
        message += chr(b2)
        # packing to unsigned long long
        l = struct.pack(">Q", payload_length)
        message.append(l)

    for c in payload:
        message.append(c)

    return message


def unmask(data):
    frame = bytearray(data)

    length = frame[1] & 127
    print('length: ' + str(length))

    mask_start = 2
    if length == 126:
        mask_start = 4
    elif length == 127:
        mask_start = 10

    data_start = mask_start + 4

    output_bytes = []
    for i in range(data_start, data_start+length):
        byte = frame[i] ^ frame[mask_start + (i - data_start) % 4]
        output_bytes.append(byte)

    return "".join(map(chr, output_bytes))

if __name__ == '__main__':
    data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]
    print(mask('test'))


