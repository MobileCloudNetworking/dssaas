#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2014, SoftTelecom"

import MySQLdb as mdb
import sys

try:
    total = len(sys.argv)
    if (total < 5):
        print ("Usage: python getcdr.py [host] [username] [password] [database]")
        sys.exit(1)
    con = mdb.connect(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]);
    cur = con.cursor()
    cur.execute("SELECT * FROM cdregister LIMIT 1;")
    if (cur.rowcount==0):
        json = '{}'
        print json
    else:
        row = cur.fetchone()
        # fill in CDR info 
        id = row[0]
        user_id=row[5]
        player_id=row[3]
        start_time=row[4]
        end_time=row[2]
        # building json
        json = '{"player_id":"' + str(player_id) + '","user_id":"' + str(user_id) + '","start_time":"' + str(start_time) + '","end_time":"' + str(end_time) + '"}'
        cur.execute("DELETE FROM `cdregister` WHERE id = " + str(id) + ";")
        con.commit()
        print json
    
except mdb.Error, e:
    print "{}"
    sys.exit(1)
    
finally:    
    if con:    
        con.close()