#!/usr/bin/env python
# coding=utf-8
import socket
import time
import threading 

import json
import hashlib

#import logging 
#logging.basicConfig(
#    #filename= '/var/log/messages',
#    #level   = logging.INFO,
#    level   = logging.DEBUG,
#    format  = '%(asctime)s %(name)s %(process)d - %(thread)d:%(threadName)s - %(levelname)s - %(pathname)s %(funcName)s line: %(lineno)d - %(message)s',
#    datefmt = '%Y/%m/%d %I:%M:%S %p'
#)

#return_code = {
#    000:'success',
#    001:'failed',
#    002:'hash fail',
#    003:'data incomplete',
#    004:'data incorrect',
#    005:'msg format error',
#    006:'msg hash failed',
#    007:'msg out of date',
#    008:'broken pipe'
#    009:'server failure',
#    010:'client unreachable',
#}


class api_server():
    def __init__(self, con_info):
        self._prefix        = con_info['session_key']
        self._server_ip     = con_info['server_ip']
        self._server_port   = con_info['server_port']
        self._timeout       = con_info['socket_timeout']
        self._mtimeout      = con_info['msg_timeout']
        self._len_max       = con_info['msg_trans_unit']
        self._con_max       = con_info['connection_max']
        # create a socket
        self._socket        = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(
            (self._server_ip, 
             self._server_port)
        )
        self._socket.listen(self._con_max)
        print("waiting for connection ..")

    def perform_task(self, _data):
        pass 

    def _check_msg(self, _stream_bytes):
        print('\n')
        print(b'check json pkg:' + _stream_bytes)
        try:
            _data   = json.loads(_stream_bytes)
            _stat   = True
            print('check ok')
        except:
            _data   = None
            _stat   = False 
            print('check fail')
        return (_data, _stat)

    def parse_msg(self, _data):
        # parse msg
        try:
            _sum    = _data['sum']
            _msg    = _data['msg']
            _tid    = _data['tid']
            _time_stamp = _tid.split('_')[0]
            _time   = time.mktime(time.strptime(_time_stamp, "%Y/%m/%d-%H:%M:%S")) 
            print(
                '\nsum:', _sum,
                '\nmsg:', _msg,
                '\ntid:', _tid,
                '\ntime:', _time_stamp,
            )
        except:
            print('fail to parse:', _stream_bytes)
            reply   = b'info status: wrong format, droped'
            return reply

        # task_id existence status check (sqlite)

        # hash validation
        _sum_confirm = hashlib.sha256(self._prefix + _msg.encode('utf-8') + str(_tid).encode('utf-8') ).hexdigest()
        if _sum == _sum:
            # reply 
            reply   = ('task %s  recived and confirmed' % _tid ).encode('utf-8')
            print('reply:', reply)
            # exec task 
            self.perform_task(_data)
        else:
            reply   = ('task %s hash failed, task invalid' % _tid).encode('utf-8')
            print(
                '\nsum:', _sum,
                '\nsum confirm:', _sum_confirm,
            )
            print('reply:', reply)

        # msg timeout
        _time_now = time.time()
        if _time_now - _time > self._mtimeout:
            reply   = ('task %s recived and abandent, cause the timestamp is out of date' % _tid).encode('utf-8')
            print('reply:', reply)
            return reply
        print('\n')

        return reply

    def thread_tcplink(self, sock, addr):
        # welcome
        print("Accept new connection from %s:%s..." % addr)

        #sock.send(b'Welcom!')
        _slice_dict = {}
        _slice_max  = hex(0)
        while True:
            _stream_bytes = sock.recv(self._len_max)
            time.sleep(0)
            
            # end and exit 
            if not _stream_bytes or _stream_bytes.decode('utf-8') == 'exit':
                break
            #sock.send(('Hello,%s!' % _stream_bytes.decode('utf-8')).encode('utf-8'))

            # confirmed stop 
            if _stream_bytes == b'f'*16:
                print('\nconfirm stop recive', '\nseq_max', _slice_max, '\n')
                # check every slice of data pkg 
                i = 0 
                _data_pkg = b''
                # check and splicing sequnces
                while i <= int(_slice_max.lstrip(b'f'), 16):
                    print('check slice num %s' % i)
                    try:
                        _data_pkg += _slice_dict[i]
                    except:
                        print('slice number %s is missing, Retransmission error!' % i)
                        _data_pkg = None
                        break
                    i = i+1
                # check msg and confirm
                _task_data_info = self._check_msg(_data_pkg)
                _task_data_pkg  = _task_data_info[0]
                _task_data_stat = _task_data_info[1]
                if _task_data_stat:
                    print('complete msg:', _task_data_pkg)
                    reply = self.parse_msg(_task_data_pkg)
                    sock.send(reply)
                else:
                    sock.send(b'data incorrect,  transportation failed')
            # continue recive the rest 
            else:
                _seq    = _stream_bytes[:8]
                _max    = _stream_bytes[8:16]
                _sum    = _stream_bytes[16:80]
                _slice  = _stream_bytes[80:].rstrip()
                _sum_confirm  = hashlib.sha256(_seq + _slice).hexdigest().encode('utf-8')
                print(
                    '\nseq:', _seq,
                    '\nmax:', _max,
                    '\nsum:', _sum,
                    '\nsum confirm:', _sum_confirm,
                    '\nslice',_slice,
                )
                # check individual data package
                if _sum_confirm == _sum :
                    _slice_max = _max
                    index = int(_seq.lstrip(b'f'), 16)
                    if not index in _slice_dict:
                        print('\nadd data num %s' % index)
                        _slice_dict[index] = _slice
                        print(_slice_dict)
                    # confirm
                    sock.send(_sum)
                else:
                    # check fail
                    sock.send(b'01') 
        # end 
        sock.close()
        print('Connection from %s:%s closed.' % addr)

    def run_forever(self):
        i = 0
        while i<2 :
            sock, addr = self._socket.accept()
            task = threading.Thread(target=self.thread_tcplink, args=(sock, addr))
            task.start()
            i = i+1
            print('socket number:', i)
            time.sleep(0.5)

if __name__ == "__main__":
    server_info = {
        'session_key'   :b'test_user_id',
        'server_ip'     :'192.168.59.252',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout':15,
    }
    s   = api_server(server_info)
    s.run_forever()


