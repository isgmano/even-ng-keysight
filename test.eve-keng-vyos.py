#! /usr/bin/python3.8
### MODULES
import urllib3
import requests
import time,re
from os import system
from prettytable import PrettyTable
from eveng_utils import *
from keng_vyos import Test_otg_flows


### GLOBAL VARIABLES
server = "10.36.86.22"
username = "admin"
password = "eve"
labPath = "Demos/KENG Demo_1.unl"
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
kengController = "10.36.86.26"

### Run IxN test
print("Waiting 60s for all nodes to complete starting and ready to run test")
time.sleep(60)
Test_otg_flows()
time.sleep(2)
userCookie = login(server, username, password)
stopAllNodes(server,labPath,userCookie)
print("Closing App")
quit()