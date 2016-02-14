"""
    Implementation of a query window - used for 1-1 irc messaging
"""

# $Id: queryView.py,v 1.20 2002/04/21 20:49:23 ivo Exp $ 

from gtk import *
from GDK import *
from libglade import *

from genericView import genericView
from msgSupport import msgSupport
from detachSupport import detachSupport
from nestable import nestable

from ui import HistoryEntry

class queryView(genericView, msgSupport, nestable, detachSupport):
    def __init__(self, name, container, state):
        genericView.__init__(self, "query_detach_container")
        nestable.__init__(self, self.window, container, state)
        #
        # Does this belong here? Code above is similair to channelView
        container.add(self.window) 
        
	self.text = self.get_widget("text")
        self.entry = HistoryEntry(self.get_widget("entry"))
	self.text.set_word_wrap(1)
	self.window = self.get_widget("query")
	self.chat_button = self.get_widget("check_chat")
	self.dcc_button = self.get_widget("check_dcc")
        # create a mixin?
        container = self.get_widget("detach_container")
        
	bindings = { 'input_activate':self.input_activate,
	             'window_close':self.window_close,
                     'detach_toggled':self.handle_detach_toggle,
                     'dcc_toggled':self.handle_dcc_toggle,
                     'chat_toggled':self.handle_chat_toggle,
                     'on_whois_pressed':self.handle_whois_pressed
                   }
        self.bindings(bindings)
        self.setname(name)
        self._use_dcc = 0
        self._has_dcc = 0
        ##
        ## checking/unchecking togglebuttons will generate appropriate
        ## events, which really sucks.
        self._in_handler = 0

    def set_handler(self, handler):
        self.handler = handler

    def setname(self, name=None):
        if name:
            self.name = name
        self.set_title("Query with %s" % self.name)
    
    def window_close(self, item, event):
	if self.handler:
            self.handler.view_winclose(self.name, self.name)
	return 1  # don't close window for us

    def handle_dcc_toggle(self, button, data=None):
        if not self._in_handler:
            self.handler.view_startdcc(self.name)

    def use_dcc(self):
        #return self.chat_button.get_active()
        return self._use_dcc

    def handle_chat_toggle(self, button, data=None):
        if self._in_handler:
            return 0 
        if not self._has_dcc:
            self._in_handler = 1
            self.announce("No DCC connection currently established")
            self.chat_button.set_active(0)
            self._in_handler = 0
            return 0
        if self._use_dcc:
            self._use_dcc = 0
            self.announce("Sending messages through IRC")
        else:
            self._use_dcc = 1
            self.announce("Sending messages through DCC connection")

    def handle_whois_pressed(self, button, data=None):
        """ a user pressed the 'whois' button in the query window """
        ## todo: schedule whois reply for notification in window
        self.handler.view_whois(self.name, self.name)

    def reset(self, propagate=1, level=0):
        # nothing to reset (at this moment) (dcc perhaps?)
        pass

    def dcc_established(self):
        self.announce("DCC Chat connection established")
        self._has_dcc = 1
        self._in_handler = 1
        self.dcc_button.set_active(1)
        self._in_handler = 0

    def dcc_lost(self):
        if self._use_dcc:
            self.announce("DCC Chat connection lost, reverting to normal chat")
        else:
            self.announce("DCC Chat connection lost")
        self._has_dcc = 0
        self._use_dcc = 0
        self._in_handler = 1
        self.chat_button.set_active(0)
        self.dcc_button.set_active(0)
        self._in_handler = 0

    def input_activate(self, item):
        text = item.get_text()
        item.set_text("")
        self.handler.handle_input(self.name, text)
