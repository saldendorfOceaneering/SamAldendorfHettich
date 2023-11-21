#!/usr/bin/python3

import logging
import json
import sys
import random


def initLogger(name, debug, info):
    """ get logger and 
        set logging level based on debug and info settings.
    """
    log = logging.getLogger(name)
    if (debug): level = logging.DEBUG
    elif info: level = logging.INFO
    else: level = logging.WARNING
    logging.basicConfig(level=level)
    return log

def setLogLevel(debug : bool , info : bool ):
    """ set logging level based on debug and info settings.
    """
    if (debug): level = logging.DEBUG
    elif info: level = logging.INFO
    else: level = logging.WARNING
    logging.basicConfig(level=level)


def readConfigFile(filename : str): 
    """ open and read a json formatted file 
        and return it as a dict
    """
    try:
        with open(filename) as json_file:
           config = json.load(json_file)
    except Exception as e: 
        print("Could not read config file: %s exception: %s" % ( filename, str(e) ) )
        sys.exit(-1)
    return config

def getValueFromDict( d : dict, key, default = None):
    """ get value identified by key from a dict
        if key does not exist in dict return default value.
    """
    if key in d.keys():
        return d[key]
    else:
        return default

ListSequences = {}
def getValueFromListInRandomOrder(l):
    key = str(l) 
    if key not in ListSequences.keys():
        random.shuffle(l)
        key = str(l)
        ListSequences[key] = (l, 0)
    (l,seq) = ListSequences[key]

    seq += 1
    if seq >= len(l): 
        seq = 0
    ListSequences[key] = (l,seq)
    return l[seq]

