#   Copyright (c) 2013-2015, Intel Performance Learning Solutions Ltd, Intel Corporation.
#   Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
#   Copyright 2014 SoftTelecom Desarrollos I MAS D S.L.
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

'''
DSS Servcie Orchestrator
'''

# These are imported in DnsMAnager Class
#import json
#import threading
#import time
#import httplib2 as http

import os
import csv
import datetime

from TemplateGenerator import *
from DnsManager import *
from SOMonitor import *
from sdk.mcn import util

HERE = os.environ.get('OPENSHIFT_REPO_DIR', '.')

# To be replaced with python logging
def writeLogFile(swComponent ,msgTo, statusReceived, jsonReceived):
    with os.fdopen(os.open(os.path.join(HERE, 'LOG_ERROR_FILE.csv'), os.O_WRONLY | os.O_CREAT, 0600), 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),' ['+swComponent+'] ',msgTo, statusReceived, jsonReceived ])
        csvfile.close()

# Not used at the moment
class msgErrors:
    '''
    Is the class responsible for the messages of errors
    '''
    authError = 'Error authentication'

class ServiceOrchstratorExecution(object):
    '''
    DSS SO execution part.
    '''

    def __init__(self, token, tenant_name):
        self.swComponent = 'SO-Execution'
        # Generate DSS basic template...
        self.token = token
        self.tenant_name = tenant_name
        self.templateManager = TemplateGenerator()
        self.template = self.templateManager.getTemplate()
        self.templateupdate = ""
        self.stack_id = None
        # make sure we can talk to deployer...
        writeLogFile(self.swComponent,'Make sure we can talk to deployer...', '', '')
        self.deployer = util.get_deployer(self.token, url_type='public', tenant_name=self.tenant_name)

    def deploy(self):
        """
        deploy SICs.
        """
        if self.stack_id is None:
            self.stack_id = self.deployer.deploy(self.template, self.token)

    def update(self):
        """
        update SICs.
        """
        if self.stack_id is not None:
            self.deployer.update(self.stack_id, self.templateupdate, self.token)

    def dispose(self):
        """
        Dispose SICs.
        """
        if self.stack_id is not None:
            self.deployer.dispose(self.stack_id, self.token)
            self.stack_id = None

    def state(self):
        """
        Report on state.
        """
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp['state'] != 'CREATE_COMPLETE' and tmp['state'] != 'UPDATE_COMPLETE':
                return 'Stack is currently being deployed...'
            else:

                print 'All good - Output to return to SM is: ' + str(tmp)
                return json.dumps(tmp)
        else:
            return 'Stack is not deployed atm.'
    
    # Getting the deployed SIC hostnames using the output of deployed stack (Heat Output)     
    def getServerNamesList(self):
        if self.stack_id is not None:
            tmp = self.deployer.details(self.stack_id, self.token)
            if tmp['state'] != 'CREATE_COMPLETE' and tmp['state'] != 'UPDATE_COMPLETE':
                return 'Stack is currently being deployed...'
            else:
                serverList = []
                for i in range(0 ,len(tmp["output"])):
                    if "name" in tmp["output"][i]["output_value"]:
                        serverList.append(str(tmp["output"][i]["output_value"]["name"]))
                    
                return serverList
        else:
            return 'Stack is not deployed atm.'
        
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
                    if not "name" in tmp["output"][i]["output_value"]:# and tmp["output"][i]["output_key"] != "mcn.dss.lb.endpoint":
                        #serverList.append(str(tmp["output"][i]["output_value"]))
                        serverList[tmp["output"][i]["output_key"]] = tmp["output"][i]["output_value"] 
                    
                return 0, serverList
        else:
            return -1, 'Stack is not deployed atm.'
    
    # Returns the current number of CMS VMs deployed in the stack for scaling purposes     
    def getNumberOfCmsInstances(self):
        return self.templateManager.numberOfCmsInstances

