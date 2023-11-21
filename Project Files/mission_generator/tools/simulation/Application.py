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

class Application():
    def __init__(self, applicationData):
        self._name = applicationData["name"]
        self._version = applicationData["version"]
        self._config = applicationData["configuration"]
        self._ANTServerVersion = applicationData["ASversion"]
        self._ANTLabVersion = applicationData["ALversion"]
        self._applicationName = applicationData["application"]["name"]
        self._applicationVersion = applicationData["application"]["version"]

    def show(self):
        print(f"name = {self._name}")
        print(f"version = {self._version}")
        print(f"config = {self._config}")
        print(f"ANT server version = {self._ANTServerVersion}")
        print(f"ANT Lab version = {self._ANTLabVersion}")
        print(f"Application name = {self._applicationName}")
        print(f"Application version = {self._applicationVersion}")
        


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

    log = common.initLogger( "Application", args.debug, args.info )

    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host )
    restClient.getSessionToken()
    app = Application(restClient.getApplicationInfo())
    app.show()


