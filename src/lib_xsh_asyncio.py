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
    #level   = logging.DEBUG,
    format  = '%(asctime)s %(name)s %(process)d - %(thread)d:%(threadName)s - %(levelname)s - %(pathname)s %(funcName)s line: %(lineno)d - %(message)s',
    datefmt = '%Y/%m/%d %I:%M:%S %p'
)

fh3 = logging.FileHandler('../log/xsh_asyncio.log')
logger3 = logging.getLogger('lib_xsh_asyncio')
logger3.setLevel(logging.DEBUG)
logger3.addHandler(fh3)

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
    from lib_ssh_paramiko import SSHConnection

#from peewee import *
#import datetime
#

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
def get_group_output_report(output):
    _output_report = {}
    _total_hosts = len(output)
    #_unaccessable = 0
    _offline_hosts_list = []

    _summary = []
    # ['command1', 'command2']
    # [cmd_report1, cmd_report2]
    _cmd_report_dict = {
        'command':None,
        'error':0,
        'success':0,
        'success output sum':{}, # md5:{content:xx, number:xx, hosts:xx}#
        'error output sum':{}
    }
    #'md5': _output_dict
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
            #print(_out)

            # check sum dict of command/transfer 
            # this will be changed later
            #_sum = copy.deepcopy(_cmd_report_dict) # oops !!
            while len(_summary) < len(_out['stdin']):
                _sum = copy.deepcopy(_cmd_report_dict) # right
                _summary.append(_sum)

            # add each cmd info to its sum seq
            for report_index in range(len(_out['stdin'])):
                cmd_index = report_index

                # command text
                _summary[report_index]['command'] = _out['stdin'][cmd_index]
                #for i in _summary:
                #    print(i)
                #print(_summary[report_index]['command'])

                # count sucess and error for this command
                _item = copy.deepcopy(_output_dict)

                if _out['status'][cmd_index] == 0:
                    _summary[report_index]['success'] +=1

                    # count number for different success output 
                    _content = _out['stdout'][cmd_index]
                    _md5 = hashlib.md5(_content.encode('utf-8')).hexdigest()
                    if _md5 in _summary[report_index]['success output sum'].keys():
                        _summary[report_index]['success output sum'][_md5]['number'] +=1
                        _summary[report_index]['success output sum'][_md5]['hosts'].append(_out['host'])
                    else:
                        _summary[report_index]['success output sum'][_md5] = _item
                        _summary[report_index]['success output sum'][_md5]['content'] = _content
                        _summary[report_index]['success output sum'][_md5]['number'] +=1
                        _summary[report_index]['success output sum'][_md5]['hosts'].append(_out['host'])
                else:
                    _summary[_output_report]['error'] +=1
                    # count different failed output content
                    _content = _out['stderr'][cmd_index]
                    _md5 = hashlib.md5(_content.encode('utf-8')).hexdigest()
                    # again
                    if _md5 in _summary[report_index]['error output sum'].keys():
                        _summary[report_index]['error output sum'][_md5]['number'] +=1
                        _summary[report_index]['error output sum'][_md5]['hosts'].append(_out['host'])
                    else:
                        _summary[report_index]['error output sum'][_md5] = _item
                        _summary[report_index]['error output sum'][_md5]['content'] = _content
                        _summary[report_index]['error output sum'][_md5]['number'] +=1
                        _summary[report_index]['error output sum'][_md5]['hosts'].append(_out['host'])

        else:
            #_unaccessable +=1
            _offline_hosts_list.append(host_index)

    _output_report['total hosts'] = _total_hosts
    _output_report['unaccessable'] = _offline_hosts_list
    _output_report['output summary'] = _summary

    #for i in _summary:
    #    print(i)
    return _output_report

