#!/usr/bin/env python
# coding=utf-8
import time
from src import npyscreen

#time.asctime( time.localtime(time.time()) )
def str_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class InfoBox(npyscreen.BoxTitle):
    #_contained_widget = 
    def create(self):
        #self.buff_messages = 200 * [None]
        pass

    def when_value_edited(self):
        pass

    def when_cursor_moved(self):
        self.parent.parentApp.queue_event(npyscreen.Event("event_messagebox_change_cursor"))

    # self.height
    # self.width
    # datetime 

    def append_msg(self, msgs):
        # single line 
        if isinstance(msgs, str):
            self.values.append(str_timestamp() + ': ' + str(msgs))
        # multiline 
        elif isinstance(msgs, list):
            if len(msgs) :
                self.values.append(str_timestamp() + ': ' + str(msgs[0]))
                for i in msgs[1:]:
                    self.values.append( 19 * ' ' + '  ' + str(i))
            else:
                self.values.append(str_timestamp() + ': 收到消息, 内容为空' + str(msgs))
        else:
            self.values.append(str_timestamp() + ': 收到消息, 格式错误' + str(type(msgs)))

        # focus on last line 
        if len(msgs) > self.height - 3:
            self.entry_widget.start_display_at = len(msgs) - self.entry_widget.start_display_at - (self.height - 3)
        
        # try to refresh widget 
        try:
            self.entry_widget.cursor_line = len(self.entry_widget._my_widgets) # doesn't work
            #self.entry_widget.update(clear=True)
            #self.entry_widget.h_cursor_end('G') # doesn't work 

            #self.entry_widget.display()
            #self.parent.display()
        except:
            pass 


    def update_msgs(self, messages):
        # replace empty char
        messages = map(lambda x : x.replace(chr(8203), ''), messages )

        self.entry_widget.highlighting_arr_color_data = color_data
        self.values = data

        if len(messages) > self.height - 3:
            self.entry_widget.start_display_at = len(messages) - self.height + 3
        else:
            self.entry_widget.start_display_at = 0

        self.entry_widget.cursor_line = len(messages)

        # a task a dialog 
        #self.name = client.dialogs[host_id].name
        #self.footer = client.online[host_id]
        self.name = 'test name'
        self.footer = 'online host xxx'

        self.display()

        # 1 debug 
        # 2 info
        # 3 warn
        # 4 error
        # 5 fatal 
        #if info_type == 1:
        #    color = len(user_name) * [self.parent.theme_manager.findPair(self, 'WARNING')]
        # if group 

        # add message to out []
        #self.prepare_message(out, mess, name, read, mess_id, color, date)

        # add media to out []
        #self.prepare_media(out, media, name, image_name, read, mess_id, color, date)

        # update buffer
        #self.buff_messages[host_id] = out

        # return Message obj
        #return msg_obj

    # structure for out message
    class Messages:
        def __init__(self, host_id, date, color, message, msg_id, read):
            self.sender   = host_id
            self.date     = date
            self.color    = color
            self.messages = message_tx
            self.id       = msg_id
            self.read     = read

#    # add message to Message structure
    def format_msg(self, out, mess, name, task_name, read, msg_id, color, date):

        max_width = int((self.width - len(task_name) - 11) / 1.3)
        max_height = int((self.height - 12) / 1.3)
#
        msg_list = _text.split("\n")
        # invert seq and add to out 
        for k in range(len(msg_list) - 1, 0, -1):
            out.append(self.Messages(len(task_name) * " ", date, color, _text[k], msg_id, read))
#
        out.append(self.Messages(name, date, color, "test str ", msg_id, read))
