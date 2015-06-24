__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2014, SoftTelecom"
import json
import logging
import random
import string
import sys
import os
from subprocess import call, Popen, PIPE, STDOUT
import httplib
import socket

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('agent_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

class fileManager:
        
    def __init__(self):
        if (len(sys.argv)==4):
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
            #print "JSON parsing example: ", decoded['one'] print "Complex JSON parsing example: ", decoded['two']['list'][1]['item']
         
        except (ValueError, KeyError, TypeError):
            print "JSON format error"

class Application:
    
    def __init__(self):
        self.ctype = 'text/plain'
        self.jsontype = 'application/json'
        self.allowedtoken = 'NONE'
        self.alloweduser = 'NONE'
        self.filemg = fileManager()
        self.SERVER_ERROR_PARSE_JSON = 'Error in parsing input json'
        self.SERVER_ERROR_SET_CONFIG_JSON = 'Error while setting instance json config file'
        self.SERVER_ERROR_DEPLOY_NOT_FINISHED = 'Deployment not finished'
        self.SERVER_ERROR_DB_NOT_READY = 'Database instance is not ready yet'
        self.SERVER_ERROR_DB_NOT_FOUND = 'Database not found'
        self.SERVER_ERROR_CALL_INSTANCE = 'Exception raised while trying to call application'
        self.SERVER_ERROR_CALL_PROVISION_SCRIPT = 'Wrong number of parameters for the script'

        self.icn_port = '9695'

        if (len(sys.argv)==4):
            self.cdn_enabled = str(sys.argv[2]) #values are : true , false
            self.icn_enabled = str(sys.argv[3]) #values are : true , false
        else:
            self.cdn_enabled = 'true'
            self.icn_enabled = 'false'

        if self.cdn_enabled == 'true' and self.icn_enabled == 'false':
            self.configurationstatus = {"cdn":"False", "provision":"False", "mon":"False", "rcb":"False", "dns":"False", "aaa":"True", "icn":"True"}
        else:
            self.configurationstatus = {"cdn":"True", "provision":"False", "mon":"False", "rcb":"False", "dns":"False", "aaa":"True", "icn":"False"}
            
    def __call__(self, environ, start_response):
        self.environ=environ
        self.start_response=start_response
        
        if environ['PATH_INFO'] == '/v1.0/test':
            return self.test()
        elif environ['PATH_INFO'] == '/v1.0/provision':
            return self.provision_vm()
        elif environ['PATH_INFO'] == '/v1.0/hostname':
            return self.get_hostname()
        elif environ['PATH_INFO'] == '/v1.0/CDN':
            return self.cdn()
        elif environ['PATH_INFO'] == '/v1.0/ICN':
            return self.icn()
        elif environ['PATH_INFO'] == '/v1.0/MON':
            return self.mon()
        elif environ['PATH_INFO'] == '/v1.0/DNS':
            return self.dns()
        elif environ['PATH_INFO'] == '/v1.0/auth':
            return self.auth()
        elif environ['PATH_INFO'] == '/v1.0/deploystat':
            return self.deployment_status()
        elif environ['PATH_INFO'] == '/v1.0/configstat':
            return self.configuration_status()
        elif environ['PATH_INFO'] == '/v1.0/RCB':
            return self.configure_rcb_batch()
        else:
            return self.not_found()
        
    def get_hostname(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = str(socket.gethostname())
            self.start_response('200 OK', [('Content-Type', self.ctype), ('Content-Length', str(len(response_body)))])
            return [response_body]
        else:
            return self.not_found()
        
    def deployment_status(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            try:
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
                        response_body = json.dumps({"Message":"Deployment Finished"})
                        self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
                        return [response_body]
                    else:
                        return self.servererror(self.SERVER_ERROR_DEPLOY_NOT_FINISHED)
            except:
                    return self.servererror(self.SERVER_ERROR_CALL_INSTANCE)
        else:
            return self.not_found()
    
    def provision_vm(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            init_json = jsonm.read(body)
            if (init_json == -1):
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            #check auth
            if not (init_json["user"]==self.alloweduser and init_json["token"]==self.allowedtoken):
                return self.unauthorised()
            try:
                if 'mcr' in socket.gethostname():
                    out_p = Popen(['./provision_mcr.sh',init_json["mcr_srv_ip"],init_json["dbname"],init_json["dbuser"],init_json["dbaas_srv_ip"],init_json["dbpassword"],init_json["cms_srv_ip"],self.cdn_enabled,self.icn_enabled,self.icn_port], shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1)
                    for line in out_p.stdout:
                        LOG.debug(line)
                else:
                    out_p = Popen(['./provision_cms.sh',init_json["dbname"],init_json["dbuser"],init_json["dbaas_srv_ip"],init_json["dbpassword"],init_json["mcr_srv_ip"],self.cdn_enabled,"http://aaa-profile.mcn.local:8080/IdentityProviderService/WsService?wsdl",self.icn_enabled], shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1)
                    for line in out_p.stdout:
                        LOG.debug(line)
                response_body = json.dumps({"Message":"Provision Finished"})
                self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
                LOG.debug(str([response_body]))
                self.configurationstatus["provision"] = "True"
                return [response_body]
            except:
                return self.servererror(self.SERVER_ERROR_CALL_PROVISION_SCRIPT)
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
        else:
            return self.not_found()
     
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
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            #check auth
            if not (cdn_json["user"]==self.alloweduser and cdn_json["token"]==self.allowedtoken):
                return self.unauthorised()
            
            try:
                self.filemg.set_value('cdnpassword', cdn_json["cdnpassword"])
                self.filemg.set_value('cdnglobalid', cdn_json["cdnglobalid"])
                self.filemg.set_value('cdnendpoint', cdn_json["cdnendpoint"])
                self.filemg.set_value('cdnfirstpop', cdn_json["cdnfirstpop"])
            except (ValueError, KeyError, TypeError):
                return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)
           
            #everything went fine
            response_body = json.dumps({"Message":"CDN config Finished"})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["cdn"] = "True"
            return [response_body]
        else:
            return self.not_found()

    def icn(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            icn_json = jsonm.read(body)
            if (icn_json == -1):
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            #check auth
            if not (icn_json["user"]==self.alloweduser and icn_json["token"]==self.allowedtoken):
                return self.unauthorised()

            try:
                self.filemg.set_value('icnendpoint', icn_json["icnendpoint"])
            except (ValueError, KeyError, TypeError):
                return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)

            #everything went fine
            response_body = json.dumps({"Message":"ICN config Finished"})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            if 'mcr' in socket.gethostname() and self.icn_enabled == 'true':
                ret_code = os.system('python icn_putcontents.py ' + icn_json["icnendpoint"] + ' &')
                LOG.debug("icn python run script returned : " + str(ret_code))
            else:
                LOG.debug("Not an MCR host or ICN service not enabled")
            self.configurationstatus["icn"] = "True"
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
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            if not (mon_json["user"]==self.alloweduser and mon_json["token"]==self.allowedtoken):
                return self.unauthorised()
            
            if 'cms' in socket.gethostname():
                try:
                    self.filemg.set_value('monendpoint', mon_json["monendpoint"])
                except (ValueError, KeyError, TypeError):
                    return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)    
                #configure and reboot zabbix
                call(['sed', '-i.bak', 's/Server=.*$/Server=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                call(['sed', '-i.bak', 's/ServerActive=.*$/ServerActive=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                        
            #if you are in mcr, add custom item for rcb
            if 'mcr' in socket.gethostname():
                try:
                    conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                    conn.request("HEAD","/DSSMCRAPI/")
                    res = conn.getresponse()
                    conn.close()
                    if res.status == 200:
                        #create query
                        try:
                            self.filemg.set_value('monendpoint', mon_json["monendpoint"])
                        except (ValueError, KeyError, TypeError):
                            return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)
                        
                        #configure and reboot zabbix
                        call(['sed', '-i.bak', 's/Server=.*$/Server=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                        call(['sed', '-i.bak', 's/ServerActive=.*$/ServerActive=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                        
                        dbuser = mon_json["dbuser"]
                        dbpassword = mon_json["dbpassword"]
                        dbhost = ''
                        with open ("/home/ubuntu/dbhost", "r") as dbhostfile:
                            dbhost+=dbhostfile.read().replace('\n', '')
                        dbname = mon_json["dbname"]
                        call(['sed', '-i.bak', 's/# UnsafeUserParameters=0/UnsafeUserParameters=1/g', '/etc/zabbix/zabbix_agentd.conf'])
                        call(['sed', '-i.bak', 's"# UserParameter="# UserParameter=\\nUserParameter=DSS.RCB.CDRString,python /home/ubuntu/getcdr.py ' + dbhost + ' ' + dbuser + ' ' + dbpassword + ' ' + dbname + '"g', '/etc/zabbix/zabbix_agentd.conf'])
                        call(['sed', '-i.bak', 's"# UserParameter="UserParameter=DSS.Players.CNT,python /home/ubuntu/getactiveplayers.py ' + dbhost + ' ' + dbuser + ' ' + dbpassword + ' ' + dbname + '"g', '/etc/zabbix/zabbix_agentd.conf'])
                    else:
                        return self.servererror(self.SERVER_ERROR_DEPLOY_NOT_FINISHED)
                except:
                    return self.servererror(self.SERVER_ERROR_CALL_INSTANCE)
            call(['service', 'zabbix-agent', 'restart'])
            
            #everything went fine
            response_body = json.dumps({"Message":"MON config Finished"})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["mon"] = "True"
            return [response_body]
        else:
            return self.not_found()
    
    def dns(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #get JSON from PAYLOAD
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            dns_json = jsonm.read(body)
            if (dns_json == -1):
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            if not (dns_json["user"]==self.alloweduser and dns_json["token"]==self.allowedtoken):
                return self.unauthorised()
            #create query
            try:
                self.filemg.set_value('dnsendpoint', dns_json["dnsendpoint"])
                self.filemg.set_value('dssdomainname', dns_json["dssdomainname"])
            except (ValueError, KeyError, TypeError):
                return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)

            try:
                resolve_conf = open('/etc/resolvconf/resolv.conf.d/base', 'w')
                resolve_conf.write('nameserver ' + dns_json["dnsendpoint"])
                resolve_conf.write("\n")
                resolve_conf.close()
            except IOError as e:
                LOG.debug("I/O error({0}): {1}".format(e.errno, e.strerror))
            except:
                LOG.debug("Unknown error while reading resolv.conf file")

            ret_code = os.system('resolvconf -u')
            LOG.debug("resolvconf command returned : " + str(ret_code))
            #everything went fine
            response_body = json.dumps({"Message":"DNS config Finished"})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["dns"] = "True"
            return [response_body]
        else:
            return self.not_found()
            
    def configure_rcb_batch(self):
        if self.environ['REQUEST_METHOD'] == 'POST':
            #check for auth
            from cStringIO import StringIO
            length = self.environ.get('CONTENT_LENGTH', '0')
            length = 0 if length == '' else int(length)
            body = self.environ['wsgi.input'].read(length)
            jsonm = JSONManager()
            jsonm.jprint(body)
            mon_json = jsonm.read(body)
            if (mon_json == -1):
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
            if not (mon_json["user"]==self.alloweduser and mon_json["token"]==self.allowedtoken):
                return self.unauthorised()
            # check if service is ready (and therefore database configured)
            try:
                ready = 'False'
                conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                conn.request("HEAD","/DSSMCRAPI/")
                res = conn.getresponse()
                conn.close()
                if res.status == 200:
                    dbuser = mon_json["dbuser"]
                    dbpassword = mon_json["dbpassword"]
                    dbhost = ''
                    with open ("/home/ubuntu/dbhost", "r") as dbhostfile:
                        dbhost+=dbhostfile.read().replace('\n', '')
                    dbname = mon_json["dbname"]
                    ready = 'True'
                    #filling query
                    sqlquery = ''
                    sqlquery += 'USE `' + dbname + '`;' + '\n'
                    sqlquery += 'DELIMITER ;;' + '\n'
                    sqlquery += 'CREATE DEFINER=`' + dbuser + '`@`%` PROCEDURE `poll_time`()' + '\n'
                    sqlquery += 'BEGIN' + '\n'
                    sqlquery += 'DECLARE done INT DEFAULT 0; ' + '\n'
                    sqlquery += 'DECLARE last_req,last_act datetime; ' + '\n'
                    sqlquery += 'DECLARE identificador,user bigint; ' + '\n'
                    sqlquery += 'DECLARE activo int;' + '\n'
                    sqlquery += 'DECLARE cur1 CURSOR FOR SELECT id,last_request,last_activation,user_id,active FROM player;' + '\n'
                    sqlquery += 'DECLARE CONTINUE HANDLER FOR SQLSTATE \'02000\' SET done = 1;' + '\n'
                    sqlquery += '\n'
                    sqlquery += ' OPEN cur1;' + '\n'
                    sqlquery += '\n'
                    sqlquery += ' REPEAT' + '\n'
                    sqlquery += ' FETCH cur1 INTO identificador,last_req, last_act,user,activo;' + '\n'
                    sqlquery += ' IF NOT done THEN' + '\n'
                    sqlquery += ' IF (((TO_DAYS(last_req)) - (TO_DAYS(last_act))) >= 1) THEN' + '\n'
                    sqlquery += ' UPDATE player SET player.last_activation=last_request WHERE player.id=identificador;' + '\n'
                    sqlquery += ' INSERT INTO `cdregister` (`version`,`end_hour`,`player_id`,`start_hour`,`user_id`)' + '\n'
                    sqlquery += ' VALUES(0,last_req,identificador,last_act,user);' + '\n'
                    sqlquery += ' ELSE # Generar un CDR si han pasado mas de 5 min desde la solicitud de un player' + '\n'
                    sqlquery += ' IF ((activo = 1) AND (SELECT TIME_TO_SEC(TIMEDIFF((select now()), last_req)) > 60*5)) THEN' + '\n'
                    sqlquery += ' UPDATE player SET player.active=0 WHERE player.id=identificador;' + '\n'
                    sqlquery += ' INSERT INTO `cdregister` (`version`,`end_hour`,`player_id`,`start_hour`,`user_id`)' + '\n'
                    sqlquery += ' VALUES(0,last_req,identificador,last_act,user);' + '\n'
                    sqlquery += ' END IF;' + '\n'
                    sqlquery += ' END IF;' + '\n'
                    sqlquery += ' END IF;' + '\n'
                    sqlquery += ' UNTIL done END REPEAT;' + '\n'
                    sqlquery += '\n'
                    sqlquery += ' CLOSE cur1;' + '\n'
                    sqlquery += 'END ;;' + '\n'
                    sqlquery += 'DELIMITER ;' + '\n'
                    sqlquery += '\n'
                    sqlquery += 'CREATE EVENT check_player' + '\n'
                    sqlquery += 'ON SCHEDULE EVERY 1 MINUTE' + '\n'
                    sqlquery += 'DO' + '\n'
                    sqlquery += 'call poll_time();' + '\n'
                    sqlquery += '\n'
                    sqlquery += 'SET GLOBAL event_scheduler = ON;' + '\n'
                    call(['mysql','-h', dbhost, '-u', dbuser, '-p'+dbpassword, '-e', sqlquery])
    
                else:
                    conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                    conn.request("HEAD","/WebAppDSS/")
                    res = conn.getresponse()
                    conn.close()
                    if res.status == 200:
                        ready = 'True'
                    else:
                        return self.servererror(self.SERVER_ERROR_DEPLOY_NOT_FINISHED)
            except:
                return self.servererror(self.SERVER_ERROR_CALL_INSTANCE)
            
            #everything went fine
            response_body = json.dumps({"Message":"RCB config Finished"})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            self.configurationstatus["rcb"] = "True"
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
                return self.servererror(self.SERVER_ERROR_PARSE_JSON)
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
    
    def servererror(self, err_description = None):
        """Called if no URL matches."""
        self.start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
        if err_description is None:
            err_description = 'Request error'
        return [err_description]
    
application = Application() 
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8051, application)
    httpd.serve_forever()
