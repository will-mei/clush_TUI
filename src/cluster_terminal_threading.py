#!/usr/bin/env python
# coding=utf-8

#import threading
#import copy 

#import asyncio
#from gevent import monkey; monkey.patch_socket()
#import gevent

# save log to both log file and a certain db 
#import logging
#logging.basicConfig(
#    format='%(asctime)s %(message)s',
#    datefmt='%Y/%m/%d %I:%M:%S %p')

#from multiprocessing.dummy import Pool as ThreadPool
#from multiprocessing import Pool 

import threading
import time



try:
    from src import paramiko_tools
except:
    import paramiko_tools


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
class host_con_group:

    # all hosts in a same group share the same login user and ssh port 
    def __init__(self, grp_info, admin_terminal):
        self.grp_info   = grp_info 
        self.grp_name   = grp_info['grp_name'] 
        self.terminal   = admin_terminal
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
        time.sleep(0)
        print(hostname, 'connection ', mode)
        if mode == 'init':
            try:
                self._connections[hostname] = paramiko_tools.SSHConnection(_host_ssh_info)
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
        list(map(
            lambda x: x.start(),
            _threads
        ))
        list(map(
            lambda x: x.join(),
            _threads
        ))

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
                    threading.Thread(
                        target=self.single_run,
                        args=(hostname, cmd_list)
                    )
                ),
                self._connections
        ))
        list(map(
            lambda x: x.start(),
            _threads
        ))
        list(map(
            lambda x: x.join(),
            _threads
        ))
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


# communicate wiht other app 
# here defines what you can do to a group 
class cluster_ssh_terminal:

    def __init__(self, server_info):

        # an array hold connection groups obj and its name 
        self._host_group_array  = {}
        # init info 
        self._server_info       = server_info 
        # tcp socket 
        self.socket             = socket.socket(socket.AF_INET,
                                                socket.SOCK_STREAM
                                               )
        self.socket.bind(
            (self._server_info['server_ip'],
             self._server_info['server_port'])
        )
        self.listen(
            self._server_info['con_max']
        )

    # the server info cannot be changed without token
    @property
    def server_info(self):
        pass
    @server_info.setter 
    def server_info(self):
        pass 

    def __add__(self, terminal2):
        #map(lambda grp : grp.admin = self.name, terminal2.con_groups)
        #return self 
        pass

    # run command list on all groups 
    def brodcast_cmd(self, cmd_list):
        pass 

#    def __class__(self):
#        pass

    def __contains__(self, grp_name):
        return self.has_grp(grp_name)
    def has_key(self, grp_name):
        return self.has_grp(grp_name)
    def has_grp(self, grp_name):
        return self._host_group_array.__contains__(grp_name)

#    def __delattr__(self):
#        pass

    def __delitem__(self):
        # remove name and info
        del self.host_group_list_array[key]
        # close all connections on that group
        map(lambda con : con.close(), self.group_connection_dict[key].connections())
        pass

#    def __dir__(self):
#        pass
#    def __doc__(self):
#        pass
#    def __eq__(self):
#        pass
#    def __format__(self):
#        pass
#    def __ge__(self):
#        pass
#    def __getattribute__(self):
#        pass
    def __getitem__(self):
        pass
#    def __gt__(self):
#        pass
#    def __hash__(self):
#        pass
#    def __init__(self):
#        pass
#    def __init_subclass__(self):
#        pass
#    def __iter__(self):
#        pass
#    def __le__(self):
#        pass
    def __len__(self):
        pass
#    def __lt__(self):
#        pass
#    def __ne__(self):
#        pass
#    def __new__(self):
#        pass
#    def __reduce__(self):
#        pass
#    def __reduce_ex__(self):
#        pass
#    def __repr__(self):
#        pass
#    def __setattr__(self):
#        pass
#
    # key: grp_name
    # value: grp_connections
    def __setitem__(self, grp, grp_con):
        self._host_group_array[grp] = grp_con
        pass
#    def __sizeof__(self):
#        pass

    def __str__(self):
        return list(map(lambda grp : grp.name, self.con_groups))
        pass

#    def __subclasshook__(self):
#        pass

    def clear(self):
        map(lambda con_grp : con_grp.close(self.name), self.con_groups)
        self._host_group_array.clear()

#    def copy(self):
#        pass
#    def fromkeys(self):
#        pass
#    def get(self):
#        pass

    def items(self):
        pass

    def keys(self):
        return self.hosts()
    def hosts(self):
        pass

    def pop(self):
        pass

    def popitem(self):
        pass

#    def setdefault(self):
#        pass

#    def update(self):
    def update_connection(self):
        pass 
    def values(self):
        return self.connections()
    def connections(self):
        pass

if __name__ == "__main__":
    # init info for a terminal server 
    t = {
        'server_ip':'127.0.0.1',
        'server_port':60000,
        'server_token':'p@ssw0rd',
        'workers':3,
        'con_max':128,
    }
    # init info for a connection group 
    # if you have an ip without knowing its fqdn, use the ip as fqdn
    g = {
        'grp_name':'grp0',
        # process :less than cores *10  (20)
        # thread :
        #'grp_concurrency':20,
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
        #    'host4':'192.168.59.14',
        #    'host5':'192.168.59.15',
        #    'host6':'192.168.59.16',
        #    'host7':'192.168.59.17',
        #    'host8':'192.168.59.18',
        #},
        'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 130)}
        #'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 40)}
        #'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 30)}
    }
    #T = cluster_ssh_terminal(t)
    #T.add_grp(g)
    ##
    #out1 = T['grp0'].grp_run('lsblk')
    #out2 = T['grp0']['host1'].run('lsblk')
    ##
    ##T.grp['grp0'].grp_run('lsblk')
    ##T.grp['grp0']['host1'].run('blkid')

    #print(out1)
    #print(out2)

    g_con = host_con_group(g, t)
    print(g_con._connections)
    #print(g_con._connections )
    if g_con.is_alive():
        out1 = g_con.run('lsblk')
        list(
            map(print,
                out1['host11'][1]     
               )
        )
    else:
        print('alive: ', g_con.is_alive())
    #out2 = g_con.run(['ls abc', 'ls'])
    #print(out2)
    g_con.close()

