
import fcntl
import struct
import os

TUN_CLONE_DEVS = [ "/dev/net/tun", "/dev/tun" ]

# constants
IFNAMESIZE = 16
TUNSETIFF = 0x400454ca
IFF_NO_PI = 0x1000
IFF_TUN = 0x0001

class Tun:
    def __init__(self, name):
        self.fd = -1
        for clone_dev in TUN_CLONE_DEVS:
            try:
                self.fd = os.open(clone_dev, os.O_RDWR)
                break
            except Exception:
                pass
        if self.fd < 0:
            raise Exception("failed to open TUN clone device")

        if len(name) > IFNAMESIZE:
            raise Exception("name for TUN device too long")
        ifreq = struct.pack("16sH", bytes(name, 'utf-8'), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self.fd, TUNSETIFF, ifreq)

        self.name = struct.unpack("16sH", ifreq)[0].partition(b'\0')[0].decode('utf-8')
