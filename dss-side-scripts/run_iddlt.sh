#!/bin/bash
if [ "$#" -ne 5 ]; then
    echo "Check number of parameters"
    exit 1
fi

execution_count="$1"
icn_api="$2"
player_id="$3"
interest_count="$4"
dns_forwarder="$5"

cp /etc/resolvconf/resolv.conf.d/head /etc/resolvconf/resolv.conf.d/head.bak
echo "nameserver $dns_forwarder" >> /etc/resolvconf/resolv.conf.d/head
resolvconf -u
export CCND_CAP=0
/home/ubuntu/ccnxdir/bin/ccndstart &
sleep 10

i=1
while [ $i -le $(eval echo $execution_count) ]
do
    mkdir -p /home/ubuntu/mcn_test/file_$i
    nohup python /home/ubuntu/icn_dss_dns_load_test.py -u http://dashboard.dssaas.mcn.com:8080/WebAppDSS/display/listContents?id=$player_id -i $icn_api -c $interest_count -f ./mcn_test/file_$i &
    (( i++ ))
done