"""
    Dummy awt msgView (as msgViews aren't supported atm)
"""

# $Id: msgView.py,v 1.4 2001/10/12 16:05:28 ivo Exp $

from view import txtview

class msgView(txtview.msgView):
    def __init__(self):
        txtview.msgView.__init__(self)
