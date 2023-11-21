#!/usr/bin/python3

import sys
sys.path.append("../")

import ANTServerRESTClient
import datetime
import time

import json
import re

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost')
parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='0')
parser.add_argument('--max', help='Max number of missions', default='100')
parser.add_argument('--all', help="Show all missions; also finished", action='store_true')
args = parser.parse_args()

def showMission(missionData):
    print("Mission[%s](type=%s) %s -> %s (state=%s)" % (missionData["missionid"], missionData["missiontype"], missionData["fromnode"], missionData["tonode"], missionData["transportstate"] ) ) 

# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ---- Get Missions ---- ")
    print(" -------------------------------------- ")

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    while True:
        restClient.getSessionToken()
        if args.all:
            missions = restClient.getMissions(args.max)
        else:
            missions = restClient.getActiveMissions(args.max)
        print(" ---- Missions ---- ")
        for mission in missions:
            print("MissionData:", mission)
            showMission(mission)
        #print(json.dumps(missions, indent=4, sort_keys=True))
        if args.interval == '0':
            # only do it once.
            return
        print(" -------- ")
        time.sleep(float(args.interval))


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()


