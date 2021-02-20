#!/bin/sh

default_rt=$(route -n | grep "^$REMOTE_IP")
gw=$(echo $default_rt | awk '{ print $2 }')
if [ "$gw" != "0.0.0.0" ]; then
    gw="gw $gw"
else
    gw=""
fi
dev=$(echo $default_rt | awk '{ printf("dev %s", $8) }')

route del -host $REMOTE_IP
route del default
route add default $gw $dev
