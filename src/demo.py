#!/usr/bin/env python
# coding=utf-8

import npyscreen

class PreSetForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = 'test settings'
        #form and widgets
        self.output_dir = self.add(npyscreen.TitleText, begin_entry_at=25, name="输入测试作业输出目录:")
        self.excel_date = self.add(npyscreen.TitleDateCombo,  begin_entry_at=25, name="选取excel报告标题日期:")
        self.ssh_config = self.add(npyscreen.TitleFilenameCombo,  begin_entry_at=25, name="调整用户ssh连接配置:")
        #self.host_group = self.add(npyscreen.TitleFilenameCombo,  begin_entry_at=25, name="加载主机IP列表文件:")
        self.nextrely += 1
        self.ny = self.nextrely
        #self.nx = self.nextrelx
        self.test_mode = self.add(npyscreen.TitleSelectOne, max_height=3, field_width=30, value = [2,], name="测试模式", exit_right=True,
                   values = ["单盘测试", "并行测试", "对比测试"], scroll_exit=True)
        self.nextrelx += 40
        self.nextrely = self.ny
        # adjust layout
        self.test_opt = self.add(npyscreen.TitleMultiSelect, max_height=3, field_width=35, value=[0,1,], name="测试选项", exit_left=True,
                   values = ["忽略失联主机", "启用sudo模式", "忽略ping检查"], scroll_exit=True)
        # recover layout
        self.nextrelx += -40
        self.nextrely += 1
        self.test_disk = self.add(npyscreen.TitleSelectOne, max_height=3, field_width=30, value = [0,], name="磁盘类型",
                   values = ["裸盘测试", "RBD测试"], scroll_exit=True)
        self.ping_interval = self.add(npyscreen.TitleSlider, field_width=75, begin_entry_at=18, lowest=10, out_of=180, step=10, name="连接状态刷新时间")
        self.ping_interval.value = 30
        self.update_interval = self.add(npyscreen.TitleSlider, field_width=75, begin_entry_at=18, lowest=10, out_of=180, step=10, name="测试状态刷新时间")
        self.update_interval.value = 30
        self.test_note = self.add(npyscreen.MultiLineEdit,
                   value = """你可以在此输入本次测试的备注信息, \n多行文本可以使用 ^R 格式化到一行.\n """,
                   max_height=5, rely=-12)
    def while_editing(self, z):
        if 2 in self.test_opt.value:
            self.ping_interval.hidden = True
        else:
            self.ping_interval.hidden = False

    def afterEditing(self):
        self.parentApp.setNextForm('MAIN')


ip_list1 = [ '192.168.1.' + str(x)  for x in range(201, 204)]
ip_list2 = [ '192.168.1.' + str(x)  for x in range(205, 214)]
ip_list3 = [ '192.168.1.' + str(x)  for x in range(215, 235)]

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
        self.treedata = npyscreen.TreeData(content='all groups:', selectable=True, ignore_root=False)
        self.values = self.treedata
    def add_grp(self, name='new', nodes=''):
        # add ip to a new tree 
        new_grp_treedata =  TreeData_group(content=name, selectable=True, ignore_root=False)
        for ip in nodes :
             new_grp_treedata.new_child(content=ip, selectable=True, selected=False)
        # update the group to root 
        self.treedata._children.append(new_grp_treedata)
    # give selected
    def give_selected_nodes(self):
        return self.get_selected_objects(return_node=False,ignore_root=True)


# handlers to be added
    # enter : host status

class GroupTreeForm(npyscreen.FormBaseNewWithMenus):
    def create(self):
        self.name = 'host groups'
        self.min_c = 25
        self.DEFAULT_X_OFFSET = 0
        self.BLANK_COLUMNS_RIGHT = 0

        # add tree, a subclass of MLTreeMultiSelect 
        self.group_tree = self.add(host_group_tree, max_height=-2)
        self.group_tree.add_grp(name='group1', nodes=ip_list1)
        self.group_tree.add_grp(name='group2', nodes=ip_list2)
        self.group_tree.add_grp(name='group3', nodes=ip_list3)
        self.menu = self.new_menu(name='menus for host groups:')

        # add an entry for add groups
        self.n1 = self.add(npyscreen.FixedText, begin_entry_at=0, value = '展开按钮: ], >, l')
        self.n2 = self.add(npyscreen.FixedText, begin_entry_at=0, value = '折叠按钮: [, <, h')

    def afterEditing(self):
        self.parentApp.setNextForm('PreSetForm')


class InfoForm(npyscreen.Form):
    pass
class InputForm(npyscreen.Form):
    pass
class MainForm(npyscreen.FormBaseNew):

    def create(self):
        # events
        # load conf
        # window size
        y, x = self.useable_space()
        # ui form
        #

class ClusterJobsApp(npyscreen.NPSAppManaged):
    #npyscreen.ThemeManager.default_colors['LABEL'] = 'YELLOW_BLACK' 
    def onStart(self):
        self.MainForm = self.addForm("PreSetForm", PreSetForm)
        #self.GroupTreeFrom = self.addForm("GroupTree", GroupTreeForm, columns=25)
        self.GroupTreeFrom = self.addForm("MAIN", GroupTreeForm, columns=25)

if __name__ == "__main__":
    App = ClusterJobsApp()
    App.run()
