#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen
from src import box_messages
from src import box_grouptree

import sqlite3
terminal_db = './db/terminal.db'

#MultiLineEditableBoxed
class TitleEditBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    def set_tx(self, text):
        self.entry_widget.value = text

class HostGroupForm(npyscreen.ActionFormV2):

    group_list  = []
    group_editable  = False
    current_group   = None

    edit_status = 'select' # 'insert delete update'

    CANCEL_BUTTON_BR_OFFSET = (2, 24)
    OK_BUTTON_TEXT = '完成  '
    CANCEL_BUTTON_TEXT = '返回  '

    def create(self):
        self.name = '管理配置主机组:'

        # window size
        y, x = self.useable_space()
        ny = self.nextrely
        nx = self.nextrelx

        # host group tree
        self.GroupTreeBox   = self.add(
            box_grouptree.HostGroupTreeBox,
            name="主机组",
            max_width=28,
            scroll_exit=False
        ) #, value=0, relx=1, max_width=x // 5, rely=2,
        self.GroupTreeBox.reload_group_tree()

        # select box ; back to topline
        self.nextrely = ny
        self.nextrelx = nx + 28
        self.group_select_box    = self.add(
            box_messages.InfoBox,
            name = "主机组 列表",
            footer = 'l 搜索主机组, L 取消搜索高亮, <Ctrls + x> / <空格> 选中条目, Ctrl + r 刷新列表',
            values = self.group_list,
            max_height = 8,
            exit_left=True,
            exit_right=True,
            scroll_exit=True,
        )

        # group connection preset
        self.ny2 = self.nextrely
        self.nextrelx += 2
        self.add_mode = self.add(
            npyscreen.TitleMultiSelect,
            name='添加选项',
            begin_entry_at=1,
            max_height=4,
            field_width=24,
            value=[0,1,],
            values=[
                "加载主机地址列表",
                "指定 ssh连接私钥",
                "网络连接  预检测",
            ],
            exit_right=True,
            scroll_exit=True,
            # add a callback for this widget when its value changed
            value_changed_callback  =   self.add_mode_value_changed_callback
        )

        # recover y     vertically
        # move x + 45   horizontally
        self.nextrely = self.ny2
        self.nextrely += 1
        self.nextrelx += 25
        self.ip_list_file           = self.add(npyscreen.TitleFilenameCombo, name="grp_conf:", begin_entry_at=12, max_width=40, exit_left=True)
        self.ssh_private_key_file   = self.add(npyscreen.TitleFilenameCombo, name="Identity:", begin_entry_at=12, max_width=40, exit_left=True)
        # pre check 
        self.ssh_connect_timeout    = self.add(npyscreen.TitleSlider, name="超时时间:", exit_left=True, field_width=35, lowest=10, out_of=90, step=10, max_width=40)
        self.ssh_connect_timeout.value = 10
        self.ssh_connect_timeout.hidden = True

        # recover x
        self.nextrelx -= 25
        self.ny = self.nextrely + 1
        self.grp_name = self.add(npyscreen.TitleText, name='* 组名称  :', begin_entry_at=14, max_width=40)
        self.grp_port = self.add(npyscreen.TitleText, name='* ssh 端口:', begin_entry_at=14, max_width=40)

        self.nextrely = self.ny
        self.nextrelx += 45
        self.ssh_user = self.add(npyscreen.TitleText, name='  ssh 用户:', begin_entry_at=14, max_width=40)
        self.ssh_pswd = self.add(npyscreen.TitleText, name='  ssh 口令:', begin_entry_at=14, max_width=40)
        self.nextrelx -= 45

        # record y
        self.ny = self.nextrely
        self.host_list_tmp  = self.add(
            TitleEditBox,
            name='手动编辑区:',
            footer='使用 ^r 格式化换行, ^e 预览结果',
            max_width=85,
        )
        self.host_list_tmp.set_tx('example-hostname1 example-hostname2 example-hostname3')

        self.nextrely  = self.ny2 +1
        self.nextrelx = -35
        self.host_list   = self.add(
            npyscreen.MultiLineEditableBoxed,
            max_width=32,
            name='主机地址预览:',
            values=['0.0.0.0'],
            footer='空格:修改, i:插入, o:新行'
        )

        self.add_handlers({
            "^Q":               self.exit_func,
            155:                self.exit_func,
            curses.ascii.BEL:   self.exit_func2,
            "^F":               self.search_task,
        })

    # callback for add_mode widget 
    def add_mode_value_changed_callback(self, widget=None):
        if widget:
            _target_widget = widget
        else:
            return 
        # hidden grp_conf 
        _target_value = _target_widget.value 
        if 0 in _target_value :
            self.ip_list_file.hidden = False
        else:
            self.ip_list_file.hidden = True
        if 1 in _target_value :
            self.ssh_private_key_file.hidden = False
        else:
            self.ssh_private_key_file.hidden = True
        # hidden conTimeout 
        if 2 in _target_value :
            self.ssh_connect_timeout.hidden = False
        else:
            self.ssh_connect_timeout.hidden = True

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def search_task(self, _input):
        self.parentApp.switchForm('SearchTaskForm')


    def on_ok(self):
        #self.auto_add_task()
        pass

    def on_cancel(self):
        self.parentApp.setNextForm('MAIN')
        self.exit_editing()


#if __name__ == "__main__":
#    print('')
