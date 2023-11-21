#!/usr/bin/python3
# script to start a simple OPC UA server for testing purpose.

import argparse
import json
from opcua import Server
from opcua.server.user_manager import UserManager

parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Host address of OPCUA-Server', default='0.0.0.0') 
parser.add_argument('--port', help='Port of OPCUA-Server', default='10001') 
parser.add_argument('--namespace', help='Namespace on OPCUA-Server', default='12') 
parser.add_argument('--verbose', help="Show verbose info", action='store_true')
parser.add_argument('--username', help="Username", default='')
parser.add_argument('--password', help="Password", default='')
parser.add_argument('--cert', help="Certificate", default='cert.pem')
parser.add_argument('--key', help="Private key", default='key.pem')
parser.add_argument('--config', help='Config file', default='OpcUaConfig.json')
args = parser.parse_args()

def user_manager(isession, username, password):
    isession.user = UserManager.User
    return username == args.user and password == args.password

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

Configuration = readConfigFile(args.config)

server = Server()
endpoint = "opc.tcp://%s:%s" % (args.host, args.port)

server.set_endpoint(endpoint)
namespace_id = server.register_namespace(args.namespace)
namespace_id = int(args.namespace)
objects = server.get_objects_node()

if len(args.username):
    if args.verbose: print("Set security certificate=%s, key=%s: " % (args.cert, args.key) )
    if args.verbose: print("Set security: username=%s, password=%s" % (args.username, args.password) )
    server.load_certificate(args.cert)
    server.load_private_key(args.key)
    server.set_security_policy([
                                    # ua.SecurityPolicyType.NoSecurity,
                                    ua.SecurityPolicyType.Basic128Rsa15_Sign,
                                    ua.SecurityPolicyType.Basic128Rsa15_SignAndEncrypt,
                                    # ua.SecurityPolicyType.Basic256Sha256_Sign,
                                    #ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt
                                ])
    policyIDs = ["Username"]
    server.set_security_IDs(policyIDs)
    server.user_manager.set_user_manager(user_manager)


OpcUaVariables = {}
for var in Configuration["OpcUaVariables"]:
    name = var["name"]
    OpcUaVariables[name] = objects.add_variable('ns=%s;s=%s' % (namespace_id, name), name, 0 )
    if var["writable"]:
        if args.verbose: print("Publishing writable variable: %s." % name)
        OpcUaVariables[name].set_writable()
    else:
        if args.verbose: print("Publishing readonly variable: %s." % name)
    OpcUaVariables[name].add_data_type("'ns=%s;s=%s'" % (namespace_id, name), var["type"])

print(f"Starting OPC UA server on: {endpoint} namespace: {args.namespace}[{namespace_id}]")
server.start()
