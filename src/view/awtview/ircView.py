"""
    Minimal awt ircView - doesn't actually need a (g)ui
"""
# $Id: ircView.py,v 1.3 2001/10/12 16:05:28 ivo Exp $

from serverView import serverView

from view import txtview

class ircView(txtview.ircView.ircView):
    def __init__(self):
        txtview.ircView.ircView.__init__(self)

    def new_view(self, name):
        newview = serverView()
        newview.run()
        return newview

    def run(self):
        pass

    def mainloop(self):
        pass

    def mainquit(self):
        pass

_view = None

def getIrcView():
    global _view
    if not _view:
        _view = ircView()
    return _view

def parse_config(file=None):
    pass
