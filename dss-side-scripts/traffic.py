__author__ = 'Santi'

'''
Packet sniffer in python using the pcapy python library
Project website
http://oss.coresecurity.com/projects/pcapy.html
'''

import socket
from struct import *

import pcapy
import sys
from time import gmtime, strftime, sleep
import web
import threading


global results

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

class NetCap:

    def __init__(self,argv):
        global results
        results = {}
        self.ports_filter = []
        for i in range(2, len(sys.argv)):
            self.ports_filter.append(sys.argv[i])
            results[sys.argv[i]] = {"elems": 0, "times": [], "inbound": [], "outbound": [], "inbound_color": "red", "outbound_color": "blue"}
        print "Ports to be filtered: " + str(self.ports_filter)

    @threaded
    def completelist(self,lock):
        global results
        global res_requested
        while True:
            if res_requested:
                for key in results:
                    results[key]["elems"] = 0
                    results[key]["times"] = []
                    results[key]["inbound"] = []
                    results[key]["outbound"] = []
                res_requested = False

            time = strftime("%H:%M:%S", gmtime())
            for key in results:
                lock.acquire()
                if results[key]["elems"] == 0:
                    results[key]["elems"] += 1
                    results[key]["times"].append(time)
                    results[key]["inbound"].append(0)
                    results[key]["outbound"].append(0)
                else:
                    if results[key]["times"][results[key]["elems"] - 1] != time:
                        results[key]["elems"] += 1
                        results[key]["times"].append(time)
                        results[key]["inbound"].append(0)
                        results[key]["outbound"].append(0)
                if results[key]["elems"] > 50:
                    results[key]["elems"] -= 1
                    results[key]["times"].pop(0)
                    results[key]["inbound"].pop(0)
                    results[key]["outbound"].pop(0)
                lock.release()
                sleep(0.5)

    @threaded
    def sniff(self,lock):
        global results
        global res_requested
        res_requested = False
        # list all devices
        devices = pcapy.findalldevs()
        print devices

        #ask user to enter device name to sniff
        print "Available devices are :"
        for d in devices:
            print d

        dev = raw_input("Enter device name to sniff : ")

        print "Sniffing device " + dev

        '''
        open device
        # Arguments here are:
        #   device
        #   snaplen (maximum number of bytes to capture _per_packet_)
        #   promiscious mode (1 for true)
        #   timeout (in milliseconds)
        '''
        cap = pcapy.open_live(dev, 65536, 1, 0)

        #start sniffing packets
        while (1):
            try:
                (header, packet) = cap.next()
                #print ('%s: captured %d bytes, truncated to %d bytes' %(datetime.datetime.now(), header.getlen(), header.getcaplen()))
                self.parse_packet(packet, self.ports_filter,lock)
            except:
               print "Error parsing..."
               pass



    # Convert a string of 6 characters of ethernet address into a dash separated hex string
    def eth_addr(self,a):
        b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(a[0]), ord(a[1]), ord(a[2]), ord(a[3]), ord(a[4]), ord(a[5]))
        return b


#function to parse a packet
    def parse_packet(self, packet, ports_filter,lock):
        global results
        global res_requested
        #parse ethernet header
        eth_length = 14

        eth_header = packet[:eth_length]
        eth = unpack('!6s6sH', eth_header)
        eth_protocol = socket.ntohs(eth[2])
        #print 'Destination MAC : ' + self.eth_addr(packet[0:6]) + ' Source MAC : ' + self.eth_addr(
        #    packet[6:12]) + ' Protocol : ' + str(eth_protocol)

        #Parse IP packets, IP Protocol number = 8
        if eth_protocol == 8:
            #Parse IP header
            #take first 20 characters for the ip header
            ip_header = packet[eth_length:20 + eth_length]

            #now unpack them :)
            iph = unpack('!BBHHHBBH4s4s', ip_header)

            version_ihl = iph[0]
            version = version_ihl >> 4
            ihl = version_ihl & 0xF

            iph_length = ihl * 4

            ttl = iph[5]
            protocol = iph[6]
            s_addr = socket.inet_ntoa(iph[8]);
            d_addr = socket.inet_ntoa(iph[9]);

        #    print 'Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(
        #        ttl) + ' Protocol : ' + str(protocol) + ' Source Address : ' + str(
        #        s_addr) + ' Destination Address : ' + str(d_addr)

            #TCP protocol
            if protocol == 6:
                t = iph_length + eth_length
                tcp_header = packet[t:t + 20]

                #now unpack them :)
                tcph = unpack('!HHLLBBHHH', tcp_header)

                source_port = tcph[0]
                dest_port = tcph[1]
                sequence = tcph[2]
                acknowledgement = tcph[3]
                doff_reserved = tcph[4]
                tcph_length = doff_reserved >> 4

        #        print 'Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Sequence Number : ' + str(
        #            sequence) + ' Acknowledgement : ' + str(acknowledgement) + ' TCP header length : ' + str(tcph_length)

                h_size = eth_length + iph_length + tcph_length * 4
                data_size = len(packet) - h_size

                #get data from the packet
                data = packet[h_size:]

                #print 'Data : ' + data
                lock.acquire()

                if str(source_port) in ports_filter:
                    time = strftime("%H:%M:%S", gmtime())
                    if results[str(source_port)]["elems"] == 0:
                        results[str(source_port)]["elems"] += 1
                        results[str(source_port)]["times"].append(time)
                        results[str(source_port)]["inbound"].append(len(packet))
                        results[str(source_port)]["outbound"].append(0)
                    else:
                        if results[str(source_port)]["times"][results[str(source_port)]["elems"] - 1] != time:
                            results[str(source_port)]["elems"] += 1
                            results[str(source_port)]["times"].append(time)
                            results[str(source_port)]["inbound"].append(len(packet))
                            results[str(source_port)]["outbound"].append(0)
                        else:
                            results[str(source_port)]["inbound"][results[str(source_port)]["elems"] - 1] += len(packet)

                if str(dest_port) in ports_filter:
                    time = strftime("%H:%M:%S", gmtime())
                    if results[str(dest_port)]["elems"] == 0:
                        results[str(dest_port)]["elems"] += 1
                        results[str(dest_port)]["times"].append(time)
                        results[str(dest_port)]["inbound"].append(0)
                        results[str(dest_port)]["outbound"].append(len(packet))
                    else:
                        if results[str(dest_port)]["times"][results[str(dest_port)]["elems"] - 1] != time:
                            results[str(dest_port)]["elems"] += 1
                            results[str(dest_port)]["times"].append(time)
                            results[str(dest_port)]["inbound"].append(0)
                            results[str(dest_port)]["outbound"].append(len(packet))
                        else:
                            results[str(dest_port)]["outbound"][results[str(dest_port)]["elems"] - 1] += len(packet)

                lock.release()


            #ICMP Packets
            elif protocol == 1:
                u = iph_length + eth_length
                icmph_length = 4
                icmp_header = packet[u:u + 4]

                #now unpack them :)
                icmph = unpack('!BBH', icmp_header)

                icmp_type = icmph[0]
                code = icmph[1]
                checksum = icmph[2]

