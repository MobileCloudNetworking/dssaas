__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2014, SoftTelecom"
import json
import logging
import sys
import os
from subprocess import call, Popen, PIPE, STDOUT
import httplib
import socket
import pika
import MySQLdb as mdb
import time

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

    def __init__(self,filepath):
        self.path = filepath
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

class Agent:

    def __init__(self, filepath):
        self.filemg = fileManager(filepath)
        self.SERVER_ERROR_PARSE_JSON = 'Error in parsing input json'
        self.SERVER_ERROR_SET_CONFIG_JSON = 'Error while setting instance json config file'
        self.SERVER_ERROR_DEPLOY_NOT_FINISHED = 'Deployment not finished'
        self.SERVER_ERROR_DB_NOT_READY = 'Database instance is not ready yet'
        self.SERVER_ERROR_DB_NOT_FOUND = 'Database not found'
        self.SERVER_ERROR_CALL_INSTANCE = 'Exception raised while trying to call application'
        self.SERVER_ERROR_CALL_PROVISION_SCRIPT = 'Wrong number of parameters for the script'

    def provision_vm(self, jsondata):
        try:
            jsonm = JSONManager()
            init_json = jsonm.read(jsondata)
            if (init_json == -1):
                return "{'result':'KO'}"
            try:
                if 'mcr' in socket.gethostname():
                    LOG.debug('Running command: ./provision_mcr.sh ' + init_json["mcr_srv_ip"] + ' ' + init_json["dbname"] + ' ' + init_json["dbuser"] + ' ' + init_json["dbaas_srv_ip"] + ' ' + init_json["dbpassword"] + ' ' + init_json["cms_srv_ip"])
                    out_p = Popen(['./provision_mcr.sh',init_json["mcr_srv_ip"],init_json["dbname"],init_json["dbuser"],init_json["dbaas_srv_ip"],init_json["dbpassword"],init_json["cms_srv_ip"]], shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1)
                    for line in out_p.stdout:
                        LOG.debug(line)
                else:
                    LOG.debug('Running command: ./provision_cms.sh ' + init_json["dbname"] + ' ' + init_json["dbuser"] + ' ' + init_json["dbaas_srv_ip"] + ' ' + init_json["dbpassword"] + ' ' + init_json["mcr_srv_ip"])
                    out_p = Popen(['./provision_cms.sh',init_json["dbname"],init_json["dbuser"],init_json["dbaas_srv_ip"],init_json["dbpassword"],init_json["mcr_srv_ip"]], shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1)
                    for line in out_p.stdout:
                        LOG.debug(line)
                return "{'result':'OK'}"
            except:
                return "{'result':'KO'}"
        except:
            return "{'result':'KO'}"

    def check_db_status(self, jsondata):
        try:
            jsonm = JSONManager()
            db_json = jsonm.read(jsondata)
            if (db_json == -1):
                return "{'result':'KO'}"
            try:
                db = mdb.connect(db_json["dbhost"], db_json["dbuser"], db_json["dbpassword"], db_json["dbname"])
                return "{'result':'OK'}"
            except:
                return "{'result':'KO'}"
        except:
            return "{'result':'KO'}"

    def mon(self, jsondata):
        try:
            jsonm = JSONManager()
            mon_json = jsonm.read(jsondata)
            if (mon_json == -1):
                return "{'result':'KO'}"
            try:

                if 'cms' in socket.gethostname():
                    try:
                        self.filemg.set_value('monendpoint', mon_json["monendpoint"])
                    except (ValueError, KeyError, TypeError):
                        return "{'result':'KO'}"
                    #configure and reboot zabbix
                    call(['sed', '-i.bak', 's/Server=.*$/Server=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                    call(['sed', '-i.bak', 's/ServerActive=.*$/ServerActive=' + mon_json["monendpoint"] + '/g', '/etc/zabbix/zabbix_agentd.conf'])
                    call(['sed', '-i.bak', 's/# UnsafeUserParameters=0/UnsafeUserParameters=1/g', '/etc/zabbix/zabbix_agentd.conf'])
                    call(['sed', '-i.bak', 's"# UserParameter="UserParameter=DSS.Player.Reqcount,python /home/ubuntu/getrequests.py"g', '/etc/zabbix/zabbix_agentd.conf'])

                #if you are in mcr, add custom item for rcb
                if 'mcr' in socket.gethostname():
                    try:
                        conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                        conn.request("HEAD","/DSSMCRAPI/")
                        res = conn.getresponse()
                        conn.close()
                        if res.status >= 200 and res.status < 400:
                            #create query
                            try:
                                self.filemg.set_value('monendpoint', mon_json["monendpoint"])
                            except (ValueError, KeyError, TypeError):
                                return "{'result':'KO'}"

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
                            call(['sed', '-i.bak', 's"# UserParameter="# UserParameter=\\nUserParameter=DSS.Players.CNT,python /home/ubuntu/getactiveplayers.py ' + dbhost + ' ' + dbuser + ' ' + dbpassword + ' ' + dbname + '"g', '/etc/zabbix/zabbix_agentd.conf'])
                            call(['sed', '-i.bak', 's"# UserParameter="# UserParameter=\\nUserParameter=DSS.Tracker.STATUS,python /home/ubuntu/checkTrackerService.py"g', '/etc/zabbix/zabbix_agentd.conf'])
                            call(['sed', '-i.bak', 's"# UserParameter="# UserParameter=\\nUserParameter=DSS.Streaming.STATUS,python /home/ubuntu/checkStreamingService.py"g', '/etc/zabbix/zabbix_agentd.conf'])
                            call(['sed', '-i.bak', 's"# UserParameter="# UserParameter=\\nUserParameter=DSS.Filesync.STATUS,python /home/ubuntu/checkFilesyncService.py"g', '/etc/zabbix/zabbix_agentd.conf'])
                            call(['sed', '-i.bak', 's"# UserParameter="UserParameter=DSS.Player.Reqcount,python /home/ubuntu/getrequests.py"g', '/etc/zabbix/zabbix_agentd.conf'])
                    except:
                        return  "{'result':'KO'}"

                os.system('service zabbix-agent restart')
                return "{'result':'OK'}"
            except:
                return "{'result':'KO'}"
        except:
            return "{'result':'KO'}"

    def dns(self, jsondata):
        try:
            jsonm = JSONManager()
            dns_json = jsonm.read(jsondata)
            if dns_json == -1:
                return "{'result':'KO'}"
            try:

                try:
                    self.filemg.set_value('dnsendpoint', dns_json["dnsendpoint"])
                    self.filemg.set_value('dssdomainname', dns_json["dssdomainname"])
                except (ValueError, KeyError, TypeError):
                    return self.servererror(self.SERVER_ERROR_SET_CONFIG_JSON)

                try:
                    resolve_conf = open('/etc/resolvconf/resolv.conf.d/head', 'a+')
                    #resolve_conf = open('/etc/resolvconf/resolv.conf.d/base', 'w')
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

                return "{'result':'OK'}"
            except:
                return "{'result':'KO'}"
        except:
            return "{'result':'KO'}"

    def configure_rcb_batch(self,jsondata):

        try:
            jsonm = JSONManager()
            mon_json = jsonm.read(jsondata)
            if (mon_json == -1):
                return "{'result':'KO'}"
            try:
                ####CORE
                ready = 'False'
                conn = httplib.HTTPConnection("localhost", 8080, timeout=10)
                conn.request("HEAD","/DSSMCRAPI/")
                res = conn.getresponse()
                conn.close()
                if res.status >= 200 and res.status < 400:
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
                    if res.status >= 200 and res.status < 400:
                        ready = 'True'
                    else:
                        return "{'result':'KO'}"#self.servererror(self.SERVER_ERROR_DEPLOY_NOT_FINISHED)
                ####
                return "{'result':'OK'}"
            except:
                return "{'result':'KO'}"
        except:
            return "{'result':'KO'}"


class MQManager():

    def __init__(self, filepath = ".", epMQ = 'localhost' ,userMQ = 'adminRabbit', passMQ = 'mcnPassword77', portMQ = 8384):
        self.agent = Agent(filepath)
        self.credentials = pika.PlainCredentials(userMQ, passMQ)
        connected = False
        try_count = 0
        max_retry = 300
        while not connected:
            try:
                self.connection = pika.BlockingConnection( pika.ConnectionParameters(host=epMQ, port=portMQ, credentials=self.credentials))
                connected = True
            except Exception as e:
                try_count += 1
                LOG.debug(str(e))
            if try_count > max_retry:
                LOG.debug("Agent failed to connect to MQ broker")
                return
            time.sleep(1)
        LOG.debug("Successfully connected to MQ broker")
        self.exchange_name = 'so-messages'
        self.so_queue_name = 'so_queue'
        self.so_queue_routing_key = 'ack_so'
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, type='direct')
        self.channel.queue_declare(queue=self.so_queue_name, durable=True)
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.so_queue_name, routing_key=self.so_queue_routing_key)
        self.queue_name = socket.gethostname()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_bind(exchange=self.exchange_name,queue=self.queue_name, routing_key=socket.gethostname())
        self.channel.basic_consume(self.callback, queue=self.queue_name, no_ack=True)
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        #actions{DB,MON,DNS,RCB,Provision}
        LOG.debug("Message received")
        LOG.debug("Message body: " + str(body))
        res = "{'result':'KO'}"
        timeout = 240
        jsonm = JSONManager()
        data_json = jsonm.read(body)
        while res != "{'result':'OK'}" or timeout <= 0:
            if data_json["action"] == "DB":
                LOG.debug("Configuring DB")
                res = self.agent.check_db_status(body)
            elif data_json["action"] == "MON":
                LOG.debug("Configuring MON")
                res = self.agent.mon(body)
            elif data_json["action"] == "DNS":
                LOG.debug("Configuring DNS")
                res = self.agent.dns(body)
            elif data_json["action"] == "RCB":
                LOG.debug("Configuring RCB")
                res = self.agent.configure_rcb_batch(body)
            elif data_json["action"] == "provision":
                LOG.debug("Provisioning")
                res = self.agent.provision_vm(body)
            timeout -= 1
            time.sleep(1)

        res = res.replace('}', ', \'host\':\'' + socket.gethostname() + '\'}')
        while self.publish(res) == 0:
            time.sleep(5)
        #print(" [x] %r" % body)

    def publish(self, message):
        try:
            self.channel.basic_publish(exchange=self.exchange_name,
                          body=message,
                          routing_key=self.so_queue_routing_key,
                          properties=pika.BasicProperties(
                             delivery_mode = 2, # 2 makes message persistent
                          ))
            LOG.debug("Answer " + str(message) + " sent succ6fully")
            return 1
        except Exception as e:
            LOG.debug("Error publishing answer to the SO " + str(e))
            return 0

    def stop(self):
        self.channel.stop_consuming()


if __name__ == '__main__':
    #arg[1] = path_to_config.json
    #arg[2] = epMQ
    if len(sys.argv) < 3:
        LOG.debug("Error in argv")
    else:
        mqm = MQManager(filepath=sys.argv[1],epMQ=sys.argv[2])

