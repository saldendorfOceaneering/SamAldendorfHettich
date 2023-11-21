#!/usr/bin/python3

import sys
sys.path.append("../libraries/ANTServerAPI/")

import ANTServerRESTClient
import datetime
import time
import json
import re
import threading
import argparse


Areas = {}

class AreaHandler:

    def handleEvent(self, event, area, prev_area):
        # to be overrules.
        print("Handle event: %s area %s" %(event, area.getId()))


class Area:
    def __init__(self, areaData):
        self._id = areaData["areaid"]
        self._name = areaData["alias"]
        self._alternative = areaData["alternativeareas"]
        self._nodes = areaData["nodes"]
        self._state = areaData["state"]
        self._timestamp = areaData["timestamp"]
        self._eventHandlers = []

    def addEventHandler(self, event_handler):
        self._eventHandlers.append(event_handler)
        
    def getId(self):
        return self._id

    def update(self, areaData):
        self._state = areaData["state"]
        self._timestamp = areaData["timestamp"]

    def isChanged(self, areaData):
        return self._state != areaData["state"]

    def isOpen(self):
        return self._state == "Open"

    def open(self):
        restClient.executeOpenAreaRESTRequest(self._name, True)

    def close(self):
        restClient.executeOpenAreaRESTRequest(self._name, False)

    def show(self, verbose=False):
        print("area %s(%s) @ %s state=%s " % (self.getId(), self._name, self._timestamp, self._state ) ) 


# call the global event handler if it exists and for each areas the registered event handlers.
def callEventHandlers(event, area, prev_area, event_handler): 
    if event_handler != None:
        event_handler(event, area, prev_area)

    for handler in area._eventHandlers:
        handler.handleEvent(event, area, prev_area)
    

def monitorAreas(restClient, interval, maxAreas, event_handler):
    while True:
        try:
            restClient.getSessionToken()
            handledAreaIds = []
            for areaData in restClient.executeGetAreaListRESTRequest(args.max):
                id = areaData["areaid"]
                if id in Areas.keys():
                    if Areas[id].isChanged(areaData):
                        prev_area = Areas[id]
                        Areas[id].update(areaData)
                        callEventHandlers("changed", Areas[id], prev_area, event_handler)
                else:
                    Areas[id] = Area(areaData)
                    callEventHandlers("new", Areas[id], None, event_handler);
                handledAreaIds.append(id)

            deleteAreaIds = []
            for id in Areas:
                if id not in handledAreaIds:
                    callEventHandlers("deleted", Areas[id], None, event_handler);
                    deleteAreaIds.append(id)
            # now realy remove the area.
            for id in deleteAreaIds:
                    del Areas[id]
        except Exception as e: 
            print("monitorAreas: exception :", e)
        time.sleep(interval)

def getArea(id):
    if id in Areas.keys():
        return Areas[id]
    else:
        return None

def getAreaByName(name):
    for id in Areas:
        if Areas[id]._name == name:
            return Areas[id]
    return None



# local test 
# dummy event handler for testing; just show event.
def dummyAreaEventHandler(event, area, prev_area):
    print(event, end=" : ")
    area.show(args.verbose)


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
    parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='1')
    parser.add_argument('--max', help='Max number of areas', default='10')
    parser.add_argument('--verbose', help="Show verbose", action='store_true')
    parser.add_argument('--info', help="Show info", action='store_true')
    parser.add_argument('--debug', help="Show debug", action='store_true')
    args = parser.parse_args()

    print(" -------------------------------------- ")
    print(" ---- Monitor Areas ---- ")
    print(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug )

    x = threading.Thread(target=monitorAreas, args=(restClient, float(args.interval), args.max, dummyAreaEventHandler), daemon=True )
    x.start()

    time.sleep(2)
    area1 = getAreaByName("Main A to B")
    area2 = getAreaByName("Main C to D")

    area1.close()
    time.sleep(2)
    area2.close()
    time.sleep(2)
    area1.open()
    time.sleep(2)
    area2.open()

    x.join()

