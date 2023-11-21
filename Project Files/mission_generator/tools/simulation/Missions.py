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
import os


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

log = logging.getLogger("Missions")

def setLoggingLevel( level ):
    logging.basicConfig(level=level)

restClient = None

def setRestClient(rest_client):
    global restClient
    restClient = rest_client
            

Missions = {}

class Mission:
    _missionType = {
         0 : "Transport from node to station",
         1 : "Move to station",
         2 : "Waiting lane",
         7 : "Transport to node",
         8 : "Move to node",
         9 : "Transport from station to station",
        10 : "Move a specific vehicle to a node",
        12 : "Move to a loop"
    }
    _priority = {
        1 : "No priority",
        1 : "Low",
        2 : "Medium",
        3 : "High"
    }
    _navigationState = {
        0 : "Received",
        1 : "Accepted",
        2 : "Rejected",
        3 : "Started",
        4 : "Terminated",
        5 : "Cancelled",
    }
    _schedulerState = {
        0 : "A vehicle has been assigned to the mission",
        1 : "There is no vehicle in state ready to get a mission",
        2 : "There are vehicles available to get mission but they cannot reach the mission start node",
        3 : "There are no vehicle of type compatible with the mission",
        4 : "The vehicle associated to this linked mission is not available",
        5 : "for mission of type deadline, the deadline is not reached",
        6 : "for mission of type priority, the priority is too low",
        7 : "7:???",
        8 : "8:???"
    }
    _transportState = {
        0 : "New",
        1 : "Accepted",
        2 : "Rejected",
        3 : "Assigned",
        4 : "Moving",
        5 : "Transporting to selector",
        6 : "Selecting delivery from start",
        7 : "Delivering",
        8 : "Terminated",
        9 : "Cancelled",
        10 : "Error",
        11 : "Cancelling",
        12 : "Selecting pick up node",
        13 : "Selecting delivering from selector",
        14 : "Moving to departure selector",
        23 : "???",
    }
    _stateInfo = {
         0 : "Undefined",
         1 : "Unknown loop",
         2 : "No insertion node into loop",
         3 : "Unknown destination",
         4 : "Transport from unknown location",
         5 : "Transport from unknown station",
         6 : "No node available in pick up station",
         7 : "Unknown station",
         8 : "No node available in drop off station",
         9 : "Unparsable mission request",
        10 : "Timetables are closed",
        11 : "Deadline is in the past",
        12 : "Selecting pick up node",
        13 : "Selecting delivering from selector",
        14 : "Moving to departure selector"
    }

    _state = {
        0 : "Pending",
        1 : "Dispatched to Scheduler",
        2 : "Accepted by Scheduler",
        3 : "Rejected by Scheduler",
        4 : "Missed",
        5 : "Cancelling",
        6 : "Cancelled"
    }

    def __init__(self, missionData):
        self._missionData = missionData

    def update(self, missionData):
        self._missionData = missionData

    def isChanged(self, missionData, stateOnly=False):
        if stateOnly:
            if ( self._missionData["transportstate"] != missionData["transportstate"] or 
                 self._missionData["navigationstate"] != missionData["navigationstate"] or
                 self._missionData["schedulerstate"] != missionData["schedulerstate"] or
                 self._missionData["state"] != missionData["state"] or
                 self._missionData["stateinfo"] != missionData["stateinfo"] or
                 self._missionData["isloaded"] != missionData["isloaded"]
             ):
                return True
        else:
            if self._missionData != missionData:
                return True

    def getToNode(self):
        if "tonode" in self._missionData:
           return self._missionData["tonode"]
        else:
            return None

    def getFromNode(self):
        if "fromnode" in self._missionData:
           return self._missionData["fromnode"]
        else:
            return None

    def getIsLoaded(self):
       return self._missionData["isloaded"]


    def show(self, verbose=False, prefix=""):
        if verbose:
            try:
                print("%20s : %s" % ( "missionid",              self._missionData["missionid"] ) )
                if "payload" in self._missionData:
                    print("%20s : %s" % ( "payload",                self._missionData["payload"] ) )
                if "fromnode" in self._missionData:
                    print("%20s : %s" % ( "fromnode",               self._missionData["fromnode"] ) )
                if "tonode" in self._missionData:
                    print("%20s : %s" % ( "tonode",                 self._missionData["tonode"] ) )
                if "priority" in self._missionData:
                    print("%20s : %s" % ( "priority",               Mission._priority[self._missionData["priority"]] ) )
                if "transportstate" in self._missionData:
                    if self._missionData["transportstate"] in Mission._transportState.keys():
                        print("%20s : %s" % ( "transportstate",     Mission._transportState[self._missionData["transportstate"]] ) )
                    else:
                        print("%20s : %s" % ( "transportstate",     self._missionData["transportstate"] ) )
                if "dispatchtime" in self._missionData:
                    print("%20s : %s" % ( "dispatchtime",           self._missionData["dispatchtime"] ) )
                if "timetodestination" in self._missionData:
                    print("%20s : %s" % ( "timetodestination",      self._missionData["timetodestination"] ) )
                if "navigationstate" in self._missionData:
                    if self._missionData["navigationstate"] in Mission._navigationState.keys():
                        print("%20s : %s" % ( "navigationstate",    Mission._navigationState[self._missionData["navigationstate"]] ) )
                    else:
                        print("%20s : %s" % ( "navigationstate",    self._missionData["navigationstate"] ) )
                if "schedulerstate" in self._missionData:
                    if self._missionData["schedulerstate"] in Mission._schedulerState.keys():
                        print("%20s : %s" % ( "schedulerstate",     Mission._schedulerState[self._missionData["schedulerstate"]] ) )
                    else:
                        print("%20s : %s" % ( "schedulerstate",     self._missionData["schedulerstate"] ) )
                if "totalmissiontime" in self._missionData:
                    print("%20s : %s" % ( "totalmissiontime",       self._missionData["totalmissiontime"] ) )
                if "arrivingtime" in self._missionData:
                    print("%20s : %s" % ( "arrivingtime",           self._missionData["arrivingtime"] ) )
                if "missiontype" in self._missionData:
                    if self._missionData["missiontype"] in Mission._missionType.keys():
                        print("%20s : %s" % ( "missiontype",        Mission._missionType[self._missionData["missiontype"]] ) )
                    else:
                        print("%20s : %s" % ( "missiontype",        self._missionData["missiontype"] ) )
                if "groupid" in self._missionData:
                    print("%20s : %s" % ( "groupid",                self._missionData["groupid"] ) )
                if "missionrule" in self._missionData:
                    print("%20s : %s" % ( "missionrule",            self._missionData["missionrule"] ) )
                if "stateinfo" in self._missionData:
                    if self._missionData["stateinfo"] in Mission._stateInfo.keys():
                        print("%20s : %s" % ( "stateinfo",          Mission._stateInfo[self._missionData["stateinfo"]] ) )
                    else:
                        print("%20s : %s" % ( "stateinfo",          self._missionData["stateinfo"] ) )
                if "assignedto" in self._missionData:
                    print("%20s : %s" % ( "assignedto",             self._missionData["assignedto"] ) )
                if "payloadstatus" in self._missionData:
                    print("%20s : %s" % ( "payloadstatus",          self._missionData["payloadstatus"] ) )
                if "isloaded" in self._missionData:
                    print("%20s : %s" % ( "isloaded",               self._missionData["isloaded"] ) )
                if "istoday" in self._missionData:
                    print("%20s : %s" % ( "istoday",                self._missionData["istoday"] ) )
                if "state" in self._missionData:
                    if self._missionData["state"] in Mission._state.keys():
                        print("%20s : %s" % ( "state",              Mission._state[self._missionData["state"]] ) )
                    else:
                        print("%20s : %s" % ( "state",              self._missionData["state"] ) )
                if "deadline" in self._missionData:
                    print("%20s : %s" % ( "deadline",               self._missionData["deadline"] ) )
            except Exception as e: 
                print("Exception :", e)
        else:
            print("mission[%s] from %s -> %s [state=%s,navigationstate=%s,transportstate=%s,isloaded=%s] " % (self._missionData["missionid"], 
                self._missionData["fromnode"], 
                self._missionData["tonode"], 
                Mission._state[self._missionData["state"]],
                Mission._navigationState[self._missionData["navigationstate"]],
                Mission._transportState[self._missionData["transportstate"]],
                self._missionData["isloaded"] ) 
            )


