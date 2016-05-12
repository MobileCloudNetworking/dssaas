'''''''''
# DSS Template Generator
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
        self.dss_mq_image_name = 'DSS-MQ-SIC'
        self.dss_db_image_name = 'DSS-DB-SIC'

        self.dbname = 'webappdss'# DO NOT CHANGE
        self.dbpass = '******'# Use the one set in DB image
        self.dbuser = 'root'# DO NOT CHANGE

        self.mq_service_user = 'adminRabbit'
        self.mq_service_pass = '******'
        self.mq_service_port = '8384'

        self.cms_scaleout_limit = 20
        self.mcr_scaleout_limit = 20

        # Content format: [{"device_name":"cms1_server", "host_name":"cms1_server_1451992360"}, ...]
        self.cms_instances = []
        self.mcr_instances = []
        self.added_sics = []

        self.initial_cms_count = 2
        self.initial_mcr_count = 2

        self.numberOfCmsInstances = 0
        self.numberOfMcrInstances = 0
        self.lastCmsNumAssigned = 1
        self.lastMcrNumAssigned = 1

        self.new_cms_lb_needed = True
        self.new_mcr_lb_needed = True
        self.new_stream_lb_needed = True
        self.cms_lb_name = None
        self.mcr_lb_name = None
        self.stream_lb_name = None

        self.scaleOut("cms", self.initial_cms_count)
        self.scaleOut("mcr", self.initial_mcr_count)

    def randomNameGenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def getBaseName(self, instance_type):
        hostname = None
        devicename = None
        if instance_type == "cms":
            hostname = devicename = "cms" + str(self.lastCmsNumAssigned) + "_server_" + str(int(time.time()))
            self.lastCmsNumAssigned += 1
        elif instance_type == "mcr":
            hostname = devicename = "mcr" + str(self.lastMcrNumAssigned) + "_server_" + str(int(time.time()))
            self.lastMcrNumAssigned += 1
        return hostname, devicename

    def getBaseMQTemplate(self):
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         MessageQ / MESSAGING RESOURCES                           #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  messageq_server:' + "\n"
        template += '    properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: dss_messageq_server' + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: ' + self.dss_mq_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - ' + "\n"
        template += '          port: ' + "\n"
        template += '            Ref: messageq_server_port' + "\n"
        template += '      user_data: |' + "\n"
        template += '        #!/bin/bash' + "\n"
        template += '        cd /home/ubuntu' + "\n"
        template += '        rabbitmqctl add_user ' + self.mq_service_user + ' ' + self.mq_service_pass + "\n"
        template += '        rabbitmqctl set_user_tags ' + self.mq_service_user + ' administrator' + "\n"
        template += '        rabbitmqctl set_permissions -p / ' + self.mq_service_user + ' ".*" ".*" ".*"' + "\n"
        template += '        rabbitmq-plugins enable rabbitmq_management' + "\n"
        template += '    type: "OS::Nova::Server"' + "\n"
        template += "\n"
        template += "  messageq_server_port:" + "\n"
        template += "    properties:" + "\n"
        template += '      network_id: ' + "\n"
        template += '        get_param: private_net_id' + "\n"
        template += "      fixed_ips:" + "\n"
        template += '        - ' + "\n"
        template += '          subnet_id: ' + "\n"
        template += '            get_param: private_subnet_id' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += '    type: "OS::Neutron::Port"' + "\n"
        template += "\n"
        template += "  messageq_server_floating_ip:" + "\n"
        template += "    properties:" + "\n"
        template += '      floating_network_id: ' + "\n"
        template += '        get_param: public_net_id' + "\n"
        template += '      port_id: ' + "\n"
        template += '        Ref : messageq_server_port' + "\n"
        template += '    type: "OS::Neutron::FloatingIP"' + "\n"

        return template

    def getBaseCmsTemplate(self, hostname, device_name):
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         CMS / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + device_name + ':' + "\n"
        template += '    properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: ' + hostname + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: ' + self.dss_cms_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - ' + "\n"
        template += '          port: ' + "\n"
        template += '            Ref: ' + device_name + '_port' + "\n"
        template += '      user_data:' + "\n"
        template += '        str_replace:' + "\n"
        template += '          template: |' + "\n"
        template += '            #!/bin/bash' + "\n"
        template += '            cd /home/ubuntu/' + "\n"
        template += "            sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "            # Download and run main server agent" + "\n"
        template += "            rm -f agent*" + "\n"
        template += "            curl http://213.165.68.82/agent_ex.tar.gz > agent_ex.tar.gz" + "\n"
        template += "            tar -xvzf agent_ex.tar.gz" + "\n"
        template += "            python /home/ubuntu/agent_ex.py /usr/share/tomcat7/ mq_service_ip &" + "\n"
        template += "          params:" + "\n"
        template += '            mq_service_ip:' + "\n"
        template += '              get_attr: ' + "\n"
        template += '                - messageq_server_floating_ip' + "\n"
        template += '                - floating_ip_address' + "\n"
        template += '    type: "OS::Nova::Server"' + "\n"
        template += "\n"
        template += "  " + device_name + "_port:" + "\n"
        template += "    properties:" + "\n"
        template += '      network_id: ' + "\n"
        template += '        get_param: private_net_id' + "\n"
        template += "      fixed_ips:" + "\n"
        template += '        - ' + "\n"
        template += '          subnet_id: ' + "\n"
        template += '            get_param: private_subnet_id' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += '    type: "OS::Neutron::Port"' + "\n"

        return template

    def getBaseMcrTemplate(self, hostname, device_name):
        template = ''
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         MCR / FRONTEND RESOURCES                                 #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  ' + device_name + ':' + "\n"
        template += '    properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: ' + hostname + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: ' + self.dss_mcr_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - ' + "\n"
        template += '          port: ' + "\n"
        template += '            Ref: ' + device_name + '_port' + "\n"
        template += '      user_data:' + "\n"
        template += '        str_replace:' + "\n"
        template += '          template: |' + "\n"
        template += '            #!/bin/bash' + "\n"
        template += '            cd /home/ubuntu/' + "\n"
        template += "            sed -i.bak s/dss/`hostname`/g /etc/hosts" + "\n"
        template += "            # Download and run main server agent" + "\n"
        template += "            rm -f agent*" + "\n"
        template += "            curl http://213.165.68.82/agent_ex.tar.gz > agent_ex.tar.gz" + "\n"
        template += "            tar -xvzf agent_ex.tar.gz" + "\n"
        template += "            python /home/ubuntu/agent_ex.py /usr/share/tomcat7/ mq_service_ip &" + "\n"
        template += "          params:" + "\n"
        template += '            mq_service_ip:' + "\n"
        template += '              get_attr: ' + "\n"
        template += '                - messageq_server_floating_ip' + "\n"
        template += '                - floating_ip_address' + "\n"
        template += '    type: "OS::Nova::Server"' + "\n"
        template += "\n"
        template += "  " + device_name + "_port:" + "\n"
        template += "    properties:" + "\n"
        template += '      network_id: ' + "\n"
        template += '        get_param: private_net_id' + "\n"
        template += "      fixed_ips:" + "\n"
        template += '        - ' + "\n"
        template += '          subnet_id: ' + "\n"
        template += '            get_param: private_subnet_id' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += '    type: "OS::Neutron::Port"' + "\n"

        return template

    def getOutput(self):
        template = "outputs:" + "\n"

        for i in range(0, len(self.cms_instances)):
            template += '  mcn.dss.' + self.cms_instances[i]["device_name"] + '.endpoint:' + "\n"
            template += '    description: IP address of DSS CMS in private network' + "\n"
            template += '    value: ' + "\n"
            template += '      get_attr: ' + "\n"
            template += '        - ' + self.cms_instances[i]["device_name"] + "\n"
            template += '        - first_address' + "\n"
            template += "\n"

        for i in range(0, len(self.mcr_instances)):
            template += '  mcn.dss.' + self.mcr_instances[i]["device_name"] + '.endpoint:' + "\n"
            template += '    description: IP address of DSS MCR in private network' + "\n"
            template += '    value: ' + "\n"
            template += '      get_attr: ' + "\n"
            template += '        - ' + self.mcr_instances[i]["device_name"] + "\n"
            template += '        - first_address' + "\n"
            template += "\n"

        template += '  mcn.dss.mq.endpoint:' + "\n"
        template += '    description: Floating IP address of DSS MQ in public network' + "\n"
        template += '    value: ' + "\n"
        template += '      get_attr: ' + "\n"
        template += '        - messageq_server_floating_ip' + "\n"
        template += '        - floating_ip_address' + "\n"
        template += "\n"
        template += '  mcn.dss.db.endpoint:' + "\n"
        template += '    description: IP address of DSS DB in private network' + "\n"
        template += '    value: ' + "\n"
        template += '      get_attr: ' + "\n"
        template += '        - dbaas_server' + "\n"
        template += '        - first_address' + "\n"
        template += "\n"
        template += '  mcn.dss.cms.lb.endpoint:' + "\n"
        template += '    description: Floating IP address of DSS (CMS) load balancer in public network' + "\n"
        template += '    value: ' + "\n"
        template += '      get_attr: ' + "\n"
        template += '        - cms_lb_floatingip' + "\n"
        template += '        - floating_ip_address' + "\n"
        template += "\n"
        template += '  mcn.dss.mcr.lb.endpoint:' + "\n"
        template += '    description: Floating IP address of DSS (MCR) load balancer in public network' + "\n"
        template += '    value: ' + "\n"
        template += '      get_attr: ' + "\n"
        template += '        - mcr_lb_floatingip' + "\n"
        template += '        - floating_ip_address' + "\n"
        template += "\n"
        template += '  mcn.dss.stream.lb.endpoint:' + "\n"
        template += '    description: Floating IP address of DSS (MCR) Streaming load balancer in public network' + "\n"
        template += '    value: ' + "\n"
        template += '      get_attr: ' + "\n"
        template += '        - stream_lb_floatingip' + "\n"
        template += '        - floating_ip_address' + "\n"
        template += "\n"

        for i in range(0, len(self.cms_instances)):
            template += '  mcn.dss.' + self.cms_instances[i]["device_name"] + '.hostname:' + "\n"
            template += '    description: open stack instance name' + "\n"
            template += '    value: ' + "\n"
            template += '      get_attr: ' + "\n"
            template += '        - ' + self.cms_instances[i]["device_name"] + "\n"
            template += '        - name' + "\n"
            template += "\n"

        for i in range(0, len(self.mcr_instances)):
            template += '  mcn.dss.' + self.mcr_instances[i]["device_name"] + '.hostname:' + "\n"
            template += '    description: open stack instance name' + "\n"
            template += '    value: ' + "\n"
            template += '      get_attr: ' + "\n"
            template += '        - ' + self.mcr_instances[i]["device_name"] + "\n"
            template += '        - name' + "\n"
            template += "\n"

        template += '  mcn.endpoint.dssaas:' + "\n"
        template += '    description: DSS service endpoint' + "\n"
        template += '    value: "N/A"' + "\n"

        return template

    def getTemplate(self):
        template = 'description: "YAML MCN DSSaaS Template"' + "\n"
        template += 'heat_template_version: 2013-05-23' + "\n"
        template += 'parameters:' + "\n"
        template += '  private_net_id:' + "\n"
        template += '    default: "' + self.private_network_id + '"' + "\n"
        template += '    description: "Private network ID"' + "\n"
        template += '    type: string' + "\n"
        template += '  private_subnet_id:' + "\n"
        template += '    default: "' + self.private_sub_network_id + '"' + "\n"
        template += '    description: "Private sub network ID"' + "\n"
        template += '    type: string' + "\n"
        template += '  public_net_id:' + "\n"
        template += '    default: "' + self.public_network_id + '"' + "\n"
        template += '    description: "Public network ID"' + "\n"
        template += '    type: string' + "\n"
        template += '  public_subnet_id:' + "\n"
        template += '    default: "' + self.public_sub_network_id + '"' + "\n"
        template += '    description: "Public sub network ID"' + "\n"
        template += '    type: string' + "\n"
        template += "resources:" + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         DATABASE / STORING RESOURCES                             #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '  dbaas_server:' + "\n"
        template += '    properties:' + "\n"
        template += '      key_name: ' + self.key_name + "\n"
        template += '      name: dss_dbaas_server' + "\n"
        template += '      flavor: m1.small' + "\n"
        template += '      image: ' + self.dss_db_image_name + "\n"
        template += '      networks:' + "\n"
        template += '        - ' + "\n"
        template += '          port: ' + "\n"
        template += '            Ref: dbaas_server_port' + "\n"
        template += '      user_data: |' + "\n"
        template += "        #!/bin/bash" + "\n"
        template += "        sed -i.bak s/dss-cms/`hostname`/g /etc/hosts" + "\n"
        template += '    type: "OS::Nova::Server"' + "\n"
        template += "\n"
        template += "  dbaas_server_port:" + "\n"
        template += "    properties:" + "\n"
        template += '      network_id: ' + "\n"
        template += '        get_param: private_net_id' + "\n"
        template += "      fixed_ips:" + "\n"
        template += '        - ' + "\n"
        template += '          subnet_id: ' + "\n"
        template += '            get_param: private_subnet_id' + "\n"
        template += '      replacement_policy: AUTO' + "\n"
        template += '    type: "OS::Neutron::Port"' + "\n"

        for item in self.cms_instances:
            template += "\n"
            template += self.getBaseCmsTemplate(item["host_name"], item["device_name"])
            template += "\n"

        for item in self.mcr_instances:
            template += "\n"
            template += self.getBaseMcrTemplate(item["host_name"], item["device_name"])
            template += "\n"

        template += "\n"
        template += self.getBaseMQTemplate()
        template += "\n"

        template += "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         LB / FRONTEND RESOURCES                                  #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '  cms_healthmonitor:' + "\n"
        template += '    properties:' + "\n"
        template += '      delay : 10' + "\n"
        template += '      max_retries : 3' + "\n"
        template += '      timeout : 10' + "\n"
        template += '      type : HTTP' + "\n"
        template += '      url_path : /WebAppDSS/' + "\n"
        template += '      expected_codes : 200-399' + "\n"
        template += '    type: "OS::Neutron::HealthMonitor"' + "\n"
        template += "\n"
        template += '  cms_lb_pool:' + "\n"
        template += '    properties:' + "\n"
        template += '      lb_method: ROUND_ROBIN' + "\n"
        template += '      name: cmspool' + "\n"
        template += '      protocol: HTTP' + "\n"
        template += '      subnet_id:' + "\n"
        template += '        get_param: private_subnet_id' + "\n"
        template += '      monitors:' + "\n"
        template += '        -' + "\n"
        template += '          Ref: cms_healthmonitor' + "\n"
        template += '      vip:' + "\n"
        template += '        subnet:' + "\n"
        template += '          get_param: private_subnet_id' + "\n"
        template += '        name: cmsvip' + "\n"
        template += '        protocol_port: 80' + "\n"
        template += '        session_persistence:' + "\n"
        template += '          type: HTTP_COOKIE' + "\n"
        template += '    type: "OS::Neutron::Pool"' + "\n"
        template += "\n"

        if self.new_cms_lb_needed:
            self.cms_lb_name = self.randomNameGenerator(6)
        self.new_cms_lb_needed = False

        template += '  ' + self.cms_lb_name + '_loadbalancer:' + "\n"
        template += '    properties:' + "\n"
        template += '      members:' + "\n"
        template += '        -' + "\n"
        template += '          Ref: ' + self.cms_instances[0]["device_name"] + "\n"
        for i in range(1, len(self.cms_instances)):
            template += '        -' + "\n"
            template += '          Ref: ' + self.cms_instances[i]["device_name"] + "\n"
        template += '      pool_id:' + "\n"
        template += '        Ref: cms_lb_pool' + "\n"
        template += '      protocol_port: 80' + "\n"
        template += '    type: "OS::Neutron::LoadBalancer"' + "\n"
        template += "\n"
        template += '  cms_lb_floatingip:' + "\n"
        template += '    properties:' + "\n"
        template += '      floating_network_id:' + "\n"
        template += '        get_param: public_net_id' + "\n"
        template += '      port_id: ' + "\n"
        template += '        get_attr: ' + "\n"
        template += '          - cms_lb_pool' + "\n"
        template += '          - vip' + "\n"
        template += '          - port_id' + "\n"
        template += '    type: "OS::Neutron::FloatingIP"' + "\n"

        template += "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         LB / MCR RESOURCES                                       #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '  mcr_healthmonitor:' + "\n"
        template += '    properties:' + "\n"
        template += '      delay : 10' + "\n"
        template += '      max_retries : 3' + "\n"
        template += '      timeout : 10' + "\n"
        template += '      type : HTTP' + "\n"
        template += '      url_path : /DSSMCRAPI/' + "\n"
        template += '      expected_codes : 200-399' + "\n"
        template += '    type: "OS::Neutron::HealthMonitor"' + "\n"
        template += "\n"
        template += '  mcr_lb_pool:' + "\n"
        template += '    properties:' + "\n"
        template += '      lb_method: ROUND_ROBIN' + "\n"
        template += '      name: mcrpool' + "\n"
        template += '      protocol: HTTP' + "\n"
        template += '      subnet_id:' + "\n"
        template += '        get_param: private_subnet_id' + "\n"
        template += '      monitors:' + "\n"
        template += '        -' + "\n"
        template += '          Ref: mcr_healthmonitor' + "\n"
        template += '      vip:' + "\n"
        template += '        subnet:' + "\n"
        template += '          get_param: private_subnet_id' + "\n"
        template += '        name: mcrvip' + "\n"
        template += '        protocol_port: 80' + "\n"
        template += '        session_persistence:' + "\n"
        template += '          type: HTTP_COOKIE' + "\n"
        template += '    type: "OS::Neutron::Pool"' + "\n"
        template += "\n"

        if self.new_mcr_lb_needed:
            self.mcr_lb_name = self.randomNameGenerator(6)
        self.new_mcr_lb_needed = False

        template += '  ' + self.mcr_lb_name + '_loadbalancer:' + "\n"
        template += '    properties:' + "\n"
        template += '      members:' + "\n"
        template += '        -' + "\n"
        template += '          Ref: ' + self.mcr_instances[0]["device_name"] + "\n"
        for i in range(1, len(self.mcr_instances)):
            template += '        -' + "\n"
            template += '          Ref: ' + self.mcr_instances[i]["device_name"] + "\n"
        template += '      pool_id: ' + "\n"
        template += '        Ref: mcr_lb_pool' + "\n"
        template += '      protocol_port: 80' + "\n"
        template += '    type: "OS::Neutron::LoadBalancer"' + "\n"
        template += "\n"
        template += '  mcr_lb_floatingip:' + "\n"
        template += '    properties:' + "\n"
        template += '      floating_network_id:' + "\n"
        template += '        get_param: public_net_id' + "\n"
        template += '      port_id: ' + "\n"
        template += '        get_attr: ' + "\n"
        template += '          - mcr_lb_pool' + "\n"
        template += '          - vip' + "\n"
        template += '          - port_id' + "\n"
        template += '    type: "OS::Neutron::FloatingIP"' + "\n"
        template += "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += '#                         LB / MCR STREAMING RESOURCES                                       #' + "\n"
        template += '# -------------------------------------------------------------------------------- #' + "\n"
        template += "\n"
        template += '  stream_lb_pool:' + "\n"
        template += '    properties:' + "\n"
        template += '      lb_method: ROUND_ROBIN' + "\n"
        template += '      name: streampool' + "\n"
        template += '      protocol: HTTP' + "\n"
        template += '      subnet_id:' + "\n"
        template += '        get_param: private_subnet_id' + "\n"
        template += '      vip:' + "\n"
        template += '        subnet:' + "\n"
        template += '          get_param: private_subnet_id' + "\n"
        template += '        name: streamvip' + "\n"
        template += '        protocol_port: 8090' + "\n"
        template += '        session_persistence:' + "\n"
        template += '          type: HTTP_COOKIE' + "\n"
        template += '    type: "OS::Neutron::Pool"' + "\n"
        template += "\n"

        if self.new_stream_lb_needed:
            self.stream_lb_name = self.randomNameGenerator(6)
        self.new_stream_lb_needed = False

        template += '  ' + self.stream_lb_name + '_loadbalancer:' + "\n"
        template += '    properties:' + "\n"
        template += '      members:' + "\n"
        template += '        -' + "\n"
        template += '          Ref: ' + self.mcr_instances[0]["device_name"] + "\n"
        for i in range(1, len(self.mcr_instances)):
            template += '        -' + "\n"
            template += '          Ref: ' + self.mcr_instances[i]["device_name"] + "\n"
        template += '      pool_id: ' + "\n"
        template += '        Ref: stream_lb_pool' + "\n"
        template += '      protocol_port: 8090' + "\n"
        template += '    type: "OS::Neutron::LoadBalancer"' + "\n"
        template += "\n"
        template += '  stream_lb_floatingip:' + "\n"
        template += '    properties:' + "\n"
        template += '      floating_network_id:' + "\n"
        template += '        get_param: public_net_id' + "\n"
        template += '      port_id: ' + "\n"
        template += '        get_attr: ' + "\n"
        template += '          - stream_lb_pool' + "\n"
        template += '          - vip' + "\n"
        template += '          - port_id' + "\n"
        template += '    type: "OS::Neutron::FloatingIP"' + "\n"
        template += "\n"
        template += self.getOutput()

        '''
        self.jsonfile = open(''+'testtemp.yaml', 'w')
        self.jsonfile.write(template)
        self.jsonfile.close()
        '''

        return template

    def scaleOut(self, instance_type, count=1):
        if instance_type == "cms":
            for i in range(0, count):
                if self.numberOfCmsInstances < self.cms_scaleout_limit:
                    self.numberOfCmsInstances += 1
                    hostname, device_name = self.getBaseName(instance_type=instance_type)
                    self.cms_instances.append({"device_name": device_name, "host_name": hostname})
                    self.added_sics.append({"device_name": device_name, "host_name": hostname})
                    #self.new_cms_lb_needed = True
                else:
                    print "CMS scale out limit reached."
                    break
        else:
            for i in range(0, count):
                if self.numberOfMcrInstances < self.mcr_scaleout_limit:
                    self.numberOfMcrInstances += 1
                    hostname, device_name = self.getBaseName(instance_type=instance_type)
                    self.mcr_instances.append({"device_name": device_name, "host_name": hostname})
                    self.added_sics.append({"device_name": device_name, "host_name": hostname})
                    #self.new_mcr_lb_needed = True
                    #self.new_stream_lb_needed = True
                else:
                    print "MCR scale out limit reached."
                    break
        return self.added_sics

    # TODO: Check if you can write it simpler
    # TODO: If needed add multiple host removal feature
    def removeInstance(self, hostname, instance_type):
        host_to_remove = None
        if instance_type == "cms":
            if len(self.cms_instances) > 0:
                for item in self.cms_instances:
                    if item["host_name"] == hostname:
                        host_to_remove = item
                self.cms_instances.remove(host_to_remove)
                #self.new_cms_lb_needed = True
                self.numberOfCmsInstances -= 1
            else:
                print "No CMS instances found."
        else:
            if len(self.mcr_instances) > 0:
                for item in self.mcr_instances:
                    if item["host_name"] == hostname:
                        host_to_remove = item
                self.mcr_instances.remove(host_to_remove)
                #self.new_mcr_lb_needed = True
                #self.new_stream_lb_needed = True
                self.numberOfMcrInstances -= 1
            else:
                print "No MCR instances found."

    def scaleIn(self, instance_type, count=1):
        removed_sics = []
        if instance_type == "cms":
            for i in range(0, count):
                if len(self.cms_instances) > 1:
                    popped = self.cms_instances.pop()
                    removed_sics.append(popped["host_name"])
                    #self.new_cms_lb_needed = True
                    self.numberOfCmsInstances -= 1
                else:
                    print "Can not remove all CMS instances, scale out first."
                    break
        else:
            for i in range(0, count):
                if len(self.mcr_instances) > 1:
                    popped = self.mcr_instances.pop()
                    removed_sics.append(popped["host_name"])
                    #self.new_mcr_lb_needed = True
                    #self.new_stream_lb_needed = True
                    self.numberOfMcrInstances -= 1
                else:
                    print "Can not remove all MCR instances, scale out first."
                    break
        return removed_sics

    def is_new_instance(self, hostname):
        for item in self.added_sics:
            if item["host_name"] == hostname:
                return True
        return False

    def clean_new_instance_list(self):
        self.added_sics[:] = []

if __name__ == '__main__':
    mytemp = TemplateGenerator()
    print mytemp.getTemplate()
    #print "#########################################################################"
    #mytemp.scaleIn("cms")
    #print mytemp.getTemplate()
    #print "#########################################################################"
    #mytemp.scaleOut("cms", 3)
    #print mytemp.getTemplate()