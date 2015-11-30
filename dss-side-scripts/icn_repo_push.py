#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import logging
import time
from subprocess import call
import os

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('icn_repo_push_log.txt')
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
            LOG.debug("Running command: " + '/home/ubuntu/ccnx-0.8.2/bin/ccnputfile ' + 'ccnx:' + prefix + '/' + filename + ' ' + repo_path + '/' + filename)
            #ret_code = call(['/home/centos/ccnx-0.8.2/bin/ccnputfile', 'ccnx:' + prefix + '/' + filename, repo_path + '/' + filename])
            ret_code = os.system('/home/ubuntu/ccnx-0.8.2/bin/ccnputfile ccnx:' + prefix + '/' + filename + ' ' + repo_path + '/' + filename)
            #ret_code = 0
        return ret_code

if __name__ == "__main__":

    repo_path = './files'
    LOG.debug("URL to poll set to: " + repo_path)

    icn_prefix = '/dss'
    LOG.debug("ICN prefix set to: " + icn_prefix)

    cntManager = IcnContentManager()

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