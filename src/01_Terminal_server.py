#!/usr/bin/env python
# coding=utf-8

import lib_terminal


def test_server():

    # one server 
    server_info = {
        'server_id'     :b'test_user_id',
        'server_ip'     :'192.168.59.252',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout'   :15,
    }

    # one group 
    group_info  = {
        'grp_name':'grp0',
        'grp_ssh_info':{
            'port':22,
            'user':None,
            'password':None,
            'timeout':15,
            'hostkey':'~/.ssh/id_rsa'
        },
        'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 130)}
    }

    server1     = lib_terminal.ClusterTerminal(server_info)
    #server1.add_grp(group_info)
    server1.run_forever()


test_server

