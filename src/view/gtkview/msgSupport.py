"""
    generic routines for classes / widgets that support printing of irc messages
"""

# $Id: msgSupport.py,v 1.11 2002/02/24 23:08:24 ivo Exp $

from gtk import *
from GDK import *
from libglade import *

red = GdkColor(-1, 0, 0)
blue = GdkColor(0, 0, -1)

class msgSupport:
    def __init__(self):
        pass

    def insert(self, msg):
        self.text.insert_defaults(msg + "\n")
        if hasattr(self, "updated") and callable(self.updated):
            self.updated()

    def msg(self, nick, msg, isme = 0, dcc=0):
        if dcc:
            _nick = "=%s=" % nick
        else:
            _nick = "<%s>" % nick

	if isme:
            self.text.insert(None, blue, None, "%s " % _nick)
	else:
            self.text.insert(None, red, None, "%s " % _nick)
	self.insert(msg)

    def notice(self, nick, msg, isme=0):
	if isme:
            self.text.insert(None, blue, None, "-%s- " % nick)
	else:
            self.text.insert(None, red, None, "-%s- " % nick)
	self.insert(msg)

    def action(self, nick, msg, isme=0, dcc=0):
        arrow = "->"
        if dcc:
            arrow = "=>"
	if isme:
            self.text.insert(None, blue, None, "%s %s " % (arrow, nick))
	else:
            self.text.insert(None, red, None, "%s %s " % (arrow, nick))
	self.insert(msg)

    def announce(self, msg):
        self.insert("*** " + msg)

    def sendmsg(self, nick, msg):
        """ insert a message *to* someone """
        self.text.insert(None, blue, None, "-> <%s> " % nick)
	self.insert(msg)

    def sendaction(self, nick, target, msg):
        """ insert a message *to* someone """
        self.text.insert(None, blue, None, "-> <%s> %s " % (target, nick))
	self.insert(msg)

