""" 
    minimal awt serverview based on txtview
"""

# $Id: serverView.py,v 1.3 2001/10/12 16:05:28 ivo Exp $

from view import txtview

from awtWindow import awtWindow
from channelView import channelView
from queryView import queryView

class serverView(awtWindow, txtview.serverView):
    def __init__(self, name=None):
        awtWindow.__init__(self)
        txtview.serverView.__init__(self, name)

    def create_channel(self, name):
        newchan = channelView(name)
        newchan.setcallback(self.view_handler)
        self.name = name
        return newchan

    def create_query(self, name):
        newquery = queryView(name)
        self.queries[name] = newquery
        newquery.setcallback(self.view_handler)
        return newquery

    def run(self):
        pass
