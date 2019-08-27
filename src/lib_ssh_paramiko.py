#!/usr/bin/env python3
# coding=utf-8

# only for linux platform

import os
import sys 
import paramiko
import datetime
try:
    from src import lib_cli_bash
except:
    import lib_cli_bash
import  warnings

warnings.filterwarnings('ignore')

#import logging
# temporarily no log func , nothing will be loged to logfile or db

#import asyncio 

import string,random

import copy
from collections import Iterable

def random_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def print_host_output(output):
    print('\noutput summary:')
    print("cmd list:",          output['stdin'])
    print("cmd pid:",           output['pid'])
    print("cmd stdout:",        output['stdout'])
    #for i in output['stdout']:
    #    print(i)
    print("cmd stderr:",        output['stderr'])
    print("cmd return status:", output['status'])
    print("cmd return time:",   output['date'])
    print("cmd host:",          output['host'])

class SSHConnection(object):
    def __init__(self, ssh_info):
        self._ssh_info      = ssh_info
        self.update_ssh_info(ssh_info)
        # ssh socket
        self._transport     = None
        self._sftp          = None
        self._client        = None
        self._connect()  # 建立连接

        # clean output
        self._output_dict = {}
        self._output_dict['pid']      = []
        self._output_dict['stdin']    = []
        self._output_dict['stdout']   = []
        self._output_dict['stderr']   = []
        self._output_dict['status']   = []
        self._output_dict['date']     = []
        self._output_dict['host']     = self._host

    def update_ssh_info(self, ssh_info):
        self.fqdn           = ssh_info['host'][0]
        self.ipaddr         = ssh_info['host'][1]
        self._host          = self.ipaddr 
        self._port          = ssh_info['port']
        self._username      = ssh_info['user']
        self._password      = ssh_info['password']
        self._timeout       = ssh_info['timeout']
        self._key_filename  = ssh_info['hostkey'].replace('~', os.path.expanduser('~'))

    # closure with connection info stored 
    def _init_client(self):
        h = self._host
        u = username=self._username
        p = password=self._password
        k = key_filename=self._key_filename
        # connect obj 
        _client = paramiko.SSHClient()
        # -q 
        _client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # test connection 
        _client.connect(
            h,
            username = u,
            password = p,
            key_filename = k,
        )
        # give a reconnect callback
        def _client_connect_fn():
            _client.connect(
                h,
                username = u,
                password = p,
                key_filename = k,
            )
            return _client
        return _client_connect_fn

    def _connect(self, mode='update'):
        # generate paramiko client connection
        if not self._client or mode == 'update':
            self._get_con_fn    = self._init_client()
            self._client = self._get_con_fn()
        elif mode == 'reconnect':
            self._client = self._get_con_fn()

        # check _client
        self._transport = self._client._transport
        self._transport.setName(self._host)
        self._transport.setName(self._host)

    # connect with the ssh info which were used at the very begining of its creation
    def reconnect(self):
        if self._client:
            self._connect(mode='reconnect')
        else:
            self._connect()

    def update_connection(self):
        self._connect(mode='update')

    def localpath_expansion(self, localpath):
        # 家目录替换
        if localpath[:2] == '~/':
            _localpath = os.environ['HOME'] + localpath[1:]
        else:
            _localpath = localpath
        # 绝对路劲转换
        _localpath = os.path.abspath(_localpath)

        # 注意,输出结果结尾无'/'后缀
        if localpath[-1] == '/':
            _localpath = _localpath + '/'

        print("local", localpath, "abspath:", _localpath)
        return _localpath

    def remotepath_expansion(self, remotepath):
        _target_type = self.remote_target_type(remotepath)
        # dir
        if _target_type == 'directory':
            _out = self.exec_command('echo $(cd %s && pwd)' % remotepath)
            #print_host_output(_out)
            if _out['status'][0] == 0:
                _remotepath  = _out['stdout'][0].strip()
        # file
        elif _target_type == 'file':
            # class paramiko.sftp_si.SFTPServerInterface 
            #_remotepath = self._sftp.canonicalize(remotepath)
            _out = self.exec_command('echo $(cd $(dirname %s) && pwd)' % remotepath)
            if _out['status'][0] == 0:
                _remotepath  = _out['stdout'][0].strip() + '/' + os.path.basename(remotepath)
        elif remotepath[:2] == '~/':
            _out = self.exec_command('echo $HOME')
            if _out['status'][0] == 0:
                _remotepath = _out['stdout'][0].strip() + remotepath[1:]
        else:
            _remotepath = remotepath

        if remotepath[-1] == '/':
            _remotepath = (_remotepath + '/').replace('//', '/')

        print("remote", remotepath, "abspath:", _remotepath)
        return _remotepath

    def remote_target_type(self, remotepath):
        # no ready method to use 
        _out = self.exec_command('file -b %s' % remotepath)
        #if _out['status'][0] == 0:
            # this doesn't work, it always return success
        #else:
        #    raise EnvironmentError("cannot stat target type: %s" % remotepath)

        # check the output text instead
        if 'No such file or directory' in _out['stdout'][0]:
            #raise FileNotFoundError(remotepath + _out['stdout'][0])
            return 'other'
        elif 'Permission denied' in _out['stdout'][0]:
            #raise PermissionError(remotepath + _out['stdout'][0])
            return 'other'
        elif _out['stdout'][0].strip() == 'directory':
            return 'directory'
        else:
            return 'file'

    def walk_local_dir_content(self, dirname):
        _result = []
        for d in os.walk(dirname):
            # dir
            if d[0] != dirname:
                _result.append(d[0])
            # file
            if d[2]:
                for f in d[2]:
                    _result.append(
                        (d[0] + '/' + f).replace('//', '/')
                    )
        return _result

    def reset_command_output(self):
        # clean output
        self.command_output = copy.deepcopy(self._output_dict)

    def reset_script_output(self):
        self.script_output = copy.deepcopy(self._output_dict)

    def reset_transfer_output(self):
        self.transfer_output = copy.deepcopy(self._output_dict)

    def generate_partial_output_of_file_transfer(self):
        self.transfer_output['pid'].append(os.getpid())
        #self.transfer_output['stdin'].append('sftp: ' +remote_source +' to ' +local_dest) 
        self.transfer_output['stdout'].append('')
        self.transfer_output['stderr'].append('')
        #self.transfer_output['status'].append(0)
        self.transfer_output['date'].append(datetime.datetime.now())

    #下载 - 递归同步
    def get(self, remote_source, local_dest, reset_output=True):
        print('\n')
        print('get:', remote_source,' to: ', local_dest)

        if reset_output:
            self.reset_transfer_output()

        # check sftp connection
        if not self._sftp:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)

        # source existence and abspath converting
        _source = self.remotepath_expansion(remote_source)

        # check the existence of dest file directory
        _dest_dir = os.path.dirname(local_dest)
        if not os.path.exists(_dest_dir):
            os.makedirs(_dest_dir)
        _dest = self.localpath_expansion(local_dest)
        _dest   = (self.localpath_expansion(_dest_dir) +'/' +os.path.basename(local_dest)).replace('//', '/')
        print(self._host, 'put:', _source, 'to:', _dest)

        # source type 
        # file
        if self.remote_target_type(_source) == 'file':
            if os.path.exists(_dest) and os.path.isdir(_dest):
                _dest = (_dest + '/' + os.path.basename(_source)).replace('//', '/')
            self.get_file(_source, _dest)
        # dir
        elif self.remote_target_type(_source) == 'directory':
            if local_dest[-1] == '/':
                if remote_source[-1] == '/':
                    # a/ b/
                    self.get_dir(
                        _source,
                        _dest
                    )
            # get as sub directory 
                else:
                    # a b/ --> a/ b/a/
                    _dest = _dest + os.path.basename(_source) +'/'
                    self.get_dir(
                        _source + '/',
                        _dest
                    )
            else:
                # a b == a/ b --> a/ b/
                self.get_dir(
                    (_source + '/').replace('//', '/'),
                    _dest + '/'
                )
        else:
            pass

        # output 
        return self.transfer_output

    def get_file(self, remote_source, local_dest):
        # file a/x b/x
        # check the directory of dest file
        _dest_dir = os.path.dirname(local_dest)
        try:
            os.listdir(_dest_dir)
        except FileNotFoundError:
            os.makedirs(_dest_dir)
        # get the file
        self._sftp.get(remote_source, local_dest)

        self.generate_partial_output_of_file_transfer()
        self.transfer_output['stdin'].append('sftp get: ' +remote_source +' to ' +local_dest) 
        self.transfer_output['status'].append(0)

    def get_dir(self, remote_source, local_dest):
        # a b : a/ b : a/ b/
        # dir content list
        content_list = list(filter(lambda x : len(x)>0,  self._sftp.listdir(remote_source) ))
        if len(content_list)>0:
            # get each file and subdir content 
            remote_source = (remote_source + '/').replace('//', '/')
            local_dest = (local_dest + '/').replace('//', '/')
            list(map(
                lambda x : self.get(remote_source + x, local_dest + x, reset_output=False),
                content_list
            ))
        else:
            # empty folder 
            os.makedirs(local_dest)

        self.generate_partial_output_of_file_transfer()
        self.transfer_output['stdin'].append('sftp get: ' +remote_source +' to ' +local_dest) 
        self.transfer_output['status'].append(0)

    #上传 - 递归同步
    def put(self, local_source, remote_dest, reset_output=True):
        print('\n')
        print('put:', local_source,' to: ', remote_dest)

        if reset_output:
            self.reset_transfer_output()

        if not self._sftp:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)

        # source existence and abspath converting
        _source = self.localpath_expansion(local_source)
        if not os.path.exists(_source):
            raise FileExistsError(_source)

        # check the existence of dest file directory
        _dest_dir = os.path.dirname(remote_dest)
        try:
            # no ready-made mathod for this, use listdir to confirm it
            self._sftp.listdir(_dest_dir)
        except FileNotFoundError:
            self.mkdir_p(_dest_dir)
        _dest = self.remotepath_expansion(remote_dest)
