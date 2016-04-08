#!/usr/bin/env python

#
#      Resource Aware VNF Agnostic (RAVA) NFV Orchestration Method/System
#
# file: mcn_zabbix.py
#
#               NEC Europe Ltd. PROPRIETARY INFORMATION
#
# This software is supplied under the terms of a license agreement or
# nondisclosure agreement with NEC Europe Ltd. and may not be copied or
# disclosed except in accordance with the terms of that agreement. The software
# and its source code contain valuable trade secrets and confidential
# information which have to be maintained in confidence.
# Any unauthorized publication, transfer to third parties or duplication of the
# object or source code - either totally or in part - is prohibited.
#
#      Copyright (c) 2015 NEC Europe Ltd. All Rights Reserved.
#
# Authors: Carlos Goncalves, <carlos.goncalves@neclab.eu>
#
# NEC Europe Ltd. DISCLAIMS ALL WARRANTIES, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE AND THE WARRANTY AGAINST LATENT
# DEFECTS, WITH RESPECT TO THE PROGRAM AND THE ACCOMPANYING
# DOCUMENTATION.
#
# No Liability For Consequential Damages IN NO EVENT SHALL NEC Europe
# Ltd., NEC Corporation OR ANY OF ITS SUBSIDIARIES BE LIABLE FOR ANY
# DAMAGES WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS
# OF BUSINESS PROFITS, BUSINESS INTERRUPTION, LOSS OF INFORMATION, OR
# OTHER PECUNIARY LOSS AND INDIRECT, CONSEQUENTIAL, INCIDENTAL,
# ECONOMIC OR PUNITIVE DAMAGES) ARISING OUT OF THE USE OF OR INABILITY
# TO USE THIS PROGRAM, EVEN IF NEC Europe Ltd. HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGES.
#
#     THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.
#


import time
from datetime import datetime
from pyzabbix import ZabbixAPI
import config
import mcn_logging
from node import Node
from phys_node import PhysNode

LOG = mcn_logging.config_logger(config.LOG_LEVEL)

class McnZabbix:

    def __init__(self, server, user, password):
        self.zapi = ZabbixAPI(server)
        self.zapi.login(user, password)

    def get_hosts_by_name(self, host_names):
        return self.zapi.host.get(filter={"host": host_names}, output='extend')

    def get_host_id(self, host_name):
        self.get_hosts_by_name(self, host_name)[0]['hostid']

    def get_hosts_by_id(self, host_ids):
        return self.zapi.host.get(hostids=host_ids, output='extend')

    def get_host_by_id(self, host_id):
        return self.get_hosts_by_id(host_id)[0]

    def get_item_by_name(self, host_name, item_name):
        return self.zapi.item.get(host=host_name, filter={"key_":
            item_name}, output='extend')[0] # assume item names are unique

    def get_items_by_id(self, host_name, item_ids):
        return self.zapi.item.get(host=host_name, itemids=item_ids,
                output='extend')

    def get_item_by_id(self, host_name, item_id):
        return self.get_items_by_id(host_name, item_id)[0]

    def get_history(self, host_name, item, time_from,
            time_till=time.mktime(datetime.now().timetuple()),
            output='extend', limit='100'):

        if not isinstance(item, dict):
            item = self.get_item_by_name(host_name, item)

            item_id = item['itemid']
            history = item['value_type']

            return self.zapi.history.get(host=host_name,
                    itemids=item_id,
                    time_from=time_from,
                    time_till=time_till,
                    output=output,
                    limit=limit,
                    history=history
                    )

    def get_history_many(self, hosts, items, time_from,
            time_till=time.mktime(datetime.now().timetuple()),
            output='extend', limit='100', uuid_enabled=False):

        hosts_map = []

        if uuid_enabled:
            zhosts = [h for h in self.get_hosts_by_name([host.name.replace('_','-') for host in hosts])]
            for instance in hosts:
                for host in zhosts:
                    if instance.name.replace('_','-') == host['host']:
                        data = {"uuid": instance.id, "host_info": host}
                        hosts_map.append(data)
                        break
        else:
            hosts_map = [h for h in self.get_hosts_by_name(hosts)]

        history = {}
        for host in hosts_map:
            if uuid_enabled:
                host_id = host['host_info']['hostid']
                host_name = host['host_info']['host']
                history[host['uuid']] = []
            else:
                host_id = host['hostid']
                host_name = host['host']
                history[host_name] = []

            for item_name in items:
                item = self.get_item_by_name(host_name, item_name)
                item_id = item['itemid']
                item_history = item['value_type']
                result = self.zapi.history.get(
                        hostids=host_id,
                        itemids=item_id,
                        time_from=int(time_from),
                        time_till=int(time_till),
                        output=output,
                        limit=limit,
                        history=item_history
                        )
                for res_item in result:
                    res_item['source_host'] = host_name 
                #print "data for " + item_name + " is " + str(result)
                if uuid_enabled:
                    history[host['uuid']].extend(result)
                else:
                    history[host_name].extend(result)
        return history

    def to_nodes(self, history, type='vm'):
        nodes = {}
        for host_name, items in history.iteritems():
            # check if it is a PM (PhysNode) or a VM (Node)
            if type == 'pm':
                n = PhysNode(id=host_name)
            else:
                n = Node(id=host_name)
            n.type = type

            # translate Zabbix's item key names to Node's attribute names
            for item in items:
                #print str(item)
                item_name = str(self.get_item_by_id(item['source_host'],
                    item['itemid'])['key_'])
                if item_name == config.CPU_IDLE:
                    item_name = 'cpu_idle'
                elif item_name == config.CPU_NUM:
                    item_name = 'cpu_cores'
                elif item_name == config.MEM_TOTAL:
                    item_name = 'mem_total'
                elif item_name == config.MEM_AVAILABLE:
                    item_name = 'mem_available'
                elif item_name == config.NET_IN_EM1:
                    item_name = 'net_in'
                elif item_name == config.NET_OUT_EM1:
                    item_name = 'net_out'
                elif item_name == config.NET_SPEED_EM1:
                    item_name = 'net_speed'
                elif item_name == config.NET_IN_ETH0:
                    item_name = 'net_in'
                elif item_name == config.NET_OUT_ETH0:
                    item_name = 'net_out'
                elif item_name == config.NET_SPEED_ETH0:
                    item_name = 'net_speed'
                else:
                    raise KeyError('Item name %s unknown' % item_name)

                # calculate average
                prev_value = getattr(n, item_name, None)
                try:
                    # try as integer type
                    curr_value = int(item['value'])
                except ValueError:
                    # if failed to convert, fallback to float
                    curr_value = float(item['value'])

                if prev_value is not None:
                    # there's a previous value; calculate average between them
                    avg = (prev_value + curr_value) / 2
                else:
                    # first value, average is this first value itself
                    avg = curr_value
                setattr(n, item_name, avg)

            # add node to nodes dict where dict key is node id
            nodes[n.id] = n

        return nodes


zabbix = McnZabbix(config.ZABBIX_SERVER, config.ZABBIX_USER, config.ZABBIX_PASSWORD)
