'''''''''
# DNS Manager to update dss related dns records n DNSaaS  
'''''''''
import threading
import json
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
        
class DnsManager():
    '''
    This class is responsible to add DNS records which are needed for accessing SICs using a domain name 
    '''
    def __init__(self, ipDNS = '192.168.100.21', portDNS = '8080', apiUserDNS = 'admin', apiPassDNS = 'password', apiTenantDNS = 'admin'):
        self.swComponent = 'SO-DNS'
        
        self.ipDNS = ipDNS
        self.portDNS = portDNS
        self.apiUserDNS = apiUserDNS
        self.apiPassDNS = apiPassDNS
        self.apiTenantDNS = apiTenantDNS
        self.apiToken = ''
    
    def doRequestDNS(self, action, method, body):
        '''
        Method to perform requests to the MaaS.
        :param method: Method to the MaaS (ex: GET)
        :param body: Messages to sent to MaaSS
        '''
        if self.apiToken == '':
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
        else:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8',
                'X-auth-token':  self.apiToken
            }

        target = urlparse("http://" + self.ipDNS + ":" + self.portDNS + "/" + action)
        h = http.Http()
        try:
            response, content = h.request(target.geturl(), method, body, headers)
        except Exception as e:
            return -1, "Server API not reachable \nError:"+str(e)
        response_status = response.get("status")
        content_dict = json.loads(content)

        return response_status, content_dict
    
    def addDomain(self, domainName, ttlValue, email):
        jsonData = {"name": domainName, "ttl": ttlValue, "email": email}

        status, content =  self.doRequestDNS('domains', 'POST', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS domain creation attempt', status, content)
        return status, content
        
    def getDomain(self, domainName):
        jsonData = {"name": domainName}
                        
        status, content =  self.doRequestDNS('domains', 'GET', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS get domain attempt', status, content)
        return status, content
        
    def updateDomain(self, idDomain, newTtlValue, newEmail):
        jsonData = {"idDomain": idDomain, "dataDomainUpdate": {"ttl": newTtlValue, "email": newEmail}}
                    
        status, content =  self.doRequestDNS('domains', 'PUSH', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS domain update attempt', status, content)
        return status, content
            
    def deleteDomain(self, idDomain):
        jsonData = {"idDomain": idDomain}
                        
        status, content =  self.doRequestDNS('domains', 'DELETE', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS domain deletion attempt', status, content)
        return status, content
        
    # for an A record : {'name': 'www.domain.com.', 'type': 'A', 'data': '192.168.1.2'}}
    def addRecord(self, idDomain, domainName, domainType, domainData):                
        jsonData = {"idDomain": idDomain, "dataRecord": {"name": domainName, "type": domainType, "data": domainData}}
                        
        status, content =  self.doRequestDNS('records', 'POST', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS record creation attempt', status, content)
        return status, content
        
    def getRecord(self, idDomain, domainName, domainType):
        jsonData = {"idDomain": idDomain, "dataRecord": {"name": domainName, "type": domainType}}
                        
        status, content =  self.doRequestDNS('records', 'POST', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS get record attempt', status, content)
        return status, content
        
    def updateRecord(self, idDomain, idRecord, domainData):        
        jsonData = {"idDomain": idDomain, "idRecord": idRecord, "dataRecord":{"data": domainData}}
                    
        status, content =  self.doRequestDNS('records', 'PUSH', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS record update attempt', status, content)
        return status, content
        
    def deleteRecord(self, idDomain, idRecord):        
        jsonData = {'idDomain': idDomain, 'idRecord': idRecord, 'dataRecord':{}}
                        
        status, content =  self.doRequestDNS('records', 'DELETE', json.dumps(jsonData))
        writeLogFile(self.swComponent,'DNS record deletion attempt', status, content)
        return status, content
        
    def getAuthId(self):
        '''
        Method to perform authentication to the DNSaaS.
        '''
        jsonData = {"user": self.apiUserDNS, "password": self.apiPassDNS, "tenant": self.apiTenantDNS}

        status, content =  self.doRequestDNS('credencials', 'GET', json.dumps(jsonData))
        
        if "access" in content["data"]:
            self.apiToken = content["data"]["access"]["token"]["id"]
        
        writeLogFile(self.swComponent,'DNS Authentication token', status, self.apiToken)        
        return status, content
