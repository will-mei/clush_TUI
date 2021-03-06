#!/usr/bin/env python
# coding=utf-8

import time
from src import IPy
from src import npyscreen

import sqlite3
terminal_db = './db/terminal.db'

def isIP(ip):
    try:
        IPy.IP(ip)
        return True
    except:
        return False

class TreeData_host(npyscreen.TreeData):
    def __init__(self, *args, **keywords):
        super(TreeData_host, self).__init__(*args, **keywords)
        self.marker = 'host'

    def get_ssh_info(self):
        _host_ssh_info = self.get_parent().ssh_info
        _host_ssh_info['host'] = self.get_content()
        return _host_ssh_info 

class TreeData_group(npyscreen.TreeData):
    def __init__(self, *args, **keywords):
        super(TreeData_group, self).__init__(*args, **keywords)
        self.marker = 'group'
        # ssh info dict, to be changed later 
        self.ssh_info = {}
        self.CHILDCLASS = TreeData_host 

class host_group_tree(npyscreen.MLTreeMultiSelect):

    def __init__(self, *args, **keywords):
        super(host_group_tree, self).__init__(*args, **keywords)
        # init a root tree for groups
        #self.treedata = npyscreen.TreeData(content='全部组:', selectable=True, ignore_root=False)
        self.treedata = TreeData_group(content='全部主机组:', selectable=True, ignore_root=False)
        self.values = self.treedata
        self.show_v_lines = False

    # add ip to a new tree 
    def add_grp(self, name='new', nodes=[], ssh_info={}):
        name = str(name)
        if isinstance(nodes, str):
            nodes = nodes.split()
        ## ip format validation
        #_valid_ip = list(filter(isIP, nodes))
        #if len(_valid_ip) != len(nodes) or len(_valid_ip) == 0:
        #    npyscreen.notify_confirm('部分IP地址因格式不合法已经被剔除,\n请检查IP列表格式以确认内容无误!', '添加失败:')
        #else:
        #    new_grp_treedata =  TreeData_group(content=name, selectable=True, ignore_root=False)
        #    new_grp_treedata.ssh_info = ssh_info
        #    for ip in _valid_ip :
        #        new_grp_treedata.new_child(content=ip, selectable=True, selected=False)
        #    # update the group to root 
        #    self.treedata._children.append(new_grp_treedata)
        #    npyscreen.notify(name, '添加成功:')
        #    time.sleep(0.5)
        # use hostname instead of ip 
        new_grp_treedata =  TreeData_group(content=name, selectable=True, ignore_root=False)
        new_grp_treedata.ssh_info = ssh_info
        for hostname in nodes :
            new_grp_treedata.new_child(content=hostname, selectable=True, selected=False)
        # update the group to root 
        self.treedata._children.append(new_grp_treedata)
        npyscreen.notify(name, '加载成功:')
        time.sleep(0.1)

    def purge_all_grp(self):
        self.treedata = TreeData_group(content='全部主机组:', selectable=True, ignore_root=False)
        self.values = self.treedata


# handlers to be added
    # enter : host status

class HostGroupTreeBox(npyscreen.BoxTitle):
    _contained_widget = host_group_tree

    def add_grp(self, *args, **keywords):
        self.entry_widget.add_grp(*args, **keywords)

    def get_selected_objects(self, node_type=None, *args, **keywords):
        if node_type: 
            return filter(lambda x : x.marker == node_type, self.entry_widget.get_selected_objects(*args, **keywords))
        else:
            return self.entry_widget.get_selected_objects(*args, **keywords)

    def purge_all_grp(self):
        self.entry_widget.purge_all_grp()

    def reload_group_tree(self):
        # get selected nodes info
        npyscreen.notify('正在读取主机组...', title='消息')
        time.sleep(0.15)
        conn = sqlite3.connect(terminal_db)
        cursorObj = conn.cursor()
        self.purge_all_grp()
        for g in list(cursorObj.execute("select * from groups")):
            _group_name = g[1]
            _user = g[3]
            _port = g[4]
            _tout = g[5]
            _pwd  = g[6]
            _hkey = g[7]
            _grp_ssh_info = {
                'user':     _user,
                'port':     _port,
                'timeout':  _tout,
                'password': _pwd,
                'hostkey':  _hkey
            }
            _hostname_list = map(
                lambda x: x[0],
                cursorObj.execute("select HOSTNAME from HOST WHERE GROUP_NAME = '%s' " % _group_name)
            )
            self.add_grp(name=_group_name, nodes=_hostname_list, ssh_info=_grp_ssh_info)
        cursorObj.close()

if __name__ == "__main__":

    ip_list1 = [ '192.168.1.' + str(x)  for x in range(201, 204)]
    ip_list2 = [ '192.168.1.' + str(x)  for x in range(205, 214)]
    ip_list3 = [ '192.168.1.' + str(x)  for x in range(215, 235)]

    ssh_info1 = {
                 'port'    :22,
                 'user'    :None,
                 'password':None,
                 'timeout' :10,
                 'hostkey' :None
                }
    class treeForm(npyscreen.FormBaseNewWithMenus):
        def create(self):
            self.t1 = self.add(HostGroupTreeBox, name='host groups', footer='f1', max_width=25)
            self.t1.add_grp(name='group1', nodes=ip_list1, ssh_info=ssh_info1)
            self.t1.add_grp(name='group2', nodes=ip_list2, ssh_info=ssh_info1)
            self.t1.add_grp(name='group3', nodes=ip_list3, ssh_info=ssh_info1)
            #
            self.menu = self.new_menu(name='menus for host groups:')

    class TestApp(npyscreen.NPSApp):
        def main(self):
            f1 = treeForm()
            f1.edit()

    App = TestApp()
    App.run()
