#!/bin/sh

ifconfig $TUN_NAME up 10.0.1.1/24 || exit 1

default_rt=$(route -n | grep "^0.0.0.0")
if [ "x$default_rt" = "x" ]; then
    echo "failed to obtain default route table"
    exit 1
fi

gw=$(echo $default_rt | awk '{ print $2 }')
if [ "$gw" != "0.0.0.0" ]; then
    gw="gw $gw"
else
    gw=""
fi
dev=$(echo $default_rt | awk '{ printf("dev %s", $8) }')
route add -host $REMOTE_IP $gw $dev
route del default
route add default gw 10.0.1.1 dev $TUN_NAME
