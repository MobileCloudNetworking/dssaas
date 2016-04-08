#!/usr/bin/env python

#
#      Resource Aware VNF Agnostic (RAVA) NFV Orchestration Method/System
#
# file: main.py
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
#          Zarrar Yousaf, <zarrar.yousaf@neclab.eu>
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


import numpy
from numpy import arange,array,ones#,random,linalg
from scipy import stats
import numpy as np

import sys
import signal
import time
from datetime import datetime

import config
import utils
import mcn_logging
import mcn_zabbix
from cloud_controller import McnNova
from phys_node import PhysNode

LOG = mcn_logging.config_logger(config.LOG_LEVEL)

NOVA = McnNova(config.NOVA_VERSION, config.OS_AUTH_URL, config.OS_USERNAME,
               config.OS_PASSWORD, config.OS_TENANT_NAME, config.OS_REGION_NAME)


def signal_handler(signal, frame):
    print('Pressed Ctrl+C!')
    sys.exit(0)


def get_monitoring_epoch(time_till, time_from):

    # Physical machines / compute nodes
    hypers = NOVA.get_hypervisors()
    history = mcn_zabbix.zabbix.get_history_many(
            #[hv.hypervisor_hostname for hv in hypers],
            [hv.hypervisor_hostname.split('.')[0] for hv in hypers],
            config.ZABBIX_PM_ITEMS, time_from, time_till, limit=10)
    #print "Hypers history is: " + str(history)
    me_pm_nodes = mcn_zabbix.zabbix.to_nodes(history, type='pm')
    
    # Virtual machines / instances
    instances = NOVA.get_hypervisor_instances(hypers)
    history = mcn_zabbix.zabbix.get_history_many(instances,
            config.ZABBIX_VM_ITEMS, time_from, time_till, limit=10, uuid_enabled=True)
    #print "Instances history is: " + str(history)
    me_vm_nodes = mcn_zabbix.zabbix.to_nodes(history, type='vm')
    
    # Add VMs to PMs.vms list
    for hyper in hypers:
        if not hasattr(hyper, 'servers'):
            #LOG.debug("PM '%s' is NOT running any VM", hyper.hypervisor_hostname)
            continue
        #LOG.debug("PM '%s' contains VMs: %s", hyper.hypervisor_hostname, hyper.servers)
        for vm_id, vm_obj in me_vm_nodes.iteritems():
            for server in hyper.servers:
                if vm_id == server['uuid']:
                    me_pm_nodes[hyper.hypervisor_hostname.split('.')[0]].vms.append(vm_obj)
                    break
    #print "me_pm_nodes is:" + str(me_pm_nodes)
    #print "me_vm_nodes is:" + str(me_vm_nodes)
    return me_pm_nodes

def linearRegression (inList):
    xi = arange(0,len(inList))
    A = array([ xi, ones(len(inList))])
    # linearly generated sequence
    y = inList
    slope, intercept, r_value, p_value, std_err = stats.linregress(xi,y)
    #print 'slope', slope
    #print 'intercept', intercept
    #print 'r value', r_value
    #print  'p_value', p_value
    #print 'standard deviation', std_err
    #line = slope*xi+intercept
    #plot(xi,line,'r-',xi,y,'o')
    #show()
    return (slope, intercept)


def selectCandidateEntity(cand_entity_dict, entity_type):

    #This function returns the id of the target-VM and the candidate-PM
    #to which the target-VM will migrate/scale to. This function is called by the
    #decisionEngine() function.
    #NOTE: We use this function instead of Python's min()/max() function as this function
    #will return only one cadidate entity in case of race condition between candidates. On the
    #other hand min()/max() function will return both candidate entities with equal values.

    ref_dict = {}
    current_dict = {}
    ref_dict[cand_entity_dict.keys()[0]] = cand_entity_dict.itervalues().next()
    for key, val in cand_entity_dict.iteritems():
        current_dict.clear()
        current_dict[key] = val

        if current_dict == ref_dict:
            current_dict.clear()
        else:
            if entity_type == "vm":  #in case of VM we select the highly loaded VM
                if current_dict[key] > ref_dict.itervalues().next():
                    ref_dict.clear()
                    ref_dict[key] = val
                    current_dict.clear()
            if entity_type == "pm":        #in case of PM we select as cnadidate the node with lower affintiy with RRU
                if current_dict[key] < ref_dict.itervalues().next():
                    ref_dict.clear()
                    ref_dict[key] = val
                    current_dict.clear()
    return ref_dict.keys()



