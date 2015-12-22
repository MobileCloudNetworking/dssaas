__author__ = 'Santi'

from socket import *
import fcntl
import struct
import logging

class TrackerManager:
    #TODO: Tracker expiration thread
    def __init__(self, file_manager):
        self.log=logging.getLogger('mylog')
        self.fm = file_manager
        self.tracker = self.get_ip_address('eth0')
        self.tracker_list=[]
        self.tracker_list.append(self.tracker)

    def get_ip_address(ifname):
        s = socket(AF_INET, SOCK_DGRAM)
        return inet_ntoa(fcntl.ioctl( s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

    # Not available ATM
    def addTracker(self,tracker_ep):
        pass

    # Not available ATM
    def removeTracker(self,tracker_ep):
        pass

    # Not available ATM
    def getTrackerList(self):
        return self.tracker_list

    # Not available ATM
    def getSelfTracker(self):
        return self.tracker
