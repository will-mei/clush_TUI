#!/usr/bin/env python
# coding=utf-8

import threading
import logging
logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%Y/%m/%d %I:%M:%S %p')

# host group info 
#{
#    'host_group_name':'grp0',
#    'grp_ssh_info':{
#        'port':22,
#        'user':None,
#        'password':None,
#        'timeout':15,
#        'hostkey':'~/.ssh/id_rsa'
#    }
#    'grp_ip_list':[
#        '192.168.1.1',
#        '192.168.1.2',
#    ],
#}


# save log to a certain db 

import copy 

# a wharfage with a watchdog to keep a group of ssh connection alive, and status info maintainable 
class host_con_group:

    # all hosts in a same group share the same login user and ssh port 
    def __init__(self, grp_info, admin_terminal):
        self.grp_info   = grp_info 
        self.grp_name   = grp_info['grp_name'] 
        #
        self.terminal   = admin_terminal
        if len(self.grp_info['grp_ip_array']):
            self._group_connect()

    def _host_connect(self, host_info):
        _host_ssh_info = self.grp_info['grp_ssh_info']
        _host_ssh_info['host'] = host_info
        try:
            return SSHConnection(_host_ssh_info)
        except:
            return None 

    def _group_connect(self):
        _online_hosts = list(
            filter(lambda x : x != None,
                map(
                    _host_connect,
                    self.grp_info['grp_ip_array'].items()
                )
            )
        )

    @property 
    def online_hosts(self):
        return self._online_hosts
    @online_hosts.setter
    def online_hosts(self):
        try:
            # verify something and set value 
            list(
                map(
                    self.check_alive, self.grp_info[grp_ip_array].values()
                )
            )
            _self._online_hosts.append(hostname)
        except:
            pass 

    # run command on all host 
    def group_exec(self, cmd_list):
        # load command and put to threading pool 
        pass 

    # check the accessablility of a host, like a quarantine 
    def is_alive(self, hostname):
        pass 

    # add a new online host to connection pool 
    def docking(self, hostname):
        if self.inspect(hostnames):
            pass 

    # close the connection of a online host, but it's still in the host ip list 
    # waiting reboot or some 
    def cut_off(self, hostname):
        pass

    # drive out a offline host, remove form host_ip_list 
    def expel(self, hostname):
        self.cut_off(hostname)
        pass

    # the output can be updated by any host in this group 
    def update_output(self):
        pass 



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
        map(lambda grp : grp.admin = self.name, terminal2.con_groups)
        return self 

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

    def copy(self):
        pass
    def fromkeys(self):
        pass
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
        'server_token':'p@ssw0rd'
        'workers':3,
        'con_max':128,
    }
    # init info for a connection group 
    # if you have an ip without knowing its fqdn, use the ip as fqdn
    g = {
            'grp_name':'grp0',
            'grp_ssh_info':{
                'port':22,
                'user':None,
                'password':None,
                'timeout':15,
                'hostkey':'~/.ssh/id_rsa'
            },
            'grp_ip_array':{
                'host1':'192.168.1.1',
                'host2':'192.168.1.2',
                'host3':'192.168.1.3',
                '192.168.1.4':'192.168.1.4',
            },
        }
    T = cluster_ssh_terminal(t)
    T.add_grp(g)
    #
    T['grp0'].grp_run('lsblk')
    T['grp0']['host1'].run('lsblk')
    #
    #T.grp['grp0'].grp_run('lsblk')
    #T.grp['grp0']['host1'].run('blkid')


