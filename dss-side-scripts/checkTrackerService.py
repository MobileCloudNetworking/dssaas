#!/usr/bin/python
# -*- coding: utf-8 -*-
author = "Mohammad Valipoor"
copyright = "Copyright 2016, SoftTelecom"

# Check if Tracker service is up and running

import os

process_id = None
process_name = "opentracker"
# Read the file on /var/run/proc_name.pid and fetch the pid
file_object = open("/var/run/" + process_name + ".pid", "r")
process_id = file_object.read().strip()
file_object.close()

try:
        os.kill(int(process_id), 0)
        print "1"
except Exception as e:
        print "0"

exit(0)