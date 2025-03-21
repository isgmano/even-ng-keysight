#! /usr/bin/python3.8


### MODULES
import urllib3
import requests
import time,re
from os import system
from prettytable import PrettyTable
from eveng_utils import *
from ixNTest import runIxNTest


### GLOBAL VARIABLES
server = "172.16.14.2"
username = "admin"
password = "eve"
labPath = "Users/Sam/IxN_demo.unl"
userCookie = ""
nodeList = []

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
if verifyLab(server,labPath,userCookie)  == False:
    print("Lab Not Present. Gracefully quitting app")
    time.sleep(1)
    quit()

### Get List of Nodes in Lab and report 
time.sleep(0.5)
nodeList=getNodes(server,labPath,userCookie)

### Starting All Nodes
time.sleep(0.5)
startAllNodes(server,labPath,userCookie,nodeList)
### Get all node IPs; not working at the moment hence hardcoding IPs
#ixVMChassisIP = re.sub("//", "", nodeList[nodeList.index("IxVM")+1].split(":")[1])
#ixNWebIP = re.sub("//", "", nodeList[nodeList.index("IxWebUI")+1].split(":")[1])
ixVMChassisIP = "172.16.14.102"
ixNWebIP = "172.16.14.103"

### Run IxN test
print("Waiting 60s for all nodes to complete starting and ready to run test")
time.sleep(60)
runIxNTest(ixVMChassisIP,ixNWebIP)
time.sleep(2)
userCookie = login(server, username, password)
stopAllNodes(server,labPath,userCookie)
print("Closing App")
quit()