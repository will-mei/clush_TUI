#!/usr/bin/env python
# coding=utf-8
import socket
import time
import threading 

import json
import hashlib




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

    def parse_msg(self, _stream_bytes):
        # check sequnce

        # parse msg
        print('\n')
        print(b'parse json pkg:' + _stream_bytes)
        try:
            _data   = json.loads(_stream_bytes)
            _sum    = _data['sum']
            _msg    = _data['msg']
            _tid    = _data['tid']
            _time_stamp = _tid.split('_')[0]
            _time   = time.mktime(time.strptime(_time_stamp, "%Y/%m/%d-%H:%M:%S")) 
            print(
                'dict_data:', _data,
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
        if hashlib.sha256(self._prefix + _msg.encode('utf-8') + str(_tid).encode('utf-8') ).hexdigest() == _sum:
            # reply 
            reply   = ('task %s  recived and confirmed' % _tid ).encode('utf-8')
            print('reply:', reply)
        else:
            reply   = ('task %s hash failed, task invalid' % _tid).encode('utf-8')
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
        while True:
            _stream_bytes = sock.recv(self._len_max)
            time.sleep(0)
            
            if not _stream_bytes or _stream_bytes.decode('utf-8') == 'exit':
                break
            #sock.send(('Hello,%s!' % _stream_bytes.decode('utf-8')).encode('utf-8'))
            sock.send(
                self.parse_msg(_stream_bytes)
            )
        sock.close()
        print('Connection from %s:%s closed.' % addr)

    def run(self):
        while True :
            sock, addr = self._socket.accept()
            task = threading.Thread(target=self.thread_tcplink, args=(sock, addr))
            task.start()

if __name__ == "__main__":
    server_info = {
        'session_key'   :b'test_user_id',
        'server_ip'     :'192.168.59.252',
        'server_port'   :9999,
        'msg_trans_unit':8192,
        'connection_max':512,
        'socket_timeout':5,
        'msg_timeout':3,
    }
    s   = api_server(server_info)
    s.run()


