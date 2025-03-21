#! /usr/bin/python3.8


### MODULES
import urllib3
import requests
import time,re
from os import system
from prettytable import PrettyTable
from kengTest import Test_ebgp_route_prefix


### GLOBAL VARIABLES
server = "10.36.86.22"
username = "admin"
password = "eve"
labPath = "Demos/KENG Demo.unl"
userCookie = ""
nodeList = []

### FUNCTIONS

def login(server, username, password):
    print("\nAuthenticating...")
    url = f"http://{server}/api/auth/login"
    headers = ""
    payload = "{\"username\":\"" + username + "\",\"password\":\"" + password + "\", \"html5\":\"-1\"}"

    response = requests.post(url=url, headers=headers, data=payload, verify=False)

    if response.json()["code"] == 200:
        print(f"Successfully Authenticated\nUser : {username}")
        userCookie = "unetlab_session=" + response.cookies['unetlab_session']
        print("Cookie : " + userCookie) 
    else:
        print("Authenictation Failed : Error " + str(response.json()["code"]))
        userCookie = ""
    return userCookie

def verifyLab():
    print("\nVerify Lab ["+ labPath +"]...")
    url = f"http://{server}/api/labs/{labPath}"
    headers={
        "Content-Type":"application/json",
        "Cookie": userCookie
        }
    payload = "{}"

    response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
    print(response["status"] + " : " + response["message"])
    if response["code"] == 200:
        return True
    else:
        return False

def getNodes(userCookie):
    print("\nGetting Nodes Lab ["+ labPath +"]...")  
    url = f"http://{server}/api/labs/{labPath}/nodes"
    headers={
        "Cookie": userCookie
        }
    payload = "{}"
    nodeList.clear()

    response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
    if response["code"] == 200:
        node_table = PrettyTable()
        node_table.field_names = ["ID", "Hostname", "Status", "Image", "Type"]
        for node in response["data"]:
            nodeList.append(node)
            if response["data"][str(node)]["status"] == 0:
                node_status = "Off"
            elif response["data"][str(node)]["status"] == 2:
                node_status = "On "
            else:
                node_status = "unkown"

            node_table.add_row([
                node,
                response["data"][str(node)]["name"],
                node_status,
                response["data"][str(node)]["image"],
                response["data"][str(node)]["type"]
                ])
            #nodeList.append(response["data"][str(node)]["name"])
            #nodeList.append(response["data"][str(node)]["url"])
        print(node_table.get_string(title=f"Title : {labPath}"))

        return nodeList
    else:
        print(response["status"] + ":" + str(response["code"]) + "Error, gracefully exiting App")
        quit()

def startAllNodes(nodeList):
    print("\nStarting All Nodes in Lab ["+ labPath +"]...") 
    for node in nodeList:
        url = f"http://{server}/api/labs/{labPath}/nodes/{node}/start"
        headers={
            "Cookie": userCookie
            }
        payload = "{}"
        response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
        print("Node" + node + response["message"])
    print("Waiting 5s for nodes to start")
    time.sleep(5)
    getNodes(userCookie)
    return 0

def stopAllNodes():
    print("\nStopping All Nodes in Lab ["+ labPath +"]...") 
    userCookie = login(server, username, password)
    nodeList = getNodes(userCookie)
    for node in nodeList:
        url = f"http://{server}/api/labs/{labPath}/nodes/{node}/stop"
        headers={
            "Cookie": userCookie
            }
        payload = "{}"
        response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
        print("Node" + node + response["message"])

    time.sleep(0.5)
    getNodes(userCookie)

    return 0
   
### PROGRAM BODY
# Initial setup and clean
system('clear') # clear CLI screen
urllib3.disable_warnings() # stop SSL Self cert error
print("=== EVE-NG Lab Loader ===")
print(f"Accessing Lab\t \"{labPath}\"")
print(f"Accessing \t{username}@{server}")
print("")

# get authentication cookie
userCookie = login(server, username, password)

# check lab exists in appliction
if verifyLab()  == False:
    print("Lab Not Present. Gracefully quitting app")
    time.sleep(1)
    quit()

### Get List of Nodes in Lab and report 
time.sleep(0.5)
getNodes(userCookie)

### Starting All Nodes
time.sleep(0.5)
startAllNodes(nodeList)
### Get all node IPs; not working at the moment hence hardcoding IPs
#ixVMChassisIP = re.sub("//", "", nodeList[nodeList.index("IxVM")+1].split(":")[1])
#ixNWebIP = re.sub("//", "", nodeList[nodeList.index("IxWebUI")+1].split(":")[1])
kengController = "10.36.86.26"

### Run IxN test
print("Waiting 60s for all nodes to complete starting and ready to run test")
time.sleep(60)
Test_ebgp_route_prefix()
time.sleep(2)
stopAllNodes()
print("Closing App")
quit()