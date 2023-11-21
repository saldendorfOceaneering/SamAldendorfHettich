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
import Missions
import Devices
import Stations
import logging


parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='0.1')
parser.add_argument('--max', help='Max number of missions/devices', default='200')
parser.add_argument('--info', help="Show info", action='store_true')
parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
parser.add_argument('--debug', help="Show  debug information", action='store_true')
parser.add_argument('--config', help='Config file', default='ActionsConfig.json')
parser.add_argument('--multithreading', help="Use multi threading", action='store_true')
args = parser.parse_args()


log = logging.getLogger("MissionsActions")
if (args.debug): level = logging.DEBUG
elif args.info: level = logging.INFO
elif args.verbose: level = logging.INFO
else: level = logging.WARNING

logging.basicConfig(level=level)
Devices.setLoggingLevel(level)
Missions.setLoggingLevel(level)



# mission data has following structure:
#MissionData: 
# 'missionid': str
# 'state': int 
# 'navigationstate': int
# 'transportstate': int
# 'fromnode': str
# 'tonode': str
# 'isloaded': bool 
# 'payload': str
# 'priority': int
# 'assignedto': str
# 'deadline': str
# 'missiontype': int
# 'groupid': int
# 'missionrule': {}
# 'istoday':bool, 
# 'schedulerstate': int
# 'askedforcancellation': bool
# 'parameters': {}

Configuration = {}

def missionEventHandler(event, current_mission, prev_mission):
    if args.verbose: current_mission.show(args.verbose, "missionEventHandler:%s:" % event)
    returnMissionMissionEventHandler(event, current_mission, prev_mission)
    feedbackLightMissionEventHandler(event, current_mission, prev_mission)
    missionOnButtonsMissionEventHandler(event, current_mission, prev_mission)


#######################################
# create return mission when something delivered
########################################
createdReturnMissionForIds = []
def stationAvailableForPickup( station, nLoads=1 ):
    try:
        stocklevel = Stations.getStation(station).stocklevel()
        log.debug("%d loads at %s: available=%s to pickup %d loads" % ( stocklevel, station, stocklevel >= nLoads, nLoads ) )
    except Exception as e:
        log.info("Could not get stocklevel for station %s; assume available for pickup; exception=%s" % ( station, e ) )
        return True
    return stocklevel >= nLoads

def stationAvailableForDropoff( station, nLoads=1 ):
    try:
        freeplaces = Stations.getStation(station).freeplaces()
        log.debug("%d freeplaces at %s: available=%s to dropoff %d loads" % ( freeplaces, station, freeplaces >= nLoads, nLoads ) )
    except Exception as e:
        log.info("Could not get freeplaces for station %s; assume available for pickup: exception %s" % ( station, e ) )
        return True
    return freeplaces >= nLoads
            
def returnMissionMissionEventHandler(event, current_mission, prev_mission):
    missionData = current_mission._missionData
    for returnMission in Configuration["returnMissions"]:
        log.debug("returnMission %s: mission tonode=%s, config delivery=%s" % ( returnMission["description"], missionData['tonode'], returnMission["delivery"] ) )
        if missionData['tonode'] == returnMission["delivery"]:
            loadAtSrc = stationAvailableForPickup( returnMission["from"] )
            roomAtDst = stationAvailableForDropoff( returnMission["to"] )

            if "timetodestination" in missionData.keys():
                log.info("returnMissionMissionEventHandler[%s]: check return for mission[%s] loadAtScr=%s, roomAtDst=%s state=%d, timetodest=%d, createdMissionIds=%s" % ( returnMission["description"], missionData['missionid'], loadAtSrc, roomAtDst, missionData['transportstate'],missionData['timetodestination'], createdReturnMissionForIds  ) )
                # something on its way to delivery station; when less than 4 seconds. create return mission.
                if missionData['transportstate'] == 7 and missionData['timetodestination'] <= returnMission["time_before_finished"] and loadAtSrc and roomAtDst and missionData["missionid"] not in createdReturnMissionForIds: 
                    log.info(f"Something delivered at {returnMission['delivery']}: create return mission {returnMission['description']}" )
                    Missions.createMission( "Transport from station to station", returnMission["description"], returnMission["from"], returnMission["to"], returnMission["payload"], returnMission["priority"] )
                    log.debug("Mark missionid %s to have created return mission for" % missionData["missionid"] )
                    createdReturnMissionForIds.append( missionData["missionid"] )

            if event == "deleted" and missionData["missionid"] in createdReturnMissionForIds:
                log.debug("Remove missionid %s from created return mission for admin" % missionData["missionid"] )
                createdReturnMissionForIds.remove( missionData["missionid"] )


