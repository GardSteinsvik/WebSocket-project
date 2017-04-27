# -*- coding: utf-8 -*-
import struct

FIN = b'\x81'
OPCODE_CONTINUATION = b'\x81'
OPCODE_TEXT = b'\x01'
OPCODE_BINARY = b'\x02'
OPCODE_CLOSE = b'\x08'
OPCODE_PING = b'\x09'
OPCODE_PONG = b'\x0a'

"""
      0       1       2       3       4       5       6       7
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-------+-+-------------+-------------------------------+
     |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
     |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
     |N|V|V|V|       |S|             |   (if payload len==126/127)   |
     | |1|2|3|       |K|             |                               |
     +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
     |     Extended payload length continued, if payload len == 127  |
     + - - - - - - - - - - - - - - - +-------------------------------+
     |                               |Masking-key, if MASK set to 1  |
     +-------------------------------+-------------------------------+
     | Masking-key (continued)       |          Payload Data         |
     +-------------------------------- - - - - - - - - - - - - - - - +
     :                     Payload Data continued ...                :
     + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
     |                     Payload Data continued ...                |
     +---------------------------------------------------------------+
"""


def build_frame(data, opcode=OPCODE_CONTINUATION, masking_key=None):

    payload = data.encode('utf-8')

    # The bytes in the header, no data
    header = b''

    # Adding fin and RSV1 2 & 3 = 0
    header += FIN

    # Opcode
    header += opcode

    # Mask
    if masking_key:
        # first bit of the byte
        mask_bit = 0x80
    else:
        mask_bit = 0x0

    payload_length = len(payload)

    if payload_length < 126:
        # Creates a byte with mask_bit first
        # !B = 1 byte
        header += struct.pack('!B', (mask_bit | payload_length))
    elif payload_length < (2 ** 16):
        # !H = 2
        header += struct.pack('!B', (mask_bit | 126)) + struct.pack('!H', payload_length)
    else:
        # !Q = 8 byte
        header += struct.pack('!B', (mask_bit | 127)) + struct.pack('!Q', payload_length)

    if not masking_key:
        return bytes(header + payload)

    return bytes(header + masking_key + mask(payload, masking_key))


def mask(data, masking_key):
    masked = bytearray(data)
    key = bytearray(masking_key)
    for i in range(len(data)):
        masked[i] = masked[i] ^ key[i % 4]
    return bytes(masked)


def unmask(data):
    frame = bytearray(data)
    print(frame)

    length = frame[2] & 127
    print('length: ' + str(length))

    # TODO fix umasking, bruker feil indexer

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

data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]

print(type(data[0]))

data = build_frame('test')

print(data)

print(unmask(data))


