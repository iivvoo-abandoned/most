#!/usr/bin/python

# $Id: ircView.py,v 1.4 2001/10/09 22:19:57 ivo Exp $

import sys
from string import strip
from threading import Thread
from time import sleep

from view import guiMessage
from genericView import genericView
from msgSupport import msgSupport
from serverView import serverView

from util.debug import debug, DEBUG, NOTICE, ERROR

class ircView(genericView,  msgSupport, Thread):
    def __init__(self):
        genericView.__init__(self, "most")
        Thread.__init__(self)
        self.handler = None
        self.running = 1

    def setcallback(self, cb):
        self.handler = cb

    def msg_handler(self, item, event):
        """ pass to handler """
        if self.handler:
            # perhaps do something with event, i.e. source?
            self.handler(item, event)

    def new_view(self, name):
        newview = serverView()
        newview.start()
        return newview

    def run(self):
        self.running = 1
        while self.running:
            text = raw_input()
            event = None
            if strip(text) != "":
                if text[0] == '/':
                    event = guiMessage.guiMessage(text[1:])
                    # if event.type == guiMessage.UNKNOWN ...
                else:
                    event = guiMessage.guiMessage()
                    event.type = guiMessage.MSG
                    if hasattr(self, 'name'):
                        event.source = self.name
                        event.target = self.name # This should invoke some method
                    event.data = text
            
                if self.handler:
                    self.handler(self, event)
        

    def mainloop(self):
        #self.start()
        pass

    def mainquit(self):
        self.running = 0

    def threads_enter(self):
        pass

    def threads_leave(self):
        pass

_view = None

def getIrcView():
    global _view
    if not _view:
        _view = ircView()
    return _view

def parse_config(file=None):
    pass