def checkForTimeoutReturnMissions(Configuration):
    for returnMission in Configuration["returnMissions"]:
        if "timeout" in returnMission.keys():
            loadAtSrc = stationAvailableForPickup( returnMission["from"] )
            roomAtDst = stationAvailableForDropoff( returnMission["to"] )
            if args.verbose: log.info("returnMissionMissionEventHandler[%s]: check for timeout %s loadAtSrc=%s, roomAtDst=%s" % ( returnMission["description"], returnMission["timeout"], loadAtSrc, roomAtDst ) )
            if Missions.retrieveMissionByDestination( returnMission['delivery'] ) is None and Missions.retrieveMissionByOrigin( returnMission['from'] ) is None and loadAtSrc and roomAtDst: 
                # nothing on the way to delivery or from return from station; check for timeout
                if not "start_time" in returnMission.keys():
                    returnMission["start_time"] = time.time()
                else:
                    t_elapsed = time.time() - returnMission["start_time"]
                    t_left = returnMission["timeout"] - t_elapsed 
                    log.info("returnMissionMissionEventHandler[%s]: check for timeout: elapsed %s timeout %s left %s loadAtSrc=%s, roomAtDest=%s" % ( returnMission["description"], t_elapsed, returnMission["timeout"], t_left, loadAtSrc, roomAtDst ) )
                    if t_left < 0: 
                        log.info(f"Timeout {t_elapsed} occured on returnMission['from']: create return mission {returnMission['description']}" )
                        Missions.createMission( "Transport from station to station", returnMission["description"], returnMission["from"], returnMission["to"], returnMission["payload"], returnMission["priority"] )
                        del returnMission["start_time"]

            else:
                # reset time
                if "start_time" in returnMission.keys():
                    del returnMission["start_time"]


#######################################
# Set feedback light when mission at pickup station 
########################################
FeedbackLights = []
def feedbackLightMissionEventHandler(event, current_mission, prev_mission):
    missionData = current_mission._missionData
    for feedbackLight in FeedbackLights:
        log.debug("feedbackLightMissionEventHandler: handle %s", feedbackLight.getId())
        if missionData['fromnode'] == feedbackLight.getId():
            if not missionData["isloaded"]:
                log.debug("Check feedback light %s isLightSet(True)=%s" %(feedbackLight.getId(), feedbackLight.isLightSet(True)))
                if not feedbackLight.isLightSet( True ):
                    log.info("##### Time has come to switch ON feedback light %s #####" % feedbackLight.getId())
                    feedbackLight.setLight( True )
                    feedbackLight.setRequestor( missionData["missionid"] )
            if ( ( event == "deleted" or missionData["isloaded"] ) and  
                 ( not feedbackLight.isLightSet (False) and  feedbackLight.compareRequestor( missionData["missionid"] ) )
            ):
                log.info("##### Time has come to switch OFF feedback light %s #####" % feedbackLight.getId())
                feedbackLight.setLight( False )
                feedbackLight.setRequestor( "" )

def setUpFeedbackLights( feedbackLightsConfig ):
    for config in feedbackLightsConfig:
        log.debug("setUpfeedbackLights: for %s", config)
        FeedbackLights.append( FeedbackLight( config ) )

class FeedbackLight:
    def __init__(self, config):
        self._device = Devices.getDevice( config["device"] )
        self._id = config["id"]
        self._requestor = None
        self._on = None

    def getId(self):
        return self._id

    def isLightSet(self, on):
        return self._on is not None and self._on == on

    def setLight(self, on):
        log.debug("setLight %s to %s" % (self._id, on) )
        self._device.set( on );
        self._on = on 

    def setRequestor(self, requestor):
        log.debug("setRequestor %s to %s" % (self._id, requestor) )
        self._requestor = requestor

    def compareRequestor(self, requestor):
        return self._requestor is not None and self._requestor == requestor


#######################################
# Create mission on button pressed
########################################
CreateMissionOnButtons = []

def setUpMissionButtons(missionOnButtonsConfig):
    for config in missionOnButtonsConfig:
        CreateMissionOnButtons.append( CreateMissionOnButtonDevice(config) )


