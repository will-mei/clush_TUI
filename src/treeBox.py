#!/usr/bin/env python
# coding=utf-8

import time
from src import IPy
from src import npyscreen

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

class TreeData_group(npyscreen.TreeData):
    def __init__(self, *args, **keywords):
        super(TreeData_group, self).__init__(*args, **keywords)
        self.marker = 'group'
        self.ssh_info = {'user':'root', 'port':'22'}
        self.CHILDCLASS = TreeData_host 

class host_group_tree(npyscreen.MLTreeMultiSelect):

    def __init__(self, *args, **keywords):
        super(host_group_tree, self).__init__(*args, **keywords)
        # init a root tree for groups
        self.treedata = npyscreen.TreeData(content='全部组:', selectable=True, ignore_root=False)
        self.values = self.treedata
        self.show_v_lines = False

    # add ip to a new tree 
    def add_grp(self, name='new', nodes=[]):
        name = str(name)
        if isinstance(nodes, str):
            nodes = nodes.split()
        # ip format validation
        _valid_ip = list(filter(isIP, nodes))
        if len(_valid_ip) != len(nodes) or len(_valid_ip) == 0:
            npyscreen.notify_confirm('部分IP地址因格式不合法已经被剔除,\n请检查IP列表格式以确认内容无误!', '添加失败:')
        else:
            new_grp_treedata =  TreeData_group(content=name, selectable=True, ignore_root=False)
            for ip in _valid_ip :
                new_grp_treedata.new_child(content=ip, selectable=True, selected=False)
            # update the group to root 
            self.treedata._children.append(new_grp_treedata)
            npyscreen.notify(name, '添加成功:')
            time.sleep(0.5)

    # give selected
    def give_groups(self):
        return self.get_selected_objects(return_node=False)


# handlers to be added
    # enter : host status

class HostGroupTreeBox(npyscreen.BoxTitle):
    _contained_widget = host_group_tree

    def add_grp(self, *args, **keywords):
        self.entry_widget.add_grp(*args, **keywords)

    def get_selected_objects(self, *args, **keywords):
        return self.entry_widget.get_selected_objects(*args, **keywords)

if __name__ == "__main__":

    ip_list1 = [ '192.168.1.' + str(x)  for x in range(201, 204)]
    ip_list2 = [ '192.168.1.' + str(x)  for x in range(205, 214)]
    ip_list3 = [ '192.168.1.' + str(x)  for x in range(215, 235)]

    class treeForm(npyscreen.FormBaseNewWithMenus):
        def create(self):
            self.t1 = self.add(HostGroupTreeBox, name='host groups', footer='f1', max_width=25)
            self.t1.add_grp(name='group1', nodes=ip_list1)
            self.t1.add_grp(name='group2', nodes=ip_list2)
            self.t1.add_grp(name='group3', nodes=ip_list3)
            #
            self.menu = self.new_menu(name='menus for host groups:')

    class TestApp(npyscreen.NPSApp):
        def main(self):
            f1 = treeForm()
            f1.edit()

    App = TestApp()
    App.run()
