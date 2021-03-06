#!/usr/bin/env python
# coding=utf-8

import os
import time
import curses
from src import npyscreen

import sqlite3
workflow_db = './db/workflow.db'

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

        self.help1                      = self.add(npyscreen.TitleText, name='任务准备', value='推送与收集文件', editable=False)
        self.nextrely   += 1
        self.nx = self.nextrelx
        self.help1_1                    = self.add(npyscreen.TitleText, name='推送:', editable=False)
        self.ny = self.nextrely
        self.transport_local_source     = self.add(npyscreen.TitleFilename, name='  本地 源文件/目录:', begin_entry_at=22, max_width=45)
        self.help1_2                    = self.add(npyscreen.TitleText, name='收集:', editable=False)
        self.transport_local_target     = self.add(npyscreen.TitleText, name='  远端 源文件/目录:', begin_entry_at=22, max_width=45)

        self.nextrely  = self.ny
        self.nextrelx += 45
        self.transport_remote_target    = self.add(npyscreen.TitleText, name='远端 目标文件/目录:', begin_entry_at=22)
        self.nextrely   += 1
        self.transport_remote_source    = self.add(npyscreen.TitleFilename, name='本地 目标文件/目录:', begin_entry_at=22)

        # task infomation
        self.nextrely   += 1
        self.nextrelx  = self.nx
        self.help2              = self.add(npyscreen.TitleText, name='任务属性:', value='动作与可读管理信息', editable=False)
        self.nextrely   += 1
        self.ny = self.nextrely
        self.help2_1            = self.add(npyscreen.TitleText, name='  可恢复性', begin_entry_at=16, max_width=20, editable=False)
        self.nextrely  = self.ny
        self.nextrelx += 16
        self.rollbackable   = self.add(npyscreen.Checkbox, name='不可回滚', max_width=20, value=True)
        self.nextrelx -= 16

        self.task_name          = self.add(npyscreen.TitleText, name='  任务名称:', max_width=40)
        self.exec_type          = self.add(npyscreen.TitleCombo, name='  动作类型', values=['批量shell命令', '批量运行程序', '批量文件同步', '自定义任务'], value=1, max_width=40)
        self.exec_source_type   = self.add(npyscreen.TitleCombo, name='  文件来源', values=['网络地址', '本地路径'], value=1, max_width=40)
        self.exec_startup_file  = self.add(npyscreen.TitleText, name='  启动文件:', max_width=40)
        self.task_tag       = self.add(npyscreen.TitleText, name='  任务标签:', max_width=40)
        self.task_note      = self.add(npyscreen.TitleText, name='  任务备注:', max_width=40)

        # transportation
        self.nextrely  = self.ny
        self.nextrelx += 45
        self.nextrely   += 2
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
            footer='鼠标/上下键 切换控件',
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
            self.exec_startup_file.value = ''.join(get_file_name(self.exec_file_local.value)[1:])

    def adjust_widgets(self):
        self.check_loadable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def check_task_value(self):
        # format
        self.task_name.value            = self.task_name.value.strip()
        self.shell_command_text.value   = self.shell_command_text.value.strip()
        self.exec_startup_file.value       = self.exec_startup_file.value.strip()

        # name
        if not self.task_name.value or not len(self.task_name.value.strip()):
            npyscreen.notify_confirm('请填写任务名称!', title='信息不全:')
            return False
        # file / cmd
        if not self.exec_startup_file.value or not len(self.exec_startup_file.value.strip()):
            if not self.shell_command_text.value or not len(self.shell_command_text.value.strip()):
                npyscreen.notify_confirm('请指定执行文件名, 或编辑可运行的shell命令!', title='信息不全:')
                return False 

        # confirm task info after check 
        # pass
        return True

    def auto_add_task(self):
        npyscreen.notify('正在检查信息', title='正在添加:')
        time.sleep(0.2)
        if self.check_task_value():
            source_type_dic = ['web_url', 'local_path']
            file_type_dic = ['shell_script', 'ansible_playbook', 'executable_file']
            rollbackable_dic = {True:1, False:0}
            ctime = int(time.time())
            var_list = (
                self.task_name.value,
                self.rollbackable.value,
                self.transport_local_source.value, self.transport_local_target.value,
                self.transport_remote_source.value, self.transport_remote_target.value,
                self.exec_type.value,
                self.task_content_type.value,
                source_type_dic[self.exec_source_type.value],
                self.exec_startup_file.value,
                file_type_dic[self.exec_file_type.value],
                self.shell_command_text.value,
                self.task_tag.value,
                self.task_note.value,
                self.auth_level.value, self.notify_level.value, ctime, ctime
            )
            # add task to db
            conn = sqlite3.connect(workflow_db)
            cur = conn.cursor()
            cur_cmd =   "INSERT INTO task (TASK_NAME, ROLLBACKABLE, " + \
                    "TRANSPORT_LOCAL_SOURDE, TRANSPORT_LOCAL_TARGET, TRANSPORT_REMOTE_SOURCE, TRANSPORT_REMOTE_TARGET, " + \
                    "EXEC_TYPE, TASK_CONTENT_TYPE, EXEC_SOURCE_TYPE, EXEC_STARTUP_FILE, " + \
                    "EXEC_FILE_TYPE, SHELL_COMMAND_TEXT, TASK_TAG, TASK_NOTE, " + \
                    "AUTH_LEVEL, NOTIFY_LEVEL, CTIME, MTIME) " + \
                    "VALUES ( '%s', %s, " % (self.task_name.value, rollbackable_dic[self.rollbackable.value]) + \
                    "'%s', '%s', '%s', '%s', " % (self.transport_local_source.value, self.transport_local_target.value, self.transport_remote_source.value, self.transport_remote_target.value) + \
                    "'%s', '%s', '%s', '%s', " % (self.exec_type.values[self.exec_type.value], self.task_content_type.values[self.task_content_type.value], source_type_dic[self.exec_source_type.value], self.exec_startup_file.value) + \
                    "'%s', '%s', '%s', '%s', " % (file_type_dic[self.exec_file_type.value], self.shell_command_text.value, self.task_tag.value, self.task_note.value) + \
                    "%d, %d, %d, %d ) " % (self.auth_level.value, self.notify_level.value, ctime, ctime)
            cur.execute(cur_cmd)
            conn.commit()
            cur.close()
            npyscreen.notify('添加成功', title='消息')
            time.sleep(0.1)
            self.parentApp.setNextForm('MAIN')


    def on_ok(self):
        self.auto_add_task()

    def on_cancel(self):
        self.parentApp.setNextForm('MAIN')
        self.exit_editing()


#if __name__ == "__main__":
#    print('')
