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
from operator import itemgetter
import random

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
            #building the udp packets and sending them separately
            stream_id = str(int(random.random()*10000 - 1))
            seq = 1
            data_index = 0
            while data_index < len(data):
                #5 first chars for seq, 3 chars for seq
                packet_header_size = len(packet)
                remaining = len(data) - data_index # remaining unsplitted data buffer size
                #available size for payload is upd_size - header - ending char(1 char)
                if (self.rec_buff_size-packet_header_size-1) < remaining:
                    #still more than 1 packet to be sent
                    packet = stream_id + '!' + str(seq) + '!' + data[data_index:data_index+self.rec_buff_size-packet_header_size-1]+"\n"
                    data_index+=self.rec_buff_size-packet_header_size-1
                else:
                    packet += data[data_index:] + '\n' #data string already finish with a \n so this one doubles it
                    data_index = len(data)
                s.sendto(packet, (self.broadcast_ip, self.broadcast_port))
                seq += 1
                time.sleep(0.5)
            time.sleep(30)

    @threaded
    def sendAmazon_broadcast_message(self):
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
            #building the udp packets and sending them separately
            stream_id = str(int(random.random()*10000 - 1))
            seq = 1
            data_index = 0
            while data_index < len(data):
                #5 first chars for seq, 3 chars for seq
                packet_header_size = len(packet)
                remaining = len(data) - data_index
                #available size for payload is upd_size - header - ending char(1 char)
                if (self.rec_buff_size-packet_header_size-1) < remaining:
                    #still more than 1 packet to be sent
                    packet = stream_id + '!' + str(seq) + '!' + data[data_index:data_index+self.rec_buff_size-packet_header_size-1]+"\n"
                    data_index+=self.rec_buff_size-packet_header_size-1
                else:
                    packet += data[data_index:] + '\n' #data string already finish with a \n so this one doubles it
                    data_index = len(data)
                for i in range(4,254):
                    s.sendto(packet, ('172.30.2.' + str(i), self.broadcast_port))
                seq += 1
                time.sleep(0.5)
            time.sleep(30)

    @threaded
    def receive_broadcast_message(self):
        s = socket(AF_INET,SOCK_DGRAM) # UDP
        s.bind(('0.0.0.0', self.broadcast_port))
        while True:
            data, addr = s.recvfrom(self.rec_buff_size) # buffer size is 4096 bytes

            # Decouple message sections
            message_id, packet_seq_num, packet_data = self.parse_packet(addr, data)

            # Proceed with pushing the message if decouple successful
            if message_id is not None:
                # Push to packet dict
                self.push_to_packets_dict(message_id, packet_seq_num, packet_data, time.time())

                # Check the packet dict if we are done with this sequence of packets
                is_complete, message_data = self.is_stream_complete(message_id)

                # All sequence received, parse the message
                if(is_complete):
                    self.log.debug("Message with ID " + message_id + " ready, parsing it ...")
                    self.log.debug("Message data: " + str(message_data))
                    self.parse_broadcast_message(message_data)
            else:
                self.log.debug("Invalid packet received")

    @threaded
    # Checks the time out for all pushed messages and removes them all in case they're expired
    def remove_expired_streams(self):
        while True:
            if len(self.all_packets_dict) > 0:
                current_time = time.time()
                expired_ones = [message for message in self.all_packets_dict if current_time >= message[timeout]]
                for message in expired_ones:
                        self.all_packets_dict.remove(message)
        time.sleep(self.message_timeout)

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
    def is_stream_complete(self, message_id):
        message_block = None
        packet_sequence = None
        # Find the corresponding dictionary entity in packets_dict
        for message in self.all_packets_dict:
            if message['id'] == message_id:
                message_block = message
                # Fetching packet sequence for the given message id sorted by sequence number
                packet_sequence = sorted(message['packets'], key=itemgetter('seq_num'))
                break

        # If message identifier is found
        if message_block is not None:
            self.log.debug("Sorted packet sequence for message id " + message_id + " is: " + str(packet_sequence))
            # If the last packet in packet list is the final packet
            # And the number of packets in the list is equal to the sequence number of final package
            # We can wrap up this stream and remove this message from buffer
            if packet_sequence[-1]['is_final'] == True and int(packet_sequence[-1]['seq_num']) == len(packet_sequence):
                self.all_packets_dict.remove(message_block)
                message_data = ''
                for packet in packet_sequence:
                    # Concatenating all the data blocks
                    # Note that each data block has a "\n" at the end and the final one has "\n\n" which will be stripped by parse_broadcast function later
                    message_data += packet['data']
                return True, message_data

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

