# -*- coding: utf-8 -*-

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xa


def unmask(data):
    frame = bytearray(data)

    length = frame[1] & 127
    print('length: ' + str(length))
    mask_start = 2
    data_start = mask_start + 4

    output_bytes = []
    for i in range(data_start, data_start+length):
        byte = frame[i] ^ frame[mask_start + (i - data_start) % 4]
        print(byte)
        output_bytes.append(byte)

    print(bytes(output_bytes).decode('windows-1252'))

data = {0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a}

unmask(data)
