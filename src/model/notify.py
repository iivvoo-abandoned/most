"""
    structure to store notifies
"""

# $Id: notify.py,v 1.1 2001/09/14 10:42:23 ivo Exp $

from util import casedict
from util.debug import *

class notify:
    def __init__(self):
        self.users = casedict()

    def online(self, users):
        self.users = casedict()
        for i in users:
            self.users[i] = i

    def get_online(self):
        return self.users

    def reset(self, propagate=1, level=0):
        """ reset the notify structure """
        self.users = casedict()
