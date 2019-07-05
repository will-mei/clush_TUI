#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen
from src import box_messages

import sqlite3
workflow_db = './db/workflow.db'

#MultiLineEditableBoxed
class TitleEditBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    def set_tx(self, text):
        self.entry_widget.value = text

class SearchTaskForm(npyscreen.ActionFormV2):
    task_list   = []
    task_editable   = False
    current_task    = None

    edit_status = 'select' # 'insert delete update'

    CANCEL_BUTTON_BR_OFFSET = (2, 24)
    OK_BUTTON_TEXT = '完成  '
    CANCEL_BUTTON_TEXT = '取消选择  '

    def create(self):
        self.name = '管理配置工作流:'

        # window size
        #y, x = self.useable_space()

        self.task_select_box = self.add(
            box_messages.InfoBox,
            name = "任务列表",
            footer = 'l 搜索任务, L 取消搜索高亮, <Ctrls + x> / <空格> 选定任务, Ctrl + r 刷新列表',
            values = self.task_list,
            max_height = 8,
            exit_right=True,
            scroll_exit=True,
        )

        self.dump_task_list()

        self.help0      = self.add(npyscreen.TitleText, name='任务编辑:', value='Ctrl + a 添加, Ctrl + d 删除, Ctrl + u 更新, Ctrl + s 提交编辑结果', editable=False)
        self.nextrely   += 1
        self.task_id                    = self.add(npyscreen.TitleText, name='任务ID号:', value='-', max_width=50, editable=False)
        self.nextrely   += 1
        self.ny1 = self.nextrely
        self.nextrely   += 1
        self.help1                      = self.add(npyscreen.TitleText, name='任务准备', value='文件分发与文件收集', max_width=50, editable=False)
        self.nextrely   += 1
        #self.ny = self.nextrely
        #self.nx = self.nextrelx
        self.help1_1                    = self.add(npyscreen.TitleText, name=' 推送', value='分发', begin_entry_at=8, max_width=50, editable=False)
        self.transport_local_source     = self.add(npyscreen.TitleFilename, name='  本地 源文件/目录:', begin_entry_at=22, max_width=50, editable=False)
        self.transport_remote_target    = self.add(npyscreen.TitleText, name='  远端 目标文件/目录:', begin_entry_at=24, max_width=50, editable=False)

        #self.nextrely  = self.ny
        #self.nextrelx += 45
        self.help1_2                    = self.add(npyscreen.TitleText, name=' 拉取', value='收集', begin_entry_at=8, max_width=50, editable=False)
        self.transport_local_target     = self.add(npyscreen.TitleText, name='  远端 源文件/目录:', begin_entry_at=22, max_width=50, editable=False)
        self.transport_remote_source    = self.add(npyscreen.TitleFilename, name='  本地 目标文件/目录:', begin_entry_at=24, max_width=50, editable=False)

        ## task infomation
        self.nextrely   += 1
        #self.nextrelx  = self.nx
        self.help2      = self.add(npyscreen.TitleText, name='管理信息', value='执行动作类型与权限', max_width=50, editable=False)
        self.nextrely   += 1

        self.ny = self.nextrely
        self.help1          = self.add(npyscreen.TitleText, name=' 基本信息', begin_entry_at=14, max_width=20, editable=False)
        self.nextrely   = self.ny
        self.nextrelx   += 14
        self.rollbackable   = self.add(npyscreen.Checkbox, name='可回滚', max_width=20, value=True, editable=False)
        self.nextrelx   -= 14

        # 名为
        self.task_name          = self.add(npyscreen.TitleText, name='  任务名称:', begin_entry_at=14, max_width=50, editable=False)
        # 的
        self.task_type          = self.add(npyscreen.TitleCombo, name='  动作类型', values=['批量shell命令', '批量运行程序', '批量文件同步', '自定义'], value=3, begin_entry_at=14, max_width=50, editable=False)
        # 任务, 完成
        self.task_description   = self.add(npyscreen.TitleCombo, name='  任务描述', values=['收集文件', '分发文件', '同步收发', '检索信息', '变更修改', '回滚变更', '多重调整'], value=3, begin_entry_at=14, max_width=50, editable=False)
        # 动作

        self.exec_source_type   = self.add(npyscreen.TitleCombo, name='  文件来源', values=['网络地址', '本地文件'], value=1, begin_entry_at=14, max_width=50, editable=False)
        self.exec_source_addr   = self.add(npyscreen.TitleFilename, name="  完整路径:", begin_entry_at=14, max_width=50, editable=False)
        self.exec_startup_file  = self.add(npyscreen.TitleText, name='  文件名称:', begin_entry_at=14, max_width=50, editable=False)
        self.exec_file_type     = self.add(npyscreen.TitleCombo, name='  文件类型', values=['shell 脚本', 'ansible playbook(添加中)', '其他可执行文件'], value=0, begin_entry_at=14, max_width=50, editable=False)

        self.auth_level         = self.add(npyscreen.TitleCombo, name='  权限等级', values=[str(x) for x in range(1,6)], value=0, begin_entry_at=14, max_width=50, editable=False)
        self.notify_level       = self.add(npyscreen.TitleCombo, name='  通知等级', values=[str(x) for x in range(1,6)], value=0, begin_entry_at=14, max_width=50, editable=False)
        self.task_tag           = self.add(npyscreen.TitleText, name='  任务标签:', begin_entry_at=14, max_width=50, editable=False)
        self.task_note          = self.add(npyscreen.TitleText, name='  任务备注:', begin_entry_at=14, max_width=50, editable=False)
        self.ctime              = self.add(npyscreen.TitleText, name='  任务创建时间:', begin_entry_at=18, max_width=50, editable=False)
        self.mtime              = self.add(npyscreen.TitleText, name='  最后修改时间:', begin_entry_at=18, max_width=50, editable=False)

        # transportation
        self.nextrely  = self.ny1
        self.nextrelx += 55
        #self.nextrely   += 1
        #self.shell_command_text = self.add(TitleEditBox, name='命令文本编辑区', max_height=20)

        #self.nextrely   += 1
        #self.nextrelx  = self.nx
        self.shell_command_text = self.add(
            TitleEditBox,
            name='命令文本预览',
            #npyscreen.MultiLineEditableBoxed,
            #max_width=50, 
            footer='只读',
            exit_left=True,
            editable=False
        )

        # status of selected_task, task_content_type
        self._conf_refreshed = None
        self._loadable_conf_status = {
            'selected_task':self.task_select_box.value,
        }

        # key binding settings
        self.add_handlers({
            "^Q":               self.exit_func,
            155:                self.exit_func,
            curses.ascii.BEL:   self.abort_func,
            "^P":               self.print_selected_task_index, # just for debug
            "^R":               self.refresh_task_list,
            "^A":               self.add_new_task,
            "^D":               self.delete_selected_task,
            "^U":               self.update_selected_task,
            "^S":               self.commit_modified_task,
            "^W":               self.give_up_task_editing,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def abort_func(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def refresh_task_list(self, _input):
        self.dump_task_list()
        self.display()

    def dump_task_list(self):
        conn  = sqlite3.connect(workflow_db)
        cur = conn.cursor()
        self.task_list = list(cur.execute("SELECT * FROM task ;"))
        cur.close()
        self.task_select_box.values = self.task_list

    # check focused item 
    def check_alterable_conf_status(self):
        if self.edit_status == 'select':
            # show detail of selected 
            if self.task_select_box.value != self._loadable_conf_status['selected_task']:
                self._loadable_conf_status['selected_task'] = self.task_select_box.value
                self._conf_refreshed = True
        if self.edit_status == 'insert':
            pass
        if self.edit_status == 'update':
            pass

    def when_conf_refreshed(self):
        if self.edit_status == 'select':
            self.load_task_preview()

        if self.edit_status == 'insert':
            pass
        if self.edit_status == 'update':
            pass

    def adjust_widgets(self):
        self.check_alterable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def print_selected_task_index(self, _input):
        npyscreen.notify_confirm(str(self.task_select_box.value), title='current value')

    def load_task_preview(self):
        if self.current_task:
            current_task = self.current_task
        elif isinstance(self.task_select_box.value, int):
            current_task = self.task_list[self.task_select_box.value]
        else:
            return
        #npyscreen.notify_confirm(str(type(current_task)), 'type')
        #tuple 

        source_type_dic = {'web_url':0, 'local_path':1}
        file_type_dic = {'shell_script':0, 'ansible_playbook':1, 'executable_file':2}

        self.task_id.value = str(current_task[0])
        self.task_name.value = str(current_task[1])
        if current_task[2]:
            self.rollbackable.value = True
        else:
            self.rollbackable.value = False

        self.transport_local_source.value   = str(current_task[3])
        self.transport_local_target.value   = str(current_task[4])
        self.transport_remote_source.value  = str(current_task[5])
        self.transport_remote_target.value  = str(current_task[6])

        self.task_type.value            = self.task_type.values.index(current_task[7])
        self.task_description.value     = self.task_description.values.index(current_task[8])

        self.exec_source_type.value     = source_type_dic[current_task[9]]
        self.exec_source_addr.value     = str(current_task[10])
        self.exec_startup_file.value    = str(current_task[11])
        self.exec_file_type.value       = file_type_dic[current_task[12]]

        self.shell_command_text.value   = str(current_task[13])
        self.task_tag.value             = str(current_task[14])
        self.task_note.value            = str(current_task[15])

        self.auth_level.value           = int(current_task[16])
        self.notify_level.value         = int(current_task[17])
        self.ctime.value                = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(current_task[18])))
        self.mtime.value                = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(current_task[19])))
        self.display()

    def enable_edit_task(self):
        self.task_editable  = True
        #npyscreen.notify_confirm(str(self._widgets__), title='editable')
        self.shell_command_text.name    = '命令文本编辑'
        self.shell_command_text.footer  = 'Ctrl + w 可以取消编辑'
        self.fresh_edit_privilege()

    def disable_edit_task(self):
        self.task_editable  = False
        self.shell_command_text.name    = '命令文本预览'
        self.shell_command_text.footer  = '只读'
        self.fresh_edit_privilege()

    def fresh_edit_privilege(self):

        e = self.task_editable

        self.task_name.editable     = e
        self.rollbackable.editable  = e

        self.transport_local_source.editable    = e
        self.transport_local_target.editable    = e
        self.transport_remote_source.editable   = e
        self.transport_remote_target.editable   = e

        self.task_type.editable             = e
        self.task_description.editable      = e

        self.exec_source_type.editable      = e
        self.exec_source_addr.editable      = e
        self.exec_startup_file.editable     = e
        self.exec_file_type.editable        = e

        self.shell_command_text.editable    = e

        self.task_tag.editable              = e
        self.task_note.editable             = e

        self.auth_level.editable            = e
        self.notify_level.editable          = e

        #self.ctime.editable                = e
        #self.mtime.editable                = e


    def add_new_task(self, _input):
        if self.edit_status != 'select':
            npyscreen.notify_confirm('请先提交当前进行编辑的任务', title='编辑冲突')
            return
        self.edit_status = 'insert'
        # new focused task
        self.initialize_empty_task()
        self.enable_edit_task()
        #self.display()

    # leave editing mode 
    def give_up_task_editing(self, _input):
        if self.edit_status == 'select':
            npyscreen.notify_confirm('当前没有正在编辑的任务.', title='未发起编辑')
            return
        if isinstance(self.task_select_box.value, int):
            self.refresh_task_list(0)
        else:
            self.initialize_empty_task()
        self.disable_edit_task()
        self.edit_status = 'select'
        self.display()

    def initialize_empty_task(self):
        # refresh the task preview
        _t = int(time.time())
        _empty_task = ('-', '', 0, '', '', '', '', '自定义', '检索信息', 'local_path', '', '', 'executable_file', '', '', '', 0, 0, _t, _t)
        self.current_task = _empty_task
        self.load_task_preview()
        self.current_task = None

    def delete_selected_task(self, _input):
        # some certain task were selected
        if isinstance(self.task_select_box.value, int):
            _id = self.task_list[self.task_select_box.value][0] 
            _name = self.task_list[self.task_select_box.value][1]
            # comfirm
            _str = '确定要删除 ID: %d 号, 名为: %s 的任务吗?' % (_id, _name)
            if npyscreen.notify_yes_no(_str, title='确认删除'):
                # delete task from db 
                cur_cmd = "DELETE FROM task WHERE ID = %d ;" % _id
                conn = sqlite3.connect(workflow_db)
                cur = conn.cursor()
                cur.execute(cur_cmd)
                conn.commit()
                cur.close()
            self.refresh_task_list(0)
        else:
            npyscreen.notify_confirm('请先选中要删除的任务才能进行删除操作.', title='没有任务可以删除')

    def update_selected_task(self, _input):
        if self.edit_status != 'select':
            npyscreen.notify_confirm('请先提交当前进行编辑的任务', title='编辑冲突')
        # task selected 
        if isinstance(self.task_select_box.value, int):
            self.edit_status = 'update'
            #self.refresh_task_list(0)
            self.enable_edit_task()
        else:
            npyscreen.notify_confirm('请先选中要更新的任务才能进行更新操作.', title='没有任务可以更新')

    def commit_modified_task(self, _input):
        if self.edit_status == 'select':
            npyscreen.notify_confirm('请先进入任务添加或者修改状态再进行内容提交.', title='没有内容可以提交')
            return
        if self.check_task_value():
            if self.edit_status == 'insert':
                self.auto_add_task()
            elif self.edit_status == 'update':
                self.auto_update_task() 
            self.disable_edit_task()
            self.edit_status    = 'select'
            self.current_task   = None
            self.refresh_task_list(0)


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
        time.sleep(0.1)
        if self.check_task_value():
            source_type_dic = ['web_url', 'local_path']
            file_type_dic = ['shell_script', 'ansible_playbook', 'executable_file']
            rollbackable_dic = {True:1, False:0}
            ctime = int(time.time())
            # add task to db
            conn = sqlite3.connect(workflow_db)
            cur = conn.cursor()
            cur_cmd =   "INSERT INTO task (TASK_NAME, ROLLBACKABLE, " + \
                    "TRANSPORT_LOCAL_SOURDE, TRANSPORT_LOCAL_TARGET, TRANSPORT_REMOTE_SOURCE, TRANSPORT_REMOTE_TARGET, " + \
                    "TASK_TYPE, TASK_DESCRIPTION, " + \
                    "EXEC_SOURCE_TYPE, EXEC_SOURCE_ADDR, EXEC_STARTUP_FILE, EXEC_FILE_TYPE, " + \
                    "SHELL_COMMAND_TEXT, TASK_TAG, TASK_NOTE, " + \
                    "AUTH_LEVEL, NOTIFY_LEVEL, CTIME, MTIME) " + \
                    "VALUES ( '%s', %s, "       % (self.task_name.value, rollbackable_dic[self.rollbackable.value]) + \
                    "'%s', '%s', '%s', '%s', "  % (self.transport_local_source.value, self.transport_local_target.value, self.transport_remote_source.value, self.transport_remote_target.value) + \
                    "'%s', '%s', "          % (self.task_type.values[self.task_type.value], self.task_description.values[self.task_description.value]) + \
                    "'%s', '%s', '%s', '%s', "  % (source_type_dic[self.exec_source_type.value], self.exec_source_addr.value, self.exec_startup_file.value, file_type_dic[self.exec_file_type.value]) + \
                    "'%s', '%s', '%s', "    % (self.shell_command_text.value, self.task_tag.value, self.task_note.value) + \
                    "%d, %d, %d, %d ) "     % (self.auth_level.value, self.notify_level.value, ctime, ctime)
            try:
                cur.execute(cur_cmd)
            except:
                raise TypeError(cur_cmd)
            conn.commit()
            cur.close()
            npyscreen.notify('添加成功', title='消息')
            time.sleep(0.2)
            #self.parentApp.setNextFormPrevious()


    def auto_update_task(self):
        _id = self.task_list[self.task_select_box.value][0] 
        # update fields 
        if self.check_task_value():
            source_type_dic = ['web_url', 'local_path']
            file_type_dic = ['shell_script', 'ansible_playbook', 'executable_file']
            rollbackable_dic = {True:1, False:0}
            _mtime = int(time.time())
            #
            conn = sqlite3.connect(workflow_db)
            cur = conn.cursor()

            cur_cmd = ("UPDATE task SET " + \
                       "TASK_NAME = '%s', "     % (self.task_name.value ,) + \
                       "ROLLBACKABLE = %d, "    % (rollbackable_dic[self.rollbackable.value] ,) + \
                       "TRANSPORT_LOCAL_SOURDE = '%s', "    % (self.transport_local_source.value ,) + \
                       "TRANSPORT_LOCAL_TARGET = '%s', "    % (self.transport_local_target.value ,) + \
                       "TRANSPORT_REMOTE_SOURCE = '%s', "   % (self.transport_remote_source.value ,) + \
                       "TRANSPORT_REMOTE_TARGET = '%s', "   % (self.transport_remote_target.value ,) + \
                       "TASK_TYPE = '%s', "             % (self.task_type.values[self.task_type.value] ,) + \
                       "TASK_DESCRIPTION = '%s', "      % (self.task_description.values[self.task_description.value] ,) + \
                       "EXEC_SOURCE_TYPE = '%s', "      % (source_type_dic[self.exec_source_type.value] ,) + \
                       "EXEC_SOURCE_ADDR = '%s', "      % (self.exec_source_addr.value ,) + \
                       "EXEC_STARTUP_FILE = '%s', "     % (self.exec_startup_file.value ,) + \
                       "EXEC_FILE_TYPE = '%s', "        % (file_type_dic[self.exec_file_type.value] ,) + \
                       "SHELL_COMMAND_TEXT = '%s', "    % (self.shell_command_text.value ,) + \
                       "TASK_TAG = '%s', "      % (self.task_tag.value ,) + \
                       "TASK_NOTE = '%s', "     % (self.task_note.value ,) + \
                       "AUTH_LEVEL = %d, "      % (self.auth_level.value ,) + \
                       "NOTIFY_LEVEL = %d, "    % (self.notify_level.value ,) + \
                       "MTIME = %d "            % _mtime + \
                       "WHERE ID = %d "         % _id )

            try:
                cur.execute(cur_cmd)
            except:
                raise TypeError(cur_cmd)
            conn.commit()
            cur.close()
            npyscreen.notify('更新成功', title='消息')
            time.sleep(0.2)
            self.parentApp.setNextFormPrevious()

    def on_ok(self):
        # if selected 
        if isinstance(self.task_select_box.value, int):
            # if on editing 
            if self.edit_status != 'select':
                if npyscreen.notify_yes_no('是否提交正在编辑的任务?', title='确认提交'):
                    self.commit_modified_task(0)
                else:
                    # empty all
                    self.initialize_empty_task()
                    self.disable_edit_task()
        else:
            npyscreen.notify('没有任务被标记', '确认选择')
            time.sleep(0.2)
        self.parentApp.setNextFormPrevious()

    def on_cancel(self):
        self.parentApp.setNextFormPrevious()
        self.exit_editing()


#if __name__ == "__main__":
#    print('')
