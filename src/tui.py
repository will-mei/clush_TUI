from src import npyscreen
from src.MainForm import MainForm
from src.HelpForm import HelpForm
from src.HostGroupForm import HostGroupForm

class App(npyscreen.StandardApp):

    def onStart(self):
        # main screen 
        self.MainForm = self.addForm("MAIN", MainForm)
        self.HelpForm = self.addForm("HelpForm", HelpForm)
        # new isinstance each time 
        self.HostGroupForm = self.addFormClass('HostGroupForm', HostGroupForm)
        #self.SendFileForm = self.addForm("SEND_FILE", SendFileForm, lines=15)
