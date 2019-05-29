#!/usr/bin/env python
# coding=utf-8
import socket
import time
import threading 

import json
import hashlib

# create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('192.168.59.252', 9999))

s.listen(5)
print("waiting for connection ..")



def get_reply(_stream_bytes):
    # check sequnce
    print('\n')
    
    # parse msg
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

    # hash check
    _prefix = b'test_user_id'
    _timeout = 5
    _time_now = time.time()
    if hashlib.sha256(
        _prefix 
        + _msg.encode('utf-8')
        + str(_tid).encode('utf-8')
    ).hexdigest() == _sum:
        # gen reply 
        reply   = ('%s task recive and confirmed' % _tid ).encode('utf-8')
        print('reply confirm msg:', reply, type(reply))
    else:
        reply   = ('%s hash failed, task info is invalid' % _tid).encode('utf-8')
        print('hash failed:', _msg, 'is coming from an invalid source')

    # time stamp check
    if _time_now - _time > _timeout:
        print('message confirmed but it is out of date', _stream_bytes)
        reply = b'info status: out of date, confirmed'
        return reply
    # tid existence check (sqlite)

    print('\n')
    return reply


def thread_tcplink(sock, addr):
    # welcome
    print("Accept new connection from %s:%s..." % addr)
    sock.send(b'Welcom!')

    while True:
        _stream_bytes = sock.recv(1024)
        time.sleep(1)
        
        if not _stream_bytes or _stream_bytes.decode('utf-8') == 'exit':
            break
        #sock.send(('Hello,%s!' % _stream_bytes.decode('utf-8')).encode('utf-8'))

        sock.send(
            get_reply(_stream_bytes)
        )

    sock.close()
    print('Connection from %s:%s closed.' % addr)

while True :
    sock, addr = s.accept()
    task = threading.Thread(target=thread_tcplink, args=(sock, addr))
    task.start()


