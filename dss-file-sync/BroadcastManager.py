__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

from socket import *
import time
import base64
import logging
from Config import *
import threading


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class BroadcastManager():
    #TODO: Sending thread, recieving thread
    def __init__(self, file_manager, torrent_manager,tracker_manager):
        self.broadcast_port = 6977
        self.broadcast_ip = '255.255.255.255'
        self.tm = torrent_manager
        self.tkm = tracker_manager
        self.fm = file_manager
        self.conf = Config()
        self.path = self.conf.get('main', 'path')
        #check
        self.log = logging.getLogger(self.conf.get('log', 'name'))
        self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        self.log.debug('TrackerList:' + str(self.tkm.get_tracker_list()))

    @threaded
    def send_broadcast_message(self):
        while True:
            s = socket(AF_INET, SOCK_DGRAM)
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            data = str(self.tkm.get_self_tracker()['url']) + '!' + repr(time.time())
            for torrent in self.tm.get_torrent_list():
                self.log.debug('Checking torrent: ' + str(torrent))
                data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
            data += '\n'
            self.log.debug(data)
            s.sendto(data, (self.broadcast_ip, self.broadcast_port))
            time.sleep(10)

    @threaded
    def sendAmazon_broadcast_message(self):
        while True:
            s = socket(AF_INET, SOCK_DGRAM)
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            data = str(self.tkm.get_self_tracker()['url']) + '!' + repr(time.time())
            self.log.debug(str(self.tm.get_torrent_list()))
            for torrent in self.tm.get_torrent_list():
                self.log.debug('Checking torrent: ' + str(torrent))
                data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
            data += '\n'
            self.log.debug(data)
            for i in range(4,254):
                s.sendto(data, ('172.30.2.' + str(i), self.broadcast_port))
            time.sleep(10)

    @threaded
    def receive_broadcast_message(self):
        s = socket(AF_INET,SOCK_DGRAM) # UDP
        s.bind(('0.0.0.0', self.broadcast_port))
        while True:
            data, addr = s.recvfrom(4096) # buffer size is 4096 bytes
            size = len(data)
            while (size == 4096):
                newdata, addr = s.recvfrom(4096)
                data += newdata
                size = len(newdata)
        self.log.debug("received message: " + str(data))
        self.parse_broadcast_message(data)


    def parse_broadcast_message(self, message):
        #udp://172.30.2.46:6969/announce!1450430624.7613!mytorrent.torrent!ZDg6YW5ub3VuY2UyOTp1ZHA6Ly9sb2NhbGhvc3Q6Njk2OS9hbm5vdW5jZTc6Y29tbWVudDQ6VGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDI4NzIxNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lODp0ZXN0LnR4dDEyOnBpZWNlIGxlbmd0aGkxNjM4NGU2OnBpZWNlczgwOv2TLO5kpmZ7SZq+v6i5Z01VNmm3IxcyPZRmLZeuJ7Gl+ZC0C9egeh99D/42XYE55Q0zaSgCrP+BIY1T7qr/muq34oDUxWetqRw89wWpSlcdZWU=!my.torrent!ZDg6YW5ub3VuY2UxMToxNzIuMzAuMi40Njc6Y29tbWVudDQ6dGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDQzMDYyNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lNzpteS5maWxlMTI6cGllY2UgbGVuZ3RoaTE2Mzg0ZTY6cGllY2VzODA6/ZMs7mSmZntJmr6/qLlnTVU2abcjFzI9lGYtl64nsaX5kLQL16B6H30P/jZdgTnlDTNpKAKs/4EhjVPuqv+a6rfigNTFZ62pHDz3BalKVx1lZQ==
        msg_list = message.strip('\n').split('!')
        tracker_struct = {'url':msg_list[0], 'timestamp':msg_list[1]}
        is_new = self.tkm.update_tracker(tracker_struct)
        if is_new:
            self.tm.recreate_all_torrents()
        for index in range (2, len(msg_list), 2):
            #check if I do have the torrent file
            torrent_name =  msg_list[index]
            torrent_content = msg_list[index + 1]
            self.tm.save_torrent(torrent_name,torrent_content)
        #check
        self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        self.log.debug('TrackerList:' + str(self.tkm.get_tracker_list()))

