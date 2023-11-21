#!/usr/bin/python

import sys
import argparse
import xmltodict
import math

def cart2pol(x, y):
    rho = math.sqrt(x**2 + y**2)
    phi = math.arctan2(y, x)
    return(rho, phi)

def pol2cart(rho, phi):
    x = rho * math.cos(phi)
    y = rho * math.sin(phi)
    return(x, y)

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='+', type=str, help="Flexisoft safety scanner export file", default='[SafetyFields.xml]')
parser.add_argument('--polar_offset', help="Offset of polar coordinates", default='45.0')
parser.add_argument('--nvalues', help="Number of values for case", type=int, default='8')
args = parser.parse_args()

for filename in args.filename:
    xml_file=open(filename, 'r')
    xml_src=xml_file.read()

    d=xmltodict.parse(xml_src)

    for area in d['AreaList']['Area']:
        #area["@Index"], area["@Name"], area["@CoordinatesType"]
        for field in area['FieldList']['Field']:
            n = 0
            # "Type:", field["@Type"])
            if field.has_key("UserPointList"): 
                if field["@Type"][:6] == 'ftWarn':
                    sys.stdout.write("%s %s_%s" %( field["@Type"][2:], str(area["@Name"]), filename.rsplit(".", 1)[0]))
                else:
                    sys.stdout.write("%s_%s" %( str(area["@Name"]), filename.rsplit(".", 1)[0] ))
                for userPoint in field["UserPointList"]["UserPoint"]:
                    if area["@CoordinatesType"] == "polar":
                        # angle is given in degree
                        angle = math.radians(float(userPoint["@Angle"]) - float(args.polar_offset)) 
                        # distance is given in cm
                        distance = float(userPoint["@Distance"]) / 100.0
                        x,y =  pol2cart(distance, angle)
                    else:
                        print ("Coordinate type %s is not supported", area["@CoordinatesType"])
                        sys.exit(-1)

                    #print("Polar: (%s, %s) (offset=%s) -> %.0f %.0f" % 
                    #    (userPoint["@Angle"], userPoint["@Distance"], args.polar_offset, x*1000,y*1000))
                    sys.stdout.write(",%.0f,%.0f" % (x*1000,y*1000))
                    n = n + 1
                for i in range (0, args.nvalues - n):
                    sys.stdout.write(",0,0")
                sys.stdout.write("\n")


