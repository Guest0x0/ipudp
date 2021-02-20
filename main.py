
import sys
import signal
import os
import subprocess
import selectors

import importlib
logger = importlib.import_module("logger")
tun = importlib.import_module("tun")
crypto = importlib.import_module("crypto")
udp = importlib.import_module("udp")

tun_name = ""

mode = None
addr = None

key = None
auth_msg = b"Infinite Socks Auth"

tunnel_type = None
MTU = 1000
padding_threshold = None
padding_range = None

i = 1
while i < len(sys.argv):
    if sys.argv[i] == '-tun':
        i = i + 1
        tun_name = sys.argv[i]
    elif sys.argv[i] == '-client':
        mode = 'c'
        i = i + 1
        ip_and_port = sys.argv[i].split(sep=':', maxsplit=2)
        addr = (ip_and_port[0], int(ip_and_port[1], 10))
    elif sys.argv[i] == '-server':
        mode = 's'
        i = i + 1
        addr = ("", int(sys.argv[i], 10))
    elif sys.argv[i] == '-key':
        i = i + 1
        key = int(sys.argv[i], 16)
    elif sys.argv[i] == '-auth':
        i = i + 1
        auth_msg = bytes(sys.argv[i])
    elif sys.argv[i] == '-tunnel':
        i = i + 1
        tunnel_type = sys.argv[i]
    elif sys.argv[i] == '-mtu':
        i = i + 1
        MTU = int(sys.argv[i], 10)
    elif sys.argv[i] == '-padding':
        i = i + 1
        padding_threshold = int(sys.argv[i], 10)
        padding_range = (padding_threshold, padding_threshold + 200)
    else:
        raise Exception("unknown option " + sys.argv[i])
    i = i + 1

if mode is None:
    print("no mode specified")
    exit(1)
elif key is None:
    print("so key specified")
    exit(1)
elif tunnel_type is None:
    print("no tunnel type specified")
    exit(1)
elif tunnel_type == 'udp':
    tunnel = udp.UDPTun(
        mode, addr,
        crypto.Encrypter(key), crypto.Decrypter(key), auth_msg,
        MTU,
        padding_threshold, padding_range,
        logger.Logger(5)
    )
else:
    print("unknown tunnel type", tunnel_type)
    exit(1)

tun = tun.Tun(tun_name)
os.putenv("TUN_NAME", tun.name)
if mode == 'c':
    os.putenv("REMOTE_IP", addr[0])
    os.putenv("REMOTE_PORT", str(addr[1]))
    subprocess.run(["./client.sh"])
else:
    os.putenv("LISTEN_PORT", str(addr[1]))
    subprocess.run(["./server.sh"])

def cleanup(signal, frame):
    if mode == 'c':
        subprocess.run(["./client-cleanup.sh"])
    else:
        subprocess.run(["./server-cleanup.sh"])
    exit(0)

for sig in [ signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM ]:
    signal.signal(sig, cleanup)

sel = selectors.DefaultSelector()
sel.register(tun.fd, selectors.EVENT_READ, 0)
sel.register(tunnel.socket, selectors.EVENT_READ, 1)

while True:
    for (skey, mask) in sel.select():
        if skey.data == 0:
            data = os.read(tun.fd, MTU)
            tunnel.send(data)
        elif skey.data == 1:
            data = tunnel.recv()
            os.write(tun.fd, data)
