from pyzabbix import ZabbixAPI

zapi = ZabbixAPI("http://160.85.4.28/zabbix")
zapi.login("admin", "zabbix")

print zapi.item.get(host='bart-node-3', filter={"key_":'vm.memory.size[total]'}, output='extend')[0]

print zapi.history.get(hostids="10111", itemids="23741", time_from="1459856208", time_till="1459856328", output='extend', limit=10, history=3)
print zapi.history.get(hostids="10111", itemids="23741", output='extend', limit=10, history=3)
