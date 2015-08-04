__author__ = "Mohammadjavad valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
import json
import logging
from Queue import Queue
import random
import string
import datetime

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('presentation_api_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

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

class Message(object):
    def __init__(self, from_whom, to_whom, task, date_time):
        self.from_whom = from_whom
        self.to_whom = to_whom
        self.task = task
        self.date_time = date_time

    def get_msg(self):
        return self.to_whom + "_from_" + self.from_whom

    def get_json(self):
        return json.dumps({"from": self.from_whom, "to": self.to_whom, "task": self.task, "date_time": str(self.date_time)})

    def get_from(self):
        return self.from_whom

    def get_to(self):
        return self.to_whom

    def get_task(self):
        return self.task

    def get_date_time(self):
        return self.date_time

    def set_from(self, value):
        self.from_whom = value

    def set_to(self, value):
        self.to_whom = value

    def set_task(self, value):
        self.task = value

    def set_date_time(self, value):
        self.date_time = str(value)

class Application:

    def __init__(self):
        self.ctype = 'text/plain'
        self.jsontype = 'application/json'
        self.allowedtoken = 'NONE'
        self.alloweduser = 'NONE'
        self.SERVER_ERROR_PARSE_JSON = 'Error in parsing input json'
        self.SERVER_ERROR_SET_CONFIG_JSON = 'Error while setting instance json config file'
        self.SERVER_ERROR_DEPLOY_NOT_FINISHED = 'Deployment not finished'
        self.SERVER_ERROR_DB_NOT_READY = 'Database instance is not ready yet'
        self.SERVER_ERROR_DB_NOT_FOUND = 'Database not found'
        self.SERVER_ERROR_CALL_INSTANCE = 'Exception raised while trying to call application'
        self.SERVER_ERROR_CALL_PROVISION_SCRIPT = 'Wrong number of parameters for the script'

        self.message_queue = Queue()

        self.component_status = {
                                    "slaaas":"None",
                                    "aaaaas":"None",
                                    "dnsaas":"None",
                                    "monaas":"None",
                                    "icnaas":"None",
                                    "cms1":"None",
                                    "cms2":"None",
                                    "cms3":"None",
                                    "mcr":"None",
                                    "db":"None",
                                    "lbaas":"None",
                                    "so":"None"
        }

    def __call__(self, environ, start_response):
        self.environ=environ
        self.start_response=start_response

        if environ['PATH_INFO'] == '/v1.0/test':
            return self.test()
        elif environ['PATH_INFO'] == '/v1.0/service_ready':
            return self.service_ready()
        elif environ['PATH_INFO'] == '/v1.0/message':
            return self.message_mgnt()
        elif environ['PATH_INFO'] == '/v1.0/auth':
            return self.auth()
        else:
            return self.not_found()

    def service_ready(self):
        if self.environ['REQUEST_METHOD'] == 'GET':
            response_body = json.dumps(self.component_status)
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            return [response_body]

        elif self.environ['REQUEST_METHOD'] == 'PUT':
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
            #check user/pass

            for item in init_json["components"]:
                self.component_status[item["name"]] = "deployed"

            LOG.debug("Status of specified components changed to ready.")
            response_body = json.dumps({"Message":"Status of specified components changed to ready."})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            LOG.debug(str([response_body]))
            return [response_body]

        elif self.environ['REQUEST_METHOD'] == 'POST':
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
            #check user/pass

            for item in init_json["components"]:
                self.component_status[item["name"]] = "configured"

            LOG.debug("Status of specified components changed to ready.")
            response_body = json.dumps({"Message":"Status of specified components changed to ready."})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            LOG.debug(str([response_body]))
            return [response_body]

        elif self.environ['REQUEST_METHOD'] == 'DELETE':
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
            #check user/pass

            for item in init_json["components"]:
                self.component_status[item["name"]] = "None"

            LOG.debug("Status of specified components changed to NOT ready.")
            response_body = json.dumps({"Message":"Status of specified components changed to NOT ready."})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            LOG.debug(str([response_body]))
            return [response_body]
        else:
            return self.not_found()

    def message_mgnt(self):
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
            #check user/pass

            if self.message_queue.qsize() > 0:
                tmp_msg = self.message_queue.get()
            else:
                tmp_msg = Message("dummy", "dummy", "dummy", "dummy")

            LOG.debug("Message popped from the queue. Content: " + tmp_msg.get_json())
            response_body = tmp_msg.get_json()
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            LOG.debug(str([response_body]))
            return [response_body]

        elif self.environ['REQUEST_METHOD'] == 'PUT':
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
            #check user/pass

            tmp_msg = Message(init_json["from_whom"], init_json["to_whom"], init_json["task"], datetime.datetime.now())
            self.message_queue.put(tmp_msg)

            LOG.debug("Message pushed to the queue.")
            response_body = json.dumps({"Message":"Message pushed to the queue."})
            self.start_response('200 OK', [('Content-Type', self.jsontype), ('Content-Length', str(len(response_body)))])
            LOG.debug(str([response_body]))
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
            if (auth_json["user"]=="UI" and auth_json["password"]=="UI"):
                token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                self.alloweduser = auth_json["user"]
                self.allowedtoken = token
                response_body = '{"user":"UI","token":"' + token + '"}'
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
    httpd = make_server('', 8055, application)
    httpd.serve_forever()