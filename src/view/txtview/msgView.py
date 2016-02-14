"""
    handling of individual messages

    Completely remove this for txtview?
"""

# $Id: msgView.py,v 1.2 2001/10/09 22:19:57 ivo Exp $

from msgSupport import msgSupport
from genericView import genericView


class msgView(msgSupport, genericView):
    def __init__(self):
        pass
