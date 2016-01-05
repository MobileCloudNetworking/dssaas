#   Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
#   Copyright 2015 Zuercher Hochschule fuer Angewandte Wissenschaften
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
DSS SO.
"""

from sm.so import service_orchestrator
from TemplateGenerator import *
from SOMonitor import *
from dnsaascli import *
import graypy
import datetime

from sdk.mcn import util

def config_logger(log_level=logging.DEBUG, mode='normal'):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    if mode is 'graylog':
        gray_handler = graypy.GELFHandler('log.cloudcomplab.ch', 12201)
        logger.addHandler(gray_handler)
    return logger

LOG = config_logger()
GLOG = config_logger(mode='graylog')

class ServiceOrchestratorExecution(service_orchestrator.Execution):
    """
    Sample SO execution part.
    """
    def __init__(self, tenant, token, ready_event):
        super(ServiceOrchestratorExecution, self).__init__(token, tenant)
        self.event = ready_event
        self.swComponent = 'SO-Execution'
        # Generate DSS basic template...
        self.token = token
        self.tenant_name = tenant
        self.region_name = 'RegionOne'
        self.templateManager = TemplateGenerator()
        self.template = self.templateManager.getTemplate()
        self.templateUpdate = ""
        self.stack_id = None
        #Variables of other services
        self.dssCmsDomainName = "dssaas.mcn.com"
        self.dssMcrDomainName = "dssaas.mcn.com"
        self.dssCmsRecordName = "cms"
        self.dssMcrRecordName = "mcr"
        self.monitoring_endpoint = None
        self.icn_endpoint = None
        self.dns_forwarder = None
        self.dns_api = None
        self.dnsManager = None
        self.update_start = 0
        self.update_end = 0

        # make sure we can talk to deployer...
        LOG.debug(self.swComponent + ' ' + 'Make sure we can talk to deployer...')
        LOG.debug("About to get the deployer with token :" + str(self.token + " Tenant name : " + self.tenant_name))
        self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name, region=self.region_name)
        LOG.debug("Got the deployer")

    def design(self):
        """
        Do initial design steps here.
        """
        LOG.debug('Executing design logic')
        self.resolver.design()

    def deploy(self, entity):
        """
        deploy SICs.
        """
        LOG.debug('Deploy service dependencies')
        self.resolver.deploy()
        LOG.debug('Executing deployment logic')
        if self.stack_id is None:
            self.stack_id = self.deployer.deploy(self.template, self.token, name='dssaas_' + str(random.randint(1000, 9999)))

        #self.event.set()

    def provision(self, entity, attrib):
        """
        (Optional) if not done during deployment - provision.
        """
        self.resolver.provision()

        # once logic executes, deploy phase is done
        self.event.set()

    def dispose(self):
        """
        Dispose SICs.
        """
        LOG.info('Disposing of 3rd party service instances...')
        self.resolver.dispose()
        LOG.debug('Executing disposal logic')
        if self.stack_id is not None:
            self.deployer.dispose(self.stack_id, self.token)
            self.stack_id = None

        # TODO on disposal, the SOE should notify the SOD to shutdown its thread

    def update_stack(self):
        """
        update SICs.
        """
        LOG.debug('Executing disposal logic')
        if self.stack_id is not None:
            self.deployer.update(self.stack_id, self.templateUpdate, self.token)

    def update(self, updated):
        """
        update EPs.
        """
        # TODO add you provision phase logic here
        #
        if updated.attributes:
            LOG.debug('DSS SO update - attributes')
            LOG.debug(self.swComponent + ' ' + 'Got DSS SO attributes in update')
            #print attributes
            if 'mcn.endpoint.maas' in updated.attributes:
                self.monitoring_endpoint = updated.attributes['mcn.endpoint.maas']
                LOG.debug(self.swComponent + ' ' + 'MaaS EP is: ' + self.monitoring_endpoint)
            if 'mcn.endpoint.forwarder' in updated.attributes:
                self.dns_forwarder = updated.attributes['mcn.endpoint.forwarder']
                LOG.debug(self.swComponent + ' ' + 'DNS forwarder EP is: ' + self.dns_forwarder)
            if 'mcn.endpoint.api' in updated.attributes:
                self.dns_api = updated.attributes['mcn.endpoint.api']
                self.dnsManager = DnsaasClientAction(self.dns_api, token=self.token)
                LOG.debug(str(self.dnsManager))
                LOG.debug(self.swComponent + ' ' + 'DNS EP is: ' + self.dns_api)

    def state(self):
        """
        Report on state.
        """
        resolver_state = self.resolver.state()
        #LOG.info('Resolver state:')
        #LOG.info(resolver_state.__repr__())
        LOG.debug('Executing state retrieval logic')
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp.get('output', None) is not None:
                for i in tmp['output']:
                    # DSS Load Balancer address
                    if i['output_key'] == "mcn.endpoint.dssaas":
                        LOG.debug('Found key mcn.endpoint.dssaas with value: ' + i['output_value'])
                        result = -1
                        instances = None
                        while (result < 0):
                            time.sleep(1)
                            result, instances = self.getServerIPs()
                            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(instances))

                        for item in instances:
                            if item == "mcn.dss.cms.lb.endpoint":
                                i['output_value'] = instances[item]
                        #i['output_value'] = 'http://' + self.dssDashboardRecordName + '.' + self.dssCmsDomainName + ':8080/WebAppDSS/'
                        LOG.debug('Replaced mcn.endpoint.dssaas value with: ' + i['output_value'])
                return tmp['state'], self.stack_id, tmp['output']
            else:
                LOG.debug('Output was None :-/')
                return tmp['state'], self.stack_id, None

        return 'Unknown', 'N/A'

    # This is not part of the SOE interface
    #def update(self, updated_service):
        # TODO implement your own update logic - this could be a heat template update call
        #pass
    # Getting the deployed SIC hostnames using the output of deployed stack (Heat Output)
    def getServerNamesList(self):
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp['state'] != 'CREATE_COMPLETE' and tmp['state'] != 'UPDATE_COMPLETE':
                return -1, 'Stack is currently being deployed...'
            else:
                serverList = []
                for i in range(0 ,len(tmp["output"])):
                    if "hostname" in tmp["output"][i]["output_key"]:
                        serverList.append(str(tmp["output"][i]["output_value"]))

                return 0, serverList
        else:
            return -1, 'Stack is not deployed atm.'

    # Getting the deployed SIC floating IPs using the output of deployed stack (Heat Output)
    def getServerIPs(self):
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp['state'] != 'CREATE_COMPLETE' and tmp['state'] != 'UPDATE_COMPLETE':
                return -1, 'Stack is currently being deployed...'
            else:
                #serverList = []
                serverList = {}
                for i in range(0 ,len(tmp["output"])):
                    if "hostname" not in tmp["output"][i]["output_key"]:
                        serverList[tmp["output"][i]["output_key"]] = tmp["output"][i]["output_value"]

                return 0, serverList
        else:
            return -1, 'Stack is not deployed atm.'

    # Returns the current number of CMS VMs deployed in the stack for scaling purposes
    def getNumberOfCmsInstances(self):
        return self.templateManager.numberOfCmsInstances

    def getNumberOfMcrInstances(self):
        return self.templateManager.numberOfMcrInstances

    def notify(self, entity, attributes, extras):
        super(ServiceOrchestratorExecution, self).notify(entity, attributes, extras)
        # TODO here you can add logic to handle a notification event sent by the CC
        # XXX this is optional

class ServiceOrchestratorDecision(service_orchestrator.Decision, threading.Thread):
    """
    Sample Decision part of SO.
    """

    def __init__(self, so_e, tenant, token, ready_event):
        super(ServiceOrchestratorDecision, self).__init__(so_e, token, tenant)
        self.event = ready_event
        self.swComponent = 'SO-Decision'
        threading.Thread.__init__(self)

        # Get service orchestrator execution reference
        self.so_e = so_e
        self.token = token

        # Variables used for checking current DSS instance status according to monitoring triggers
        self.decisionArray = {}
        self.hostsWithIssues = []
        self.playerCount = 0
        self.decisionMapMCR = [{"More than 90% hard disk usage on {HOST.NAME}": 0},
                               {"Less than 30% hard disk usage on {HOST.NAME}": 0}]
                               #{"Number of active players on {HOST.NAME}":0}]

        self.decisionMapCMS = [{"More than 30% cpu utilization for more than 1 minute on {HOST.NAME}": 0},
                               {"Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}": 0}]

        # Creating a configuring object ( REST client for SO::SIC interface )
        self.configure = SOConfigure(self.so_e, self, self.event)

        # Scaling guard time
        self.cmsScaleInThreshold = 450#in seconds
        self.mcrScaleDownThreshold = 450#in seconds

        # Number of players needed for each scale out/in
        self.playerCountLimit = 5.0

        # Current scaling status
        self.lastCmsScale = 0
        self.lastMcrScale = 0
        self.numberOfScaleUpsPerformed = 0
        self.numberOfCmsScaleOutsPerformed = 0
        self.numberOfMcrScaleOutsPerformed = 0

        self.timeout = 10

    def run(self):
        """
        Decision part implementation goes here.
        """
        # it is unlikely that logic executed will be of any use until the provisioning phase has completed
        LOG.debug('Waiting for deploy and provisioning to finish')
        self.event.wait()
        self.configure.start()
        LOG.debug('Waiting for local config to finish')
        self.event.clear()
        self.event.wait()
        LOG.debug('Starting runtime logic...')
        # TODO implement you runtime logic here - you should probably release the locks afterwards, maybe in stop ;-)
        # Start pushing configurations to SICs



        # Decision loop
        while(1):
            instanceListInCaseOfScaleIn = None
            LOG.debug(self.swComponent + ' ' + "Start of decision loop ...")
            time.sleep(3)
            cmsCount = self.so_e.getNumberOfCmsInstances()
            mcrCount = self.so_e.getNumberOfMcrInstances()
            #Reseting the values in decision map
            for item in self.decisionMapCMS:
                item[item.keys()[0]] = 0
            for item in self.decisionMapMCR:
                item[item.keys()[0]] = 0
            LOG.debug(self.swComponent + ' ' + "DecisionMap reset successful")

            # Update decision map
            for item in self.hostsWithIssues:
                for row in self.decisionArray:
                    if item == row:
                        if "cms" in self.decisionArray[row][0]:
                            self.updateDecisionMap("cms", self.decisionArray[row][1])
                        else:
                            self.updateDecisionMap("mcr", self.decisionArray[row][1])
            LOG.debug(self.swComponent + ' ' + str(self.decisionMapCMS))
            LOG.debug(self.swComponent + ' ' + str(self.decisionMapMCR))
            LOG.debug(self.swComponent + ' ' + "DecisionMap update successful")

            # Take scaling decisions according to updated map and sending corresponding command to the Execution part
            scaleTriggered = False
            cmsScaleOutTriggered = False
            cmsScaleInTriggered = False
            LOG.debug(self.swComponent + ' ' + "Checking CMS status")
            for item in self.decisionMapCMS:
                if item.keys()[0] == "More than 30% cpu utilization for more than 1 minute on {HOST.NAME}":
                    LOG.debug(self.swComponent + ' ' + "More than 30% cpu utilization for more than 1 minute on " + str(item[item.keys()[0]]) + " CMS machine(s)")
                elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}":
                    LOG.debug(self.swComponent + ' ' + "Less than 10% cpu utilization for more than 10 minutes on " + str(item[item.keys()[0]]) + " CMS machine(s)")
                LOG.debug(self.swComponent + ' ' + "Total CMS machine(s) count is: " + str(cmsCount))
                if item[item.keys()[0]] == cmsCount:
                    # CMS scale out
                    if item.keys()[0] == "More than 30% cpu utilization for more than 1 minute on {HOST.NAME}":
                        cmsScaleOutTriggered = True
                    # CMS scale in
                    elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}" and self.numberOfCmsScaleOutsPerformed > 0:
                        cmsScaleInTriggered = True

            #Calculate the player scaling situation
            numOfCmsNeeded = int((float(self.playerCount)/self.playerCountLimit) + 1)
            LOG.debug(self.swComponent + ' ' + "Number of CMS needed is: " + str(numOfCmsNeeded) + " and we have: " + str(cmsCount))
            #CMS scale out because more than specific number of players
            if numOfCmsNeeded > cmsCount or cmsScaleOutTriggered:
                self.lastCmsScale = time.time()
                self.so_e.templateManager.scaleOut("cms")
                self.numberOfCmsScaleOutsPerformed += 1
                if cmsScaleOutTriggered is not True:
                    cmsScaleOutTriggered = True
                scaleTriggered = True
                LOG.debug(self.swComponent + ' ' + "IN CMS scaleOut")

            if self.lastCmsScale == 0:
                diff = 0
            else:
                diff = int(time.time() - self.lastCmsScale)
            LOG.debug(self.swComponent + ' ' + "Number of scale outs performed: " + str(self.numberOfCmsScaleOutsPerformed))
            LOG.debug(self.swComponent + ' ' + "Last CMS scale action happened " + str(diff) + " second(s) ago")
            LOG.debug(self.swComponent + ' ' + "Threshold for CMS scale in is: " + str(self.cmsScaleInThreshold) + " second(s)")
            LOG.debug(self.swComponent + ' ' + "CMS cpu metric scale in triggered: " + str(cmsScaleInTriggered))
            if diff > self.cmsScaleInThreshold or self.lastCmsScale == 0:
                #CMS scale out because less than specific number of players
                if  numOfCmsNeeded < cmsCount and self.numberOfCmsScaleOutsPerformed > 0 and cmsScaleInTriggered:
                    self.lastCmsScale = time.time()
                    self.so_e.templateManager.scaleIn("cms")
                    self.numberOfCmsScaleOutsPerformed -= 1
                    scaleTriggered = True
                    LOG.debug(self.swComponent + ' ' + "IN CMS scaleIn")
                    # Get a backup of the server name list
                    result = -1
                    while (result < 0):
                        time.sleep(1)
                        result, instanceListInCaseOfScaleIn = self.so_e.getServerNamesList()

            for item in self.decisionMapMCR:
                LOG.debug(self.swComponent + ' ' + "Checking MCR status")
                if self.lastMcrScale == 0:
                    diff = 0
                else:
                    diff = int(time.time() - self.lastMcrScale)
                if item[item.keys()[0]] > 0:
                    # MCR scale up
                    # It is commented because it's not working for current heat version )
                    if item.keys()[0] == "More than 90% hard disk usage on {HOST.NAME}":
                        LOG.debug(self.swComponent + ' ' + "More than 90% hard disk usage on MCR machine")
                        self.lastMcrScale = time.time()
                        #self.so_e.templateManager.templateToScaleUp()
                        self.numberOfScaleUpsPerformed += 1
                        #scaleTriggered = True
                        LOG.debug(self.swComponent + ' ' + "IN MCR scaleUp")
                    # MCR scale down
                    elif  item.keys()[0] == "Less than 30% hard disk usage on {HOST.NAME}" and self.numberOfScaleUpsPerformed > 0 and diff > self.mcrScaleDownThreshold:
                        LOG.debug(self.swComponent + ' ' + "Less than 30% hard disk usage on MCR machine")
                        LOG.debug(self.swComponent + ' ' + "Number of scale ups performed: " + str(self.numberOfScaleUpsPerformed))
                        LOG.debug(self.swComponent + ' ' + "Last MCR scale action happened " + str(diff) + " second(s) ago")
                        LOG.debug(self.swComponent + ' ' + "Threshold for MCR scale down is: " + str(self.mcrScaleDownThreshold) + " second(s)")
                        self.lastMcrScale = time.time()
                        #self.so_e.templateManager.templateToScaleDown()
                        self.numberOfScaleUpsPerformed -= 1
                        #scaleTriggered = True
                        LOG.debug(self.swComponent + ' ' + "IN MCR scaleDown")

            # Call SO execution if scaling required
            LOG.debug(self.swComponent + ' ' + str(scaleTriggered))
            if scaleTriggered:
                self.configure.monitor.mode = "idle"
                self.so_e.templateUpdate = self.so_e.templateManager.getTemplate()

                # find the deleted host from the server list backup
                #zHostToDelete = None
                #if instanceListInCaseOfScaleIn is not None:
                #    for item in instanceListInCaseOfScaleIn:
                #        if self.so_e.templateManager.cmsHostToRemove in item:
                #            zHostToDelete = item

                LOG.debug(self.swComponent + ' ' + "Performing stack update")
                #Scale has started
                scale_type = None
                if cmsScaleInTriggered is True:
                    scale_type = 'scaling-in'
                elif cmsScaleOutTriggered is True:
                    scale_type = 'scaling-out'
                infoDict = {
                    'so_id': 'idnotusefulhere',
                    'sm_name': 'dssaas',
                    'so_phase': 'update',
                    'scaling': scale_type,
                    'phase_event': 'start',
                    'response_time': 0,
                    'tenant': self.so_e.tenant_name
                    }
                tmpJSON = json.dumps(infoDict)
                GLOG.debug(tmpJSON)
                self.so_e.update_start = datetime.datetime.now()
                self.so_e.update_stack()
                LOG.debug(self.swComponent + ' ' + "Update in progress ...")

                #Removing the deleted host from zabbix server
                #if zHostToDelete is not None:
                    #self.configure.monitor.removeHost(zHostToDelete.replace("_","-"))

                # Checking configuration status of the instances after scaling
                self.checkConfigurationStats(scale_type= scale_type)
                self.configure.monitor.mode = "checktriggers"

    # Goes through all available instances and checks if the configuration info is pushed to all SICs, if not, tries to push the info
    def checkConfigurationStats(self, scale_type):
        result = -1
        # Waits till the deployment of the stack is finished
        while(result == -1):
            time.sleep(1)
            result, listOfAllServers = self.so_e.getServerIPs()

        #Scale has finished
        LOG.debug(self.swComponent + ' ' + "Update Type: " + scale_type)
        self.so_e.update_end = datetime.datetime.now()
        diff = self.so_e.update_end - self.so_e.update_start
        infoDict = {
                    'so_id': 'idnotusefulhere',
                    'sm_name': 'dssaas',
                    'so_phase': 'update',
                    'scaling': scale_type,
                    'phase_event': 'done',
                    'response_time': diff.total_seconds(),
                    'tenant': self.so_e.tenant_name
                    }
        tmpJSON = json.dumps(infoDict)
        GLOG.debug(tmpJSON)
        LOG.debug(self.swComponent + ' ' + "Update successful")
        LOG.debug(self.swComponent + ' ' + "Check config stat of instances")
        checkList = {}
        for item in listOfAllServers:
            if item != "mcn.dss.cms.lb.endpoint" and item != "mcn.dss.mcr.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.endpoint.dssaas":
                checkList[listOfAllServers[item]] = "unknown"

        # Talking to DSS SIC agents to get the configuration status of each
        while "unknown" in checkList.values():
            for item in checkList:
                if checkList[item] == "unknown":
                    response_status = 0
                    while (response_status < 200 or response_status >= 400):
                        time.sleep(1)
                        headers = {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json; charset=UTF-8'
                        }
                        target = 'http://' + item + ':8051/v1.0/configstat'
                        LOG.debug(self.swComponent + ' ' + target)
                        try:
                            h = http.Http()
                            h.timeout = self.timeout
                            LOG.debug(self.swComponent + ' ' + "Sending config request to " + item + ":")
                            response, content = h.request(target, 'GET', None, headers)
                            LOG.debug(self.swComponent + ' ' + "Config stat is: " + str(content))
                        except Exception as e:
                            LOG.debug(self.swComponent + ' ' + "Handled config request exception " + str(e))
                            continue
                        response_status = int(response.get("status"))
                        instanceInfo = json.loads(content)
                        if "False" not in instanceInfo.values():
                            LOG.debug(self.swComponent + ' ' + item + " already configured")
                            checkList[item] = "Configured"
                        else:
                            LOG.debug(self.swComponent + ' ' + 'Configuring ' + item)
                            LOG.debug(self.swComponent + ' ' + 'Configuring in progress ...')
                            self.configure.provisionInstance(item, listOfAllServers)
                            self.configure.configInstance(item)
                            LOG.debug(self.swComponent + ' ' + 'instance ' + item + ' configured successfully')
                            self.configure.deploymentPause()
                            response_status = 0
                            while (response_status < 200 or response_status >= 400):
                                time.sleep(1)
                                headers = {
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json; charset=UTF-8'
                                }
                                target = 'http://' + item + ':8051/v1.0/hostname'
                                LOG.debug(self.swComponent + ' ' + target)
                                try:
                                    h = http.Http()
                                    h.timeout = self.timeout
                                    LOG.debug(self.swComponent + ' ' + "Sending hostname request to " + item + ":")
                                    response, content = h.request(target, 'GET', None, headers)
                                except Exception as e:
                                    LOG.debug(self.swComponent + ' ' + "Handled hostname request exception " + str(e))
                                    continue
                                response_status = int(response.get("status"))
                                self.configure.SICMonConfig(content)

    # Updates the decision map according to the triggered triggers :-)
    def updateDecisionMap(self, type, description):
        if type == "cms":
            for item in self.decisionMapCMS:
                if item.keys()[0] == description:
                    item[description] += 1

        elif type == "mcr":
            for item in self.decisionMapMCR:
                if item.keys()[0] == description:
                    item[description] += 1

# Implements client part of DSS agent REST api to push configs into DSS SICs
class SOConfigure(threading.Thread):

    def __init__(self, so_e, so_d, ready_event):
        self.event = ready_event
        self.swComponent = 'SO-SIC-Config'
        threading.Thread.__init__(self)
        LOG.debug(self.swComponent + ' ' + "SOConfigure executed ................")

        self.so_e = so_e
        self.so_d = so_d

        self.dns_forwarder = None
        self.dns_api = None
        self.dssCmsDomainName = self.so_e.dssCmsDomainName
        self.dssMcrDomainName = self.so_e.dssMcrDomainName
        self.dssCmsRecordName = self.so_e.dssCmsRecordName
        self.dssMcrRecordName = self.so_e.dssMcrRecordName

        self.monitoring_endpoint = None
        self.monitor = None
        self.instances = None

        self.timeout = 10

        self.dependencyStat = {"DNS":"not ready","MON":"not ready"}

    def run(self):
        #Pushing DNS configurations to DNS SICs
        #------------------------------------------------------------------------------#
        # Comment the next 11 lines in case you are using SDK GET DNSaaS functionality #
        # And don't forget to set its stat to "Ready"                                  #
        # self.dependencyStat["DNS"] = "ready"                                         #
        #------------------------------------------------------------------------------#

        if self.so_e.templateManager.dns_enable == 'true':
            LOG.debug(self.swComponent + ' ' + "Waiting for DNS config info ...")
            while self.dependencyStat["DNS"] != "ready":
                if self.so_e.dns_api != None and self.so_e.dns_forwarder != None:
                    self.dns_forwarder = self.so_e.dns_forwarder
                    self.dns_api = self.so_e.dns_api
                    LOG.debug("DNS Forwarder EP: " + self.dns_forwarder)
                    LOG.debug("DNS api EP: " + self.dns_api)
                    self.performDNSConfig()
                    self.dependencyStat["DNS"] = "ready"
                time.sleep(3)
        else:
            self.dns_forwarder = '4.2.2.4'
            self.dependencyStat["DNS"] = "ready"
            LOG.debug("DNSaaS disabled, using " + self.dns_forwarder + " as DNS server")
        LOG.debug(self.swComponent + ' ' + "DNSaaS dependency stat changed to READY")

        LOG.debug(self.swComponent + ' ' + "Waiting for Monitoring config info ...")
        while self.dependencyStat["MON"] != "ready":
            if self.so_e.monitoring_endpoint != None:
                #Now that all DSS SICs finished application deployment we can start monitoring
                self.monitoring_endpoint = self.so_e.monitoring_endpoint
                LOG.debug(self.swComponent + ' ' + "MON EP: " + self.monitoring_endpoint)
                self.dependencyStat["MON"] = "ready"
            time.sleep(3)
        LOG.debug(self.swComponent + ' ' + "MONaaS dependency stat changed to READY")

        #Pushing local configurations to DSS SICs
        self.performLocalConfig()

        #Wait for DSS SICs to finish application deployment
        self.deploymentPause()

        # Creating a monitor for pulling MaaS information
        # We need it here because we need all teh custome items and everything configured before doing it

        self.monitor = SOMonitor(self.so_e, self.so_d, self.monitoring_endpoint, 0, 'http://' + self.monitoring_endpoint +'/zabbix/api_jsonrpc.php', 'admin', 'zabbix')
        self.performMonConfig()

        #LOG.debug(self.swComponent + ' ' + "Start monitoring service ...")
        self.monitor.start()
        # once logic executes, deploy phase is done
        self.event.set()

    def deploymentPause(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))

        #WAIT FOR FINISHING THE DEPLOYMENT
        for item in self.instances:
            if item != "mcn.dss.cms.lb.endpoint" and item != "mcn.dss.mcr.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.endpoint.dssaas":
                response_status = 0
                i = self.instances[item]
                while (response_status < 200 or response_status >= 400):
                    time.sleep(1)
                    headers = {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json; charset=UTF-8'
                    }
                    target = 'http://' + i + ':8051/v1.0/deploystat'
                    try:
                        h = http.Http()
                        h.timeout = self.timeout
                        LOG.debug(self.swComponent + ' ' + "Sending deployment status request to:" + target)
                        response, content = h.request(target, 'GET', None, headers)
                    except Exception as e:
                        LOG.debug(self.swComponent + ' ' + "Handled deployment status request exception." + str(e))
                        continue
                    response_status = int(response.get("status"))
                    LOG.debug(self.swComponent + ' ' + "response status is:" + str(response_status))

    def performDNSConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))

        #configure instances
        LOG.debug(self.swComponent + ' ' + "Entering the loop to push dns domain names for each instance ...")

        lbDomainExists = self.so_e.dnsManager.get_domain(self.dssCmsDomainName, self.so_e.token)
        if lbDomainExists.get('code', None) is not None and lbDomainExists['code'] == 404:
            result = -1
            while (result != 1):
                time.sleep(1)
                result = self.so_e.dnsManager.create_domain(self.dssCmsDomainName, "info@dss-test.es", 3600, self.so_e.token)
                LOG.debug(self.swComponent + ' ' + result.__repr__())
                LOG.debug(self.swComponent + ' ' + 'DNS domain creation attempt')
            LOG.debug(self.swComponent + ' ' + 'DNS domain created')
        else:
            LOG.debug(self.swComponent + ' ' + 'DNS domain already exists' + lbDomainExists.__repr__())

        for item in self.instances:
            if item == "mcn.dss.cms.lb.endpoint":
                lbRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssCmsDomainName, record_name=self.dssCmsRecordName, record_type='A', token=self.so_e.token)
                if lbRecordExists.get('code', None) is not None and lbRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(1)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssCmsDomainName,record_name=self.dssCmsRecordName, record_type='A', record_data=self.instances[item], token=self.so_e.token)
                        LOG.debug(self.swComponent + ' ' + result.__repr__())
                        LOG.debug(self.swComponent + ' ' + 'DNS record creation attempt for: ' + str(self.instances[item]))
                    LOG.debug(self.swComponent + ' ' + 'DNS record created for: ' + str(self.instances[item]))
                else:
                    LOG.debug(self.swComponent + ' ' + 'DNS record already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbRecordExists.__repr__())
            elif item == "mcn.dss.mcr.lb.endpoint":
                mcrRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', token=self.so_e.token)
                if mcrRecordExists.get('code', None) is not None and mcrRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(1)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', record_data=self.instances[item], token=self.so_e.token)
                        LOG.debug(self.swComponent + ' ' + result.__repr__())
                        LOG.debug(self.swComponent + ' ' + 'DNS record creation attempt for:' + str(self.instances[item]))
                    LOG.debug(self.swComponent + ' ' + 'DNS record created for: ' + str(self.instances[item]))
                else:
                    LOG.debug(self.swComponent + ' ' + 'DNS record already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbRecordExists.__repr__())

        LOG.debug(self.swComponent + ' ' + "Exiting the loop to push dns domain names for all instances")

    def performLocalConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))

        result = -1
        while (result < 0):
            time.sleep(1)
            result, serverList = self.so_e.getServerNamesList()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(serverList))

        #configure instances
        LOG.debug(self.swComponent + ' ' + "Entering the loop to provision each instance ...")
        for item in self.instances:
            if item != "mcn.dss.cms.lb.endpoint" and item != "mcn.dss.mcr.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.endpoint.dssaas":
                self.provisionInstance(self.instances[item], self.instances)

        LOG.debug(self.swComponent + ' ' + "Entering the loop to create JSON config file for each instance ...")
        for item in self.instances:
            if item != "mcn.dss.cms.lb.endpoint" and item != "mcn.dss.mcr.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.endpoint.dssaas":
                self.configInstance(self.instances[item])

        LOG.debug(self.swComponent + ' ' + "Exiting the loop for JSON config file creation for all instances")

    # Executes the two shell scripts in the SIC which takes care of war deployment
    def provisionInstance(self, target_ip, all_ips):
        #AGENT AUTH
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/auth', 'POST', '{"user":"SO","password":"SO"}')
        token = resp["token"]
        LOG.debug(self.swComponent + ' ' + "Auth response is:" + str(resp))
        #AGENT STARTS PROVISIONING OF VM
        #CMS ip address is sent to MCR for cross domain issues but as the player is trying to get contents from CMS DOMAIN NAME it will not work as it's an ip address
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/provision', 'POST', '{"user":"SO","token":"' + token + '","mcr_srv_ip":"' + all_ips["mcn.dss.mcr.lb.endpoint"] + '","cms_srv_ip":"' + all_ips["mcn.dss.cms.lb.endpoint"] + '","dbaas_srv_ip":"' + all_ips["mcn.dss.db.endpoint"] + '", "dbuser":"' + self.so_e.templateManager.dbuser +'", "dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}')
        LOG.debug(self.swComponent + ' ' + "Provision response is:" + str(resp))

    # Calls to the SIC agent to complete the provisioning
    def configInstance(self, target_ip):
        #AGENT AUTH
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/auth', 'POST', '{"user":"SO","password":"SO"}')
        token = resp["token"]
        LOG.debug(self.swComponent + ' ' + "Auth response is:" + str(resp))
        #AGENT PUSH DNS EP
        #DNS endpoint will be used later by CMS application to generate the player configuration script
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/DNS', 'POST', '{"user":"SO","token":"' + token + '","dnsendpoint":"'+ self.dns_forwarder + '","dssdomainname":"' + self.dssCmsRecordName + '.' + self.dssCmsDomainName + '"}')
        LOG.debug(self.swComponent + ' ' + "DNS response is:" + str(resp))
        #AGENT PUSH MON EP & CONFIG
        #MON endpoint is not really being used at the moment
        #DB info is being sent to be used by the getcdr script in zabbix custom item definitions
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/MON', 'POST', '{"user":"SO","token":"' + token + '","monendpoint":"' + self.monitoring_endpoint + '","dbuser":"' + self.so_e.templateManager.dbuser + '","dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}')
        LOG.debug(self.swComponent + ' ' + "MON response is:" + str(resp))
        #AGENT PUSH RCB CONFIG
        #DB info is used to create an event for generating cdr data in DB
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/RCB', 'POST', '{"user":"SO","token":"' + token + '","dbuser":"' + self.so_e.templateManager.dbuser + '","dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}')
        LOG.debug(self.swComponent + ' ' + "RCB response is:" + str(resp))

    def sendRequestToSICAgent(self, api_url, req_type, json_data):
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            try:
                h = http.Http()
                if 'provision' in api_url or 'MON' in api_url:
                    h.timeout = 60
                else:
                    h.timeout = self.timeout
                LOG.debug(self.swComponent + ' ' + "Sending request to:" + api_url)
                response, content = h.request(api_url, req_type, json_data, headers)
            except Exception as e:
                LOG.debug(self.swComponent + ' ' + "Handled " + api_url + " exception." + str(e))
                continue
            response_status = int(response.get("status"))
            LOG.debug(self.swComponent + ' ' + "response status is:" + str(response_status) + " Content: " + str(content))
            if (response_status < 200 or response_status >= 400):
                continue
            content_dict = json.loads(content)
            return content_dict
            #if response status is not OK, retry

    def performMonConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, serverList = self.so_e.getServerNamesList()

        for item in serverList:
            self.SICMonConfig(item)
        # Finished adding triggers so we change to monitoring mode
        self.monitor.mode = "checktriggers"

    def SICMonConfig(self,targetHostName):
        LOG.debug(self.swComponent + ' ' + time.strftime("%H:%M:%S"))
        LOG.debug(self.swComponent + ' ' + targetHostName)
        zabbixName = targetHostName.replace("_","-")

        if "mcr" in zabbixName:
            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.itemExists(zabbixName, "vfs.fs.size[/,pfree]")
                if res != 1:
                    res = self.monitor.configItem("Free disk space in %", zabbixName, "vfs.fs.size[/,pfree]", 0, 10)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.itemExists(zabbixName, "DSS.Players.CNT")
                if res != 1:
                    # 4 - Specifies data type "String" and 30 Specifies this item will be checked every 30 seconds
                    res = self.monitor.configItem("DSS number of active player data", zabbixName, "DSS.Players.CNT", 4, 30)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('More than 90% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}<10')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('Less than 30% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}>70')
        else:
            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('More than 30% cpu utilization for more than 1 minute on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].min(1m)}<70')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].avg(10m)}>90')
        res = 0
        while (res != 1):
            time.sleep(1)
            res = self.monitor.itemExists(zabbixName, "DSS.Player.Reqcount")
            if res != 1:
                # 4 - Specifies data type "String" and 60 Specifies this item will be checked every 60 seconds
                res = self.monitor.configItem("DSS players request count", zabbixName, "DSS.Player.Reqcount", 4, 60)

        LOG.debug(self.swComponent + ' ' + 'All triggers and items added succesfully for host: ' + targetHostName)

class ServiceOrchestrator(object):
    """
    Sample SO.
    """

    def __init__(self, token, tenant, isFirst = True):
        # this python thread event is used to notify the SOD that the runtime phase can execute its logic
        self.event = threading.Event()
        self.so_e = ServiceOrchestratorExecution(tenant, token, self.event)
        self.so_d = ServiceOrchestratorDecision(self.so_e, tenant=tenant, token=token, ready_event=self.event)
        LOG.debug('Starting SOD thread...')
        self.so_d.start()
