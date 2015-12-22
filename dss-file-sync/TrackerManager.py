__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

from socket import *
import fcntl
import struct
import logging
import Config
import time
import threading

class TrackerManager(threading.Thread):
    def __init__(self, file_manager):
        threading.Thread.__init__(self)
        self.log = logging.getLogger(Config.get('log', 'name'))
        self.fm = file_manager
        self.tracker = {'url': self.get_ip_address(Config.get('main','interface')), 'timestamp': repr(time.time())}
        self.tracker_list = []
        self.tracker_list.append(self.tracker)
        self.tracker_timeout = int(Config.get('main', 'tracker_timeout'))

    def run(self):
        self.log.debug("Starting Tracker Expiration Monitoring")
        # Check time stamp of trackers and make them expire
        while 1:
            for tracker in self.tracker_list:
                self.log.debug("Processing tracker: " + str(tracker))
                diff = time.time() - time.ctime(float(tracker['timestamp']))
                self.log.debug("Tracker is " + str(diff) + " seconds old")
                if diff > self.tracker_timeout:
                    self.log.debug("Removing tracker " + str(tracker['url']))
                    self.remove_tracker(tracker)
            time.sleep(1)
        self.log.debug("Exiting Tracker Expiration Monitoring")

    def get_ip_address(ifname):
        s = socket(AF_INET, SOCK_DGRAM)
        return inet_ntoa(fcntl.ioctl( s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

    def add_tracker(self, tracker_ep):
        self.tracker_list.append(tracker_ep)

    def remove_tracker(self, tracker_ep):
        self.tracker_list.remove(tracker_ep)

    def get_tracker_list(self):
        return self.tracker_list

    def get_self_tracker(self):
        return self.tracker