#        _dest   = (self.remotepath_expansion(_dest_dir) +'/' +os.path.basename(remote_dest)).replace('//', '/')
        print(self._host, 'put:', _source, 'to:', _dest)

        # source type
        # file
        if os.path.isfile(_source):
            if remote_dest[-1] == '/':
                _dest = (_dest + '/' + os.path.basename(_source)).replace('//', '/')
            else:
                _type = self.remote_target_type(_dest)
                if _type == 'directory':
                    _dest = (_dest + '/' + os.path.basename(_source)).replace('//', '/')

            self.put_file(_source, _dest)
        # dir
        elif os.path.isdir(_source):
            if remote_dest[-1] == '/':
                if local_source[-1] == '/':
                    # a/ b/
                    self.put_dir(
                        _source,
                        _dest
                    )
            # put as sub directory 
                else:
                    # a b/ --> a/ b/a/
                    _dest = _dest + os.path.basename(_source) + '/'
                    self.put_dir(
                        _source + '/',
                        _dest
                    )
            else:
                # a/ b == a b --> a/ b/
                self.put_dir(
                    (_source + '/').replace('//', '/'),
                    _dest + '/'
                )
        else:
            pass

        # output 
        return self.transfer_output

    def put_file(self, local_source, remote_dest):
        # file a/x b/x
        # check dest file dir
        _dest_dir = os.path.dirname(remote_dest)
        print('file:', local_source, remote_dest)
        try:
            self._sftp.listdir(_dest_dir)
        except FileNotFoundError:
            self.mkdir_p(_dest_dir)

        self._sftp.put(local_source, remote_dest, confirm=True)

        self.generate_partial_output_of_file_transfer()
        self.transfer_output['stdin'].append('sftp put: ' +local_source +' to ' +remote_dest) 
        self.transfer_output['status'].append(0)
        print(self.transfer_output)

    def put_dir(self, local_source, remote_dest):
        print('dir:', local_source, remote_dest)
        self.mkdir_p(remote_dest)

        if os.path.exists(local_source):
            if os.path.isdir(local_source):
                content_list = self.walk_local_dir_content(local_source)
                if content_list:
                    print(content_list)
                    for x in content_list:
                        print(x, remote_dest + x[len(local_source):])
                    list(map(
                        lambda sub_target : self.put(sub_target , remote_dest + sub_target[len(local_source):], reset_output=False),
                        content_list
                    ))
            else:
                raise TypeError("%s is not a directory!" % local_source)
        else:
            raise FileNotFoundError("%s not found." % local_source)

        self.transfer_output['stdin'].append('sftp put: ' +local_source +' to ' +remote_dest) 
        self.transfer_output['status'].append(0)
        print(self.transfer_output)

    # 创建远程目录
    def mkdir_p(self, _dir):
        _out = self.exec_command('test -d %s' % _dir)
        if _out['status'][0] == 0:
            return
        else:
            self.exec_command('mkdir -p %s' % _dir)

    #执行命令
    def run(self, command):
        return self.exec_command(command)

    # input str / list of str 
    # output tuple of hostname, stdout  and err  
    def exec_command(self, command):
        ## clean output
        self.reset_command_output()
        # get connection 
        if self._client is None:
            self._client = paramiko.SSHClient()
            self._client._transport = self._transport
        # check cmd
        if isinstance(command, str):
            self.single_exec(command)
        # not str but Iterable
        elif isinstance(command, Iterable) and False not in map(lambda x : isinstance(x, str), command):
            list(map(self.single_exec, command))
        # the log part
        # temporarily skiped

        # output 
        return self.command_output

    def single_exec(self, cmd, stdin=None):
        #stdin, stdout, stderr = self._client.exec_command(cmd)

        #_command_prefix = 'echo "$$" ; exec '
        #stdin, stdout, stderr = self._client.exec_command(_command_prefix + cmd)

        # paramiko_process 1 (when connected via paramiko)
        # |
        # subprocess 2 (deal with exec_command )
        # |
        # command process 3 (subprocess of 2, exec the command you want to run)
        # |
        # end

        #_command = 'echo "$$" ; { echo $$ ; %s }; echo "$!"'  % cmd
        _command = '{\n%s\n}; \ncmd_return=$? ; \n_trace(){\necho -n "${!:-$$}" && return $cmd_return\n}; \n_trace'  % cmd
        #print("\ncmd:", _command)
        stdin, stdout, stderr = self._client.exec_command(_command)

        #pid = stdout.readline().strip()
        if sys.version_info.major >= 3:
            out = str(stdout.read(), encoding='utf-8')
            err = str(stderr.read(), encoding='utf-8')
        else:
            out = stdout.read()
            err = stderr.read()

        #print("out:", out)
        pid     = out.split('\n')[-1]
        data    = out[:len(pid) *-1]

        # collect info 
        self.command_output['pid'].append(pid)
        self.command_output['stdin'].append(cmd)
        self.command_output['stdout'].append(data)
        self.command_output['stderr'].append(err)
        self.command_output['status'].append(stdout.channel.recv_exit_status())
        #self.command_output['date'].append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.command_output['date'].append(datetime.datetime.now())

    def exec_script(self, script_file):
        print('exec script:', script_file)
        self.reset_script_output()
        if isinstance(script_file, str):
            self.single_copy_run(script_file)
        # not str but Iterable
        elif isinstance(script_file, Iterable) and False not in map(lambda x : isinstance(x, str), script_file):
            list(map(self.single_copy_run, script_file))

        return self.script_output

    def single_copy_run(self, script_file, script_exec_dir='/tmp/'):
        # generate a tmp file name 
        script_exec_dir = (script_exec_dir +'/').replace('//', '/')
        _tmp_file_name = script_exec_dir +random_string(8) +os.path.basename(script_file) 

        # copy file 
        self.put(script_file, _tmp_file_name)

        # run script 
        self.exec_command('chmod +x ' + _tmp_file_name)
        _script_output = self.exec_command(_tmp_file_name)
        #print(_script_output)

        # cleanning
        self.exec_command('rm -f ' + _tmp_file_name)

        # collect info 
        #print(self.script_output)
        for k in _script_output:
            if k == 'host':
                continue
            elif k == 'stdin':
                #print(self.script_output[k])
                self.script_output[k].append(script_file)
            else:
                #print(self.script_output[k])
                self.script_output[k].append(_script_output[k][0])

    def is_alive(self):
        try:
            # temporary solution on linux 
            self.exec_command('/bin/true')
            return True 
        except paramiko.ssh_exception.NoValidConnectionsError:
            return False 

    def close(self):
        if self._transport:
            self._transport.close()
        if self._client:
            self._client.close()
        #print('closed')

    def __str__(self):
        if not self._username:
            u = 'default'
        else:
            u = self._username
        return u + '@' + self.ipaddr + ':' + str(self._port)

