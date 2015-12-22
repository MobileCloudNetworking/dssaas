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
from Config import *
import time
import threading

class TrackerManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
	conf = Config()
        self.log = logging.getLogger(conf.get('log', 'name'))
	print conf.get('main','interface')
	iface = str(conf.get('main','interface'))
        self.tracker = {'url': 'udp://'+str(self.get_ip_address(iface))+':6969/announce', 'timestamp': repr(time.time())}
        self.tracker_list = []
        self.tracker_list.append(self.tracker)
        self.tracker_timeout = int(conf.get('main', 'tracker_timeout'))

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

    def get_ip_address(self,ifname):
        s = socket(AF_INET, SOCK_DGRAM)
        return inet_ntoa(fcntl.ioctl( s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

    def add_tracker(self, tracker_struct):
        self.tracker_list.append(tracker_struct)

    def remove_tracker(self, tracker_struct):
        self.tracker_list.remove(tracker_struct)

    def get_tracker_list(self):
        return self.tracker_list

    def get_self_tracker(self):
        return self.tracker

    #is_new = self.tkm.update_tracker(tracker_struct)
    def update_tracker(self, tracker_struct):
	for tracker in self.tracker_list:
	   if tracker['url'] == tracker_struct['url']:
		#we had the tracker before, i just update the timestamp
		tracker['timestamp'] = tracker_struct['timestamp']
		return False
	#it is new, we add it
	self.add_tracker(tracker_struct)
	return True
