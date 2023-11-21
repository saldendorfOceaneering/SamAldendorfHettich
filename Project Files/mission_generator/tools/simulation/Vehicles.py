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
import logging


# vehicleData has following structure:
# 'name': str
# 'isloaded': bool 
# 'payload': str
# 'operatingstate': int
# 'state' : 
#    'body.shape': [float, ...] 
#    'traffic.info': ['Free', '', 'Inserted', '', 'parking', '80', '', '', '0.0', '80'] 
#    'mission.progress': [None, None, None, None] 
#    'connection.ok': [bool], 
#    'battery.info.maxtemperature': [int], 
#    'error.bits': ['0,0,256,0,256,0,0,0'], 
#    'sharedMemory.out': [int,...], 
#    'battery.info': ['0', '0.0'] 
#    'vehicle.type': [str] 
#    'vehicle.shape': [float, ...] 
#    'lock.UUID': [str] 
#    'vehicle.state': ['parking', 'false'] 
#    'lock.owner': ['antserver', '24WB1Z2', 'BJordense']
#    'messages': [str,str,...] 
#    'mission.info': ['Parking_AD1', '', ''] 
#    'sharedMemory.in': [int,...] 
#    'errors': [str,..]
                                                                              
log = logging.getLogger("Vehicles")

def setLoggingLevel( level ):
    logging.basicConfig(level=level)

Vehicles = {}

class Vehicle:
    _operatingState = {
        0 : "Not inserted", 
        1 : "Ready",
        2 : "Assigned to a vehicle",
        3 : "Not available",
        4 : "Paused",
        5 : "Asleep",
        6 : "In error",
    }

    def __init__(self, vehicleData):
        self._vehicleData = vehicleData

    def update(self, vehicleData):
        self._vehicleData = vehicleData

    def isChanged(self, vehicleData, stateOnly=False):
        if stateOnly:
            if ( self._vehicleData["isloaded"] != vehicleData["isloaded"] or 
                 self._vehicleData["operatiingstate"] != vehicleData["operatiingstate"] or
                 self._vehicleData["action"] != vehicleData["action"] or
                 self._vehicleData["state"] != vehicleData["state"] or
                 self._vehicleData["stateinfo"] != vehicleData["stateinfo"] or
                 self._vehicleData["isloaded"] != vehicleData["isloaded"]
             ):
                return True
        else:
            if self._vehicleData != vehicleData:
                return True



    def show(self, verbose=False):
        if verbose:
            try:
                if "name" in self._vehicleData:
                    print("%20s : %s" % ( "name",                           self._vehicleData["name"] ) )
                if "isloaded" in self._vehicleData:
                    print("%20s : %s" % ( "isloaded",                       self._vehicleData["isloaded"] ) )
                if "payload" in self._vehicleData:
                    print("%20s : %s" % ( "payload",                        self._vehicleData["payload"] ) )
                if "operatingstate" in self._vehicleData:
                    print("%20s : %s" % ( "operatingstate",                 Vehicle._operatingState[self._vehicleData["operatingstate"]] ) )
                if "state" in self._vehicleData:
                    if 'body.shape' in self._vehicleData['state']:
                        print("%20s : %s" % ( "body.shape",                 self._vehicleData["state"]['body.shape'] ) )
                    if 'traffic.info' in self._vehicleData['state']:
                        print("%20s : %s" % ( "traffic.info",               self._vehicleData["state"]['traffic.info'] ) )
                    if 'mission.progress' in self._vehicleData['state']:
                        print("%20s : %s" % ( "mission.progress",           self._vehicleData["state"]['mission.progress'] ) )
                    if 'connection.ok' in self._vehicleData['state']:
                        print("%20s : %s" % ( "connection.ok",              self._vehicleData["state"]['connection.ok'] ) )
                    if 'battery.info.maxtemperature' in self._vehicleData['state']:
                        print("%20s : %s" % ( "battery.info.maxtemperature",                 self._vehicleData["state"]['battery.info.maxtemperature'] ) )
                    if 'error.bits' in self._vehicleData['state']:
                        print("%20s : %s" % ( "error.bits",                 self._vehicleData["state"]['error.bits'] ) )
                    if 'sharedMemory.out' in self._vehicleData['state']:
                        print("%20s : %s" % ( "sharedMemory.out",           self._vehicleData["state"]['sharedMemory.out'] ) )
                    if 'battery.info' in self._vehicleData['state']:
                        print("%20s : %s" % ( "battery.info",               self._vehicleData["state"]['battery.info'] ) )
                    if 'vehicle.type' in self._vehicleData['state']:
                        print("%20s : %s" % ( "vehicle.type",               self._vehicleData["state"]['vehicle.type'] ) )
                    if 'vehicle.shape' in self._vehicleData['state']:
                        print("%20s : %s" % ( "vehicle.shape",              self._vehicleData["state"]['vehicle.shape'] ) )
                    if 'lock.UUID' in self._vehicleData['state']:
                        print("%20s : %s" % ( "lock.UUID",                  self._vehicleData["state"]['lock.UUID'] ) )
                    if 'vehicle.state' in self._vehicleData['state']:
                        print("%20s : %s" % ( "vehicle.state",              self._vehicleData["state"]['vehicle.state'] ) )
                    if 'lock.owner' in self._vehicleData['state']:
                        print("%20s : %s" % ( "lock.owner",                 self._vehicleData["state"]['lock.owner'] ) )
                    if 'messages' in self._vehicleData['state']:
                        print("%20s : %s" % ( "messages",                   self._vehicleData["state"]['messages'] ) )
                    if 'mission.info' in self._vehicleData['state']:
                        print("%20s : %s" % ( "mission.info",               self._vehicleData["state"]['mission.info'] ) )
                    if 'sharedMemory.in' in self._vehicleData['state']:
                        print("%20s : %s" % ( "sharedMemory.in",            self._vehicleData["state"]['sharedMemory.in'] ) )
                    if 'errors' in self._vehicleData['state']:
                        print("%20s : %s" % ( "errors",                     self._vehicleData["state"]['errors'] ) )
            except Exception as e: 
                print("Exception :", e)
        else:
            print("vehicle[%s] [operationalstate=%s,isloaded=%s] " % (self._vehicleData["name"], Vehicle._operatingState[self._vehicleData["operatingstate"]], self._vehicleData["isloaded"] ) )


