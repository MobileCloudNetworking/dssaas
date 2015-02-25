#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import MySQLdb as mdb
import sys
from subprocess import call
import time
import logging

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('addicnroutes_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

try:
    total = len(sys.argv)
    if (total < 6):
        print "Usage: python addicnroutes.py [host] [username] [password] [database] [icn_port]"
        sys.exit(1)
    while 1:
        con = mdb.connect(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        LOG.debug("Connection to DB opened")
        cur = con.cursor()
        idList = []
        cur.execute("SELECT `id`,`player_name`,`playerip` FROM `player` WHERE icn_flag = 0;")
        LOG.debug("Select row count is : " + str(cur.rowcount))
        if cur.rowcount > 0:
            cnt = 0
            allRowCount = cur.rowcount
            while cnt < allRowCount:
                row = cur.fetchone()
                ip = row[2]
                LOG.debug("Running command : " + './ccnxdir/bin/ccndc' + 'add' + 'ccnx:/ccnx.org' + 'udp' + ip + sys.argv[5])
                ret_code = call(['./ccnxdir/bin/ccndc', 'add', 'ccnx:/ccnx.org', 'udp', ip, sys.argv[5]])
                LOG.debug("return code for player " + row[1] + " with id " + str(row[0]) + " is " + str(ret_code))
                idList.append(row[0])
                time.sleep(5)
                cnt += 1

            for item in idList:
                LOG.debug("UPDATE `player` SET icn_flag=1 WHERE id = " + str(item) + ";")
                cur.execute("UPDATE `player` SET icn_flag=1 WHERE id = " + str(item) + ";")
                time.sleep(5)
        con.close()
        LOG.debug("Connection closed, waiting 30 seconds for next poll")
        time.sleep(30)

except mdb.Error as e:
    LOG.debug("Error " + str(e))
    if con:
        LOG.debug("Unexpected connection close")
        con.close()
    sys.exit(1)
