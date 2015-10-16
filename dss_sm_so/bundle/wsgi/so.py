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

import logging
import sys
import threading

from sm.so import service_orchestrator
from sm.so.service_orchestrator import LOG
from TemplateGenerator import *
from SOMonitor import *
from dnsaascli import *

from sdk.mcn import util
from sm.so.service_orchestrator import BUNDLE_DIR

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()

# To be replaced with python logging
def writeLogFile(swComponent ,msgTo, statusReceived, jsonReceived):
    LOG.debug(swComponent + ' ' +  msgTo)
    '''
    with os.fdopen(os.open(os.path.join(BUNDLE_DIR, 'LOG_ERROR_FILE.csv'), os.O_WRONLY | os.O_CREAT, 0600), 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),' ['+swComponent+'] ',msgTo, statusReceived, jsonReceived ])
        csvfile.close()
    '''

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
        #self.dnsObject = None
        self.dssCmsDomainName = "dssaas.mcndemo.org"
        self.dssMcrDomainName = "dssaas.mcndemo.org"
        self.dssCmsRecordName = "cms"
        self.dssDashboardRecordName = "dashboard"
        self.dssMcrRecordName = "mcr"
        self.monitoring_endpoint = None
        self.icn_endpoint = None
        self.dns_forwarder = None
        self.dns_api = None
        self.dnsManager = None
        # CDN Related Variables
        #self.cdn_password = 'password'
        #self.cdn_password = None
        #self.cdn_endpoint = '160.85.4.104:8182'
        #self.cdn_endpoint = None
        #self.cdn_global_id = 'd3e30c11-8a4d-41b4-b0c0-17de168de2a9'
        #self.cdn_global_id = None
        #self.cdn_origin = '160.85.4.103:8181'
        #self.cdn_origin = None
        #------------------------

        # make sure we can talk to deployer...
        writeLogFile(self.swComponent,'Make sure we can talk to deployer...', '', '')
        LOG.debug("About to get the deployer with token :" + str(self.token + " Tenant name : " + self.tenant_name))
        self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name, region=self.region_name)
        LOG.debug("Got the deployer")

    def design(self):
        """
        Do initial design steps here.
        """
        LOG.debug('Executing design logic')
        self.resolver.design()

    def deploy(self,entity):
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
        LOG.debug('DSS SO provision - Getting EPs')
        for ep_entity in self.resolver.service_inst_endpoints:
            for item in ep_entity:
                if 'mcn.endpoint.icnaas' in item['attributes']:
                    # The endpoint includes http:// part
                    self.icn_endpoint = item['attributes']['mcn.endpoint.icnaas']
                    writeLogFile(self.swComponent,'ICN EP is: ' + item['attributes']['mcn.endpoint.icnaas'], '', '')
                if 'mcn.endpoint.maas' in item['attributes']:
                    self.monitoring_endpoint = item['attributes']['mcn.endpoint.maas']
                    writeLogFile(self.swComponent,'MON EP is: ' + item['attributes']['mcn.endpoint.maas'], '', '')
                if 'mcn.endpoint.forwarder' in item['attributes']:
                    self.dns_forwarder = item['attributes']['mcn.endpoint.forwarder']
                    writeLogFile(self.swComponent,'DNS forwarder EP is: ' + self.dns_forwarder, '', '')
                if 'mcn.endpoint.api' in item['attributes']:
                    self.dns_api = item['attributes']['mcn.endpoint.api']
                    self.dnsManager = DnsaasClientAction(self.dns_api, token=self.token)
                    LOG.debug(str(self.dnsManager))
                    writeLogFile(self.swComponent,'DNS EP is: ' + self.dns_api, '', '')

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
        if self.templateManager.dns_enable == 'true':
                writeLogFile(self.swComponent,'Trying to remove load balancer record: ' + self.dssCmsRecordName, '', '')
                result = -1
                while (result != 1):
                    time.sleep(1)
                    result = self.dnsManager.delete_record(self.dssCmsDomainName, self.dssCmsRecordName, 'A', self.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    try:
                        if result.get('status', None) is not None:
                            if(result['status'] == '404'):
                                break
                        elif result.get('code', None) is not None:
                            if(result['code'] == 500):
                                break
                    except:
                        break
                writeLogFile(self.swComponent,self.dssCmsRecordName + 'has been successfully removed', '', '')
                writeLogFile(self.swComponent,'Trying to remove dashboard record: ' + self.dssDashboardRecordName, '', '')
                result = -1
                while (result != 1):
                    time.sleep(1)
                    result = self.dnsManager.delete_record(self.dssCmsDomainName, self.dssDashboardRecordName, 'A', self.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    try:
                        if result.get('status', None) is not None:
                            if(result['status'] == '404'):
                                break
                        elif result.get('code', None) is not None:
                            if(result['code'] == 500):
                                break
                    except:
                        break
                writeLogFile(self.swComponent,self.dssDashboardRecordName + 'has been successfully removed', '', '')
                writeLogFile(self.swComponent,'Trying to remove MCR record: ' + self.dssMcrRecordName, '', '')
                result = -1
                while (result != 1):
                    time.sleep(1)
                    result = self.dnsManager.delete_record(self.dssMcrDomainName, self.dssMcrRecordName, 'A', self.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    try:
                        if result.get('status', None) is not None:
                            if(result['status'] == '404'):
                                break
                        elif result.get('code', None) is not None:
                            if(result['code'] == 500):
                                break
                    except:
                        break
                writeLogFile(self.swComponent,self.dssMcrRecordName + 'has been successfully removed', '', '')

                writeLogFile(self.swComponent,'Trying to remove load balancer domain: ' + self.dssCmsDomainName, '', '')
                result = -1
                while (result != 1):
                    time.sleep(1)
                    result = self.dnsManager.delete_domain(self.dssCmsDomainName, self.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    try:
                        if result.get('status', None) is not None:
                            if(result['status'] == '404'):
                                break
                        elif result.get('code', None) is not None:
                            if(result['code'] == 500):
                                break
                    except:
                        break
                writeLogFile(self.swComponent,self.dssCmsDomainName + 'has been successfully removed', '', '')
                writeLogFile(self.swComponent,'Trying to remove MCR domain: ' + self.dssMcrDomainName, '', '')
                result = -1
                while (result != 1):
                    time.sleep(1)
                    result = self.dnsManager.delete_domain(self.dssMcrDomainName, self.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    try:
                        if result.get('status', None) is not None:
                            if(result['status'] == '404'):
                                break
                        elif result.get('code', None) is not None:
                            if(result['code'] == 500):
                                break
                    except:
                        break
                writeLogFile(self.swComponent,self.dssMcrDomainName + 'has been successfully removed', '', '')
        # TODO on disposal, remove the registered hosts on MaaS service
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
            writeLogFile(self.swComponent,'Got DSS SO attributes in update', '', '')
            #print attributes
            if 'mcn.endpoint.maas' in updated.attributes:
                self.monitoring_endpoint = updated.attributes['mcn.endpoint.maas']
                writeLogFile(self.swComponent,'MaaS EP is: ' + self.monitoring_endpoint, '', '')
            if 'mcn.endpoint.icnaas' in updated.attributes:
                self.icn_endpoint = updated.attributes['mcn.endpoint.icnaas']
                writeLogFile(self.swComponent,'ICN EP is: ' + self.icn_endpoint, '', '')
            if 'mcn.endpoint.forwarder' in updated.attributes:
                self.dns_forwarder = updated.attributes['mcn.endpoint.forwarder']
                writeLogFile(self.swComponent,'DNS forwarder EP is: ' + self.dns_forwarder, '', '')
            if 'mcn.endpoint.api' in updated.attributes:
                self.dns_api = updated.attributes['mcn.endpoint.api']
                self.dnsManager = DnsaasClientAction(self.dns_api, token=self.token)
                LOG.debug(str(self.dnsManager))
                writeLogFile(self.swComponent,'DNS EP is: ' + self.dns_api, '', '')
            #if 'mcn.endpoints.cdn.mgt' in updated.attributes:
                #self.cdn_endpoint = updated.attributes['mcn.endpoints.cdn.mgt']
                #writeLogFile(self.swComponent,'CDN EP is: ' + self.cdn_endpoint, '', '')
            #if 'mcn.endpoints.cdn.origin' in updated.attributes:
                #self.cdn_origin = updated.attributes['mcn.endpoints.cdn.origin']
                #writeLogFile(self.swComponent,'CDN Origin EP is: ' + self.cdn_origin, '', '')
            #if 'mcn.cdn.password' in updated.attributes:
                #self.cdn_password = updated.attributes['mcn.cdn.password']
                #writeLogFile(self.swComponent,'CDN Pass is: ' + self.cdn_password, '', '')
            #if 'mcn.cdn.id' in updated.attributes:
                #self.cdn_global_id = updated.attributes['mcn.cdn.id']
                #writeLogFile(self.swComponent,'CDN Golobal id is: ' + self.cdn_global_id, '', '')

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
                            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(instances) ,'','')

                        for item in instances:
                            if item == "mcn.dss.lb.endpoint":
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
        self.decisionMapMCR = [{"More than 90% hard disk usage on {HOST.NAME}":0},
                               {"Less than 30% hard disk usage on {HOST.NAME}":0}]
                               #{"Number of active players on {HOST.NAME}":0}]

        self.decisionMapCMS = [{"More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":0},
                               {"Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}":0}]

        # Creating a configuring object ( REST client for SO::SIC interface )
        self.configure = SOConfigure(self.so_e,self,self.event)

        # Scaling guard time
        self.cmsScaleInThreshold = 450 #in seconds
        self.mcrScaleDownThreshold = 450 #in seconds

        # Number of players needed for each scale out/in
        self.playerCountLimit = 5.0

        # Current scaling status
        self.lastCmsScale = 0
        self.lastMcrScale = 0
        self.numberOfScaleUpsPerformed = 0
        self.numberOfScaleOutsPerformed = 0

        self.timeout = 10

    def run(self):
        """
        Decision part implementation goes here.
        """
        # it is unlikely that logic executed will be of any use until the provisioning phase has completed
        resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"so"}]}')
        writeLogFile(self.swComponent,"Request response is:" + str(resp),'','')
        LOG.debug('Waiting for deploy and provisioning to finish')
        self.event.wait()
        resp = ''
        if self.so_e.templateManager.aaa_enable == "true":
            resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"cms1"},{"name":"mcr"},{"name":"db"},{"name":"slaaas"},{"name":"aaaaas"},{"name":"lbaas"}]}')
        else:
            resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"cms1"},{"name":"mcr"},{"name":"db"},{"name":"slaaas"},{"name":"lbaas"}]}')
        writeLogFile(self.swComponent,"Request response is:" + str(resp),'','')
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
            writeLogFile(self.swComponent,"Start of decision loop ...",'','')
            time.sleep(3)
            cmsCount = self.so_e.getNumberOfCmsInstances()
            #Reseting the values in decision map
            for item in self.decisionMapCMS:
                item[item.keys()[0]] = 0
            for item in self.decisionMapMCR:
                item[item.keys()[0]] = 0
            writeLogFile(self.swComponent,"DecisionMap reset successful",'','')

            # Update decision map
            for item in self.hostsWithIssues:
                for row in self.decisionArray:
                    if item == row:
                        if "cms" in self.decisionArray[row][0]:
                            self.updateDecisionMap("cms", self.decisionArray[row][1])
                        else:
                            self.updateDecisionMap("mcr", self.decisionArray[row][1])
            writeLogFile(self.swComponent,str(self.decisionMapCMS),'','')
            writeLogFile(self.swComponent,str(self.decisionMapMCR),'','')
            writeLogFile(self.swComponent,"DecisionMap update successful",'','')

            # Take scaling decisions according to updated map and sending corresponding command to the Execution part
            scaleTriggered = False
            cmsScaleOutTriggered = False
            cmsScaleInTriggered = False
            writeLogFile(self.swComponent,"Checking CMS status",'','')
            for item in self.decisionMapCMS:
                if item.keys()[0] == "More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":
                    writeLogFile(self.swComponent,"More than 60% cpu utilization for more than 1 minute on " + str(item[item.keys()[0]]) + " CMS machine(s)",'','')
                elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}":
                    writeLogFile(self.swComponent,"Less than 10% cpu utilization for more than 10 minutes on " + str(item[item.keys()[0]]) + " CMS machine(s)",'','')
                writeLogFile(self.swComponent,"Total CMS machine(s) count is: " + str(cmsCount),'','')
                if item[item.keys()[0]] == cmsCount:
                    # CMS scale out
                    if item.keys()[0] == "More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":
                        cmsScaleOutTriggered = True
                    # CMS scale in
                    elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}" and self.numberOfScaleOutsPerformed > 0:
                        cmsScaleInTriggered = True

            #Calculate the player scaling situation
            numOfCmsNeeded = int((float(self.playerCount)/self.playerCountLimit) + 1)
            writeLogFile(self.swComponent,"Number of CMS needed is: " + str(numOfCmsNeeded) + " and we have: " + str(cmsCount),'','')
            #CMS scale out because more than specific number of players
            if numOfCmsNeeded > cmsCount or cmsScaleOutTriggered:
                self.lastCmsScale = time.time()
                self.so_e.templateManager.templateToScaleOut()
                self.numberOfScaleOutsPerformed += 1
                scaleTriggered = True
                writeLogFile(self.swComponent,"IN CMS scaleOut",'','')

            if self.lastCmsScale == 0:
                diff = 0
            else:
                diff = int(time.time() - self.lastCmsScale)
            writeLogFile(self.swComponent,"Number of scale outs performed: " + str(self.numberOfScaleOutsPerformed),'','')
            writeLogFile(self.swComponent,"Last CMS scale action happened " + str(diff) + " minute(s) ago",'','')
            writeLogFile(self.swComponent,"Threshold for CMS scale in is: " + str(self.cmsScaleInThreshold) + " second(s)",'','')
            writeLogFile(self.swComponent,"CMS cpu metric scale in triggered: " + str(cmsScaleInTriggered),'','')
            if diff > self.cmsScaleInThreshold or self.lastCmsScale == 0:
                #CMS scale out because less than specific number of players
                if  numOfCmsNeeded < cmsCount and self.numberOfScaleOutsPerformed > 0 and cmsScaleInTriggered:
                    self.lastCmsScale = time.time()
                    self.so_e.templateManager.templateToScaleIn()
                    self.numberOfScaleOutsPerformed -= 1
                    scaleTriggered = True
                    writeLogFile(self.swComponent,"IN CMS scaleIn",'','')
                    # Get a backup of the server name list
                    result = -1
                    while (result < 0):
                        time.sleep(1)
                        result, instanceListInCaseOfScaleIn = self.so_e.getServerNamesList()

            for item in self.decisionMapMCR:
                writeLogFile(self.swComponent,"Checking MCR status",'','')
                if self.lastMcrScale == 0:
                    diff = 0
                else:
                    diff = int(time.time() - self.lastMcrScale)
                if item[item.keys()[0]] > 0:
                    # MCR scale up
                    # It is commented because it's not working for current heat version )
                    if item.keys()[0] == "More than 90% hard disk usage on {HOST.NAME}":
                        writeLogFile(self.swComponent,"More than 90% hard disk usage on MCR machine",'','')
                        self.lastMcrScale = time.time()
                        #self.so_e.templateManager.templateToScaleUp()
                        self.numberOfScaleUpsPerformed += 1
                        #scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleUp",'','')
                    # MCR scale down
                    elif  item.keys()[0] == "Less than 30% hard disk usage on {HOST.NAME}" and self.numberOfScaleUpsPerformed > 0 and diff > self.mcrScaleDownThreshold:
                        writeLogFile(self.swComponent,"Less than 30% hard disk usage on MCR machine",'','')
                        writeLogFile(self.swComponent,"Number of scale ups performed: " + str(self.numberOfScaleUpsPerformed),'','')
                        writeLogFile(self.swComponent,"Last MCR scale action happened " + str(diff) + " minute(s) ago",'','')
                        writeLogFile(self.swComponent,"Threshold for MCR scale down is: " + str(self.mcrScaleDownThreshold) + " second(s)",'','')
                        self.lastMcrScale = time.time()
                        #self.so_e.templateManager.templateToScaleDown()
                        self.numberOfScaleUpsPerformed -= 1
                        #scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleDown",'','')

            # Call SO execution if scaling required
            writeLogFile(self.swComponent,str(scaleTriggered),'','')
            if scaleTriggered == True:
                self.configure.monitor.mode = "idle"
                self.so_e.templateUpdate = self.so_e.templateManager.getTemplate()

                # find the deleted host from the server list backup
                zHostToDelete = None
                if instanceListInCaseOfScaleIn is not None:
                    for item in instanceListInCaseOfScaleIn:
                        if self.so_e.templateManager.cmsHostToRemove in item:
                            zHostToDelete = item

                writeLogFile(self.swComponent,"Performing stack update",'','')
                self.so_e.update_stack()
                writeLogFile(self.swComponent,"Update in progress ...",'','')

                #Removing the deleted host from zabbix server
                if zHostToDelete is not None:
                    self.configure.monitor.removeHost(zHostToDelete.replace("_","-"))
                    resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'DELETE', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"cms' + str(self.so_e.templateManager.numberOfCmsInstances+1) + '"}]}')
                    writeLogFile(self.swComponent,"Request response is:" + str(resp),'','')
                else:
                    resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"cms' + str(self.so_e.templateManager.numberOfCmsInstances) + '"}]}')
                    writeLogFile(self.swComponent,"Request response is:" + str(resp),'','')

                # Checking configuration status of the instances after scaling
                self.checkConfigurationStats()
                self.configure.monitor.mode = "checktriggers"

    # Goes through all available instances and checks if the configuration info is pushed to all SICs, if not, tries to push the info
    def checkConfigurationStats(self):
        result = -1
        # Waits till the deployment of the stack is finished
        while(result == -1):
            time.sleep(1)
            result, listOfAllServers = self.so_e.getServerIPs()

        writeLogFile(self.swComponent,"Update successful",'','')
        writeLogFile(self.swComponent,"Check config stat of instances",'','')
        checkList = {}
        for item in listOfAllServers:
            if item != "mcn.dss.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.dss.dashboard.lb.endpoint" and item != "mcn.endpoint.dssaas":
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
                        writeLogFile(self.swComponent,target,'','')
                        try:
                            h = http.Http()
                            h.timeout = self.timeout
                            writeLogFile(self.swComponent,"Sending config request to " + item + ":",'','')
                            response, content = h.request(target, 'GET', None, headers)
                            writeLogFile(self.swComponent,"Config stat is: " + str(content),'','')
                        except Exception as e:
                            writeLogFile(self.swComponent,"Handled config request exception " + str(e),'','')
                            continue
                        response_status = int(response.get("status"))
                        instanceInfo = json.loads(content)
                        if "False" not in instanceInfo.values():
                            writeLogFile(self.swComponent,item + " already configured",'','')
                            checkList[item] = "Configured"
                        else:
                            writeLogFile(self.swComponent,'Configuring ' + item ,'','')
                            writeLogFile(self.swComponent,'Configuring in progress ...' ,'','')
                            self.configure.provisionInstance(item, listOfAllServers)
                            self.configure.configInstance(item)
                            writeLogFile(self.swComponent,'instance ' + item + ' configured successfully','','')   
                            self.configure.deploymentPause()
                            response_status = 0
                            while (response_status < 200 or response_status >= 400):
                                time.sleep(1)
                                headers = {
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json; charset=UTF-8'
                                }
                                target = 'http://' + item + ':8051/v1.0/hostname'
                                writeLogFile(self.swComponent,target,'','')
                                try:
                                    h = http.Http()
                                    h.timeout = self.timeout
                                    writeLogFile(self.swComponent,"Sending hostname request to " + item + ":",'','')
                                    response, content = h.request(target, 'GET', None, headers)
                                except Exception as e:
                                    writeLogFile(self.swComponent,"Handled hostname request exception " + str(e),'','')
                                    continue
                                response_status = int(response.get("status"))
                                self.configure.SICMonConfig(content)
                            resp = self.configure.sendRequestToStatusUI(self.configure.ui_url + '/v1.0/service_ready', 'POST', '{"user":"SO","token":"' + self.configure.ui_token + '","components":[{"name":"cms' + str(self.so_e.templateManager.numberOfCmsInstances) + '"}]}')
                            writeLogFile(self.swComponent,"Request response is:" + str(resp),'','')

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
        writeLogFile(self.swComponent,"SOConfigure executed ................",'','')

        self.so_e = so_e
        self.so_d = so_d

        self.dns_forwarder = None
        self.dns_api = None
        self.dssCmsDomainName = self.so_e.dssCmsDomainName
        self.dssMcrDomainName = self.so_e.dssMcrDomainName
        self.dssCmsRecordName = self.so_e.dssCmsRecordName
        self.dssDashboardRecordName = self.so_e.dssDashboardRecordName
        self.dssMcrRecordName = self.so_e.dssMcrRecordName

        self.monitoring_endpoint = None
        self.monitor = None
        self.instances = None
        self.mcr_host_name = None

        #self.cdn_password = None
        #self.cdn_endpoint = None
        #self.cdn_global_id = None
        #self.cdn_origin = None

        self.ui_url = "http://54.171.14.235:8055"

        self.icn_endpoint = None

        self.timeout = 10

        self.dependencyStat = {"DNS":"not ready","MON":"not ready","CDN":"ready","ICN":"not ready"}

        resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/auth', 'POST', '{"user":"SO","password":"SO"}')
        self.ui_token = resp["token"]
        writeLogFile(self.swComponent,"Auth response is:" + str(resp),'','')

    def run(self):
        #Pushing DNS configurations to DNS SICs
        #------------------------------------------------------------------------------#
        # Comment the next 11 lines in case you are using SDK GET DNSaaS functionality #
        # And don't forget to set its stat to "Ready"                                  #
        # self.dependencyStat["DNS"] = "ready"                                         #
        #------------------------------------------------------------------------------#

        if self.so_e.templateManager.dns_enable == 'true':
            writeLogFile(self.swComponent,"Waiting for DNS config info ...",'','')
            while self.dependencyStat["DNS"] != "ready":
                if self.so_e.dns_api != None and self.so_e.dns_forwarder != None:
                    self.dns_forwarder = self.so_e.dns_forwarder
                    self.dns_api = self.so_e.dns_api
                    resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"dnsaas"}]}')
                    writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')
                    LOG.debug("DNS Forwarder EP: " + self.dns_forwarder)
                    LOG.debug("DNS api EP: " + self.dns_api)
                    self.performDNSConfig()
                    self.dependencyStat["DNS"] = "ready"
                    resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'POST', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"dnsaas"}]}')
                    writeLogFile(self.swComponent,"Service_ready post response is:" + str(resp),'','')

                time.sleep(3)
        else:
            self.dns_forwarder = '4.2.2.4'
            self.dependencyStat["DNS"] = "ready"
            LOG.debug("DNSaaS disabled, using " + self.dns_forwarder + " as DNS server")
        writeLogFile(self.swComponent,"DNSaaS dependency stat changed to READY",'','')

        #------------------------------------------------------------------------------#
        # Comment the next 16 lines in case you are using SDK GET CDNaaS functionality #
        # And don't forget to set its stat to "Ready"                                  #
        # self.dependencyStat["CDN"] = "ready"                                         #
        #------------------------------------------------------------------------------#
        #writeLogFile(self.swComponent,"Waiting for CDN config info ...",'','')
        #while self.dependencyStat["CDN"] != "ready":
        #    if self.so_e.cdn_endpoint != None:
        #        self.cdn_password = self.so_e.cdn_password
        #        self.cdn_endpoint = self.so_e.cdn_endpoint
        #        self.cdn_global_id = self.so_e.cdn_global_id
        #        self.cdn_origin = self.so_e.cdn_origin
        #        #Configuring primary parameters of CDN service - empty for now
        #        self.performCDNConfig()
        #        writeLogFile(self.swComponent,"CDN Origin: " + self.cdn_origin,'','')
        #        writeLogFile(self.swComponent,"CDN Endpoint: " + self.cdn_endpoint,'','')
        #        writeLogFile(self.swComponent,"CDN Global Id: " + self.cdn_global_id,'','')
        #        writeLogFile(self.swComponent,"CDN Password: " + self.cdn_password,'','')
        #        self.dependencyStat["CDN"] = "ready"
        #    time.sleep(3)
        #writeLogFile(self.swComponent,"CDNaaS dependency stat changed to READY",'','')

        if self.so_e.templateManager.icn_enable == 'true':
            writeLogFile(self.swComponent,"Waiting for ICN config info ...",'','')
            while self.dependencyStat["ICN"] != "ready":
                if self.so_e.icn_endpoint != None:
                    self.icn_endpoint = self.so_e.icn_endpoint
                    resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"icnaas"}]}')
                    writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')
                    #Configuring primary parameters of ICN service - empty for now
                    self.performICNConfig()
                    writeLogFile(self.swComponent,"ICN Endpoint: " + self.icn_endpoint,'','')
                    self.dependencyStat["ICN"] = "ready"
                time.sleep(3)
            writeLogFile(self.swComponent,"ICNaaS dependency stat changed to READY",'','')

        #---------------------------------------------------------------------------#
        # Comment the next 9 lines in case you are using SDK GET MaaS functionality #
        # And don't forget to set its stat to "Ready"                               #
        # self.dependencyStat["MON"] = "ready"                                      #
        #---------------------------------------------------------------------------#
        writeLogFile(self.swComponent,"Waiting for Monitoring config info ...",'','')
        while self.dependencyStat["MON"] != "ready":
            if self.so_e.monitoring_endpoint != None:
                #Now that all DSS SICs finished application deployment we can start monitoring
                self.monitoring_endpoint = self.so_e.monitoring_endpoint
                resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'PUT', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"monaas"}]}')
                writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')
                writeLogFile(self.swComponent,"MON EP: " + self.monitoring_endpoint,'','')
                self.dependencyStat["MON"] = "ready"
            time.sleep(3)
        writeLogFile(self.swComponent,"MONaaS dependency stat changed to READY",'','')

        #Pushing local configurations to DSS SICs
        self.performLocalConfig()

        #Wait for DSS SICs to finish application deployment
        self.deploymentPause()
        if self.so_e.templateManager.aaa_enable == 'true':
            resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'POST', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"cms1"},{"name":"mcr"},{"name":"db"},{"name":"slaaas"},{"name":"aaaaas"},{"name":"lbaas"}]}')
            writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')
        else:
            resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'POST', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"cms1"},{"name":"mcr"},{"name":"db"},{"name":"slaaas"},{"name":"lbaas"}]}')
            writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')

        # Creating a monitor for pulling MaaS information
        # We need it here because we need all teh custome items and everything configured before doing it

        #maas_obj = util.get_maas(token=YOUR_TOKEN, tenant_name=SHARED_TENANT)
        #This get_address function is recursive so we don't have to put it inside an infinite loop
        #self.monitoring_endpoint = maas_obj.get_address(YOUR_TOKEN)

        self.monitor = SOMonitor(self.so_e,self.so_d,self.monitoring_endpoint,0,'http://' + self.monitoring_endpoint +'/zabbix/api_jsonrpc.php','admin','zabbix')
        self.performMonConfig()
        resp = self.sendRequestToStatusUI(self.ui_url + '/v1.0/service_ready', 'POST', '{"user":"SO","token":"' + self.ui_token + '","components":[{"name":"monaas"}]}')
        writeLogFile(self.swComponent,"Service_ready response is:" + str(resp),'','')

        #writeLogFile(self.swComponent,"Start monitoring service ...",'','')
        self.monitor.start()
        # once logic executes, deploy phase is done
        self.event.set()

    def deploymentPause(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(self.instances) ,'','')

        #WAIT FOR FINISHING THE DEPLOYMENT
        for item in self.instances:
            if item != "mcn.dss.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.dss.dashboard.lb.endpoint" and item != "mcn.endpoint.dssaas":
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
                        writeLogFile(self.swComponent,"Sending deployment status request to:" + target  ,'','')
                        response, content = h.request(target, 'GET', None, headers)
                    except Exception as e:
                        writeLogFile(self.swComponent,"Handled deployment status request exception." + str(e) ,'','')
                        continue
                    response_status = int(response.get("status"))
                    writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')

    def performDNSConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(self.instances) ,'','')

        #configure instances
        writeLogFile(self.swComponent,"Entering the loop to push dns domain names for each instance ...",'','')

        for item in self.instances:
            lbDomainExists = self.so_e.dnsManager.get_domain(self.dssCmsDomainName, self.so_e.token)
            if lbDomainExists.get('code', None) is not None and lbDomainExists['code'] == 404:
                result = -1
                while (result != 1):
                    time.sleep(2)
                    result = self.so_e.dnsManager.create_domain(self.dssCmsDomainName, "info@dss-test.es", 3600, self.so_e.token)
                    writeLogFile(self.swComponent,result.__repr__(), '', '')
                    writeLogFile(self.swComponent,'DNS domain creation attempt for: ' + str(self.instances[item]) , '', '')
                writeLogFile(self.swComponent,'DNS domain created for: ' + str(self.instances[item]) , '', '')
            else:
                writeLogFile(self.swComponent,'DNS domain already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbDomainExists.__repr__(), '', '')
            if item == "mcn.dss.lb.endpoint":
                lbRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssCmsDomainName, record_name=self.dssCmsRecordName, record_type='A', token=self.so_e.token)
                if lbRecordExists.get('code', None) is not None and lbRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(2)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssCmsDomainName,record_name=self.dssCmsRecordName, record_type='A', record_data=self.instances[item], token=self.so_e.token)
                        writeLogFile(self.swComponent,result.__repr__(), '', '')
                        writeLogFile(self.swComponent,'DNS record creation attempt for: ' + str(self.instances[item]) , '', '')
                    writeLogFile(self.swComponent,'DNS record created for: ' + str(self.instances[item]) , '', '')
                else:
                    writeLogFile(self.swComponent,'DNS record already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbRecordExists.__repr__(), '', '')
            elif item == "mcn.dss.dashboard.lb.endpoint":
                dashboardRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssCmsDomainName, record_name=self.dssDashboardRecordName, record_type='A', token=self.so_e.token)
                if dashboardRecordExists.get('code', None) is not None and dashboardRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(2)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssCmsDomainName, record_name=self.dssDashboardRecordName, record_type='A', record_data=self.instances[item], token=self.so_e.token)
                        writeLogFile(self.swComponent,result.__repr__(), '', '')
                        writeLogFile(self.swComponent,'DNS record creation attempt for:' + str(self.instances[item]) , '', '')
                    writeLogFile(self.swComponent,'DNS record created for: ' + str(self.instances[item]) , '', '')
                else:
                    writeLogFile(self.swComponent,'DNS record already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbRecordExists.__repr__(), '', '')

            elif item == "mcn.dss.mcr.endpoint":
                #mcrDomainExists = DNSaaSClientAction.get_domain(self.dssMcrDomainName, self.so_e.token)
                #writeLogFile(self.swComponent,mcrDomainExists.__repr__(), '', '')
                #if mcrDomainExists['code'] == 404:
                #    result = -1
                #    while (result != 1):
                #        time.sleep(2)
                #        result = DNSaaSClientAction.create_domain(self.dssMcrDomainName, "info@dss-test.es", 3600, self.so_e.token)
                #        writeLogFile(self.swComponent,result.__repr__(), '', '')
                #        writeLogFile(self.swComponent,'DNS domain creation attempt for:' + str(self.instances[item]) , '', '')
                #    writeLogFile(self.swComponent,'DNS domain created for: ' + str(self.instances[item]) , '', '')
                #else:
                #    writeLogFile(self.swComponent,'DNS domain already exists for:' + str(self.instances[item]) , '', '')
                mcrRecordExists = self.so_e.dnsManager.get_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', token=self.so_e.token)
                if mcrRecordExists.get('code', None) is not None and mcrRecordExists['code'] == 404:
                    result = -1
                    while (result != 1):
                        time.sleep(2)
                        result = self.so_e.dnsManager.create_record(domain_name=self.dssMcrDomainName, record_name=self.dssMcrRecordName, record_type='A', record_data=self.instances[item], token=self.so_e.token)
                        writeLogFile(self.swComponent,result.__repr__(), '', '')
                        writeLogFile(self.swComponent,'DNS record creation attempt for:' + str(self.instances[item]) , '', '')
                    writeLogFile(self.swComponent,'DNS record created for: ' + str(self.instances[item]) , '', '')
                else:
                    writeLogFile(self.swComponent,'DNS record already exists for:' + str(self.instances[item]) + ' Or invaid output: ' + lbRecordExists.__repr__(), '', '')

        writeLogFile(self.swComponent,"Exiting the loop to push dns domain names for all instances",'','')

    def performCDNConfig(self):
        pass

    def performICNConfig(self):
        pass

    def performLocalConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(self.instances) ,'','')

        result = -1
        while (result < 0):
            time.sleep(1)
            result, serverList = self.so_e.getServerNamesList()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(serverList) ,'','')

        for item in serverList:
            zabbixName = item.replace("_","-")
            if "mcr" in zabbixName:
                self.mcr_host_name = zabbixName

        #configure instances
        writeLogFile(self.swComponent,"Entering the loop to provision each instance ...",'','')
        for item in self.instances:
            if item != "mcn.dss.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.dss.dashboard.lb.endpoint" and item != "mcn.endpoint.dssaas":
                self.provisionInstance(self.instances[item],self.instances)

        writeLogFile(self.swComponent,"Entering the loop to create JSON config file for each instance ...",'','')
        for item in self.instances:
            if item != "mcn.dss.lb.endpoint" and item != "mcn.dss.db.endpoint" and item != "mcn.dss.dashboard.lb.endpoint" and item != "mcn.endpoint.dssaas":
                self.configInstance(self.instances[item])

        writeLogFile(self.swComponent,"Exiting the loop for JSON config file creation for all instances",'','')

    # Executes the two shell scripts in the SIC which takes care of war deployment
    def provisionInstance(self, target_ip, all_ips):
        #AGENT AUTH
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/auth','POST','{"user":"SO","password":"SO"}')
        token = resp["token"]
        writeLogFile(self.swComponent,"Auth response is:" + str(resp)  ,'','')
        #AGENT STARTS PROVISIONING OF VM
        #CMS ip address is sent to MCR for cross domain issues but as the player is trying to get contents from CMS DOMAIN NAME it will not work as it's an ip address
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/provision','POST','{"user":"SO","token":"'+ token +'","mcr_srv_name":"'+ self.mcr_host_name +'","mcr_srv_ip":"'+ all_ips["mcn.dss.mcr.endpoint"] +'","cms_srv_ip":"' + all_ips["mcn.dss.lb.endpoint"] + '","dbaas_srv_ip":"'+ all_ips["mcn.dss.db.endpoint"] +'","dbuser":"'+ self.so_e.templateManager.dbuser +'","dbpassword":"'+ self.so_e.templateManager.dbpass +'","dbname":"'+ self.so_e.templateManager.dbname +'"}')
        writeLogFile(self.swComponent,"Provision response is:" + str(resp)  ,'','')

    # Calls to the SIC agent to complete the provisioning
    def configInstance(self, target_ip):
        #AGENT AUTH
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/auth','POST','{"user":"SO","password":"SO"}')
        token = resp["token"]
        writeLogFile(self.swComponent,"Auth response is:" + str(resp)  ,'','')
        #AGENT PUSH DNS EP
        #DNS endpoint will be used later by CMS application to generate the player configuration script
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/DNS','POST','{"user":"SO","token":"' + token + '","dnsendpoint":"'+ self.dns_forwarder + '","dssdomainname":"' + self.dssCmsRecordName + '.'  + self.dssCmsDomainName + '"}')
        writeLogFile(self.swComponent,"DNS response is:" + str(resp)  ,'','')
        #AGENT PUSH ICN EP & ACC INFO
        #ICN data to be used by CMS for finding closest icn router
        if self.so_e.templateManager.icn_enable == 'true':
            resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/ICN','POST','{"user":"SO","token":"'+ token +'","icnendpoint":"'+ self.icn_endpoint +'"}')
            writeLogFile(self.swComponent,"ICN response is:" + str(resp)  ,'','')
        #AGENT PUSH MON EP & CONFIG
        #MON endpoint is not really being used at the moment
        #DB info is being sent to be used by the getcdr script in zabbix custom item definitions
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/MON','POST','{"user":"SO","token":"'+ token +'","monendpoint":"'+ self.monitoring_endpoint +'","dbuser":"'+ self.so_e.templateManager.dbuser +'","dbpassword":"'+ self.so_e.templateManager.dbpass +'","dbname":"'+ self.so_e.templateManager.dbname +'"}')
        writeLogFile(self.swComponent,"MON response is:" + str(resp)  ,'','')
        #AGENT PUSH RCB CONFIG
        #DB info is used to create an event for generating cdr data in DB
        resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/RCB','POST','{"user":"SO","token":"'+ token +'","dbuser":"'+ self.so_e.templateManager.dbuser +'","dbpassword":"'+ self.so_e.templateManager.dbpass +'","dbname":"'+ self.so_e.templateManager.dbname +'"}')
        writeLogFile(self.swComponent,"RCB response is:" + str(resp)  ,'','')
        #AGENT PUSH CDN EP & ACC INFO
        #CDN data to be used by MCR for uploading data
        #resp = self.sendRequestToSICAgent('http://' + target_ip + ':8051/v1.0/CDN','POST','{"user":"SO","token":"'+ token +'","cdnpassword":"'+ self.cdn_password +'","cdnglobalid":"'+ self.cdn_global_id +'","cdnendpoint":"'+ self.cdn_origin +'","cdnfirstpop":"' + self.cdn_origin + '"}')
        #writeLogFile(self.swComponent,"CDN response is:" + str(resp)  ,'','')

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
                writeLogFile(self.swComponent,"Sending request to:" + api_url  ,'','')
                response, content = h.request(api_url, req_type, json_data, headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled " + api_url + " exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status) + " Content: " + str(content) ,'','')
            if (response_status < 200 or response_status >= 400):
                continue
            content_dict = json.loads(content)
            return content_dict
            #if response status is not OK, retry

    def sendRequestToStatusUI(self, api_url, req_type, json_data):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        try:
            h = http.Http()
            h.timeout = 10
            writeLogFile(self.swComponent,"Sending request to:" + api_url  ,'','')
            response, content = h.request(api_url, req_type, json_data, headers)
        except Exception as e:
            writeLogFile(self.swComponent,"Handled " + api_url + " exception." + str(e) ,'','')
        response_status = int(response.get("status"))
        writeLogFile(self.swComponent,"response status is:" + str(response_status) + " Content: " + str(content) ,'','')
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
        writeLogFile(self.swComponent,time.strftime("%H:%M:%S"),'','')
        writeLogFile(self.swComponent,targetHostName,'','')
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
                res = self.monitor.itemExists(zabbixName, "DSS.RCB.CDRString")
                if res != 1:
                    # 4 - Specifies data type "String" and 30 Specifies this item will be checked every 30 seconds 
                    res = self.monitor.configItem("DSS RCB CDR data", zabbixName, "DSS.RCB.CDRString", 4, 30)

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.itemExists(zabbixName, "DSS.Players.CNT")
                if res != 1:
                    # 4 - Specifies data type "Unsigned" and 30 Specifies this item will be checked every 30 seconds
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
                res = self.monitor.configTrigger('More than 60% cpu utilization for more than 1 minute on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].min(1m)}<40')

            res = 0
            while (res != 1):
                time.sleep(1)
                res = self.monitor.configTrigger('Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].avg(10m)}>90')

        writeLogFile(self.swComponent,'All triggers and items added succesfully for host: ' + targetHostName,'','')

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
