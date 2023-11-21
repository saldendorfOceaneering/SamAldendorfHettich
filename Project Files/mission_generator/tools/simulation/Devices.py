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
import logging
import common

log = logging.getLogger("Devices")

def setLoggingLevel( level ):
    logging.basicConfig(level=level)

# device data has following structure:
# note: deviceid is forced to be unique across the project
#deviceData:
# 'node': str
# 'meta': 
#      'driverid': str
#      'hardwareid': str
#      'state': 
#           'isconnected': bool
#           'state': {}
#           'timestamp':  str
#      'deviceid': str
#      'devicetype': str 
# 'location': 
#       'coord': [float, float, float], 
#       'course': int
#       'currentnode': 
#            'name': str
#            'id': int
#       'map': str
#       'group': str
# 'type': str
# 'class': str
# 'enabled': bool
# 'group': str


restClient = None

def setRestClient(rest_client):
    global restClient
    restClient = rest_client
            
Devices = {}

class DeviceHandler:

    def handleEvent(self, event, device, prev_device):
        # to be overrules.
        print("Handle event: %s device %s" %(event, device.getId()))


class Device:
    def __init__(self, deviceData):
        self._deviceData = deviceData
        self._eventHandlers = []

    def addEventHandler(self, event_handler):
        self._eventHandlers.append(event_handler)
        

    def getId(self):
        return self._deviceData['meta']['deviceid']

    def getType(self):
        return self._deviceData['meta']['devicetype']

    def update(self, deviceData):
        self._deviceData = deviceData

    def isChanged(self, deviceData):
        d = self._deviceData
        d['meta']['state']['timestamp'] = deviceData['meta']['state']['timestamp'] 
        return d != deviceData

    def isEnabled(self):
        return self._deviceData['enabled']

    def getStationName(self):
        if 'group' in self._deviceData:
            return self._deviceData['group']
        else:
            return "NO STATION"

    def show(self, verbose=False):
        if verbose:
            try:
                print("%20s : %s" % ( 'deviceid   ',                self.getId() ) )
                if 'meta' in self._deviceData:
                    if 'devicetype' in self._deviceData['meta']:
                        print("%20s : %s" % ( 'devicetype   ',              self._deviceData['meta']['devicetype'] ) )
                    if 'state' in self._deviceData['meta']:
                        if 'isconnected' in self._deviceData['meta']['state']:
                            print("%20s : %s" % ( 'isconnected ',             self._deviceData['meta']['state']['isconnected'] ) )
                        if 'state' in self._deviceData['meta']['state']:
                            print("%20s : %s" % ( 'state ',                   self._deviceData['meta']['state']['state'] ) )
                        if 'timestamp' in self._deviceData['meta']['state']:
                            print("%20s : %s" % ( 'timestamp ',               self._deviceData['meta']['state']['timestamp'] ) )
                    if 'hardwareid' in self._deviceData['meta']:
                        print("%20s : %s" % ( 'hardwareid     ',              self._deviceData['meta']['hardwareid'] ) )
                if 'enabled' in self._deviceData:
                    print("%20s : %s" % ( 'enabled      ',                    self._deviceData['enabled'] ) )
                if 'node' in self._deviceData:
                    print("%20s : %s" % ( 'node       ',                       self._deviceData['node'] ) )
                if 'location' in self._deviceData:
                    print("%20s :" % ( 'location         ') )
                    if 'coord' in self._deviceData['location']:
                        print("%20s : %s" % ( 'coord     ',                   self._deviceData['location']['coord'] ) )
                    if 'course' in self._deviceData['location']:
                        print("%20s : %s" % ( 'course     ',                  self._deviceData['location']['course'] ) )
                    if 'currentnode' in self._deviceData['location']:
                        print("%20s :" % ( 'currentnode     ') )
                        if 'name' in self._deviceData['location']['currentnode']:
                            print("%20s : %s" % ( 'name ',                    self._deviceData['location']['currentnode']['name'] ) )
                        if 'id' in self._deviceData['location']['currentnode']:
                            print("%20s : %s" % ( 'id ',                      self._deviceData['location']['currentnode']['id'] ) )
                    if 'map' in self._deviceData['location']:
                        print("%20s : %s" % ( 'map     ',                     self._deviceData['location']['map'] ) )
                    if 'group' in self._deviceData['location']:
                        print("%20s : %s" % ( 'group     ',                   self._deviceData['location']['group'] ) )
                if 'type' in self._deviceData:
                    print("%20s : %s" % ( 'type      ',                       self._deviceData['type'] ) )
                if 'class' in self._deviceData:
                    print("%20s : %s" % ( 'class      ',                      self._deviceData['class'] ) )
                if 'group' in self._deviceData:
                    print("%20s : %s" % ( 'group      ',                      self._deviceData['group'] ) )
            except Exception as e: 
                print("Exception missing:", e)
        else:
            print("device %s @ %s state=%s enabled=%s" % (self._deviceData["meta"]["deviceid"], self._deviceData["meta"]["state"]["timestamp"], self._deviceData["meta"]["state"]["state"], self._deviceData["enabled"]) ) 


