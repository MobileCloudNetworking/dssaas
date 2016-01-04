'''''''''
#Template Generator for scaling purposes 
'''''''''
import string
import random
import time


class TemplateGenerator:
    """
    Sample SO execution part.
    """

    def __init__(self):
        #Later to be filled by asking CC
        self.public_network_id = "77e659dd-f1b4-430c-ac6f-d92ec0137c85"
        self.public_sub_network_id = "a7628952-bb27-4217-8154-fb41ac727a61"
        self.private_network_id = "82c56778-da2c-4e12-834d-8d09958d0563"
        self.private_sub_network_id = "0e768fd0-2bbc-482c-9cbd-7469529d141f"
        #self.private_network_id = "df6fc93e-6af7-4fb3-9d0f-71e4a377dccb"
        #self.private_sub_network_id = "c8e7b799-50fc-4da1-89a3-9d7ea9671e88"
        #self.key_name = "mcn-key"
        #self.key_name = "ubern-key"
        self.key_name = "mcn-key"
        self.dns_enable = 'false'
        self.dss_cms_image_name = 'DSS-IMG-filesync'
        self.dss_mcr_image_name = 'DSS-IMG-filesync'
        self.dss_db_image_name = 'DSS-DB-SIC'
        
        self.dbname = 'webappdss'
        self.dbpass = 'registro00'
        self.dbuser = 'root'
        
        self.mcr_flavor_idx = 1
        self.minimum_flavor_idx = 1
        self.maximum_flavor_idx = 4
        self.flavor_list = ['m1.tiny','m1.small','m1.medium','m1.large','m1.xlarge']
        
        self.numberOfCmsInstances = 1
        self.numberOfMcrInstances = 1
        self.cmsCounter = 1
        self.mcrCounter = 1

        self.cmsHostToRemove = None
    
    def randomNameGenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    def getBaseName(self, instance_type):
        if instance_type is "cms":
            return "cms" + str(self.cmsCounter) + "_server_" + str(int(time.time())), "cms" + str(self.cmsCounter) + "_server"
        elif instance_type is "mcr":
            return "mcr" + str(self.mcrCounter) + "_server_" + str(int(time.time())), "mcr" + str(self.mcrCounter) + "_server"
        else:
            return None

    def getBaseCmsTemplate(self):
        hostname, device_name = self.getBaseName(instance_type='cms')
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         CMS / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + device_name + ':' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: ' + hostname + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: ' + self.dss_cms_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : ' + device_name + '_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += '        #!/bin/bash' + "\n"
        template += '        cd /home/ubuntu/' + "\n"
        template += "        sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "        # Download and run main server agent" + "\n"
        template += "        rm -f agent*" + "\n"
        template += "        curl http://213.165.68.82/agent_ex.tar.gz > agent_ex.tar.gz" + "\n"
        template += "        tar -xvzf agent_ex.tar.gz" + "\n"
        template += "        python /home/ubuntu/agent_ex.py /usr/share/tomcat7/ &" + "\n"
        template += "\n"             
        template += "  " + device_name + "_port:" + "\n"
        template += "    Type: OS::Neutron::Port" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      network_id: "' + self.private_network_id + '"' + "\n"             
        template += "      fixed_ips:" + "\n"             
        template += '        - subnet_id: "' + self.private_sub_network_id + '"' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += "\n"             
        template += "  " + device_name + "_floating_ip:" + "\n"
        template += "    Type: OS::Neutron::FloatingIP" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      floating_network_id: "' + self.public_network_id + '"  # public OK' + "\n"
        template += '      port_id: { Ref : ' + device_name + '_port }' + "\n"

        return template             
    
    def getBaseMcrTemplate(self):
        hostname, device_name = self.getBaseName(instance_type='mcr')
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         MCR / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + device_name + ':' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: ' + hostname + "\n"
        template += '      flavor: ' + self.flavor_list[self.mcr_flavor_idx] + "\n"
        template += '      image: ' + self.dss_mcr_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - port: { Ref : ' + device_name + '_port }' + "\n"
        template += '      user_data: |' + "\n"
        template += '        #!/bin/bash' + "\n"
        template += '        cd /home/ubuntu/' + "\n"
        template += "        sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "        # Download and run main server agent" + "\n"
        template += "        rm -f agent*" + "\n"
        template += "        curl http://213.165.68.82/agent_ex.tar.gz > agent_ex.tar.gz" + "\n"
        template += "        tar -xvzf agent_ex.tar.gz" + "\n"
        template += "        python /home/ubuntu/agent_ex.py /usr/share/tomcat7/ &" + "\n"
        template += "\n"             
        template += "  " + device_name + "_port:" + "\n"
        template += "    Type: OS::Neutron::Port" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      network_id: "' + self.private_network_id + '"' + "\n"             
        template += "      fixed_ips:" + "\n"             
        template += '        - subnet_id: "' + self.private_sub_network_id + '"' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += "\n"             
        template += "  " + device_name + "_floating_ip:" + "\n"
        template += "    Type: OS::Neutron::FloatingIP" + "\n"             
        template += "    Properties:" + "\n"             
        template += '      floating_network_id: "' + self.public_network_id + '"  # public OK' + "\n"
        template += '      port_id: { Ref : ' + device_name + '_port }' + "\n"
        
        return template
    
    def getOutput(self):
        template = "Outputs:" + "\n"
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += '  mcn.dss.cms' + str(self.cmsCounter) + '.endpoint:' + "\n"
            template += '    Description: Floating IP address of DSS CMS in public network' + "\n"
            template += "    Value: {'Fn::GetAtt': [" + self.getBaseName('cms')[1] + "_floating_ip, floating_ip_address] }" + "\n"
            template += "\n"

        for self.mcrCounter in range(1, self.numberOfMcrInstances + 1):
            template += '  mcn.dss.mcr' + str(self.mcrCounter) + '.endpoint:' + "\n"
            template += '    Description: Floating IP address of DSS MCR in public network' + "\n"
            template += "    Value: {'Fn::GetAtt': [" + self.getBaseName('mcr')[1] + "_floating_ip, floating_ip_address] }" + "\n"
            template += "\n"

        template += '  mcn.dss.db.endpoint:' + "\n"
        template += '    Description: IP address of DSS DB in private network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ dbaas_server, first_address ] }" + "\n"
        template += "\n"
        template += '  mcn.dss.cms.lb.endpoint:' + "\n"
        template += '    Description: Floating IP address of DSS (CMS) load balancer in public network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ cms_lb_floatingip, floating_ip_address ] }" + "\n"
        template += "\n"
        template += '  mcn.dss.mcr.lb.endpoint:' + "\n"
        template += '    Description: Floating IP address of DSS (MCR) load balancer in public network' + "\n"
        template += "    Value: { 'Fn::GetAtt': [ mcr_lb_floatingip, floating_ip_address ] }" + "\n"
        template += "\n"
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += "\n"
            template += '  mcn.dss.cms' + str(self.cmsCounter) + '.hostname:' + "\n"
            template += '    Description: open stack instance name' + "\n"
            template += "    Value: { 'Fn::GetAtt': [ " + self.getBaseName('cms')[1] + ", name ] }" + "\n"

        for self.mcrCounter in range(1, self.numberOfMcrInstances + 1):
            template += "\n"
            template += '  mcn.dss.mcr' + str(self.mcrCounter) + '.hostname:' + "\n"
            template += '    Description: open stack instance name' + "\n"
            template += "    Value: { 'Fn::GetAtt': [ " + self.getBaseName('mcr')[1] + ", name ] }" + "\n"

        template += '  mcn.endpoint.dssaas:' + "\n"
        template += '    Description: DSS service endpoint' + "\n"
        template += '    Value: "N/A"' + "\n"

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
        template += '      name: dss_dbaas_server' + "\n"
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
        template += '      replacement_policy: AUTO' + "\n"
        
        for self.cmsCounter in range(1, self.numberOfCmsInstances + 1):
            template += "\n"
            template += self.getBaseCmsTemplate()
            template += "\n"
        
        self.cmsCounter = 1

        for self.mcrCounter in range(1, self.numberOfMcrInstances + 1):
            template += "\n"
            template += self.getBaseMcrTemplate()
            template += "\n"

        self.mcrCounter = 1

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
        template += '      name: cmspool' + "\n"
        template += '      protocol: HTTP' + "\n"            
        template += '      subnet_id: "' + self.private_sub_network_id + '"' + "\n"            
        template += '      monitors : [{ Ref: cms_healthmonitor }]' + "\n"            
        template += '      vip : {"subnet": "' + self.private_sub_network_id + '", "name": cmsvip, "protocol_port": 80, "session_persistence":{"type": HTTP_COOKIE }}' + "\n"
        template += "\n"
        
        self.lbNameRandom = self.randomNameGenerator(6)
         
        template += '  ' + self.lbNameRandom  + '_loadbalancer:' + "\n"           
        template += '    Type: OS::Neutron::LoadBalancer' + "\n"           
        template += '    Properties:' + "\n"           
        template += '      members: [ '
        
        self.cmsCounter = 1
        template += '{ Ref: ' + self.getBaseName(instance_type='cms')[1] +' }'
        for self.cmsCounter in range(2, self.numberOfCmsInstances + 1):
            template += ', { Ref: ' + self.getBaseName(instance_type='cms')[1] +' }'

        self.cmsCounter = self.numberOfCmsInstances + 1
        self.cmsHostToRemove = self.getBaseName(instance_type='cms')[1]

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
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         LB / MCR RESOURCES                                       #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '  mcr_healthmonitor:' + "\n"
        template += '    Type: OS::Neutron::HealthMonitor' + "\n"
        template += '    Properties:' + "\n"
        template += '      delay : 10' + "\n"
        template += '      max_retries : 3' + "\n"
        template += '      timeout : 10' + "\n"
        template += '      type : HTTP' + "\n"
        template += '      url_path : /DSSMCRAPI/' + "\n"
        template += '      expected_codes : 200-399'
        template += "\n"
        template += '  mcr_lb_pool:' + "\n"
        template += '    Type: OS::Neutron::Pool' + "\n"
        template += '    Properties:' + "\n"
        template += '      lb_method: ROUND_ROBIN' + "\n"
        template += '      name: mcrpool' + "\n"
        template += '      protocol: HTTP' + "\n"
        template += '      subnet_id: "' + self.private_sub_network_id + '"' + "\n"
        template += '      monitors : [{ Ref: mcr_healthmonitor }]' + "\n"
        template += '      vip : {"subnet": "' + self.private_sub_network_id + '", "name": mcrvip, "protocol_port": 80, "session_persistence":{"type": HTTP_COOKIE }}' + "\n"
        template += "\n"

        self.lbNameRandom = self.randomNameGenerator(6)

        template += '  ' + self.lbNameRandom  + '_loadbalancer:' + "\n"
        template += '    Type: OS::Neutron::LoadBalancer' + "\n"
        template += '    Properties:' + "\n"
        template += '      members: [ '

        self.mcrCounter = 1
        template += '{ Ref: ' + self.getBaseName(instance_type='mcr')[1] +' }'
        for self.mcrCounter in range(2, self.numberOfMcrInstances + 1):
            template += ', { Ref: ' + self.getBaseName(instance_type='mcr')[1] +' }'

        self.mcrCounter = self.numberOfMcrInstances + 1
        self.mcrHostToRemove = self.getBaseName(instance_type='mcr')[1]

        template += ' ]' + "\n"
        template += '      pool_id: { Ref: mcr_lb_pool }' + "\n"
        template += '      protocol_port: 80' + "\n"
        template += "\n"
        template += '  mcr_lb_floatingip:' + "\n"
        template += '    Type: OS::Neutron::FloatingIP' + "\n"
        template += '    Properties:' + "\n"
        template += '      floating_network_id: "' + self.public_network_id + '"' + "\n" #Change this for local testbed
        template += "      port_id: {'Fn::Select' : ['port_id', { 'Fn::GetAtt': [ mcr_lb_pool, vip ] } ] }" + "\n"
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

if __name__ == '__main__':
    mytemp = TemplateGenerator()
    print mytemp.getTemplate()