def monitorMissions(interval, maxMissions, event_handler):
    while True:
        handledMissionIds = []
        try: 
            restClient.getSessionToken()
            for missionData in restClient.getActiveMissions(maxMissions):
                id = missionData["missionid"]
                if id in Missions:
                    if Missions[id].isChanged(missionData):
                        prev_mission = Missions[id] 
                        Missions[id].update(missionData)
                        event_handler("changed", Missions[id], prev_mission)
                else:
                    Missions[id] = Mission(missionData)
                    event_handler("new", Missions[id], None)

                handledMissionIds.append(id)
            # now check if mission is deleted; when mission is not in the list anymore it must be deleted.
            deleteMissionIds = []
            for id in Missions:
                if id not in handledMissionIds:
                    event_handler("deleted", Missions[id], None)
                    deleteMissionIds.append(id)
            for id in deleteMissionIds:
                    del Missions[id]
        except Exception as e: 
            log.warn("monitorMissions exception :", e)
        if interval != 0:
            time.sleep(interval)
        else:
            return

def retrieveMissionByDestination( dest ):
    for id in Missions:
        if Missions[id]._missionData["tonode"] == dest:
            return Missions[id]
    return None

def retrieveMissionByOrigin( origin ):
    for id in Missions:
        if Missions[id]._missionData["fromnode"] == origin:
            return Missions[id]
    return None

