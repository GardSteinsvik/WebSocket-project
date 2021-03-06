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


def build_frame(outgoing_data, opcode, data_type=OPCODE_TEXT):
    """
    Builds a frame for the server to send
    :param outgoing_data: The payload of the frame 
    :param opcode: The opcode of the frame
    :param data_type: The data type of the payload. This is always None, OPCODE_TEXT or OPCODE_BINARY.
    It is used to tell the builder the data type if the opcode is OPCODE_CONTINUATION, so that it can encode it properly
    :return: a frame supporting RFC6455
    """
    if opcode == OPCODE_BINARY and not data_type == OPCODE_BINARY:
        raise ValueError('1007 - Invalid frame, opcode is binary data, but the specified data type is not binary data')

    if outgoing_data is None:
        outgoing_data = ''

    payload = outgoing_data

    if not data_type == OPCODE_BINARY:
        payload = outgoing_data.encode('utf-8')

    # The bytes in the header, no data
    header = b''

    # Adding fin = 1 and RSV = 0 and opcode
    fin_rsv_opcode = FIN + int(hex(opcode), 16)
    header += struct.pack('!B', fin_rsv_opcode)

    # Mask, server does not send masked data
    mask_bit = 0x0

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

    return header + payload


def unmask(incoming_frame, data_type=None):
    """
    This method interprets a frame and unmasks the payload
    :param incoming_frame: A string of text, or bytes object b''
    :param data_type: Specifies data type if opcode is OPCODE_CONTINUATION. It is None otherwise.
    :return: An UnmaskedMessage object containing the frame properties and the payload.
    The payload is formatted as a string of decoded text or bytes object with decoded bytes
    """
    if not incoming_frame:
        raise ValueError('1002 - No frame to unmask')

    frame = bytearray(incoming_frame)

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

    # Checking if specified data type is stated if it is a continuation frame
    if opcode == OPCODE_CONTINUATION and data_type is None:
        raise ValueError('Internal unmasking error: Opcode is continuation, but there is no provided data type.')

    # Checking if a control frame is fragmented
    if opcode > 0x07 and fin == 0:
        raise ValueError('1002 - A control frame cannot be fragmented')

    # Checking if the masking bit is 1
    if not frame[1] & 128:
        raise ValueError('1002 - Mask bit sent from client must be 1')

    # Using & 127 to omit the first bit, which is the masking bit
    initial_length = frame[1] & 127

    # Checking if a control frame is carrying a too large payload
    if opcode > 0x07 and initial_length > 125:
        raise ValueError('1002 - A control frame cannot use extended payload length')

    payload_length = initial_length
    mask_key_start = 2
    if initial_length == 126:
        mask_key_start = 4
        payload_length = (frame[2] << 8) + frame[3]
    elif initial_length == 127:
        mask_key_start = 10
        payload_length = 0
        # Going though every byte in the extended payload length, and adding the decimal values
        j = 7
        for i in range(2, 10):
            payload_length += (frame[i] << (8 * j))
            j -= 1

    # the masking key is always 4 bytes, so the payload is always 4 bytes after where the masking key starts
    data_start = mask_key_start + 4

    output_bytes = b''
    for i in range(data_start, data_start+payload_length):
        # Using an XOR-operation with the payload and masking key to unmask the payload
        output_bytes += struct.pack('!B', frame[i] ^ frame[mask_key_start + (i - data_start) % 4])

    msg = UnmaskedMessage()
    msg.is_close_fin = frame[0] & FIN != 0

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

    data = build_frame('X?P=Uøåæ%46&D%^?jQL!srQS!kæøåe9K-$5KUFd4jJKK6jdvøå3Yp!=4cR4F!cC+E6Y!Vøåæøåæ'
                       'wdL5@2!6kwcrøåæ*79pUJv?8B=*KWzC+PZxtøæå7&8m56w!TQqy6BDec#qVTkJQFBj_4U$Hhæøå'
                       , OPCODE_TEXT, OPCODE_TEXT)

    print(data)

    print('---------')

    data = [0x81, 0x83, 0xb4, 0xb5, 0x03, 0x2a, 0xdc, 0xd0, 0x6a]

    print(unmask(data).return_data)