def monitorVehicles(restClient, interval, event_handler):
    while True:
        restClient.getSessionToken()
        handledVehicleIds = []
        try: 
            jsonVehicles = restClient.getVehiclesInfo()
            vehicles = jsonVehicles["payload"]["vehicles"]
            for vehicleData in vehicles:
                id = vehicleData["name"]
                if id in Vehicles:
                    if Vehicles[id].isChanged(vehicleData):
                        prev_vehicle = Vehicles[id] 
                        Vehicles[id].update(vehicleData)
                        event_handler("changed", Vehicles[id], prev_vehicle)
                else:
                    Vehicles[id] = Vehicle(vehicleData)
                    event_handler("new", Vehicles[id], None)

                handledVehicleIds.append(id)
        except Exception as e: 
            print("monitorVehicles exception :", e)
        time.sleep(interval)


# dummy event handler for testing; just show event.
def dummyVehicleEventHandler(event, vehicle, prev_vehicle):
    vehicle.show(args.verbose)
    print("--------------")

    
#######################################
# read configuration json file
########################################

def readConfigFile(filename):
    try:
        with open(filename) as json_file:
           config = json.load(json_file)
    except Exception as e: 
        print("Could not read config file: %s exception: %s" % ( filename, str(e) ) )
        sys.exit(-1)
    return config



# -----------------------------------------------------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
    parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='0')
    parser.add_argument('--all', help="Show all vehicles; also finished", action='store_true')
    parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
    parser.add_argument('--info', help="Show info", action='store_true')
    parser.add_argument('--debug', help="Show debug", action='store_true')
    parser.add_argument('--insert_vehicles', help='Insert vehicles specified in json file', default='') 
    args = parser.parse_args()

    print(" -------------------------------------- ")
    print(" ---- Monitor Vehicles ---- ")
    print(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug )

    if (args.debug): level = logging.DEBUG
    elif args.info: level = logging.INFO
    else: level = logging.WARNING
    setLoggingLevel( level )


    if args.insert_vehicles != "":
        Configuration = readConfigFile(args.insert_vehicles)
        for vehicle in Configuration["Initial positions"]:
            log.info( f"Insert vehicle {vehicle['id']} at {vehicle['location']}" )
            restClient.getSessionToken()
            restClient.executeExtractVehicleRESTRequest( vehicle['id'] )
            restClient.executeInsertVehicleRESTRequest( vehicle['id'], vehicle['location'] )
    else:
        x = threading.Thread(target=monitorVehicles, args=(restClient, float(args.interval), dummyVehicleEventHandler), daemon=True )
        x.start()
        x.join()
