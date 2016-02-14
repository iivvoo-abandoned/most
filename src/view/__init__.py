"""
    "dynamically" load the appropriate view
"""

# $Id: __init__.py,v 1.7 2002/01/23 17:07:01 ivo Exp $

import viewHandler
import metaHandler

from util.cfg import getCfg

viewHandler = viewHandler.viewHandler
metaHandler = metaHandler.metaHandler
#
# Perhaps move this to the view-importing class?
gui = getCfg()("client.gui", "gtkview") # default is gtkview

if gui == "gtkview":
    import gtkview
    ircView = gtkview.ircView
    msgView = gtkview.msgView
    queryView = gtkview.queryView
    serverView = gtkview.serverView
elif gui == "txtview":
    import txtview
    ircView = txtview.ircView
    msgView = txtview.msgView
    queryView = txtview.queryView
    serverView = txtview.serverView
elif gui == 'awtview':
    # if sys.platform[:4] != 'java' ?
    import awtview
    ircView = awtview.ircView
    msgView = awtview.msgView
    queryView = awtview.queryView
    serverView = awtview.serverView

