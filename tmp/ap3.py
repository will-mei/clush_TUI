#!/usr/bin/env python
# coding=utf-8
import npyscreen

class myEmployeeForm(npyscreen.Form):
    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):
        self.myName       = self.add(npyscreen.TitleText, name='Name')
        self.myDepartment = self.add(npyscreen.TitleSelectOne, scrool_exit=True, max_height=3,
                                     name='Department',
                                     values = ['Department 1', 'Department 2', 'Department 3']
                                    )
        self.myDate       = self.add(npyscreen.TitleDateCombo, name='Date')

class MyApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm('MAIN', myEmployeeForm, name='New myEmployee')


if __name__ == '__main__':
    TestApp = MyApplication().run()
    print("All objects, baby.")
