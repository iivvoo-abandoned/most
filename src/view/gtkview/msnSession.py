"""
    The view for an msnsession. This a session with 0, one or more users.
"""

from gtk import *
from GDK import *
from libglade import *

from genericView import genericView
from msgSupport import msgSupport

from ui import HistoryEntry, UserList

class msnSession(genericView, msgSupport):
    def __init__(self):
        genericView.__init__(self, "msnSession")
        self.entry = HistoryEntry(self.get_widget("entry"))
        self.list = UserList(self.get_widget("list"))
        self.text = self.get_widget("text")

        bindings = { 'input_activate':self.input_activate,
                     'window_close':self.window_close }
        self.bindings(bindings)
        self.handler = None

    def set_handler(self, handler):
        self.handler = handler

    def input_activate(self, item):
        text = item.get_text()
        item.set_text("")
        self.handler.handle_input(text)

    def window_close(self, whatmore):
        pass
