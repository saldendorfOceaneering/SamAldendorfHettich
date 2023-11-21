#!/bin/sh

python3 CreateNodeToNodeMission.py -h 192.168.178.241 PandD_1 PalletTracking  PandD_3 Dropoff
python3 CreateNodeToNodeMission.py -h 192.168.178.241 PandD_2 PalletTracking  PandD_4 Dropoff 
python3 CreateNodeToNodeMission.py -h 192.168.178.241 PandD_3 PalletTracking  PandD_2 Dropoff 
python3 CreateNodeToNodeMission.py -h 192.168.178.241 PandD_4 PalletTracking  PandD_1 Dropoff 
