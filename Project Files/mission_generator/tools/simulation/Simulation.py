#!/usr/bin/python3

# import sys
import sys
from os import path

current = path.dirname(path.realpath(__file__))
parent = path.dirname(current)
sys.path.append(parent)

sys.path.append("../libraries/ANTServerAPI/")
sys.path.append("../libraries/common/")

import ANTServerRESTClient
import datetime
import time
import json
import re
import argparse
import logging
import common
import random
import Timer
import Missions
from MqttClient import MqttClient
from common import getValueFromListInRandomOrder
from common import getValueFromDict

def CreateANTMission(mission):
    
    # for now only support random sequence...
    fr = getValueFromListInRandomOrder(mission["from"])
    to = getValueFromListInRandomOrder(mission["to"])
    ty = getValueFromDict(mission, "type", "transport from station to station")
    descr = getValueFromDict(mission, "description", f"Transport from {fr} to {to}")
    payload = getValueFromDict(mission, 'payload', "Default Payload")
    prio = getValueFromDict(mission, 'priority', "Medium")
    snt = getValueFromDict(mission, 'sourceNodeType')
    dnt = getValueFromDict(mission, 'destNodeType')

    log.info(f"Create ANT '{ty}' mission from {fr} to {to}")
    Missions.createMission(ty, descr, fr, to, payload, prio, sourceNodeType=snt, destNodeType=dnt )

AutoId = 1

def CreateMQTTMission(mission, mqtt):
    
    global AutoId
    # for now only support random sequence...
    fr = getValueFromListInRandomOrder(mission["from"])
    to = getValueFromListInRandomOrder(mission["to"])
    ty = getValueFromDict(mission, "type", "transport from station to station")
    descr = getValueFromDict(mission, "description", f"Transport from {fr} to {to}")
    payload = getValueFromDict(mission, 'payload', "Default Payload")
    prio = getValueFromDict(mission, 'priority', "Medium")
    snt = getValueFromDict(mission, 'sourceNodeType')
    dnt = getValueFromDict(mission, 'destNodeType')
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    AutoId += 1


    log.info(f"Create MQTT mission '{ty}' mission from {fr} to {to}")

    encoding = getValueFromDict(mqtt, 'encoding', 'json')
    form = getValueFromDict(mqtt, 'form', mission)
    topic = getValueFromDict(mqtt, 'topic', "DP Request/{auto_id}")

    # fill variables in form
    d = {}
    for key in form:
        d[key] = form[key].format(fr=fr, to=to, ty=ty, descr=descr, payload=payload, prio=prio, sourceNodeType=snt, destNodeType=dnt, time=time, auto_id=AutoId)
    # now encode 
    if encoding == "json":
        msg = json.dumps(d)
    else:
        log.fatal(f"MQTT encoding action {encoding} not supported")
        sys.exit(-2)

    log.info(f"Public MQTT msg '{msg}' on topic {topic}")
    mqttClient.publish( topic.format(auto_id=AutoId), msg )

def executeAction(action, data):
    """ Execute the specified action
        parameters:
            action : str indicatation of the action
            data : dictionairy with the necesarry data
    """
    
    if action == "Create ANT Mission":
        log.info(f"Genenate ANT  mission:  {data['mission']}")
        CreateANTMission(data['mission'])
    elif action == "Create MQTT Mission":
        log.info(f"Genenate MQTT  mission:  {data['mission']}")
        CreateMQTTMission(data['mission'], data['mqtt'])
    else:
        log.fatal(f"Action '{action}' not supported")
        sys.exit(-2)

# just for testing.
def display(data):
    print("Display: %s" % (data))

#start
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of ANT-Server', default='localhost') 
parser.add_argument('--verbose', help="Show missions verbose", action='store_true')
parser.add_argument('--info', help="Show info", action='store_true')
parser.add_argument('--debug', help="Show debug", action='store_true')
parser.add_argument('--no_init', help="No backlog or initialize vehicles", action='store_true')
parser.add_argument('--config', help='Simulation specified in json file', default='HSim.json') 
#parser.add_argument('--config', help='Simulation specified in json file', default='SimulationTest.json') 
args = parser.parse_args()

