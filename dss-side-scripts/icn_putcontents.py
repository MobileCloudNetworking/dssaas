#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import json
import logging
import time
from subprocess import call, Popen, PIPE, STDOUT
import sys
import os
import httplib2 as http

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('icn_putcontents_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

class IcnContentManager:

    def generate_contentlist(self, repo_path):
        contentlist = []
        for file in os.listdir(repo_path):
            if file.endswith(".webm"):
                contentlist.append(file)
        return contentlist

    def insert_file_to_icn(self, filename, prefix, repo_path):
        ret_code = -1
        if filename != "" and prefix != "":
            LOG.debug("Running command: " + '/home/ubuntu/ccnxdir/bin/ccnputfile ' + '-allownonlocal ' + 'ccnx:' + prefix + '/' + filename + ' ' + repo_path + '/' + filename)
            ret_code = call(['/home/ubuntu/ccnxdir/bin/ccnputfile', '-allownonlocal', 'ccnx:' + prefix + '/' + filename, repo_path + '/' + filename])
            #ret_code = 0
        return ret_code

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

                LOG.debug("Sending request to:" + target_url)
                response, content = h.request(target_url, req_type, json_data, headers)
            except Exception as e:
                LOG.debug("Handled " + target_url + " exception." + str(e))
                continue
            response_status = int(response.get("status"))
            LOG.debug("response status is:" + str(response_status) + " Content: " + str(content))
            if (response_status < 200 or response_status >= 400):
                continue
            content_dict = json.loads(content)
            return content_dict

if __name__ == "__main__":
    total = len(sys.argv)
    if (total < 2):#should be impossible to happen
        print ("Usage: python icn_putcontents.py <ICN_END_POINT> [<FILE_REPOSITORY_PATH> default: ./files] [<ICN_PREFIX> default: /dss]")
        sys.exit(1)

    icn_endpoint = sys.argv[1]
    LOG.debug("ICN endpoint set to: " + icn_endpoint)

    try:
        repo_path = sys.argv[2]
    except:
        repo_path = './files'
    LOG.debug("URL to poll set to: " + repo_path)

    try:
        icn_prefix = sys.argv[3]
    except:
        icn_prefix = '/dss'
    LOG.debug("ICN prefix set to: " + icn_prefix)

    cntManager = IcnContentManager()

    resp = cntManager.doRequest(icn_endpoint + '/icnaas/api/v1.0/endpoints/server','get','')
    LOG.debug("ICN get ICN server endpoints response is:" + str(resp))

    if len(resp) <= 0:
        LOG.debug("No icn server found. Now we exit ...")
        sys.exit(1)

    for item in resp["routers"]:
        route_added = False
        while route_added is not True:
            desired_route = item["public_ip"] + ':9695'
            out_p = Popen('/home/ubuntu/ccnxdir/bin/ccndstatus', stdout=PIPE, stderr=STDOUT, bufsize=1)
            for line in out_p.stdout:
                if desired_route in line:
                    route_added = True
            if route_added == False:
                LOG.debug("Route " + desired_route + ' not found, try to add the route:')

                LOG.debug('Executing: /home/ubuntu/ccnxdir/bin/ccndc add ccnx:/dss tcp ' + item["public_ip"] + ' 9695')
                #ret_code = call(['/home/ubuntu/ccnxdir/bin/ccndc', 'add', 'ccnx:/dss', 'tcp', item["public_ip"], '9695'])
                first_route_out_p = Popen('/home/ubuntu/ccnxdir/bin/ccndc add ccnx:' + icn_prefix + ' tcp ' + item["public_ip"] + ' 9695', shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)
                for line in first_route_out_p.stdout:
                    LOG.debug(line)
                #LOG.debug("ICN prefix route return code for " + item["public_ip"] + " is " + str(ret_code))

                LOG.debug('Executing: /home/ubuntu/ccnxdir/bin/ccndc add ccnx:/ccnx.org tcp ' + item["public_ip"] + ' 9695')
                #ret_code = call(['/home/ubuntu/ccnxdir/bin/ccndc', 'add', 'ccnx:/ccnx.org', 'tcp', item["public_ip"], '9695'])
                second_route_out_p = Popen('/home/ubuntu/ccnxdir/bin/ccndc add ccnx:/ccnx.org tcp ' + item["public_ip"] + ' 9695', shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)
                for line in second_route_out_p.stdout:
                    LOG.debug(line)
                #LOG.debug("ICN ccnx.org route return code for " + item["public_ip"] + " is " + str(ret_code))
            time.sleep(3)

    oldCntList =[]
    while 1:
        cntList = cntManager.generate_contentlist(repo_path)
        print str(cntList)
        if cntList != oldCntList:
            i = 0
            while i < len(cntList):
                if cntList[i] not in oldCntList:
                    LOG.debug("Inserting file " + cntList[i])
                    ret_code = cntManager.insert_file_to_icn(cntList[i], icn_prefix, repo_path)
                    if ret_code == 0:
                        i += 1
                else:
                    LOG.debug("File " + cntList[i] + " has been already inserted.")
                    i += 1
            LOG.debug("Contentlist process complete. Next insertion in 30 seconds ...")
            oldCntList = cntList
        else:
            LOG.debug("No change in content list detected. Next insertion in 30 seconds ...")
        time.sleep(30)