__author__ = 'Santiago Ruiz'
__copyright__ = "Copyright 2014, SoftTelecom"

import json
import sys
from subprocess import call
import httplib
import urllib
import pycurl
from StringIO import StringIO

class dbManager:
    def __init__(self):
        self.user = 'user'
        self.passwd = 'pass'
        self.host = 'localhost'

    def perform_query(self, query):
        call(['mysql', '-h', self.host, '-u', self.user, '-p' + self.passwd, '-e', query])


class fileManager:
    def __init__(self):
        if (len(sys.argv) == 3):
            self.path = sys.argv[1]  # final slash is required!!
        else:
            self.path = ''
        self.contents = '['

    def __del__(self):
        pass

    def set_value(self, item, value):
        self.jsonfile = open(self.path + 'config.json', 'w')
        self.contents += '{"' + item + '":"' + value + '"}'
        self.jsonfile.write(self.contents + ']')
        self.contents += ','
        self.jsonfile.close()


class JSONManager:
    def __init__(self):
        pass

    def read(self, myjson):
        try:
            decoded = json.loads(myjson)
        except (ValueError, KeyError, TypeError):
            return -1
        return decoded

    def jprint(self, myjson):
        try:
            decoded = json.loads(myjson)
            # pretty printing of json-formatted string
            print json.dumps(decoded, sort_keys=True, indent=4)
            # print "JSON parsing example: ", decoded['one']
            # print "Complex JSON parsing example: ", decoded['two']['list'][1]['item']

        except (ValueError, KeyError, TypeError):
            print "JSON format error"


class SLAManager:
    def __init__(self):
        self.SLAHost = "134.191.243.7"
        self.SLAPort = "8005"
        #self.SLATarget = "/"

    def perform_sla_acceptance(self):

       headers = StringIO()

       pf = {}
       c = pycurl.Curl()
       c.setopt(c.URL, "http://"+self.SLAHost+":"+self.SLAPort+"/agreement/")
       c.setopt(c.VERBOSE, 1)
       c.setopt(c.POST, 1)
       c.setopt(c.POSTFIELDS, urllib.urlencode(pf))
       c.setopt(c.HEADERFUNCTION, headers.write)
       c.setopt(pycurl.HTTPHEADER, ['Content-Type: text/occi',
                                          'Category: agreement; scheme="http://schemas.ogf.org/occi/sla#"; class=\"kind\"',
                                          'Category: dss_gold; scheme="http://sla.dss.org/agreements#"; class=\"kind\"',
                                          'Content-Type:text/occi',
                                          'Provider:DSS',
                                          'Provider_pass:dss_pass',
                                          'customer:lola',
                                          'x-occi-attribute: occi.agreement.effectiveFrom=\"2014-11-02T02:20:26Z\"',
                                          'x-occi-attribute: occi.agreement.effectiveUntil=\"2015-11-02T02:20:26Z\"'])
       c.perform()
       c.close()
       print "----"
       print headers.getvalue()
       print "----"
       location_p = headers.getvalue().split('\n')[4].split('/')
       sla_location_id = location_p[len(location_p)-1].strip()
       print "PARSED_LOCATION: " + sla_location_id

       c = pycurl.Curl()
       c.setopt(c.URL, "http://"+self.SLAHost+":"+self.SLAPort+"/agreement_link/")
       c.setopt(c.VERBOSE, 1)
       c.setopt(c.POST, 1)
       c.setopt(c.POSTFIELDS, urllib.urlencode(pf))

       c.setopt(pycurl.HTTPHEADER, ['Content-Type: text/occi',
                                          'Category: agreement_link; scheme=\"http://schemas.ogf.org/occi/sla#\"; class=\"kind\"',
                                          'Content-Type:text/occi',
                                          'Provider:DSS',
                                          'Provider_pass:dss_pass',
                                          'customer:lola',
                                          'x-occi-attribute: occi.core.source=\"'+ "/agreement/" + sla_location_id+'\"',
                                          'x-occi-attribute: occi.core.target=\"DSSMCRHOSTNAME\"'])
       c.perform()
       c.close()

       c = pycurl.Curl()
       c.setopt(c.URL, "http://"+self.SLAHost+":"+self.SLAPort+"/agreement/"+sla_location_id+"?action=accept")
       c.setopt(c.VERBOSE, 1)
       c.setopt(c.POST, 1)
       c.setopt(c.POSTFIELDS, urllib.urlencode(pf))
       c.setopt(pycurl.HTTPHEADER, ['Content-Type: text/occi',
                                          'Category: accept; scheme=\"http://schemas.ogf.org/occi/sla#\"; class=\"kind\"',
                                          'Content-Type:text/occi',
                                          'Provider:DSS',
                                          'Provider_pass:dss_pass',
                                          'customer:lola'])
       c.perform()
       c.close()

       return 0


class Application:
    def __init__(self):
        self.ctype = 'text/plain'
        self.htmltype = 'text/html'
        self.jsontype = 'application/json'

    def __call__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

        if environ['PATH_INFO'] == '/sla':
            return self.serve_sla_agreement()
        elif environ['PATH_INFO'] == '/validated':
            return self.validate()
        else:
            return self.not_found()

    def validate(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = 'OK'
            slam = SLAManager()
            slam.perform_sla_acceptance()
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            return [response_body]

    def serve_sla_agreement(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = '<!doctype html><html><head>        <title>HTML Editor - Full Version</title></head><body><h1>SLAaaS Agreement Acceptance for DSSaaS</h1><p>Please read carefully following agreement and click on &quot;Accept&quot; button to sign and validate.</p><blockquote><p>{template}</p></blockquote><p><input name="Validate" type="button" onClick="location.href=\'validated\'" value="Accept" /><input name="Reject" type="button" value="Reject" /></p></body></html>'
            self.start_response('200 OK', [('Content-Type', self.htmltype), ('Content-Length', str(len(response_body)))])
            return [response_body]
        else:
            return not_found()


# ////////////////ERROR MGMT////////////////////

def not_found(self):
    """Called if no URL matches."""
    self.start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


def unauthorised(self):
    """Called if no URL matches."""
    self.start_response('401 UNAUTHORIZED', [('Content-Type', 'text/plain')])
    return ['Unauthorised']


def servererror(self):
    """Called if no URL matches."""
    self.start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
    return ['Request error']


application = Application()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    httpd = make_server('', 8081, application)
    httpd.serve_forever()
