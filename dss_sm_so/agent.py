import json
import random
import string
import sys
from subprocess import call
import httplib


class fileManager:
        
    def __init__(self):
        if (len(sys.argv)==3):
            self.path = sys.argv[1] #final slash is required!!
        else:
            self.path =''
        self.contents = '['
        
    def __del__(self):
        pass
        
    def set_value(self,item,value):
        self.jsonfile = open(self.path+'config.json', 'w')
        self.contents += '{"'+item+'":"'+value+'"}'
        self.jsonfile.write(self.contents + ']')
        self.contents += ','
        self.jsonfile.close()


class JSONManager:
    def __init__(self):
        pass
    
    def read(self,myjson):
        try:
            decoded = json.loads(myjson)
        except (ValueError, KeyError, TypeError):
            return -1
        return decoded
            
    def jprint(self,myjson):
        try:
            decoded = json.loads(myjson)
            # pretty printing of json-formatted string
            print json.dumps(decoded, sort_keys=True, indent=4)
            #print "JSON parsing example: ", decoded['one']
            #print "Complex JSON parsing example: ", decoded['two']['list'][1]['item']
         
        except (ValueError, KeyError, TypeError):
            print "JSON format error"


class Application:
    
    def __init__(self):
        self.ctype = 'text/plain'
        self.jsontype = 'application/json'
        self.allowedtoken = 'NONE'
        self.alloweduser = 'NONE'
        self.filemg = fileManager()
        
        if (len(sys.argv)==3):
            self.cdn_enabled = str(sys.argv[2]) #values are : true , false
        else:
            self.cdn_enabled = 'true'
            
        if self.cdn_enabled is 'false':
            self.configurationstatus = {"cdn":"False","mon":"False","zab":"False"}
        else:
            self.configurationstatus = {"cdn":"True","mon":"False","zab":"False"}
    def __call__(self, environ, start_response):
        self.environ=environ
        self.start_response=start_response
        
        if environ['PATH_INFO'] == '/v1.0/test':
            return self.test()
        elif environ['PATH_INFO'] == '/v1.0/CDN':
            return self.cdn()
        elif environ['PATH_INFO'] == '/v1.0/MON':
            return self.mon()
        elif environ['PATH_INFO'] == '/v1.0/auth':
            return self.auth()
        elif environ['PATH_INFO'] == '/v1.0/ZABBIX':
            return self.configure_zabbix()
        elif environ['PATH_INFO'] == '/v1.0/deploystat':
            return self.deployment_status()
        elif environ['PATH_INFO'] == '/v1.0/configstat':
            return self.configuration_status()
        else:
            return self.not_found()

    def deployment_status(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
            conn.request("HEAD","/WebAppDSS/")
            res = conn.getresponse()
            print res.status, res.reason
            if res.status == 200:
                conn.close()
                response_body = 'Deployment finished'
                self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
                return [response_body]
            else:
                conn.close()
                conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                conn.request("HEAD","/DSSMCRAPI/")
                res = conn.getresponse()
                print res.status, res.reason
                conn.close()
                if res.status == 200:
                    response_body = 'Deployment finished'
                    self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
                    return [response_body]
                else:
                    return self.not_found()
        else:
            return self.not_found()
        
    def configuration_status(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = json.dumps(self.configurationstatus)
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            return [response_body]
        else:
            return self.not_found()
        
    def test(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = 'OK'
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            return [response_body]
     
    def cdn(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            cdn_json = jsonm.read(body)
            if (cdn_json == -1):
                return self.servererror()
            #check auth
            if not (cdn_json["user"]==self.alloweduser and cdn_json["token"]==self.allowedtoken):
                return self.unauthorised()
            
            try:
                self.filemg.set_value('cdnpassword', cdn_json["cdnpassword"])
                self.filemg.set_value('cdnglobalid', cdn_json["cdnglobalid"])
                self.filemg.set_value('cdnendpoint', cdn_json["cdnendpoint"])
                self.filemg.set_value('cdnfirstpop', cdn_json["cdnfirstpop"])
            except (ValueError, KeyError, TypeError):
                return self.servererror()
           
            #everything went fine
            response_body = 'OK'
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["cdn"] = "True"
            return [response_body]
        else:
            return self.not_found()
        
    def mon(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            mon_json = jsonm.read(body)
            if (mon_json == -1):
                return self.servererror()
            if not (mon_json["user"]==self.alloweduser and mon_json["token"]==self.allowedtoken):
                return self.unauthorised()
            #create query
            try:
                self.filemg.set_value('monendpoint', mon_json["monendpoint"])
            except (ValueError, KeyError, TypeError):
                return self.servererror()
            
            #everything went fine
            response_body = 'OK'
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["mon"] = "True"
            return [response_body]
        else:
            return self.not_found()
        
    
    def configure_zabbix(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            mon_json = jsonm.read(body)
            if (mon_json == -1):
                return self.servererror()
            if not (mon_json["user"]==self.alloweduser and mon_json["token"]==self.allowedtoken):
                return self.unauthorised()
            #configure and reboot zabbix            
            call(['sed', '-i.bak', 's/127.0.0.1/' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
            call(['service', 'zabbix-agent', 'restart'])
            #everything went fine
            response_body = 'OK'
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["zab"] = "True"
            return [response_body]
        else:
            return self.not_found()
        

    def auth(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            auth_json = jsonm.read(body)
            if (auth_json == -1):
                return self.servererror()
            #check user/pass
            if (auth_json["user"]=="SO" and auth_json["password"]=="SO"):
                token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                self.alloweduser = auth_json["user"]
                self.allowedtoken = token
                response_body = '{"user":"SO","token":"' + token + '"}'
                self.start_response('200 OK', [('Content-Type', 'text/json'), ('Content-Length', str(len(response_body)))])
                return [response_body]
            else:
                return self.unauthorised()
            #everything went fine
        else:
            return self.not_found()



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
    httpd = make_server('', 8051, application)
    httpd.serve_forever()