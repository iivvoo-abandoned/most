"""
    Implementation of a query window - used for 1-1 irc messaging
"""

# $Id: queryView.py,v 1.2 2001/10/10 15:56:30 ivo Exp $

from view import txtview
from awtWindow import awtWindow

class queryView(awtWindow, txtview.queryView):
    def __init__(self, name = None):
        awtWindow.__init__(self)
        txtview.queryView.__init__(self, name)