class ServiceOrchstratorDecision(threading.Thread):
    '''
    Decision part of DSS SO.
    '''

    def __init__(self, so_e, token):
        self.swComponent = 'SO-Decision'
        threading.Thread.__init__(self)
        
        # Get service orchestrator execution reference
        self.so_e = so_e
        self.token = token
        
        # Variables used for checking current DSS instance status according to monitoring triggers 
        self.decisionArray = {}                      
        self.hostsWithIssues = []
        self.decisionMapMCR = [{"More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":0},
                               {"More than 90% hard disk usage on {HOST.NAME}":0},
                               {"Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}":0},
                               {"Less than 30% hard disk usage on {HOST.NAME}":0}]
        
        self.decisionMapCMS = [{"More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":0},
                               {"Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}":0}]
        
        # Creating a monitor for pulling MaaS information 
        self.monitor = SOMonitor(self.so_e,self)
        # Creating a configuring object ( REST client for SO::SIC interface )
        self.configurer = SOConfigurer(self.so_e,self)
        
        # Scaling guard time
        self.cmsScalethreshold = 1800 #in seconds
        self.McrScalethreshold = 1800 #in seconds
        
        # Current scaling status
        self.lastCmsScale = 0
        self.lastMcrScale = 0
        self.numberOfScaleUpsPerformed = 0
        self.numberOfScaleOutsPerformed = 0
        
        self.timeout = 10

    def run(self):
        # Start pushing configurations to SICs
        self.configurer.start()
        
        # Decision loop
        while(1):
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
            for item in self.decisionMapCMS:
                writeLogFile(self.swComponent,"Checking CMS status",'','')
                if self.lastCmsScale == 0:
                    diff = 0
                else:
                    diff = int(time.time() - self.lastCmsScale)
                writeLogFile(self.swComponent,str(item[item.keys()[0]]) + " == " + str(cmsCount) + " and ( " + str(diff) + " > " + str(self.cmsScalethreshold) + " or " + str(self.lastCmsScale) + " == 0 )",'','')     
                if item[item.keys()[0]] == cmsCount and (diff > self.cmsScalethreshold or self.lastCmsScale == 0):
                    # CMS scale out
                    if item.keys()[0] == "More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":
                        self.lastCmsScale = time.time()
                        self.so_e.templateManager.templateToScaleOut()
                        self.numberOfScaleOutsPerformed += 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN CMS scaleOut",'','')
                    # CMS scale in
                    elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}" and self.numberOfScaleOutsPerformed > 0:
                        self.lastCmsScale = time.time()
                        self.so_e.templateManager.templateToScaleIn()
                        self.numberOfScaleOutsPerformed -= 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN CMS scaleIn",'','')
                                
            for item in self.decisionMapMCR:
                writeLogFile(self.swComponent,"Checking MCR status",'','')
                if self.lastCmsScale == 0:
                    diff = 0
                else:
                    diff = int(time.time() - self.lastMcrScale)
                writeLogFile(self.swComponent,str(item[item.keys()[0]]) + " > 0 and ( " + str(diff) + " > " + str(self.McrScalethreshold) + " or " + str(self.lastMcrScale) + " == 0 )",'','')
                if item[item.keys()[0]] > 0 and (diff > self.McrScalethreshold or self.lastMcrScale == 0):
                    # MCR scale up
                    # It is commented because it's not working for current heat version 
                    if item.keys()[0] == "More than 60% cpu utilization for more than 1 minute on {HOST.NAME}":
                        #self.so_e.templateManager.templateToScaleUp()
                        self.lastMcrScale = time.time()
                        self.numberOfScaleUpsPerformed += 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleUp",'','')
                    elif item.keys()[0] == "More than 90% hard disk usage on {HOST.NAME}":
                        #self.so_e.templateManager.templateToScaleUp()
                        self.lastMcrScale = time.time()
                        self.numberOfScaleUpsPerformed += 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleUp",'','')
                    # MCR scale down
                    elif item.keys()[0] == "Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}" and self.numberOfScaleUpsPerformed > 0:
                        #self.so_e.templateManager.templateToScaleDown()
                        self.lastMcrScale = time.time()
                        self.numberOfScaleUpsPerformed -= 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleDown",'','')
                    elif  item.keys()[0] == "Less than 30% hard disk usage on {HOST.NAME}" and self.numberOfScaleUpsPerformed > 0:
                        self.lastMcrScale = time.time()
                        #self.so_e.templateManager.templateToScaleDown()
                        self.numberOfScaleUpsPerformed -= 1
                        scaleTriggered = True
                        writeLogFile(self.swComponent,"IN MCR scaleDown",'','')
            
            # Call SO execution if scaling required
            writeLogFile(self.swComponent,str(scaleTriggered),'','')           
            if scaleTriggered == True:            
                self.so_e.templateupdate = self.so_e.templateManager.getTemplate()
                writeLogFile(self.swComponent,"Performing stack update",'','')
                self.so_e.update()
                writeLogFile(self.swComponent,"Update successful",'','')
                
                writeLogFile(self.swComponent,"Check config stat of instances",'','')
                # Checking configuration status of the instances after scaling
                self.checkConfigurationStats()
                
    # Goes through all available instances and checks if the configuration info is pushed to all SICs, if not, tries to push the info 
    def checkConfigurationStats(self):
        result = -1
        # Waits till the deployment of the stack is finished
        while(result == -1):
            result, listOfAllServers = self.so_e.getServerIPs()
        
        checkList = {}
        for item in listOfAllServers:
            if item != "mcn.dss.lb.endpoint": 
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
                            self.configurer.configInstance(item)
                            writeLogFile(self.swComponent,'instance ' + item + ' configured successfully','','')
                            self.monitor.mode = "idle"
                            self.configurer.deploymentPause()
                            self.monitor.mode = "addtriggers"                 
    
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
class SOConfigurer(threading.Thread):
    
    def __init__(self,so_e,so_d):
        self.swComponent = 'SO-SIC-Config'
        threading.Thread.__init__(self)
        writeLogFile(self.swComponent,"SOConfigurer executed ................",'','')
        self.monitoring_endpoint = '192.168.0.2'
        self.dns_endpoint = '192.168.0.99'
        self.dns_token = 'dnstoken'
        self.cdnpassword = 'pass'
        self.cdn_endpoint = '160.85.4.104:8182'
        self.so_e = so_e
        self.so_d = so_d
        self.dnsConfig = DnsManager()
        self.dssCmsDomainName = "cms.test03.dss-softtelecom.es"
        self.dssMcrDomainName = "mcr.test03.dss-softtelecom.es"
        self.timeout = 10
        self.cdn_pops = []
        self.cdn_global_id = 0
        self.cdn_origin = 0
        
    def run(self):
        writeLogFile(self.swComponent,"Calling CDN service for Account creation and do POP updates ...",'','')
        #configure CDN data
        #POST:http://160.85.4.104:8182/account 
        #- headers: Content-Type: application/json
        #- payload: {"global_password":"password", "dns_url":"dns.management.endpoint", "dns_token":"tokendata"}
        '''
        self.cdn_global_id = 0
        self.cdn_origin = 0
        
        cdn_info = 0
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            target = 'http://' + self.cdn_endpoint + '/account'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending CDN Account request to: " + target  ,'','')
                response, content = h.request(target, 'POST', '{"global_password":"' + self.cdnpassword + '", "dns_url":"' + self.dns_endpoint + '", "dns_token":"' + self.dns_token + '"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled auth exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
            cdn_info = json.loads(content)
            self.cdn_global_id = cdn_info["global_id"];
            self.cdn_origin = cdn_info["origin"];
        
        
        #GET LIST OF POPS
        #GET: http://160.85.4.104:8182/pop
        #- sample result: [{"location": "FR", "address": "160.85.4.103:8181"}, {"location": "FR", "address": "160.85.4.120:8181"}]
        
        cdn_info = 0
        self.cdn_pops = []
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            target = 'http://' + self.cdn_endpoint + '/pop'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending CDN Account request to: " + target  ,'','')
                response, content = h.request(target, 'GET', None, headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled auth exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
            cdn_info = json.loads(content)
            for pop in cdn_info:
                self.cdn_pops.append(pop["address"])
                


        #UPDATE USER ACCOUNT 
        #POST: http://160.85.4.104:8182/account/d3e30c11-8a4d-41b4-b0c0-17de168de2a9
        #- headers: Content-Type: application/json
        #- payload: {"pops": ["160.85.4.103:8181", "160.85.4.120:8181"], "global_password": "password"}
        #- sample result: {"origin": "160.85.4.103:8181"}
        
        cdn_info = 0
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Content-Type': 'application/json'
            }
            target = 'http://' + self.cdn_endpoint + '/account/' + self.cdn_global_id
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending CDN Account request to: " + target  ,'','')
                payload_pops = '"' + self.cdn_pops[0] + '"'
                for j in range(1 ,len(self.cdn_pops)):
                    payload_pops += ', "' + self.cdn_pops[j] + '"'
                #writeLogFile(self.swComponent,"Payload is : " + '{"pops":[' + payload_pops + '], "global_password":"' + self.cdnpassword + '"}')
                response, content = h.request(target, 'POST', '{"pops":[' + payload_pops + '], "global_password":"' + self.cdnpassword + '"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled auth exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
            cdn_info = json.loads(content)
            self.cdn_origin = cdn_info["origin"];
            
        writeLogFile(self.swComponent,"CDN service account creation and do POP updates finished.",'','')
        '''
        #Pushing DNS configurations to DNS SICs
        self.performDNSConfig()
        
        #Pushing local configurations to DSS SICs        
        self.performLocalConfig()
        
        #Wait for DSS SICs to finish application deployment
        self.deploymentPause()  
        
        #Now that all DSS SICs finished application deployment we can start monitoring
        writeLogFile(self.swComponent,"Start monitoring service ...",'','')
        self.so_d.monitor.start()
    
    def deploymentPause(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(self.instances) ,'','')
            
        #WAIT FOR FINISHING THE DEPLOYMENT
        for item in self.instances:
            if item != "mcn.dss.lb.endpoint": 
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
        
        status = "0"
        while (int(status) < 200 or int(status) >= 400):
            time.sleep(1)
            status, content = self.dnsConfig.getAuthId()
            
        for item in self.instances:
            if item == "mcn.dss.lb.endpoint":
                status = "0"
                while (int(status) < 200 or int(status) >= 400):
                    time.sleep(1)
                    status, content = self.dnsConfig.addDomain(self.dssCmsDomainName + ".", 128, "info@dss-test.es")
                status = "0"
                while (int(status) < 200 or int(status) >= 400):
                    time.sleep(1)
                    status, content = self.dnsConfig.addRecord(content["data"]["id"], self.dssCmsDomainName + ".", "A", self.instances[item])
            elif item == "mcn.dss.mcr.endpoint":
                status = "0"
                while (int(status) < 200 or int(status) >= 400):
                    time.sleep(1)
                    status, content = self.dnsConfig.addDomain(self.dssMcrDomainName + ".", 128, "info@dss-test.es")
                status = "0"
                while (int(status) < 200 or int(status) >= 400):
                    time.sleep(1)
                    status, content = self.dnsConfig.addRecord(content["data"]["id"], self.dssMcrDomainName + ".", "A", self.instances[item])
            
        writeLogFile(self.swComponent,"Exiting the loop to push dns domain names for all instances",'','')
            
    def performLocalConfig(self):
        result = -1
        while (result < 0):
            time.sleep(1)
            result, self.instances = self.so_e.getServerIPs()
            writeLogFile(self.swComponent,"In while: " + str(result) + " , " + str(self.instances) ,'','')
            
        #configure instances
        writeLogFile(self.swComponent,"Entering the loop to create JSON config file for each instance ...",'','')
        for item in self.instances:
            if item != "mcn.dss.lb.endpoint": 
                self.configInstance(self.instances[item])            
            
        writeLogFile(self.swComponent,"Exiting the loop for JSON config file creation for all instances",'','')

    def configInstance(self,ip):
        response_status = 0
        token = ''
        i = ip
        #AGENT AUTH
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/auth'
            try:
                h = http.Http()
                h.timeout = self.timeout
                writeLogFile(self.swComponent,"Sending auth request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","password":"SO"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled auth exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
            if (response_status < 200 or response_status >= 400):
                continue
            content_dict = json.loads(content)
            token = content_dict["token"]
            #if response status is not OK, retry
            
        #AGENT PUSH DNS data
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/DNS'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending DNS request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","token":"'+ token +'","dnsendpoint":"'+ self.dns_endpoint +'"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled DNS exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
                
        #AGENT PUSH MON data
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/MON'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending MON request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","token":"'+ token +'","monendpoint":"'+ self.monitoring_endpoint +'"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled MON exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
            
        #AGENT PUSH RCB data
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/RCB'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending RCB request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","token":"'+ token +'","dbuser":"'+ self.so_e.templateManager.dbuser +'","dbpassword":"'+ self.so_e.templateManager.dbpass +'","dbname":"'+ self.so_e.templateManager.dbname +'"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled RCB exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
    
        ''' 
        #push to the agent
        #- sample result: {"origin": "160.85.4.103:8181", "domain": "d3e30c11-8a4d-41b4-b0c0-17de168de2a9.cdn.mobile-cloud-networking.eu", "global_id": "d3e30c11-8a4d-41b4-b0c0-17de168de2a9"}
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/CDN'
            h = http.Http()
            h.timeout = self.timeout
            try:
                writeLogFile(self.swComponent,"Sending CDN request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","token":"'+ token +'","cdnpassword":"'+ self.cdnpassword +'","cdnglobalid":"'+ self.cdn_global_id +'","cdnendpoint":"'+ self.cdn_origin +'","cdnfirstpop":"' + self.cdn_pops[0] + '"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled CDN exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
        '''  
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            writeLogFile(self.swComponent,"Inside the config loop ...",'','')
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            target = 'http://' + i + ':8051/v1.0/ZABBIX'
            try:
                h = http.Http()
                h.timeout = self.timeout
                writeLogFile(self.swComponent,"Sending MON CONFIG request to:" + target  ,'','')
                response, content = h.request(target, 'POST', '{"user":"SO","token":"'+ token +'","monendpoint":"'+ self.monitoring_endpoint +'","dbuser":"'+ self.so_e.templateManager.dbuser +'","dbpassword":"'+ self.so_e.templateManager.dbpass +'","dbname":"'+ self.so_e.templateManager.dbname +'"}', headers)
            except Exception as e:
                writeLogFile(self.swComponent,"Handled MON_CONFIG exception." + str(e) ,'','')
                continue
            response_status = int(response.get("status"))
            writeLogFile(self.swComponent,"response status is:" + str(response_status)  ,'','')
                
class ServiceOrchstrator(object):
    """
    DSS SO
    """

    def __init__(self, token, tenant_name):
        self.swComponent = 'SO'
        self.so_e = ServiceOrchstratorExecution(token, tenant_name)
        self.so_d = ServiceOrchstratorDecision(self.so_e, token)
        self.so_d.start()
