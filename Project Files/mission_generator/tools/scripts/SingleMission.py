#!/usr/bin/python3

import sys
sys.path.append("../libraries/ANTServerAPI/")
sys.path.append("../libraries/common/")
sys.path.append("../simulation/")

import ANTServerRESTClient
import argparse
import common
import Missions



parser = argparse.ArgumentParser()
parser.add_argument('fr', type=str, help="origin")
parser.add_argument('to', type=str, help="destination")
parser.add_argument('--ty', help="mission type", default="transport from station to station")
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
parser.add_argument('--info', help="Show info", action='store_true')
parser.add_argument('--debug', help="Show debug", action='store_true')
parser.add_argument('--payload', help="payload", default="Default Payload")
parser.add_argument('--prio', help="priority", default="Medium")
parser.add_argument('--snt', type=str, help="Source node type", default=None)
parser.add_argument('--dnt', type=str, help="Destination node type", default=None)
args = parser.parse_args()

log = common.initLogger( "SingleMission", args.debug, args.info )

log.info(" -------------------------------------- ")
log.info(" ---- Run simulation ---- ")
log.info(" -------------------------------------- ")
restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug )
Missions.setRestClient(restClient)

descr=f"{args.ty} from {args.fr} to {args.to}"

Missions.createMission( args.ty, descr, args.fr, args.to, args.payload, args.prio, sourceNodeType=args.snt, destNodeType=args.dnt )
