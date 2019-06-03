#!/usr/bin/env python
# coding=utf-8

import cluster_terminal


def test_main():
    # local settings
    # all commands will be hashed with it 
    # there will be a hash str send to terminal alone with the cmd 
    _id = 'hash_keyword'
    # init info for a terminal server 
    t = {
        'server_id':_id,
        'server_ip':'127.0.0.1',
        'server_port':60000,
        'workers':3,
        'con_max':128,
    }
    # init info for a connection group 
    # if you have an ip without knowing its fqdn, use the ip as fqdn
    g = {
        'grp_name':'grp0',
        #'grp_concurrency':20,
        # process :less than 20; cores *10
        # thread : 200+
        'grp_ssh_info':{
            'port':22,
            'user':None,
            'password':None,
            'timeout':15,
            'hostkey':'~/.ssh/id_rsa'
        },
        #'grp_ip_array':{
        #    'host1':'192.168.59.11',
        #    'host2':'192.168.59.12',
        #    'host3':'192.168.59.13',
        #},
        'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 130)}
        #'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 30)}
    }

    server1 = cluster_terminal.cluster_ssh_terminal(t)
    server1.add_grp(g)
    #print(server1['grp0']) 

#test_main

import socket

def front_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(
        ('172.0.0.1', 60000)
    )
    s.send(b'any info test')

