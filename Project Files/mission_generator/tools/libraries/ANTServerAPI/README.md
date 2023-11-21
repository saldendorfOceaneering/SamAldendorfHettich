### Preparation
- Launch ANT server simulation
- In ANT lab, open a project
- in ANT lab, go to "ANT server -> Apply config"
- Close ant reopen the "ANT Vehicle simulator" window

Running examples (need python 3.x)
- Open a command line and type:
    - cd <Project Root>/scripts/ANTServerAPI/Examples
    - python <Script> <Arguments>

#### Running Scripts
Running examples (need python 3))
- Open a command line and type:
    - cd <Project Root>/scripts/InsightAPI/examples
    - python <script-name> <arguments>

### Scripts

#### CancelAllMissions.py
_This script cancels all active missions in ANT-Server_
```
$ python CancelAllMissions.py
```

#### CreateNodeToNodeMission.py [Source] [Destination][payload]
_This script creates a transport between Nodes_
- source: Label of pickup location
- destination: Label of dropoff location
- payload: Label of payload
```
$ python CreateNodeToNodeMission.py S101 S102 Pallet
```

#### ExtractAllVehicle.py
_This script extracts all vehicles from the Layout_
```
$ python ExtractAllVehicle.py
```

#### GetFleetBatteryLevel.py [period] [samples]
_This script provides the battery state of all vehicles in the fleet_
- period: Refresh rate of the data
- maxSamples = Amount of samples
```
$ python GetFleetBatteryLevel.py 1 100
```
#### GetVehcilePosition.py
_This script provides the current position of all vehicles_
```
$ python GetVehcilePosition.py
```
Ensure all vehicles are inserted in the layout

#### InsertVehicle.py [vehicleName] [nodeName]
_This script inserts a vehicle in the layout_

Two arguments are required:
- VehicleName: The name of the vehicle as defined in the project
- NodeName: The label of the node as defined in the project
```
$ python InsertVehicle.py CM-FOL-1 S101
```

#### GetStations.py
_This script provides the station information of all stations in the fleet_
```
$ python GetVehcilePosition.py
```
Ensure all vehicles are inserted in the layout