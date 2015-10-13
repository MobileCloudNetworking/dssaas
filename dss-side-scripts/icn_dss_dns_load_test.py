#!/usr/bin/python
# -*- coding: utf-8 -*-
import getopt

__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import json
import time
import httplib2 as http
from subprocess import call
import sys


class IcnContentManager:

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
            ret_code = call(['/home/ubuntu/ccnxdir/bin/ccncat', '-p8', 'ccnx:' + prefix + '/' + filename], stdout=f_handler)
        return ret_code

    def remove_file(self, filename, http_server_path):
        ret_code = -1
        if filename != "":
            ret_code = call(['rm', http_server_path + filename])
        return ret_code

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hu:t:f:p:",["url=","time=","file_path=","prefix="])
    except getopt.GetoptError:
        print ("Usage: python icn_dss_dns_load_test.py -u <URL_TO_POLL_FROM> -t [Request delay default: 0.5] -f [PATH_TO_SAVE-FILES default: ./] -p [ICN_PREFIX default: /dss]")
        sys.exit(0)

    url_to_poll = None
    request_delay = None
    http_server_path = None
    icn_prefix = None

    for opt, arg in opts:
        if opt == '-h':
            print ("Usage: python icn_dss_dns_load_test.py -u <URL_TO_POLL_FROM> -t [Request delay default: 0.5] -f [PATH_TO_SAVE-FILES default: ./] -p [ICN_PREFIX default: /dss]")
            sys.exit(0)
        elif opt in ("-u", "--url"):
            url_to_poll = arg
        elif opt in ("-t", "--time"):
            request_delay = arg
        elif opt in ("-f", "--file_path"):
            http_server_path = arg
        elif opt in ("-p", "--prefix"):
            icn_prefix = arg

    if url_to_poll is None:
        print 'Polling URL is mandatory!'
        exit(0)

    if request_delay is None:
        request_delay = '0.5'

    if http_server_path is None:
        http_server_path = './'

    if icn_prefix is None:
        icn_prefix = '/dss'

    cntManager = IcnContentManager()
    oldCntList =[]
    while 1:
        data = cntManager.doRequest(url_to_poll, "GET", None)
        cntList = cntManager.generate_contentlist(data)
        i = 0
        while i < len(cntList):
            ret_code = cntManager.get_file_from_icn(cntList[i], icn_prefix, http_server_path)
            if ret_code == 0:
                i += 1
            else:
                print "Error while getting content " + str(i)
            time.sleep(request_delay)
        i = 0
        while i < len(cntList):
            ret_code = cntManager.remove_file(oldCntList[i], http_server_path)
            if ret_code == 0:
                i += 1
            else:
                print "Error while removing content " + str(i)
            time.sleep(0.1)

if __name__ == "__main__":
    main(sys.argv[1:])