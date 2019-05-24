#!/usr/bin/env python
# coding=utf-8

import asyncio 

from pprint import pprint
from pssh.clients.native import ParallelSSHClient

hosts = ['192.168.59.11']
client = ParallelSSHClient(hosts)

output = client.run_command('uname')
for host, host_output in output.items():
    for line in host_output.stdout:
        print(line)

