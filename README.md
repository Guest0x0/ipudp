# tunneling IP over UDP, with encryption and random padding

## MAINTANENCE WARNING
Although the author is very glad to discuss on this project,
fix its problems and make improvements to it,
NO MAINTANENCE OR TECHNICAL SUPPORT IS GUARANTEED.
You are welcomed to open issues/submit PRs,
BUT THERE ARE NO GUARANTEES ON (SWIFT) HANDLING.
If your issue/PR is not handled in time somehow,
you are encouraged to read the source, understand the idea,
and implement your own version.
That's also the spirit behind the design of `ipudp`.

## Introduction
This tool can be used to hide your traffic and/or pass certain firewalls.
You need a remote machine that is secure and has full internet access.
Both local client and the remote server should run Linux as the operating systems
(although a windows client is possible too, theoretically).
Only one client can connect to the server at a time.

## Usage
On the client side, as root or with `CAP_NET_ADMIN`:
```
python main.py -key 64BIT_HEX_KEY -client SERVER_IP:SERVER_PORT -tunnel udp \
    [-auth VARIABLE_LENGTH_AUTHENTICATION_MESSAGE] \
    [-padding PACKET_SMALLER_THAN_THIS_WILL_BE_PADDED] \
    [-mtu MTU_TO_USE_DEFAULT_TO_1500] \
    [-tun THE_NAME_OF_THE_TUN_DEVICE]
```
On the server side, as root or with `CAP_NET_ADMIN`:
```
python main.py -key SAME_KEY_AS_CLIENT -server SERVER_PORT -tunnel udp \
    [-auth SAME_AUTH_MESSAGE_AS_CLIENT] \
    [-padding PACKET_SMALLER_THAN_THIS_WILL_BE_PADDED] \
    [-mtu MTU_TO_USE_DEFAULT_TO_1500] \
    [-tun THE_NAME_OF_THE_TUN_DEVICE]
```
You must turn off reverse path filtering on your server system,
and make sure that the `SERVER_PORT` is open.

You should see traffic statistics every 5 seconds, on both sides,
if `ipudp` is running normally.

## Overview of Design
`ipudp` works as follows:
```
 __________ Local Machine _________      ______________       __________ Remote Server ___________
|                                  |     |  firewall  |      |                                    |
| applications             |--UDP--|-----|------------|------|-UDP--> script                   |--|-----> target
|      |                   |       |     |(encrypted  |      |          |                      |  |
|      | routing           |encrypt|     |UDP traffic)|      |  decrypt |           MASQUERADE |  |
|      V                   |       |     |            |      |          V                      |  |
| TUN virtual device --> script    |     |            |      |  TUN virutal device --iptables--|  |
|__________________________________|     |____________|      |____________________________________|
```
(and vice versa)

The "imaginary enemy" of this tool are advanced firewalls with the capability of
deep packet inspection (DPI), traffic pattern analysis, or even active sniffing.

Here are some details about the design space of `ipudp`:

- the use of TUN virtual device means any IP traffic can be tunneled by `ipudp`,
including TCP, UDP, or even ICMP, without the need to configure applications.
But it also means that only one client can connect to the remote server at a time,
as port mapping is impossible at the Networking Layer.

- The protocol for communication between client and server is UDP.
As the connectionless property of UDP can reduce tunneling overhead.
However, other protocols are possible, too.
Again, the tunneling part is designed to be modular.
When UDP is not the best option,
switching to other protocols like TCP or ICMP should be easy.

- Instead of using complicated ciphers like AES, TLS, etc.. `ipudp` uses a very simple
reactive (stream cipher with key stream dependent on all previous plaintext bytes as well)
cipher. This cipher is undoubtedly uncomparable to well-tested industrial ciphers.
However, the point is, for any ciphers, once widely used, even if the firewall can't
decrypt ciphertext directly, discovering the underlying cipher via various methods,
such as machine learning, is possible. However, if every individual user uses a simple
but unique cipher, it would be impossible to discover the pattern.
The crypto part of `ipudp` (`crypto.py`) is designed in such a way,
that one can easily implement a different cipher.
That's also the encouraged way to use this tool.
Just take it as a cryptographic mind-storming ;)

- To avoid traffic pattern analysis (usually based on packet size),
`ipudp` offers optional random padding to packages.

