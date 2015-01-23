#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2014, SoftTelecom"

import MySQLdb as mdb
import sys

try:
    total = len(sys.argv)
    if (total < 5):
        print "Usage: python getcdr.py [host] [username] [password] [database]"
        sys.exit(1)
    con = mdb.connect(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM `player` WHERE active = 1;")
    if cur.rowcount is 0:
        print "0"
    else:
        row = cur.fetchone()
        n = row[0]
        print n
except mdb.Error as e:
    print "Error " + str(e)
    sys.exit(1)  
finally:    
    if con:    
        con.close()
