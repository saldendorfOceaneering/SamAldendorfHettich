#!/usr/bin/python3


import sys
from os import path
import json
import urllib
from urllib import request
from urllib.request import Request
from datetime import datetime
import logging
import datetime
import time


# ==============================================================================
class ANTServerRestClient():
    '''
    Rest client to send Rest requests and to receive Rest responses
    '''
    def __init__(self, ipAddress="localhost", portNumber=8081, username="admin", password="123456", debug=False): 
        ''' Initialize connection url. '''
        self._hostUrl = "{0}:{1}".format(ipAddress, portNumber)
        self._ipAddress = ipAddress
        self._portNumber = portNumber
        self._requestor = "admin"
        self._debug = debug
        self._missionType = {
            "transport from node to station" : "0",
            "move to station" : "1",
            "waiting lane" : "2",
            "transport from node to node" : "7",
            "move to node" : "8",
            "transport from station to station" : "9",
            "move a specific vehicle to a node" : "10",
            "move to a loop" : "12" 
        }
        self._priority = {
            "low" : 1,
            "medium" : 2,
            "high" : 3
        }
        self._sessionToken = ""
        now = datetime.datetime.utcnow()
        timeFormat = "%Y-%m-%dT%H:%M:%S.%mZ"
        self._currentTime = now.strftime(timeFormat)
        
        self._restLoginRequestPath = "http://"+self._hostUrl+f"/wms/monitor/session/login?username={username}&pwd={password}"
        self._restVehicleRequestPath = "http://"+self._hostUrl+"/wms/rest/vehicles"
        self._restStationRequestPath = "http://"+self._hostUrl+"/wms/rest/groups"
        self._restDeviceRequestPath = "http://"+self._hostUrl+"/wms/rest/devices"
        self._restMissionRequestPath = "http://"+self._hostUrl+"/wms/rest/missions"
        self._restMissionRulesPath = "http://"+self._hostUrl+"/wms/rest/missionsrules"
        self._restChangeMissionPriorityRequestPath = "http://"+self._hostUrl+"/wms/rest/missioncommands"
        self._restApplicationRequestPath = "http://"+self._hostUrl+"/wms/rest/application"
        self._restServerRequestPath = "http://"+self._hostUrl+"/wms/rest/server"
        self._restApplicationNavigationSettingsRequestPath = "http://"+self._hostUrl+"/wms/rest/application/navigationsettings"
        self._restAlarmsRequestPath = "http://"+self._hostUrl+"/wms/rest/alarms"
        self._restAlarmsSettingsRequestPath = "http://"+self._hostUrl+"/wms/rest/alarmssettings"
        self._restLoopsRequestPath = "http://"+self._hostUrl+"/wms/rest/loops"
        self._restAreasRequestPath = "http://"+self._hostUrl+"/wms/rest/areas"
        self._restMapRequestPath = "http://"+self._hostUrl+"/wms/rest/maps/level/1/data"

        self._sessionTokenPath = "?&sessiontoken="

    def checkConnection(self):
        ''' verify that connection is possible'''
        import socket
        socketConnection = None
        try:
            print("Checking connection to address '%s' on port %d", self._ipAddress, self._portNumber)
            socketConnection = socket.create_connection((self._ipAddress, self._portNumber), 10)
            print("Connection established")
            return True
        except:
            print("Connection could not be established")
        finally:
            try:
                if socketConnection is not None:
                    socketConnection.close()
            except:
                pass
        return False


    # -----------------------------------
    # Method to call when starting a session with ANT server
    def getSessionToken(self):
        loginResp = self.executeRESTRequest(self._restLoginRequestPath, "GET")
        jsonLogin = json.loads(loginResp)
        self._sessionToken = str(jsonLogin["payload"]["sessiontoken"])


    def executeRESTRequest(self, requestPath, method, data=None):

        # Replace all spaces in the request by %20
        requestPath = requestPath.replace(" ", "%20")

        ''' send REST request and get response'''
        timeout = 10 * 60 #seconds
        if self._debug:
            print(" REQ:", requestPath)
        try:
            req = Request(requestPath, data=data)
            if method is not None:
                req.get_method = lambda: method

            response = request.urlopen(req, data, timeout=timeout).read().decode('utf-8')
            if self._debug:
                print("RESP:", response)
            return response

        except Exception as e:
            print("\tERROR: Unable to process request '%s': %s", requestPath, e)
            raise


    # -----------------------------------
    # insert a vehicle at a specified node
    def executeInsertVehicleRESTRequest(self, vehicleName, nodeId):
        ''' Execute REST request to insert a vehicle at a given node'''
        if self._debug:
            print("Inserting vehicle : " + vehicleName + " on node : " + nodeId)
        insertData = {}
        insertCommand = {}
        insertCommand["name"]  = "insert"
        insertArgs = {}
        insertArgs["nodeId"]  = str(nodeId)
        insertCommand["args"] = insertArgs
        insertData["command"] = insertCommand

        if self._debug:
            print (str(insertData))
        
        requestData = json.JSONEncoder().encode(insertData)
        vehicleResp = self.executeRESTRequest(self._restVehicleRequestPath + "/" + vehicleName + "/command" + self._sessionTokenPath +self._sessionToken, "POST", requestData.encode('utf-8'))

        jsonVehicles = json.loads(vehicleResp)
        vehicles = jsonVehicles["payload"]["vehicle"]
        return vehicles


    # -----------------------------------
    # extract a vehicle from traffic
    def executeExtractVehicleRESTRequest(self, vehicleName):
        ''' Execute REST request to extract a vehicle'''
        if self._debug:
            print("Extract vehicle : " + vehicleName )
        extractData = {}
        extractCommand = {}
        extractCommand["name"]  = "extract"
        extractArgs = {}
        extractCommand["args"] = extractArgs
        extractData["command"] = extractCommand

        requestData = json.JSONEncoder().encode(extractData)
        vehicleResp = self.executeRESTRequest(self._restVehicleRequestPath + "/" + vehicleName + "/command" + self._sessionTokenPath +self._sessionToken, "POST", requestData.encode('utf-8'))

        jsonVehicles = json.loads(vehicleResp)
        vehicles = jsonVehicles["payload"]["vehicle"]
        return vehicles


    # -----------------------------------
    # set value of an IO
    def executeSetIOValueRESTRequest(self, IOName, value):
        ''' Execute REST request to set IO device '''
        if self._debug:
            print("Setting IO : " + IOName + " to value : " + str(value))
        ioData = {}
        ioCommand = {}
        ioCommand["name"]  = "write"
        ioArgs = {}
        ioArgs["value"]  = str(value)
        ioCommand["args"] = ioArgs
        ioData["command"] = ioCommand

        if self._debug:
            print (str(ioData))

        requestLink = self._restDeviceRequestPath + "/" + IOName + "/command" + self._sessionTokenPath +self._sessionToken
        requestData = json.JSONEncoder().encode(ioData)
        if self._debug:
            print( "executeSetIOValueRESTRequest: requestLink %s" % requestLink )
            print( "executeSetIOValueRESTRequest: requestData %s" % requestData )
        ioResp = self.executeRESTRequest(requestLink , "POST", requestData.encode('utf-8'))
        
        if self._debug:
            print( "executeSetIOValueRESTRequest: ioResp %s" % ioResp );
        return



    # -----------------------------------
    # Extract all vehicles from traffic
    def executeExtractAllVehicleRESTRequest(self):
        ''' Execute REST request to extract all vehicles '''
        print("Extracting all vehicles : ")
        vehicleList = self.executeGetVehicleListRESTRequest()

        for vehicle in vehicleList:
            vehicleName = vehicle["name"]
            self.executeExtractVehicleRESTRequest(vehicleName)

        return vehicleList


    # -----------------------------------
    # Get the list of all vehicles
    def executeGetVehicleListRESTRequest(self):
        try:
            vehicles = self.executeRESTRequest(self._restVehicleRequestPath + self._sessionTokenPath + self._sessionToken, "GET")
            jsonVehicles = json.loads(vehicles)
            vehicleList = jsonVehicles["payload"]["vehicles"]
        except:
            print( "executeGetVehicleListRESTRequest: EXCEPT" )
            vehicleList = []
        return vehicleList


    # -----------------------------------
    # Get the list of all devices
    def executeGetDeviceListRESTRequest(self, nbrOfDevices):
        try:
            devices = self.executeRESTRequest(self._restDeviceRequestPath + self._sessionTokenPath + self._sessionToken + "&datarange=%5B0%2C" + str(nbrOfDevices) + "%5D",  "GET")
            jsonDevices = json.loads(devices)
            if self._debug:
                print( "jsonDevices=%s" % jsonDevices )
            deviceList = jsonDevices["payload"]["devices"]
        except:
            print( "executeGetDeviceListRESTRequest: retcode = %d" % jsonDevices["retcode"] )
            deviceList = []
        return deviceList

    # -----------------------------------
    # Get the list of all areas
    def executeGetAreaListRESTRequest(self, nbrOfAreas):
        #areas = self.executeRESTRequest(self._restAreasRequestPath + self._sessionTokenPath + self._sessionToken + "&datarange=%5B0%2C" + str(nbrOfAreas) + "%5D",  "GET")
        areas = self.executeRESTRequest(self._restAreasRequestPath + self._sessionTokenPath + self._sessionToken,  "GET")
        jsonAreas = json.loads(areas)
        if self._debug:
            print( "jsonAreas=%s" % jsonAreas )
        areaList = jsonAreas["payload"]["areas"]
        return areaList

    def executeOpenAreaRESTRequest(self, areaId, open):
        ''' Execute REST request to set area open '''
        if self._debug:
            print("Setting area : " + areaId + " to value : " + value)
        areaData = {}
        areaCommand = {}
        areaCommand["name"]  = "open"
        areaArgs = {}
        if open:
            areaArgs["open"]  = "true"
        else:
            areaArgs["open"]  = "false"
        areaCommand["args"] = areaArgs
        areaData["command"] = areaCommand

        if self._debug:
            print (str(areaData))

        requestLink = self._restAreasRequestPath + "/" + str(areaId) + "/command" + self._sessionTokenPath + self._sessionToken
        requestData = json.JSONEncoder().encode(areaData)
        if self._debug:
            print( "executeOpenAreaRESTRequest: requestLink %s" % requestLink )
            print( "executeOpenAreaRESTRequest: requestData %s" % requestData )
        areaResp = self.executeRESTRequest(requestLink , "POST", requestData.encode('utf-8'))
        
        if self._debug:
            print( "executeSetIOValueRESTRequest: areaResp %s" % areaResp );
        return
            
            
    # -----------------------------------
    # Create a new mission
    def executeCreateMissionRESTRequest(self, missionData):
        if self._debug:
            print("Create Mission Request : ")
            print("request data : " + missionData)
    
        requestLink = self._restMissionRequestPath + self._sessionTokenPath + self._sessionToken
        missions = self.executeRESTRequest(requestLink, "POST", missionData.encode('utf-8'))

        jsonMissions = json.loads(missions)
        if self._debug:
            print("reponse from ANT server :")
            print(str(jsonMissions))
        try: 
            createdMissions = jsonMissions["payload"]["acceptedmissions"] + jsonMissions["payload"]["pendingmissions"]
            return createdMissions   
        except Exception as e:
            print("executeCreateMissionRESTRequest: could not retrieve acceptedmissions + pendingmissions; exception: %s" % e)
            return None

    # -----------------------------------
    # change the priority of a mission
    def executeChangeMissionPriorityRequest(self, missionid, prio ):
        if self._debug:
            print("Change mission priority : " + missionid + " prio : " + prio )

        insertData = {}
        insertCommand = {}                  
        insertCommand["name"]  = "setPriority"
        insertArgs = {}
        try: 
            insertArgs["priority"]  = self._priority[prio.lower()]
        except:
            print("priority %s not defined; use medium priority", prio)
            insertArgs["priority"]  = self._priority["medium"]
        insertCommand["args"] = insertArgs
        insertData["command"] = insertCommand
    
        if self._debug:
            print (str(insertData))
        
        requestData = json.JSONEncoder().encode(insertData)

        requestLink = self._restChangeMissionPriorityRequestPath + "/" + missionid + "/command" + self._sessionTokenPath +self._sessionToken
        missionResp = self.executeRESTRequest( requestLink, "POST", requestData.encode( 'utf-8' ) )
        
        jsonMission = json.loads(missionResp)
        try:
            mission = jsonMission["payload"]["missions"]
        except:
            print( "executeChangeMissionPriorityRequest: json=%s" % jsonMission )
            mission = []
        return mission 

    # -----------------------------------
    # Get the list of all missions
    def executeGetMissionListRESTRequest(self, nbrOfMissions):
        requestLink = self._restMissionRequestPath + self._sessionTokenPath + self._sessionToken
        requestLink += "&datarange=%5B0%2C" + str(nbrOfMissions) + "%5D"
        missions = self.executeRESTRequest( requestLink, "GET")
        jsonMissions = json.loads(missions)
        missionList = jsonMissions["payload"]["missions"]
        return missionList
    
    
    # -----------------------------------
    # Get the list of all active  missions    
    def executeGetActiveMissionListRESTRequest(self, nbrOfMissions):
        jsonMissions = { "retcode": -1 }
        try:
            requestLink = self._restMissionRequestPath + self._sessionTokenPath + self._sessionToken
            requestLink += "&datarange=%5B0%2C" + str(nbrOfMissions) + "%5D"
            requestLink += "&dataorderby=%5B%5B%22createdat%22%2C%22desc%22%5D%5D"
            requestLink += "&dataselection=%7B%22criteria%22%3A%5B%22navigationstate%3A%3Aint IN%3A 3%7C0%7C1%22%5D%2C%22composition%22%3A%22AND%22%7D"
            missions = self.executeRESTRequest( requestLink, "GET")
            jsonMissions = json.loads(missions)
            missionList = jsonMissions["payload"]["missions"]
        except:
            print( "executeGetActiveMissionListRESTRequest: retcode = %d" % jsonMissions["retcode"] )
            missionList = []
        return missionList


    # -----------------------------------
    # Cancel a specific mission
    def executeCancelMissionRESTRequest(self, missionID):
        if self._debug:
            print("Canceling mission : " + str(missionID))
        self.executeRESTRequest(self._restMissionRequestPath + "/" + str(missionID) + self._sessionTokenPath + self._sessionToken, "DELETE")

    # -----------------------------------
    # Cancel a specific mission
    def executeCancelAllMissionRESTRequest(self):
        if self._debug:
            print("Canceling all planned missions : ")
        self.executeRESTRequest(self._restMissionRequestPath + self._sessionTokenPath + self._sessionToken, "DELETE")


    # -----------------------------------
    # Get infos about all vehicles
    def getVehiclesInfo(self):
        ''' Execute REST request to get the informations on all vehicles '''
        vehicleResp = self.executeRESTRequest(self._restVehicleRequestPath + self._sessionTokenPath +self._sessionToken, "GET")
        jsonVehicles = json.loads(vehicleResp)
        #vehicles = jsonVehicles["payload"]["vehicles"]
        #return vehicles
        return jsonVehicles

    # -----------------------------------
    # Get info about all alarms
    def getAlarms(self, addition):
        ''' Execute REST request to get all alarms '''
        alarmResp = self.executeRESTRequest(self._restAlarmsRequestPath + self._sessionTokenPath + self._sessionToken + addition, "GET")
        jsonAlarms = json.loads(alarmResp)
        #print(str(jsonAlarms))
        alarms = jsonAlarms["payload"]["alarms"]
        return alarms

    # -----------------------------------
    # Get info about all missions
    def getMissions(self, nrOfMissions):
        ''' Execute REST request to get all missions '''

        request = self._restMissionRequestPath + self._sessionTokenPath + self._sessionToken
        request += "&datarange=%5B0%2C" + str(nrOfMissions) + "%5D"
        request += "&dataorderby=%5B%5B%22createdat%22%2C%22desc%22%5D%5D"
        missionResp = self.executeRESTRequest( request, "GET")
        jsonMissions = json.loads(missionResp)

        if len(jsonMissions["payload"]["missions"]):
            return jsonMissions["payload"]["missions"]
        else:
            return None

    # -----------------------------------
    # Get info about all active missions
    def getActiveMissions(self, nrOfMissions):
        ''' Execute REST request to get all active missions '''
        missionResp = self.executeGetActiveMissionListRESTRequest(nrOfMissions)
        return missionResp


        # -----------------------------------
        # Get info about all missions

    def getMission(self, id):
        ''' Execute REST request to get all missions '''

        request = self._restMissionRequestPath + "/"+ id + self._sessionTokenPath + self._sessionToken
        missionResp = self.executeRESTRequest(request, "GET")
        jsonMissions = json.loads(missionResp)
        missions = jsonMissions["payload"]["missions"]
        if len(jsonMissions["payload"]["missions"]):
            return jsonMissions["payload"]["missions"][0]
        else:
            return None

    # Get infos about Application
    def getApplicationInfo(self):
        appResp = self.executeRESTRequest(self._restApplicationRequestPath + self._sessionTokenPath +self._sessionToken, "GET")
        jsonApplication = json.loads(appResp)
        return jsonApplication["payload"]["application"]


    # -----------------------------------
    # Get infos the server
    def getServerInfo(self):
        serverResp = self.executeRESTRequest(self._restServerRequestPath + self._sessionTokenPath +self._sessionToken, "GET")
        jsonServer = json.loads(serverResp)
        return jsonServer["payload"]

    # Get info about all stations
    def getStations(self):
        ''' Execute REST request to get all stations '''
        request = self._restStationRequestPath + self._sessionTokenPath + self._sessionToken
        stationResp = self.executeRESTRequest( request, "GET")
        jsonStations = json.loads(stationResp)

        stations = jsonStations["payload"]["groups"]
        return stations

    # -----------------------------------
    # Get info about the map
    def getMap(self):
        ''' Execute REST request to get map data '''

        #! The RequestToken is set static to floor 0 !#
        request = self._restMapRequestPath + self._sessionTokenPath + self._sessionToken
        mapResp = self.executeRESTRequest( request, "GET")
        jsonMap = json.loads(mapResp)

        mapData = jsonMap["payload"]["data"][0]
        return mapData

    # -----------------------------------
    # Get infos about all alarms
    def deleteAlarm(self, addition):
        ''' Execute REST request to get all alarms '''
        alarmResp = self.executeRESTRequest(self._restAlarmsRequestPath + "/" + addition + self._sessionTokenPath + self._sessionToken, "DELETE")
        jsonAlarms = json.loads(alarmResp)
        alarms = jsonAlarms["payload"]
        return alarms



    # -----------------------------------
    # Fill in the data about a mission before making a mission request
    def createMissionData(self, missionType, source, dest, numberOfMissions, payload, prio="Medium", isLinkable=None, linkedMission=None, linkWaitTimeout=60, sourceNodeType=None, destNodeType=None):
        
        missionrequest = {}
        missionData = {}
        missionData["requestor"]  = self._requestor
        missionData["missiontype"]  = self._missionType[missionType.lower()]
        missionData["fromnode"]  = source
        missionData["tonode"]  = dest
        missionData["cardinality"]  = numberOfMissions
        try: 
            missionData["priority"]  = self._priority[prio.lower()]
        except:
            print("priority %s not defined; use 'medium' priority", prio)
            prio = "Medium"
            missionData["priority"]  = self._priority[prio.lower()]
        missionData["deadline"]  = self._currentTime
        missionData["dispatchtime"]  = self._currentTime

        missionParams = {}
        missionParamsValue = {}
        missionParamsValue["payload"] = payload
        missionParamsValue["priority"] = prio

        if sourceNodeType is not None and destNodeType is not None:
            missionParamsValue["dynamicnodetypes"] = {"fromnodetype":eval(sourceNodeType), "tonodetype":eval(destNodeType)}
        elif sourceNodeType is not None:
            missionParamsValue["dynamicnodetypes"] = {"fromnodetype":eval(sourceNodeType)}
        elif destNodeType is not None:
            missionParamsValue["dynamicnodetypes"] = {"tonodetype":eval(destNodeType)}
        else:
            if self._debug:
                print("No dynamic nodetypes specified")

        if isLinkable is not None:
            missionParamsValue["isLinkable"] = isLinkable
            missionParamsValue["linkWaitTimeout"] = linkWaitTimeout
        if linkedMission is not None:
            missionParamsValue["linkedMission"] = linkedMission

        missionParams["value"] =  missionParamsValue
        missionParams["desc"]  = "Mission extension"
        missionParams["type"]  = "org.json.JSONObject"
        missionParams["name"]  = "parameters"

        missionData["parameters"]  = missionParams

        missionrequest["missionrequest"] = missionData
        requestData = json.JSONEncoder().encode(missionrequest)
        if self._debug:
            print("REQ: ", requestData)
        return requestData

    # -----------------------------------
    # Change the pause mode of ant server
    def executePauseANTServerRESTRequest(self, pausestate ):
        ''' Execute REST request to change the pause state of the server'''
        if self._debug:
            print( "pauseANTServer: %s" % pausestate )
        Data = {}
        Command = {}                  
        Command["name"]  = "pauseANTServer"
        Args = {}
        if pausestate:
            Args["pause"] = "true"
        else:
            Args["pause"] = "false"
        Command["args"] = Args
        Data["commands"] = [ Command ]
    
        if self._debug:
            print ( str( Data ) )
       
        requestLink = self._restApplicationNavigationSettingsRequestPath + "/command" + self._sessionTokenPath + self._sessionToken
        requestData = json.JSONEncoder().encode( Data )
        serverResp = self.executeRESTRequest( requestLink, "POST", requestData.encode( 'utf-8' ) )
        jsonServer = json.loads( serverResp )
        return jsonServer["payload"]
