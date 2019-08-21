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
    #filename= '../log/messages',
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
import copy

try:
    from src.lib_ssh_paramiko import SSHConnection
except:
    from lib_ssh_paramiko import SSHConnection,print_output

#from peewee import *
#import datetime
#
#cluster_db = SqliteDatabase('../db/cluster_database.db')
#
#class BaseModel(Model):
#    class Meta:
#        database = cluster_db

#terminal.db
#   groups 
#   hosts 
#   device 
#   
#task.db
#   exec source 
#   target
#
#outut_db
#   task
#   test
#   cmd
#
##io_test_db


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

# give the output summary of a single command
def print_group_output(output):
    #_unaccessable = 0
    _offline_hosts = []
    _total = len(output)
    _summary = []

    _report_dict = {
        'command':None,
        'error':0,
        'success':0,
        'success output sum':{}, # md5:{content:xx, number:xx, hosts:xx}#
        'error output sum':{}
    }
    #
        #'md5': None,
    _output_dict = {
        'content': None,
        'number': 0,
        'hosts': []
    }

    # the result of a host
    for host_index in output:
        # not None
        if output[host_index]:
            _out = output[host_index]

            # check sum dict
            # ['cmd1', 'cmd2']
            # [_sum1, _sum2]
            _sum = copy.deepcopy(_report_dict)
            while len(_summary) < len(_out['stdin']):
                _summary.append(_sum)

            # add cmd info to sum seq
            for i in range(len(_out['stdin'])):
                # command text
                _summary[i]['command'] = _out['stdin'][i]
                # count sucess and error 
                _item = copy.deepcopy(_output_dict)
                if _out['status'][i] == 0:
                    _summary[i]['success'] +=1
                    # count success output content
                    _content = _out['stdout'][i]
                    _md5 = hashlib.md5(_content.encode('utf-8')).hexdigest()
                    if _md5 in _summary[i]['success output sum'].keys():
                        _summary[i]['success output sum'][_md5]['number'] +=1
                        _summary[i]['success output sum'][_md5]['hosts'].append(_out['host'])
                    else:
                        _summary[i]['success output sum'][_md5] = _item
                        _summary[i]['success output sum'][_md5]['content'] = _content
                        _summary[i]['success output sum'][_md5]['number'] +=1
                        _summary[i]['success output sum'][_md5]['hosts'].append(_out['host'])
                else:
                    _summary[i]['error'] +=1
                    # count success output content
                    _content = _out['stderr'][i]
                    _md5 = hashlib.md5(_content.encode('utf-8')).hexdigest()
                    if _md5 in _summary[i]['error output sum'].keys():
                        _summary[i]['error output sum'][_md5]['number'] +=1
                        _summary[i]['error output sum'][_md5]['hosts'].append(_out['host'])
                    else:
                        _summary[i]['error output sum'][_md5] = _item
                        _summary[i]['error output sum'][_md5]['content'] = _content
                        _summary[i]['error output sum'][_md5]['number'] +=1
                        _summary[i]['error output sum'][_md5]['hosts'].append(_out['host'])

        else:
            #_unaccessable +=1
            _offline_hosts.append(host_index)

    print('\ntask summary:')
    print('total hosts:',   _total)
    print('offline hosts:', len(_offline_hosts))
    print('unaccessable:',  _offline_hosts)
    print('\noutput summary:')
    for i in range(len(_summary)):
        _sum = _summary[i]
        print('command:',   _sum['command'])
        print('success:',   _sum['success'])
        print('error:',     _sum['error'])
        for m in _sum['success output sum']:
            _cmd_sum = _sum['success output sum'][m]
            print(_cmd_sum['number'], 'host', _cmd_sum['hosts'], '\ncmd successfully returned as:')
            print(_cmd_sum['content'])
        for m in _sum['error output sum']:
            _cmd_sum = _sum['error output sum'][m]
            print(_cmd_sum['number'], 'host', _cmd_sum['hosts'], '\ncmd with error returned as:')
            print(_cmd_sum['content'])

# a wharfage with a watchdog to keep a group of ssh connection alive, and keep their status info maintainable 
# pass in server info
# get group info
# build connects to all the hosts
# run cmd/script on specified host
# give a summary of group executation result.

