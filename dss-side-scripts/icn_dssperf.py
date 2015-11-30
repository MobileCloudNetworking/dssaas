#!/usr/bin/python
# -*- coding: utf-8 -*-
import getopt
import threading

__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import json
import time
import httplib2 as http
from subprocess import call
import sys
import pycurl
import cStringIO
import datetime
import os
import numpy

class IcnContentManager:

    def __init__(self):
        self.dl_time = 0.0
        self.zipfcounter = 0
        self.zipfdist = numpy.random.zipf(1.01,5000) # list size 5000!!!!

    def doCurlRequest(self, target_url):
        response_status = 0
        if (response_status < 200 or response_status >= 400):
            curl = pycurl.Curl()
            buff = cStringIO.StringIO()
            curl.setopt(pycurl.URL, target_url)
            curl.setopt(pycurl.WRITEFUNCTION, buff.write)
            try:
                    curl.perform()
                    response_status = int(curl.getinfo(pycurl.HTTP_CODE))
            except Exception as e:
                    response_status = -1
            curl.close()
            if (response_status < 200 or response_status >= 400):
                print 'error in ' + target_url + 'request'
                return None
            content_dict = json.loads(buff.getvalue())
        return content_dict

    def doRequest(self, target_url, req_type, json_data):
        response_status = 0
        while (response_status < 200 or response_status >= 400):
            time.sleep(1)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            try:
                h = http.Http()
                h.timeout = 30

                response, content = h.request(target_url, req_type, json_data, headers)
            except Exception as e:
                continue
            response_status = int(response.get("status"))
            if (response_status < 200 or response_status >= 400):
                continue
            content_dict = json.loads(content)
            return content_dict

    def generate_contentlist(self, data):
        contentlist = []
        if data is not None:
            for item in data.get("contents"):
                contentlist.append(item.get("filename"))
        return contentlist

    def get_file_from_icn(self, filename, prefix, http_server_path):
        ret_code = -1
        if filename != "" and prefix != "":
            #Using C client
            f_handler = open(http_server_path + filename, "w")
            start_t = datetime.datetime.now()
            ret_code = call(['/home/ubuntu/ccnxdir/bin/ccncat', '-p16', 'ccnx:' + prefix + '/' + filename], stdout=f_handler)
            end_t = datetime.datetime.now()
            self.dl_time = float((end_t - start_t).seconds)
            if self.dl_time < 1.0:
                self.dl_time = 1.0
        return ret_code

    def get_zipf_file_from_icn(self, prefix, http_server_path):
        ret_code = -1
        while (self.zipfdist[self.zipfcounter] > 199): # biggest file name 199.webm!!!!
            self.zipfcounter = self.zipfcounter + 1
        self.filename = str(self.zipfdist[self.zipfcounter]) + ".webm"
        if (self.zipfcounter == 5000):
            self.zipfconuter = 0
        self.zipfcounter = self.zipfcounter + 1
        if self.filename != "" and prefix != "":
            #Using C client
            f_handler = open(http_server_path + self.filename, "w")
            start_t = datetime.datetime.now()
            ret_code = call(['/home/ubuntu/ccnxdir/bin/ccncat', '-p16', 'ccnx:' + prefix + '/' + self.filename], stdout=f_handler)
            end_t = datetime.datetime.now()
            self.dl_time = float((end_t - start_t).seconds)
            if self.dl_time < 1.0:
                self.dl_time = 1.0
        return ret_code

    def remove_file(self, filename, http_server_path):
        ret_code = -1
        if filename != "":
            ret_code = call(['rm', http_server_path + filename])
        return ret_code

    def remove_zipf_file(self, http_server_path):
        ret_code = -1
        ret_code = call(['rm', http_server_path + self.filename])
        return ret_code


