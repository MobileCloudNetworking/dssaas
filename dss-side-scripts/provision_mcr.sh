#!/bin/bash
if [ "$#" -ne 9 ]; then
    exit 1
fi
cd /home/ubuntu/
#Static data, to be removed
mcrapistoragedirectory='/home/ubuntu/files/'
mcrapistorageserverurl="http://$1"
mcrapistorageserverport='80'
mcrapicontentmanagementurl='/api/contents'
databasename="$2"
databaseusername="$3"
databasehost="$4"
databasepassword="$5"
corsalloworiginregex="$6"
servicecdnenabled="$7"
serviceicnenabled="$8"
icnport="$9"
corsurlpattern="/api/contents/\*"
echo $4 > /home/ubuntu/dbhost
sed -i.bak "s,Hostname=,#Hostname=,g" /etc/zabbix/zabbix_agentd.conf
#Autoconf
sed -i.bak "s,SERVICECDNENABLED,$servicecdnenabled,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,MCRAPISTORAGEDIRECTORY,$mcrapistoragedirectory,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,MCRAPISTORAGESERVERURL,$mcrapistorageserverurl,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,MCRAPISTORAGESERVERPORT,$mcrapistorageserverport,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,MCRAPICONTENTMANAGEMENTURL,$mcrapicontentmanagementurl,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,DSSMCRAPIDBSERVERURL,$databasehost,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,DSSMCRAPIDBNAME,$databasename,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,DSSMCRAPIDBUSERNAME,$databaseusername,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,DSSMCRAPIDBPASSWORD,$databasepassword,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,MCRAPICONTENTMANAGEMENTPATTERN,$corsurlpattern,g" DSSMCRAPIConfig.groovy
sed -i.bak "s,DSSCMSSERVER,$corsalloworiginregex,g" DSSMCRAPIConfig.groovy
cp DSSMCRAPIConfig.groovy /usr/share/tomcat7/
cp DSSMCRAPI.war /var/lib/tomcat7/webapps/
if [[ $serviceicnenabled == "true" ]]
then
    nohup /home/ubuntu/ccnxdir/bin/ccnd &
    #nohup /home/ubuntu/ccnxdir/bin/ccnr &
    #nohup python /home/ubuntu/addicnroutes.py $databasehost $databaseusername $databasepassword $databasename $icnport &
    #nohup python icn_putcontents.py &
fi

#Create db if required
# Check database aaS is already there
while [[ `echo "status" | mysql -h $databasehost -u $databaseusername -p$databasepassword | grep Uptime` != *Uptime* ]]
do
#It is not ready yet, wait 1 second and try again
	sleep 1
done
if [[ `echo "show schemas;" | mysql -h $databasehost -u $databaseusername -p$databasepassword` != *$databasename* ]]
then
	echo "create database $databasename" | mysql -h $databasehost -u $databaseusername -p$databasepassword
fi
#Start services
service zabbix-agent restart
service tomcat7 restart
service apache2 restart
exit 0
