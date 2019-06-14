#!/usr/bin/env python
# coding=utf-8


try:
    from src.lib_api_server import api_server
except:
    from lib_api_server import api_server 

# save log
import logging
logging.basicConfig(
    #filename= '/var/log/messages',
    filename= '../log/messages',
    level   = logging.INFO,
    format  = '%(asctime)s %(name)s %(process)d - %(thread)d:%(threadName)s - %(levelname)s - %(pathname)s %(funcName)s line: %(lineno)d - %(message)s',
    datefmt = '%Y/%m/%d %I:%M:%S %p'
)
#rHandler = RotatingFileHandler("log.txt", maxBytes = 100*1024*1024, backupCount = 5)
#rHandler.setLevel(logging.INFO)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#rHandler.setFormatter(formatter)
#logger.addHandler(rHandler)

#from multiprocessing.dummy import Pool as ThreadPool
#from multiprocessing import Pool 

import threading
import time

#from gevent import monkey; monkey.patch_socket()
#import gevent

#import asyncio

import hashlib

try:
    from src.lib_ssh_paramiko import SSHConnection
except:
    from lib_ssh_paramiko import SSHConnection

#from peewee import *
#import datetime
#
#cluster_db = SqliteDatabase('../db/cluster_database.db')
#
#class BaseModel(Model):
#    class Meta:
#        database = cluster_db

cluster_db
task_db
device_db
io_test_db
outut_db


# check ip format 
def valid_ip(ip):
    return ip.split('.') == 4 and \
            len(
                filter(
                    lambda x: x >=0 and x <=255,
                    map(
                        int,
                        filter(
                            lambda x: x.isdigit(),
                            ip.split('.')
                        )
                    )
                )
            ) == 4


