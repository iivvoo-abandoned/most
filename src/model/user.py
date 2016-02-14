"""
    user state
"""

# $Id: user.py,v 1.2 2001/09/18 12:26:07 ivo Exp $

from util import casedict
from util.debug import *
from modesupport import modesupport

class user(modesupport):
    MODE_NONE = 0
    MODE_OP = 1
    MODE_VOICE = 2
    
    def __init__(self, name, mode=MODE_NONE):
        modesupport.__init__(self)
        self.name = name
        self.mode = mode
        self.away = ""
        self.in_whois = 0       # to track if we're parsing a whois response
        self.dcc = []           # store dcc offerings

    def reset(self, propagate=1, level=1):
        """ nothing to reset """
        modesupport.reset(self, propagate, level)

    def add_dcc(self, host, port, type, args):
        """ store an offered dcc connection """
        new_dcc = [host, port, type]
        if type(args) == type([]):
            new_dcc.extend(args)
        else:
            new_dcc.append(args)
        self.dcc.append(new_dcc)
