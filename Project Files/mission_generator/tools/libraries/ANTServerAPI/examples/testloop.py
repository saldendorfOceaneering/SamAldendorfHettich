#!/usr/bin/python3
"""\
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


# -----------------------------------------------------------------------------
def main ():
   host = "localhost" 
   if len(sys.argv) > 1:
       host = sys.argv[1]

   restClient = ANTServerRESTClient.ANTServerRestClient(host)


    #First connection to get the session token :
    restClient.getSessionToken()

    while True:
       mission = restClient.createMissionData("Transport to node", "station1", "station2", 1, "test", "Medium", False, None, 0, "pickup", "_dropoff")
        elif stationWithLoad == "station2":
           mission = restClient.createMissionData("Transport to node", "station2", "station1", 1, "test", "Medium", False, None, 0, "_pickup", "dropoff")
        else:

        id = restClient.executeCreateMissionRESTRequest(mission)[0]
        print("mission ID:" + id)
        if not WaitForMissionFinsihed(restClient, id):
          print("wait for agv to go to charger")
          time.sleep(20)
          if stationWithLoad == "station1":
              mission = restClient.createMissionData("Transport to node", "station2", "station1", 1, "test", "Medium", False, None, 0, "_pickup", "dropoff" )
          else:
              mission = restClient.createMissionData("Transport to node", "station1", "station2", 1, "test", "Medium", False, None, 0, "pickup", "_dropoff" )
          id = restClient.executeCreateMissionRESTRequest(mission)[0]
          print("mission ID:" + id)

          if WaitForMissionFinsihed(restClient, id):
              print("failed mission")
              return None
        else:
            print("failed mission")
            return None



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
