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

    if outgoing_data is None:
        outgoing_data = ''

    payload = None
    if opcode == OPCODE_TEXT or opcode == OPCODE_CLOSE or opcode == OPCODE_PING or opcode == OPCODE_PONG:
        payload = outgoing_data.encode('utf-8')
    if opcode == OPCODE_BINARY:
        payload = outgoing_data

    # The bytes in the header, no data
    header = b''

    # Adding fin = 1 and RSV = 0 and opcode
    fin_rsv_opcode = FIN + int(hex(opcode), 16)
    header += struct.pack('!B', fin_rsv_opcode)

    # Mask, server does not send masked data
    mask_bit = 0x0

    print('Payload: {}'.format(payload))
    payload_length = len(payload)
    print('Payload length: {}'.format(payload_length))

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
    if not incoming_data:
        raise ValueError('1002 - No data to unmask')

    frame = bytearray(incoming_data)
    print('Frame comes here:')
    print(frame)

    opcode = frame[0] & OPCODE
    fin = frame[0] & FIN

    # Checking if the fin 1 or 0
    if fin != 0x80 and fin != 0:
        raise ValueError('1002 - Fin must be 1 or 0')

    # Checking if the rsv values are 0
    if frame[0] & 0x70 != 0:
        raise ValueError('1002 - RSV values must be 0')

    # Checking for valid opcodes
    if 0x02 < opcode < 0x08 or opcode > 0x0a:
        raise ValueError('1002 - Reserved opcode')

    # Checking if a control frame is fragmented
    if opcode > 0x07 and fin == 0:
        raise ValueError('1002 - A control frame cannot be fragmented')

    # Checking if the masking bit is 1
    if not frame[1] & 128:
        raise ValueError('1002 - Mask bit sent from client must be 1')

    # Using & 127 to omit the first bit, which is the masking bit
    # This gives us the payload length
    length = frame[1] & 127
    print('length in first byte: {}'.format(length))

    # Checking if a control frame is carrying a too large payload
    if opcode > 0x07 and length > 125:
        raise ValueError('1002 - A control frame cannot use extended payload length')

    mask_key_start = 2
    if length == 126:
        mask_key_start = 4
        print('decimal value in second byte: {}'.format(frame[2]))
        print('decimal value in third byte: {}'.format(frame[3]))
        length = (frame[2] << 8) + frame[3]
    elif length == 127:
        mask_key_start = 10
        length = 0
        # Going though every byte in the extended payload length, and adding the decimal values
        j = 7
        for i in range(2, 10):
            print('decimal value of byte {0}: {1}'.format(i, frame[i]))
            length += (frame[i] << (8 * j))
            j -= 1

    print('total length: {}'.format(length))

    # the masking key is always 4 bytes, so the payload is always 4 bytes after where the masking key starts
    data_start = mask_key_start + 4

    try:
        frame[data_start+length-1]
    except IndexError:
        raise ValueError('1002 - Provided length of payload is larger than the actual payload')

    output_bytes = b''
    for i in range(data_start, data_start+length):
        # Using an XOR-operation with the payload and masking key to unmask the payload
        output_bytes += struct.pack('!B', frame[i] ^ frame[mask_key_start + (i - data_start) % 4])

    msg = UnmaskedMessage()
    msg.is_close_fin = frame[0] & FIN == 0

    msg.is_continuation = opcode == OPCODE_CONTINUATION
    msg.is_close = opcode == OPCODE_CLOSE
    msg.is_ping = opcode == OPCODE_PING
    msg.is_pong = opcode == OPCODE_PONG
    msg.is_text = opcode == OPCODE_TEXT
    msg.is_binary = opcode == OPCODE_BINARY

    if msg.is_text:
        msg.return_data = output_bytes.decode('utf-8')
    if msg.is_binary:
        msg.return_data = output_bytes

    return msg


if __name__ == '__main__':

    # data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]
    #
    # print(unmask(data))

    # data = build_frame('X?P=Uøåæ%46&D%^?jQL!srQS!kæøåe9K-$5KUFd4jJKK6jdvøå3Yp!=4cR4F!cC+E6Y!Vøåæøåæ'
    #                   'wdL5@2!6kwcrøåæ*79pUJv?8B=*KWzC+PZxtøæå7&8m56w!TQqy6BDec#qVTkJQFBj_4U$Hhæøå', OPCODE_TEXT)
    data = build_frame('☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭'
                       '☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭☭a', OPCODE_TEXT)

    print(data)

    print('---------')

    # print(unmask(data).return_data)

    print(unmask(b''))
