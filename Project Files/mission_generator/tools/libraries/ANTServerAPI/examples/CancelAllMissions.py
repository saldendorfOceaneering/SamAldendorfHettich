#!/usr/bin/python3
"""
Copyright (C) 2017 BlueBotics SA
"""

import sys
sys.path.append("../")

import ANTServerRESTClient
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost')
args = parser.parse_args()


# -----------------------------------------------------------------------------
def main ():

    print(" -------------------------------------- ")
    print(" ---- Cancel Missions ---- ")
    print(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    #First connection to get the session token :
    restClient.getSessionToken()

    # Get list of mission :
    missionList = restClient.executeGetMissionListRESTRequest(10000)
    print(str(missionList))

    # and cancel all active missions
    for mission in missionList:
        missionID = mission["missionid"]
        missionState = mission["navigationstate"]

        print("mission id :" + missionID)
        print("navigationstate :" + str(missionState))

        if missionState in [0, 1, 3]:

            restClient.executeCancelMissionRESTRequest(missionID)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