class IO(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("IO: '%s': state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        if 'value' in self._deviceData['meta']['state']['state']:
            return (self._deviceData['meta']['state']['state']['value'] == 1)
        else:
            return False

    def set(self, on):
        log.debug("IO.set %s to %s" % (self.getId(), on) )
        restClient.executeSetIOValueRESTRequest(self._deviceData['meta']['deviceid'], "%s" % on)

class OPC_UA_Node(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("OPC_UA_Node: '%s': state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        if 'value' in self._deviceData['meta']['state']['state']:
            return (self._deviceData['meta']['state']['state']['value'] == True)
        else:
            return False

    def set(self, on):
        log.debug("OPC_UA_NODE.set %s to %s" % (self.getId(), on) )
        restClient.executeSetIOValueRESTRequest(self._deviceData['meta']['deviceid'], "%s" % on)


class DigitalDetector(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("DigitalDetector: '%s' state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        return self._deviceData['meta']['state']['state']['presencedetected']


class OPC_UA_DigitalDetector(Device):
    def show(self, verbose=False):
        if args.verbose:
            Device.show(self, args.verbose)
        else:
            print ("OPC_UA_DigitalDetector: '%s' state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        log.debug ("OPC_UA_DigitalDetector: '%s' state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state']) )
        if 'Presence' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['Presence']
        else:
            return False

class PresenceDetector(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("PresenceDetector: '%s': state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        if 'label' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['label'] == "Presence detected"
        else:
            return False

class FireDetector(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("FireDetector: '%s': state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        return self._deviceData['meta']['state']['state']['label'] != 'No fire detected' 

class OPC_UA_FireDetector(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("FireDetector: '%s': state=%s, getValue()=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'], self.getValue() ) )

    def getValue(self):
        if 'label' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['label'] != 'No fire detected' 
        else:
            return False

class DigitalReader(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("DigitalReader: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

    def getValue(self):
        if 'Presence' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['Presence']
        else:
            return False

    def getMissionId(self):
        if 'missionid' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['missionid']
        else:
            return 0


class OPC_UA_DigitalReader(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("OPC_UA_DigitalReader: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

    def getValue(self):
        if 'Presence' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['Presence']
        else:
            return False

    def getMissionId(self):
        if 'missionid' in self._deviceData['meta']['state']['state']:
            return self._deviceData['meta']['state']['state']['missionid']
        else:
            return 0

class OPC_UA_Door(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("OPC_UA_DgitalReader: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

    def getValue(self):
        return self._deviceData['meta']['state']['state']

    def setValue(self, value):
        print(" ##### OPC_UA_DOOR setValue: TO BE IMPLEMENTED #####")


class ChangeDirection(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("ChangeDirection: '%s'" % (self._deviceData['meta']['deviceid'] ) )

class Arrival(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("Arrival: '%s'" % (self._deviceData['meta']['deviceid'] ) )

class ArrivalSelector(Device):
    def __init__(self, deviceData):
        Device.__init__(self, deviceData)
        self._stations = []

    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("ArrivalSelector: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

    def setStations(self, stations):
        log.debug("ArrivalSelector[%s] set stations: %s" % (self.getId(), stations) )
        self._stations = stations

    def getValue(self):
        # ArrivalSelector is loaded when all positions are loaded.
        return self.freeplaces() <= 0

    # count the number of available locations.
    def freeplaces(self):
        log.debug("ArrivalSelector[%s]: station=%s" % (self.getId(), self._stations ) )
        n = 0
        for station in self._stations:
            try: 
                device = getDevice(station)
                log.debug("ArrivalSelector[%s]: station[%s].getValue()=%s, (n=%d)" % (self.getId(), station, device.getValue(), n ) )
                if not device.getValue(): 
                    n = n + 1
            except Exception as e: 
                log.warn("ArrivalSelector.count() Station %s: Assume no load present. exception: %s" %( station,  e))
        return n


class Departure(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("Departure: '%s'" % (self._deviceData['meta']['deviceid'] ) )

class SmartDeparture(Device):
    def __init__(self, deviceData):
        Device.__init__(self, deviceData)
        self._stations = []

    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("SmartDeparture: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

    def getValue(self):
        # DepartureSelector is loaded when any positions is loaded.
        return self.stocklevel() > 0

    # count the number of available locations.
    def stocklevel(self):
        log.debug("ArrivalSelector[%s]: station=%s" % (self.getId(), self._stations ) )
        n = 0
        for station in self._stations:
            try: 
                device = getDevice(station)
                log.debug("ArrivalSelector[%s]: station[%s].getValue()=%s, (n=%d)" % (self.getId(), station, device.getValue(), n ) )
                if device.getValue(): 
                    n = n + 1
            except Exception as e: 
                log.warn("ArrivalSelector.count() Station %s: Assume no load present. exception: %s" % (station, e ))
        return n

    def setStations(self, stations):
        log.debug("SmartDeparture[%s] set stations: %s" % (self.getId(), stations) )
        self._stations = stations

class Parking(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("Parking: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

class Charger(Device):
    def show(self, verbose=False):
        if verbose:
            Device.show(self, verbose)
        else:
            print ("Charger: '%s': state=%s" % (self._deviceData['meta']['deviceid'], self._deviceData['meta']['state']['state'] ) )

# call the global event handler if it exists and for each devices the registered event handlers.
def callEventHandlers(event, device, prev_device, event_handler): 
    if event_handler != None:
        event_handler(event, device, prev_device)

    for handler in device._eventHandlers:
        handler.handleEvent(event, device, prev_device)
    

def monitorDevices(interval, maxDevices, event_handler):
    while True:
        try:
            handledDeviceIds = []
            restClient.getSessionToken()
            for deviceData in restClient.executeGetDeviceListRESTRequest(maxDevices):
                id = deviceData["meta"]["deviceid"]
                if id in Devices.keys():
                    if Devices[id].isChanged(deviceData):
                        prev_device = Devices[id]
                        Devices[id].update(deviceData)
                        callEventHandlers("changed", Devices[id], prev_device, event_handler);
                else:
                    if deviceData['meta']['devicetype'] == 'i/o':
                         Devices[id] = IO(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opcua-node':
                         Devices[id] = OPC_UA_Node(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opcua-input':
                         Devices[id] = OPC_UA_Node(deviceData)
                    elif deviceData['meta']['devicetype'] == 'arrival-selector':
                         Devices[id] = ArrivalSelector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'smart-departure':
                         Devices[id] = SmartDeparture(deviceData)
                    elif deviceData['meta']['devicetype'] == 'digitaldetector':
                         Devices[id] = DigitalDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opc-ua-digital-detector':
                         Devices[id] = OPC_UA_DigitalDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'presence-detector':
                         Devices[id] = PresenceDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opcua-presence-detector':
                         Devices[id] = PresenceDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'digitalreader':
                         Devices[id] = DigitalReader(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opc-ua-digital-reader':
                         Devices[id] = OPC_UA_DigitalReader(deviceData)
                    elif deviceData['meta']['devicetype'] == 'fire-detector':
                         Devices[id] = FireDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opcua-fire-detector':
                         Devices[id] = OPC_UA_FireDetector(deviceData)
                    elif deviceData['meta']['devicetype'] == 'opcua-door-driver':
                         Devices[id] = OPC_UA_Door(deviceData)
                    elif deviceData['meta']['devicetype'] == 'arrival':
                         Devices[id] = Arrival(deviceData)
                    elif deviceData['meta']['devicetype'] == 'departure':
                         Devices[id] = Departure(deviceData)
                    elif deviceData['meta']['devicetype'] == 'change-direction':
                         Devices[id] = ChangeDirection(deviceData)
                    elif deviceData['meta']['devicetype'] == 'parking':
                         Devices[id] = Parking(deviceData)
                    elif deviceData['meta']['devicetype'] == 'charger':
                         Devices[id] = Charger(deviceData)
                    else:
                        Devices[id] = Device(deviceData)
                    callEventHandlers("new", Devices[id], None, event_handler);
                handledDeviceIds.append(id)

            deleteDeviceIds = []
            for id in Devices:
                if id not in handledDeviceIds:
                    callEventHandlers("deleted", Devices[id], None, event_handler);
                    deleteDeviceIds.append(id)
            # now realy remove the device.
            for id in deleteDeviceIds:
                    del Devices[id]
        except Exception as e: 
            print("monitorDevices: exception :", e)
        if interval != 0:
            time.sleep(interval)
        else:
            # no interval just do it once...
            return

def getDevice(id):
    if id in Devices.keys():
        return Devices[id]
    else:
        return None


# local test 
# dummy event handler for testing; just show event.
def dummyDeviceEventHandler(event, device, prev_device):
    print(event, end=" : ")
    device.show(args.verbose)


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
    parser.add_argument('--interval', help='Monitor every interval seconds (when zero only do it once)', default='0')
    parser.add_argument('--max', help='Max number of devices', default='150')
    parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
    parser.add_argument('--debug', help="Show debug", action='store_true')
    parser.add_argument('--info', help="Show debug", action='store_true')
    args = parser.parse_args()

    if (args.debug): level = logging.DEBUG
    elif args.info: level = logging.INFO
    else: level = logging.WARNING
    setLoggingLevel( level )


    print(" -------------------------------------- ")
    print(" ---- Monitor Devices ---- ")
    print(" -------------------------------------- ")
    setRestClient( ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host, debug=args.debug ) )

    x = threading.Thread(target=monitorDevices, args=(float(args.interval), args.max, dummyDeviceEventHandler), daemon=True )
    x.start()
    x.join()

    time.sleep(20)

    try:
        ArrivalSelector_D = getDevice("Arrival-selector D")
        ArrivalSelector_D.setStations(["D1 Load presence", "D2 Load presence", "D3 Load presence", "D4 Load presence", "D5 Load presence"]) 
    except Exception as e: 
        print ("Could not set stations in 'Arrival-selector D'" )
        print("Exception:", e)

    try:
        smart_departure_E = getDevice("Departure-selector E")
        smart_departure_E.setStations(["E1", "E2", "E3", "E4", "E5", "E6"]) 
    except Exception as e: 
        print ("Could not set stations in 'Departure-selector E'" )
        print("Exception:", e)

    try:
        ArrivalSelector_H = getDevice("Arrival-selector H")
        ArrivalSelector_H.setStations(["H1 Load presence", "H2 Load presence", "H3 Load presence", "H4 Load presence", "H5 Load presence", "H6 Load presence"]) 
    except Exception as e: 
        print ("Could not set stations in 'arrival-selector H'" )
        print("Exception:", e)

    for name in Devices:
        print("Device[%s]" % (Devices[name].getId()), end=":" ) 
        try:
            getValue = Devices[name].getValue()
            print("getValue()=%s" % getValue, end=" ") 
        except: 
            pass

        try:
            count = Devices[name].stocklevel()
            print(" stocklevel()=%s" % count, end="" ) 
        except: 
            pass

        try:
            count = Devices[name].freeplaces()
            print(" freeplaces()=%s" % count, end="" ) 
        except: 
            pass
            
        print("")

    button_A1 = getDevice("A1 Button")
    feedback_A1 = getDevice("A1 Feedback light")

    try:
        print("A1 Button is %s" % button_A1.getValue() )
        print("A1 feedback light is %s" % feedback_A1.getValue() )
        print("Set A1 feedback light" )
        feedback_A1.set(True)
        time.sleep(10)
        monitorDevices(0, args.max, dummyDeviceEventHandler )
        print("A1 feedback light is %s" % feedback_A1.getValue() )
        print("Reset A1 feedback light" )
        feedback_A1.set(False)
        time.sleep(2)
        monitorDevices(0, args.max, dummyDeviceEventHandler )
        print("A1 feedback light is %s" % feedback_A1.getValue() )
        print("E1_Load_Detector=%s" % E1_Load_Detector.getValue() )
        time.sleep(2)
        print("Set E1_Load_Detector" )
        E1_Load_Detector.set(True)
        time.sleep(2)
        print("E1_Load_Detector=%s" % E1_Load_Detector.getValue() )
    except Exception as e: 
        print (" could not read 'A1 Button' or set 'A1 Feedback light'" )
        print("Exception:", e)

