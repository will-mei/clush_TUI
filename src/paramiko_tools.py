#!/usr/bin/env python3
# coding=utf-8

import os
import sys 
import paramiko
from src import bash_cli
#import bash_cli
import  warnings
warnings.filterwarnings('ignore')

class SSHConnection(object):
    def __init__(self, ssh_info):
        self._host = ssh_info['host']
        self._port = ssh_info['port']
        self._username = ssh_info['user']
        self._password = ssh_info['password']
        self._timeout  = ssh_info['timeout']
        self._key_filename = ssh_info['hostkey'].replace('~', os.path.expanduser('~'))
        self._transport = None
        self._sftp = None
        self._client = None
        self._connect()  # 建立连接

    def _connect(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
                             self._host,
                             username=self._username,
                             password=self._password,
                             key_filename=self._key_filename
                            )
        self._transport = self._client._transport


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
            file_list = list(filter(lambda x : len(x) > 0, bash_cli.ez_cmd('find ' + localpath + '*').split('\n')))
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

    #执行命令
    def exec_command(self, command):
        if self._client is None:
            self._client = paramiko.SSHClient()
            self._client._transport = self._transport
        stdin, stdout, stderr = self._client.exec_command(command)
        if sys.version_info.major >= 3:
            data = str(stdout.read(), encoding='utf-8')
            err = str(stderr.read(), encoding='utf-8')
        else:
            data = stdout.read()
            err = stderr.read()
        if len(data) > 0:
#            print(data.strip())  #打印正确结果
            return data
        elif len(err) > 0:
#            print(err.strip())   #输出错误结果
            return err

    def close(self):
        if self._transport:
            self._transport.close()
        if self._client:
            self._client.close()

if __name__ == "__main__":
    d = {'host':'192.168.59.11',
         'port':22,
         'user':None,
         'password':None,
         'timeout':15,
         'hostkey':'~/.ssh/id_rsa'
        }
    con_test = SSHConnection(d)
    tx = con_test.exec_command('lsblk')
    print(tx)
    #con_test.put('../tmp/a/', 'aa')
    #con_test.put('bash_cli.py', 'b')
    con_test.exec_command('ls -hl')
    con_test.exec_command('ls abcde')
    #con_test.get('aa/', './aaxx')


