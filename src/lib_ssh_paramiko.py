#!/usr/bin/env python3
# coding=utf-8

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

class SSHConnection(object):
    def __init__(self, ssh_info):
        self._ssh_info      = ssh_info
        self.update_ssh_info()
        # ssh socket
        self._transport     = None
        self._sftp          = None
        self._client        = None
        self._init_con_fn   = self._init_fn()
        self._connect()  # 建立连接

    def update_ssh_info(self):
        self.fqdn           = self._ssh_info['host'][0]
        self.ipaddr         = self._ssh_info['host'][1]
        self._host          = self.ipaddr 
        self._port          = self._ssh_info['port']
        self._username      = self._ssh_info['user']
        self._password      = self._ssh_info['password']
        self._timeout       = self._ssh_info['timeout']
        self._key_filename  = self._ssh_info['hostkey'].replace('~', os.path.expanduser('~'))

    # closure with connection info stored 
    def _init_fn(self):
        h = self._host
        u = username=self._username
        p = password=self._password
        k = key_filename=self._key_filename
        _client = paramiko.SSHClient()
        _client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        def _client_connect_fn():
            try:
                _client.connect(h,
                                username = u,
                                password = p,
                                key_filename = k,
                                )
            except:
                pass
            return _client
        return _client_connect_fn

    def _connect(self, mode='init'):
        if not self._client:
            self._client = self._init_con_fn()
        elif mode == 'reconnect':
            self._client = self._init_con_fn()
        self._transport = self._client._transport
        self._transport.setName(self._host)

    # connect with the ssh info which were used at the very begining of its creation
    def reconnect(self):
        if self._client:
            self._connect(mode='reconnect')
        else:
            self._connect()

    # connect with current ssh info
    def update_connection(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._client.connect(self._host,
                                username=self._username,
                                password=self._password,
                                key_filename=self._key_filename
                                )
        except:
            self._client = None
            pass

    #def update_status(status):
    #    if      status == 'reconnect':
    #        self._connect(mode='reconnect')
    #    elif    status == 'update':
    #        self.update_connection()
    #    elif    status == 'close':
    #        self.close()

    def get_sync(self, remotepath, localpath):
#        print('get: ', remotepath, 'to: ', localpath)
        # check remotepath
        try:
            # dir a/ b/
            self._sftp.listdir(remotepath)
            localpath = (localpath + '/').replace('//', '/')
            self.get_dir(remotepath, localpath)
        except:
            # file a/x b/x
            try:
                self._sftp.lstat(remotepath)
                os.makedirs(os.path.dirname(localpath))
                self._sftp.get(remotepath, localpath)
            # not exist 
            except:
#                print(remotepath, 'does not exist.')
                pass

    def get_dir(self, remotepath, localpath):
        localpath = (localpath + '/').replace('//', '/')
        # check remote dir 
        try:
            file_list = list(filter(lambda x : len(x)>0,  self._sftp.listdir(remotepath) ))
            if len(file_list)>0:
                remotepath = (remotepath + '/').replace('//', '/')
                list(map(lambda x : self.get_sync(remotepath + x, localpath + x) , file_list))
            else:
                # empty folder 
                try:
                    os.makedirs(localpath)
                except:
                    pass 
        except:
            # not dir or not exist 
            self.get_sync(remotepath, localpath)

    #下载
    def get(self, remotepath, localpath):
        if self._sftp is None:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        if remotepath[-1] == '/':
            self.get_dir(remotepath, localpath)
        else:
            self.get_sync(remotepath, localpath)


    def mkdir_p(self, remotepath):
        try:
            try:
                self._sftp.listdir(remotepath)
            except:
                self._sftp.mkdir(remotepath)
        except:
            self.mkdir_p(os.path.dirname(remotepath))

    def put_sync(self, localpath, remotepath):
#        print('put:', localpath,' to: ', remotepath)
        # a/ b/
        if os.path.isdir(localpath):
            self.mkdir_p(remotepath)
        # a b/ 
        elif os.path.isfile(localpath):
            if remotepath[-1] == '/':
                self.mkdir_p(remotepath)
                self._sftp.put(localpath, remotepath+localpath.split('/')[-1], confirm=True)
            # a b
            else:
                self._sftp.put(localpath, remotepath, confirm=True)

    def put_dir(self, localpath, remotepath):
        remotepath = (remotepath + '/').replace('//', '/')
        if os.path.isdir(localpath):
            file_list = list(filter(lambda x : len(x) > 0, lib_cli_bash.ez_cmd('find ' + localpath + '*').split('\n')))
            #print('dir info: ', file_list, remotepath)
            #list(map(lambda x : print(x , remotepath + x.lstrip(localpath) ), file_list))
            list(map(lambda x : self.put_sync(x , remotepath + x.lstrip(localpath) ), file_list))
        else:
            #print('please use "/" as the end of pathname')
            #raise NotADirectoryError(localpath)
            self.put_sync(localpath, remotepath)

    #上传
    def put(self, localpath, remotepath):
        if self._sftp is None:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        # check local dir 
        if localpath[-1] == '/':
            self.put_dir(localpath, remotepath)
        else:
            self.put_sync(localpath, remotepath)

    def single_cmd(self, cmd, stdin=None):
        stdin, stdout, stderr = self._client.exec_command(cmd)

        if sys.version_info.major >= 3:
            data = str(stdout.read(), encoding='utf-8')
            err = str(stderr.read(), encoding='utf-8')
        else:
            data = stdout.read()
            err = stderr.read()
        #
        self.output_cmd.append(cmd)
        self.output_data.append(data)
        self.output_err.append(err)
        self.output_ret.append(stdout.channel.recv_exit_status())

    #执行命令
    def run(self,command):
        return self.exec_command(command)
    # input str / list of str 
    # output tuple of hostname, stdout  and err  
    def exec_command(self, command):
        # clean output
        self.output_cmd  = []
        self.output_data = []
        self.output_err  = []
        self.output_ret  = []
        # get connection 
        if self._client is None:
            self._client = paramiko.SSHClient()
            self._client._transport = self._transport
        # check cmd
        if isinstance(command, str):
            self.single_cmd(command)
        elif isinstance(command, list) and False not in map(lambda x : isinstance(x, str), command):
            list(map(self.single_cmd, command))

        # the log part
        # temporarily skiped

        # output 
        return (self.output_cmd,
                self.output_data,
                self.output_err,
                self.output_ret,
                datetime.datetime.now(),
                self._host
               )

    #def pipe_run(self, script_file):
    #    pass 
    def copy_run(self, script_file):
        _tmp_file_name = '' 
        self.put(script_file, _tmp_file_name)
        self.exec_command('chmod +x ' + _tmp_file_name)
        _tmp_out_tuple = self.exec_command(_tmp_file_name)
        self.exec_command('rm -f ' + _tmp_file_name)
        return tuple( [script_file] + list(_tmp_out_tuple[1:]) )

    def exec_script(self, script_file):
        return self.copy_run(script_file)

    def is_alive(self):
        try:
            # temporary solution on linux 
            self.exec_command('/bin/true')
            return True 
        except:
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
    h = {
         'host':        ('host1', '192.168.59.11'),
         'port':        22,
         'user':        None,
         'password':    None,
         'timeout':     15,
         'hostkey':     '~/.ssh/id_rsa'
        }
    c = ['lsblk', 'blkid', 'ps aux|grep grep']
#    con_test = SSHConnection(d)
#    tx = con_test.exec_command('lsblk')
#    print(tx)
#    #con_test.put('../tmp/a/', 'aa')
#    #con_test.put('lib_cli_bash.py', 'b')
#    con_test.exec_command('ls -hl')
#    con_test.exec_command('ls abcde')
#    #con_test.get('aa/', './aaxx')
#    con_test.close()
    with ssh_to(h) as con:
        out1 = con.exec_command(c)
        out2 = con.exec_command('echo $HOSTNAME')
        out3 = con.exec_command('ls notexistfile')
    # output
    # 0: cmd / stdin
    # 1: stdout
    # 2: stderr 
    # 3: return_status
    # 4: return_time 
    # 5: hostname
    list(map(print, out1[1]))
    print(out1)
    print(out2)
    print(out3)
    # try reconnect 
    print(str(con.fqdn))
    con.reconnect()
    out4 = con.exec_command('ls aa')
    con.close()
    print(out4)


