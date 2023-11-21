#!/usr/bin/python3

import sys
sys.path.append("../libraries/ANTServerAPI/")
sys.path.append("../libraries/common/")

import ANTServerRESTClient
import datetime
import time
import json
import re
import threading
import argparse
import common


Alarms = {}
counter = 1

class AlarmHandler:

    def handleEvent(self, event, alarm):
        # to be overrules.
        print("Handle event: %s area %s" %(event, alarm.getName()))


class Alarm:
    _stateName = {
        0 : "Active",
        1 : "Acknowledged",
        2 : "Closed",
        3 : "Deleted"
    }
    _sourceType = [
        "Device",
        "Hardware",
        "Station",
        "Vehicle",
        "Mission",

    ]
    def __init__(self, alarmData):
        self._uuid = alarmData["uuid"]
        self._sourceid = alarmData["sourceid"]
        self._sourcetype = alarmData["sourcetype"]
        self._eventname = alarmData["eventname"]
        self._eventcount = alarmData["eventcount"]
        self._state = alarmData["state"]
        self._firsteventat = alarmData["firsteventat"]
        self._lasteventat = alarmData["lasteventat"]
        self._timestamp = alarmData["timestamp"]
        self._eventHandlers = []

    def addEventHandler(self, event_handler):
        self._eventHandlers.append(event_handler)
        
    def getId(self):
        return self._uuid


    def isChanged(self, alarm):
        return self._state != alarm._state

    def show(self, verbose=False):
        print("alarm[%s]: %s @ %s state=%s " % (self.getId(), self._eventname, self._timestamp, self._stateName[self._state] ) ) 


# call the global event handler if it exists and for each areas the registered event handlers.
def callEventHandlers(event, area, prev_area, event_handler): 
    if event_handler != None:
        event_handler(event, area, prev_area)

    for handler in area._eventHandlers:
        handler.handleEvent(event, area, prev_area)
    

def monitorAlarms(restClient, interval, maxAlarms, event_handler):
    while True:
        try:
            restClient.getSessionToken()
            handledAlarmIds = []
            for sourceType in Alarm._sourceType:
                for alarmData in restClient.getAlarms("station"):
                    alarm = Alarm(alarmData)
                    id = alarm.getId()
                    if id in Alarms.keys():
                        if Alarms[id].isChanged(alarm):
                            prev_alarm = Alarms[id]
                            Alarms[id].update(alarm)
                            callEventHandlers("changed", Alarms[id], prev_alarm, event_handler)
                    else:
                        Alarms[id] = alarm
                        callEventHandlers("new", Alarms[id], None, event_handler);
                    handledAlarmIds.append(id)

                deleteAlarmIds = []
                for id in Alarms:
                    if id not in handledAlarmIds:
                        callEventHandlers("deleted", Alarms[id], None, event_handler);
                        deleteAlarmIds.append(id)
                # now realy remove the area.
                for id in deleteAlarmIds:
                        del Alarms[id]
        except Exception as e: 
            print("monitorAlarms: exception :", e)
        if interval == 0:
            return
        else:
            time.sleep(interval)

def getAlarm(id):
    if id in Alarms.keys():
        return Alarms[id]
    else:
        return None


# local test 
# dummy event handler for testing; just show event.
def dummyAlarmEventHandler(event, area, prev_area):
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

    log = common.initLogger( "Alarms", args.debug, args.info )
    log.info(" -------------------------------------- ")
    log.info(" ---- Monitor Alarms ---- ")
    log.info(" -------------------------------------- ")
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )

    x = threading.Thread(target=monitorAlarms, args=(restClient, float(args.interval), args.max, dummyAlarmEventHandler), daemon=True )
    x.start()
    for id in Alarms:
        Alarms[id].show(args.verbose)

    x.join()

