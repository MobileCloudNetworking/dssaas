#!/bin/bash
################################################################################################################################################################################################
# How to call it:                                                                                                                                                                              #
# run.sh <Number of concurrent players> <ICN service endpoint> <Player ID> <ICN desired interest count> <DNS service forwarder endpoint> <DNS service desired QPS> <DSS loadbalancer endpoint> #
# Example:                                                                                                                                                                                     #
# Having 10 concurrent players                                                                                                                                                                 #
# Sending 50 interests per minute toward ICN                                                                                                                                                   #
# Sending 20 Queries per second toward DNS                                                                                                                                                     #
# Using player ID 1                                                                                                                                                                            #
# sudo ./run_test.sh 10 http://130.92.70.252:5000 1 50 130.92.70.248 20 160.85.4.35                                                                                                            #
################################################################################################################################################################################################
if [ "$#" -ne 7 ]; then
    echo "Check number of parameters"
    exit 1
fi

execution_count="$1"
icn_api="$2"
player_id="$3"
interest_count="$4"
dns_forwarder="$5"
dns_qps="$6"
dss_ep="$7"

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
    n=$RANDOM
    sleep 0.$(( n %= 100 ))
    nohup python /home/ubuntu/icn_dss_dns_load_test_2.py -u http://dashboard.dssaas.mcn.com:8080/WebAppDSS/display/listContents?id=$player_id -e $dss_ep -i $icn_api -c $interest_count -f ./mcn_test/file_$i/ -q $dns_qps  &> ./mcn_test/log_$i.txt &
    sleep 0.$(( 100 - ( n %= 100 ) ))
    (( i++ ))
done