log = logging.getLogger( "Simulation" )
common.setLogLevel( args.debug, args.info )
Configuration = common.readConfigFile(args.config)

log.info(" -------------------------------------- ")
log.info(" ----       Run simulation         ---- ")
log.info(" -------------------------------------- ")

conf = {}
# open connection to ANT
conf = getValueFromDict(Configuration, 'ANT Server')
if conf is not None:
    host = getValueFromDict(conf, "host", args.host) 
    port = getValueFromDict(conf, "port", 8081) 
    user = getValueFromDict(conf, "user", "admin") 
    password = getValueFromDict(conf, "password", "123456") 

    log.info(f"Open connection to ANT: {host}:{port} as {user}:{password}")
    restClient = ANTServerRESTClient.ANTServerRestClient(ipAddress=host, portNumber=port, username=user, password=password, debug=args.debug )
else:
    log.info(f"Open connection to ANT: {args.host}")
    restClient = ANTServerRESTClient.ANTServerRestClient(ipAddress=args.host, debug=args.debug )
Missions.setRestClient(restClient)

# open connection to MQTT broker if configured
conf = getValueFromDict(Configuration, 'MQTT Client')
if conf is not None:
    host = getValueFromDict(conf, "host", args.host) 
    port = getValueFromDict(conf, "port", 1881) 
    user = getValueFromDict(conf, "user", "") 
    password = getValueFromDict(conf, "password", "") 

    log.info(f"Open connection to MQTT: {host}:{port} as {user}:{password}")
    mqttClient = MqttClient(host, int(port), user, password)
    while not mqttClient.isConnected():
        log.info("Waiting for connection to MQTT broker...")
        mqttClient.loop()
        time.sleep(1)

# handle global settings.
simulation_speed = 1.0
conf = getValueFromDict(Configuration, 'Global settings')
if conf is not None:
    seed = getValueFromDict(conf, "seed")
    if seed is not None:
        random.seed(seed)
    simulation_speed = getValueFromDict(conf, "simulation_speed", 1.0)

if args.no_init == False:
    # start with mission assignment disabled
    Missions.PauseMissionAssignment(True)
    #insert backlog missions 
    if 'Backlog'in Configuration.keys():
        # first clear all missions in the system
        log.info(f"backlog defined clear all existing missions")
        Missions.cancelAllMissions()
        for backlog in Configuration["Backlog"]:
            for count in range(1,backlog['quantity']+1):
                executeAction(backlog["action"], backlog)

    # initialize vehicles at initial positions
    if 'Initial positions'in Configuration.keys():
        for vehicle in Configuration["Initial positions"]:
            log.info( f"Extract vehicle {vehicle['id']}" )
            restClient.getSessionToken()
            restClient.executeExtractVehicleRESTRequest( vehicle['id'] )

        for vehicle in Configuration["Initial positions"]:
            if vehicle['location'] != 'extracted':
                log.info( f"Insert vehicle {vehicle['id']} at {vehicle['location']}" )
                restClient.getSessionToken()
                restClient.executeInsertVehicleRESTRequest( vehicle['id'], vehicle['location'] )
    Missions.PauseMissionAssignment(False)



# now generate triggers:
if 'Triggers'in Configuration.keys():
    for trigger in Configuration["Triggers"]:
        interval = (3600.0 / trigger["flow per hour"]) / simulation_speed
        start = interval - (interval * random.random())
        log.info(f"Execute {trigger['action']} with {int(interval)} seconds interval start at {int(start)}")
        Timer.CreateIntervalTimer(start, interval, executeAction, [trigger["action"], trigger])

while True:
    try: 
        time.sleep(1)
    except:
        print("Bye bye...")
        Timer.CancelAllTimers()
        sys.exit(-1)
        