def decisionEngine(from_ae, dc_nodes):

    """
    This function parses the output from the Analytics Engine to and get the relevant parameters that it needs
    to enforce the orchestration management policy.
    """

    print "THIS IS THE DECISION ENGINE_2"
    ae_output = from_ae
    #print "TYPE OF ae_output: ", type(ae_output)
    dc_dict = dc_nodes
    print "IN DE: ",dc_dict, type(dc_dict)
    #print "Input data from AE: ", ae_output

    TARGET_NODE = "bart" #hardcoded
    TARGET_NIC_INGRESS_THRESH = 4000
    TARGET_NIC_NET_IN_AV_THRESH = 30000
    TARGET_NIC_NET_IN_SLOPE_THRESH = 2000
    TARGET_NIC_NET_IN_INTERCEPT_THRESH = 25000

    vm_io_rras_slope={}
    vm_netIn_rras_slope={}
    vm_netIn_rras_intercept={}

    #vm_io_rras_intercept={}
    candidate_Pm_dict = {} # this dict will contain the id (key) and "param value" of the candidate PM to which the Target VM will be migrated to. 
    candPm_av_netIn_rras_slope ={}# this dict will contain the id (key) and mean slope value of the netIn RRAS of the VMs in the rrascandidate PM to which the Target VM will be migrated to.
    candPm_av_netIn_rras_intercept ={}

    for key, values in ae_output.iteritems():
        if key == TARGET_NODE:
            print "#+#+#+#+ TARGET NODE IS: ", key
            print "+*+*+ TARGET NODE NET_IN_AV: ", values["net_in_av"]
            print "+*+*+ TARGET NODE NET_IN_SLOPE: ", values["net_in_slope"]
            print "+*+*TARGET NODE NET_IN_INTERCEPT: ", values["net_in_intercept"]
            if values["net_in_av"] > TARGET_NIC_NET_IN_AV_THRESH:
                print "Cycling thru VMs in different compute nodes"
                for targetPm, vmsList in dc_dict.iteritems():                    
                    if targetPm ==  TARGET_NODE:
                        #print "######++++++vmsList['vm_id']: ", vmsList['vm_id']
                        for i in range(0, len(vmsList['vm_id'])):

                            print "++VM_IDs IN TARGET NODE ARE *****: ",vmsList['vm_id'][i]
                            for key2, value2 in values.iteritems():
                                #print "++++INNER LOOPYYYY: ", key2
                                if key2 == vmsList['vm_id'][i]:
                                    #print "++++++VM VALUES ARE: ", value2
                                    print "++++++VM NET SLOPE is: ", value2["net_in_slope"]
                                    #vm_val_dict[key2]= value2["net_in_slope"]
                                    vm_io_rras_slope[key2]= np.absolute(value2["net_in_slope"]) #only the absolute value of slope

        else:
            print ""
            print "#+#+#+#+ CANDIATE NODE IS: ", key
            print "######## CANDIDATE NODE NET_IN_AV: ", values["net_in_av"]
            print "######## CANDIDATE NODE NET_IN_SLOPE: ", values["net_in_slope"]
            #print "########!! CANDIDATE VM IDs ARE: ", dc_dict[key], type(dc_dict[key]) # extracting the dict
            #print "########!! CANDIDATE VM IDs ARE: ", dc_dict[key]['vm_id'], type(dc_dict[key]['vm_id']) #extrqacting the list
            vms_netIn_rras_slope = []
            vms_netIn_rras_intercept = []
            for candPm, candVmList in dc_dict.iteritems():
                if candPm == key:
                    for i in range(0, len(dc_dict[key]['vm_id'])):
                        print "!!++!! VM_IDs IN CANDIDATE NODE ARE *****: ",dc_dict[key]['vm_id'][i]
                        for vmIdKey, value3 in values.iteritems():
                            if vmIdKey == dc_dict[key]['vm_id'][i]:
                                print "!!*#*#*#*#!! NET_IN_SLOPE for Cand. VM is: ", value3["net_in_slope"]
                                print "!!*#*#*#*#!! NET_IN_INTERCEPT for Cand. VM is: ", value3["net_in_intercept"]
                                print "+#+#+#+# NET_IN LIST: ", value3["net_in"]
                                print "+#+#+#+# CPU_UTIL LIST: ", value3["cpu_util"]

                                #pearsonCorr(value3["cpu_util"],value3["net_in"])
                                #print "!!*#*#*#*#!! MEM_SLOPE for Cand. VM is: ", value3["mem_slope"]
                                #print "!!*#*#*#*#!! MEM_INTERCEPT for Cand. VM is: ", value3["mem_intercept"]

                                vms_netIn_rras_slope.append(value3["net_in_slope"])
                                vms_netIn_rras_intercept.append(value3["net_in_intercept"])
            print "!!!!!!! vms_netIn_rras_slope: ", vms_netIn_rras_slope, key
            print "!!!!!!! vms_netIn_rras_intercept: ", vms_netIn_rras_intercept, key
            candidate_Pm_dict[key] = np.mean(vms_netIn_rras_slope)
            candPm_av_netIn_rras_intercept[key] = np.absolute(np.mean(vms_netIn_rras_intercept))
            #print " +!*!*!*!candidate_Pm_dict: ", candidate_Pm_dict


    print " +!*!*!*!candidate_Pm_dict: ", candidate_Pm_dict
    print "#+#+#+#+#candPm_av_netIn_rras_intercept: ", candPm_av_netIn_rras_intercept



    ##print "******vm_val_dict: ", vm_val_dict
    print "Slope of the Target VM's I/O RRAS values is: ", vm_io_rras_slope
    print "******candidate_Pm_dict: ", candidate_Pm_dict
    #print "CANDIDATE PM IS: ", selectCandidateEntity(candidate_Pm_dict, "pm")[0]
    print "TARGET VM IS: ", selectCandidateEntity(vm_io_rras_slope, "vm")[0]
    print "CANDIDATE HOST IS: ", selectCandidateEntity(candPm_av_netIn_rras_intercept, "pm")[0]
    candidate_vm = selectCandidateEntity(vm_io_rras_slope, "vm")[0]
    candidate_pm = selectCandidateEntity(candPm_av_netIn_rras_intercept, "pm")[0]
    NOVA.live_migrate(candidate_vm, candidate_pm)
    #print "CANDIDATE VM: ", [k for k, v in vm_val_dict.iteritems() if v == max(vm_val_dict.values())]
    #print "CANDIDATE PM: ", [k for k, v in candidate_Pm_dict.iteritems() if v == min(candidate_Pm_dict.values())]


