#!/usr/bin/python3
"""\
Copyright (C) 2017 BlueBotics SA
"""

import sys
sys.path.append("../")

import ANTServerRESTClient
import datetime
import time
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost')
parser.add_argument('--interval', help='interval, when zero do it only once', default='0.0')
args = parser.parse_args()


# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ---- Fleet position display ---- ")
    print(" -------------------------------------- ")

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )


    while (True):
        print("--- getting positions ---")

        restClient.getSessionToken()
        fleetInfo = restClient.getVehiclesInfo()

        for vehicle in fleetInfo["payload"]["vehicles"]:
            try:
                name = str(vehicle["name"])
                coordinates = vehicle["location"]["coord"]
                mapname = vehicle["location"]["map"]
                nodeId = vehicle["location"]["currentnode"]["id"]
                nodeName = vehicle["location"]["currentnode"]["name"]

                print("Vehicle " + name + ":" + "[" + mapname + "] " + str(coordinates) + " node(" + str(nodeId)+")" )
            except:
                print("Vehicle " + name + ": Vehicle might not be inserted")
                pass

        if float(args.interval) > 0.0:
            time.sleep(float(args.interval))
        else: 
            return



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

