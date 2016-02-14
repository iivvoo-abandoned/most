"""
    server state
"""

# $Id: server.py,v 1.2 2001/09/14 16:27:05 ivo Exp $

from util import casedict
from util.debug import *
from modesupport import modesupport
from notify import notify

class server(modesupport):
    STATE_NOTCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2

    def __init__(self):
        modesupport.__init__(self)
        self.nick = "<UNKNOWN>"
        self.name = ""
        self.channels = casedict()
        self.notifies = notify()
        #
        # the users dict. can be used to store/track user related info
        self.users = casedict() 
        self.state = server.STATE_NOTCONNECTED

    def addChannel(self, channel):
        self.channels[channel.name] = channel

    def delChannel(self, name):
        del self.channels[name]

    def getChannel(self, name):
        if self.channels.has_key(name):
            return self.channels[name]
        return None

    def getChannels(self):
        return self.channels.items()

    def addUser(self, user):
        self.users[user.name] = user

    def delUser(self, user):
        if self.users.has_key(name):
            del self.users[name]
    def getUser(self, name):
        return self.users.get(name, None)

    def getUsers(self):
        return self.users.items()

    def getState(self):
        return self.state

    def setState(self, newstate):
        """ set the new state """
        self.state = newstate

    def reset(self, propagate=1, level=1):
        """ 
            reset the server datastructure.

            depending on propagate/level, substructures (i.e. channels)
            are also reset, or completely removed.

            This method does not alter self.state - an explicit extra call
            to setState is required for this.

            Levels:

            0           clear all structures
            1           mark object as INACTIVE / DISCONNECTED / whatever
        """
        modesupport.reset(self, propagate, level)
        if propagate:
            for i in self.channels.values() + self.users.values():
                i.reset(propagate, level)
        self.notifies.reset(propagate, level)
        if level > 0:
            self.setState(server.STATE_NOTCONNECTED)
