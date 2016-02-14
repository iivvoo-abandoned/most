"""
    Implementation of a query window - used for 1-1 irc messaging
"""

# $Id: queryView.py,v 1.1 2001/09/23 23:21:42 ivo Exp $

from view import guiMessage

from genericView import genericView
#from cmdHandler import cmdHandler
from msgSupport import msgSupport

class queryView(genericView, msgSupport):
    def __init__(self, name = None):
        genericView.__init__(self, "query")
	self.name = name

    def setcallback(self, cb):
        self.handler = cb
    
    def setname(self, name=None):
        if name:
            self.name = name
        self.announce("Starting query with %s" % self.name)
    
    def window_close(self, item, event):
        pass
