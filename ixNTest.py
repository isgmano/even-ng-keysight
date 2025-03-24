import json, sys, os, traceback, time

# Import the RestPy module
from ixnetwork_restpy import SessionAssistant, Files

def runIxNTest(ixvmIP, ixnIP):
    apiServerIp = ixnIP
    # A list of chassis to use
    ixChassisIpList = [ixvmIP]
    portList = [[ixChassisIpList[0], 1, 1], [ixChassisIpList[0], 1, 2]]

    # For Linux API server only
    username = 'admin'
    password = 'admin'

    # For linux and connection_manager only. Set to True to leave the session alive for debugging.
    debugMode = False

    # Forcefully take port ownership if the portList are owned by other users.
    forceTakePortOwnership = True

    configFile = 'eve-ng-demo.ixncfg'

    try:
        # LogLevel: none, info, warning, request, request_response, all
        session = SessionAssistant(IpAddress=apiServerIp, RestPort=None, UserName='admin', Password='admin', 
                                SessionName=None, SessionId=None, ApiKey=None,
                                ClearConfig=True, LogLevel='info', LogFilename='restpy.log')

        ixNetwork = session.Ixnetwork
        licensing = ixNetwork.Globals.Licensing.find()
        licensing.LicensingServers = ['10.36.84.12']
        licensing.VmMode = 'subscription'

        ixNetwork.info('Loading config file: {0}'.format(configFile))
        ixNetwork.LoadConfig(Files(configFile, local_file=False))
    
        # Assign ports. Map physical ports to the configured vports.
        portMap = session.PortMapAssistant()
        vport = dict()
        for index,port in enumerate(portList):
            # For the port name, get the loaded configuration's port name
            portName = ixNetwork.Vport.find()[index].Name
            portMap.Map(IpAddress=port[0], CardId=port[1], PortId=port[2], Name=portName)
            
        portMap.Connect(forceTakePortOwnership)

        ixNetwork.StartAllProtocols(Arg1='sync')

        ixNetwork.info('Verify protocol sessions\n')
        protocolSummary = session.StatViewAssistant('Protocols Summary')
        protocolSummary.CheckCondition('Sessions Not Started', protocolSummary.EQUAL, 0)
        protocolSummary.CheckCondition('Sessions Down', protocolSummary.EQUAL, 0)
        ixNetwork.info(protocolSummary)

        # Get the Traffic Item name for getting Traffic Item statistics.
        trafficItem = ixNetwork.Traffic.TrafficItem.find()[0]

        trafficItem.Generate()
        ixNetwork.Traffic.Apply()
        ixNetwork.Traffic.StartStatelessTrafficBlocking()

        trafficItemStatistics = session.StatViewAssistant('Traffic Item Statistics')

        # StatViewAssistant could also filter by REGEX, LESS_THAN, GREATER_THAN, EQUAL. 
        # Examples:
        #    trafficItemStatistics.AddRowFilter('Port Name', trafficItemStatistics.REGEX, '^Port 1$')
        #    trafficItemStatistics.AddRowFilter('Tx Frames', trafficItemStatistics.GREATER_THAN, "5000")

        ixNetwork.info('{}\n'.format(trafficItemStatistics))

        # Get the statistic values
        txFrames = trafficItemStatistics.Rows['Tx Frames']
        rxFrames = trafficItemStatistics.Rows['Rx Frames']
        ixNetwork.info('\nTraffic Item Stats:\n\tTxFrames: {}  RxFrames: {}\n'.format(txFrames, rxFrames))

        ixNetwork.Traffic.StopStatelessTrafficBlocking()

        if debugMode == False:
            # For Linux and Windows Connection Manager only
            if session.TestPlatform.Platform != 'windows':
                session.Session.remove()

    except Exception as errMsg:
        print('\n%s' % traceback.format_exc())
        if debugMode == False and 'session' in locals():
            if session.TestPlatform.Platform != 'windows':
                session.Session.remove()

