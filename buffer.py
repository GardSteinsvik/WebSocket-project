import frame_handler


class Buffer:

    def __init__(self, is_text):
        self.data = ''
        if is_text:
            self.datatype = frame_handler.OPCODE_TEXT
        else:
            self.datatype = frame_handler.OPCODE_BINARY

    def append(self, data):
        if data:
            self.data += data

    def get_data(self):
        d = self.data
        self.data = ''
        return d
