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
import Devices
import Missions
import Timer
import logging

log = logging.getLogger("Devices")

def setLoggingLevel( level ):
    logging.basicConfig(level=level)


# configuration:
# "id"                        : id 
# "descr"                     : description
# "type"                      : "Pickup" | "Dropoff" | "PickupBuffer" | "DropoffBuffer"
# "load present detection"    : device to indicate transfer location is occupied
#       device      : device type: ANT | Modbus | RJE
#       type        : [optional] entity type e.g. "I/O" or "input register"
#       address     : entity name/address e.g. "A1 Button" or "1"
#       latch time  : [optional] trigger signal. Signal is reset after 'latch time' seconds
#       inverted    : [optional] occupied signal is inverted

Stations = {}
StationTypes = {}
Plcs = {}
Configuration = {}

class Station(Devices.DeviceHandler):
    def __init__(self, config):
        self._config = config;
        self._id = config["id"]
        self._description = config["descr"]
        self._stationType = getStationType(config["type"])
        self._stocklevel = 0
        self._freeplaces = 0

        if "stocklevel device" in config.keys():
            if config["stocklevel device"]["type"] == "ANT":
                self._stocklevel_device = Devices.getDevice(config["stocklevel device"]["address"])
                log.debug("get stocklevel device[%s] %s:%s" % (self._stocklevel_device, config["stocklevel device"]["type"], config["stocklevel device"]["address"]))
            else:
                print("FATAL: stocklevel device type '%s' is not supported" % config["stocklevel device"]["type"] )
                sys.exit(-1)
        else:
            #log.debug("NO stocklevel device for station %s" % self._id)
            self._stocklevel_device = None

        if "freeplaces device" in config.keys():
            if config["freeplaces device"]["type"] == "ANT":
                self._freeplaces_device = Devices.getDevice(config["freeplaces device"]["address"])
                log.debug("get freeplaces device[%s] %s:%s" % (self._freeplaces_device, config["freeplaces device"]["type"], config["freeplaces device"]["address"]))
            else:
                print("FATAL: freeplaces device type '%s' is not supported" % config["freeplaces device"]["type"] )
                sys.exit(-1)
        else:
            #log.debug("NO freeplaces device for station %s" % self._id)
            self._freeplaces_device = None

        if "loadpresent device" in config.keys():
            if "inverted" in config["loadpresent device"]:
                self._loadpresent_inverted = config["loadpresent device"]["inverted"]
            else:
                self._loadpresent_inverted = False
            if config["loadpresent device"]["type"] == "ANT":
                self._loadpresent_device = Devices.getDevice(config["loadpresent device"]["address"])
                log.debug("get loadpresent device[%s] %s:%s" % (self._loadpresent_device, config["loadpresent device"]["type"], config["loadpresent device"]["address"]))
            else:
                print("FATAL: loadpresent device type '%s' is not supported" % config["loadpresent device"]["type"] )
                sys.exit(-1)
        else:
            #log.debug("NO loadpresent device for station %s" % self._id)
            self._loadpresent_device = None

        if "actions" in config.keys():
            self._actions = config["actions"]
        else:
            self._actions = []
        self._loadsOnTransferPositions = []
        self._loadsOnQueuePositions = []

    def handleEvent(self, event, device, prev_device):
        # for now dummy print 
        print("STATION %s: Handle event: %s device %s" %(self._config["id"], event, device.getId()))

    def stocklevel(self):
        if self.TriggerActionsOnEvent("determineStocklevel"):
            return self._stocklevel
        if self._stationType._can_be_pickup:
            if not (self._loadpresent_device is None):
                if (self._loadpresent_device.getValue() and not self._loadpresent_inverted) or (not self._loadpresent_device.getValue() and self._loadpresent_inverted):
                    self._stocklevel = 1
                else:
                    self._stocklevel = 0
                log.debug("Got stocklevel from loadpresent device %s=%s (inverted=%s), stocklevel=%s" % (self._loadpresent_device.getId(), self._loadpresent_device.getValue(), self._loadpresent_inverted, self._stocklevel) )
            elif not (self._stocklevel_device is None):
                # determine stocklevel by device
                self._stocklevel = self._stocklevel_device.getValue()
                log.debug("Got stocklevel from device %s, stocklevel=%s" % (self._stocklevel_device.getId(), self._stocklevel) )
            elif not (self._freeplaces_device is None):
                # determine stocklevel by freeplaces device
                self._stocklevel = (self.getNTransferPositions() + self.getNQueuePositions()) - self._freeplaces_device.getValue()
                log.debug("Got stocklevel from freeplaces device %s, stocklevel=%s" % (self._freeplaces_device.getId(), self._stocklevel) )
            else: 
                self._stocklevel = len(self._loadsOnTransferPositions) + len(self._loadsOnQueuePositions)
                log.debug("Got stocklevel from queue and transfer location sizes, stocklevel=%s" % (self._stocklevel) )
        else:
            self._stocklevel = 0

        return self._stocklevel

    def freeplaces(self):
        if self.TriggerActionsOnEvent("determineFreeplaces"):
            return self._freeplaces
        if self._stationType._can_be_dropoff:
            if not (self._loadpresent_device is None):
                if (self._loadpresent_device.getValue() and self._loadpresent_inverted) or (not self._loadpresent_device.getValue() and not self._loadpresent_inverted):
                    self._freeplaces = 1
                else:
                    self._freeplaces = 0
                log.debug("Got freeplaces from loadpresent device %s=%s (inverted=%s), freeplaces=%s" % (self._loadpresent_device.getId(), self._loadpresent_device.getValue(), self._loadpresent_inverted, self._freeplaces) )
            elif not (self._freeplaces_device is None):
                # determine freeplaces by device
                self._freeplaces = self._freeplaces_device.getValue()
                log.debug("Got freeplaces from device %s, freeplaces=%s" % (self._freeplaces_device.getId(), self._freeplaces) )
            elif not (self._freeplaces_device is None):
                # determine freeplaces by stocklevel device
                self._freeplaces = (self.getNTransferPositions() + self.getNQueuePositions()) - self._stocklevel_device.getValue()
                log.debug("Got freeplaces from stocklevel device %s, freeplaces=%s" % (self._freeplaces_device.getId(), self._freeplaces) )
            else:
                self._freeplaces = (self.getNTransferPositions() + self.getNQueuePositions()) - (len(self._loadsOnTransferPositions) + len(self._loadsOnQueuePositions))
                log.debug("Got freeplaces from queue and transfer location sizes, freeplaces=%s" % (self._freeplaces) )
        else:
            self._freeplaces = 0
        return self._freeplaces

    def sumStocklevel(self, stations):
        self._stocklevel = 0
        for id in stations:
            station = getStation(id)
            self._stocklevel = self._stocklevel + station.stocklevel()

    def sumFreeplaces(self, stations):
        self._freeplaces = 0
        for id in stations:
            station = getStation(id)
            self._freeplaces = self._freeplaces + station.freeplaces()

    def getActions(self):
        return self._actions + self._stationType._actions 

    def getNTransferPositions(self):
        return self._stationType._nTransferPositions

    def getNQueuePositions(self):
        return self._stationType._nQueuePositions

    def putLoad(self, loadId = "Load" ):
        if args.verbose: print("### station %s: putLoad" % self._id)
        if len(self._loadsOnTransferPositions) >= self.getNTransferPositions():
            LogError("put load on station %s, but station transfer location is occupied: '%s')" % (self._id, self._loadsOnTransferPositions) )
        else:    
            self._loadsOnTransferPositions.append(loadId)
            self.TriggerActionsOnEvent("putLoad")

    def pullLoad(self):
        if args.verbose: print("### station %s: pullLoad" % self._id)
        if len(self._loadsOnTransferPositions) == 0:
            LogError("Pull load from station %s, but station transfer location is empty" % self._id )
            return None
        else:    
            self.TriggerActionsOnEvent("pullLoad")
            load = self._loadsOnTransferPositions.pop()
            return load

    def moveLoadFromQueueToTransferPosition(self):
        if args.verbose: print("### station %s: moveLoadFromQueueToTransferPosition" % self._id)
        if len(self._loadsOnQueuePositions) == 0:
            LogError("Move load from queue position; station %s, but station queue location is empty" % self._id )
        else:    
            self.putLoad( self._loadsOnQueuePositions.pop( ) )

    def moveLoadFromTransferToQueuePosition(self):
        if args.verbose: print("### station %s: moveLoadFromTransferToQueuePosition" % self._id)
        if len(self._loadsOnQueuePositions) >= self.getNQueuePositions():
            LogError("Move load from transfer position to queue position; station %s, but station queue location is full (n=%d, max=%d)" % ( self._id, len(self._loadsOnQueuePositions), self.getNQueuePositions() ) )
        else:    
            self._loadsOnQueuePositions.append( self.pullLoad( ) )

    def moveLoadToStation(self, stationId):
        if args.verbose: print("### station %s: moveLoadToStation %s" % ( self._id, stationId ) )
        if len(self._loadsOnQueuePositions) >= 0:
            load = self._loadsOnQueuePositions.pop( )
        else:
            load = self.pullLoad()

        if load is None:
            LogError("Station %s: Move load to station %s, but no load on station" % ( self._id, stationId ) )
        else:
            PutLoadOnStation(stationId, load)

    def moveLoadFromStation(self, stationId):
        if args.verbose: print("### station %s: moveLoadFromStation %s" % ( self._id, stationId ) )
        station = getStation(stationId)
        
        if station is None:
            LogError("Station %s: Move load from station %s, but no station" % ( self._id, stationId ) )
            return
        load = station.pullLoad()

        if load is None:
            LogError("Station %s: Move load from station %s, but no load on station" % ( self._id, stationId ) )
        else:
            self.putLoad( load )

    def CreateMission(self, missionType, fr, to, payload, priority):
        Missions.createMission( MissionType, "Mission on station event %s" % self._id, fr, to, payload, priority )

    def TriggerActionsOnEvent(self, event):
        for action in self.getActions():
            if event == action["onEvent"]:
                if "delay" in action:
                    delay = float(action["delay"])
                else:
                    delay = 0
                if "interval" in action:
                    interval = float(action["interval"])
                else:
                    interval = 0
                arguments = action["arguments"]
                function = None
                if action["function"] == "CreateMission":
                    function = self.CreateMission
                elif action["function"] == "PutLoad":
                    function = self.putLoad
                elif action["function"] == "PutLoadOnStation":
                    function = PutLoadOnStation
                elif action["function"] == "PutLoadOnAllStations":
                    function = PutLoadOnAllStations
                elif action["function"] == "MoveLoadToStation":
                    function = self.moveLoadToStation
                elif action["function"] == "PullLoad":
                    function = self.pullLoad
                elif action["function"] == "PullLoadFromStation":
                    function = PullLoadFromStation
                elif action["function"] == "PullLoadFromAllStations":
                    function = PullLoadFromAllStations
                elif action["function"] == "MoveLoadFromStation":
                    function = self.moveLoadFromStation
                elif action["function"] == "MoveLoadFromQueueToTransferPosition":
                    function = self.moveLoadFromQueueToTransferPosition
                elif action["function"] == "MoveLoadFromTransferToQueuePosition":
                    function = self.moveLoadFromTransferToQueuePosition
                elif action["function"] == "sumFreeplaces":
                    function = self.sumFreeplaces
                elif action["function"] == "sumStocklevel":
                    function = self.sumStocklevel
                else:
                    print("Action %s not supported" % action["function"] )
                    return False
                
                if interval != 0:
                    # start interval at a random time.
                    Timer.CreateIntervalTimer(delay, interval, function, arguments)
                elif delay != 0:
                    Timer.CreateDelayedTimer(delay, function, arguments)
                else:
                    function(arguments)
                return True
        return False



    def show(self, verbose=False):
        #if verbose:
        #    print("%20s : %s" % ( 'config',                 self._config ) )
        self._stationType.show(verbose)
        print('Station %s:' % self._id, end=" : ")
        print('Loads on transfer: %s, Loads on queue: %s' % (self._loadsOnTransferPositions, self._loadsOnQueuePositions ), end=", " ) 
        print('Stocklevel=%s, Freeplaces=%s' % (self.stocklevel(), self.freeplaces() ) ) 

