
import struct

# Python has variable length integers (and without a full-featured, fixed-length one,
# AFAIK), so manually keep length of integer 64 bits via modula operation.
INT64_MAX = (65536 * 65536) ** 2

class Encrypter:
    def __init__(self, key):
        self.init_key = key
        self.key = key

    def reset(self):
        self.key = self.init_key

    def encrypt(self, data):
        result = bytearray(data)
        self.encrypt_in_place(result)
        return result

    def encrypt_in_place(self, data):
        i = 0
        while i < len(data):
            if i + 8 <= len(data):
                frag = data[i:i+8]
                frag_len = 8
            else:
                frag = data[i:]
                frag.extend(bytearray(i + 8 - len(data)))
                frag_len = len(data) - i

            frag_int = struct.unpack('Q', frag)[0]
            dest_int = (frag_int ^ self.key) % INT64_MAX
            data[i:i+frag_len] = struct.pack('Q', dest_int)[0:frag_len]
            self.key = (frag_int + self.key) ** 3 % INT64_MAX
            i = i + 8

class Decrypter:
    def __init__(self, key):
        self.init_key = key
        self.key = key

    def reset(self):
        self.key = self.init_key

    def decrypt(self, data):
        result = bytearray(data)
        self.decrypt_in_place(result)
        return result

    def decrypt_in_place(self, data):
        i = 0
        while i < len(data):
            if i + 8 <= len(data):
                frag = data[i:i+8]
                frag_len = 8
            else:
                frag = data[i:]
                frag.extend(bytearray(i + 8 - len(data)))
                frag_len = len(data) - i

            frag_int = struct.unpack('Q', frag)[0]
            dest_int = (frag_int ^ self.key) % INT64_MAX
            data[i:i+frag_len] = struct.pack('Q', dest_int)[0:frag_len]
            self.key = (dest_int + self.key) ** 3 % INT64_MAX
            i = i + 8