def print_group_output_report(_output_report):
    print('\ntask summary:')
    _total_hosts        = _output_report['total hosts']
    _offline_hosts_list = _output_report['unaccessable']
    _summary            = _output_report['output summary']

    print('total hosts:',   _total_hosts)
    print('offline hosts:', len(_offline_hosts_list))
    print('unaccessable:',  _offline_hosts_list)

    print('\nsubtask output summary:\n')
    for i in range(len(_summary)):
        _sum = _summary[i]
        print('task discription:',   _sum['command'])
        print('task success account:',       _sum['success'])
        print('task error account:',         _sum['error'])
        for m in _sum['success output sum']:
            _cmd_sum = _sum['success output sum'][m]
            print(_cmd_sum['number'], 'host', _cmd_sum['hosts'], '\n get a success output as:')
            print(_cmd_sum['content'])
        for m in _sum['error output sum']:
            _cmd_sum = _sum['error output sum'][m]
            print(_cmd_sum['number'], 'host', _cmd_sum['hosts'], '\n get an error output as:')
            print(_cmd_sum['content'])

def print_group_output(output):
    print_group_output_report(
        get_group_output_report(output)
    )

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

        self._histtory = []

    def _get_host_connection(self, hostname):
        # get ssh info combined together
        # (fqdn, ip)
        _host_info              = (hostname, self.ip_array[hostname])
        _host_ssh_info          = copy.deepcopy(self.ssh_info) # oops
        _host_ssh_info['host']  = _host_info

        #print(hostname, 'connection ', mode)
        #_msg = 'ssh connection group: ' +self.grp_name + ' get client connection @ ' +hostname 
        #logger3.debug(_msg)

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
        logger3.debug(self.grp_name + ' change connections status:' + mode)
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

    # run command or command list
    def run(self, command):
        return self.exec_command(command)

    def exec_command(self, command):
        return self.group_exec(command, task_type='exec_command')

    def exec_script(self, script_file):
        return self.group_exec(script_file, task_type='exec_script')

    def put(self, local_source, remote_dest):
        return self.group_exec(local_source, remote_dest, task_type='put')

    def get(self, remote_source, local_dest):
        return self.group_exec(remote_source, local_dest, task_type='get')

    def group_exec(self, *args, task_type='exec_command'):
        #print(type(args), args)
        logger3.debug(self.grp_name + ' running task ' + task_type +': ' + str(args))
        if task_type == 'exec_command':
            task_function = self._run_command_on_single_host
        elif task_type == 'exec_script':
            task_function = self._run_script_on_single_host
        elif task_type == 'put':
            task_function = self._put_to_single_host
        elif task_type == 'get':
            task_function = self._get_from_single_host

        self._histtory.append([task_type, args])

        self._output = {}
        _threads = []
        list(map(
                lambda hostname: _threads.append(
                    threading.Thread(
                        target=task_function,
                        args=(hostname, *args)
                    )
                ),
                self._connections
        ))
        [ x.start() for x in  _threads ]
        [ x.join() for x in _threads ]

        return self._output

    def _run_command_on_single_host(self, hostname, cmd_list):
        _con_obj = self._connections[hostname]
        if _con_obj :
            try:
                _out = _con_obj.exec_command(cmd_list)
            except:
                #_out = False 
                _out = None 
        else:
            _out = None
        self._output[hostname] = _out

    def _run_script_on_single_host(self, hostname, script_file):
        _con_obj = self._connections[hostname]
        if _con_obj :
            try:
                _out = _con_obj.exec_script(script_file)
            except:
                #_out = False
                _out = None 
        else:
            _out = None
        self._output[hostname] = _out

    def _put_to_single_host(self, hostname, local_source, remote_dest):
        _con_obj = self._connections[hostname]
        if _con_obj:
            _out = _con_obj.put(local_source, remote_dest)
            self._output[hostname] = _out
            #try:
            #    _out = _con_obj.put(local_source, remote_dest)
            #    self._output[hostname] = _out
            #except:
            #    #self._output[hostname] = False
            #    self._output[hostname] = None
        else:
            self._output[hostname] = None

    def _get_from_single_host(self, hostname, remote_source, local_dest):
        # different host different target directory
        local_dest = (local_dest +'/' + hostname +'/').replace('//', '/')
        _con_obj = self._connections[hostname]
        if _con_obj:
            try:
                _out = _con_obj.get(remote_source, local_dest)
                self._output[hostname] = _out
            except:
                self._output[hostname] = None
        else:
            self._output[hostname] = None

    # if a group is alive or unvalid 
    def is_alive(self):
        return True in map(
            lambda con: con.is_alive(),
            filter(
                lambda ssh_con: ssh_con != None,
                self._connections.values()
            )
        )

    def get_health_status(self):
        _result = {}
        _result['accessable hosts'] = list(
            filter(
                lambda x: self._connections[x] != None,
                self._connections
            )
        )
        _result['unaccessable hosts'] = list(
            filter(
                lambda x: self._connections[x] == None,
                self._connections
            )
        )
        _result['accessable'] = len(_result['accessable hosts'])
        _result['unaccessable'] = len(_result['unaccessable hosts'])
        return _result

    def get_history(self, history_length=0):
        return self._histtory

    def clean_up_history(self):
        self._histtory = []

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
            'host' + str(x) : '192.168.59.' + str(x) for x in range(110, 150)
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
    # summary for each single host
    # summary for each single cmd
