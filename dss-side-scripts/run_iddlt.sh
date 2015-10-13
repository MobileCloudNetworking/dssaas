#!/bin/bash
i=1
while [ $i -le 1 ]
do
    mkdir -p ./test/file_$i
    nohup python /home/ubuntu/icn_getcontents.py http://cms.dssaas.mcndemo.org/WebAppDSS/display/listContents?id=COSTUME_ID ./test/file_$i &
    (( i++ ))
done