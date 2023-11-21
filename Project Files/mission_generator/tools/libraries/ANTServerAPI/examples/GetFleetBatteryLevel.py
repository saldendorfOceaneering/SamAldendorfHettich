#!/usr/bin/python3
"""
Copyright (C) 2016 BlueBotics SA
"""

import sys
sys.path.append("../")

import ANTServerRESTClient
import datetime
import time
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host',       help='Host address of ANT-Server',  default='localhost')
parser.add_argument('--period',     help='period in seconds',           default='60')
parser.add_argument('--maxSamples', help='max samples',                 default='60')
parser.add_argument('--loopMode',   help='loop mode',                   default='n')
args = parser.parse_args()


# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ---- Fleet battery level recorder ---- ")
    print(" -------------------------------------- ")

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    while (True):
        startTime = datetime.datetime.now().isoformat()
        startTime = startTime.replace(":", "-")
        nbSamples = 1

        print("Recording Fleet batery level every " + str(args.period) + " seconds, during " + str(args.period*args.maxSamples) + " seconds")

        while nbSamples < args.maxSamples:
            print("getting battery level : "+str(nbSamples) + "/" + str(args.maxSamples))

            restClient.getSessionToken()
            fleetInfo = restClient.getVehiclesInfo()
            for vehicle in fleetInfo:
                name = str(vehicle["name"])
                filename = "./" + name + "_" + str(startTime)+".txt"
                batteryInfo = vehicle["state"]["battery.info"]
                timestamp = vehicle["timestamp"]

                if len(batteryInfo)>1:
                    with open(filename, "a") as f:
                        f.write(str(timestamp) + ", " + str(batteryInfo[0]) + ", " + str(batteryInfo[1]) + ";\n")

            time.sleep(args.period)
            nbSamples = nbSamples+1
            print("-> Done")

        if ( args.loopMode != 'y' ):
            return


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
