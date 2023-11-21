#!/usr/bin/python3
"""
Copyright (C) 2017 BlueBotics SA
"""

import sys
import time
sys.path.append("../")

import ANTServerRESTClient

def WaitForMissionFinsihed(restClient, id):
    while True:
        mission = restClient.getMission(id)
        if mission != None:
            print(mission["navigationstate"])
            if mission["navigationstate"] == 4:
                return False
            if mission["navigationstate"] == 2 or mission["navigationstate"] == 5:
                return True
        time.sleep(2)

def Usage():
    print("Create a mission for transporting a payload from a node to another node")
    print("Usage : python CreateNodeToNodeMission.py [-h ANTServerHostname] NameOfSourceNode NameOfSourceNodeType NameOfDestNode NameOfDestNodeType NameOfPayload")

# -----------------------------------------------------------------------------
def main ():

    index=1
    if len(sys.argv) < 5:
        Usage()
        return None

    hostName = "localhost"
    if len(sys.argv) > 6: 
        if sys.argv[1] == '-h':
            hostName = sys.argv[2]
            index=3
        else:
            Usage()
            return None

    # get parameters
    sourceNode = str(sys.argv[index])
    sourceNodeType = str(sys.argv[index+1])
    destNode   = str(sys.argv[index+2])
    destNodeType = str(sys.argv[index+3])

    restClient = ANTServerRESTClient.ANTServerRestClient(hostName)

    print(" -------------------------------------- ")
    print(" ---- Create a mission ---- ")
    print(" -------------------------------------- ")

    #First connection to get the session token :
    restClient.getSessionToken()

    # Create mission:

    mission = restClient.createMissionData("Transport to node", sourceNode, destNode, 1, "test", "Medium", False, None, 0, sourceNodeType, destNodeType )
    id = restClient.executeCreateMissionRESTRequest(mission)[0]
    print("mission ID:" + id)
    if WaitForMissionFinsihed(restClient, id):
        print("failed mission")

    time.sleep(10)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
