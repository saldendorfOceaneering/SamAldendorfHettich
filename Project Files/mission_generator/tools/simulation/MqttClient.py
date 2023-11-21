#!/usr/bin/python3
# script to start a simple OPC UA server for testing purpose.

import argparse
import random
import json
import logging
import time
from paho.mqtt import client as mqtt_client


class MqttClient():
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info("Connected to MQTT Broker!")
            self.connected = True
        else:
            self.log.info("Failed to connect, return code %d\n", rc)
            self.connected = False

    def on_message(self, client, userdata, msg):
        self.log.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        for (topic, handler) in self.subscriptions:
            self.log.debug(f"Compare subscription:`{topic}` with `{msg.topic}`")
            if mqtt_client.topic_matches_sub(topic, msg.topic):
                handler(msg.topic, msg.payload.decode())


    def __init__(self, host, port, username, password):
        # Set Connecting Client ID
        self.log = logging.getLogger("MqttClient")
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.client = mqtt_client.Client(client_id)
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.log.debug(f"Connect `{host}`:`{port}`")
        self.client.connect(host, port)
        self.connected = False
        self.client.on_message = self.on_message
        self.subscriptions = []

    def subscribe(self, topic : str, handler):
        self.client.subscribe(topic)
        self.subscriptions.append((topic, handler)) 

    def publish(self, topic : str, data : str): 
        self.log.info(f"publish `{data}` on `{topic}`")
        result = self.client.publish(topic, data)
        return result

    def isConnected(self):
        return self.connected

    def loop(self):
        return self.client.loop()


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    def handler(topic: str, msg : str):
        print(f"Handler: Received `{msg}` on topic '{topic}'")
        
        
    import sys
    sys.path.append("../libraries/common/")
    import common

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Host address of mqqt broker', default='localhost') 
    parser.add_argument('--port', help='Port of OPCUA-Server', default='1883') 
    parser.add_argument('--info', help="Show verbose info", action='store_true')
    parser.add_argument('--debug', help="Show verbose info", action='store_true')
    parser.add_argument('--username', help="Username", default='')
    parser.add_argument('--password', help="Password", default='')
    parser.add_argument('--config', help='Config file', default='MqttClient.json')
    args = parser.parse_args()

    mqttConfig = common.readConfigFile(args.config)["MQTT Client"]
    mqttClient = MqttClient(mqttConfig["host"], int(mqttConfig["port"]), mqttConfig["user"], mqttConfig["password"])
    common.setLogLevel(args.debug, args.info) 
    
    while not mqttClient.isConnected():
        print("Waiting for connection to MQTT broker...")
        mqttClient.client.loop()
        time.sleep(1)

    print("Now publish something MQTT broker...")

    result = mqttClient.publish("bogus_topic/test", "This is a test")

    mqttClient.subscribe( "bogus_topic/test/#", handler)
    mqttClient.subscribe( "bogus_topic/#", handler)
    mqttClient.client.loop_forever()