# a wharfage with a watchdog to keep a group of ssh connection alive, and status info maintainable 
class ConnectionGroup:

    # all hosts in a same group share the same login user and ssh port 
    def __init__(self, grp_info, admin_terminal):
        self.grp_info   = grp_info 
        self.grp_name   = grp_info['grp_name'] 
        self.term_id    = admin_terminal
        # host:connection 
        self._connections = {}
        #
        if len(self.grp_info['grp_ip_array']):
            self._group_connect('init')

    def _host_connect(self, hostname, mode='init'):
        # get ssh info combined together
        # (fqdn, ip)
        _host_info              = (hostname, self.grp_info['grp_ip_array'][hostname])
        _host_ssh_info          = self.grp_info['grp_ssh_info']
        _host_ssh_info['host']  = _host_info

        # sleep for threading 
        #time.sleep(0)

        #print(hostname, 'connection ', mode)
        _msg = 'ssh connection group: ' +self.grp_name + ' '+mode +' connection @' +hostname 
        logging.debug(_msg)

        if mode == 'init':
            try:
                self._connections[hostname] = SSHConnection(_host_ssh_info)
                print(hostname, 'ssh success')
            except:
                self._connections[hostname] = None
        elif mode == 'update':
            self._connections[hostname]._ssh_info = _host_ssh_info
            self._connections[hostname].update_connection()
        elif mode == 'reconnect':
            self._connections[hostname].reconnect()
        elif mode == 'close' and self._connections[hostname]:
            self._connections[hostname].close()

    def _group_connect(self, mode):
        _threads         = []
        list(map(
                lambda hostname: _threads.append(
                    threading.Thread(target=self._host_connect, args=(hostname, mode) )
                ),
                self.grp_info['grp_ip_array']
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]

    # reconnect all connections 
    def reconnect(self):
        self._group_connect('reconnect')

    # reconnect the failed ones
    def update_connections(self):
        # update grp_info
        self._group_connect('update')

    def close(self):
        self._group_connect('close')

    # bind key of output 
    def single_run(self, hostname, cmd_list):
        _con_obj = self._connections[hostname]
        if _con_obj :
            try:
                _out = _con_obj.run(cmd_list)
            except:
                _out = None 
        else:
            _out = None
        self._output_data[hostname] = _out

    # run command on all host 
    def grp_run(self, cmd_list):
        self._output_data = {}

        _threads         = []
        list(map(
                lambda hostname: _threads.append(
                    threading.Thread(target=self.single_run,
                                     args=(hostname, cmd_list))
                ),
                self._connections
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]
        return self._output_data 

    def run(self, cmd_list):
        return self.grp_run(cmd_list)

    # if a group is alive or unvalid 
    def is_alive(self):
        return True in map(
            lambda con: con.is_alive(),
            filter(
                lambda ssh_con: ssh_con != None,
                self._connections.values()
            )
        )

    # close the connection of a online host, but it's info is still in the grp_info 
    def cut_off(self, hostname):
        if self._connections[hostname]:
            self._connections[hostname].close()

    # drive out or expel a host, info removed , connection closed 
    # its connection cannot be reused any more 
    def expel(self, hostname):
        self.cut_off(hostname)
        del self.grp_info['grp_ip_array'][hostname]

    def __getitem__(self, hostname):
        return self._connections[hostname]

    def __setitem__(self, hostname, connection):
        if isinstance(hostname, str):
            self._connections[hostname] = connection 

    def __delitem__(self, hostname, connection):
        del self._connections[hostname]

    def __iter__(self):
        return ( h for h in self._connections )

    def __len__(self):
        return len(self._connections)

    def keys(self):
        return self._connections.keys()

    def values(self):
        return self._connections.values()

    def hosts(self):
        return list(self._connections.keys())

    def connections(self):
        return list(filter(
            lambda x : x != None,
            self._connections.values()
        ))
    def __str__(self):
        return str(list(map(
            lambda x : x + ' : ' + str(self._connections[x]),
            self._connections
        )))
        #return str(self._connections)

# communicate wiht other app 
# here defines what you can do to a group 
class ClusterTerminal(api_server):

    def create(self):
        self._groups  = {}

    def parse_call(self, _data):
        if _data['tag'] == 'msg':
            self.parse_msg(_data['data'])
        else:
            self.perform_task(_data)

    def perform_task(self, _data):
        print('call with tag:', _data['tag'])
        print('data content:', _data['data'])

    def parse_msg(self, _msg):
        print('recived msg:', _msg)

    # run command list on all groups 
    def brodcast_cmd(self, cmd_list):
        print('broadcast cmd:', cmd_list)

#    def __contains__(self, grp_name):
#        return self.has_grp(grp_name)
#    def has_key(self, grp_name):
#        return self.has_grp(grp_name)
#    def has_grp(self, grp_name):
#        return self._host_group_array.__contains__(grp_name)
#
    def __getitem__(self):
        pass

    def __delitem__(self):
        # close all connections on that group
        map(lambda con : con.close(), self._groups[key].connections())
        # remove name and info
        del self._groups[key]

#    def __len__(self):
#        pass

    # key: grp_name
    # value: grp_connections
#    def __setitem__(self, grp, grp_con):
#        self._host_group_array[grp] = grp_con
#        pass

#    def __str__(self):
#        return list(map(lambda grp : grp.name, self.con_groups))
#        pass

#    def clear(self):
#        map(lambda con_grp : con_grp.close(self.name), self.con_groups)
#        self._host_group_array.clear()

#    def items(self):
#        pass
#
#    def keys(self):
#        return self.groups()
#    def groups(self):
#        pass
#
#    def pop(self):
#        pass
#
#    def popitem(self):
#        pass
#
#    def setdefault(self):
#        pass

#    def update(self):
#    def update_connection(self):
#        pass 
#    def values(self):
#        return self.connections()
#    def connections(self):
#        pass

if __name__ == "__main__":
    # local settings

    # init info for a terminal server 
    # there will be a hash str send to terminal alone with the cmd, all commands will be hashed with it 
    server_info = {
        'server_id'     :b'test_user_id',
        'server_ip'     :'192.168.59.252',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout'   :15,
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

    grp_con = ConnectionGroup(g, server_info['server_id'])
    #print(grp_con._connections)

    if grp_con.is_alive():
        out1 = grp_con.run('lsblk')
        list(map(print, out1['host11'][1] ))
    else:
        print('alive: ', grp_con.is_alive())
    #
    for h in grp_con.hosts()[1:3]:
        print(h)

    if grp_con['host12']:
        grp_con['host12'].run('echo $HOSTNAME')

    if grp_con['host11']:
        out2 = grp_con['host11'].run(['ls abc', 'ls'])
        print(out2)
    grp_con.close()

    #print('values:', grp_con.values())
    print('connections:', grp_con.connections())
    #print('connection group:', grp_con)



    #T = cluster_ssh_terminal(t)
    #T.add_grp(g)

    #out1 = T['grp0'].run('lsblk')
    #out2 = T['grp0']['host1'].run('lsblk')

    #print(out1)
    #print(out2)
