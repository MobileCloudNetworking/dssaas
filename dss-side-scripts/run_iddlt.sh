#!/bin/bash
if [ "$#" -ne 4 ]; then
    echo "Check number of parameters"
    exit 1
fi

icn_api="$1"
player_id="$2"
timeout="$3"
dns_forwarder="$4"

echo "nameserver $dns_forwarder" >> /etc/resolvconf/resolv.conf.d/head
resolvconf -u
export CCND_CAP=0
/home/ubuntu/ccnxdir/bin/ccndstart &
sleep 10

i=1
while [ $i -le 10 ]
do
    mkdir -p /home/ubuntu/test/file_$i
    nohup python /home/ubuntu/icn_dss_dns_load_test.py -u http://dashboard.dssaas.mcn.com:8080/WebAppDSS/display/listContents?id=$player_id -i $icn_api -t $timeout -f ./test/file_$i &
    (( i++ ))
done