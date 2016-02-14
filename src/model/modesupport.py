"""
    generic support for mode setting/retrieving/deleting
"""

# $Id: modesupport.py,v 1.1 2001/09/14 10:42:23 ivo Exp $

from util.debug import *

class modesupport:
    """ mixin for classes that support modes """
    def __init__(self):
        self.mode = 0

    def setmode(self, mode):
        self.mode = self.mode | mode
        return self.mode

    def delmode(self, mode):
        self.mode = self.mode & ~mode
        return self.mode

    def getmode(self, mode = 0):
        if mode:
            return self.mode & mode
        return self.mode

    def reset(self, propagate=1, level=1):
        """ reset modes """
        self.mode = 0
