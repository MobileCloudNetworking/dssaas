#!/usr/bin/python
# -*- coding: utf-8 -*-
author = "Mohammad Valipoor"
copyright = "Copyright 2016, SoftTelecom"

# Check if Filesync service is up and running

import os

process_id = None
process_name = "main.py"
try:
    # Read the file on /var/run/proc_name.pid and fetch the pid
    file_object = open("/var/run/filesync/" + process_name + ".pid", "r")
    process_id = file_object.read().strip()
    file_object.close()
    os.kill(int(process_id), 0)
    print "1"
except Exception as e:
    print "0"
exit(0)