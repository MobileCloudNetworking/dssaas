'''
Created on 03/04/2014
@author: Onesource
'''
import httplib2 as http
import json

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


class DNSaaSClientCore:
    '''
    Works as a client to the API DNSaaS. This class can be employed by other MCN services, or applications that require services from DNSaaS.
    '''

    apiurlDNSaaS = ''


    def doRequest(self, method, path, body, tokenId):
        '''
        Method to perform requests to the DNSaaS API. Requests can include creation, delete and other operations.
        This method needs to handle requests through a REST API.
        '''
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8',
            'x-auth-token': tokenId
        }
        target = urlparse(self.apiurlDNSaaS + path)

        h = http.Http()

        try:
            '''
            TODO: check error output on delete operations.
            '''
            response, content = h.request(target.geturl(), method, body, headers)

        except:
            return -1, "Server API not reachable"
        response_status = response.get("status")
        content_dict = json.loads(content)

        return response_status, content_dict

    def processReply(self, response):
        '''
        Method to process the reply from the DNSaaS API. The processing can be a simple print or other kind of treatment.
        '''
        print "processReply"


# Global Variables
DNSaaSClient = DNSaaSClientCore()

# #######    METHODS   ##########
def getTokenId(user, password, tenant):
    '''
    Method to authenticate user.
    :param user: Name of the user
    :param password: Password of the user
    '''
    msgJson = {'user': user, 'password': password, 'tenant': tenant}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }

    target = urlparse(DNSaaSClient.apiurlDNSaaS + '/credencials')
    h = http.Http()
    response, content = h.request(target.geturl(), 'GET', json.dumps(msgJson), headers)
    content = json.loads(content)
    content_ = json.loads(content['data'])
    if response['status'] == '200':

        if content['status'] == '200':
            return content_['access']['token']['id']

        else:
            print 'Status: ' + str(content['status']) + '\nMessage: ' + str(content_['data'])
            return ''
    else:
        print 'Status: ' + str(response) + '\nMessage: ' + str(content)
        return ''


def createDomain(domain_name, domain_admin_email, tokenId, **kwargs):
    '''
    Method to create a domain.
    :param name: Name of the domain
    '''
    if 'ttl' in kwargs:
        ttl = kwargs['ttl']
    else:
        ttl = 3600

    domain_name = verify_domain_syntax(domain_name)
    msgJson = {'name': domain_name, 'ttl': ttl, 'email': domain_admin_email}
    status, content = DNSaaSClient.doRequest('POST', '/domains', json.dumps(msgJson), tokenId)

    if content['status'] == '200':

        return 1

    elif content['data']['code'] == 409:
        # print content['data']['type'] # to print error info
        return 0
    else:
        return 0


def getDomain(domain_name, tokenId):
    '''
    Method to create a domain.
    :param name: Name of the domain
    '''
    domain_name = verify_domain_syntax(domain_name)
    msgJson = {'name': domain_name}
    status, content = DNSaaSClient.doRequest('GET', '/domains', json.dumps(msgJson), tokenId)

    if len(content['data']) > 0:
        if content['status'] == '200':
            return content['data']
        else:
            return 0
    else:
        return 0


def updateDomain(domain_name, parameter_to_update, data, tokenId, **kwargs):
    '''
    Method to update a domain.
    :param name: Name of the domain
    '''
    domain_name = verify_domain_syntax(domain_name)

    idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:
        idDomain = idDomain_['id']

        if parameter_to_update in ('ttl', 'email', 'description'):

            if parameter_to_update == 'ttl':
                data = int(data)

            jsonData = {'' + parameter_to_update + '': data}

            msgJson = {'idDomain': idDomain, 'dataDomainUpdate': jsonData}
            status, content = DNSaaSClient.doRequest('PUT', '/domains', json.dumps(msgJson), tokenId)

            if content['status'] == '200':
                return 1
            else:
                return 0
        else:
            return 0
    else:
        return 0