def analytics_engine(ae_nodes):
    print "THIS IS THE ANALYTICS ENGINE"
    result = {}
    dc_dict = {}

    for me_nodes in ae_nodes:
        # remove timestamp key
        me_nodes.pop('timestamp')

    #==========for creating a dictionary for PMs and related VMs===============
        #print "++++ ME_NODES: ", me_nodes
        for pm_id, values in me_nodes.iteritems():
            if not pm_id in dc_dict:
                dc_dict[pm_id] = {}
                vm_id_list = []

                for vm in values.vms:
                    if vm.id not in vm_id_list:
                        vm_id_list.append(vm.id)
                    dc_dict[pm_id]['vm_id'] = vm_id_list
		    print "+++VM_ID_LIST: ", vm_id_list
                    print "+++DC_DICT: ", dc_dict
    #===========================================================

        for pm_id, value in me_nodes.iteritems():
            if not pm_id in result:
                result[pm_id] = {}

            for vm in value.vms:
                vm_id = vm.id
                if not vm_id in result[pm_id]:
                    result[pm_id][vm_id] = {}
                result[pm_id][vm_id].setdefault('net_in', []).append(vm.net_in) #added by zarrar 31.08.2015
                result[pm_id][vm_id].setdefault('cpu_util', []).append(vm.cpu_util) #added by zarrar 31.08.2015
                result[pm_id][vm_id].setdefault('net_in_rras',[]).append(vm.net_in_rras)
                result[pm_id][vm_id].setdefault('net_out_rras',[]).append(vm.net_out_rras)
                result[pm_id][vm_id].setdefault('mem_rras', []).append(vm.mem_rras)

    for pm_id, value in result.iteritems():

        for vm_id, vm_value in value.iteritems():
            mem_slope, mem_intercept = linearRegression(vm_value['mem_rras'])
            net_in_slope, net_in_intercept = linearRegression(vm_value['net_in_rras'])
            net_out_slope, net_out_intercept = linearRegression(vm_value['net_out_rras'])
            vm_value['mem_slope'] = mem_slope
            vm_value['mem_intercept'] = mem_intercept
            vm_value['net_in_slope'] = net_in_slope
            vm_value['net_out_slope'] = net_out_slope
            vm_value['net_in_intercept'] = net_in_intercept
            vm_value['net_out_intercept'] = net_out_intercept

    #ADDITIONS BY ZARRAR
    for pm_id, value in me_nodes.iteritems():
        result[pm_id]['net_speed'] = value.net_speed
        result[pm_id]['net_in'] = value.net_in
        result[pm_id]['net_out'] = value.net_out

    for me_nodes in ae_nodes:
        for pm_id, value in me_nodes.iteritems():
            #print "**net_in for pm_id: ", value['net_in'], pm_id
            result[pm_id].setdefault('net_in_val', []).append(value.net_in)
            result[pm_id].setdefault('net_out_val', []).append(value.net_out)
            #result[pm_id].setdefault('net_rras_val', []).append(value['net_rras'])

    for pm_id, value in result.iteritems():
        net_in_slope, net_in_intercept = linearRegression(value['net_in_val'])
        value['net_in_slope'] = net_in_slope
        value['net_in_intercept'] = net_in_intercept
        value['net_in_av'] = numpy.mean(value['net_in_val'])

        net_out_slope, net_out_intercept = linearRegression(value['net_out_val'])
        value['net_out_slope'] = net_out_slope
        value['net_out_intercept'] = net_out_intercept
        value['net_out_av'] = numpy.mean(value['net_out_val'])

       # net_rras_slope, net_rraas_intercept = linearRegression(value['net_rras_val'])
        #value['net_rras_slope'] = net_rras_slope
        #value['net_rras_intercept'] = net_rraas_intercept


    print "DC NODES LIST: ", dc_dict, type(dc_dict)
    print "AE OUTPUT RESULT: ", result, type(result)
    decisionEngine(result, dc_dict)


