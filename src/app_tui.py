from src import npyscreen
from src.form_main import MainForm
from src.form_help import HelpForm
from src.form_HostGroup import HostGroupForm
#from src.form_AddTask import AddTaskForm
from src.form_Workflow import WorkflowForm
from src.form_SearchTask import SearchTaskForm
from src.form_CephDeply import CephDeplyForm

#import signal
import curses
import curses.ascii 

class App(npyscreen.StandardApp):

    def onStart(self):
        # main screen 
        self.MainForm           = self.addForm("MAIN", MainForm)
        self.HelpForm           = self.addForm("HelpForm", HelpForm)

        self.HostGroupForm      = self.addForm('HostGroupForm', HostGroupForm)
#        self.AddTaskForm        = self.addForm('AddTaskForm', AddTaskForm)
        self.WorkflowForm       = self.addForm('WorkflowForm', WorkflowForm)
        self.SearchTaskForm     = self.addForm('SearchTaskForm', SearchTaskForm)
        # new isinstance each time 
        #self.HostGroupForm = self.addFormClass('HostGroupForm', HostGroupForm)
        self.CephDeplyForm      = self.addForm('CephDeplyForm', CephDeplyForm)
        #self.SendFileForm = self.addForm("SEND_FILE", SendFileForm, lines=15)


    # not this way
    #    self._traps()

    def _cancel_action(self, *args, **keywords):
        #npyscreen.TEST_SETTINGS['TEST_INPUT'] = [' ', '^', 'C', curses.ascii.CAN ]
        #npyscreen.TEST_SETTINGS['TEST_INPUT'] = [ curses.ascii.CAN ]
        #npyscreen.TEST_SETTINGS['TEST_INPUT'] = [ curses.ascii.ESC ]
        npyscreen.TEST_SETTINGS['TEST_INPUT'] = [ curses.ascii.BEL ]
        #npyscreen.TEST_SETTINGS['TEST_INPUT'] = [ curses.ascii.DLE ]
        npyscreen.TEST_SETTINGS['CONTINUE_AFTER_TEST_INPUT'] = True
        #self.get_cancel = True

    #def while_waiting(self):
    #    pass

    #def trap_watcher(self):
    #    while True:
    #        signal.signal(signal.SIGINT, self._trap_cancel)

    #def _trap_abort(self):
    #    self.MainForm.confirm_abort()
