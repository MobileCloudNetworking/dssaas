'''''''''
# DNS Manager to update dss related dns records n DNSaaS  
'''''''''
import threading
import json
from so import writeLogFile
import time
import os
import csv
import datetime

import httplib2 as http

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

HERE = os.environ.get('OPENSHIFT_REPO_DIR', '.')

# To be replaced with python logging
def writeLogFile(swComponent ,msgTo, statusReceived, jsonReceived):
    with os.fdopen(os.open(os.path.join(HERE, 'LOG_ERROR_FILE.csv'), os.O_WRONLY | os.O_CREAT, 0600), 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),' ['+swComponent+'] ',msgTo, statusReceived, jsonReceived ])
        csvfile.close()
        
class SOMonitor(threading.Thread):
    '''
    This class is responsible to add triggers and items which are needed for monitoring DSS SICs
    It also updates the decision array ( according to the added triggers ) which will be used in decision part of service orchestrator
    And contacts zabbix to get the problematic triggers so that SO-D can take scale decisions accordingly 
    '''
    def __init__(self, executionModule, decisionModule, ipMaaS = '160.85.4.52', portMaaS = 0 , apiurlMaaS = 'http://160.85.4.52/zabbix/api_jsonrpc.php', apiUserMaaS = 'admin', apiPassMaaS = 'zabbix'):
        self.swComponent = 'SO-Monitor'
        threading.Thread.__init__(self)
        
        self.ipMaaS = ipMaaS
        self.portMaaS = portMaaS
        self.apiurlMaaS = apiurlMaaS
        self.apiUserMaaS = apiUserMaaS
        self.apiPassMaaS = apiPassMaaS
        self.__authId = ''
        self.addedServers = {}
        self.so_e = executionModule
        self.so_d = decisionModule
        
        self.mode = "addtriggers"
        writeLogFile(self.swComponent,"SOMonitor initiated ................",'','')
        
    def run(self):
        i = 0
        serverList = self.so_e.getServerNamesList()
        
        while(1):
            # Adding triggers to zabbix for each registered DSS SIC 
            if self.mode == "addtriggers":
                time.sleep(3)
                if i > 20:
                    serverList = self.so_e.getServerNamesList()
                    i = 0
                else:
                    i += 1
                writeLogFile(self.swComponent,time.strftime("%H:%M:%S"),'','')
                changeFlag = 0
                for item in serverList:
                    writeLogFile(self.swComponent,item,'','')
                    zabbixName = item.replace("_","-")
                    
                    res = self.configTrigger('More than 60% cpu utilization for more than 1 minute on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].min(1m)}<40')
                    if res == 1:
                        changeFlag = 1
                        
                    res = self.configTrigger('Less than 10% cpu utilization for more than 10 minutes on {HOST.NAME}',zabbixName,':system.cpu.util[,idle].avg(10m)}>90')
                    if res == 1:
                        changeFlag = 1
                    
                    if "mcr" in zabbixName:            
                        res = self.configItem("Free disk space in %", zabbixName, "vfs.fs.size[/,pfree]", 0, 10)
                        if res == 1:
                            changeFlag = 1
                        
                        # 4 - Specifies data type "String" and 10 Specifies this item will be checked every 30 seconds    
                        res = self.configItem("DSS RCB CDR data", zabbixName, "DSS.RCB.CDRString", 4, 30)
                        if res == 1:
                            changeFlag = 1            
                        
                        res = self.configTrigger('More than 90% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}<10')
                        if res == 1:
                            changeFlag = 1            
                        
                        res = self.configTrigger('Less than 30% hard disk usage on {HOST.NAME}', zabbixName, ':vfs.fs.size[/,pfree].last(0)}>70')
                        if res == 1:
                            changeFlag = 1             
                            
                if changeFlag == 0:
                    # Finished adding triggers so we change to monitoring mode
                    self.mode = "checktriggers"
                    writeLogFile(self.swComponent,str(self.so_d.decisionArray) ,'','')
            # Getting the triggers which are triggered if in monitoring mode        
            elif self.mode == "checktriggers":
                time.sleep(10)
                if i > 6:
                    serverList = self.so_e.getServerNamesList()
                    i = 0
                else:
                    i += 1
                writeLogFile(self.swComponent,time.strftime("%H:%M:%S") ,'','')
                self.so_d.hostsWithIssues = []
                for item in serverList:
                    writeLogFile(self.swComponent,item ,'','')
                    if len(item) > 1:
                        res = self.getProblematicTriggers(item.replace("_","-"))
                        for trigger in res:
                            self.so_d.hostsWithIssues.append(trigger)
                        writeLogFile(self.swComponent,str(res) ,'','')
                writeLogFile(self.swComponent,str(self.so_d.hostsWithIssues) ,'','')
            # Idle mode will be enabled when scaling out is happening    
            elif self.mode == "idle":
                time.sleep(5)
                
    #Add trigger to zabbix and update decision array            
    def configTrigger(self, tName, zName, tCondition):
        triggerName = tName
        zabbixName = zName
        if zabbixName + ":" + triggerName not in self.addedServers.keys():
            if len(zabbixName) > 1:
                result = self.addTriggerToMaas(zabbixName, triggerName,'{' + zabbixName + tCondition)
                if result != -1:
                    self.so_d.decisionArray.update({str(result):[str(zabbixName), str(triggerName)]})
                    self.addedServers[zabbixName + ":" + triggerName] = result 
                    writeLogFile(self.swComponent,"Trigger added and id is : " + result ,'','')
            return 1
        return 0
    
    # Add item to zabbix
    def configItem(self, iName, zName, iKey, valueType, delay):
        itemName = iName
        zabbixName = zName
        if zabbixName + ":" + itemName not in self.addedServers.keys():
            if len(zabbixName) > 1:
                result = self.addItemToMaas(zabbixName, "General", itemName, iKey, valueType, delay)
                if result != -1:
                    self.addedServers[zabbixName + ":" + itemName] = result 
                    writeLogFile(self.swComponent,"Item successfully added",'','')
            return 1
        return 0
        
    # Implements zabbix interface o add a trigger    
    def addTriggerToMaas(self, hostName, triggerDescription, expression):
        '''
        Adds a trigger to Zabbix server
        :param hostName: Hostname to add the trigger to
        :param triggerDescription: This will be the trigger name
        :param expression: Expression for the new trigger
        :return: 1 if the creation is successful and -1 if error occurs  
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            jsonData = {
                        "jsonrpc": "2.0",
                        "method": "trigger.create",
                        "params":[{
                                   "description": triggerDescription,
                                   "expression": expression,
                                   "status": 0,
                                   "priority": 2
                                   }],
                        "auth": str(self.__authId),
                        "id": 1
                        }
            status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
            if "result" in content:
                return content["result"]["triggerids"][0]
        writeLogFile(self.swComponent,'Error adding trigger to host:' + hostName, status, content)     
        return -1
    
    # Implements zabbix interface o add a trigger
    def addItemToMaas(self, hostName, AppName, itemName, itemKey, valueType, delay):
        '''
        Adds an item to Zabbix server
        :param hostName: Hostname to add the item to
        :param AppName: Application name that the item will be added to
        :param itemName: This will be the item name
        :param itemKey: Key defined in zabbix server for this item
        :param valueType: Possible values: 0 - numeric float; 1 - character; 2 - log; 3 - numeric unsigned; 4 - text
        :return: 1 if the creation is successful and -1 if error occurs   
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                applicationId = self.__getApplicationId(hostId[0]['hostid'],AppName)
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "item.create",
                        "params":{
                                   "name": itemName,
                                   "key_": itemKey,
                                   "type": 7, #Zabbix Agent(active)
                                   "value_type": valueType,
                                   "delay": delay, 
                                   "history": 7, #Keep history for 7 days
                                   "hostid": str(hostId[0]['hostid']),
                                   "applications": [str(applicationId)]
                                   },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if "result" in content:
                    return 1
        writeLogFile(self.swComponent,'Error adding item to host:' + hostName, status, content)     
        return -1
    
    # Iterates through triggers and returns a list of the ones with PROBLEM status 
    def getProblematicTriggers(self, hostName, valuesLimit = 10):
        '''
        Lists the triggers with PROBLEM status
        :param hostName: Hostname to list the problematic triggers
        :param valuesLimit: Sets how many problematic triggers will be selected
        '''
        status = '0'
        content = "WoW"
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostsid = self.__getHostId(hostName)
            if hostsid is not None:
                jsonData = {
                            "jsonrpc": "2.0",
                            "method": "trigger.get",
                            "params": {
                                       "filter":{
                                                 "hostid": [str(hostsid[0]['hostid'])]
                                                 },
                                       "output": "extend"
                                       },
                            "auth": str(self.__authId),
                            "id": 1
                }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                problematicTriggers = {}    
                if status == '200':
                    for item in content['result']:
                            if item['value'] == "1":
                                problematicTriggers[str(item['triggerid'])] = str(item['description'])
                    return problematicTriggers
                else:
                    return status
            else:
                writeLogFile(self.swComponent,'MaaS Trigger Id', status, content)
                return 'None'
        
    def doRequestMaaS(self, method, body):
        '''
        Method to perform requests to the MaaS.
        :param method: Method to the MaaS (ex: GET)
        :param body: Messages to sent to MaaSS
        '''
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        target = urlparse(self.apiurlMaaS)
        h = http.Http()
        try:
            response, content = h.request(target.geturl(), method, body, headers)
        except Exception as e:
            return -1, "Server API not reachable \nError:"+str(e)
        response_status = response.get("status")
        content_dict = json.loads(content)

        return response_status, content_dict
    
    def __getApplicationId (self, hostId , applicationName):
        '''
        Method to get a application id from the MaaS.
        :param hostId: Host id to send to MaaS
        :param applicationName: Name of the application to sent to MaaSS
        :rtype : return
        '''
        jsonData = {
                        "jsonrpc": "2.0",
                        "method": "application.get",
                        "params": {
                            "output": "extend",
                            "hostids": hostId,
                            "sortfield": "name"
                        },
                        "auth": self.__authId,
                        "id": 1
                    }
        status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
        if status == '200':
            for application in content['result']:
                if application['name'] == applicationName:
                    return application['applicationid']
        else:
            writeLogFile(self.swComponent,'MaaS Application Id', status, content)
            return None
        
    def __getHostId(self, hostName):
        '''
        Method to get a host id from the MaaS.
        :param hostName: Name of the host to search in the MaaS
        :rtype : return
        '''
        jsonData = {
                    "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": "extend",
                        "filter": {
                            "host":[hostName]
                        }
                    },
                    "auth": self.__authId,
                    "id": 1
                }
        status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
        if status == '200':
            if len(content['result']) == 1:
                return content['result']
            else:
                return None
        else:
            writeLogFile(self.swComponent,'MaaS Host Id', status, content)
            return None

    def __getAuthId(self):
        '''
        Method to perform authentication to the MaaS.
        '''
        jsonData = {"jsonrpc": "2.0",
               "method": "user.login",
               "params": {"user": self.apiUserMaaS,
                          "password": self.apiPassMaaS},
               "id": 2}
        status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
        if status == '200':
            return content['result']
        else:
            writeLogFile(self.swComponent,'MaaS Authentication', status, content)
            return None
