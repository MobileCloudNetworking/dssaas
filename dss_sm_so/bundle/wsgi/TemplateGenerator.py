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
        #self.private_network_id = "82c56778-da2c-4e12-834d-8d09958d0563"
        #self.private_sub_network_id = "0e768fd0-2bbc-482c-9cbd-7469529d141f"
        self.private_network_id = "313a8f80-4397-4add-83c9-94f568611ade"
        self.private_sub_network_id = "2948595e-bbc0-4ab8-a46f-79afb9f3d277"
        #self.key_name = "mcn-key"
        #self.key_name = "ubern-key"
        self.key_name = "mcn-key"
        self.dns_enable = 'false'
        self.dss_cms_image_name = 'DSS-IMG-filesync'
        self.dss_mcr_image_name = 'DSS-IMG-filesync'
        self.dss_db_image_name = 'DSS-DB-SIC'
        
        self.dbname = 'webappdss'
        self.dbpass = '******'
        self.dbuser = 'root'
        
        self.cms_scaleout_limit = 4
        self.mcr_scaleout_limit = 4

        # Content format: [{"device_name":"cms1_server", "host_name":"cms1_server_1451992360"}, ...]
        self.cms_instances = []
        self.mcr_instances = []

        self.initial_cms_count = 1
        self.initial_mcr_count = 1

        self.numberOfCmsInstances = 0
        self.numberOfMcrInstances = 0

        self.new_cms_lb_needed = False
        self.new_mcr_lb_needed = False
        self.cms_lb_name = None
        self.mcr_lb_name = None

        self.scaleOut("cms", self.initial_cms_count)
        self.scaleOut("mcr", self.initial_mcr_count)

    def randomNameGenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def getBaseName(self, instance_type):
        hostname = None
        devicename = None
        if instance_type is "cms":
            hostname = devicename = "cms" + str(self.numberOfCmsInstances) + "_server_" + str(int(time.time()))
        elif instance_type is "mcr":
            hostname = devicename = "mcr" + str(self.numberOfMcrInstances) + "_server_" + str(int(time.time()))
        return hostname, devicename

    def getBaseCmsTemplate(self, hostname, device_name):
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
    
    def getBaseMcrTemplate(self, hostname, device_name):
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         MCR / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + device_name + ':' + "\n"
        template += '    Type: OS::Nova::Server' + "\n"
        template += '    Properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: ' + hostname + "\n"
        template += '      flavor: m1.small' + "\n"
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
        
        for i in range(0, len(self.cms_instances)):
            template += '  mcn.dss.' + self.cms_instances[i]["device_name"] + '.endpoint:' + "\n"
            template += '    Description: Floating IP address of DSS CMS in public network' + "\n"
            template += "    Value: {'Fn::GetAtt': [" + self.cms_instances[i]["device_name"] + "_floating_ip, floating_ip_address] }" + "\n"
            template += "\n"

        for i in range(0, len(self.mcr_instances)):
            template += '  mcn.dss.' + self.mcr_instances[i]["device_name"] + '.endpoint:' + "\n"
            template += '    Description: Floating IP address of DSS MCR in public network' + "\n"
            template += "    Value: {'Fn::GetAtt': [" + self.mcr_instances[i]["device_name"] + "_floating_ip, floating_ip_address] }" + "\n"
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
        
        for i in range(0, len(self.cms_instances)):
            template += '  mcn.dss.' + self.cms_instances[i]["device_name"] + '.hostname:' + "\n"
            template += '    Description: open stack instance name' + "\n"
            template += "    Value: { 'Fn::GetAtt': [ " + self.cms_instances[i]["device_name"] + ", name ] }" + "\n"
            template += "\n"

        for i in range(0, len(self.mcr_instances)):
            template += '  mcn.dss.' + self.mcr_instances[i]["device_name"] + '.hostname:' + "\n"
            template += '    Description: open stack instance name' + "\n"
            template += "    Value: { 'Fn::GetAtt': [ " + self.mcr_instances[i]["device_name"] + ", name ] }" + "\n"
            template += "\n"

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
        
        for item in self.cms_instances:
            template += "\n"
            template += self.getBaseCmsTemplate(item["host_name"], item["device_name"])
            template += "\n"

        for item in self.mcr_instances:
            template += "\n"
            template += self.getBaseMcrTemplate(item["host_name"], item["device_name"])
            template += "\n"

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

        if self.new_cms_lb_needed:
            self.cms_lb_name = self.randomNameGenerator(6)
        self.new_cms_lb_needed = False
         
        template += '  ' + self.cms_lb_name + '_loadbalancer:' + "\n"
        template += '    Type: OS::Neutron::LoadBalancer' + "\n"           
        template += '    Properties:' + "\n"           
        template += '      members: [ '
        
        template += '{ Ref: ' + self.cms_instances[0]["device_name"] +' }'
        for i in range(1, len(self.cms_instances)):
            template += ', { Ref: ' + self.cms_instances[i]["device_name"] +' }'

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

        if self.new_mcr_lb_needed:
            self.mcr_lb_name = self.randomNameGenerator(6)
        self.new_mcr_lb_needed = False

        template += '  ' + self.mcr_lb_name + '_loadbalancer:' + "\n"
        template += '    Type: OS::Neutron::LoadBalancer' + "\n"
        template += '    Properties:' + "\n"
        template += '      members: [ '

        template += '{ Ref: ' + self.mcr_instances[0]["device_name"] +' }'
        for i in range(1, len(self.mcr_instances)):
            template += ', { Ref: ' + self.mcr_instances[i]["device_name"] +' }'

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

    def scaleOut(self, instance_type, count=1):
        if instance_type is "cms":
            for i in range(0, count):
                if self.numberOfCmsInstances < self.cms_scaleout_limit:
                    self.numberOfCmsInstances += 1
                    hostname, device_name = self.getBaseName(instance_type=instance_type)
                    self.cms_instances.append({"device_name": device_name, "host_name": hostname})
                    self.new_cms_lb_needed = True
                else:
                    print "CMS scale out limit reached."
                    break
        else:
            for i in range(0, count):
                if self.numberOfMcrInstances < self.mcr_scaleout_limit:
                    self.numberOfMcrInstances += 1
                    hostname, device_name = self.getBaseName(instance_type=instance_type)
                    self.mcr_instances.append({"device_name": device_name, "host_name": hostname})
                    self.new_mcr_lb_needed = True
                else:
                    print "MCR scale out limit reached."
                    break

    # TODO: Check if you can write it simpler
    # TODO: If needed add multiple host removal feature
    def removeInstance(self, hostname, instance_type):
        host_to_remove = None
        if instance_type is "cms":
            if len(self.cms_instances) > 1:
                for item in self.cms_instances:
                    if item["host_name"] == hostname:
                        host_to_remove = item
                self.cms_instances.remove(host_to_remove)
                self.new_cms_lb_needed = True
                self.numberOfCmsInstances -= 1
            else:
                print "Can not remove all CMS instances, scale out first."
        else:
            if len(self.mcr_instances) > 1:
                for item in self.mcr_instances:
                    if item["host_name"] == hostname:
                        host_to_remove = item
                self.mcr_instances.remove(host_to_remove)
                self.new_mcr_lb_needed = True
                self.numberOfMcrInstances -= 1
            else:
                print "Can not remove all MCR instances, scale out first."

    def scaleIn(self, instance_type, count=1):
        if instance_type is "cms":
            for i in range(0, count):
                if len(self.cms_instances) > 1:
                    self.cms_instances.pop()
                    self.new_cms_lb_needed = True
                    self.numberOfCmsInstances -= 1
                else:
                    print "Can not remove all CMS instances."
                    break
        else:
            for i in range(0, count):
                if len(self.mcr_instances) > 1:
                    self.mcr_instances.pop()
                    self.new_mcr_lb_needed = True
                    self.numberOfMcrInstances -= 1
                else:
                    print "Can not remove all MCR instances."
                    break

if __name__ == '__main__':
    mytemp = TemplateGenerator()
    print mytemp.getTemplate()
    print "#########################################################################"
    mytemp.scaleIn("cms")
    print mytemp.getTemplate()
    print "#########################################################################"
    mytemp.scaleOut("cms", 3)
    print mytemp.getTemplate()