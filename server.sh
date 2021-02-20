#!/bin/sh

ifconfig $TUN_NAME up 10.0.1.0/24

echo 1 | dd of=/proc/sys/net/ipv4/ip_forward

iptables -t nat -A POSTROUTING -m comment --comment "ipudp" -j MASQUERADE -s 10.0.1.0/24
