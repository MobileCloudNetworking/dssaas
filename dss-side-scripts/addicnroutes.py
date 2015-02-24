#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Mohammad Valipoor"
__copyright__ = "Copyright 2014, SoftTelecom"

import MySQLdb as mdb
import sys
from subprocess import call
import time

try:
    total = len(sys.argv)
    if (total < 6):
        print "Usage: python addicnroutes.py [host] [username] [password] [database] [icn_port]"
        sys.exit(1)
    con = mdb.connect(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    cur = con.cursor()
    while 1:
        idList = []
        cur.execute("SELECT `id`,`player_name`,`playerip` FROM `player` WHERE icn_flag = 0;")
        if cur.rowcount > 0:
            cnt = 0
            allRowCount = cur.rowcount
            while cnt < allRowCount:
                row = cur.fetchone()
                ip = row[2]
                ret_code = call(['./ccnxdir/bin/ccndc', 'add', 'ccnx:/ccnx.org', 'udp', ip, sys.argv[5]])
                print "return code for player " + row[1] + " with id " + str(row[0]) + " is " + str(ret_code)
                idList.append(row[0])
                time.sleep(5)
                cnt += 1

            for item in idList:
                cur.execute("UPDATE `player` SET icn_flag=1 WHERE id = " + str(item) + ";")
                time.sleep(5)

        time.sleep(30000)

except mdb.Error as e:
    print "Error " + str(e)
    sys.exit(1)
finally:
    if con:
        con.close()