def getStation(id):
    if id in Stations.keys():
        return Stations[id]
    else:
        return None

def PutLoadOnStation(station, loadId = "Load" ):
    try:
        getStation(station).putLoad(loadId)
    except Exception as e:
        print("Could not put load on station '%s' : %s" % (station, str(e) ))

def PutLoadOnAllStations(stations, loadId = "Load" ):
    try:
        for station in stations:
            getStation(station).putLoad(loadId)
    except Exception as e:
        print("Could not put load on station '%s' : %s" % (station, str(e) ))


def PullLoadFromStation(station):
    try:
        getStation(station).pullLoad()
    except Exception as e:
        print("Could not pull load from station '%s' : %s" % (station, str(e) ))

def PullLoadFromAllStations(stations):
    try:
        for station in stations:
            getStation(station).pullLoad()
    except Exception as e:
        print("Could not pull load from station '%s' : %s" % (station, str(e) ))


def LogError( msg ):
    print( "ERROR:", msg )



#station type config 
# "type"              : id
# "nTransferPositions": number of load AGV - Station transfer locations; normally 1 
# "nQueuePositions"   : number of queue positions
# "handling" : [        array with station type specific handlings
#    {
#        "onEvent"   : event this action is triggered
#        "function"  : action being triggered
#        "arguments" : station + these arguments are passed to the action.
#    },
#]
#},

