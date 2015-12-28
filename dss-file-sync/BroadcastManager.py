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
        self.rec_buff_size = 4096
        #check
        self.log = logging.getLogger(self.conf.get('log', 'name'))
        self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        self.log.debug('TrackerList:' + str(self.tkm.get_tracker_list()))

        # A list of dictionaries that contains message ID, a list of corresponding packets for that ID and an expiration time
        # Example: [{'id':'RANDOME_MESSAGE_ID', 'packets':[{'seq_num':'Integer', 'data':'String', 'is_final':'Boolean'}, packet2, packet3, ...], 'timeout':'Current time + self.message_timeout'}]
        self.all_packets_dict = []
        self.message_timeout = 60# Seconds

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
            data, addr = s.recvfrom(self.rec_buff_size) # buffer size is 4096 bytes
            #size = len(data)
            #while (size == self.rec_buff_size):
            #    newdata, addr = s.recvfrom(self.rec_buff_size)
            #    data += newdata
            #    size = len(newdata)
            #self.log.debug("received message: " + str(data))

            # Decouple message sections
            message_id, packet_seq_num, packet_data = self.parse_packet(addr, data)

            # Proceed with pushing the message if decouple successful
            if message_id is not None:
                # Push to packet dict
                self.push_to_packets_dict(message_id, packet_seq_num, packet_data, time.time())

                # Check the packet dict if we are done with this sequence of packets
                packet_ready, message_data = self.packet_sequence_complete(message_id)

                # All sequence received, parse the message
                if(packet_ready):
                    self.log.debug("Message with ID " + message_id + " ready, parsing it ...")
                    self.parse_broadcast_message(message_data)
            else:
                self.log.debug("Invalid packet received")

    # Gets a packet and returns message identifier, packet sequence number and its data
    def parse_packet(self, addr, data):
        # Expected packet structure
        try:
            data_parts = data.split('!')
            message_id = data_parts[0]
            sequence = data_parts[1]
            data = data_parts[2]
            return message_id, sequence, data
        except Exception as e:
            self.log.warning("Exception while parsing packet data: " + str(e))
            return None, None, None

    # Checks if the parameter packet_data is a final packet in a message sequence
    def is_final(self, packet_data):
        return "\n\n" in packet_data

    # Gets message identifier, packet sequence number and its data, then pushes it into packets dictionary
    def push_to_packets_dict(self, message_id, sequence, data, time):
        msg_id = message_id
        msg_arrival_time = time
        new_packet = {'seq_num': sequence, 'data': data, 'is_final': self.is_final(data)}

        # Check if we arleady have gotten a packet related to this message
        # if yes we just add new packet to the packet list
        msg_id_exists = False
        for item in self.all_packets_dict:
            if item['id'] == msg_id:
                item['packets'].append(new_packet)
                msg_id_exists = True

        # This is the first packet we are getting for this message, so we init a new dict item for this message in all_packets_dict
        if msg_id_exists is not True:
            new_msg_entity = {'id': msg_id, 'packets': [new_packet], 'timeout': msg_arrival_time + self.message_timeout}
            self.all_packets_dict.append(new_msg_entity)

    # Gets the identifier of a message and check if all the related packets are received
    # If the message is complete returns True plus the message and removes it from packets dictionary
    def packet_sequence_complete(self, message_id):
        return False, None

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

