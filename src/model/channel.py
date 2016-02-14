"""
    channel state
"""

# $Id: channel.py,v 1.2 2001/09/23 12:51:13 ivo Exp $

from util import casedict
from util.debug import *
from modesupport import modesupport

#
# So, we also store channels that we have not joined (anymore).
# Perhaps *really* delete channel once the window is clicked away
# (but that's a View issue)

class channel(modesupport):
    STATE_INACTIVE = 0
    STATE_ACTIVE = 1
    STATE_LEFT = 2
    STATE_KICKED = 3

    MODE_NONE = 0
    MODE_PRIVATE = 1
    MODE_SECURE = 2
    MODE_NOMSG = 4
    MODE_TOPIC = 8
    MODE_INVITE = 16

    def __init__(self, name):
        modesupport.__init__(self)
        self.name = name
        self.users = casedict()
        self.topic = ""
        self.bans = casedict() # because equal bans can differ in case :(
        self.invite = casedict() # I modes
        self.excempt = casedict() # e modes
        # you can set a limit to any number (positive or negative) but not 0
        self.limit = 0 # no limit
        self.key = "" # no key
        self.state = channel.STATE_INACTIVE

    def adduser(self, user):
        self.users[user.name] = user

    def deluser(self, name):
        del self.users[name]

    def getuser(self, name):
        if self.users.has_key(name):
            return self.users[name]
        return None

    def settopic(self, topic):
        self.topic = topic

    def gettopic(self):
        return self.topic

    def setkey(self, key):
        self.key = key

    def getkey(self):
        return self.key

    def setlimit(self, limit=0):
        self.limit = limit

    def getlimit(self):
        return self.limit

    def setstate(self, state):
        self.state = state

    def getstate(self):
        return self.state

    def addban(self, ban):
        self.bans[ban] = 1

    def delban(self, ban):
        # you can remove non-existing bands. How usefull
        if self.bans.has_key(ban):
            del self.bans[ban]

    def addinvite(self, invite):
        self.invite[invite] = 1

    def delinvite(self, invite):
        if self.invite.has_key(invite):
            del self.invite[invite]

    def addexcempt(self, excempt):
        self.excempt[excempt] = 1

    def delexcempt(self, excempt):
        if self.excempt.has_key(excempt):
            del self.excempt[excempt]

    def getbans(self):
        return self.bans.keys()

    def reset(self, propagate=1, level=0):
        """ reset the channel structure """
        modesupport.reset(self, propagate, level)
        self.users = casedict()
        self.topic = ""
        self.bans = casedict() 
        self.invite = casedict()
        self.excempt = casedict()
        self.limit = 0 # no limit
        self.key = "" # no key
        if level > 0:
            self.state = channel.STATE_INACTIVE
