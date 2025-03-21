
### MODULES
import urllib3
import requests
import time,re
from os import system
from prettytable import PrettyTable

### FUNCTIONS

def login(server, username, password):
    print("\nAuthenticating...")
    url = f"https://{server}/api/auth/login"
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

def verifyLab(server,labPath,userCookie):
    print("\nVerify Lab ["+ labPath +"]...")
    url = f"https://{server}/api/labs/{labPath}"
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

def getNodes(server,labPath,userCookie):
    nodeList =[]
    print("\nGetting Nodes Lab ["+ labPath +"]...")  
    url = f"https://{server}/api/labs/{labPath}/nodes"
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

def startAllNodes(server,labPath,userCookie,nodeList):
    print("\nStarting All Nodes in Lab ["+ labPath +"]...") 
    for node in nodeList:
        url = f"https://{server}/api/labs/{labPath}/nodes/{node}/start"
        headers={
            "Cookie": userCookie
            }
        payload = "{}"
        response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
        print("Node" + node + response["message"])
    print("Waiting 5s for nodes to start")
    time.sleep(5)
    getNodes(server,labPath,userCookie)
    return 0

def stopAllNodes(server,labPath,userCookie):
    print("\nStopping All Nodes in Lab ["+ labPath +"]...") 
    nodeList = getNodes(server,labPath,userCookie)
    for node in nodeList:
        url = f"https://{server}/api/labs/{labPath}/nodes/{node}/stop/stopmode=3"
        headers={
            "Cookie": userCookie
            }
        payload = "{}"
        response = requests.get(url=url, headers=headers, data=payload, verify=False).json()
        print("Node" + node + response["message"])

    time.sleep(0.5)
    getNodes(server,labPath,userCookie)

    return 0