# $Id: detachSupport.py,v 1.5 2001/10/15 08:05:40 ivo Exp $

"""
    Support for detachable windows
"""

class detachSupport:
    def __init__(self):
        self.detach_handler = None

    def set_detach_handler(self, handler):
        self.detach_handler = handler

    def handle_detach_toggle(self, *arg):
        self.detach_handler(self)
        

