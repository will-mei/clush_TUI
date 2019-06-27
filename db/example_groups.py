#!/usr/bin/env python
# coding=utf-8
import sqlite3
conn = sqlite3.connect('terminal.db')
cursor = conn.cursor()

try:
    cursor.execute("INSERT INTO groups (GROUP_NAME, SSH_PORT, SSH_TIMEOUT, SSH_HOSTKEY) VALUES ('EXAMPLE', 22, 30, '~/.ssh/id_rsa')")
except:
    pass

#cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME, BOARD_SN, TAG) VALUES ('test01', 'EXAMPLE', 'L1HF4BV014C', 'example host')")

for n in range(1,10):
    hostname = 'test' + str(n)
    groupname = 'EXAMPLE'
    sn = 'L1HF4BV014' + str(n)
    tag = 'example host'
    cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME, BOARD_SN, TAG) VALUES ('%s', '%s', '%s', '%s')" % (hostname, groupname, sn, tag))

conn.commit()
cursor.close()
