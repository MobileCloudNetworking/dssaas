__author__ = 'Santi'

from socket import *
import time
import base64
import logging
import Config

class BroadcastManager:
    #TODO: Sending thread, recieving thread
    def __init__(self, file_manager, torrent_manager):
        self.broadcast_port = 6977
        self.broadcast_ip = '255.255.255.255'
        self.tm = torrent_manager
        self.fm = file_manager
        self.path = './'
        #check
        self.log = logging.getLogger(Config.get('log','name'))
        self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        self.log.debug('TrackerList:' + str(self.tm.get_tracker_list()))

    def send_broadcast_message(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        data = 'udp://' + str(self.tm.get_self_tracker()) +':6969/announce' + '!' + repr(time.time())
        for torrent in self.tm.get_torrent_list():
            self.log.debug('Checking torrent: ' + str(torrent))
            data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
        data += '\n'
        self.log.debug(data)
        s.sendto(data, (self.broadcast_ip, self.broadcast_port))
        time.sleep(1)

    def sendAmazon_broadcast_message(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        data = 'udp://' + str(self.tm.get_self_tracker()) +':6969/announce' + '!' + repr(time.time())
        self.log.debug(str(self.tm.get_torrent_list()))
        for torrent in self.tm.get_torrent_list():
            self.log.debug('Checking torrent: ' + str(torrent))
            data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
        data += '\n'
        self.log.debug(data)
        for i in range(4,254):
            s.sendto(data, ('172.30.2.'+str(i), self.broadcast_port))
        time.sleep(1)

    def receive_broadcast_message(self):
        s = socket(AF_INET,SOCK_DGRAM) # UDP
        s.bind(('0.0.0.0',self.broadcast_port))
        while True:
            data, addr = s.recvfrom(4096) # buffer size is 4096 bytes
            self.log.debug("received message:", data)
            self.parse_broadcast_message(data)


    def parse_broadcast_message(self,message):
        #udp://172.30.2.46:6969/announce!1450430624.7613!mytorrent.torrent!ZDg6YW5ub3VuY2UyOTp1ZHA6Ly9sb2NhbGhvc3Q6Njk2OS9hbm5vdW5jZTc6Y29tbWVudDQ6VGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDI4NzIxNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lODp0ZXN0LnR4dDEyOnBpZWNlIGxlbmd0aGkxNjM4NGU2OnBpZWNlczgwOv2TLO5kpmZ7SZq+v6i5Z01VNmm3IxcyPZRmLZeuJ7Gl+ZC0C9egeh99D/42XYE55Q0zaSgCrP+BIY1T7qr/muq34oDUxWetqRw89wWpSlcdZWU=!my.torrent!ZDg6YW5ub3VuY2UxMToxNzIuMzAuMi40Njc6Y29tbWVudDQ6dGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDQzMDYyNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lNzpteS5maWxlMTI6cGllY2UgbGVuZ3RoaTE2Mzg0ZTY6cGllY2VzODA6/ZMs7mSmZntJmr6/qLlnTVU2abcjFzI9lGYtl64nsaX5kLQL16B6H30P/jZdgTnlDTNpKAKs/4EhjVPuqv+a6rfigNTFZ62pHDz3BalKVx1lZQ==
        msg_list = message.split('!')
        if (msg_list[0] not in self.tm.get_tracker_list()):
            self.tm.add_tracker(msg_list[0])
            #new tracker was added, I should recreate my torrents for fully downloaded files
            for filename in self.fm.list_files(self.path,['.webm'])[1]:
                self.tm.create_torrent(self.path,filename.split('.')[0]+'.torrent')
        for index in range (2, len(msg_list),2):
            #check if I do have the torrent file
            torrent_name =  msg_list[index]
            torrent_content = msg_list[index+1]
            if (torrent_name not in self.tm.get_torrent_list()):
                with open(self.path + torrent_name, "wb") as torrentfileh:
                    torrentfileh.write(base64.b64decode(torrent_content))
        #now I might add it to the session to start downloading
        #check
        self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        self.log.debug('TrackerList:' + str(self.tm.get_tracker_list()))

