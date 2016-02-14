"""
    Dispatch meta events, such as closing connections, creating new
    connections, etc
"""

# $Id: metaHandler.py,v 1.1 2002/01/23 17:07:01 ivo Exp $

from string import *

class metaHandler:
    def __init__(self):
        pass

    ##
    ## Generic UI events
    def meta_close(self, source, text):
        """ invoked when the application is closed/terminated """
        pass

    def meta_quit(self, source, text):
        """ invoked when a specific connection is closed """
        pass

    def meta_new(self, source, text):
        pass