class ssh_to:
    def __init__(self, ssh_info):
        self._client_connection = SSHConnection(ssh_info)

    def __enter__(self):
        return self._client_connection

    def __exit__(self, exp_type, exp_value, exp_tracback):
        self._client_connection.close()

if __name__ == "__main__":
    # a host
    h = {
         'host':        ('host1', '192.168.59.252'),
         'port':        None,
         'user':        None,
         'password':    None,
         'timeout':     15,
         'hostkey':     '~/.ssh/id_rsa'
        }

    # output
    # 0: cmd / stdin
    # 1: stdout
    # 2: stderr 
    # 3: return_status
    # 4: return_time 
    # 5: hostname

    with ssh_to(h) as con:
        #print(str(con.fqdn))

        # put a file
    #ok    con.put('~/repository/../a.sh', '~/aa')
    #ok    con.put('~/repository/../a.sh', 'aa')

        # put dir 
    #ok    con.put('~/repository/Cluster_jobs_TUI/log', '~/log')

        # get file 
    #ok    out01 = con.get('~/aa', '~/abc')
    #    print_host_output(out01)

        # get dir 
    #ok    con.get('~/log', '~/logsub/')

        # cmd list squnce 
    #ok    c = ['lsblk', 'blkid', 'ps aux|grep grep']
    #    out0 = con.exec_command(c)
    #    print_host_output(out0)

        # cmd in background
        # if you want a command run in background, please redirect the output!!
        # otherwise, paramiko will keep waiting till the subprocess ends itself!!
        # cause the subprocess shares the same output pipe with the current bash which was called by paramiko
    #ok    out1 = con.exec_command('~/a.sh &>/dev/null &')
    #    print_host_output(out1)

        # single cmd 
    #    out2 = con.exec_command('echo $HOSTNAME')
    #    print_host_output(out2)

        # cmd with error
    #ok    out3 = con.exec_command('ls notexistfile')
    #    print_host_output(out3)

        # run a script 
        sout = con.exec_script('~/a.sh')
        print_host_output(sout)

    # try reconnect 
#ok    con.reconnect()
#    out4 = con.exec_command('ls /')
#    con.close()
#    print("out4 (with reconnect)\n", out4, "\n")

