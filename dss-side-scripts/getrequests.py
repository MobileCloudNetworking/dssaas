#!/usr/bin/python
# -*- coding: utf-8 -*-
author = "Santiago Ruiz"
copyright = "Copyright 2014, SoftTelecom"

import datetime

delta = datetime.timedelta(0,0,0,0,1)
now = datetime.datetime.utcnow() - delta
path = '/var/log/tomcat7/localhost_access_log.' + str(now.year) + '-' + "%02d" % now.month + '-' + "%02d" % now.day + '.txt'
#11/Nov/2015:15:54:15
strmonth = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
pattern = "%02d" % now.day + '/' + strmonth[now.month-1] + '/' + str(now.year) + ':' + "%02d" % now.hour + ':' + "%02d" % now.minute + ':'
counter = 0
f_handler = open(path)
for line in f_handler:
        if pattern in line:
                counter += 1
f_handler.close()
print str(counter)