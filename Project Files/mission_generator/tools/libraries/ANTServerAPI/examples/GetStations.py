#!/usr/bin/python3

import sys
sys.path.append("../")

import ANTServerRESTClient
import datetime
import time

import json

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server')
args = parser.parse_args()

# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ---- Get Stations ---- ")
    print(" -------------------------------------- ")

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    restClient.getSessionToken()
    missions = restClient.getStations()

    print(json.dumps(missions, indent=4, sort_keys=True))
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()


