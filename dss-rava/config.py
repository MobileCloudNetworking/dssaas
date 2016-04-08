#!/usr/bin/env python

#
#      Resource Aware VNF Agnostic (RAVA) NFV Orchestration Method/System
#
# file: config.py
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


import logging

# Zabbix
ZABBIX_SERVER = 'http://160.85.4.28/zabbix'
ZABBIX_USER = 'admin'
ZABBIX_PASSWORD = 'zabbix'

# Log level
LOG_LEVEL = logging.DEBUG

# Zabbix items
CPU_NUM = 'system.cpu.num'
CPU_IDLE = 'system.cpu.util[,idle]'
MEM_TOTAL = 'vm.memory.size[total]'
MEM_AVAILABLE = 'vm.memory.size[available]'
NET_IN_EM1 = 'net.if.in[enp1s0f0]'
NET_OUT_EM1 = 'net.if.out[enp1s0f0]'
NET_SPEED_EM1 = 'net.speed[enp1s0f0]'
NET_IN_ETH0 = 'net.if.in[eth0]'
NET_OUT_ETH0 = 'net.if.out[eth0]'
NET_SPEED_ETH0 = 'net.speed[eth0]'

# PM metrics to monitor
ZABBIX_PM_ITEMS = [CPU_NUM, CPU_IDLE, MEM_TOTAL, MEM_AVAILABLE, NET_IN_EM1,
                   NET_OUT_EM1]#, NET_SPEED_EM1]
#ZABBIX_PM_ITEMS = [CPU_IDLE, MEM_TOTAL, MEM_AVAILABLE]
# VM metrics to monitor
ZABBIX_VM_ITEMS = [CPU_NUM, CPU_IDLE, MEM_TOTAL, MEM_AVAILABLE, NET_IN_ETH0,
                   NET_OUT_ETH0]#, NET_SPEED_ETH0]
#ZABBIX_VM_ITEMS = [CPU_IDLE, MEM_TOTAL, MEM_AVAILABLE]

# OpenStack testbed info
OS_AUTH_URL = 'http://bart.cloudcomplab.ch:5000/v2.0'
OS_USERNAME = 'test'
OS_PASSWORD = 'test'
OS_TENANT_NAME= 'STT-DSS'
OS_REGION_NAME= 'RegionOne'
NOVA_VERSION= '2'

MONITORING_EPOCH = 2 * 60 # seconds
ANALYTIC_EPOCH = 1 # how many monitoring epoch runs, where each run is of duration MONITORING_EPOCH

# RRU can be: cpu, memory, net_in, net_out
RRU_NAME = 'cpu'
