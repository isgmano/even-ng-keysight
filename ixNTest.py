import json, sys, os, traceback

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

### For Testing
'''
ixvmIP="10.36.86.135"
ixnIP="10.36.86.220"     
runIxNTest(ixvmIP,ixnIP)
'''
