'''''''''
#Template Generator for scaling purposes 
'''''''''
import string
import random

class TemplateGenerator:
    """
    Sample SO execution part.
    """

    def __init__(self):
        #Later to be filled by asking CC
        self.public_network_id = "d6ce8ab6-1be8-4c85-8067-9c77d7600ffa"
        self.public_sub_network_id = "3a27a222-7d66-4e09-9277-4e26d0b611e3"
        self.private_network_id = "1c98d7e4-5085-4cfd-b21d-4ab2bea1a9dc"
        self.private_sub_network_id = "2d372303-3727-4c8d-b5d5-6c18fdc6cb21"
        
        self.key_name = "bart-key"
        self.cdn_enable = 'false'

        self.dbname = 'webappdss'
        self.dbpass = 'password'
        self.dbuser = 'root'
        
        self.mcr_flavor_idx = 1
        self.minimum_flavor_idx = 1
        self.maximum_flavor_idx = 4
        self.flavor_list = ['m1.tiny','m1.small','m1.medium','m1.large','m1.xlarge']
        
        self.numberOfCmsInstances = 1
        self.cmsCounter = 1
        
        self.baseCmsResourceName = ""
        self.lbNameRandom = ""
    
    def randomNameGenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    def getCmsBaseName(self):
        return "cms" + str(self.cmsCounter) + "_server"
    
    def getBaseCmsTemplate(self):
        self.baseCmsResourceName = self.getCmsBaseName()
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         CMS / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + self.baseCmsResourceName + ':' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: DSS-CMS-IMG' + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : ' + self.baseCmsResourceName + '_port }' + "\n"
        template += '      user_data:' + "\n"
        template += '        Fn::Base64:' + "\n"
        template += '          Fn::Replace:' + "\n"
        template += "          - mcr_srv_ip: { 'Fn::GetAtt' : [mcr_server_floating_ip, floating_ip_address] }" + "\n"
        template += "            dbaas_srv_ip: { 'Fn::GetAtt' : [dbaas_server, first_address] }" + "\n"
        template += '          - |' + "\n"
        template += '            #!/bin/bash' + "\n"
        template += '            cd /home/ubuntu/' + "\n"
        template += '            #Static data, to be removed' + "\n"
        template += "            monaashost='192.168.0.2'" + "\n"
        template += "            databasename='" + self.dbname + "'" + "\n"
        template += "            databaseusername='" + self.dbuser + "'" + "\n"
        template += "            databasehost='dbaas_srv_ip' #localhost" + "\n"
        template += "            databasepassword='" + self.dbpass + "'" + "\n"
        template += "            dssmcrapiurl='mcr_srv_ip' #to be filled with the ip of the MCR SIC" + "\n"
        template += "            dssmcrapiport='80'" + "\n"
        template += "            dssmcrapisuperadmin='sysadmin'" + "\n"
        template += "            dssmcrapisuperadminpassword='sysadmin2014'" + "\n"
        template += "            dssmcrapiloginurl='/api/authentications/login'" + "\n"
        template += "            dssmcrapicontentmanagementurl='/api/contents'" + "\n"
        template += "            dssmcrapiusermanagementurl='/api/users'" + "\n"
        template += "            sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "            # Download and run main server agent" + "\n"
        template += "            rm -f agent*" + "\n"
        template += "            curl http://213.165.68.82/agent.tar.gz > agent.tar.gz" + "\n"
        template += "            tar -xvzf agent.tar.gz" + "\n"
        template += "            python /home/ubuntu/agent.py /usr/share/tomcat7/ " + self.cdn_enable + " &" + "\n"
        template += '            sed -i.bak "s,Hostname=,#Hostname=,g" /etc/zabbix/zabbix_agentd.conf' + "\n"
        template += "            #Stop services" + "\n"
        template += "            service tomcat7 stop" + "\n"
        template += "            service apache2 stop" + "\n"
        template += "            #Autoconf" + "\n"
        template += '            sed -i.bak "s,DSSCSDBNAME,$databasename,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSCSDBSERVERURL,$databasehost,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSCSDBUSERNAME,$databaseusername,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSCSDBPASSWORD,$databasepassword,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIURL,$dssmcrapiurl,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIPORT,$dssmcrapiport,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPISUPERADMINUSER,$dssmcrapisuperadmin," WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPISUPERADMINPASSWORD,$dssmcrapisuperadminpassword,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPILOGINURL,$dssmcrapiloginurl,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPICONTENTMANAGEMENTURL,$dssmcrapicontentmanagementurl,g" WebAppDSSConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIUSERMANAGEMENTURL,$dssmcrapiusermanagementurl,g" WebAppDSSConfig.groovy' + "\n"
        template += "            cp WebAppDSSConfig.groovy /usr/share/tomcat7/" + "\n"
        template += '            # Check database aaS is already there' + "\n"
        template += '            while [[ `echo "show schemas;" | mysql -h $databasehost -u $databaseusername -p$databasepassword` != *$databasename* ]]' + "\n"
        template += '            do' + "\n"
        template += '                #It is not ready yet, wait 1 second and try again' + "\n" 
        template += '                sleep 1' + "\n"
        template += '            done' + "\n"
        template += "            #Start services" + "\n"
        template += "            service zabbix-agent restart" + "\n"        
        template += "            service tomcat7 restart" + "\n"
        template += "            service apache2 restart" + "\n"             
        template += "\n"             
        template += "  " + self.baseCmsResourceName + "_port:" + "\n"             
        template += "    Type: OS::Neutron::Port" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      network_id: "' + self.private_network_id + '"' + "\n"             
        template += "      fixed_ips:" + "\n"             
        template += '        - subnet_id: "' + self.private_sub_network_id + '"' + "\n"             
        template += "\n"             
        template += "  " + self.baseCmsResourceName + "_floating_ip:" + "\n"             
        template += "    Type: OS::Neutron::FloatingIP" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      floating_network_id: "' + self.public_network_id + '"  # public OK' + "\n"
        template += '      port_id: { Ref : ' + self.baseCmsResourceName + '_port }' + "\n"
        
        return template             
    
    def getBaseMcrTemplate(self):
        self.baseCmsResourceName = self.getCmsBaseName()
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         MCR / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  mcr_server:' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      flavor: ' + self.flavor_list[self.mcr_flavor_idx] + "\n"
        template += '      image: DSS-MCR-IMG' + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : mcr_server_port }' + "\n"
        template += '      user_data:' + "\n"
        template += '        Fn::Base64:' + "\n"
        template += '          Fn::Replace:' + "\n"
        template += "          - mcr_srv_ip: { 'Fn::GetAtt': [ mcr_server_floating_ip, floating_ip_address ] }" + "\n"
        template += "            cms_srv_ip: { 'Fn::GetAtt': [ " + self.baseCmsResourceName + "_floating_ip, floating_ip_address ] }" + "\n"
        template += "            dbaas_srv_ip: { 'Fn::GetAtt': [ dbaas_server, first_address ] }" + "\n"
        template += '          - |' + "\n"
        template += '            #!/bin/bash' + "\n"
        template += '            cd /home/ubuntu/' + "\n"
        template += '            #Static data, to be removed' + "\n"
        template += "            monaashost='192.168.0.2'" + "\n"
        template += "            servicecdnenabled='" + self.cdn_enable + "'" + "\n"
        template += "            mcrapistoragedirectory='/home/ubuntu/files/'" + "\n"
        template += "            mcrapistorageserverurl='http://mcr_srv_ip'" + "\n"
        template += "            mcrapistorageserverport='80'" + "\n"
        template += "            mcrapicontentmanagementurl='/api/contents'" + "\n"
        template += "            databasename='" + self.dbname + "'" + "\n"
        template += "            databaseusername='" + self.dbuser + "'" + "\n"
        template += "            databasehost='dbaas_srv_ip'" + "\n"
        template += "            databasepassword='" + self.dbpass + "'" + "\n"
        template += "            corsalloworiginregex='cms_srv_ip'" + "\n"
        template += '            corsurlpattern="/api/contents/\*"' + "\n"
        template += "            sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "            echo dbaas_srv_ip > /home/ubuntu/dbhost" + "\n"
        template += "            # Download and run main server agent" + "\n"
        template += "            rm -f agent*" + "\n"
        template += "            curl http://213.165.68.82/agent.tar.gz > agent.tar.gz" + "\n"
        template += "            tar -xvzf agent.tar.gz" + "\n"
        template += "            curl http://213.165.68.82/getcdr.tar.gz > getcdr.tar.gz" + "\n"
        template += "            tar -xvzf getcdr.tar.gz" + "\n"
        template += "            python /home/ubuntu/agent.py /usr/share/tomcat7/ " + self.cdn_enable + " &" + "\n"
        template += '            sed -i.bak "s,Hostname=,#Hostname=,g" /etc/zabbix/zabbix_agentd.conf' + "\n"
        template += "            #Stop services" + "\n"
        template += "            service tomcat7 stop" + "\n"
        template += "            service apache2 stop" + "\n"
        template += "            #Autoconf" + "\n"
        template += '            sed -i.bak "s,SERVICECDNENABLED,$servicecdnenabled,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,MCRAPISTORAGEDIRECTORY,$mcrapistoragedirectory,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,MCRAPISTORAGESERVERURL,$mcrapistorageserverurl,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,MCRAPISTORAGESERVERPORT,$mcrapistorageserverport,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,MCRAPICONTENTMANAGEMENTURL,$mcrapicontentmanagementurl,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIDBSERVERURL,$databasehost,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIDBNAME,$databasename,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIDBUSERNAME,$databaseusername,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSMCRAPIDBPASSWORD,$databasepassword,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,MCRAPICONTENTMANAGEMENTPATTERN,$corsurlpattern,g" DSSMCRAPIConfig.groovy' + "\n"
        template += '            sed -i.bak "s,DSSCMSSERVER,$corsalloworiginregex,g" DSSMCRAPIConfig.groovy' + "\n"
        template += "            cp DSSMCRAPIConfig.groovy /usr/share/tomcat7/" + "\n"
        template += "            #Create db if required" + "\n"
        template += '            # Check database aaS is already there' + "\n"
        template += '            while [[ `echo "status" | mysql -h $databasehost -u $databaseusername -p$databasepassword | grep Uptime` != *Uptime* ]]' + "\n"
        template += '            do' + "\n"
        template += '                #It is not ready yet, wait 1 second and try again' + "\n" 
        template += '                sleep 1' + "\n"
        template += '            done' + "\n"
        template += '            echo "drop database $databasename" | mysql -h $databasehost -u $databaseusername -p$databasepassword' + "\n"
        template += '            echo "create database $databasename" | mysql -h $databasehost -u $databaseusername -p$databasepassword' + "\n"
        template += "            #Start services" + "\n"
        template += "            service zabbix-agent restart" + "\n"        
        template += "            service tomcat7 restart" + "\n"
        template += "            service apache2 restart" + "\n"             
        template += "\n"             
        template += "  mcr_server_port:" + "\n"             
        template += "    Type: OS::Neutron::Port" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      network_id: "' + self.private_network_id + '"' + "\n"             
        template += "      fixed_ips:" + "\n"             
        template += '        - subnet_id: "' + self.private_sub_network_id + '"' + "\n"             
        template += "\n"             
        template += "  mcr_server_floating_ip:" + "\n"             
        template += "    Type: OS::Neutron::FloatingIP" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      floating_network_id: "' + self.public_network_id + '"  # public OK' + "\n"
        template += '      port_id: { Ref : mcr_server_port }' + "\n"
        
        return template
    
    def getOutput(self):
        self.baseCmsResourceName = self.getCmsBaseName()
        template = "Outputs:" + "\n"
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += '  mcn.dss.cms' + str(self.cmsCounter) + '.endpoint:' + "\n"
            template += '    Description: Floating IP address of DSS CMS in public network' + "\n"
            template += "    Value: {'Fn::GetAtt': [" + self.getCmsBaseName() + "_floating_ip, floating_ip_address] }" + "\n"
            template += "\n"
            
        template += '  mcn.dss.mcr.endpoint:' + "\n"
        template += '    Description: Floating IP address of DSS MCR in public network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ mcr_server_floating_ip, floating_ip_address ] }" + "\n"
        template += "\n"
        template += '  mcn.dss.lb.endpoint:' + "\n"
        template += '    Description: Floating IP address of DSS load balancer in public network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ cms_lb_floatingip, floating_ip_address ] }" + "\n"
        template += "\n"
        template += '  mcn.dss.mcr.hostname:' + "\n"
        template += '    Description: open stack instance name' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ mcr_server, show ] }" + "\n"
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += "\n"
            template += '  mcn.dss.cms' + str(self.cmsCounter) + '.hostname:' + "\n"
            template += '    Description: open stack instance name' + "\n"
            template += "    Value: { 'Fn::GetAtt': [ " + self.getCmsBaseName() + ", show ] }" + "\n"
        
        return template
        
    def getTemplate(self):
        template = "HeatTemplateFormatVersion: '2012-12-12'" + "\n"
        template += "Description: 'YAML MCN DSSaaS Template'" + "\n"
        template += "Resources:" + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         DATABASE / STORING RESOURCES                             #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '#  dbaas_trove_instance:' + "\n"
        template += '#    Type: OS::Trove::Instance' + "\n"
        template += '#    Properties:' + "\n"
        template += '#      databases: [{"character_set": utf8, "name": DSSaaS, "collate": utf8_general_ci}]' + "\n"
        template += '#      flavor: m1.small' + "\n"
        template += '#      name: dbaas_trove_instance' + "\n"
        template += '#      size: 2' + "\n"
        template += '#      users: [{"password": changeme, "name": user, "databases": [DSSaaS]}]' + "\n"
        template += "\n"
        template += '  dbaas_server:' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: DSS-CLEAN-SIC' + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : dbaas_server_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += "        #!/bin/bash" + "\n"
        template += "        cd /home/ubuntu/" + "\n"
        template += "        #Static data, to be removed" + "\n"
        template += "        databaseusername='root'" + "\n"
        template += "        databasehost='localhost'" + "\n"
        template += "        databasepassword='password'" + "\n"
        template += "        sed -i.bak s/dss-cms/`hostname`/g /etc/hosts" + "\n"
        template += '        #Configure db' + "\n"
        template += '        echo "GRANT ALL PRIVILEGES ON *.* TO \'$databaseusername\'@\'%\' IDENTIFIED BY \'$databasepassword\';" | mysql -u $databaseusername -p$databasepassword' + "\n"
        template += '        sed -i.bak "s,bind-address,#bind-address,g" /etc/mysql/my.cnf' + "\n"
        template += '        #restart services' + "\n"
        template += "        service mysql restart" + "\n"           
        template += "\n"             
        template += "  dbaas_server_port:" + "\n"             
        template += "    Type: OS::Neutron::Port" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      network_id: "' + self.private_network_id + '"' + "\n"             
        template += "      fixed_ips:" + "\n"             
        template += '        - subnet_id: "' + self.private_sub_network_id + '"' + "\n"             
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += "\n"
            template += self.getBaseCmsTemplate()
            template += "\n"
        
        self.cmsCounter = 1    
        template += self.getBaseMcrTemplate()
        template += "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         LB / FRONTEND RESOURCES                                  #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '  cms_healthmonitor:' + "\n"
        template += '    Type: OS::Neutron::HealthMonitor' + "\n"
        template += '    Properties:' + "\n"
        template += '      delay : 3' + "\n"            
        template += '      max_retries : 3' + "\n"            
        template += '      timeout : 3' + "\n"            
        template += '      type : HTTP' + "\n"            
        template += "\n"            
        template += '  cms_lb_pool:' + "\n"            
        template += '    Type: OS::Neutron::Pool' + "\n"            
        template += '    Properties:' + "\n"            
        template += '      lb_method: ROUND_ROBIN' + "\n"            
        template += '      name: mypool' + "\n"            
        template += '      protocol: HTTP' + "\n"            
        template += '      subnet_id: "' + self.private_sub_network_id + '"' + "\n"            
        template += '      monitors : [{ Ref: cms_healthmonitor }]' + "\n"            
        template += '      vip : {"subnet": "' + self.private_sub_network_id + '", "name": myvip, "protocol_port": 80 }' + "\n"            
        template += "\n"
        
        self.lbNameRandom = self.randomNameGenerator(6)
         
        template += '  ' + self.lbNameRandom  + '_loadbalancer:' + "\n"           
        template += '    Type: OS::Neutron::LoadBalancer' + "\n"           
        template += '    Properties:' + "\n"           
        template += '      members: [ '
        
        self.cmsCounter = 1
        template += '{ Ref: ' + self.getCmsBaseName() +' }' 
        for self.cmsCounter in range(2, self.numberOfCmsInstances + 1):
            template += ', { Ref: ' + self.getCmsBaseName() +' }'
            
        template += ' ]' + "\n"           
        template += '      pool_id: { Ref: cms_lb_pool }' + "\n"           
        template += '      protocol_port: 80' + "\n"           
        template += "\n"           
        template += '  cms_lb_floatingip:' + "\n"           
        template += '    Type: OS::Neutron::FloatingIP' + "\n"           
        template += '    Properties:' + "\n"           
        template += '      floating_network_id: "' + self.public_network_id + '"' + "\n" #Change this for local testbed          
        template += "      port_id: {'Fn::Select' : ['port_id', { 'Fn::GetAtt': [ cms_lb_pool, vip ] } ] }" + "\n"           
        template += "\n"
        template += self.getOutput()           
        
        '''
        self.jsonfile = open(''+'testtemp.yaml', 'w')
        self.jsonfile.write(template)
        self.jsonfile.close()
        '''
        
        return template
    
    def templateToScaleUp(self):
        if self.mcr_flavor_idx < self.maximum_flavor_idx:
            self.mcr_flavor_idx += 1
        return self.getTemplate()
    
    def templateToScaleDown(self):
        if self.mcr_flavor_idx - 1 >= self.minimum_flavor_idx:
            self.mcr_flavor_idx -= 1
        return self.getTemplate()
    
    def templateToScaleOut(self):
        self.numberOfCmsInstances += 1
        return self.getTemplate()
    
    def templateToScaleIn(self):
        if self.numberOfCmsInstances > 1:
            self.numberOfCmsInstances -= 1
        return self.getTemplate()
