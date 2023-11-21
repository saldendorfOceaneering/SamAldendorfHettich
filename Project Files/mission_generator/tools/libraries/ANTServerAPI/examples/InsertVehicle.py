#!/usr/bin/python3
"""\
Copyright (C) 2017 BlueBotics SA
"""
import sys
sys.path.append("../")

import ANTServerRESTClient
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost')
parser.add_argument('--vehicleName', help='Name of vehicle')
parser.add_argument('--nodeName', help='Node name')
args = parser.parse_args()


# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ----------- Insert Vehicle ----------- ")
    print(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient()

    #First connection to get the session token :
    restClient.getSessionToken()

    # Insert
    restClient.executeInsertVehicleRESTRequest(args.vehicleName, args.nodeName)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
