#!/usr/bin/python3
import sys
import time
import argparse
sys.path.append("../")

import ANTServerRESTClient

restClient = None

def WaitForMissionFinished(restClient, id):
    while True:
        mission = restClient.getMission(id)
        if mission != None:
            print(mission["navigationstate"])
            if mission["navigationstate"] == 4:
                return False
            if mission["navigationstate"] == 2 or mission["navigationstate"] == 5:
                return True
        time.sleep(2)

def ExecuteFromNodeToNode( fr, snt, to, dnt, payload ):
#    global restClient
    mission = restClient.createMissionData("Transport to node", fr, to, 1, payload, "Medium", False, None, 0, snt, dnt)

    id = restClient.executeCreateMissionRESTRequest(mission)[0]
    print("mission ID:" + id)
    if WaitForMissionFinished(restClient, id):
      print("failed mission")
      sys.exit( -1 );

class Payload():
    def __init__( self, name ):
        self._counter = 0
        self._name = name

    def getName( self ):
        self._counter = self._counter + 1
        return self._name + "_" + str(self._counter)
        

    
        

# -----------------------------------------------------------------------------
def main ():
    global restClient

    parser = argparse.ArgumentParser(description="""Generate a loop transporting a payload from <fr> node to <to> node and vice versa
                                                    and optional from <st3> to <st4> and vice versa. 
                                                    Note: wait 20 seconds for vehicle to go to the charger when only 1 source destination pair given""")
    parser.add_argument('-host',help='ANTServerHostName (default=localhost)', default='localhost')
    parser.add_argument('-st1',  help='station 1; first from node (mandatory)')
    parser.add_argument('-st2',  help='station 2; first to node (mandatory)')
    parser.add_argument('-st3', help='station 3; second from node')
    parser.add_argument('-st4', help='station 4; second to node')
    parser.add_argument('-snt1', help='Source node type station 1 (default=Pickup)', default='Pickup')
    parser.add_argument('-dnt1', help='Destination node type station 1 (default=Dropoff)', default='Dropoff')
    parser.add_argument('-snt2', help='Source node type station 1 (default=Pickup)', default='Pickup')
    parser.add_argument('-dnt2', help='Destination node type station 1 (default=Dropoff)', default='Dropoff')
    parser.add_argument('-snt3', help='Source node type station 1 (default=Pickup)', default='Pickup')
    parser.add_argument('-dnt3', help='Destination node type station 1 (default=Dropoff)', default='Dropoff')
    parser.add_argument('-snt4', help='Source node type station 1 (default=Pickup)', default='Pickup')
    parser.add_argument('-dnt4', help='Destination node type station 1 (default=Dropoff)', default='Dropoff')
    parser.add_argument('-payload', help='Payload name (default=Test)', default='Test')

    # get arguments
    args = parser.parse_args()
    payload = Payload( args.payload )

    if args.st1 is None or args.st2 is None:
        print( "st1 and st2 not given; they are mandatory")
        parser.usage()
        sys.exit -1

    # start restClient
    restClient = ANTServerRESTClient.ANTServerRestClient(args.host)

    #First connection to get the session token :
    restClient.getSessionToken()

    while True:
        ExecuteFromNodeToNode(args.st1, args.snt1, args.st2, args.dnt2, payload.getName())
        if args.st3 is None or args.st4 is None:
            print("wait for agv to go to charger")
            time.sleep(20)
        else:
            ExecuteFromNodeToNode( args.st3, args.snt3, args.st4, args.dnt4, payload.getName() )
        ExecuteFromNodeToNode( args.st2, args.snt2, args.st1, args.dnt1, payload.getName() )
        if args.st3 is None or args.st4 is None:
            print("wait for agv to go to charger")
            time.sleep(20)
        else:
            ExecuteFromNodeToNode( args.st4, args.snt4, args.st3, args.dnt3, payload.getName() )


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
