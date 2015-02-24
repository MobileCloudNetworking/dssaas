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
        self.public_network_id = "1b31bc6b-8aff-4e13-912a-d9c9a427475a"
        self.public_sub_network_id = "017c2d8a-66d5-458f-ba57-646082fbd285"
        self.private_network_id = "a8cbfc3c-42d0-4431-86ec-4597d38bbb52"
        self.private_sub_network_id = "70506734-0b95-4a8e-b8b7-4a8a54330db0"
        
        self.key_name = "bart-key"
        self.cdn_enable = 'false'
        self.icn_enable = 'true'
        self.dss_cms_image_name = 'DSS-IMAGE-FINAL'
        self.dss_mcr_image_name = 'DSS-IMAGE-FINAL'
        self.dss_db_image_name = 'DSS-DB-SIC'
        
        self.dbname = 'webappdss'
        self.dbpass = 'pass'
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
        template += '      image: ' + self.dss_cms_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : ' + self.baseCmsResourceName + '_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += '        #!/bin/bash' + "\n"
        template += '        cd /home/ubuntu/' + "\n"
        template += "        sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "        # Download and run main server agent" + "\n"
        template += "        rm -f agent*" + "\n"
        template += "        curl http://213.165.68.82/agent.tar.gz > agent.tar.gz" + "\n"
        template += "        tar -xvzf agent.tar.gz" + "\n"
        template += "        python /home/ubuntu/agent.py /usr/share/tomcat7/ " + self.cdn_enable + " " + self.icn_enable + " &" + "\n"
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
        template += '      image: ' + self.dss_mcr_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : mcr_server_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += '        #!/bin/bash' + "\n"
        template += '        cd /home/ubuntu/' + "\n"
        template += "        sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "        # Download and run main server agent" + "\n"
        template += "        rm -f agent*" + "\n"
        template += "        curl http://213.165.68.82/agent.tar.gz > agent.tar.gz" + "\n"
        template += "        tar -xvzf agent.tar.gz" + "\n"
        template += "        python /home/ubuntu/agent.py /usr/share/tomcat7/ " + self.cdn_enable + " " + self.icn_enable + " &" + "\n"
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
        template += '  mcn.dss.db.endpoint:' + "\n"
        template += '    Description: IP address of DSS MCR in private network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ dbaas_server, first_address ] }" + "\n"
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
        template += '      image: ' + self.dss_db_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : dbaas_server_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += "        #!/bin/bash" + "\n"
        template += "        cd /home/ubuntu/" + "\n"
        template += "        #Static data, to be removed" + "\n"
        template += "        databaseusername='" + self.dbuser + "'" + "\n"
        template += "        databasehost='localhost'" + "\n"
        template += "        databasepassword='" + self.dbpass + "'" + "\n"
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
        template += '      delay : 10' + "\n"            
        template += '      max_retries : 3' + "\n"            
        template += '      timeout : 10' + "\n"            
        template += '      type : HTTP' + "\n"
        template += '      url_path : /WebAppDSS/' + "\n"
        template += '      expected_codes : 200-399'            
        template += "\n"            
        template += '  cms_lb_pool:' + "\n"            
        template += '    Type: OS::Neutron::Pool' + "\n"            
        template += '    Properties:' + "\n"            
        template += '      lb_method: ROUND_ROBIN' + "\n"            
        template += '      name: mypool' + "\n"            
        template += '      protocol: HTTP' + "\n"            
        template += '      subnet_id: "' + self.private_sub_network_id + '"' + "\n"            
        template += '      monitors : [{ Ref: cms_healthmonitor }]' + "\n"            
        template += '      vip : {"subnet": "' + self.private_sub_network_id + '", "name": myvip, "protocol_port": 80, "session_persistence":{"type": HTTP_COOKIE }}' + "\n"            
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
