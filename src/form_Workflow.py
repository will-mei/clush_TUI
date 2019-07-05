#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen
from src import box_messages
from src import box_grouptree
from src import box_status

import sqlite3
workflow_db = './db/workflow.db'

#MultiLineEditableBoxed
class TitleEditBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    def set_tx(self, text):
        self.entry_widget.value = text

class WorkflowForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = '管理配置工作流:'

        # window size
        y, x = self.useable_space()

        ny = self.nextrely
        nx = self.nextrelx

        self.GroupTreeBoxObj = self.add(
            box_grouptree.HostGroupTreeBox,
            name="主机组",
            max_width=28,
            scroll_exit=False
        ) #, value=0, relx=1, max_width=x // 5, rely=2,
        self.GroupTreeBoxObj.reload_group_tree()

        self.nextrely = ny
        self.nextrelx = nx + 28
        x_half = int((x - 28) / 2 -5)
        self.task_select_box = self.add(
            box_messages.InfoBox,
            name = "任务列表",
            footer = 'l 搜索已选任务, L 取消搜索高亮, Ctrl + f 从任务管理界面选择',
            values = ['asdfasdfasdf', 'asdfsadfsadf'],
            max_height = 10,
            max_width = x_half,
            #contained_widget_arguments={'maxlen':3},
            #exit_left=True,
            exit_right=True,
            scroll_exit=True,
            #editable=False
        )
        self.nextrely = ny
        self.nextrelx = nx + 28 + x_half
        self.task_status_box = self.add(
            box_status.statusBox,
            name="任务信息",
            footer='运行中主机数: 0',
            values=['选中主机组: 0/0', '选中节点数: 0/0', '在线节点数: 0/0/0'], # 选中在线/所有在线/所有
            max_height=10,
            #contained_widget_arguments={'maxlen':3},
            exit_left=True,
            exit_right=True,
            scroll_exit=True,
            editable=False
        )
        #self.help1                      = self.add(npyscreen.TitleText, name='任务准备', value='文件分发与文件收集', editable=False)
        #self.nextrely   += 1
        #self.ny = self.nextrely
        #self.nx = self.nextrelx
        #self.help2                      = self.add(npyscreen.TitleText, name='推送', value='件收集', editable=False)
        #self.transport_local_source     = self.add(npyscreen.TitleFilename, name='本地 源文件/目录:', begin_entry_at=22, max_width=45)
        #self.transport_remote_target    = self.add(npyscreen.TitleText, name='远端 目标文件/目录:', begin_entry_at=22, max_width=45)

        #self.nextrely  = self.ny
        #self.nextrelx += 45
        #self.transport_local_target     = self.add(npyscreen.TitleText, name='远端 源文件/目录:', begin_entry_at=22)
        #self.transport_remote_source    = self.add(npyscreen.TitleFilename, name='本地 目标文件/目录:', begin_entry_at=22)

        ## task infomation
        #self.nextrely   += 1
        #self.ny = self.nextrely
        #self.nextrelx  = self.nx
        #self.help1          = self.add(npyscreen.TitleText, name='基本信息', begin_entry_at=16, max_width=20, editable=False)
        #self.nextrely  = self.ny
        #self.nextrelx += 16
        #self.rollbackable   = self.add(npyscreen.Checkbox, name='不可回滚', max_width=20, value=True)
        #self.nextrelx -= 16

        #self.task_name          = self.add(npyscreen.TitleText, name='任务名称:', max_width=40)
        #self.exec_type          = self.add(npyscreen.TitleCombo, name='动作类型', values=['批量shell命令', '批量运行程序', '批量文件同步', '自定义任务'], value=1, max_width=40)
        #self.exec_source_type   = self.add(npyscreen.TitleCombo, name='文件来源', values=['网络地址', '本地路径'], value=1, max_width=40)
        #self.exec_startup_file  = self.add(npyscreen.TitleText, name='启动文件:', max_width=40)
        #self.task_tag       = self.add(npyscreen.TitleText, name='任务标签:', max_width=40)
        #self.task_note      = self.add(npyscreen.TitleText, name='任务备注:', max_width=40)

        ## transportation
        #self.nextrely  = self.ny
        #self.nextrelx += 45
        #self.help3  = self.add(npyscreen.TitleText, name='管理信息', value='执行动作类型与权限', editable=False)
        #self.nextrely   += 1
        #self.task_content_type  = self.add(npyscreen.TitleCombo, name='内容标签', values=['收集文件', '分发文件', '执行检查', '发起变更', '执行回滚'], value=3)
        #self.exec_file_local    = self.add(npyscreen.TitleFilename, name="路径地址:")
        #self.exec_file_type     = self.add(npyscreen.TitleCombo, name='文件类型', values=['shell 脚本', 'ansible playbook(添加中)', '其他可执行文件'], value=0)
        #self.auth_level         = self.add(npyscreen.TitleCombo, name='权限等级', values=[str(x) for x in range(1,6)], value=0)
        #self.notify_level       = self.add(npyscreen.TitleCombo, name='通知等级', values=[str(x) for x in range(1,6)], value=0)
        ##self.shell_command_text = self.add(TitleEditBox, name='命令文本编辑区', max_height=20)

        #self.nextrely   += 1
        #self.nextrelx  = self.nx
        #self.shell_command_text = self.add(
        #    TitleEditBox,
        #    name='命令文本编辑区',
        #    #npyscreen.MultiLineEditableBoxed,
        #    #max_width=40, 
        #    footer='鼠标/上下键 切换控件',
        #    exit_left=True
        #)

    #    self._conf_refreshed = None
    #    self._loadable_conf_status = {
    #        'file_local':self.exec_file_local.value,
    #    }
        self.add_handlers({
            "^Q":               self.exit_func,
            155:                self.exit_func,
            curses.ascii.BEL:   self.exit_func2,
            "^F":               self.search_task,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def search_task(self, _input):
        self.parentApp.switchForm('SearchTaskForm')

    #def check_loadable_conf_status(self):
    #    if self.exec_file_local.value != self._loadable_conf_status['file_local']:
    #        self._loadable_conf_status['file_local'] = self.exec_file_local.value
    #        self._conf_refreshed = True

    #def when_conf_refreshed(self):
    #    if self.exec_file_local.value :
    #        self.exec_startup_file.value = ''.join(get_file_name(self.exec_file_local.value)[1:])

    #def adjust_widgets(self):
    #    self.check_loadable_conf_status()
    #    if self._conf_refreshed:
    #        self.when_conf_refreshed()
    #        self._conf_refreshed = None

    #def check_task_value(self):
    #    # format
    #    self.task_name.value            = self.task_name.value.strip()
    #    self.shell_command_text.value   = self.shell_command_text.value.strip()
    #    self.exec_startup_file.value       = self.exec_startup_file.value.strip()

    #    # name
    #    if not self.task_name.value or not len(self.task_name.value.strip()):
    #        npyscreen.notify_confirm('请填写任务名称!', title='信息不全:')
    #        return False
    #    # file / cmd
    #    if not self.exec_startup_file.value or not len(self.exec_startup_file.value.strip()):
    #        if not self.shell_command_text.value or not len(self.shell_command_text.value.strip()):
    #            npyscreen.notify_confirm('请指定执行文件名, 或编辑可运行的shell命令!', title='信息不全:')
    #            return False 

    #    # confirm task info after check 
    #    # pass
    #    return True

    #def auto_add_task(self):
    #    npyscreen.notify('正在检查信息', title='正在添加:')
    #    time.sleep(0.2)
    #    if self.check_task_value():
    #        source_type_dic = ['web_url', 'local_path']
    #        file_type_dic = ['shell_script', 'ansible_playbook', 'executable_file']
    #        rollbackable_dic = {True:1, False:0}
    #        ctime = int(time.time())
    #        var_list = (
    #            self.task_name.value,
    #            self.rollbackable.value,
    #            self.transport_local_source.value, self.transport_local_target.value,
    #            self.transport_remote_source.value, self.transport_remote_target.value,
    #            self.exec_type.value,
    #            self.task_content_type.value,
    #            source_type_dic[self.exec_source_type.value],
    #            self.exec_startup_file.value,
    #            file_type_dic[self.exec_file_type.value],
    #            self.shell_command_text.value,
    #            self.task_tag.value,
    #            self.task_note.value,
    #            self.auth_level.value, self.notify_level.value, ctime, ctime
    #        )
    #        # add task to db
    #        conn = sqlite3.connect(workflow_db)
    #        cur = conn.cursor()
    #        cur_cmd =   "INSERT INTO task (TASK_NAME, ROLLBACKABLE, " + \
    #                "TRANSPORT_LOCAL_SOURDE, TRANSPORT_LOCAL_TARGET, TRANSPORT_REMOTE_SOURCE, TRANSPORT_REMOTE_TARGET, " + \
    #                "EXEC_TYPE, TASK_CONTENT_TYPE, EXEC_SOURCE_TYPE, EXEC_STARTUP_FILE, " + \
    #                "EXEC_FILE_TYPE, SHELL_COMMAND_TEXT, TASK_TAG, TASK_NOTE, " + \
    #                "AUTH_LEVEL, NOTIFY_LEVEL, CTIME, MTIME) " + \
    #                "VALUES ( '%s', %s, " % (self.task_name.value, rollbackable_dic[self.rollbackable.value]) + \
    #                "'%s', '%s', '%s', '%s', " % (self.transport_local_source.value, self.transport_local_target.value, self.transport_remote_source.value, self.transport_remote_target.value) + \
    #                "'%s', '%s', '%s', '%s', " % (self.exec_type.value, self.task_content_type.value, source_type_dic[self.exec_source_type.value], self.exec_startup_file.value) + \
    #                "'%s', '%s', '%s', '%s', " % (file_type_dic[self.exec_file_type.value], self.shell_command_text.value, self.task_tag.value, self.task_note.value) + \
    #                "%d, %d, %d, %d ) " % (self.auth_level.value, self.notify_level.value, ctime, ctime)
    #        cur.execute(cur_cmd)
    #        conn.commit()
    #        cur.close()
    #        npyscreen.notify('添加成功', title='消息')
    #        time.sleep(0.1)
    #        self.parentApp.setNextForm('MAIN')


    def on_ok(self):
        #self.auto_add_task()
        pass

    def on_cancel(self):
        self.parentApp.setNextForm('MAIN')
        self.exit_editing()


#if __name__ == "__main__":
#    print('')
