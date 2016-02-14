"""
    Implementation of the channel (1-n communication) view
"""

# $Id: channelView.py,v 1.2 2001/10/10 15:56:30 ivo Exp $

from view import txtview
from awtWindow import awtWindow

class channelView(awtWindow, txtview.channelView):
    def __init__(self, name):
        awtWindow.__init__(self)
        txtview.channelView.__init__(self, name)
