""" 
    a singleton-ish state structure for irc

    How about thread safety? I.e. serverthread updating nick, 
    guithread using nick?
"""

# $Id: ircModel.py,v 1.11 2001/09/14 10:42:23 ivo Exp $

from util import casedict
from util.debug import *

class _ircState:
    def __init__(self):
        # active servers
        self.servers = {}
        self.serverid = 0
        # serverlist, config, etc

    def addServer(self, server):
        self.serverid = self.serverid + 1
        self.servers[self.serverid] = server
        return self.serverid

    def getServer(self, id):
        return self.servers[id]

    def removeServer(self, id):
        del self.servers[id]

    def reset(self, propagate=1, level=1):
        """ 
            reset entire model. Here for completeness, as usually only
            individual servers are reset
        """
        for i in self.servers.items():
            i.reset(propagate, level)

#
# This somewhat fakes a class ircModel constructor
def ircModel():
    global _state
    if not _state:
        _state = _ircState()
    return _state

_state = None
