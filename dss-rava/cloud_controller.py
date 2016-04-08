#!/usr/bin/env python

#
#      Resource Aware VNF Agnostic (RAVA) NFV Orchestration Method/System
#
# file: cloud_controller.py
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


from novaclient.client import Client
from novaclient.v2 import hosts
from novaclient import utils as nova_utils

import config
import mcn_logging

LOG = mcn_logging.config_logger(config.LOG_LEVEL)

class McnNova:

    def __init__(self, novaclient_v, auth_url, user, password, tenant, region_name):
        self.client = Client(novaclient_v, user, password, tenant, auth_url, region_name=region_name)

    def get_hypervisors(self, hostname='cloudcomplab.ch', servers=True):
        # all compute node names are prefixed/start with'compute' followed by a
        # number (e.g. 'compute1', 'compute2', ...)
        hypers = self.client.hypervisors.search(hostname, servers)
        return hypers

    def get_hypervisor_instances(self, hypers=None):
        if hypers is None:
            hypers = self.get_hypervisors(servers=True)

        class InstanceOnHyper(object):
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        instances = []
        for hyper in hypers:
            hyper_host = hyper.hypervisor_hostname
            hyper_id = hyper.id
            if hasattr(hyper, 'servers'):
                instances.extend([InstanceOnHyper(id=serv['uuid'],
                                                  name=serv['name'],
                                                  hypervisor_hostname=hyper_host,
                                                  hypervisor_id=hyper_id)
                                 for serv in hyper.servers])
        
        filtered_instances = []
        for instance in instances:
            try:
                instance.name = self.client.servers.find(id=instance.id).name
                if "cms" in instance.name or "mcr" in instance.name:
                    filtered_instances.append(instance)
            except Exception as e:
                #print "Unbale to find instance name for instance ID: " + instance.id
                pass
        
        #print str(filtered_instances)
        return filtered_instances

    def live_migrate(self, vm_id, pm_name):
        self.client.servers.live_migrate(vm_id, pm_name, block_migration=False, disk_over_commit=False)
