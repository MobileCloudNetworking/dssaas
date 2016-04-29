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
from MessagingService import *
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

        self.none_host_keys = ["mcn.dss.cms.lb.endpoint", "mcn.dss.mcr.lb.endpoint", "mcn.dss.db.endpoint",
                             "mcn.endpoint.dssaas", "mcn.dss.mq.endpoint"]

        # make sure we can talk to deployer...
        LOG.debug(self.swComponent + ' ' + 'Make sure we can talk to deployer...')
        LOG.debug("About to get the deployer with token :" + str(self.token + " Tenant name : " + self.tenant_name))
        try:
            self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name, region=self.region_name)
        except Exception as e:
            LOG.debug("Failed to get deployer")
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
        try:
            LOG.debug('Deploy service dependencies')
            self.resolver.deploy()
            LOG.debug('Executing deployment logic')
            if self.stack_id is None:
                self.stack_id = self.deployer.deploy(self.template, self.token, name='dssaas_' + str(random.randint(1000, 9999)))
        except Exception as e:
            LOG.debug("Failed to deploy stack")
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
        try:
            LOG.info('Disposing of 3rd party service instances...')
            self.resolver.dispose()
            LOG.debug('Executing disposal logic')
            if self.stack_id is not None:
                self.deployer.dispose(self.stack_id, self.token)
                self.stack_id = None
        except Exception as e:
            LOG.debug("Failed to delete stack")

        # TODO on disposal, the SOE should notify the SOD to shutdown its thread

    def update_stack(self):
        """
        update SICs.
        """
        try:
            LOG.debug('Executing scale logic')
            if self.stack_id is not None:
                self.deployer.update(self.stack_id, self.templateUpdate, self.token)
        except Exception as e:
            LOG.debug("Failed to update stack")

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
        try:
            LOG.debug('Executing state retrieval logic')
            if self.stack_id is not None:
                tmp = self.deployer.details(self.stack_id, self.token)
                if tmp.get('output', None) is not None:
                    for i in tmp['output']:
                        # DSS Load Balancer address
                        if i['output_key'] == "mcn.endpoint.dssaas":
                            LOG.debug('Found key mcn.endpoint.dssaas with value: ' + i['output_value'])
                            result = -1
                            sic_info = None
                            while (result < 0):
                                time.sleep(1)
                                result, sic_info = self.getServerInfo()
                                LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(sic_info))

                            for item in sic_info:
                                if item["output_key"] == "mcn.dss.cms.lb.endpoint":
                                    i['output_value'] = item["ep"]
                            #i['output_value'] = 'http://' + self.dssDashboardRecordName + '.' + self.dssCmsDomainName + ':8080/WebAppDSS/'
                            LOG.debug('Replaced mcn.endpoint.dssaas value with: ' + i['output_value'])
                    return tmp['state'], self.stack_id, tmp['output']
                else:
                    LOG.debug('Output was None :-/')
                    return tmp['state'], self.stack_id, None

            return 'Unknown', '', None
        except:
            return 'Unknown', '', None

    # This is not part of the SOE interface
    #def update(self, updated_service):
        # TODO implement your own update logic - this could be a heat template update call
        #pass

    # Getting the deployed SIC floating IPs and host names using the output of deployed stack (Heat Output)
    def getServerInfo(self):
        try:
            if self.stack_id is not None:
                tmp = self.deployer.details(self.stack_id, self.token)
                if tmp['state'] != 'CREATE_COMPLETE' and tmp['state'] != 'UPDATE_COMPLETE':
                    return -1, 'Stack is currently being deployed ...'
                elif tmp['state'] == 'CREATE_FAILED':
                    return -2, 'Stack creation failed ...'
                elif tmp['state'] == 'UPDATE_FAILED':
                    return -3, 'Stack update failed ...'
                else:
                    # Example: {"outputKey": "mcn.dss.mcr.lb.endpoint", "ep": "160.85.4.37", "hostname": "-"}
                    # Example: {"outputKey": "mcn.dss.cms1_server_1454513381.endpoint", "ep": "160.85.4.29", "hostname": "cms1_server_1454513381"}
                    serverInfo = []
                    for i in range(0 ,len(tmp["output"])):
                        output_key = tmp["output"][i]["output_key"]
                        if output_key in self.none_host_keys:
                            if "hostname" not in output_key:
                                serverInfo.append({"output_key": output_key, "ep": tmp["output"][i]["output_value"], "hostname": "-"})
                        elif "hostname" not in output_key:
                            for j in range(0 ,len(tmp["output"])):
                                j_key = tmp["output"][j]["output_key"]
                                if "hostname" in j_key and output_key.split('.')[2] in j_key:
                                    serverInfo.append({"output_key": output_key, "ep": tmp["output"][i]["output_value"], "hostname": tmp["output"][j]["output_value"]})
                    return 0, serverInfo
            else:
                return -1, 'Stack is not deployed atm.'
        except Exception as e:
            return -1, str(e)

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
        self.ftlist = []
        self.playerCount = 0
        self.decisionMapMCR = [{"More than 90% hard disk usage on {HOST.NAME}": 0},
                               {"Less than 30% hard disk usage on {HOST.NAME}": 0}]
                               #{"Number of active players on {HOST.NAME}":0}]

        self.decisionMapCMS = [{"More than 50% cpu utilization for more than 1 minute on {HOST.NAME}": 0},
                               {"Less than 10% cpu utilization for more than 5 minutes on {HOST.NAME}": 0}]

        # Creating a configuring object ( REST client for SO::SIC interface )
        self.configure = SOConfigure(self.so_e, self, self.event)

        # Scaling guard time
        self.cmsScaleInThreshold = 600# in seconds
        self.mcrScaleDownThreshold = 600# in seconds

        # Number of players needed for each scale out/in
        self.playerCountLimit = 5.0

        # Current scaling status
        self.lastCmsScale = 0
        self.lastMcrScale = 0
        self.numberOfScaleUpsPerformed = 0
        self.numberOfCmsScaleOutsPerformed = 0
        self.numberOfMcrScaleOutsPerformed = 0

        self.timeout = 10

        self.ignored_keys = ["mcn.dss.cms.lb.endpoint", "mcn.dss.mcr.lb.endpoint", "mcn.dss.db.endpoint", "mcn.endpoint.dssaas", "mcn.dss.mq.endpoint"]

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
            # Resetting the values in decision map
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
            #self.configure.monitor.mode = "idle"
            # Take scaling decisions according to updated map and sending corresponding command to the Execution part
            scaleTriggered = False
            replaceTriggered = False
            cmsScaleOutTriggered = False
            cmsScaleInTriggered = False
            cmsReplaceTriggered = False
            mcrReplaceTriggered = False
            LOG.debug(self.swComponent + ' ' + "Checking CMS status")
            for item in self.decisionMapCMS:
                if item.keys()[0] == "More than 50% cpu utilization for more than 1 minute on {HOST.NAME}":
                    LOG.debug(self.swComponent + ' ' + "More than 50% cpu utilization for more than 1 minute on " + str(item[item.keys()[0]]) + " CMS machine(s)")
                elif item.keys()[0] == "Less than 10% cpu utilization for more than 5 minutes on {HOST.NAME}":
                    LOG.debug(self.swComponent + ' ' + "Less than 10% cpu utilization for more than 5 minutes on " + str(item[item.keys()[0]]) + " CMS machine(s)")
                LOG.debug(self.swComponent + ' ' + "Total CMS machine(s) count is: " + str(cmsCount))
                if item[item.keys()[0]] == cmsCount:
                    # CMS scale out
                    if item.keys()[0] == "More than 50% cpu utilization for more than 1 minute on {HOST.NAME}":
                        cmsScaleOutTriggered = True
                    # CMS scale in
                    elif item.keys()[0] == "Less than 10% cpu utilization for more than 5 minutes on {HOST.NAME}" and self.numberOfCmsScaleOutsPerformed > 0:
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

            # Check if you need to replace one of the SICs cos of failure
            for item in self.ftlist:
                if "cms" in item:
                    LOG.debug(self.swComponent + ' ' + "Removing and replacing faulty instance " + item)
                    self.so_e.templateManager.removeInstance(item, "cms")
                    self.so_e.templateManager.scaleOut("cms")
                    cmsReplaceTriggered = True
                    replaceTriggered = True
                    self.configure.monitor.removeWebScenarioFromWSList(item)
                elif "mcr" in item:
                    LOG.debug(self.swComponent + ' ' + "Removing and replacing faulty instance " + item)
                    self.so_e.templateManager.removeInstance(item, "mcr")
                    self.so_e.templateManager.scaleOut("mcr")
                    mcrReplaceTriggered = True
                    replaceTriggered = True
                    self.configure.monitor.removeWebScenarioFromWSList(item)
                    self.configure.monitor.removeHostFromFTItemList(item)
            LOG.debug(self.swComponent + ' ' + "Cleaned up FT list")
            self.ftlist[:] = []

            if diff > self.cmsScaleInThreshold or self.lastCmsScale == 0:
                #CMS scale out because less than specific number of players
                if  numOfCmsNeeded < cmsCount and self.numberOfCmsScaleOutsPerformed > 0 and cmsScaleInTriggered:
                    self.lastCmsScale = time.time()
                    removed_hosts = self.so_e.templateManager.scaleIn("cms")
                    for hostname in removed_hosts:
                        self.configure.monitor.removeWebScenarioFromWSList(hostname)
                    self.numberOfCmsScaleOutsPerformed -= 1
                    scaleTriggered = True
                    LOG.debug(self.swComponent + ' ' + "IN CMS scaleIn")

            # Call SO execution if scaling required
            LOG.debug(self.swComponent + ' ' + str(scaleTriggered))
            if scaleTriggered or replaceTriggered:
                self.configure.monitor.mode = "idle"
                self.so_e.templateUpdate = self.so_e.templateManager.getTemplate()

                LOG.debug(self.swComponent + ' ' + "Performing stack update")
                #Scale has started
                scale_type = None
                if cmsScaleInTriggered is True:
                    scale_type = 'scaling-in'
                elif cmsScaleOutTriggered is True:
                    scale_type = 'scaling-out'
                if replaceTriggered:
                    if scale_type is None:
                        scale_type = 'replacing'
                    else:
                        scale_type = scale_type + 'and replacing'
                upd_result = -1
                upd_code = ''
                while(upd_result < 0):
                    if "cms" in upd_code and upd_result == -2:
                        LOG.debug(self.swComponent + ' ' + "Removing and replacing faulty CMS instance " + str(upd_code))
                        self.so_e.templateManager.removeInstance(upd_code, "cms")
                        self.so_e.templateManager.scaleOut("cms")
                        self.so_e.templateUpdate = self.so_e.templateManager.getTemplate()
                    elif "mcr" in upd_code and upd_result == -2:
                        LOG.debug(self.swComponent + ' ' + "Removing and replacing faulty MCR instance " + str(upd_code))
                        self.so_e.templateManager.removeInstance(upd_code, "mcr")
                        self.so_e.templateManager.scaleOut("mcr")
                        self.so_e.templateUpdate = self.so_e.templateManager.getTemplate()
                    elif upd_result == -3:
                        return

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

                    # Checking configuration status of the instances after scaling
                    # upd_result = 0 OK; upd_result = -1 FAIL; upd_result = -2, faulty host; upd_result = -3 DB issue;
                    upd_result, upd_code = self.checkConfigurationStats(scale_type= scale_type)
                self.configure.monitor.changeMode = True
                self.configure.monitor.mode = "checktriggers"
            #self.configure.monitor.changeMode = True
            #self.configure.monitor.mode = "checktriggers"

    # Goes through all available instances and checks if the configuration info is pushed to all SICs, if not, tries to push the info
    def checkConfigurationStats(self, scale_type):
        result = -1
        config_max_retry = 120
        config_retry_counter = 0
        listOfAllServers = None
        # Waits till the deployment of the stack is finished
        while(result < 0 and config_retry_counter < config_max_retry):
            result, listOfAllServers = self.so_e.getServerInfo()
            if result < 0 and config_retry_counter >= config_max_retry:
                #Scale has failed
                LOG.debug(self.swComponent + ' ' + "Update Type: " + scale_type)
                self.so_e.update_end = datetime.datetime.now()
                diff = self.so_e.update_end - self.so_e.update_start
                infoDict = {
                            'so_id': 'idnotusefulhere',
                            'sm_name': 'dssaas',
                            'so_phase': 'update',
                            'scaling': scale_type,
                            'phase_event': 'failed',
                            'response_time': diff.total_seconds(),
                            'tenant': self.so_e.tenant_name
                            }
                tmpJSON = json.dumps(infoDict)
                GLOG.debug(tmpJSON)
                LOG.debug(self.swComponent + ' ' + "Update failed")
                LOG.debug(self.swComponent + ' ' + "Re-executing update")
                return -1, 'FAIL'
            config_retry_counter += 1
            time.sleep(1)

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

        newcomers = []
        for item in listOfAllServers:
            if self.so_e.templateManager.is_new_instance(item["hostname"]) or item["output_key"] in self.ignored_keys:
                newcomers.append(item)
        self.so_e.templateManager.clean_new_instance_list()

        first_newcomer_in_list = ''
        try:
            for item in newcomers:
                if item["output_key"] not in self.ignored_keys:
                    first_newcomer_in_list = item["hostname"]
                    break
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + "No new comers found, are you sure everything is OK? Just sayin'")

        # Talking to DSS SIC agents to get the configuration status of each# Pushing local configurations to DSS SICs
        localConfig_status = 0
        while localConfig_status != 1:
            localConfig_status, localConfig_msg = self.configure.performLocalConfig(newcomers)
            LOG.debug(self.swComponent + ' ' + "Config status is: " + str(localConfig_status))
            LOG.debug(self.swComponent + ' ' + "Config message is: " + str(localConfig_msg))
            if localConfig_msg != 'all_ok':
                if localConfig_msg == self.configure.agent_timedout:
                    LOG.debug(self.swComponent + ' ' + "SIC Agent unreachable - Deployment Failed")
                    return -2, first_newcomer_in_list # We send back the first new comer we find in the list as the faulty one
                elif localConfig_msg == self.configure.db_failed_msg:
                    LOG.debug(self.swComponent + ' ' + "DB unreachable - Deployment Failed")
                    return -3, 'DB'

        for item in newcomers:
            if item["output_key"] not in self.ignored_keys:
                self.configure.SICMonConfig(item["hostname"], item["ep"])
        return 0, 'OK'

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
        self.so_mqs = None

        self.dns_forwarder = None
        self.dns_api = None
        self.dssCmsDomainName = self.so_e.dssCmsDomainName
        self.dssMcrDomainName = self.so_e.dssMcrDomainName
        self.dssCmsRecordName = self.so_e.dssCmsRecordName
        self.dssMcrRecordName = self.so_e.dssMcrRecordName

        self.monitoring_endpoint = None
        self.monitor = None
        self.instances = None
        self.db_endpoint = None
        self.mq_service_endpoint = None

        self.timeout = 10
        self.max_retry_count = 30

        self.send_count = 0
        self.rec_count = 0
        self.consume_timedout = False

        self.dependencyStat = {"DNS":"not ready","MON":"not ready"}
        self.ignored_keys = ["mcn.dss.cms.lb.endpoint", "mcn.dss.mcr.lb.endpoint", "mcn.dss.db.endpoint", "mcn.endpoint.dssaas", "mcn.dss.mq.endpoint"]

        self.db_failed_msg = "DATABSE FAILURE"
        self.dss_instance_mq_failed = "DSS INSTANCE FAILED TO CONFIGURE MQ SERVICE"
        self.dss_instance_failed_msg = "DSS INSTANCE FAILED"
        self.dss_mq_service_failed_msg = "DSS MESSAGE QUEUE SERVICE FAILED"
        self.agent_timedout = "DSS INSTANCE AGENT FAILED TO RESPOND ON TIME"

    def run(self):
        # Pushing DNS configurations to DNS SICs
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
        #TODO: What would you do if you never get the eps? Needs some checks here too

        # Get the DB endpoint from stack output
        # In this function we also make sure our stack creation is done
        self.db_endpoint = self.getDbEndpoint()
        # Get the MQ Service endpoint from stack output
        # In this function we also make sure our stack creation is done
        self.mq_service_endpoint = self.getMQServiceEndpoint()
        #TODO: What would you do if at this point stack creation fails? Needs some checks here too
        LOG.debug(self.swComponent + ' ' + "MQ EP is: " + str(self.mq_service_endpoint))
        self.so_mqs = MessagingService(self, epMQ = self.mq_service_endpoint, portMQ = self.so_e.templateManager.mq_service_port,
                                       userMQ = self.so_e.templateManager.mq_service_user, passMQ = self.so_e.templateManager.mq_service_pass)
        mq_reachable = False
        try_to_reach_mq = 0
        max_retry = self.max_retry_count * self.timeout# 30 * 10 * 1 = 5 minutes
        while mq_reachable is not True:
            time.sleep(1)
            try_to_reach_mq += 1
            try:
                mq_reachable = self.so_mqs.connect_to_mq()
            except Exception as e:
                LOG.debug(self.swComponent + ' ' + str(e))
                mq_reachable = False
            if try_to_reach_mq > max_retry:
                LOG.debug(self.swComponent + ' ' + self.dss_mq_service_failed_msg)
                # Finishes the thread
                # Decision is already on waiting mode
                # Monitoring has not even started yet
                LOG.debug(self.swComponent + ' ' + "Adios nube!")
                return

        #result = -1
        #while (result < 0):
        #    result, self.instances = self.so_e.getServerInfo()
        #    LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))
        #    time.sleep(0.5)
        #TODO: What would you do if at this point we get stuck? if you made it up to here 90% u're good

        # Pushing local configurations to DSS SICs
        localConfig_status = 0
        while localConfig_status != 1:
            localConfig_status, localConfig_msg = self.performLocalConfig(self.instances)
            LOG.debug(self.swComponent + ' ' + "Config status is: " + str(localConfig_status))
            LOG.debug(self.swComponent + ' ' + "Config message is: " + str(localConfig_msg))
            if localConfig_msg != 'all_ok':
                if localConfig_msg == self.agent_timedout:
                    LOG.debug(self.swComponent + ' ' + "Connection between SO and SIC agents malfunctioning - Deployment Failed")
                    # Everything failed, STOP
                elif localConfig_msg == self.db_failed_msg:
                    LOG.debug(self.swComponent + ' ' + "DB unreachable - Deployment Failed")
                    # TODO: Recreate Stack and replace DB
                    # TODO: Call an update with new DB resource
                # Finishes the thread
                # Decision is already on waiting mode
                # Monitoring has not even started yet
                LOG.debug(self.swComponent + ' ' + "Adios nube!")
                return

        self.so_e.templateManager.clean_new_instance_list()

        # Creating a monitor for pulling MaaS information
        # We need it here because we need all teh custome items and everything configured before doing it
        LOG.debug(self.swComponent + ' ' + "About to get MaaS object")
        self.monitor = SOMonitor(self.so_e, self.so_d, self.monitoring_endpoint, 0, 'http://' + self.monitoring_endpoint +'/zabbix/api_jsonrpc.php')
        LOG.debug(self.swComponent + ' ' + "Succesfully got MaaS object")
        self.performMonConfig()

        #LOG.debug(self.swComponent + ' ' + "Start monitoring service ...")
        self.monitor.start()
        # once logic executes, deploy phase is done
        self.event.set()

    def notify_msg_receive(self, data):
        #TODO: process the data and act accordingly
        LOG.debug(self.swComponent + ' ' + "Response received " + str(data))
        if "'result':'OK'" in data:
            self.rec_count += 1
            if self.rec_count >= self.send_count:
                LOG.debug(self.swComponent + ' ' + "Send count: " + str(self.send_count))
                LOG.debug(self.swComponent + ' ' + "Rec count: " + str(self.rec_count))
                LOG.debug(self.swComponent + ' ' + "Received all config responses, ready to proceed")
                self.consume_timedout = False
                self.so_mqs.channel.stop_consuming()
            else:
                LOG.debug(self.swComponent + ' ' + "Send count: " + str(self.send_count))
                LOG.debug(self.swComponent + ' ' + "Rec count: " + str(self.rec_count))

    def getDbEndpoint(self):
        result = -1
        while (result < 0):
            result, self.instances = self.so_e.getServerInfo()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))
            time.sleep(0.5)

        #WAIT FOR FINISHING THE DEPLOYMENT
        for item in self.instances:
            if item["output_key"] == "mcn.dss.db.endpoint":
                return item["ep"]

    def getMQServiceEndpoint(self):
        result = -1
        while (result < 0):
            result, self.instances = self.so_e.getServerInfo()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))
            time.sleep(0.5)

        #WAIT FOR FINISHING THE DEPLOYMENT
        for item in self.instances:
            if item["output_key"] == "mcn.dss.mq.endpoint":
                return item["ep"]

    def performDNSConfig(self):
        result = -1
        while (result < 0):
            result, self.instances = self.so_e.getServerInfo()
            LOG.debug(self.swComponent + ' ' + "In while: " + str(result) + " , " + str(self.instances))
            time.sleep(0.5)

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
            if item["output_key"] == "mcn.dss.cms.lb.endpoint":
                lbRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssCmsDomainName, record_name=self.dssCmsRecordName, record_type='A', token=self.so_e.token)
                if lbRecordExists.get('code', None) is not None and lbRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(1)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssCmsDomainName,record_name=self.dssCmsRecordName, record_type='A', record_data=item["ep"], token=self.so_e.token)
                        LOG.debug(self.swComponent + ' ' + result.__repr__())
                        LOG.debug(self.swComponent + ' ' + 'DNS record creation attempt for: ' + str(item["ep"]))
                    LOG.debug(self.swComponent + ' ' + 'DNS record created for: ' + str(item["ep"]))
                else:
                    LOG.debug(self.swComponent + ' ' + 'DNS record already exists for:' + str(item["ep"]) + ' Or invaid output: ' + lbRecordExists.__repr__())
            elif item["output_key"] == "mcn.dss.mcr.lb.endpoint":
                mcrRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', token=self.so_e.token)
                if mcrRecordExists.get('code', None) is not None and mcrRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(1)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', record_data=item["ep"], token=self.so_e.token)
                        LOG.debug(self.swComponent + ' ' + result.__repr__())
                        LOG.debug(self.swComponent + ' ' + 'DNS record creation attempt for:' + str(item["ep"]))
                    LOG.debug(self.swComponent + ' ' + 'DNS record created for: ' + str(item["ep"]))
                else:
                    LOG.debug(self.swComponent + ' ' + 'DNS record already exists for:' + str(item["ep"]) + ' Or invaid output: ' + lbRecordExists.__repr__())

        LOG.debug(self.swComponent + ' ' + "Exiting the loop to push dns domain names for all instances")

    def performLocalConfig(self, list_of_instances):
        LOG.debug(self.swComponent + ' ' + "Entering the loop to provision each instance ...")
        while True:
            try:
                #Publish DB config messages to broker
                self.send_count = 0
                for item in list_of_instances:
                    time.sleep(0.1)
                    if item["output_key"] not in self.ignored_keys:
                        queue_exists = 0
                        timeout_counter = 0
                        max_retry = 300
                        while queue_exists != 1:
                            try:
                                queue_exists = self.so_mqs.queue_exists(item["hostname"].replace("_","-"))
                            except Exception as e:
                                LOG.debug(self.swComponent + ' ' + str(e))
                                queue_exists = 0
                                try:
                                    self.so_mqs.close_connection()
                                    LOG.debug(self.swComponent + ' ' + "Connection closed manually")
                                except:
                                    LOG.debug(self.swComponent + ' ' + "No Connection to close")
                                self.so_mqs.reconnect()
                            LOG.debug(self.swComponent + ' ' + "Queue status of host " + item["hostname"].replace("_", "-") + " " + str(queue_exists))
                            time.sleep(1)
                            timeout_counter += 1
                            if timeout_counter > max_retry:
                                LOG.debug(self.swComponent + ' ' + self.agent_timedout)
                                return 0, self.agent_timedout
                        LOG.debug(self.swComponent + ' ' + "Declaring queue for host " + item["hostname"].replace("_","-"))
                        self.so_mqs.declare_queue(item["hostname"].replace("_","-"))
                        self.so_mqs.bind_queue(item["hostname"].replace("_","-"), self.so_mqs.exchange_name, item["hostname"].replace("_","-"))
                        dbconfig_status, status_msg = self.configureInstanceDB(item["ep"], item["hostname"].replace("_","-"))
                        if dbconfig_status == 0:
                            return dbconfig_status, status_msg
                        self.send_count += 1
                if self.send_count > 0:
                    self.consume_timedout = True
                    LOG.debug(self.swComponent + ' ' + "Consumption started ...")
                    self.so_mqs.connection.add_timeout(self.so_mqs.wait_time, self.so_mqs.stop_listening)
                    self.so_mqs.basic_consume(self.so_mqs.so_queue_name)
                    LOG.debug(self.swComponent + ' ' + "Consumption stopped ...")
                    if self.consume_timedout:
                        LOG.debug(self.swComponent + ' ' + self.agent_timedout)
                        return 0, self.agent_timedout

                self.rec_count = 0

                #Publish SIC provision messages to broker
                self.send_count = 0
                for item in list_of_instances:
                    time.sleep(0.1)
                    if item["output_key"] not in self.ignored_keys:
                        provision_status, status_msg = self.provisionInstance(item["ep"], item["hostname"].replace("_","-"), list_of_instances)
                        if provision_status == 0:
                            return provision_status, status_msg
                        self.send_count += 1

                if self.send_count > 0:
                    self.consume_timedout = True
                    LOG.debug(self.swComponent + ' ' + "Consumption started ...")
                    self.so_mqs.connection.add_timeout(self.so_mqs.wait_time, self.so_mqs.stop_listening)
                    self.so_mqs.basic_consume(self.so_mqs.so_queue_name)
                    LOG.debug(self.swComponent + ' ' + "Consumption stopped ...")
                    if self.consume_timedout:
                        LOG.debug(self.swComponent + ' ' + self.agent_timedout)
                        return 0, self.agent_timedout

                self.rec_count = 0

                LOG.debug(self.swComponent + ' ' + "Entering the loop to create JSON config file for each instance ...")
                #Publish JSON config messages to broker
                self.send_count = 0
                for item in list_of_instances:
                    time.sleep(0.1)
                    if item["output_key"] not in self.ignored_keys:
                        json_publish_status, status_msg = self.configInstance(item["ep"], item["hostname"].replace("_","-"))
                        if json_publish_status == 0:
                            return json_publish_status, status_msg
                        self.send_count += 3

                if self.send_count > 0:
                    self.consume_timedout = True
                    LOG.debug(self.swComponent + ' ' + "Consumption started ...")
                    self.so_mqs.connection.add_timeout(self.so_mqs.wait_time, self.so_mqs.stop_listening)
                    self.so_mqs.basic_consume(self.so_mqs.so_queue_name)
                    LOG.debug(self.swComponent + ' ' + "Consumption stopped ...")
                    if self.consume_timedout:
                        LOG.debug(self.swComponent + ' ' + self.agent_timedout)
                        return 0, self.agent_timedout

                self.send_count = 0
                self.rec_count = 0
                LOG.debug(self.swComponent + ' ' + "Exiting the loop for JSON config file creation for all instances")
                return 1, 'all_ok'
            except Exception as e:
                self.so_mqs.reconnect


    # Configures all the things SIC needs to attach to DBaaS
    def configureInstanceDB(self, target_ip, target_hostname):
        # We don't declare the queue here, SICs later should do it and bind to SO exchange
        # Here we just publish required message to already defined exchange
        # Publish message for DB config
        resp = self.so_mqs.basic_publish('{"action":"DB","dbuser":"' + self.so_e.templateManager.dbuser + '","dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '","dbhost":"' + self.db_endpoint + '"}', target_hostname)
        LOG.debug(self.swComponent + ' ' + 'DB Message publish for ' + target_hostname + ' returned ' + str(resp))
        if resp == 1:
            return 1, 'all_ok'
        else:
            return 0, self.db_failed_msg

    # Executes the two shell scripts in the SIC which takes care of war deployment
    def provisionInstance(self, target_ip, target_hostname, all_sic_info):
        # We don't declare the queue here, SICs later should do it and bind to SO exchange
        # Here we just publish required message to already defined exchange
        # Publish message for provision config
        mcr_srv_ip = None
        cms_srv_ip = None
        dbaas_srv_ip = None
        for inf in all_sic_info:
            if inf["output_key"] == "mcn.dss.cms.lb.endpoint":
                cms_srv_ip = inf["ep"]
            elif inf["output_key"] == "mcn.dss.mcr.lb.endpoint":
                mcr_srv_ip = inf["ep"]
            elif inf["output_key"] == "mcn.dss.db.endpoint":
                dbaas_srv_ip = inf["ep"]
        # CMS ip address is sent to MCR for cross domain issues but as the player is trying to get contents from CMS DOMAIN NAME it will not work as it's an ip address
        resp = self.so_mqs.basic_publish('{"action":"provision","mcr_srv_ip":"' + mcr_srv_ip + '","cms_srv_ip":"' + cms_srv_ip + '","dbaas_srv_ip":"' + dbaas_srv_ip + '", "dbuser":"' + self.so_e.templateManager.dbuser +'", "dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}', target_hostname)
        LOG.debug(self.swComponent + ' ' + 'Provision Message publish for ' + target_hostname + ' returned ' + str(resp))
        if resp == 1:
            return 1, 'all_ok'
        else:
            return 0, self.dss_instance_failed_msg

    # Calls to the SIC agent to complete the provisioning
    def configInstance(self, target_ip, target_hostname):
        # Publish DNS EP
        resp = self.so_mqs.basic_publish('{"action":"DNS","dnsendpoint":"'+ self.dns_forwarder + '","dssdomainname":"' + self.dssCmsRecordName + '.' + self.dssCmsDomainName + '"}', target_hostname)
        LOG.debug(self.swComponent + ' ' + 'DNS EP publish for ' + target_hostname + ' returned ' + str(resp))
        if resp == 0:
            return 0, 'nok'
        # Publish MON EP & Conf
        # MON endpoint is not really being used at the moment
        # DB info is being sent to be used by the getcdr script in zabbix custom item definitions
        resp = self.so_mqs.basic_publish('{"action":"MON","monendpoint":"' + self.monitoring_endpoint + '","dbuser":"' + self.so_e.templateManager.dbuser + '","dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}', target_hostname)
        LOG.debug(self.swComponent + ' ' + 'MON EP publish for ' + target_hostname + ' returned ' + str(resp))
        if resp == 0:
            return 0, 'nok'
        # Publish RCB Conf
        # DB info is used to create an event for generating cdr data in DB
        resp = self.so_mqs.basic_publish('{"action":"RCB","dbuser":"' + self.so_e.templateManager.dbuser + '","dbpassword":"' + self.so_e.templateManager.dbpass + '","dbname":"' + self.so_e.templateManager.dbname + '"}', target_hostname)
        LOG.debug(self.swComponent + ' ' + 'RCB Conf publish for ' + target_hostname + ' returned ' + str(resp))
        if resp == 0:
            return 0, 'nok'
        return 1, 'all_ok'

    def performMonConfig(self):
        result = -1
        while (result < 0):
            time.sleep(0.5)
            result, serverList = self.so_e.getServerInfo()

        for item in serverList:
            if item["hostname"] != "-":
                self.SICMonConfig(item["hostname"], item["ep"])
        # Finished adding triggers so we change to monitoring mode
        self.monitor.changeMode = True
        self.monitor.mode = "checktriggers"

    def SICMonConfig(self, targetHostName, targetEp):
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
                res = self.monitor.itemExists(zabbixName, "DSS.Tracker.STATUS")
                if res != 1:
                    # 4 - Specifies data type "String" and 30 Specifies this item will be checked every 30 seconds
                    res = self.monitor.configItem("DSS tracker service status", zabbixName, "DSS.Tracker.STATUS", 4, 30, ft_enabler=True)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.itemExists(zabbixName, "DSS.Streaming.STATUS")
                if res != 1:
                    # 4 - Specifies data type "String" and 30 Specifies this item will be checked every 30 seconds
                    res = self.monitor.configItem("DSS streaming service status", zabbixName, "DSS.Streaming.STATUS", 4, 30, ft_enabler=True)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.itemExists(zabbixName, "DSS.Filesync.STATUS")
                if res != 1:
                    # 4 - Specifies data type "String" and 30 Specifies this item will be checked every 30 seconds
                    res = self.monitor.configItem("DSS filesync service status", zabbixName, "DSS.Filesync.STATUS", 4, 30, ft_enabler=True)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('More than 90% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}<10')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('Less than 30% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}>70')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.addWebScenarioToMaas(zabbixName, "DSSMCRAPI_APP", "HomePage", "http://" + targetEp + "/DSSMCRAPI/", 200, 1)
        else:
            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('More than 50% cpu utilization for more than 1 minute on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].min(1m)}<50')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('Less than 10% cpu utilization for more than 5 minutes on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].avg(5m)}>90')
            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.addWebScenarioToMaas(zabbixName, "WEBAPPDSS_APP", "HomePage", "http://" + targetEp + "/WebAppDSS/", 200, 1)

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