#ok    out0 = xsh.exec_command('lsblk')
#    print_group_output(out0)

    # exec command list
#ok    cl = ['ls /etc/ssh/', 'echo $HOME']
#    out00 = xsh.exec_command(cl)
#    # by host
#    print(out00['host252'])
#    rpt = get_group_output_report(out00)
#    # by cmd index
#    print(cl[1])
#    print(rpt['output summary'][1])

    # a failed command
#ok    out1 = xsh.exec_command('ls failtest')
#    print_group_output(out1)

#ok    out01 = xsh.run('lsblk')
#    print_group_output(out01)

    # run a script
#ok    out2 = xsh.exec_script('~/a.sh')
#    print(out2)
#    print_group_output(out2)

    # distribute a file
#ok    out3 = xsh.put('~/a.sh', '~/aabb')
#    print_group_output(out3)

    # distribute a dir
#ok    out4 = xsh.put('~/aabc', '~/abc')
    #print(out4)
    #print(out4['host252'])
#    print_group_output(out4)

    # collect dir from group
#ok    out5 = xsh.get('~/abc', '~/abc')
#    print_group_output(out5)

    # collect one file from group to a dir 
#ok    out6 = xsh.get('/etc/os-release', '~/osinfo')
#    print_group_output(out6)

    # get hosts list
#ok    h = xsh.hosts()
#    print(h)

    # run cmd on a certain host
#ok    if xsh['host250']:
#        out7 = xsh['host250'].exec_command('echo $HOSTNAME')
#        print(out7)
#    if xsh['host252']:
#        out7 = xsh['host252'].exec_command('echo $HOSTNAME')
#        print(out7)

    # get connections list 
#ok    c = xsh.connections()
#    print(c)

    # get ssh info
#ok    print(xsh.ssh_info)
#    print(xsh.ip_array)

    # get connections group health status
#ok    if xsh.is_alive():
#        s = xsh.get_health_status()
#        #print(s['alive'])
#        print(s)

    # get cmd history
    # clean up history
    out8 = xsh.exec_command(['echo $HOSTNAME', 'lsblk'])
    print_group_output(out8)
    hs = xsh.get_history()
    print(hs)
#    xsh.clean_up_history()
#    hs2 = xsh.get_history()
#    print(hs2)

    # close connections 
    xsh.close()

    # reconnect
#    xsh.reconnect()

    # get a task to be executed over again
#    xsh.redo_task(xsh.get_history()[-1]) 

    # stop action
#    xsh.stop()

    # get fault tolerance info
#    xsh.get_valid_ratio()

    # configure fault tolerance 20%
#    xsh.set_valid_ratio(20.0)


