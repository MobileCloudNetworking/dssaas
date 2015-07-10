__author__ = 'Santiago Ruiz'
__copyright__ = "Copyright 2014, SoftTelecom"

import urllib
import pycurl
from StringIO import StringIO

class Storage:
    def __init__(self):
        self.contents = ''
        self.line = 0

    def store(self, buf):
        self.line = self.line + 1
        self.contents = "%s%i: %s" % (self.contents, self.line, buf)

    def __str__(self):
        return self.contents

    def get_contents(self):
        return self.contents

class SLAManager:
    def __init__(self):
        self.SLAHost = "134.191.243.7"
        self.SLAPort = "8005"
        #self.SLATarget = "/"
        self.results = {
            "category":"",
            "status":"",
            "id":"",
            "link":"http://134.191.243.7:8006/occi-viz/",
            "terms":[],
            "effective_from":"",
            "effective_until":""
        }

    def perform_sla_acceptance(self, name):

        self.results["category"] = 'dss_' + name

        headers_agreement = StringIO()

        pf = {}
        c = pycurl.Curl()
        c.setopt(c.URL, "http://"+self.SLAHost+":"+self.SLAPort+"/agreement/")
        c.setopt(c.VERBOSE, 1)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, urllib.urlencode(pf))
        c.setopt(c.HEADERFUNCTION, headers_agreement.write)
        c.setopt(pycurl.HTTPHEADER, ['Content-Type: text/occi',
                                          'Category: agreement; scheme="http://schemas.ogf.org/occi/sla#"; class=\"kind\"',
                                          'Category: dss_' + name + '; scheme="http://sla.dss.org/agreements#"; class=\"kind\"',
                                          'Content-Type:text/occi',
                                          'Provider:DSS',
                                          'Provider_pass:dss_pass',
                                          'customer:lola',
                                          'x-occi-attribute: occi.agreement.effectiveFrom=\"2014-11-02T02:20:26Z\"',
                                          'x-occi-attribute: occi.agreement.effectiveUntil=\"2015-11-02T02:20:26Z\"'])
        c.perform()
        c.close()
        print "----"
        print headers_agreement.getvalue()
        print "----"
        location_p = headers_agreement.getvalue().split('\n')[4].split('/')
        sla_location_id = location_p[len(location_p)-1].strip()
        print "PARSED_LOCATION: " + sla_location_id

        self.results["id"] = sla_location_id

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

        headers_accept = Storage()

        c = pycurl.Curl()
        c.setopt(c.URL, "http://"+self.SLAHost+":"+self.SLAPort+"/agreement/"+sla_location_id+"?action=accept")
        c.setopt(c.VERBOSE, 1)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, urllib.urlencode(pf))
        c.setopt(c.WRITEFUNCTION, headers_accept.store)
        c.setopt(pycurl.HTTPHEADER, ['Content-Type: text/occi',
                                          'Category: accept; scheme=\"http://schemas.ogf.org/occi/sla#\"; class=\"kind\"',
                                          'Content-Type:text/occi',
                                          'Provider:DSS',
                                          'Provider_pass:dss_pass',
                                          'customer:lola'])
        c.perform()
        c.close()

        x_occi_attributes = {}
        headers_accept.contents = headers_accept.contents[headers_accept.contents.find("X-OCCI-Attribute:"):]
        for i in range(1, 11):
            before = headers_accept.contents
            headers_accept.contents = headers_accept.contents[headers_accept.contents.find("X-OCCI-Attribute:") + 17:]
            x_occi_attributes[str(i)] = before[before.find("X-OCCI-Attribute:"):before.find("X-OCCI-Attribute:") + headers_accept.contents.find("X-OCCI-Attribute:") + 17]

        return self.parseOcciAttribs(x_occi_attributes)

    def parseOcciAttribs(self, x_occi_attributes):

        sla_term = {
            "type":"SLO-TERM",
            "desc":"",
            "name":"",
            "value":"",
            "limiter_type":""
        }

        for item in x_occi_attributes:
            if "occi.agreement.state=" in x_occi_attributes[item]:
                self.results["status"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip()
            elif "occi.agreement.effectiveFrom=" in x_occi_attributes[item]:
                self.results["effective_from"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip().replace("T"," ").split("+")[0] + " UTC"
            elif "occi.agreement.effectiveUntil=" in x_occi_attributes[item]:
                self.results["effective_until"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip().replace("T"," ").split("+")[0] + " UTC"
            elif "connections_load.term.desc=" in x_occi_attributes[item]:
                sla_term["desc"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip()
            elif "dss_gold.connections_load.DSS number of active player data=" in x_occi_attributes[item]:
                sla_term["value"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip()
            elif "dss_gold.connections_load.DSS number of active player data.limiter_type=" in x_occi_attributes[item]:
                sla_term["limiter_type"] = x_occi_attributes[item].split("=")[1].replace("\"","").strip()
                sla_term["name"] = x_occi_attributes[item].split(".")[2].replace("\"","").strip()

        self.results["terms"].append(sla_term)

        return self.results

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
        elif environ['PATH_INFO'] == '/validated_gold':
            return self.validate("gold")
        elif environ['PATH_INFO'] == '/validated_silver':
            return self.validate("silver")
        elif environ['PATH_INFO'] == '/validated_bronze':
            return self.validate("bronze")

    def validate(self, name):
        if self.environ['REQUEST_METHOD'] == 'GET':
            slam = SLAManager()
            results = slam.perform_sla_acceptance(name)
            response_body = '<!doctype html>' \
                                '<html>' \
                                '<head>' \
                                    '<meta charset="utf-8">' \
                                    '<title>DSS SLA agreement</title>' \
                                    '<link rel="stylesheet" type="text/css" href="http://54.171.14.235/sla_template_files/css/bootstrap.min.css">' \
                                    '<link rel="stylesheet" type="text/css" href="http://54.171.14.235/sla_template_files/css/bootstrap-theme.min.css">' \
                                '</head>' \
                                '<body>' \
                                  '<div style="width: 30%; margin: 5px;">' \
                                      '<h1 style="font-family: Times New Roman, Times, serif;">DSS SLAaaS Agreement</h1>' \
                                      '<p>Please find the information regarding to the accepted agreement below:</p>' \
                                  '</div>' \
                                  '<br />' \
                                  '<table width="30%">' \
                                    '<tr>' \
                                      '<td>' \
                                        '<div class="panel panel-info" style="margin: 5px;">' \
                                            '<div class="panel-heading"><strong>Category: ' + results["category"] + '</strong></div>' \
                                            '<div class="panel-body" >' \
                                                '<br />' \
                                                '<div><strong>Status: ' + results["status"] + '</strong></div>' \
                                                '<br />' \
                                                '<div><strong>ID: ' + results["id"] + '</strong></div>' \
                                                '<br />' \
                                                '<div>Link to SLA violations: <a href="' + results["link"] + '">' + results["link"] + '</a></div>' \
                                                '<br />' \
                                                '<label>Agreement terms</label>' \
                                                '<ul>' \
                                                  '<li>' \
                                                    '<label>TERM1</label>' \
                                                  '</li>' \
                                                  '<ul>' \
                                                    '<li><strong>Type</strong>: ' + results["terms"][0]["type"] + '</li>' \
                                                    '<li><strong>Description</strong>: <span>' + results["terms"][0]["desc"] + '</span></li>' \
                                                    '<li><strong>Name</strong>: ' + results["terms"][0]["name"] + '</li>' \
                                                    '<li><strong>Value</strong>: ' + results["terms"][0]["value"] + '</li>' \
                                                    '<li><strong>Limiter_type</strong>: ' + results["terms"][0]["limiter_type"] + '</li>' \
                                                  '</ul>' \
                                                '</ul>' \
                                                '<label>Agreement dates</label>' \
                                                '<ul>' \
                                                  '<li><strong>Effective From</strong>: ' + results["effective_from"] + '</li>' \
                                                  '<li><strong>Effective Until</strong>: ' + results["effective_until"] + '</li>' \
                                                '</ul>' \
                                            '</div>' \
                                        '</div>' \
                                       '</td>' \
                                    '<tr>' \
                                  '</table>' \
                                '</body>' \
                                '</html>'
            self.start_response('200 OK', [('Content-Type', self.htmltype), ('Content-Length', str(len(response_body)))])
            return [response_body]

    def serve_sla_agreement(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = '<!doctype html>' \
                                '<html>' \
                                    '<head>' \
                                        '<meta charset="utf-8">' \
                                        '<title>DSS SLA agreement</title>' \
                                        '<link rel="stylesheet" type="text/css" href="http://54.171.14.235/sla_template_files/css/bootstrap.min.css">' \
                                        '<link rel="stylesheet" type="text/css" href="http://54.171.14.235/sla_template_files/css/bootstrap-theme.min.css">' \
                                    '</head>' \
                                    '<body>' \
                                        '<div style="width: 70%; margin: 5px;">' \
                                            '<h1 style="font-family: Times New Roman, Times, serif;">SLAaaS Agreement Acceptance for DSSaaS</h1>' \
                                            '<p>Please carefully read the following agreements and click on &quot;Accept&quot; button to sign and validate the desired one.</p>' \
                                        '</div>' \
                                        '<br />' \
                                        '<table width="70%">' \
                                            '<tr>' \
                                                '<td>' \
                                                    '<div class="panel panel-info" style="margin: 5px">' \
                                                          '<div style="text-align: center" class="panel-heading" ><strong>Category: dss_gold</strong></div>' \
                                                          '<div class="panel-body" >' \
                                                              '<br />' \
                                                              '<label>Agreement terms</label>' \
                                                              '<ul>' \
                                                                '<li><label>TERM1</label></li>' \
                                                                '<ul>' \
                                                                  '<li><strong>Type</strong>: SLO-TERM</li>' \
                                                                  '<li><strong>Description</strong>: <span>This is the SLO term for an instance of DSS regarding the connections of the players</span></li>' \
                                                                  '<li><strong>Name</strong>: DSS number of active player data</li>' \
                                                                  '<li><strong>Value</strong>: 100</li>' \
                                                                  '<li><strong>Limiter_type</strong>: max</li>' \
                                                                '</ul>' \
                                                              '</ul>' \
                                                              '<label>Agreement dates</label>' \
                                                              '<ul>' \
                                                                '<li><strong>Effective From</strong>: 2014-11-02 02:20:26 UTC</li>' \
                                                                '<li><strong>Effective Until</strong>: 2015-11-02 02:20:26 UTC</li>' \
                                                              '</ul>' \
                                                          '</div>' \
                                                        '<div style="text-align: center">' \
                                                          '<button type="button" class="btn btn-primary" onClick="location.href=\'validated_gold\'" style="margin: 10px">Accept</button>' \
                                                        '</div>' \
                                                    '</div>' \
                                                '</td>' \
                                                '<td>' \
                                                    '<div class="panel panel-info" style="margin: 5px">' \
                                                          '<div style="text-align: center" class="panel-heading"><strong>Category: dss_silver</strong></div>' \
                                                          '<div class="panel-body" >' \
                                                          '<br />' \
                                                          '<label>Agreement terms</label>' \
                                                          '<ul>' \
                                                            '<li><label>TERM1</label></li>' \
                                                            '<ul>' \
                                                              '<li><strong>Type</strong>: SLO-TERM</li>' \
                                                              '<li><strong>Description</strong>: <span>This is the SLO term for an instance of DSS regarding the connections of the players</span></li>' \
                                                              '<li><strong>Name</strong>: DSS number of active player data</li>' \
                                                              '<li><strong>Value</strong>: 50</li>' \
                                                              '<li><strong>Limiter_type</strong>: max</li>' \
                                                            '</ul>' \
                                                          '</ul>' \
                                                          '<label>Agreement dates</label>' \
                                                          '<ul>' \
                                                            '<li><strong>Effective From</strong>: 2014-11-02 02:20:26 UTC</li>' \
                                                            '<li><strong>Effective Until</strong>: 2015-11-02 02:20:26 UTC</li>' \
                                                          '</ul>' \
                                                          '</div>' \
                                                        '<div style="text-align: center">' \
                                                          '<button type="button" class="btn btn-primary" onClick="location.href=\'validated_silver\'" disabled="disabled" style="margin: 10px">Accept</button>' \
                                                        '</div>' \
                                                    '</div>' \
                                                '</td>' \
                                                '<td>' \
                                                    '<div class="panel panel-info" style="margin: 5px">' \
                                                          '<div style="text-align: center" class="panel-heading"><strong>Category: dss_bronze</strong></div>' \
                                                          '<div class="panel-body" >' \
                                                          '<br />' \
                                                          '<label>Agreement terms</label>' \
                                                          '<ul>' \
                                                            '<li><label>TERM1</label></li>' \
                                                            '<ul>' \
                                                              '<li><strong>Type</strong>: SLO-TERM</li>' \
                                                              '<li><strong>Description</strong>: <span>This is the SLO term for an instance of DSS regarding the connections of the players</span></li>' \
                                                              '<li><strong>Name</strong>: DSS number of active player data</li>' \
                                                              '<li><strong>Value</strong>: 25</li>' \
                                                              '<li><strong>Limiter_type</strong>: max</li>' \
                                                            '</ul>' \
                                                          '</ul>' \
                                                          '<label>Agreement dates</label>' \
                                                          '<ul>' \
                                                            '<li><strong>Effective From</strong>: 2014-11-02 02:20:26 UTC</li>' \
                                                            '<li><strong>Effective Until</strong>: 2015-11-02 02:20:26 UTC</li>' \
                                                          '</ul>' \
                                                          '</div>' \
                                                        '<div style="text-align: center">' \
                                                          '<button type="button" class="btn btn-primary" onClick="location.href=\'validated_bronze\'" disabled="disabled" style="margin: 10px">Accept</button>' \
                                                        '</div>' \
                                                    '</div>' \
                                                '</td>' \
                                            '<tr>' \
                                        '</table>' \
                                    '</body>' \
                                    '</html>'
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
