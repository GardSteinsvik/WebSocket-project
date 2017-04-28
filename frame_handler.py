# -*- coding: utf-8 -*-
import struct

OPCODE_CONTINUATION = 0x81
OPCODE_TEXT = 0x01
OPCODE_BINARY = 0x02
OPCODE_CLOSE = 0x08
OPCODE_PING = 0x09
OPCODE_PONG = 0x0a

"""
indx  0               1               2               3
      0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-------+-+-------------+-------------------------------+
     |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
     |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
     |N|V|V|V|       |S|             |   (if payload len==126/127)   |
     | |1|2|3|       |K|             |                               |
     +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
indx  4               5               6               7
     +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
     |     Extended payload length continued, if payload len == 127  |
     + - - - - - - - - - - - - - - - +-------------------------------+
indx  8               9               10              11
     + - - - - - - - - - - - - - - - +-------------------------------+
     |                               |Masking-key, if MASK set to 1  |
     +-------------------------------+-------------------------------+
indx  12              13              14              15    
     +-------------------------------+-------------------------------+
     | Masking-key (continued)       |          Payload Data         |
     +-------------------------------- - - - - - - - - - - - - - - - +
     :                     Payload Data continued ...                :
     + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
     |                     Payload Data continued ...                |
     +---------------------------------------------------------------+
"""


def build_frame(data, opcode=OPCODE_TEXT):
    payload = data.encode('utf-8')

    # The bytes in the header, no data
    header = b''

    # Adding fin = 1 and RSV = 0 and opcode
    fin_rsv_opcode = 128 + int(hex(opcode), 16)
    header += struct.pack('!B', fin_rsv_opcode)

    # Mask, server does not send masked data
    mask_bit = 0x0

    payload_length = len(data)

    if payload_length < 126:
        # Creates a byte with mask_bit first
        # !B = 1 byte
        header += struct.pack('!B', (mask_bit | payload_length))
    elif payload_length < (2 ** 16):
        # !H = 2 bytes
        header += struct.pack('!B', (mask_bit | 126)) + struct.pack('!H', payload_length)
    else:
        # !Q = 8 bytes
        header += struct.pack('!B', (mask_bit | 127)) + struct.pack('!Q', payload_length)

    # Adding 4 empty bytes to fill the masking key
    header += struct.pack('!L', 0)

    return header+payload


def unmask(data):
    frame = bytearray(data)
    print(frame)

    # Using & 127 to omit the first bit, which is the masking bit
    # This gives us the payload length
    length = frame[1] & 127
    print('length: ' + str(length))

    mask_key_start = 2
    if length == 126:
        mask_key_start = 4
    elif length == 127:
        mask_key_start = 10

    # the masking key is always 4 bytes, so the payload is always 4 bytes after where the masking key starts
    data_start = mask_key_start + 4

    output_bytes = []
    for i in range(data_start, data_start+length):
        # Using an XOR-operation with the payload and masking key to unmask the payload
        byte = frame[i] ^ frame[mask_key_start + (i - data_start) % 4]
        output_bytes.append(byte)

    return "".join(map(chr, output_bytes))

if __name__ == '__main__':

    data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]

    print(unmask(data))

    print('---------')

    data = build_frame('test')
    print(data)

    print('---------')

    print(unmask(data))
