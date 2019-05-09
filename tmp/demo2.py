import npyscreen


class MyTestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    def create(self):
        self.add(npyscreen.TitleText, name = "Text:", value= "Hellow World!" )

    def afterEditing(self):
        self.parentApp.setNextForm(None)

if __name__ == '__main__':
    TA = MyTestApp()
    TA.run()