class StationType():
    def __init__(self, config):
        self._config = config
        self._id = config["id"]
        if "can be pickup" in config.keys():
            self._can_be_pickup = config["can be pickup"]
        else:
            self._can_be_pickup = True
        if "can be dropoff" in config.keys():
            self._can_be_dropoff = config["can be dropoff"]
        else:
            self._can_be_dropoff = True
        if "actions" in config.keys():
            self._actions = config["actions"]
        else:
            self._actions = []
        if "nTransferPositions" in config.keys():
            self._nTransferPositions = config["nTransferPositions"]
        else:
            self._nTransferPositions = 1
        if "nQueuePositions" in config.keys():
            self._nQueuePositions = config["nQueuePositions"]
        else:
            self._nQueuePositions = 0

    def show(self, verbose=False):
        #if verbose:
        #    print("StationType: %20s : %s" % ( 'config',                 self._config ) )
        print()



def getStationType(id):
    if id in StationTypes.keys():
        return StationTypes[id]
    else:
        print("StationType '%s' not defined" % id )
        return None


def missionEventHandler(event, current_mission, prev_mission):
    if args.info:
        print("%s" % event, end=" : ")
        current_mission.show(args.verbose)
    missionEvent = None 
    if event == "delete":
        missionEvent = "jobFinished"
    elif event == "new":
        misisonEvent = "jobCreated"
    else:
        isLoaded = current_mission.getIsLoaded()
        if prev_mission is not None:
            wasLoaded = prev_mission.getIsLoaded()
        else:
            wasLoaded = False
        if isLoaded != wasLoaded:
            if isLoaded:
                missionEvent = "jobPickedUp"
            else:
                missionEvent = "jobDroppedOff"
    if missionEvent is not None:
        getStation(current_mission.getFromNode()).TriggerActionsOnEvent(missionEvent)
        getStation(current_mission.getToNode()).TriggerActionsOnEvent(missionEvent)


