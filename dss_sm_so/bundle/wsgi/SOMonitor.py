'''''''''
# DNS Manager to update dss related dns records n DNSaaS  
'''''''''
import threading
import json
import time
import logging

import httplib2 as http

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()
        
class SOMonitor(threading.Thread):
    '''
    This class is responsible to add triggers and items which are needed for monitoring DSS SICs
    It also updates the decision array ( according to the added triggers ) which will be used in decision part of service orchestrator
    And contacts zabbix to get the problematic triggers so that SO-D can take scale decisions accordingly 
    '''
    def __init__(self, executionModule, decisionModule, ipMaaS = '192.168.100.21', portMaaS = 0 , apiurlMaaS = 'http://192.168.100.21/zabbix/api_jsonrpc.php', apiUserMaaS = 'zAdmin', apiPassMaaS = '*******'):
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
        self.changeMode = False

        self.webScenarioList = []
        self.scenarioAllowedFailCount = 6
        self.ftItemList = []
        self.ftItemFailCount = 6
        self.mode = "addtriggers"
        LOG.debug(self.swComponent + ' ' + "SOMonitor initiated ................")
        
    def run(self):
        i = 0
        result = -1
        
        while 1:
            # Getting the triggers which are triggered if in monitoring mode        
            if self.mode == "checktriggers":
                time.sleep(10)
                if i > 6 or self.changeMode is True:
                    while (result < 0):
                        time.sleep(0.2)
                        result, serverList = self.so_e.getServerInfo()
                    i = 0
                    result = -1
                    self.changeMode = False
                else:
                    i += 1
                LOG.debug(self.swComponent + ' ' + time.strftime("%H:%M:%S"))
                self.so_d.hostsWithIssues = []
                for item in serverList:
                    LOG.debug(self.swComponent + ' ' + item["hostname"])
                    if len(item["hostname"]) > 1:
                        if 'mcr' in item["hostname"]:
                            checkCount = self.getMetric(item["hostname"].replace("_","-"), "DSS.Players.CNT")
                            try:
                                self.so_d.playerCount = int(checkCount)
                                LOG.debug(self.swComponent + ' ' + "Number of active players: " + str(self.so_d.playerCount))
                            except:
                                LOG.error(self.swComponent + ' ' + "Unable to convert player count to Integer")
                        res = self.getProblematicTriggers(item["hostname"].replace("_","-"))
                        try:
                            for trigger in res:
                                self.so_d.hostsWithIssues.append(trigger)
                        except:
                            LOG.debug(self.swComponent + ' ' + 'Be careful! Your trigger stats are messed up!')
                            continue;
                        LOG.debug(self.swComponent + ' ' + str(res))
                LOG.debug(self.swComponent + ' ' + str(self.so_d.hostsWithIssues))

                self.so_d.ftlist[:] = []

                LOG.debug(self.swComponent + ' ' + 'FT list BEFORE check: ' + str(self.so_d.ftlist))
                for item in self.ftItemList:
                    LOG.debug(self.swComponent + ' ' + item["hostName"])
                    if 'mcr' in item["hostName"]:
                        checkFilesyncStat = self.getMetric(item["hostName"].replace("_","-"), "DSS.Filesync.STATUS")
                        checkStreamingStat = self.getMetric(item["hostName"].replace("_","-"), "DSS.Streaming.STATUS")
                        checkTrackerStat = self.getMetric(item["hostName"].replace("_","-"), "DSS.Tracker.STATUS")
                        try:
                            if int(checkFilesyncStat) != 1 or int(checkStreamingStat) != 1 or int(checkTrackerStat) != 1:
                                if item["fail_count"] >= self.ftItemFailCount:
                                    LOG.debug(self.swComponent + ' ' + "Faulty SIC Info: " + str(item))
                                    if item["hostName"] not in self.so_d.ftlist:
                                        self.so_d.ftlist.append(item["hostName"])
                                else:
                                    item["fail_count"] += 1
                            else:
                                item["fail_count"] = 0
                        except Exception as e:
                            LOG.error(self.swComponent + ' ' + "Unable to retrieve service stats, " + str(e))
                for item in self.webScenarioList:
                    LOG.debug(self.swComponent + ' ' + 'Checking item in Web Scenario: ' + str(item))
                    #check = self.getWebScenarioFromMaas(item["id"])
                    check = self.getMetric(item["hostName"].replace("_","-"), "web.test.rspcode[" + item["name"] + ",HomePage]")
                    if check is None:
                        LOG.debug(self.swComponent + ' ' + 'Status code is: Unknown')
                    if check is not None and check != "200":
                        if item["fail_count"] >= self.scenarioAllowedFailCount:
                            LOG.debug(self.swComponent + ' ' + "Faulty SIC Info: " + str(item))
                            LOG.debug(self.swComponent + ' ' + "Status code is: " + check)
                            if item["hostName"] not in self.so_d.ftlist:
                                self.so_d.ftlist.append(item["hostName"])
                        else:
                            item["fail_count"] += 1
                    elif check is not None and check == "200":
                        LOG.debug(self.swComponent + ' ' + "Status code is: " + check)
                        # Reset fail count
                        item["fail_count"] = 0
                LOG.debug(self.swComponent + ' ' + 'FT list AFTER check: ' + str(self.so_d.ftlist))

            # Idle mode will be enabled when scaling out is happening    
            elif self.mode == "idle":
                time.sleep(5)

    # Add trigger to zabbix and update decision array
    def configTrigger(self, tName, zName, tCondition):
        triggerName = tName
        zabbixName = zName
        if zabbixName + ":" + triggerName not in self.addedServers.keys():
            if len(zabbixName) > 1:
                result = self.addTriggerToMaas(zabbixName, triggerName,'{' + zabbixName + tCondition)
                if result != -1:
                    self.so_d.decisionArray.update({str(result):[str(zabbixName), str(triggerName)]})
                    self.addedServers[zabbixName + ":" + triggerName] = result 
                    LOG.debug(self.swComponent + ' ' + "Trigger added and id is : " + result)
            return 1
        return 0
    
    # Add item to zabbix
    def configItem(self, iName, zName, iKey, valueType, delay, ft_enabler=False):
        itemName = iName
        zabbixName = zName
        if zabbixName + ":" + itemName not in self.addedServers.keys():
            if len(zabbixName) > 1:
                result = self.addItemToMaas(zabbixName, "General", itemName, iKey, valueType, delay, ft_enabler)
                if result != -1:
                    self.addedServers[zabbixName + ":" + itemName] = result 
                    LOG.debug(self.swComponent + ' ' + "Item successfully added")
            return 1
        return 0
        
    # Implements zabbix interface to add a trigger
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
        LOG.debug(self.swComponent + ' ' + 'Error adding trigger to host: ' + hostName)
        return -1
    
    # Implements zabbix interface to add an item
    def addItemToMaas(self, hostName, AppName, itemName, itemKey, valueType, delay, ft_enabler):
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
                    if ft_enabler:
                        self.ftItemList.append({"name": itemKey, "hostName": hostName.replace("-","_"), "fail_count": 0})
                        LOG.debug(self.swComponent + ' ' + 'FT item successfully added for: ' + hostName)
                    return 1
        LOG.debug(self.swComponent + ' ' + 'Error adding item to host: ' + hostName)
        return -1

    # Implements zabbix interface to add a web scenario
    def addWebScenarioToMaas(self, hostName, scenarioName, stepName, stepUrl, stepStatCode, no):
        '''
        Adds an item to Zabbix server
        Note: we can have more than one step in a scenario but here we just add one
        :param hostName: Hostname to add the item to (String)
        :param scenarioName: A name for the new scenario (String)
        :param stepName: A name for the new specific step (String)
        :param stepUrl: A URL to poll and check if it works fine or not (String)
        :param stepStatCode: The status code of the http call which we expect as working i.e 200 (Integer)
        :return: 1 if the creation is successful and -1 if error occurs
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "httptest.create",
                        "params":{
                                   "name": scenarioName,
                                   "hostid": str(hostId[0]['hostid']),
                                   "delay": "60",
                                   "steps":[{
                                       "name": stepName,
                                       "url": stepUrl,
                                       "status_codes": stepStatCode,
                                       "no": no
                                   }]
                                 },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if "result" in content:
                    self.webScenarioList.append({"name": scenarioName, "hostName": hostName.replace("-","_"), "id": content["result"]["httptestids"][0], "fail_count": 0})
                    LOG.debug(self.swComponent + ' ' + "Web Scenario successfully added with id: " + content["result"]["httptestids"][0])
                    return 1
        LOG.debug(self.swComponent + ' ' + 'Error adding web scenario to host: ' + hostName)
        return -1

    def getWebScenarioFromMaas(self, scenarioId):
        '''
        :param scenarioId: The ID of the target scenario (Integer)
        :return: Json on success i.e {
                    "httpstepid": "4",
                    "httptestid": "4",
                    "name": "Homepage",
                    "no": "1",
                    "url": "http://mycompany.com",
                    "timeout": "30",
                    "posts": "",
                    "required": "",
                    "status_codes": "200",
                    "webstepid": "4"
                }
                Failure -1
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "httptest.get",
                        "params":{
                                   "output": "extend",
                                   "selectSteps": "extend",
                                   "httptestids": str(scenarioId)
                                 },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if "result" in content:
                    return content["result"][0]["steps"][0]
        LOG.debug(self.swComponent + ' ' + 'Error getting we scenario info')
        return -1

    def removeWebScenarioFromWSList(self, hostname):
        targetWS = None
        for item in self.webScenarioList:
            if item["hostName"] == hostname:
                targetWS = item
        if targetWS is not None:
            LOG.debug(self.swComponent + ' ' + 'Removing Web Scenario of host ' + targetWS["hostName"])
            self.webScenarioList.remove(targetWS)

    def removeFTItemFromFTList(self, hostname):
        targetHost = None
        for item in self.ftItemList:
            if item["hostName"] == hostname:
                targetHost = item
        if targetHost is not None:
            LOG.debug(self.swComponent + ' ' + 'Removing FTitem of host ' + targetHost["hostName"])
            self.ftItemList.remove(targetHost)

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
                LOG.debug(self.swComponent + ' ' + 'MaaS Trigger Id')
                return 'None'
            
    def itemExists(self, hostName, itemKey):
        '''
        Checks existance of an item in Zabbix server for a special hostname
        :param hostName: Hostname to add the item to
        :param itemKey: Key defined in zabbix server for this item
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "item.get",
                        "params":{
                                  "output": "extend",
                                  "hostids": str(hostId[0]['hostid']),
                                  "search": {
                                             "key_": itemKey
                                             },
                                  "sortfield": "name"
                                  },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if len(content["result"]) > 0:
                    LOG.debug(self.swComponent + ' ' + 'Item already exists on host: ' + hostName)
                    return 1
        #'Item is not added to the host yet     
        return -1

    def listHostItems(self, hostName):
        '''
        Lists all items in Zabbix server for a special hostname
        :param hostName: Hostname to add the item to
        '''
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "item.get",
                        "params":{
                                  "output": "extend",
                                  "hostids": str(hostId[0]['hostid']),
                                  "sortfield": "name",
                                  "webitems": "true"
                                  },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if len(content["result"]) > 0:
                    LOG.debug(self.swComponent + ' ' + str(content))
                    return 1
        #'Item is not added to the host yet
        return -1

    def getMetric(self, hostName, itemKey):
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "item.get",
                        "params":{
                                  "output": "extend",
                                  "hostids": str(hostId[0]['hostid']),
                                  "search": {
                                             "key_": itemKey
                                             },
                                  "sortfield": "name",
                                  "webitems": "true"
                                  },
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if len(content["result"]) > 0:
                    return content["result"][0]["lastvalue"]
                else:
                    return None
        else:
            return None

    def removeHost(self, hostName):
        self.__authId = self.__getAuthId()
        if self.__authId is not None:
            hostId = self.__getHostId(hostName)
        if hostId is not None:
                jsonData = {
                        "jsonrpc": "2.0",
                        "method": "host.delete",
                        "params":[
                            {"hostid": str(hostId[0]['hostid'])}
                        ],
                        "auth": str(self.__authId),
                        "id": 1
                        }
                status, content =  self.doRequestMaaS('GET', json.dumps(jsonData))
                if len(content["result"]["hostids"]) > 0:
                    LOG.debug(self.swComponent + ' ' + 'Host successfully deleted:' + hostName)
                    return 1
                else:
                    LOG.debug(self.swComponent + ' ' + 'Host ' + hostName + ' not found')
        #Probably host doesn't exist or deletion failed
        return -1

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
            LOG.debug(self.swComponent + ' ' + 'MaaS Application Id')
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
            LOG.debug(self.swComponent + ' ' + 'MaaS Host Id')
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
            LOG.debug(self.swComponent + ' ' + 'MaaS Authentication')
            return None