def runIxNTestNewCfg(ixvmIP, ixnIP):
    apiServerIp = ixnIP
    # A list of chassis to use
    ixChassisIpList = [ixvmIP]
    portList = [[ixChassisIpList[0], 1, 1], [ixChassisIpList[0], 1, 2]]

    # For Linux API server only
    username = 'admin'
    password = 'admin'

    # For linux and connection_manager only. Set to True to leave the session alive for debugging.
    debugMode = False

    # Forcefully take port ownership if the portList are owned by other users.
    forceTakePortOwnership = True

    configFile = 'eve-ng-demo.ixncfg'

    try:
        # LogLevel: none, info, warning, request, request_response, all
        session = SessionAssistant(IpAddress=apiServerIp, RestPort=None, UserName='admin', Password='admin', 
                                SessionName=None, SessionId=None, ApiKey=None,
                                ClearConfig=True, LogLevel='info', LogFilename='restpy.log')

        ixNetwork = session.Ixnetwork
        licensing = ixNetwork.Globals.Licensing.find()
        licensing.LicensingServers = ['10.36.84.12']
        licensing.VmMode = 'subscription'

        ixNetwork.info('Assign ports')
        portMap = session.PortMapAssistant()
        vport = dict()
        for index,port in enumerate(portList):
            portName = 'Port_{}'.format(index+1)
            vport[portName] = portMap.Map(IpAddress=port[0], CardId=port[1], PortId=port[2], Name=portName)

        portMap.Connect(forceTakePortOwnership)

        ixNetwork.info('Creating Topology Group 1')
        topology1 = ixNetwork.Topology.add(Name='Topo1', Ports=vport['Port_1'])
        deviceGroup1 = topology1.DeviceGroup.add(Name='DG1', Multiplier='1')
        ethernet1 = deviceGroup1.Ethernet.add(Name='Eth1')
        ethernet1.Mac.Increment(start_value='00:01:01:01:00:01', step_value='00:00:00:00:00:01')

        ixNetwork.info('Configuring IPv4')
        ipv4 = ethernet1.Ipv4.add(Name='Ipv4')
        ipv4.Address.Increment(start_value='192.168.11.2', step_value='0.0.0.1')
        ipv4.GatewayIp.Increment(start_value='192.168.11.1', step_value='0.0.0.0')

        ixNetwork.info('Creating Topology Group 2')
        topology2 = ixNetwork.Topology.add(Name='Topo2', Ports=vport['Port_2'])
        deviceGroup2 = topology2.DeviceGroup.add(Name='DG2', Multiplier='1')

        ethernet2 = deviceGroup2.Ethernet.add(Name='Eth2')
        ethernet2.Mac.Increment(start_value='00:01:01:02:00:01', step_value='00:00:00:00:00:01')

        ixNetwork.info('Configuring IPv4 2')
        ipv4 = ethernet2.Ipv4.add(Name='Ipv4-2')
        ipv4.Address.Increment(start_value='192.168.12.2', step_value='0.0.0.1')
        ipv4.GatewayIp.Increment(start_value='192.168.12.1', step_value='0.0.0.0')
    
        ixNetwork.StartAllProtocols(Arg1='sync')

        ixNetwork.info('Verify protocol sessions\n')
        protocolSummary = session.StatViewAssistant('Protocols Summary')
        protocolSummary.CheckCondition('Sessions Not Started', protocolSummary.EQUAL, 0)
        protocolSummary.CheckCondition('Sessions Down', protocolSummary.EQUAL, 0)
        ixNetwork.info(protocolSummary)

        ixNetwork.info('Create Traffic Item')
        trafficItem = ixNetwork.Traffic.TrafficItem.add(Name='EVE Traffic', BiDirectional=False, TrafficType='ipv4')

        ixNetwork.info('Add endpoint flow group')
        trafficItem.EndpointSet.add(Sources=topology1, Destinations=topology2)

        # Note: A Traffic Item could have multiple EndpointSets (Flow groups).
        #       Therefore, ConfigElement is a list.
        ixNetwork.info('Configuring config elements')
        configElement = trafficItem.ConfigElement.find()[0]
        configElement.FrameRate.update(Type='framesPerSecond', Rate=10)
        configElement.FrameRateDistribution.PortDistribution = 'splitRateEvenly'
        configElement.FrameSize.FixedSize = 128
        trafficItem.Tracking.find()[0].TrackBy = ['flowGroup0']

        trafficItem.Generate()
        ixNetwork.Traffic.Apply()
        ixNetwork.Traffic.StartStatelessTrafficBlocking()
        time.sleep(5)
        ixNetwork.Traffic.StopStatelessTrafficBlocking()

        trafficItemStatistics = session.StatViewAssistant('Traffic Item Statistics')

        # StatViewAssistant could also filter by REGEX, LESS_THAN, GREATER_THAN, EQUAL. 
        # Examples:
        #    trafficItemStatistics.AddRowFilter('Port Name', trafficItemStatistics.REGEX, '^Port 1$')
        #    trafficItemStatistics.AddRowFilter('Tx Frames', trafficItemStatistics.GREATER_THAN, "5000")

        ixNetwork.info('{}\n'.format(trafficItemStatistics))

        # Get the statistic values
        txFrames = trafficItemStatistics.Rows['Tx Frames']
        rxFrames = trafficItemStatistics.Rows['Rx Frames']
        ixNetwork.info('\nTraffic Item Stats:\n\tTxFrames: {}  RxFrames: {}\n'.format(txFrames, rxFrames))

        ixNetwork.Traffic.StopStatelessTrafficBlocking()

        if debugMode == False:
            # For Linux and Windows Connection Manager only
            if session.TestPlatform.Platform != 'windows':
                session.Session.remove()

    except Exception as errMsg:
        print('\n%s' % traceback.format_exc())
        if debugMode == False and 'session' in locals():
            if session.TestPlatform.Platform != 'windows':
                session.Session.remove()
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
### For Testing
'''
ixvmIP="10.36.86.135"
ixnIP="10.36.86.220"     
runIxNTestNewCfg(ixvmIP,ixnIP)
'''
