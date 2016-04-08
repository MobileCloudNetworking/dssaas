#!/usr/bin/env python

#
#      Resource Aware VNF Agnostic (RAVA) NFV Orchestration Method/System
#
# file: node.py
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


import config
import mcn_zabbix
import mcn_logging

LOG = mcn_logging.config_logger(config.LOG_LEVEL)

class Node(object):

    valid_attrs = ('id', 'type', 'timestamp', 'cpu_cores',
            'cpu_idle', 'mem_total', 'mem_used', 'mem_available', 'net_in',
            'net_out', 'net_speed',
            'cpu_util', 'mem_util', 'net_in_util', 'net_out_util',
            'cpu_rras', 'mem_rras', 'net_in_rras', 'net_out_rras', )

    def __init__(self, **kwargs):
        # assume it's of virtual machine type
        self.type = 'vm'

        # FIXME: find a way to get NIC link speed for VMs. In the meantime,
        # assuming it's 1000 Mbps
        self.net_speed = 1000

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return "%r" % (self.__dict__)

    def __str__(self):
        return self.id

    def __setattr__(self, name, value):
        # convert from item id to item name/key
        if name.isdigit():
            name = mcn_zabbix.zabbix.get_item_by_id(self.id, name)['key_']

        if name not in self.valid_attrs:
            raise KeyError('Key %s unknown', name)

        # convert unicode to str
        if isinstance(value, unicode):
            value = str(value)

        super(Node, self).__setattr__(name, value)

    def calculate_utils(self):
        # CPU RRAS
        self.cpu_util = (100 - self.cpu_idle)

        # Network RRAS
        # NOTE: NICs are full duplex.
        self.net_in_util = (self.net_in * 100 / (self.net_speed * 1024 * 1024))
        self.net_out_util = (self.net_out * 100 / (self.net_speed * 1024 * 1024))

        # Memory RRAS
        self.mem_util = 100 - ((self.mem_available * 100) / self.mem_total)

    def calculate_rrases(self):
        if config.RRU_NAME == 'cpu':
            self.mem_rras = self.mem_util - self.cpu_util
            self.net_in_rras = self.net_in_util - self.cpu_util
            self.net_out_rras = self.net_out_util - self.cpu_util
        elif config.RRU_NAME == 'memory':
            self.cpu_rras = self.cpu_util - self.mem_util
            self.net_in_rras = self.net_in_util - self.mem_util
            self.net_out_rras = self.net_out_util - self.mem_util
        elif config.RRU_NAME == 'net_in':
            self.cpu_rras = self.cpu_util - self.net_in_util
            self.mem_rras = self.mem_util - self.net_in_util
            self.net_out_rras = self.net_out_util - self.net_in_util
        elif config.RRU_NAME == 'net_out':
            self.cpu_rras = self.cpu_util - self.net_out_util
            self.mem_rras = self.mem_util - self.net_out_util
            self.net_in_rras = self.net_in_util - self.net_out_util
        else:
            raise ValueError("RRU name '%s' is invalid", config.RRU_NAME)