class icnThread(threading.Thread):
    def __init__(self, url_to_poll, ep_to_poll, icn_api_url, interest_count, http_server_path, icn_prefix, ready_event):
        self.event = ready_event
        self.testComponent = 'icnThread'
        threading.Thread.__init__(self)
        print self.testComponent + " initialized."

        self.url_to_poll = url_to_poll
        self.ep_to_poll = ep_to_poll
        self.icn_api_url = icn_api_url
        self.http_server_path = http_server_path
        self.icn_prefix = icn_prefix
        self.interest_count = interest_count

        #parseUrl = url_to_poll.split("/")
        self.url_to_poll = "http://localhost/"

    def run(self):
        print self.testComponent + " started."
        cntManager = IcnContentManager()
        oldRouterList = {"routers":[]}
        while 1:
            resp_routers = cntManager.doRequest(self.icn_api_url + '/icnaas/api/v1.0/endpoints/client','GET','')

            if oldRouterList != resp_routers:
                i = 0
                while i < len(resp_routers["routers"]):
                    if resp_routers["routers"][i] not in oldRouterList["routers"]:
                        ret_code = call(['/home/ubuntu/ccnxdir/bin/ccndc', 'add', 'ccnx:' + self.icn_prefix, 'tcp', resp_routers["routers"][i]["public_ip"], '9695'])
                        time.sleep(0.2)
                        ret_code = call(['/home/ubuntu/ccnxdir/bin/ccndc', 'add', 'ccnx:/ccnx.org', 'tcp', resp_routers["routers"][i]["public_ip"], '9695'])
                        time.sleep(0.2)
                    i += 1
                oldRouterList = resp_routers
                ret_code = call(['/home/ubuntu/ccnxdir/bin/ccndc', 'setstrategy', 'ccnx:' + self.icn_prefix, 'loadsharing'])

            ret_code = cntManager.get_zipf_file_from_icn(self.icn_prefix, self.http_server_path)
            if ret_code == 0:
                pass
            else:
                print "Error while getting content " + str(i)

            ret_code = cntManager.remove_zipf_file(self.http_server_path)
            if ret_code == 0:
                pass
            else:
                print "Error while removing content " + str(i)


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hu:e:i:c:f:p:q:",["url=","endpoint=","icn=","icount=","file_path=","prefix=","dns_qps="])
    except getopt.GetoptError:
        print ("Usage: python icn_dss_dns_load_test.py -u <URL_TO_POLL_FROM> -e <DSS_CMS_IP> -i <ICN_API_URL> -c [Number of desired interests per sec: 300] -f [PATH_TO_SAVE-FILES default: ./] -p [ICN_PREFIX default: /dss] -q [dns_qps]")
        sys.exit(0)

    url_to_poll = None
    ep_to_poll = None
    request_delay = None
    http_server_path = None
    icn_prefix = None
    icn_api_url = None
    dns_qps = None

    for opt, arg in opts:
        if opt == '-h':
            print ("Usage: python icn_dss_dns_load_test.py -u <URL_TO_POLL_FROM> -e <DSS_CMS_IP> -i <ICN_API_URL> -c [Number of desired interests per sec: 300] -f [PATH_TO_SAVE-FILES default: ./] -p [ICN_PREFIX default: /dss]")
            sys.exit(0)
        elif opt in ("-u", "--url"):
            url_to_poll = arg
        elif opt in ("-e", "--endpoint"):
            ep_to_poll = arg
        elif opt in ("-i", "--icn"):
            icn_api_url = arg
        elif opt in ("-c", "--icount"):
            interest_count = int(arg)
        elif opt in ("-f", "--file_path"):
            http_server_path = arg
        elif opt in ("-p", "--prefix"):
            icn_prefix = arg
        elif opt in ("-q", "--dns_qps"):
            dns_qps = arg

    if url_to_poll is None:
        print 'Polling URL is mandatory!'
        exit(0)

    if ep_to_poll is None:
        print 'Polling Endpoint is mandatory!'
        exit(0)

    if icn_api_url is None:
        print 'ICN Polling URL is mandatory!'
        exit(0)

    if interest_count is None:
        interest_count = 10

    if http_server_path is None:
        http_server_path = './'

    if icn_prefix is None:
        icn_prefix = '/dss'

    if dns_qps is None:
        dns_qps = 10


    shared_event = threading.Event()
    icn_thread = icnThread(url_to_poll, ep_to_poll, icn_api_url, interest_count, http_server_path, icn_prefix, shared_event)
    icn_thread.daemon = True
    #Running threads
    icn_thread.start()
    #Making app wait till someone actually kill the process
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1:])