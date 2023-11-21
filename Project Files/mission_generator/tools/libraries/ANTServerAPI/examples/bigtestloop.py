#!/usr/bin/python3
"""\
Copyright (C) 2017 BlueBotics SA
"""

import sys
import time
sys.path.append("../")

import ANTServerRESTClient

transportmatrix = [
    ["station1", "pickup", "station3", "dropoff"],
    ["station3", "pickup", "station1", "dropoff"]

]

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


# -----------------------------------------------------------------------------
def main ():
    restClient = ANTServerRESTClient.ANTServerRestClient("localhost")
   #First connection to get the session token :
    restClient.getSessionToken()

    for transport in transportmatrix:
        mission = restClient.createMissionData("Transport to node", transport[0], transport[2], 1, "test", "Medium", False, None, 0, transport[1], transport[3])
        id = restClient.executeCreateMissionRESTRequest(mission)[0]
        print("mission ID:" + id)
        if WaitForMissionFinsihed(restClient, id):
           print("mission failed")
           return None

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