def deleteDomain(domain_name, tokenId):
    '''
    Method to delete a domain.
    :param name: Name of the domain
    '''
    domain_name = verify_domain_syntax(domain_name)

    idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:

        idDomain = idDomain_['id']

        msgJson = {'idDomain': idDomain}
        status, content = DNSaaSClient.doRequest('DELETE', '/domains', json.dumps(msgJson), tokenId)

        if content['status'] == '200':
            return 1
        else:
            return 0
    else:
        return 0


def check_Recursive_zone(record_data):
    record_data_ = record_data.split(".")
    mylist = []
    for line in record_data_:
        mylist.append(line)
    i = len(mylist) - 1

    mylist2 = []
    for line in mylist:
        mylist2.append(mylist[i])
        i = i - 1

    zone = mylist2[1] + '.' + mylist2[2] + '.' + mylist2[3] + '.in-addr.arpa.'

    return zone, (mylist2[0] + '.')


def createRecord(domain_name, record_name, record_type, record_data, tokenId, **kwargs):
    '''
    Method to create a record.
    :param idDomain: Id of the domain
    '''
    if 'codeISO' in kwargs:
        codeISO = kwargs['codeISO']
    else:
        codeISO = []

    if 'geoRecord' in kwargs:
        geoRecord = kwargs['geoRecord']
    else:
        geoRecord = ''

    if record_type == 'PTR':
        zone, data = check_Recursive_zone(record_data)

        if getDomain(zone, tokenId) == 0:
            createDomain(zone, 'admin@example.com', tokenId)

        idDomain_ = getDomain(zone, tokenId)
        domain_name = verify_domain_syntax(domain_name)
        record_data = verify_record_syntax(record_name, domain_name)
        record_name = data + zone

    else:
        domain_name = verify_domain_syntax(domain_name)
        idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:
        idDomain = idDomain_['id']

        if record_type == 'MX':
            if 'priority' in kwargs:
                priority = kwargs['priority']
            else:
                priority = 10
            record_data = verify_record_syntax(record_name, domain_name)
            jsonRecord = {'name': domain_name, 'type': record_type, 'data': record_data, 'priority': int(priority)}

        elif record_type == 'SRV':
            if 'priority' in kwargs:
                priority = kwargs['priority']
            else:
                priority = 30
            domain_name = verify_record_syntax(record_name, domain_name)
            jsonRecord = {'name': domain_name, 'type': record_type, 'data': record_data, 'priority': int(priority)}


        elif record_type == 'NAPTR':
            if 'priority' in kwargs:
                priority = kwargs['priority']
            else:
                priority = 30

            if record_name is not '':
                domain_name = verify_record_syntax(record_name, domain_name)

            jsonRecord = {'name': domain_name, 'type': record_type, 'data': record_data, 'priority': int(priority)}

        elif record_type == 'CNAME':
            record_data = verify_domain_syntax(record_data)
            record_name = verify_record_syntax(record_name, domain_name)
            jsonRecord = {'name': record_name, 'type': record_type, 'data': record_data}

        elif record_type == 'NS':
            record_name = verify_domain_syntax(domain_name)
            record_data = verify_record_syntax(record_data, domain_name)
            jsonRecord = {'name': record_name, 'type': record_type, 'data': record_data}


        else:
            jsonRecord = {'name': record_name, 'type': record_type, 'data': record_data}

        msgJson = {'idDomain': idDomain, 'dataRecord': jsonRecord, 'ISOcodes': codeISO, 'geoRecord': geoRecord}

        status, content = DNSaaSClient.doRequest('POST', '/records', json.dumps(msgJson, sort_keys = False), tokenId)


        if content['status'] == '200':

            return 1
        elif content['status'] == '409':
            print content['data']['type']
            return 0
        else:
            return 0
    else:
        return 0


def getRecord(domain_name, record_name, record_type, tokenId):
    '''
    Method to create a record.
    :param idDomain: Id of the domain
    '''
    domain_name = verify_domain_syntax(domain_name)
    idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:
        idDomain = idDomain_['id']

        if record_type is not 'PTR':
            record_name = verify_record_syntax(record_name, domain_name)

        if record_type == 'MX' or record_type == 'NS' or record_type == 'SPF':

            jsonRecord = {'name': domain_name, 'type': record_type}

        else:
            jsonRecord = {'name': record_name, 'type': record_type}

        msgJson = {'idDomain': idDomain, 'dataRecord': jsonRecord}

        status, content = DNSaaSClient.doRequest('GET', '/records', json.dumps(msgJson), tokenId)

        if status == '200' and len(content['data']) > 0:

            return content['data'][0]
        else:
            return 0

    else:
        return 0