- To act against active sniffing, `ipudp` offers simple authentication mechanism.
Client and server should pre-share a variable length authentication message,
and that message would appear in every UDP packet.
Packets that fail to authenticate will be ignored by the server,
as if the server is not responsive.
While this authentication method introduces more traffic overhead,
it completely eliminates the traffic pattern of hand-shaking.
Smarter authentication methods can be integrated easily, of course.

In general, `ipudp` does not try to be general, or make the best decision everywhere.
Instead, it tries to be a framework which allow various design options to be altered easily.
So you are highly encouraged to read and modify the (very short) code to make it suit your need better.
The ultimate idea is,
one mono protocol is still possible to crack, no matter how robust it is.
But it is impossible to crack hundreds, or even thousands of potentially broken,
but different protocols.

## Function of Files
- `tun.py`:
interface to TUN virtual devices.
- `crypto.py`:
cryptographic stuffs.
If you want to use an alternative cipher, simply modify the methods
of the `Encrypter` and `Decrypter` classes. The interface is as follows:
```
# class Encrypter
__init__(self, key): initializer
reset(self):
    Reset the state of the cipher. Used for stateful (stream) ciphers

encrypt(self, data):
    copy and return an encrypted version of [data].
    You don't need to modify this, as it is derived from [encrypt_in_place].
    
encrypt_in_place(self, data):
    [data] being a mutable bytes-compatible object,
    encrypt [data] in place.

# class Decrypter
__init__(self, key): initializer

reset(self):
    Reset the state of the cipher. Used for stateful (stream) ciphers

decrypt(self, data):
    copy and return an decrypted version of [data].
    You don't need to modify this, as it is derived from [encrypt_in_place].
    
decrypt_in_place(self, data):
    [data] being a mutable bytes-compatible object,
    decrypt [data] in place.
```
- `logger.py`:
For logging facilities.
Modify this if not satisfied with the UI.
Interface:
```
# class Logger:
__init__(self, freq, target=sys.stdout):
    [freq] is the frequency to log traffic, in seconds.
    [target] is where the logger logs to

log(self, msg):
    Output [msg]. Should output unconditionally.

log_traffic(self):
    Output current traffic statistics. Should only output after at least
    [freq] seconds since the last output of traffic.

add_traffic(self, mode, size):
    [mode] is 'i' for inbound traffic or 'o' for outbound traffic.
    [size] is the size of new traffic, in bytes.
    Should call [log_traffic] to flush the changes.
```
- `udp.py`:
Implementation of the UDP tunnel.
Check this if you want to implement an alternative authentication method
or padding strategy.
Interface:
```
# class UDPTun
__init__(
    self,
    mode, # 'c' for client side, 's' for server side
    addr, # (server_ip, server_port) pair for client side, ("", port) for server side
    encrypter, decrypter, # with the interface described above
    auth_msg, MTU,
    padding_threshold, # the [-padding] option if presents, or None
    padding_range, # a pair of int, specifying the range of the payload size of padded packets
    logger # as described above
): initializer

socket:
    The socket used for the tunnel.
    A possible improvement would be to make the whole class selectors-compatible.

send(self, data): Send data over the tunnel. len(data) < self.MTU.
    Should handle insertion of authentication message, encryption, and padding
    
recv(self): Block and return the next received packet.
    Should handle verification of authentication message, decryption, and unpadding
```
- `client.sh`:
Client initialization script.
Would be called after the intialization of TUN device and the tunnel class.
Make the TUN virtual device up,
assign an IP address to it,
and configure the routing rules of client system
to redirect all traffics to the TUN virtual device.
Available environment variables:
```
$TUN_NAME: name of the TUN virtual device
$REMOTE_IP: IP of server
$REMOTE_PORT: target port on server
```
- `client-cleanup.sh`:
Would be called on exit of `ipudp` at client side.
Should restore the originally routing rules of the client system.
With the same set of available environment variables as `client.sh`
- `server.sh`:
Server initialization script.
Would be called after the intialization of TUN device and the tunnel class.
Make the TUN virtual device up,
assign an IP address to it,
enable IP forwarding on the server,
and configure iptables rules for IP Masquerade.
Available environment variables:
```
$TUN_NAME: name of the TUN virtual device
$LISTEN_PORT: the port which the server listens on
```
- `server-cleanup.sh`:
Called on server side exit of `ipudp`.
Should delete the Masquerade rule.
With the same set of available environment variables as `server.sh`
- `main.py`:
Entry point. Pretty much just combines the above scripts.

## Inspirations
[icmptunnel](https://github.com/dhavalkapil/icmptunnel)

## License
WTFPL
