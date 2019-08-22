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

def random_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def print_output(output):
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

def localpath_expansion(localpath):
    # 家目录替换
    if localpath[:2] == '~/':
        localpath = os.environ['HOME'] + localpath[1:]
    # 相对路劲转换
    localpath = os.path.abspath(localpath)

    # 注意,输出结果结尾无'/'后缀
    #print("local abspath:", localpath)
    return localpath

class SSHConnection(object):
    def __init__(self, ssh_info):
        self._ssh_info      = ssh_info
        self.update_ssh_info(ssh_info)
        # ssh socket
        self._transport     = None
        self._sftp          = None
        self._client        = None
        self._connect()  # 建立连接

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

    def remotepath_expansion(self, remotepath):
        # dir
        _target_type = self.remote_target_type(remotepath)
        if _target_type == 'directory':
            _out = self.exec_command('echo $(cd %s && pwd)' % remotepath)
            #print_output(_out)
            if _out['status'][0] == 0:
                remotepath  = _out['stdout'][0].strip()
        else:
            # file
            _out = self.exec_command('echo $(cd $(dirname %s) && pwd)' % remotepath)
            if _out['status'][0] == 0:
                remotepath  = _out['stdout'][0].strip() + '/' + remotepath.split('/')[-1]

        #print("remote abspath:", remotepath)
        return {'abspath':remotepath, 'type':_target_type}

    def remote_target_type(self, remotepath):
        _out = self.exec_command('file -b %s' % remotepath)
        if _out['status'][0] == 0:
            if _out['stdout'][0].strip() == 'directory':
                return 'directory'
            else:
                return 'file'
        else:
            raise EnvironmentError("cannot stat target type: %s" % remotepath)

    def reset_cmd_output(self):
        # clean output
        self.output = {}
        self.output['pid']      = []
        self.output['stdin']    = []
        self.output['stdout']   = []
        self.output['stderr']   = []
        self.output['status']   = []
        self.output['date']     = []
        self.output['host']     = self._host

    def reset_transfer_output(self):
        # clean output
        self.transfer_output = {}
        self.transfer_output['pid']      = []
        self.transfer_output['stdin']    = []
        self.transfer_output['stdout']   = []
        self.transfer_output['stderr']   = []
        self.transfer_output['status']   = []
        self.transfer_output['date']     = []
        self.transfer_output['host']     = self._host

    def generate_partial_output_of_file_transfer(self):
        self.transfer_output['pid'].append(os.getpid())
        #self.transfer_output['stdin'].append('sftp: ' +remote_source +' to ' +local_dest) 
        self.transfer_output['stdout'].append('')
        self.transfer_output['stderr'].append('')
        #self.transfer_output['status'].append(0)
        self.transfer_output['date'].append(datetime.datetime.now())


    #下载 - 递归同步
    def get(self, remote_source, local_dest):
        #print(self._host, 'get:', remote_source,' to: ', local_dest)

        self.reset_transfer_output()

        # check sftp connection
        if not self._sftp:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)

        # abspath converting
        _source = self.remotepath_expansion(remote_source)
        _dest   = localpath_expansion(local_dest)

        # file
        if _source['type'] == 'file':
            self.get_file(_source['abspath'], _dest)
        # dir
        elif _source['type'] == 'directory':
            # get dir under local dir as a sub directory 
            if local_dest[-1] == '/':
                if remote_source[-1] == '/':
                    # a/ b/
                    self.get_dir(
                        _source['abspath'] + '/',
                        _dest + '/'
                    )
                else:
                    # a b/ : a/ b/a/
                    _dest = _dest + '/' + _source['abspath'].split('/')[-1]
                    self.get_dir(
                        _source['abspath'] + '/',
                        _dest + '/'
                    )
            else:
                # dir content
                # a b : a/ b : a/ b/
                self.get_dir(
                    _source['abspath'] + '/',
                    _dest + '/'
                )

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
                lambda x : self.get(remote_source + x, local_dest + x),
                content_list
            ))
        else:
            # empty folder 
            os.makedirs(local_dest)

        self.generate_partial_output_of_file_transfer()
        self.transfer_output['stdin'].append('sftp get: ' +remote_source +' to ' +local_dest) 
        self.transfer_output['status'].append(0)

    #上传 - 递归同步
    def put(self, local_source, remote_dest):
        #print(self._host, 'put:', local_source,' to: ', remote_dest)

        self.reset_transfer_output()

        if not self._sftp:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)

        _source = localpath_expansion(local_source)
        _dest   = self.remotepath_expansion(remote_dest)

        # file
        if os.path.isfile(_source):
            self.put_file(_source, _dest['abspath'])
        # dir
        else:
            if remote_dest[-1] == '/':
                if local_source[-1] == '/':
                    # a/ b/
                    self.put_dir(
                        _source + '/',
                        _dest['abspath'] + '/'
                    )
                else:
                    # a b/ : a/ b/a/
                    _dest = _dest['abspath'] + '/' + _source.split('/')[-1]
                    self.put_dir(
                        _source + '/',
                        _dest + '/'
                    )
            else:
                # a/ b : a b : a/ b/
                self.put_dir(
                    _source + '/',
                    _dest['abspath'] + '/'
                )

        # output 
        return self.transfer_output


    def put_file(self, local_source, remote_dest):
        # file a/x b/x
        # check dest file dir
        _dest_dir = os.path.dirname(remote_dest)
        try:
            self._sftp.listdir(_dest_dir)
        except FileNotFoundError:
            self.mkdir_p(_dest_dir)

        self._sftp.put(local_source, remote_dest, confirm=True)

        self.generate_partial_output_of_file_transfer()
        self.transfer_output['stdin'].append('sftp put: ' +local_source +' to ' +remote_dest) 
        self.transfer_output['status'].append(0)

    def put_dir(self, local_source, remote_dest):
        self.mkdir_p(remote_dest)

        if lib_cli_bash.cmd_ok('ls %s/' % local_source):
            content_list = list(filter(
                lambda x : len(x) > 0,
                lib_cli_bash.ez_cmd('find ' +local_source +'*').split('\n')
            ))
            list(map(
                lambda x : self.put(x , remote_dest + x.lstrip(local_source)),
                content_list
            ))
        else:
            raise FileExistsError("%s is not a directory!" % local_source)

        self.transfer_output['stdin'].append('sftp put: ' +local_source +' to ' +remote_dest) 
        self.transfer_output['status'].append(0)

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
        #self.output = {}
        #self.output['pid']      = []
        #self.output['stdin']    = []
        #self.output['stdout']   = []
        #self.output['stderr']   = []
        #self.output['status']   = []
        #self.output['date']     = []
        #self.output['host']     = self._host
        self.reset_cmd_output()
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
        return self.output

    def single_cmd(self, cmd, stdin=None):
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
        self.output['pid'].append(pid)
        self.output['stdin'].append(cmd)
        self.output['stdout'].append(data)
        self.output['stderr'].append(err)
        self.output['status'].append(stdout.channel.recv_exit_status())
        #self.output['date'].append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.output['date'].append(datetime.datetime.now())

    def exec_script(self, script_file):
        return self.copy_run(script_file)

    def copy_run(self, script_file):
        # generate a tmp file name 
        _tmp_file_name = '/tmp/'+ random_string(8) + os.path.basename(script_file) 
        # copy file 
        self.put(script_file, _tmp_file_name)
        # run script 
        self.exec_command('chmod +x ' + _tmp_file_name)
        _script_output = self.exec_command(_tmp_file_name)
        _script_output['stdin'] = script_file
        # cleanning
        self.exec_command('rm -f ' + _tmp_file_name)
        # return 
        return _script_output

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
    # a command list
    c = ['lsblk', 'blkid', 'ps aux|grep grep']

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
        out01 = con.get('~/aa', '~/abc')
        print_output(out01)

        # get dir 
    #ok    con.get('~/log', '~/logsub/')

        # cmd list 
    #ok    out0 = con.exec_command(c)
    #    print_output(out0)

        # cmd in background
        # if you want a command run in background, please redirect the output!!
        # otherwise, paramiko will keep waiting till the subprocess ends itself!!
        # cause the subprocess shares the same output pipe with the current bash which was called by paramiko
    #ok    out1 = con.exec_command('~/a.sh &>/dev/null &')
    #    print_output(out1)

        # single cmd 
    #ok    out2 = con.exec_command('echo $HOSTNAME')
    #    print_output(out2)

        # cmd with error
        out3 = con.exec_command('ls notexistfile')
        print_output(out3)

        # run a script 
    #ok    sout = con.exec_script('~/a.sh')
    #    print_output(sout)

    # try reconnect 
#ok    con.reconnect()
#    out4 = con.exec_command('ls /')
#    con.close()
#    print("out4 (with reconnect)\n", out4, "\n")

