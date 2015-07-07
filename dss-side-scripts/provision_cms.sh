#!/bin/bash
if [ "$#" -ne 10 ]; then
    exit 1
fi
cd /home/ubuntu/
#Static data, to be removed
databasename="$1"
databaseusername="$2"
databasehost="$3"
databasepassword="$4"
dssmcrapiurl="$5"
servicecdnenabled="$6"
dssopenamendpoint="$7"
serviceicnenabled="$8"
serviceaaaenabled="$9"
dssmcrhostname="${10}"
dssmcrapiport='80'
dssmcrapisuperadmin='sysadmin'
dssmcrapisuperadminpassword='sysadmin2014'
dssmcrapiloginurl='/api/authentications/login'
dssmcrapicontentmanagementurl='/api/contents'
dssmcrapiusermanagementurl='/api/users'
sed -i.bak "s,Hostname=,#Hostname=,g" /etc/zabbix/zabbix_agentd.conf
#Autoconf
sed -i.bak "s,SERVICEICNENABLED,$serviceicnenabled,g" WebAppDSSConfig.groovy
sed -i.bak "s,SERVICECDNENABLED,$servicecdnenabled,g" WebAppDSSConfig.groovy
sed -i.bak "s,SERVICEAAAENABLED,$serviceaaaenabled,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSCSDBNAME,$databasename,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSCSDBSERVERURL,$databasehost,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSCSDBUSERNAME,$databaseusername,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSCSDBPASSWORD,$databasepassword,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPIURL,$dssmcrapiurl,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPIPORT,$dssmcrapiport,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPISUPERADMINUSER,$dssmcrapisuperadmin," WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPISUPERADMINPASSWORD,$dssmcrapisuperadminpassword,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPILOGINURL,$dssmcrapiloginurl,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPICONTENTMANAGEMENTURL,$dssmcrapicontentmanagementurl,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRAPIUSERMANAGEMENTURL,$dssmcrapiusermanagementurl,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSOPENAMENDPOINT,$dssopenamendpoint,g" WebAppDSSConfig.groovy
sed -i.bak "s,DSSMCRHOSTNAME,$dssmcrhostname,g" SLAmgr.py
if [[ $serviceaaaenabled == "false" ]]
then
    # Disabling web policy agent
    sed -i.bak "s,include,#include,g" /usr/local/apache2/conf/httpd.conf
fi
cp WebAppDSSConfig.groovy /usr/share/tomcat7/
cp WebAppDSS.war /var/lib/tomcat7/webapps/
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
service mysla restart
service zabbix-agent restart
service tomcat7 restart
service apache2 restart
exit 0