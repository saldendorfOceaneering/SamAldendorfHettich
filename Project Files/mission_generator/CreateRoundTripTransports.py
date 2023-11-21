import pandas
import datetime
import json
from sys import path
import os


#Read the worksheet in the Excel workbook
excelfilename = "Hettich_Simulation_Test_1.xlsx"            # excel file name (input to read)
jsonfilename = "Hettich_Simulation_Test_1.json"             # json file name (output to write)

while not os.path.isfile(excelfilename):
    excelfilename = input("Whoops! No such file! Please enter the name of the file you'd like to use.")

mission_sheetname = "Lower"
transport_data = pandas.read_excel(excelfilename,sheet_name=mission_sheetname)

vehicles_sheetname = "Vehicles"
vehicle_position_data = pandas.read_excel(excelfilename,sheet_name=vehicles_sheetname)


#Convert the data to be a list of dict
transports = transport_data.to_dict('records')
print(transports)

vehicle_positions = vehicle_position_data.to_dict('records')

#Create missions for Triggers dict
Triggers = []
what = "Create Mission"
action = "Create ANT Mission"
client = "SpringHill ANT"
missionType = "transport from station to station"
atStartup = 1
#Create mission dict
for d in transports:
    startHour = d["Period Start Hour"]
    endHour = startHour + 1
    periodStart = "%02d:00:00" % startHour
    periodEnd = "%02d:00:00" % endHour
    period = []
    period.append(periodStart)
    period.append(periodEnd)

    # ======== From --> To ======== #
    descriptionEmpty = "%s to %s" % (d["From"], d["To"])
    fromEmpty = [d["From"]]
    fromTo = [d["To"]]
    missionEmpty = {"description": descriptionEmpty,
               "type": missionType,
               "from": fromEmpty,
               "to": fromTo,
               "payload": d["Payload"],
               "priority": d["Priority"]}
    actionEmpty = {"what": what,
              "client": client,
              "mission": missionEmpty}
    triggerEmpty = {"period": period,
               "flow per hour": d["Flow Per Hour"],
    #TESS           "at startup": atStartup,
    #TESS           "action": actionEmpty}
               "action": action,
               "mission": missionEmpty}
    Triggers.append(triggerEmpty)

    # ======== To --> From ======== #
    descriptionFull = "%s to %s" % (d["To"], d["From"])
    fromFull = [d["To"]]
    toFull = [d["From"]]
    missionFull = {"description": descriptionFull,
               "type": missionType,
               "from": fromFull,
               "to": toFull,
               "payload": d["Payload"],
               "priority": d["Priority"]}
    actionFull = {"what": what,
              "client": client,
              "mission": missionFull}
    triggerFull = {"period": period,
               "flow per hour": d["Flow Per Hour"],
    #TESS           "at startup": atStartup,
    #TESS           "action": actionFull}
               "action": action,
               "mission": missionFull}
    # Triggers.append(triggerFull)                                  # do not consider To ==> From

#Global Settings dict
globalSettings = {"seed": 1,
                  "simulation_speed": 2.0}

#Clients dict
clientID = "SpringHill ANT"
clientType = "ANT"
clientCredentials = {"host": "localhost",
                     "port": 8081,
                     "user": "admin",
                     "password": "123456",
                     "interval": 500}
clients = {"id": clientID,
           "type": clientType,
           "credentials": clientCredentials}

#Combine to make simulation config file
simConfigFile = {"Global settings": globalSettings,
#TESS                 "Clients": clients,
                 "Initial positions": vehicle_positions,
                 "Triggers": Triggers}

#Serialize json
json_object = json.dumps(simConfigFile, indent=4)

#Write to json file
with open(jsonfilename, "w") as outfile:
    outfile.write(json_object)