def missionOnButtonsMissionEventHandler(event, current_mission, prev_mission):
    # handle mission events.
    missionData = current_mission._missionData
    if ( event == "deleted" or missionData["isloaded"] ):
        # check if mission is created by a button. If so clear missionid
        for create_mission_on_button in CreateMissionOnButtons:
            if create_mission_on_button._missionid == missionData["missionid"]:
                log.debug("Mission %s at %s picked up; ready for next: clear missionid" % ( missionData["missionid"], create_mission_on_button._config["button"] ) )
                create_mission_on_button._missionid = None
    if ( event == "new" and not missionData["isloaded"] ):
        for create_mission_on_button in CreateMissionOnButtons:
            # disable button if mission for pick is already created; mark missionid
            if "fromnode" in missionData.keys() and create_mission_on_button._missionid is None and create_mission_on_button._config["from"] == missionData["fromnode"]:
                log.debug("Mission %s at %s picked up; already exists: set missionid" % ( missionData["missionid"], create_mission_on_button._config["button"] ) )
                #mark missionid
                create_mission_on_button._missionid = missionData["missionid"]




class CreateMissionOnButtonDevice(Devices.DeviceHandler):
    def __init__(self, config):
        self._button_device = Devices.getDevice(config["button"]) 
        if self._button_device is None:
            log.fatal("FATAL: CreateMissionOnButton: button device %s is not found" % config["button"])
            sys.exit(-2)
        self._config = config
        self._missionid = None
        self._button_device.addEventHandler( self )
        
        
    def handleEvent(self, event, device, prev_device):
        # to be overrules.
        try:
            if device.getValue():
                if self._missionid is None:
                    log.info("Button %s pressed: Create mission %s" % ( self._config["button"], self._config["description"] ) )
                    self._missionid = Missions.createMission( "Transport from station to station", self._config["description"], self._config["from"], self._config["to"], self._config["payload"], self._config["priority"] )
                else:
                    log.warn("Button %s pressed twice (IGNORED)" % self._config["button"])
        except Exception as e: 
            log.warn("CreateMissionOnButtonDevice: Could not handle device event: %s exception: %s" % ( event, str(e) ) )
        


#######################################
# set io at startup
########################################
def setIoAtStartup(setIoAtStartupconfig):
    for config in setIoAtStartupconfig:
        try:
            if config["device"]["type"] == "ANT":
                log.info ("%s: set %s:%s to %s" % ( config["description"], config["device"]["type"], config["device"]["address"], config["value"] ) )
                device = Devices.getDevice(config["device"]["address"])
                device.setValue(config["value"])
        except Exception as e:
            log.fatal("Failed to set io at startup: exception=%s" % e)
            pass
       
            

#######################################
# read configuration json file
########################################

def readConfigFile(filename):
    try:
        with open(filename) as json_file:
           config = json.load(json_file)
    except Exception as e: 
        log.fatal("Could not read config file: %s exception: %s" % ( filename, str(e) ) )
        sys.exit(-1)
    return config


def deviceEventHandler(event, device, prev_device):
    if args.info: device.show(args.verbose, "deviceEventHandler:%s:" % event)



# -----------------------------------------------------------------------------
if __name__ == '__main__':

    if args.verbose:
        args.info = True

    Configuration = readConfigFile(args.config)

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug )
    Devices.setRestClient(restClient)
    Missions.setRestClient(restClient)

    if args.multithreading:
        # start monitoring devices.
        log.info(" ---- Start Monitoring Devices ---- ")
        y = threading.Thread(target=Devices.monitorDevices, args=(float(args.interval), args.max, None), daemon=True )
        y.start()


    Devices.monitorDevices( 0, args.max, None )
    time.sleep(1)
    setUpMissionButtons( Configuration["MissionOnButton"] ) 
    setUpFeedbackLights( Configuration["feedbackLights"] )
    setIoAtStartup( Configuration["SetIoAtStartup"] ) 
    Stations.setupStationTypes( Configuration["StationTypes"] )
    Stations.setupStations( Configuration["Stations"] )

    if args.multithreading:
        log.info(" ---- Start Monitoring Missions ---- ")
        x = threading.Thread(target=Missions.monitorMissions, args=(float(args.interval), args.max, missionEventHandler), daemon=True )
        x.start()

    while True:
        if args.multithreading:
            if not x.is_alive() or not y.is_alive():
                log.fatal("Thread stopped; exiting")
                sys.exit(-1)

        Devices.monitorDevices( 0, args.max, None )
        Missions.monitorMissions( 0, args.max, missionEventHandler )
        checkForTimeoutReturnMissions( Configuration )
        time.sleep(1)