def updateRecord(domain_name, record_name, record_type, parameter_to_update, data, tokenId, **kwargs):
    '''
    Method to create a record.
    :param idDomain: Id of the domain
    '''

    if 'codeISO' in kwargs:
        codeISO = kwargs['codeISO']
    else:
        codeISO = []

    if 'geoRecord' in kwargs:
        geoRecord = kwargs['geoRecord']
    else:
        geoRecord = ''

    domain_name = verify_domain_syntax(domain_name)
    idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:
        idDomain = idDomain_['id']
        idRecord_ = getRecord(domain_name, record_name, record_type, tokenId)

        if idRecord_ is not 0:
            idRecord = idRecord_['id']

            if parameter_to_update == 'priority' or parameter_to_update == 'ttl':

                jsonRecord = {'' + parameter_to_update + '': int(data)}

            elif parameter_to_update == 'data':

                if record_type in ['SSHFP, A', 'CNAME', 'SRV', 'NS']:

                    data = verify_record_syntax(data, domain_name)

                elif record_type == 'PTR':

                    data = verify_domain_syntax(data)

                jsonRecord = {'' + parameter_to_update + '': str(data)}
            else:
                jsonRecord = {'' + parameter_to_update + '': str(data)}

            if len(codeISO) > 0 or len(geoRecord) > 0:
                msgJson = {'idDomain': idDomain, 'idRecord': idRecord, 'dataRecord': jsonRecord, 'ISOcodes': codeISO,
                           'geoRecord': geoRecord}
            else:
                msgJson = {'idDomain': idDomain, 'idRecord': idRecord, 'dataRecord': jsonRecord}

            status, content = DNSaaSClient.doRequest('PUT', '/records', json.dumps(msgJson, sort_keys = False), tokenId)

            if status == '200' and content['status'] == '200':
                return 1
            else:
                return 0

        else:
            return 0
    else:
        return 0


def deleteRecord(domain_name, record_name, record_type, tokenId, **kwargs):
    '''
    Method to create a record.
    :param idDomain: Id of the domain
    '''

    if 'codeISO' in kwargs:
        codeISO = kwargs['codeISO']
    else:
        codeISO = []

    if 'geoRecord' in kwargs:
        geoRecord = kwargs['geoRecord']
    else:
        geoRecord = ''

    domain_name = verify_domain_syntax(domain_name)
    idDomain_ = getDomain(domain_name, tokenId)

    if idDomain_ is not 0:

        idDomain = idDomain_['id']
        jsonRecord = {}

        idRecord_ = getRecord(domain_name, record_name, record_type, tokenId)

        if idRecord_ is not 0:
            idRecord = idRecord_['id']

            if len(codeISO) > 0 or len(geoRecord) > 0:
                msgJson = {'idDomain': idDomain, 'idRecord': idRecord, 'dataRecord': jsonRecord, 'ISOcodes': codeISO,
                           'geoRecord': geoRecord}

            else:
                msgJson = {'idDomain': idDomain, 'idRecord': idRecord, 'dataRecord': jsonRecord}

            status, content = DNSaaSClient.doRequest('DELETE', '/records', json.dumps(msgJson, sort_keys = False),
                                                     tokenId)

            if status == '200':

                return 1
            else:
                return 0

        else:
            return 0
    else:
        return 0


def verify_domain_syntax(domain_name):
    domain_name = str(domain_name)
    if not domain_name.endswith(".", len(domain_name) - 1, len(domain_name)):
        domain_name = domain_name + "."

    return domain_name


def verify_record_syntax(record_name, domain_name):
    domain_name = str(domain_name)
    record_name = record_name + "." + domain_name

    return record_name
