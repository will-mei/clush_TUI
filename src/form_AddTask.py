#!/usr/bin/env python
# coding=utf-8

import os
import time
import curses
from src import npyscreen


 # ('./abc', 'def', '.h')
def get_file_name(_path_filename):
    (filepath,tmpfilename) = os.path.split(_path_filename)
    (shortname,extension)  = os.path.splitext(tmpfilename)
    return filepath,shortname,extension

#MultiLineEditableBoxed
class TitleEditBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    def set_tx(self, text):
        self.entry_widget.value = text

class AddTaskForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = '添加并配置新的任务:'

        self.help2                      = self.add(npyscreen.TitleText, name='任务准备', value='文件分发与文件收集', editable=False)
        self.nextrely   += 1
        self.ny = self.nextrely
        self.nx = self.nextrelx
        self.transport_local_source     = self.add(npyscreen.TitleFilename, name='本地 源文件/目录:', begin_entry_at=22, max_width=45)
        self.transport_remote_target    = self.add(npyscreen.TitleText, name='远端 目标文件/目录:', begin_entry_at=22, max_width=45)

        self.nextrely  = self.ny
        self.nextrelx += 45
        self.transport_local_target     = self.add(npyscreen.TitleText, name='远端 源文件/目录:', begin_entry_at=22)
        self.transport_remote_source    = self.add(npyscreen.TitleFilename, name='本地 目标文件/目录:', begin_entry_at=22)

        # task infomation
        self.nextrely   += 1
        self.ny = self.nextrely
        self.nextrelx  = self.nx
        self.help1          = self.add(npyscreen.TitleText, name='基本信息', begin_entry_at=16, max_width=20, editable=False)
        self.nextrely  = self.ny
        self.nextrelx += 16
        self.rollbackable   = self.add(npyscreen.Checkbox, name='不可回滚', max_width=20, value=True)
        self.nextrelx -= 16

        self.task_name          = self.add(npyscreen.TitleText, name='任务名称:', max_width=40)
        self.exec_type          = self.add(npyscreen.TitleCombo, name='动作类型', values=['批量shell命令', '批量运行程序', '批量文件同步', '自定义任务'], value=1, max_width=40)
        self.exec_source_type   = self.add(npyscreen.TitleCombo, name='文件来源', values=['网络地址', '本地路径'], value=1, max_width=40)
        self.exec_file_name     = self.add(npyscreen.TitleText, name='启动文件:', max_width=40)
        self.task_tag       = self.add(npyscreen.TitleText, name='任务标签:', max_width=40)
        self.task_note      = self.add(npyscreen.TitleText, name='任务备注:', max_width=40)

        # transportation
        self.nextrely  = self.ny
        self.nextrelx += 45
        self.help3  = self.add(npyscreen.TitleText, name='管理信息', value='执行动作类型与权限', editable=False)
        self.nextrely   += 1
        self.task_content_type  = self.add(npyscreen.TitleCombo, name='内容标签', values=['收集文件', '分发文件', '执行检查', '发起变更', '执行回滚'], value=3)
        self.exec_file_local    = self.add(npyscreen.TitleFilename, name="路径地址:")
        self.exec_file_type     = self.add(npyscreen.TitleCombo, name='文件类型', values=['shell 脚本', 'ansible playbook(添加中)', '其他可执行文件'], value=0)
        self.auth_level         = self.add(npyscreen.TitleCombo, name='权限等级', values=[str(x) for x in range(1,6)], value=0)
        self.notify_level       = self.add(npyscreen.TitleCombo, name='通知等级', values=[str(x) for x in range(1,6)], value=0)
        #self.shell_command_text = self.add(TitleEditBox, name='命令文本编辑区', max_height=20)

        self.nextrely   += 1
        self.nextrelx  = self.nx
        self.shell_command_text = self.add(
            TitleEditBox,
            name='命令文本编辑区',
            #npyscreen.MultiLineEditableBoxed,
            #max_width=40, 
            footer='使用上下键切换到其他控件',
            exit_left=True
        )

        self._conf_refreshed = None
        self._loadable_conf_status = {
            'file_local':self.exec_file_local.value,
        }
        self.add_handlers({
            "^Q":             self.exit_func,
            155:              self.exit_func,
            curses.ascii.BEL: self.exit_func2,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def check_loadable_conf_status(self):
        if self.exec_file_local.value != self._loadable_conf_status['file_local']:
            self._loadable_conf_status['file_local'] = self.exec_file_local.value
            self._conf_refreshed = True

    def when_conf_refreshed(self):
        if self.exec_file_local.value :
            self.exec_file_name.value =get_file_name(self.exec_file_local.value)[1]

    def adjust_widgets(self):
        self.check_loadable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def check_task_value(self):
        # format
        self.task_name.value            = self.task_name.value.strip()
        self.shell_command_text.value   = self.shell_command_text.value.strip()
        self.exec_file_name.value       = self.exec_file_name.value.strip()

        if not self.task_name.value or not len(self.task_name.value.strip()):
            npyscreen.notify_confirm('请填写任务名称!', title='信息不全:')
            return False
        if not self.exec_file_name.value or not len(self.exec_file_name.value.strip()):
            if not self.shell_command_text.value or not len(self.shell_command_text.value.strip()):
                npyscreen.notify_confirm('请指定执行文件名, 或编辑可运行的shell命令!', title='信息不全:')
                return False 

        # confirm task info after check 
        return True

    def auto_add_task(self):
        npyscreen.notify('正在检查信息', title='正在添加:')
        time.sleep(0.2)
        if self.check_task_value():
            # add task to db
            #
            self.parentApp.setNextForm('MAIN')

    def on_ok(self):
        self.auto_add_task()

    def on_cancel(self):
        self.parentApp.setNextForm('MAIN')
        self.exit_editing()


#if __name__ == "__main__":
#    print('')
