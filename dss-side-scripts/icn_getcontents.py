#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import json
import logging
import time
import httplib2 as http
from subprocess import call
import sys

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('icn_getcontents_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

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

    def generate_contentlist(self, data):
        contentlist = []
        if data is not None:
            for item in data.get("contents"):
                contentlist.append(item.get("filename"))
        return contentlist

    def get_file_from_icn(self, filename, prefix, http_server_path):
        ret_code = -1
        if filename != "" and prefix != "":
            #Using java client
            #LOG.debug("Running command: " + '/home/ubuntu/ccnxdir/bin/ccngetfile ' + '-v ' + 'ccnx:' + prefix + '/' + filename + ' ' + http_server_path + filename)
            #ret_code = call(['/home/ubuntu/ccnxdir/bin/ccngetfile', '-v', 'ccnx:' + prefix + '/' + filename, http_server_path + filename])

            #Using C client
            f_handler = open(http_server_path + filename, "w")
            LOG.debug("Running command: " + '/home/ubuntu/ccnxdir/bin/ccncat -p8' + 'ccnx:' + prefix + '/' + filename + ' > ' + http_server_path + filename)
            ret_code = call(['/home/ubuntu/ccnxdir/bin/ccncat', '-p8', 'ccnx:' + prefix + '/' + filename], stdout=f_handler)
            #f_handler.close()
        return ret_code

    def remove_file(self, filename, http_server_path):
        ret_code = -1
        if filename != "":
            LOG.debug("Running command: " + 'rm ' + http_server_path + filename)
            ret_code = call(['rm', http_server_path + filename])
        return ret_code

if __name__ == "__main__":
    total = len(sys.argv)
    if (total < 2):
        print ("Usage: python icn_getcontents.py <URL_TO_POLL_FROM> [<HTTP_SERVER_PATH> default: /var/www/] [<ICN_PREFIX> default: /dss]")
        sys.exit(1)

    url_to_poll = sys.argv[1]
    LOG.debug("URL to poll set to: " + url_to_poll)

    try:
        http_server_path = sys.argv[2]
    except:
        http_server_path = '/var/www/'
    LOG.debug("HTTP server path set to: " + http_server_path)

    try:
        icn_prefix = sys.argv[3]
    except:
        icn_prefix = '/dss'
    LOG.debug("ICN prefix set to: " + icn_prefix)

    cntManager = IcnContentManager()
    oldCntList =[]
    while 1:
        data = cntManager.doRequest(url_to_poll, "GET", None)
        cntList = cntManager.generate_contentlist(data)
        if cntList != oldCntList:
            i = 0
            while i < len(cntList):
                if cntList[i] not in oldCntList:
                    LOG.debug("Downloading file " + cntList[i])
                    ret_code = cntManager.get_file_from_icn(cntList[i], icn_prefix, http_server_path)
                    if ret_code == 0:
                        LOG.debug("File " + cntList[i] + " successfully downloaded.")
                        i += 1
                else:
                    LOG.debug("File " + cntList[i] + " has been already downloaded.")
                    i += 1
            i = 0
            while i < len(oldCntList):
                if oldCntList[i] not in cntList:
                    LOG.debug("Removing file " + oldCntList[i])
                    ret_code = cntManager.remove_file(oldCntList[i], http_server_path)
                    if ret_code == 0:
                        LOG.debug("File " + oldCntList[i] + " successfully removed.")
                        i += 1
                else:
                    i += 1
            LOG.debug("Contentlist process complete. Next poll in 30 seconds ...")
            oldCntList = cntList
        else:
            LOG.debug("No change in content list detected. Next poll in 30 seconds ...")
        time.sleep(30)