def monitorStations(interval, eventHandler):
    for id in Stations:
        if args.verbose: print("Check station %s" % Stations[id]._config["id"])
# handle timer event:
#   move load to next buffer location. 
#   handle load i.e. remove from station
#   clear all buffer locations.
    time.sleep(interval)


def setupStations(stationsConfig):
    for config in stationsConfig:
        id = config["id"]
        Stations[id] = Station(config)

def setupStationTypes(stationTypesConfig):
    for config in stationTypesConfig:
        id = config["id"]
        StationTypes[id] = StationType(config)

def setupPlcs(plcs):
    for plc in plcs:
        id = plc["id"]
        if plc["type"] == "modbus":
#            Plcs[id] = Modbus.ModbusServer(plc["ip-address"], plc["port"])
            print("PLC %s is not supported" % plc["type"] )
        else:
            print("PLC type %s is not supported" % plc["type"] )



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
    parser.add_argument('--max', help='Max number of devices', default='150')
    parser.add_argument('--verbose', help="Show verbose info", action='store_true')
    parser.add_argument('--info', help="Show info", action='store_true')
    parser.add_argument('--debug', help="Show debug", action='store_true')
    parser.add_argument('--config', help='Config file', default='StationsConfig.json')
    args = parser.parse_args()

    if (args.debug): level = logging.DEBUG
    elif args.info: level = logging.INFO
    else: level = logging.WARNING
    setLoggingLevel( level )
    Devices.setLoggingLevel( level )

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )
    Missions.setRestClient(restClient)
    Devices.setRestClient(restClient)
    Configuration = readConfigFile(args.config)
    setupPlcs(Configuration["Plcs"])

    if args.info:
        print(" ---- Start Monitoring Devices ---- ")
    x = threading.Thread(target=Devices.monitorDevices, args=(float(args.interval), args.max, None), daemon=True )
    x.start()

    time.sleep(2)

    setupStationTypes(Configuration["StationTypes"])
    setupStations(Configuration["Stations"])


    if args.info:
        print(" ---- Start Monitoring Missions ---- ")
    y = threading.Thread(target=Missions.monitorMissions, args=(float(args.interval), args.max, missionEventHandler), daemon=True )
    y.start()

    if args.verbose:
        print("### StationTypes:")
        for stationType in StationTypes:
            StationTypes[stationType].show(args.verbose)
    if args.verbose:
        print("### Stations:")
        for station in Stations:
            Stations[station].show(args.verbose)


# now start all interval timers.
    for station in Stations:
        Stations[station].TriggerActionsOnEvent("intervalTimer")


    station_A1 = getStation("A1")
    station_F = getStation("F")
    station_G = getStation("G")

    if args.info: print("### Put load on A1")
    station_A1.putLoad()
    station_A1.show(args.verbose)
    time.sleep(1)
    if args.info: print("### Pull load from A1")
    station_A1.pullLoad()
    station_A1.show(args.verbose)

    if args.info: print("### Put load on F; sleep 3")
    station_F.putLoad("L1")
    station_F.show(args.verbose)
    time.sleep(3)
    if args.info: print("### Put load on F; sleep 1")
    station_F.putLoad("L2")
    station_F.show(args.verbose)
    time.sleep(1)
    if args.info: print("### Put load on F; sleep 20")
    station_F.putLoad("L3")
    station_F.show(args.verbose)
    station_G.show(args.verbose)

    time.sleep(20)
    station_F.show(args.verbose)
    station_G.show(args.verbose)
    while x.is_alive() and y.is_alive():
        time.sleep(1)
        monitorStations(float(args.interval), None)

    x.join()
    y.join()
    Timer.CancelAllTimers()
