
import socket
import struct
import random

class UDPTun:
    def __init__(
        self,
        mode, addr,
        encrypter, decrypter, auth_msg,
        MTU,
        padding_threshold, padding_range,
        logger
    ):
        self.mode = mode
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.encrypter = encrypter
        self.decrypter = decrypter
        self.auth_msg = auth_msg
        self.MTU = MTU
        self.padding_threshold = padding_threshold
        self.padding_range = padding_range
        self.logger = logger

        if mode == 'c':
            self.remote_addr = addr
        elif mode == 's':
            self.remote_addr = None
            self.socket.bind(addr)
        else:
            raise Exception("unknown mode" + mode)

    def send(self, data):
        if self.remote_addr is not None:
            if self.padding_threshold is not None and len(data) < self.padding_threshold:
                data_size = random.randint(self.padding_range[0], self.padding_range[1])
            else:
                data_size = len(data)

            msg = bytearray(data_size + len(self.auth_msg) + 2)
            msg[0:len(self.auth_msg)] = self.auth_msg
            msg[len(self.auth_msg):len(self.auth_msg)+2] = struct.pack('H', len(data))
            msg[len(self.auth_msg)+2:len(self.auth_msg)+2+len(data)] = data

            self.encrypter.reset()
            self.encrypter.encrypt_in_place(msg)

            self.socket.sendto(msg, self.remote_addr)

            self.logger.add_traffic('o', len(msg))

    def recv(self):
        msg, self.remote_addr = self.socket.recvfrom(self.MTU + len(self.auth_msg) + 2)

        self.decrypter.reset()
        msg = self.decrypter.decrypt(msg)

        if msg[0:len(self.auth_msg)] == self.auth_msg:
            data_size = struct.unpack('H', msg[len(self.auth_msg):len(self.auth_msg)+2])[0]
            self.logger.add_traffic('i', len(msg))
            return msg[len(self.auth_msg)+2:len(self.auth_msg)+2+data_size]
        else:
            self.logger.log("authentication failure from " + str(self.remote_addr))
            return None
