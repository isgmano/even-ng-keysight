from evengsdk.client import EvengClient
from evengsdk.client import EvengApi
import telnetlib
from ixNTest import runIxNTest
import time

def getIxiaIP(telnet_add,telnet_port):
    try:
        tn = telnetlib.Telnet(host=telnet_add, port=telnet_port, timeout=5)
        time.sleep(10)
        output = tn.read_until(b"login: ", timeout=5)
        text = output.decode('ascii')
        
        tn.write(b"admin\n")
        tn.read_until(b"Password: ", timeout=5)
        tn.write(b"admin\n")
        tn.write(b"show ip\n")
        output = tn.read_until(b"scope", timeout=5)
        text = output.decode('ascii')
        print(text)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'tn' in locals() and tn.sock is not None:
            tn.close()
    index = text.find("Management IPv4: ")
    ipaddr = text[index+17:index+28]
    return ipaddr

client = EvengClient("10.36.86.22", log_file="test.log", ssl_verify=False, protocol="http")
client.disable_insecure_warnings()  # disable warnings for self-signed certificates
client.login(username="admin", password="eve")
client.set_log_level("DEBUG")

# create a lab
lab = {"name": "test_lab", "description": "Test Lab1", "path": "/"}
resp = client.api.create_lab(**lab)
if resp['status'] == "success":
  print("lab created successfully.")

# we need the lab path to create objects in the lab
lab_path = f"{lab['path']}{lab['name']}.unl"

# create management network
mgmt_cloud = {"name": "eve-mgmt", "network_type": "pnet0"}
client.api.add_lab_network(lab_path, **mgmt_cloud)

# create Nodes
nodes = [
    {"name": "Cisco-DUT", "template": "viosl2", "image": "viosl2-1234", "left": 50, "top": 200},
    {"name": "IxVMONE", "template": "ixvm", "image": "ixvm-vta-11.0", "left": 500, "top": 200},
]

for node in nodes:
    client.api.add_node(lab_path, **node)

# connect nodes to management network
mgmt_connections = [
    {"src": "IxVMONE", "src_label": "e0", "dst": "eve-mgmt"},
]
for link in mgmt_connections:
    client.api.connect_node_to_cloud(lab_path, **link)

# create p2p links
p2p_links = [
    {"src": "Cisco-DUT", "src_label": "Gi0/1", "dst": "IxVMONE", "dst_label": "e1"},
    {"src": "Cisco-DUT", "src_label": "Gi0/2", "dst": "IxVMONE", "dst_label": "e2"}
]
for link in p2p_links:
    client.api.connect_node_to_node(lab_path, **link)
    
# start all nodes
resp = client.api.start_all_nodes(lab_path)
print("waiting for 1 min for the nodes to start")
time.sleep(60)
if resp['status'] == "success":
  print("All nodes started successfully.")

#get node id
node_id = client.api.get_node_by_name(lab_path, "IxVMONE")["id"]
#get the telnet port
telnet_add=client.api.list_nodes(lab_path)['data'][str(node_id)]['url'].replace("//","").split(':')[1]
telnet_port=client.api.list_nodes(lab_path)['data'][str(node_id)]['url'].replace("//","").split(':')[2]
#ixiaIP = getIxiaIP(telnet_add,telnet_port)
ixiaIP="10.36.86.135"
runIxNTest(ixiaIP)
client.api.stop_all_nodes(lab_path)
time.sleep(10)
client.api.delete_lab(lab_path)
client.logout()