#!/bin/bash
i=1
while [ $i -le 1 ]
do
    mkdir -p ./test/file_$i
    nohup python /home/ubuntu/icn_dss_dns_load_test.py -u http://cms.dssaas.mcndemo.org/WebAppDSS/display/listContents?id=COSTUME_ID -t 0.5 -f ./test/file_$i &
    (( i++ ))
done