#                print 'Type : ' + str(icmp_type) + ' Code : ' + str(code) + ' Checksum : ' + str(checksum)

                h_size = eth_length + iph_length + icmph_length
                data_size = len(packet) - h_size

                #get data from the packet
                data = packet[h_size:]

#                print 'Data : ' + data

            #UDP packets
            elif protocol == 17:
                u = iph_length + eth_length
                udph_length = 8
                udp_header = packet[u:u + 8]

                #now unpack them :)
                udph = unpack('!HHHH', udp_header)

                source_port = udph[0]
                dest_port = udph[1]
                length = udph[2]
                checksum = udph[3]

#                print 'Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Length : ' + str(
#                    length) + ' Checksum : ' + str(checksum)

                h_size = eth_length + iph_length + udph_length
                data_size = len(packet) - h_size

                #get data from the packet
                data = packet[h_size:]

#                print 'Data : ' + data

                lock.acquire()

                if str(source_port) in ports_filter:
                    time = strftime("%H:%M:%S", gmtime())
                    if results[str(source_port)]["elems"] == 0:
                        results[str(source_port)]["elems"] += 1
                        results[str(source_port)]["times"].append(time)
                        results[str(source_port)]["inbound"].append(len(packet))
                        results[str(source_port)]["outbound"].append(0)
                    else:
                        if results[str(source_port)]["times"][results[str(source_port)]["elems"] - 1] != time:
                            results[str(source_port)]["elems"] += 1
                            results[str(source_port)]["times"].append(time)
                            results[str(source_port)]["inbound"].append(len(packet))
                            results[str(source_port)]["outbound"].append(0)
                        else:
                            results[str(source_port)]["inbound"][results[str(source_port)]["elems"] - 1] += len(packet)

                if str(dest_port) in ports_filter:
                    time = strftime("%H:%M:%S", gmtime())
                    if results[str(dest_port)]["elems"] == 0:
                        results[str(dest_port)]["elems"] += 1
                        results[str(dest_port)]["times"].append(time)
                        results[str(dest_port)]["inbound"].append(0)
                        results[str(dest_port)]["outbound"].append(len(packet))
                    else:
                        if results[str(dest_port)]["times"][results[str(dest_port)]["elems"] - 1] != time:
                            results[str(dest_port)]["elems"] += 1
                            results[str(dest_port)]["times"].append(time)
                            results[str(dest_port)]["inbound"].append(0)
                            results[str(dest_port)]["outbound"].append(len(packet))
                        else:
                            results[str(dest_port)]["outbound"][results[str(dest_port)]["elems"] - 1] += len(packet)

                lock.release()




            #some other IP packet like IGMP
            else:
                pass
 #               print 'Protocol other than TCP/UDP/ICMP'

#            print

class get_values:

    def GET(self):
        global results
        global res_requested
        res_requested = True
        return str(results).replace('\'','"')


if __name__ == "__main__":
    lock = threading.Lock()
    sniffer = NetCap(sys.argv)
    sniffer.sniff(lock)
    sniffer.completelist(lock)
    urls = ( '/values', 'get_values' )
    app = web.application(urls, globals())
    app.run()