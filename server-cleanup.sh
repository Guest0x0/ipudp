#!/bin/sh

iptables -t nat -D POSTROUTING -m comment --comment "gfw-udptun" -j MASQUERADE -s 10.0.1.0/24
