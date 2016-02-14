"""
    Implementation of the channel (1-n communication) view
"""

# $Id: channelView.py,v 1.1 2001/09/23 23:21:42 ivo Exp $

from string import strip, join
from view import guiMessage

from genericView import genericView
from msgSupport import msgSupport

from util import casedict
from util.debug import debug, DEBUG, NOTICE, ERROR

class channelView(genericView, msgSupport):
    def __init__(self, name):
        genericView.__init__(self, "channel")
        self.name = name
        self.setname(name)

        self.users = casedict() # to store list items
        self.closeonleave = 0
        self.active = 1 # by default

    def setcallback(self, handler):
        self.handler = handler

    def setname(self, name=None):
        if name:
            self.name = name

    def adduser(self, nick, mode=None):
        pass

    def deluser(self, nick):
        pass

    def userjoin(self, nick, userhost):
        self.announce("%s (%s) has joined channel %s" % \
                      (nick, userhost, self.name))
        self.adduser(nick)

    def userquit(self, nick, userhost, reason):
        self.announce("%s has quit (%s)" % (nick,  reason))
        self.deluser(nick)

    # add: isself
    def userleave(self, nick, userhost, reason):
        self.announce("%s (%s) has left channel %s (%s)" % \
                      (nick, userhost, self.name, reason))
        self.deluser(nick)

    def userkick(self, nick, userhost, target, reason, isself=0):
        if isself:
            self.announce("You have been kicked from channel %s by " \
                          "%s (%s) (%s)" % (self.name, nick, userhost, reason))
        else:
            self.announce("%s has been kicked from channel %s by " \
                          "%s (%s) (%s)" % (target, self.name, nick, 
                                            userhost, reason))
        self.deluser(target)

    def modechange(self, nick, plusmodes, minmodes, plusparams, minparams):
        """ handle channelmode changes """
        modestr = ""
        if plusmodes != "":
            modestr = modestr + "+" + plusmodes
        if minmodes != "":
            modestr = modestr + "-" + minmodes
        if plusmodes != []:
            modestr = modestr + " " + join(plusparams, ' ')
        if minmodes != []:
            modestr = modestr + " " + join(minparams, ' ')

        self.announce("%s sets mode %s" % (nick, modestr))

    def usermodechange(self, nick, mode):
        """ Handle a usermode change on a channel """
        pass

    def topic(self, topic, changed_by = None):
        if changed_by:
            self.announce("%s sets the topic to %s" % (changed_by, topic))
        else:
            self.announce("Topic for %s: %s" % (self.name, topic))

    def nickchange(self, oldnick, newnick):
        self.announce("%s is now known as %s" % (oldnick, newnick))

    def part(self):
        """ invoked when *I* leave this channel. I.e. after explicit /leave
            or after kick. Closing a window implicitly triggers a /leave,
            but also sets the self.closeonleave flag to true

            Todo (?): add type (type of parting: kick, part, ..)
        """
        pass

