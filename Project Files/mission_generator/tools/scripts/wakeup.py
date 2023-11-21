#!/usr/bin/python3

import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Wakeup address', default='172.19.22.177') 
parser.add_argument('--port', help='Wakeup port', type=int, default=9000) 
args = parser.parse_args()


print(f"Wakeup {args.host} on port {args.port}")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((args.host, args.port))
s.sendall(b'ON')
s.close()
