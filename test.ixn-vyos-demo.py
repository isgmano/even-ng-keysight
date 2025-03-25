from evengsdk.client import EvengClient
from evengsdk.client import EvengApi
import telnetlib
from ixNTest import *
import time

print("Log in to Eve-ng")
client = EvengClient("10.36.86.22", log_file="test.log", ssl_verify=False, protocol="http")
client.disable_insecure_warnings()  # disable warnings for self-signed certificates
client.login(username="admin", password="eve")
client.set_log_level("DEBUG")

print("Creating lab")
lab = {"name": "Demo-IxN-Vyos", "description": "IxNetwork lab with Vyos DUT", "path": "/"}
resp = client.api.create_lab(**lab)
if resp['status'] == "success":
  print("lab created successfully.")

# we need the lab path to create objects in the lab
lab_path = f"{lab['path']}{lab['name']}.unl"

print("Create management network")
mgmt_cloud = {"name": "eve-mgmt", "network_type": "pnet0"}
client.api.add_lab_network(lab_path, **mgmt_cloud)

print("Create Nodes")
nodes = [
    {"name": "Vyos-DUT", "template": "vyos", "image": "vyos-1.2.9-amd64", "left": 50, "top": 200},
    {"name": "IxVMONE", "template": "ixvm", "image": "ixvm-vta-x10.40", "left": 500, "top": 200},
    {"name": "IxWebUI", "template": "ixweb", "image": "xweb-ixnwebui.10.40", "left": 500, "top": 50},
]

for node in nodes:
    client.api.add_node(lab_path, **node)

print("Connect nodes to management network")
mgmt_connections = [
    {"src": "IxVMONE", "src_label": "e0", "dst": "eve-mgmt"},
    {"src": "IxWebUI", "src_label": "e0", "dst": "eve-mgmt"}
]
for link in mgmt_connections:
    client.api.connect_node_to_cloud(lab_path, **link)

print("Create p2p links")
p2p_links = [
    {"src": "Vyos-DUT", "src_label": "eth1", "dst": "IxVMONE", "dst_label": "e1"},
    {"src": "Vyos-DUT", "src_label": "eth2", "dst": "IxVMONE", "dst_label": "e2"}
]
for link in p2p_links:
    client.api.connect_node_to_node(lab_path, **link)
with open("vyos.cfg", "r") as file:
    config = file.read()
node_id = client.api.get_node_by_name(lab_path, "Vyos-DUT")["id"]
client.api.upload_node_config(lab_path, node_id, config, configset='default')
client.api.enable_node_config(lab_path, node_id)
print("Start all nodes")
resp = client.api.start_all_nodes(lab_path)
print("waiting for 1 min for the nodes to start")
time.sleep(60)
if resp['status'] == "success":
  print("All nodes started successfully.")

ixvmIP="10.36.86.135"
ixnIP="10.36.86.220"
print("Running IxNetwork Test")
runIxNTestNewCfg(ixvmIP,ixnIP)
print("Completed IxNetwork Test")
print("Stopping all nodes")
client.api.stop_all_nodes(lab_path)
time.sleep(10)
print("Deleting lab and logging off")
client.api.delete_lab(lab_path)
client.logout()