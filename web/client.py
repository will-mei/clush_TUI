#!/usr/bin/env python
# coding=utf-8
import socket

#import sys 
#import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.59.252', 9999))
print(s.recv(1024).decode('utf-8'))

for data in [b'Alex', b'Bob', b'Charlie']:
    s.send(data)
    print(s.recv(1024).decode('utf-8'))

    #data = {'sum':'testsumxxxxxxx', 'msg':' '.join(sys.argv[1:])}
    #msg = json.dumps(data).encode('utf-8')

s.send(b'exit')
s.close()
exit(0)