def calculate_rrases(me_pm_nodes):
    # calculate RRASes for each PM
    for key, pm in me_pm_nodes.iteritems():
        if not isinstance(pm, PhysNode):
            # ignore key 'timestamp'
            continue

        # caculate RRAS and store result in object's attributes
        pm.calculate_utils()
        pm.calculate_rrases()

        # calculate RRASes for each VM
        for vm in pm.vms:
            vm.calculate_utils()
            vm.calculate_rrases()


def main(argv):
    LOG.info('Initializing...')

    # monitoring and recording statistics for every monitoring_epoch
    monitoring_interval = config.MONITORING_EPOCH # seconds


    while True:
        # reset monitoring runs to zero
        me_runs = 0
        ae_nodes = []

        while me_runs < config.ANALYTIC_EPOCH:
            # sleep for config.MONITORING_EPOCH seconds
            LOG.info("Sleep for " + str(monitoring_interval) + " seconds")
            time.sleep(monitoring_interval)

            time_till = time.mktime(datetime.now().timetuple())
            time_from = time_till - monitoring_interval

            # get monitoring data
            me_pm_nodes = get_monitoring_epoch(time_till, time_from)

            # add timestamp
            me_pm_nodes['timestamp'] = time_till

            # derive preliminary RRAS report
            calculate_rrases(me_pm_nodes)

            # add result of monitoring to array
            ae_nodes.append(me_pm_nodes)

            LOG.debug('Output of monitoring run #%s:' % me_runs)
            LOG.debug(ae_nodes)

            # increment monitoring runs
            me_runs += 1

        # We've run config.ANALYTIC_EPOCH times; time to pass this info to the
        # analytics_engine
        print "GIVE OUTPUT TO ANALYTICS ENGINE: ", ae_nodes
        analytics_engine(ae_nodes)
	#analytics_engine_1(ae_nodes)



if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv)
