#!/usr/bin/env python
# coding=utf-8
import curses
import npyscreen

class HelpForm(npyscreen.ActionFormV2):
    def create(self):
        # Attribute 
        self.name = '帮助'
        #self.DEFAULT_X_OFFSET = 0
        #self.BLANK_COLUMNS_RIGHT = 0

        self.help1 = self.add(npyscreen.TitleText, name="折叠主机组列表:", value='< [ h', editable=False)
        self.help2 = self.add(npyscreen.TitleText, name="展开主机组列表:", value='> ] l', editable=False)
    def afterEditing(self):
        self.parentApp.setNextForm('MAIN')


