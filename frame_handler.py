# -*- coding: utf-8 -*-
import struct

from unmasked_message import UnmaskedMessage

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

FIN = 0x80
OPCODE = 0x0f
OPCODE_CONTINUATION = 0x00
OPCODE_TEXT = 0x01
OPCODE_BINARY = 0x02
OPCODE_CLOSE = 0x08
OPCODE_PING = 0x09
OPCODE_PONG = 0x0a


def build_frame(outgoing_data, opcode=OPCODE_CONTINUATION):
    print('BUILDING FRAME')

    payload = None
    if opcode == OPCODE_TEXT or opcode == OPCODE_BINARY or opcode == OPCODE_CONTINUATION:
        payload = outgoing_data.encode('utf-8')

    # The bytes in the header, no data
    header = b''

    # Adding fin = 1 and RSV = 0 and opcode
    fin_rsv_opcode = FIN + int(hex(opcode), 16)
    header += struct.pack('!B', fin_rsv_opcode)

    # Mask, server does not send masked data
    mask_bit = 0x0

    print(payload)
    payload_length = len(payload)

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

    return header + payload


def unmask(incoming_data):
    print('UNMASKING')
    frame = bytearray(incoming_data)
    print('Frame comes here:')
    print(frame)

    # Using & 127 to omit the first bit, which is the masking bit
    # This gives us the payload length
    length = frame[1] & 127
    print('length in first byte: {}'.format(length))

    mask_key_start = 2
    if length == 126:
        mask_key_start = 4
        print('length in second byte: {}'.format(frame[2]))
        print('length in third byte: {}'.format(frame[3]))
        length = (frame[2] + frame[3])
    elif length == 127:
        mask_key_start = 10
        length = 0
        for i in range(2, 10):
            print('length of byte {0}: {1}'.format(i, frame[i]))
            length += frame[i]

    print('total length: {}'.format(length))

    # the masking key is always 4 bytes, so the payload is always 4 bytes after where the masking key starts
    data_start = mask_key_start + 4

    output_bytes = []
    for i in range(data_start, data_start+length):
        # Using an XOR-operation with the payload and masking key to unmask the payload
        byte = frame[i] ^ frame[mask_key_start + (i - data_start) % 4]
        output_bytes.append(byte)

    print('Output bytes: {}'.format(output_bytes))

    msg = UnmaskedMessage()
    msg.is_close_fin = frame[0] & FIN == 0

    opcode = frame[0] & OPCODE
    msg.is_continuation = opcode == OPCODE_CONTINUATION
    msg.is_close = opcode == OPCODE_CLOSE
    msg.is_ping = opcode == OPCODE_PING
    msg.is_pong = opcode == OPCODE_PONG
    msg.is_text = opcode == OPCODE_TEXT
    msg.is_binary = opcode == OPCODE_BINARY

    if msg.is_text:
        msg.return_data = "".join(map(chr, output_bytes))
    if msg.is_binary:
        msg.return_data = output_bytes

    return msg


if __name__ == '__main__':

    data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]

    print(unmask(data))

    print('---------')

    # data = build_frame('X?P=U%46&D%^?jQL!srQS!ke9K-$5KUFd4jJKK6jdv3Yp!=4cR4F!cC+E6Y!VwdL5@2!6kwcr*79pUJv?8B=*KWzC+PZxt7&8m56w!TQqy6BDec#qVTkJQFBj_4U$Hhæøå', OPCODE_TEXT)
    # data = build_frame('☭☭☭☭', OPCODE_TEXT)
    data = build_frame('æøå', OPCODE_TEXT)
    print(data)

    print('---------')

    print(unmask(data).return_data)
