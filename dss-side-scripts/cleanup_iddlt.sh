#!/bin/bash
kill `ps aux | grep icn_dss_dns_load_test.py | grep -v grep | awk '{print $2}'`
mv /etc/resolvconf/resolv.conf.d/head.bak /etc/resolvconf/resolv.conf.d/head
mv /etc/resolv.conf.bak /etc/resolv.conf
resolvconf -u
export CCND_CAP=
/home/ubuntu/ccnxdir/bin/ccndstop