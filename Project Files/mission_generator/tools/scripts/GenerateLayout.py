#!/usr/bin/python3

import sys
sys.path.append("../libraries/ANTServerAPI/")
import ANTServerRESTClient

import argparse

import json

import xml.etree.cElementTree as ET
from xml.dom import minidom

from datetime import date

parser = argparse.ArgumentParser()
parser.add_argument('--host', nargs='+', default="localhost", help='Host address of ANT-Server')
parser.add_argument('--filename', nargs='+', default="layout.export", help='Name of Export-file')
args = parser.parse_args()

identifier = 0
def getId():
    global identifier
    identifier += 1
    return identifier

# -----------------------------------------------------------------------------
def main ():
    print(" -------------------------------------- ")
    print(" ---- Generate Export-File ---- ")
    print(" -------------------------------------- ")

    # --- Retrieve Layout Elements ---
    restClient = ANTServerRESTClient.ANTServerRestClient( ipAddress = args.host[0] )

    restClient.getSessionToken()
    layout = restClient.getMap()

    #TODO Parse through all station in the strucutre layer
    stations = restClient.getStations()

    #print(json.dumps(layout, indent=4, sort_keys=True))

    # --- Create Xml Object Root ---
    namespace="https://www.oceaneering.com"
    ET.register_namespace('Frog',namespace)

    root = ET.Element("{" + namespace + "}" + "FrogLayout")
    root.set("version", "2.0")

    # --- Add layout parameters ---
    projectname = ET.SubElement(root, 'name')
    projectname.text = layout["data"]["alias"]

    layoutversion = ET.SubElement(root, 'dataVersion')
    layoutversion.text = str(layout["data"]["id"])

    activationdate = ET.SubElement(root, 'activationDate')
    activationdate.text = str(date.today())

    # --- Construct Layout ---
    section = ET.SubElement(root, 'section')

    # --- Add Layer: Structure Layer for Stations ---
    lStructure = ET.SubElement(section, 'structureLayer')
    lStructure.set("name","1")

    for station in [1]:
        equipment = ET.SubElement( lStructure, 'equipment' )
        equipment.set("name","abc")
        equipment.set("function","CHARGER")

        position = ET.SubElement( equipment, 'position' )
        position.set("id", str(getId()) )
        position.set("x", "0.0" )
        position.set("y", "0.0" )
        position.set("z", "0.0" )

        volume = ET.SubElement( equipment, 'volume' )
        volume.set("width", "1.0" )
        volume.set("length", "1.0" )

        orientation = ET.SubElement( equipment, 'orientation' )
        orientation.set("angle","0.0")

        pinpoint = ET.SubElement( equipment, 'pinpoint' )
        formula = ET.SubElement( pinpoint, 'formula' )
        formula.set("name","x")
        formula.set("factor","0.0")
        formula.set("offset","0.0")

        formula = ET.SubElement( pinpoint, 'formula' )
        formula.set("name","y")
        formula.set("factor","0.0")
        formula.set("offset","0.0")

        outline = ET.SubElement( equipment, 'outlinePolygons' )
        polygon = ET.SubElement( outline, 'polygon' )
        point = ET.SubElement( polygon, 'point' )
        point.set("x","0.0")
        point.set("y","0.0")

        point = ET.SubElement( polygon, 'point' )
        point.set("x","0.0")
        point.set("y","0.0")

    # --- Add Layer: Route Layer for nodes and paths ---
    lRoute = ET.SubElement(section, 'routeLayer')
    lRoute.set("name","1")

    # Retrieve all possible nodes
    nodes = {}
    lines = layout["data"]["layers"][1]["lines"]
    for line in lines:
        x1,y1,x2,y2 = line["coord"]

        h =  hash( str(x1)+str(y1) )

        x1 =  str(x1).replace(',', '.')
        y1 =  str(y1).replace(',', '.')
        nodes[h] = [x1,y1]

        h =  hash( str(x2)+str(y2) )

        x2 =  str(x2).replace(',', '.')
        y2 =  str(y2).replace(',', '.')
        nodes[h] = [x2,y2]

    # Add paths
    lines = layout["data"]["layers"][1]["lines"]
    for line in lines:
        x1,y1,x2,y2 = line["coord"]

        path = ET.SubElement( lRoute, 'path' )
        path.set("id","0")
        path.set("uniDirectional","false")

        # Configure begin point of line
        x,y = nodes[ hash( str(x1)+str(y1) )]
        bcp = ET.SubElement( path, 'beginConnectionPoint' )
        cp = ET.SubElement( bcp, 'connectionPoint' )
        p = ET.SubElement( cp, 'position' )

        p.set("x",x)
        p.set("y",y)
        p.set("z","0.0")

        # Configure end point of line
        x,y = nodes[ hash( str(x2)+str(y2) )]

        ecp = ET.SubElement( path, 'endConnectionPoint' )
        cp = ET.SubElement( ecp, 'connectionPoint' )
        p = ET.SubElement( cp, 'position' )

        p.set("x",x)
        p.set("y",y)
        p.set("z","0.0")

    # --- Write File ----
    xmlstr = minidom.parseString( ET.tostring(root) ).toprettyxml( indent="   " )
    with open( args.filename, "w" ) as f:
        f.write( xmlstr )

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()



