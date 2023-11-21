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
    print(" ---- Extract a vehicle ---- ")
    print(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    #First connection to get the session token :
    restClient.getSessionToken()

    restClient.executeExtractAllVehicleRESTRequest()
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