def retrieveMissionAtOrigin( origin ):
    for id in Missions:
        if Missions[id]._missionData["fromnode"] == origin and Missions[id]._missionData["isloaded"] == False:
            return Missions[id]
    return None


def createMission( missionType, description, fr, to, payload, priority, sourceNodeType = None, destNodeType = None):
    log.info("###### Generate mission '%s': from=%s to=%s load=%s prio=%s" % (description, fr, to, payload, priority))
    try: 
        restClient.getSessionToken()
        mission = restClient.createMissionData(missionType, fr, to, 1, payload, priority, sourceNodeType=sourceNodeType, destNodeType=destNodeType)
        return restClient.executeCreateMissionRESTRequest(mission)[0]
    except Exception as e:
        log.fatal("Could not create mission: '%s': from=%s to=%s load=%s prio=%s (Exception=%s)" % ( description, fr, to, payload, priority, e ) )
        os._exit(-2)
        


def cancelMission(missionId):
    log.info(f"###### Cancel mission: {missionId}")
    try: 
        restClient.getSessionToken()
        restClient.executeCancelMissionRESTRequest(missionId)
        return True
    except Exception as e:
        log.warn(f"Could not cancel mission: {missionId} exception: {e}")
        return False


def cancelAllMissions():
    log.info(f"###### Cancel all planned missions")
    try: 
        restClient.getSessionToken()
        restClient.executeCancelAllMissionRESTRequest()
        return True
    except Exception as e:
        log.fatal(f"Could not cancel mission: {missionId} exception: {e}")
        os._exit(-2)
 
     
def PauseMissionAssignment(pausestate):
    log.info(f"###### Set mission assignment: {pausestate}")
    try: 
        restClient.getSessionToken()
        restClient.executePauseANTServerRESTRequest(pausestate)
        return True
    except Exception as e:
        log.warn(f"Could not set mission assignment to: {pausestate} exception: {e}")
        return False


# dummy event handler for testing; just show event.
def dummyMissionEventHandler(event, mission, prev_mission):
    mission.show(args.verbose)
    print("--------------")

    


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
    parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='0')
    parser.add_argument('--max', help='Max number of missions', default='100')
    parser.add_argument('--all', help="Show all missions; also finished", action='store_true')
    parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
    parser.add_argument('--info', help="Show info", action='store_true')
    parser.add_argument('--debug', help="Show debug", action='store_true')
    args = parser.parse_args()

    if (args.debug): level = logging.DEBUG
    elif args.info: level = logging.INFO
    else: level = logging.WARNING
    setLoggingLevel( level )

    log.info(" -------------------------------------- ")
    log.info(" ---- Monitor Missions ---- ")
    log.info(" -------------------------------------- ")
    setRestClient( ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug ) )

    x = threading.Thread(target=monitorMissions, args=(float(args.interval), args.max, dummyMissionEventHandler), daemon=True )
    x.start()
    x.join()