class ConnectionGroup:

    # all hosts in a same group share the same login info 
    def __init__(self, grp_info):
        self.grp_name   = grp_info['grp_name']
        self.ssh_info   = grp_info['grp_ssh_info']
        self.ip_array   = grp_info['grp_ip_array']
        # host connection obj list 
        self._connections = {}
        # get hosts connected
        if len(self.ip_array):
            self._manage_connections(mode='update')

    def _get_host_connection(self, hostname):
        # get ssh info combined together
        # (fqdn, ip)
        _host_info              = (hostname, self.ip_array[hostname])
        _host_ssh_info          = self.ssh_info
        _host_ssh_info['host']  = _host_info

        #print(hostname, 'connection ', mode)
        _msg = 'ssh connection group: ' +self.grp_name + 'get ssh client connection @' +hostname 
        logging.debug(_msg)

        # ignore the failed ones
        try:
            _connection = SSHConnection(_host_ssh_info)
            #print(hostname, 'ssh success')
        except:
            _connection = None
            #print(hostname, 'ssh failed')

        return _connection

    def _alter_host_connection(self, hostname, mode='update'):
        if mode == 'update':
            self._connections[hostname] = self._get_host_connection(hostname)
        elif self._connections[hostname]:
            if mode == 'reconnect':
                self._connections[hostname].reconnect()
            elif mode == 'close':
                self._connections[hostname].close()
        else:
            pass

    def _manage_connections(self, mode):
        _threads_list   = []
        list(map(
                lambda hostname: _threads_list.append(
                    # thread for connecting remote host
                    threading.Thread(
                        target=self._alter_host_connection,
                        args=(hostname, mode) 
                    )
                ),
                self.ip_array
        ))
        # start every thread
        [ x.start() for x in  _threads_list ]
        # join and end
        [ x.join() for x in _threads_list ]

    def close(self):
        self._manage_connections('close')

    # reconnect the existed ones
    def reconnect(self):
        self._manage_connections('reconnect')

    # reconnect all connections 
    def update_connections(self):
        # update grp_info
        self._manage_connections('update')

    def _run_on_single_host(self, hostname, cmd_list):
        _con_obj = self._connections[hostname]
        if _con_obj :
            try:
                _out = _con_obj.run(cmd_list)
            except:
                _out = None 
        else:
            _out = None
        self._output[hostname] = _out

    # run command of command list
    def run(self, command):
        self.exec_command(command)

    # run command on all host
    def exec_command(self, cmd_list):
        # 
        self._output = {}

        _threads = []
        list(map(
                lambda hostname: _threads.append(
                    threading.Thread(
                        target=self._run_on_single_host,
                        args=(hostname, cmd_list)
                    )
                ),
                self._connections
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]

        return self._output

    def put(self, local_source, remote_dest):
        _threads = []
        list(map(
            lambda hostname: _threads.append(
                threading.Thread(
                    target=self._put_to_single_host,
                    args=(hostname, local_source, remote_dest)
                )
            ),
            self._connections
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]

    def _put_to_single_host(self, hostname, local_source, remote_dest):
        _con_obj = self._connections[hostname]
        try:
            if _con_obj:
                _con_obj.put(local_source, remote_dest)
        except:
            pass

    def get(self, remote_source, local_dest):
        _threads = []
        list(map(
            lambda hostname: _threads.append(
                threading.Thread(
                    target=self._get_from_single_host,
                    args=(hostname, remote_source, local_dest)
                )
            ),
            self._connections
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]

    def _get_from_single_host(self, hostname, remote_source, local_dest):
        local_dest = (local_dest +'/' + hostname +'/').replace('//', '/')
        _con_obj = self._connections[hostname]
        try:
            if _con_obj:
                _con_obj.get(remote_source, local_dest)
        except:
            pass

    # if a group is alive or unvalid 
    def is_alive(self):
        return True in map(
            lambda con: con.is_alive(),
            filter(
                lambda ssh_con: ssh_con != None,
                self._connections.values()
            )
        )

    # drive out a host, info removed , connection closed 
    def remove_host(self, hostname):
        if self._connections[hostname]:
            self._connections[hostname].close()
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
    # a host group 
    # if you have an ip without knowing its fqdn, use the ip as fqdn
    g = {
        'grp_name':'grp0',
        'grp_ssh_info':{
            'port':None,
            'user':None,
            'password':None,
            'timeout':15,
            'hostkey':'~/.ssh/id_rsa'
        },
        'grp_ip_array': {
            # hostname:ip
            'host' + str(x) : '192.168.59.' + str(x) for x in range(200, 254)
        }
    }

    # precheck / connect / exec_command 
    # stdin
    # stdout
    # status
    # stderr
    # time costs
    # host id

    # xsh obj is a host connection group
    xsh = ConnectionGroup(g)
    #print(xsh._connections)

    # run a command
#ok    out0 = xsh.exec_command('lsblk')
    # summary for each single host
    # summary for each single cmd
#    print_group_output(out0)

    # a failed command
#ok    out1 = xsh.exec_command('ls failtest')
#    print_group_output(out1)

#    # run a script
#    xsh.exec_script('~/a.sh')
#
    # distribute a file
    xsh.put('~/a.sh', '~/aabb')
#
#    # distribute a dir
#    xsh.put('~/abc', '~/abc')
#
#    # collect one file from group to a dir 
#    xsh.get('/etc/redhat-release', '~/release')
#
#    # collect dir from group
#    xsh.get('/etc/ssh/', '~/ssh')
#
#    # configure fault tolerance 20%
#    xsh.set_valid_ratio(20.0)
#
#    # get fault tolerance info
#    xsh.get_valid_ratio()
#
#    # get cmd history
#    xsh.get_history()
#
#    # get a task to be executed over again
#    xsh.redo_task(xsh.get_history()[-1]) 
#
#    # clean up history
#    xsh.clean_up_history()
#
#    # run cmd on a certain host
#    xsh['host1'].exec_command('echo $HOSTNAME')
#
#    # get hosts list
#    xsh.hosts()
#
#    # get connections list 
#    xsh.connections()
#
#    # get ssh info
#    xsh.ssh_info()
#
#    # get connections group health status
#    xsh.health_info()
#
    # close connections 
    xsh.close()
#
#    # reconnect
#    xsh.reconnect()
#
#    # stop action
#    xsh.stop()


    # recive info from socket
    # there will be a hash str send to terminal alone with the cmd, all commands will be hashed with it 
    s = {
        'server_id'     :b'test_user_id',
        'server_ip'     :'192.168.59.102',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout'   :15,
    }


    #T = cluster_ssh_terminal(t)
    #T.add_grp(g)

    #out1 = T['grp0'].run('lsblk')
    #out2 = T['grp0']['host1'].run('lsblk')

    #print(out1)
    #print(out2)

