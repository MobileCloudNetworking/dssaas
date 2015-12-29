__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

from socket import *
import time
import logging
from Config import *
import threading
from operator import itemgetter
import random
import zlib
import md5
import base64

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class BroadcastManager():
    #TODO: Sending thread, recieving thread
    def __init__(self, file_manager, torrent_manager,tracker_manager):
        self.broadcast_port = 6977
        self.broadcast_ip = '192.168.20.255'
        self.tm = torrent_manager
        self.tkm = tracker_manager
        self.fm = file_manager
        self.conf = Config()
        self.path = self.conf.get('main', 'path')
        self.payload_size = int(self.conf.get('main', 'udp_payload_size'))
        #check
        self.log = logging.getLogger(self.conf.get('log', 'name'))
        #self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        #self.log.debug('TrackerList:' + str(self.tkm.get_tracker_list()))

        # A list of dictionaries that contains message ID, a list of corresponding packets for that ID and an expiration time
        # Example: [{'id':'RANDOME_MESSAGE_ID', 'packets':[{'seq_num':'Integer', 'data':'String', 'is_final':'Boolean'}, packet2, packet3, ...], 'timeout':'Current time + self.message_timeout'}]
        self.all_packets_dict = []
        self.message_timeout = 600# Seconds

    @threaded
    def send_broadcast_message(self):
        while True:
            s = socket(AF_INET, SOCK_DGRAM)
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            data = str(self.tkm.get_self_tracker()['url']) + '!' + repr(time.time()) + '!'
            for torrent in self.tm.get_removed_torrent_list():
                self.log.debug('Checking removed torrent: ' + str(torrent))
                data += str(torrent.split('.')[0] + '.torrent') + ','
            for torrent in self.tm.get_torrent_list():
                self.log.debug('Checking torrent: ' + str(torrent))
                data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
            cdata = zlib.compress(data)
            self.log.debug('Data size is ' + str(len(data))+ ' and data compressed size is ' +str(len(cdata)))
            md5_handler = md5.new()
            md5_handler.update(cdata)
            signature = md5_handler.digest()
            b64signature = base64.b64encode(signature)
            self.log.debug('Data compressed base signature is ' + b64signature)
            #data += '\n'
            #self.log.debug(data)
            #building the udp packets and sending them separately
            stream_id = str(int(random.random()*10000 - 1))
            seq = 1
            data_index = 0
            packet = ''
            while data_index < len(cdata):
                #Header is fixed = 6 for id, 4 for seq, 4 for len and 1 for is_final
                packet_header_size = 6 + 4 + 4 + 1
                remaining = len(cdata) - data_index
                #self.log.debug('SENDING MESSAGE: Packet header size = ' + str(packet_header_size) + ' and remaining = ' + str(remaining))
                #available size for payload is upd_size - header - ending char(1 char)
                if (self.payload_size - packet_header_size) < remaining:
                    #still more than 1 packet to be sent
                    packet = stream_id.zfill(6) + str(seq).zfill(4) + str(self.payload_size - packet_header_size).zfill(4) \
                             + '0' + cdata[data_index:data_index + self.payload_size - packet_header_size]
                    data_index += self.payload_size - packet_header_size
                else:
                    packet = stream_id.zfill(6) + str(seq).zfill(4) + str(len(cdata[data_index:])).zfill(4) \
                             + '1' + cdata[data_index:]
                    data_index = len(cdata)
                #self.log.debug('SENDING MESSAGE: ' + str(packet.replace('\n','*EOL*')))
                s.sendto(packet, (self.broadcast_ip, self.broadcast_port))
                seq += 1
            time.sleep(30)

    @threaded
    def sendAmazon_broadcast_message(self):
        while True:
            s = socket(AF_INET, SOCK_DGRAM)
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            data = str(self.tkm.get_self_tracker()['url']) + '!' + repr(time.time()) + '!'
            for torrent in self.tm.get_removed_torrent_list():
                self.log.debug('Checking removed torrent: ' + str(torrent))
                data += str(torrent) + ','
            for torrent in self.tm.get_torrent_list():
                self.log.debug('Checking torrent: ' + str(torrent))
                data += '!' + str(torrent) + '!' + str(self.tm.get_torrent_content(torrent))
            cdata = zlib.compress(data)
            #data += '\n'
            #self.log.debug(data)
            #building the udp packets and sending them separately
            stream_id = str(int(random.random()*10000 - 1))
            seq = 1
            data_index = 0
            packet = ''
            while data_index < len(cdata):
                #5 first chars for ID, 3 chars for seq
                packet_header_size = len(stream_id) + len(str(seq)) + 2
                remaining = len(cdata) - data_index
                #self.log.debug('SENDING MESSAGE: Packet header size = ' + str(packet_header_size) + ' and remaining = ' + str(remaining))
                #available size for payload is upd_size - header - ending char(1 char)
                if (self.payload_size - packet_header_size - 1) < remaining:
                    #still more than 1 packet to be sent
                    packet = stream_id.zfill(6) + str(seq).zfill(4) + str(self.payload_size - packet_header_size - 1).zfill(4) \
                             + '0' + cdata[data_index:data_index + self.payload_size - packet_header_size - 1]
                    data_index += self.payload_size - packet_header_size - 1
                else:
                    packet = stream_id.zfill(6) + str(seq).zfill(4) + str(self.payload_size - packet_header_size - 1).zfill(4) \
                             + '1' + cdata[data_index:]
                    data_index = len(cdata)
                for i in range(4, 100):
                    s.sendto(packet, ('172.30.2.' + str(i), self.broadcast_port))
                seq += 1
            time.sleep(30)

    @threaded
    def receive_broadcast_message(self):
        s = socket(AF_INET,SOCK_DGRAM) # UDP
        s.bind(('0.0.0.0', self.broadcast_port))
        while True:
            data, addr = s.recvfrom(4096)# Maximum allowed size is 4096 bytes

            # Decouple message sections
            message_id, packet_seq_num, packet_data, final_flag = self.parse_packet(addr, data)

            # Proceed with pushing the message if decouple successful
            if message_id is not None:
                # Push to packet dict
                self.push_to_packets_dict(message_id, packet_seq_num, packet_data, final_flag, time.time())

                # Check the packet dict if we are done with this sequence of packets
                is_complete, message_data = self.is_stream_complete(message_id)

                # All sequences are received, parse the message
                if(is_complete):
                    self.log.debug("Message with ID " + message_id + " is ready, parsing it ...")
                    #self.log.debug("Message data: " + str(message_data))
                    self.parse_broadcast_message(message_data)
            else:
                self.log.debug("Invalid packet received")

    @threaded
    # Checks the time out for all pushed messages and removes them all in case they're expired
    def remove_expired_streams(self):
        while True:
            if len(self.all_packets_dict) > 0:
                current_time = time.time()
                expired_ones = [message for message in self.all_packets_dict if current_time >= message['timeout']]
                for message in expired_ones:
                        self.all_packets_dict.remove(message)
            time.sleep(self.message_timeout)

    # Gets a packet and returns message identifier, packet sequence number and its data
    def parse_packet(self, addr, data):
        # Expected packet structure
        # MESSAGE_ID!PACKET_SEQUENCE!REST_OF_PACKET_DATA
        try:
            message_id = data[:6]
            sequence = data[6:10]
            length = data[10:14]
            is_final = data[14:15]
            content = data[15:]
            self.log.debug('MESSAGE RECEIVED: ID= ' + message_id + ' seq= ' + sequence + ' length= ' + length + ' is_final= ' + str(is_final) + ' real_content_lengt= ' + str(len(content)))
            if len(content) != int(length):
                self.log.debug("Discarding packet due to invalid format")
                return None, None, None, None
            else:
                return message_id, int(sequence), content, bool(int(is_final))
        except Exception as e:
            self.log.warning("Exception while parsing packet data: " + str(e))
            return None, None, None, None

    # Gets message identifier, packet sequence number and its data, then pushes it into packets dictionary
    def push_to_packets_dict(self, message_id, sequence, data, final_flag, time):
        msg_id = message_id
        msg_arrival_time = time
        new_packet = {'seq_num': sequence, 'data': data, 'is_final': final_flag}

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
            #self.log.debug("Sorted packet sequence for message id " + message_id + " is: " + str(packet_sequence))
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
        # udp://172.30.2.46:6969/announce!1450430624.7613!mytorrent.torrent!ZDg6YW5ub3VuY2UyOTp1ZHA6Ly9sb2NhbGhvc3Q6Njk2OS9hbm5vdW5jZTc6Y29tbWVudDQ6VGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDI4NzIxNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lODp0ZXN0LnR4dDEyOnBpZWNlIGxlbmd0aGkxNjM4NGU2OnBpZWNlczgwOv2TLO5kpmZ7SZq+v6i5Z01VNmm3IxcyPZRmLZeuJ7Gl+ZC0C9egeh99D/42XYE55Q0zaSgCrP+BIY1T7qr/muq34oDUxWetqRw89wWpSlcdZWU=!my.torrent!ZDg6YW5ub3VuY2UxMToxNzIuMzAuMi40Njc6Y29tbWVudDQ6dGVzdDEwOmNyZWF0ZWQgYnkyMDpsaWJ0b3JyZW50IDAuMTYuMTMuMDEzOmNyZWF0aW9uIGRhdGVpMTQ1MDQzMDYyNGU0OmluZm9kNjpsZW5ndGhpNTgxOTZlNDpuYW1lNzpteS5maWxlMTI6cGllY2UgbGVuZ3RoaTE2Mzg0ZTY6cGllY2VzODA6/ZMs7mSmZntJmr6/qLlnTVU2abcjFzI9lGYtl64nsaX5kLQL16B6H30P/jZdgTnlDTNpKAKs/4EhjVPuqv+a6rfigNTFZ62pHDz3BalKVx1lZQ==
        self.log.debug('Data compressed size is ' + str(len(message)))
        md5_handler = md5.new()
        md5_handler.update(message)
        signature = md5_handler.digest()
        b64signature = base64.b64encode(signature)
        self.log.debug('Data compressed base signature is ' + b64signature)


        msg_list = (zlib.decompress(message)).replace('\n', '').split('!')
        #self.log.debug("Stripped message data: " + str(msg_list))

        # Manage deleted files block
        self.log.debug("DELETED TORRENTS BLOCK " + str(msg_list[2]))
        if len(msg_list[2]) > 0:
            deleted_list = msg_list[2].split(',')
            deleted_list.pop()
            self.log.debug("Got the list of deleted torrents from broadcast message:" + str(deleted_list))
            for deleted_file in deleted_list:
                self.tm.delete_torrent(torrent_name=deleted_file)
        # Manage deleted files block end

        # Manage tracker list block
        tracker_struct = {'url': msg_list[0], 'timestamp': msg_list[1]}
        is_new = self.tkm.update_tracker(tracker_struct)
        if is_new:
            self.tm.recreate_all_torrents()
        # Manage tracker list block end

        # Manage torrents content block
        for index in range (3, len(msg_list), 2):
            #check if I do have the torrent file
            torrent_name =  msg_list[index]
            torrent_content = msg_list[index + 1]
            self.tm.save_torrent(torrent_name, torrent_content)
        # Manage torrents content block end

        #check
        #self.log.debug('TorrentList:' + str(self.tm.get_torrent_list()))
        #self.log.debug('TrackerList:' + str(self.tkm.get_tracker_list()))

