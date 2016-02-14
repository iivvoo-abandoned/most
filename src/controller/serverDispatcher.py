""" 
    This module dispatches (preparsed) events from the server over several
    handlers.
"""

# $Id: serverDispatcher.py,v 1.75 2002/03/22 08:54:15 ivo Exp $

from net import *
from string import *
import time
import model

from ctcpSupport import ctcpSupport
from mode import mode
from util.debug import debug, DEBUG, NOTICE, ERROR
from util.timefmt import sec_to_str
from util import Log

class serverDispatcher(ctcp, ctcpSupport):
    def __init__(self):
        ctcpSupport.__init__(self)
        self.irc = irc(self)

    def connect(self, host, port=6667):
        self.host = host
        self.port = port
        tcp.Client(self.host, self.port, self.irc) # move to serverDispatcher

    def close(self):
        print "XXX serverDispatcher.close() not implemented"

    def connectionMade(self):
        self.irc.user("most", self.serverState.name)
        self.irc.nick(self.serverState.nick)

    def connectionLost(self):
        debug(DEBUG, "ERROR RECEIVED")
        self.viewtext.announce("Connection lost: %s" % self.irc.errstr)
        self.reset()

    def connectionFailed(self):
        debug(DEBUG, "ERROR RECEIVED")
        self.viewtext.announce("Connection failed: %s" % self.irc.errstr)
        self.reset()
        
    # generic shortcut bindings

    def ignore(self, command, prefix, args):
        pass

    def show_main(self, command, prefix, args):
        # check prefix against serverState.hostname?
        self.viewtext.announce(args[-1])

    ##                      
    ## irc protocol handlers - numerics

    def irc_001(self, command, prefix, args):
        """ 
           rpl welcome

           we use this message to check our own nick 
        """
        self.serverState.serverhost = prefix
        self.viewtext.setname(prefix)
        self.viewtext.setnick(args[0])
        self.serverState.nick = args[0]
        self.serverState.state = model.server.STATE_CONNECTED
        self.show_main(command, prefix, args)
       
    #
    # Whois replies

    def irc_301(self, command, prefix, args):
        """ 
            whois reply: away 
        
            This reply is given both as a whois reply as when messaging someone
            who is away. Currently, this is the only whois reply that is 
            dispatched to query/msg windows, so this will look confusing when
            doing a whois on someone you're querying with.

            Solution? Probably to send all whois info to the query window
        """
        #
        # check if we've already seen this away message
        nick = args[1]
        remainder = args[-1]
        user = self.serverState.users.get(nick, model.user(nick))
        self.serverState.addUser(user)

        #
        # Only surpress display if we're not in a whois
        if user.away == args[-1] and not user.in_whois:
            return                      # XXX check if SHOW_AWAY_ONCE is on
        #
        # only store awaymsg if not in whois, so we see the awaymsg 
        # explicitly again on first msg.
        if not user.in_whois:
            user.away = remainder

        #
        # send the 303 to the query window if it's not part of a whois
        # (perhaps display entire whois replies in msg/query windows?)
        if not user.in_whois:
            if self.queries.has_key(nick):
                self.queries[nick].announce("%s is away: %s" % \
                                            (nick, args[-1]))
            else:
                msg = self.viewtext.get_msgwin(create=0)
                if msg:
                    msg.isaway(nick, args[-1])
        self.viewtext.announce("%s is away: %s" % (nick, args[-1]))

    def irc_303(self, command, prefix, args):
        """ ISON reply, i.e. who is online """
        nicks = filter(None, split(args[-1], " "))
        old = self.serverState.notifies.get_online()
        self.serverState.notifies.online(nicks)
        new = self.serverState.notifies.get_online()

        for i in new.values():
            if not old.has_key(i):
                self.viewtext.notify_online(i)

        for i in old.values():
            if not new.has_key(i):
                self.viewtext.notify_offline(i)
        
    def irc_305(self, comand, prefix, args):
        """ away: no longer marked away """
        # store away status?
        self.viewtext.announce("You are no longer marked away")

    def irc_306(self, comand, prefix, args):
        """ away: marked away """
        # store away status?
        self.viewtext.announce("You have been marked away")
        
    def irc_311(self, command, prefix, args):
        """ whois reply """
        # mark that we're parsing this users whois
        nick = getnick(args[0])
        user = self.serverState.users.get(nick, model.user(nick))
        user.in_whois = 1
        self.serverState.addUser(user)
        self.viewtext.announce("%s is %s@%s (%s)" % \
             (args[1], args[2], args[3], args[-1]))

    def irc_312(self, command, prefix, args):
        """ whois reply: on server """
        # XXX This reply is also used for whowas, so the 'is' is wrong then
        self.viewtext.announce("%s is on server %s (%s)" % \
                           (args[1], args[2], args[-1]))

    def irc_313(self, command, prefix, args):
        """ whois reply: irc operator """
        self.viewtext.announce("%s is an irc operator" % (args[1]))

    def irc_314(self, command, prefix, args):
        """ whowas reply """
        self.viewtext.announce("%s was %s@%s (%s)" % \
             (args[1], args[2], args[3], args[-1]))

    def irc_317(self, command, prefix, args):
        """ whois reply: x seconds idle """
        self.viewtext.announce("%s is idle for %s" % \
                           (args[1], sec_to_str(args[2])))

    def irc_318(self, command, prefix, args):
        """ end of whois """
        # mark that we're done parsing this users whois
        nick = getnick(args[0])
        user = self.serverState.users.get(nick, None)
        if user:
            user.in_whois = 0

    def irc_319(self, command, prefix, args):
        """ whois reply: channels """
        self.viewtext.announce("%s is on channels %s" % (args[1], args[-1]))
    # end of whois replies

    def irc_324(self, command, prefix, args):
        """ 
            324 is a basic mode reply. We use it to get the mode
            of a channel we just joined.

            But we can also receive this mode for channels we have not 
            joined, in which case it will not contain the channelkey
            (if any)

            Todo: check the channelstate to see if we really want this
            info, or if the user just typed /mode #foo
        """
        # check 'await 324 flag' in model?
        modechange = mode(join(args[2:]))
        #
        # DRY - this code looks alot like the code in irc_MODE
        chanModel = self.serverState.getChannel(args[1])
        #
        # However, we don't handle all modes here (such as o,b,v)
        ## XXX DUPLICATION
        modemap = { 'p':model.channel.MODE_PRIVATE,
                    's':model.channel.MODE_SECURE,
                    'n':model.channel.MODE_NOMSG,
                    't':model.channel.MODE_TOPIC,
                    'i':model.channel.MODE_INVITE }

        for i in range(len(modechange.plusmodes())):
            c = modechange.plusmode(i)
            if c == 'l':
                # in this context, we can assume the limit is not ""
                chanModel.setlimit(atoi(modechange.plusparam(i)))
            elif c == 'k':
                # in this context, we can assume the key is not ""
                chanModel.setkey(modechange.plusparam(i))
            elif c == 'I':
                chanModel.addinvite(modechange.plusparam(i))
            elif c == 'e':
                chanModel.addexcempt(modechange.plusparam(i))
            else:
                if modemap.has_key(c):
                    chanModel.setmode(modemap[c])
                # else warn for unknown channelmode?
        for i in range(len(modechange.minmodes())):
            c = modechange.minmode(i)
            if c == 'l':
                chanModel.setlimit(0)
            elif c == 'k':
                chanModel.setkey("")
            elif c == 'I':
                chanModel.addinvite(modechange.minparam(i))
            elif c == 'e':
                chanModel.addexcempt(modechange.minparam(i))
            else:
                if modemap.has_key(i):
                     chanModel.delmode(modemap[c])
                # else warn for unknown channelmode?
        if self.channels.has_key(args[1]):
            chanView = self.channels[args[1]]
            chanView.modechange(args[0], modechange, notice=0)

    def irc_329(self, command, prefix, args):
        """ 329 is time the channel was created (?) (opn, ...?) """
        if self.channels.has_key(args[0]):
            self.channels[args[0]].announce("Channel created at %s" % \
                              time.ctime(int(args[2])))

    def irc_332(self, command, prefix, args):
        """ 332 shows the topic when a channel is joined 
        
            :struis.intranet.amaze.nl 332 Vladje #foo :Foo Bar Blah
        """
        if self.channels.has_key(args[1]):
            self.channels[args[1]].topic(args[-1])
        # state.channel.topic = ...
        
    def irc_333(self, command, prefix, args):
        """ 333 is time and who set topic (opn, ...?) """
        if self.channels.has_key(args[0]):
            self.channels[args[0]].announce("Topic set at %s by %s" % \
                              (time.ctime(int(args[2])), args[1]))

    def irc_341(self, command, prefix, args):
        """ 341 is "inviting nick to channel #bar" """
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce("Inviting %s" % args[0])
        else:
            self.viewtext.announce("Inviting %s to channel %s" % (args[0],
                                   args[1]))

    def irc_352(self, command, prefix, args):
        """ /who reply """
        # remainder also contains # of hops on some (?) servers..
        self.viewtext.announce("%s %s %s@%s (%s)" % \
         (args[0], args[4], args[1], args[2], args[-1]))

    def irc_353(self, command, prefix, args):
        """ names list, shown when joining a channel 
        
            Currently, intercept 353 to build a userlist for channel. This
            means that doing a NAMES by hand will not result in any output.
            This can be changed if we use 366 (end of names) to mark a
            channel 'complete'
        """
        channel = args[2]
        # filter out empty spaces, remainder may end in ' '
        names = filter(None, split(args[-1], ' '))
        
        modemap = { None:model.user.MODE_NONE,
                    '@':model.user.MODE_OP, 
                    '+':model.user.MODE_VOICE }

        c = self.serverState.getChannel(channel)
        for i in names:
            name,mode = nickparse(i)
            u = c.getuser(name)
            if not u:
                c.adduser(model.user(name, modemap[mode])) # , mode
                self.channels[channel].adduser(name, mode)
            else: # use mode to update modes
                self.channels[channel].usermodechange(name, mode)
                u.setmode(modemap[mode])

    def irc_367(self, command, prefix, args):
        """
            Channel ban list, i.e. after /mode #channel b

            Use this info to fill the banlist.

            XXX TODO: Check if channel requires this info or if we 
            should just display entries.

            The 'ending' 368 is handled as a shortcut (for now)
        """
        chanModel = self.serverState.getChannel(args[1])
        chanModel.addban(args[2])

    def irc_401(self, command, prefix, args):
        """ 
            401 is "No suck nick/channel" 

            Try to dispatch this message to the appropriate window.
            For now, this means find the appropriate query or display
            it in the messagewindow, if available. Always display in 
            the main window.
        
        """
        #
        # TODO: Provide an alternative text if 'nick' is a channel
        nick = args[1]
        if self.queries.has_key(nick):
            self.queries[nick].announce("%s is not online" % nick)
        else:
            msg = self.viewtext.get_msgwin(create=0)
            if msg:
                msg.notonline(nick)
        self.viewtext.announce("%s is not online" % nick)

    def irc_403(self, command, prefix, args):
        """ 403 is 'no such channel """
        self.viewtext.announce("channel %s does not exist" % args[1])

    def irc_404(self, command, prefix, args):
        """
            404 is 'cannot send to channel'
        """
        if self.channels.has_key(args[1]):
            #
            # TODO:
            # Figure out what could be wrong (i.e. +m, no v, not on chan, etc)
            self.channels[args[1]].announce("Cannot send text to this channel")
        else:
            self.viewtext.announce("Cannot send to channel %s" % args[2])

    def irc_406(self, command, prefix, args):
        """ 406 is 'there was no such nick """
        self.viewtext.announce("There was no user named %s" % args[1])

    def irc_433(self, command, prefix, args):
        """ 
            433 is 'nick already in use'
        """
        self.viewtext.announce("Nickname %s is already in use by someone else" \
                               % args[1])

    def irc_437(self, command, prefix, args):
        """ 
            437 is 'nick/channel temporarily unavailable'
        """
        if self.channels.has_key(args[1]):
            #
            # TODO:
            # Figure out what could be wrong (i.e. +m, no v, not on chan, etc)
            self.channels[args[1]].announce(
                         "This channel is temprarily unavailable")
        else:
            self.viewtext.announce("Cannot send to channel %s" % args[1])
        #
        # XXX check if it is a nick or a channel, display more appropriate
        #     message
        self.viewtext.announce("Nick/channel %s is temporarily unavailable" \
                               % args[1])
        
    def irc_443(self, command, prefix, args):
        """ "is already on channel" """
        if self.channels.has_key(args[2]):
            self.channels[args[2]].announce(
                         "%s is already on this channel" % (args[1]))
        else:
            self.viewtext.announce("%s is already on channel %s" % \
                               (args[1], args[2]))
        
    def irc_464(self, command, prefix, args):
        """ password incorrect """
        self.viewtext.announce("Server password incorrect")
        # close connection, mark as not connected, etc.

    def irc_465(self, command, prefix, args):
        """ You are banned """
        self.viewtext.announce("You are banned from this server: %s" % args[-1])
        # close connection, mark as not connected, etc.

    def irc_466(self, command, prefix, args):
        """ You will be banned """
        self.viewtext.announce("You will be banned from this server: %s" % \
                               args[-1])

    def irc_471(self, command, prefix, args):
        """ channel is full """
        self.viewtext.announce("%s is full (+l limit reached)" % args[1])
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce(
                         "%s is full (+l limit reached)" % args[1])

    def irc_472(self, command, prefix, args):
        """ mode not supported / unknown """
        # The channelname is (usually?) encoded in the remainder..
        # use it?
        self.viewtext.announce("Mode %c is not supported" % args[1])

    def irc_473(self, command, prefix, args):
        """ channel is invite only """
        self.viewtext.announce("%s is invite-only" % args[1])
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce("%s is invite-only" % args[1])

    def irc_474(self, command, prefix, args):
        """ banned from channel """
        self.viewtext.announce("You are banned from %s" % args[1])
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce("You are banned from %s" % args[1])

    def irc_475(self, command, prefix, args):
        """ channel key required """
        self.viewtext.announce("A (correct) key is required to join %s" % \
                               args[1])
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce(
                     "A (correct) key is required to join %s" % args[1])

    def irc_476(self, command, prefix, args):
        """ bad channel mask (???) """
        self.viewtext.announce("Bad channel mask %s" % args[1])
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce("Bad channel mask %s" % args[1])

    def irc_477(self, command, prefix, args):
        """ channel does not support modes """
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce(
                     "This channel does not support modes" % args[1])

    def irc_478(self, command, prefix, args):
        """ list is full, optinal rest[1] contains char (I and e?) """
        #
        # XXX make proper translation of 'char' to listname
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce( "Channel list is full (%c)" % args[1])

    def irc_481(self, command, prefix, args):
        """ You are not irc operator """
        self.viewtext.announce("Permission denied - you are not an ircop")

    def irc_482(self, command, prefix, args):
        """ You are not channel operator """
        if self.channels.has_key(args[1]):
            self.channels[args[1]].announce(
                   "You are not channeloperator")

    # named replies
    def irc_PING(self, command, prefix, args):
        self.irc.pong(args[-1])

    def irc_INVITE(self, command, prefix, args):
        """ handle invites. """
        self.viewtext.announce("%s invites you to channel %s" % \
                           (getnick(prefix), args[-1]))

    # formatting the string in the controller makes the controller decide 
    # part of the view - wrong!
    def irc_JOIN(self, command, prefix, args):
        """ the channelname is in the remainder part. A bit weird.

            actually, it seems there are two syntaxes? One where the 
            channelname is the target ?! 
        """
        ##if ircMsg.target:
        ##    channel = ircMsg.target
        ##else:
        ##    channel = ircMsg.remainder
        channel = args[0]
        nick = getnick(prefix)
        userhost = getuserhost(prefix)

        if self.isme(nick):
            self.do_join(channel)
        # add user to model
        c = self.serverState.getChannel(channel)
        c.adduser(model.user(nick))

        self.channels[channel].userjoin(nick, userhost)
        self.logger.log(channel, "*** %s (%s) has joined channel %s" % \
                        (nick, userhost, channel))

    def irc_PART(self, command, prefix, args):
        """ check if it's us that parts """
        channel = args[0]
        nick = getnick(prefix)
        userhost = getuserhost(prefix)

        self.channels[channel].userleave(nick, userhost, args[-1])
        if self.isme(nick):
            # xchat saves channel - add to channelwindowpool?
            #self.channels[channel].close()
            if self.channels[channel].part():
                # true means window was destroyed
                # XXX Duplication with ircController.view_hander-WIN_CLOSE
                del self.channels[channel]
                self.viewtext.delete_channel(channel)
            self.serverState.delChannel(channel)
        else:
            # remove user from model
            c = self.serverState.getChannel(channel)
            c.deluser(nick)
        self.logger.log(channel, "*** %s (%s) has left channel %s (%s)" % \
                        (nick, userhost, channel, args[-1]))

    def handle_message(self, source, target, text, dcc):
        nick = getnick(source)

        ##
        ## Yes, we support ctcp through dcc (i.e. action) - why not?
        if ctcp.is_ctcp(text):
            self.handle_ctcp(source, target, text, dcc=dcc)
            ## ctcp logging is done elsewhere
            return

        if ischannel(target) and self.channels.has_key(target):
            self.channels[target].msg(nick, text)
        elif self.queries.has_key(nick):
            self.queries[nick].msg(nick, text, dcc=dcc)
        elif self.cfg('client.use_msg_win'):
            msg = self.viewtext.get_msgwin()
            if msg:
                msg.msg(nick, text, dcc=dcc)
            else:
                self.viewtext.msg(nick, text, dcc=dcc)
        else: # create query
            self.queries[nick] = self.viewtext.create_query(nick)
            self.queries[nick].msg(nick, text, dcc=dcc)

        # log!
        # if it's a private message to me, log it in the senders log
        if self.isme(target):
            log_target = nick
        else:
            log_target = target
        if dcc:
            self.logger.log(log_target, "=%s= %s" % (nick, text))
        else:
            self.logger.log(log_target, "<%s> %s" % (nick, text))
    
    def irc_PRIVMSG(self, command, prefix, args):
        # check if it's a ctcp. If so, invoke a separate handler.
        # Some bots (and clients?) don't properly terminate CTCP's with ^A
        # - should we support this?
        remainder = args[-1]
        target = args[0]
        nick = getnick(prefix)

        self.handle_message(prefix, target, remainder, dcc=0)

    def irc_NOTICE(self, command, prefix, args):
        # This may also be ctcp replies! 
        remainder = args[-1]
        target = args[0]
        if prefix:
            nick = getnick(prefix)
        else:
            nick = "SERVER"

        print "Prefix", prefix
        if prefix == "":
            # sometimes we get these before logging in at all 
            # (i.e. Checking hostname.. etc)
            self.viewtext.notice("SERVER", remainder)
        elif isserver(prefix):
            # what if target at channel?
            self.viewtext.notice(prefix, remainder)
        elif self.channels.has_key(target):
            self.channels[target].notice(nick, remainder)
        elif self.queries.has_key(nick):
                self.queries[nick].notice(nick, remainder)
        elif self.cfg('client.use_msg_win'):
            msg = self.viewtext.get_msgwin()
            if msg:
                msg.notice(nick, remainder)
            else:
                self.viewtext.notice(nick, remainder)
        else: # create query
            self.queries[nick] = self.viewtext.create_query(nick)
            self.queries[nick].notice(nick, remainder)
        if prefix == "":
            # XXX Perhaps not log at all? Or log to special, per server, file
            log_target = 'SERVER'
        elif self.isme(target):
            log_target = nick
        else:
            log_target = target
        self.logger.log(log_target, "-%s- %s" % (nick, remainder))

    def irc_NICK(self, command, prefix, args):
        oldnick = getnick(prefix)
        newnick = args[-1]
        isme = self.isme(oldnick)

        if isme:
            self.serverState.nick = newnick
            # log this? Where?
        for name, chan in self.serverState.getChannels():
            if chan.getuser(oldnick):
                # XXX can this be done in viewtext.nickchange?
                self.channels[name].nickchange(oldnick, newnick)
                # pass the nickchange to model as well
                # as in ircView, it may be smarter to combine the 2 below
                chan.deluser(oldnick)
                chan.adduser(model.user(newnick))
                self.logger.log(name, "*** %s is now known as %s" % \
                                (oldnick, newnick))
        # Track nickchanges in querywindows
        self.viewtext.nickchange(oldnick, newnick, isme)
        if self.queries.has_key(oldnick):
            q = self.queries[oldnick]
            del self.queries[oldnick]
            # XXX move this to viewtext.nickchange as well?
            q.announce("%s is now known as %s" % (oldnick, newnick))
            self.queries[newnick] = q
            # perhaps log to newnick as well? Or perhaps not log at all?
            self.logger.log(oldnick, "*** %s is now known as %s" % \
                            (oldnick, newnick))
        else:
            msg = self.viewtext.get_msgwin(create=0)
            if msg:
                msg.nickchange(oldnick, newnick)

    def irc_MODE(self, command, prefix, args):
        """ MODE has several syntaxes I think """
        
        target = args[0]
        rest = args[1:]
        remainder = args[-1]
        nick = getnick(prefix)

        modechange = mode(rest)
        if self.channels.has_key(target):
            chanModel = self.serverState.getChannel(target)
            chanView = self.channels[target]

            #
            # TODO: Parse individual modes and call appropriate methods on 
            # channelview, instead of passing the entire mode change to 1 method
            chanView.modechange(nick, modechange)
            
            ###modechange.plusmodes(), 
            ###            modechange.minmodes(), modechange.plusparams(),
            ###                     modechange.minparams())

            #
            # Dict to map modechars to model modes
            modemap = { 'p':model.channel.MODE_PRIVATE,
                        's':model.channel.MODE_SECURE,
                        'n':model.channel.MODE_NOMSG,
                        't':model.channel.MODE_TOPIC,
                        'i':model.channel.MODE_INVITE }
            #
            # modes have been parsed, now analyze them and update model/view
            for i in range(len(modechange.plusmodes())):
                c = modechange.plusmodes()[i]
                if c == 'o':
                    nick = modechange.plusparam(i)
                    userModel = chanModel.getuser(nick)
                    m = userModel.setmode(model.user.MODE_OP)
                    chanView.usermodechange(nick, mode2char(m))
                elif c == 'v':
                    nick = modechange.plusparam(i)
                    userModel = chanModel.getuser(nick)
                    m = userModel.setmode(model.user.MODE_VOICE)
                    chanView.usermodechange(nick, mode2char(m))
                elif c == 'b':
                    chanModel.addban(modechange.plusparam(i))
                elif c == 'l':
                    # in this context, we can assume the limit is not ""
                    chanModel.setlimit(atoi(modechange.plusparam(i)))
                elif c == 'k':
                    # in this context, we can assume the key is not ""
                    chanModel.setkey(modechange.plusparam(i))
                elif c == 'I':
                    chanModel.addinvite(modechange.plusparam(i))
                elif c == 'e':
                    chanModel.addexcempt(modechange.plusparam(i))
                else:
                    if modemap.has_key(c):
                        chanModel.setmode(modemap[c])
                    # else warn for unknown channelmode?
            for i in range(len(modechange.minmodes())):
                c = modechange.minmodes()[i]
                if c == 'o':
                    nick = modechange.minparam(i)
                    userModel = chanModel.getuser(nick)
                    m = userModel.delmode(model.user.MODE_OP)
                    chanView.usermodechange(nick, mode2char(m))
                elif c == 'v':
                    nick = modechange.minparam(i)
                    userModel = chanModel.getuser(nick)
                    m = userModel.delmode(model.user.MODE_VOICE)
                    chanView.usermodechange(nick, mode2char(m))
                elif c == 'b':
                    chanModel.delban(modechange.minparam(i))
                elif c == 'l':
                    chanModel.setlimit(0)
                elif c == 'k':
                    chanModel.setkey("")
                elif c == 'I':
                    chanModel.delinvite(modechange.minparam(i))
                elif c == 'e':
                    chanModel.delexcempt(modechange.minparam(i))
                else:
                    if modemap.has_key(c):
                         chanModel.delmode(modemap[c])
                    # else warn for unknown channelmode?
        elif self.isme(nick):
            # The <:Test MODE Test :-i> form
            self.viewtext.modechange(nick, modechange)
        else:
            # is this likely?
            self.viewtext.announce("%s sets mode %s on %s" % \
                      (nick, join(rest, " "), target))
        ##
        ## For now, don't log user mode changes (i.e. VladDrac +i).
        ## channel - user mode changes are still logged.
        if not self.isme(target):
            self.logger.log(target, "*** %s sets mode %s on %s" % \
                      (nick, join(rest, " "), target))

    def irc_KICK(self, command, prefix, args):
        # can a kick be applied to multiple nicks in one message?
        target = args[0]
        nick = getnick(prefix)
        userhost = getuserhost(prefix)

        for i in args[1:-1]:
            if self.isme(i):
                # xchat saves channel - add to channelwindowpool?
                #self.channels[ircMsg.target].close()
                #del self.channels[ircMsg.target]
                self.channels[target].userkick(nick,
                     userhost, i, args[-1], isself=1)
                self.channels[target].part()
                self.serverState.getChannel(target).setstate(
                                                model.channel.STATE_KICKED)
                self.logger.log(target, 
                    "*** You have been kicked from %s by %s (%s): %s" % \
                    (target, nick, userhost, args[-1]))
                                
            else:
                self.channels[target].userkick(nick, userhost, i, args[-1])
                # remove user from model
                c = self.serverState.getChannel(target)
                c.deluser(i)
                self.logger.log(target, 
                 "*** %s has been kicked from %s by %s (%s): %s" % \
                 (i, target, nick, userhost, args[-1]))

    def irc_TOPIC(self, command, prefix, args):
        # :Vlads!^ivo@struis.intranet.amaze.nl TOPIC #foo :Foo Bar Blah

        #
        # We check our own list of channels - should we check Model instead?
        # we also alter model based on this..

        nick = getnick(prefix)

        if self.channels.has_key(args[0]):
            # you don't have to be on a channel to view it's topic.. (?)
            self.channels[args[0]].topic(args[-1], nick)
            self.serverState.getChannel(args[0]).settopic(args[-1])
            self.logger.log(args[0], "*** %s sets topic to %s"%(nick, args[-1]))

    def irc_QUIT(self, command, prefix, args):
        # is it me that quit?
        nick = getnick(prefix)
        userhost = getuserhost(prefix)

        for name, chan in self.serverState.getChannels():
            if chan.getuser(nick):
                chan.deluser(nick)
                self.channels[name].userquit(nick, prefix, args[-1])
                self.logger.log(name, "*** %s (%s) has quit (%s)" % \
                                (nick, userhost, args[-1]))
        # Track nickchanges in querywindows
        if self.queries.has_key(nick):
            self.queries[nick].announce("%s has quit (%s)" % (nick, args[-1]))
        else:
            msg = self.viewtext.get_msgwin(create=0)
            if msg:
                msg.hasquit(nick, prefix, args[-1])
        
    def irc_ERROR(self, command, prefix, args):
        self.viewtext.announce(args[-1])
        self.quit()
        self.do_clear()

    def irc_unknown(self, command, prefix, args):
        debug(ERROR, "Could not handle <%s %s %s>" % (command, prefix, args))
        self.viewtext.insert("%s %s %s" % (prefix, command, join(args)))

    def do_clear(self):
        """ reset all internal state (i.e. after disconnect) """
        #for name, chan in self.serverState.getChannels():
        #    if chan.getuser(ircMsg.nick):
        #        self.channels[name].userquit(ircMsg.nick, 
        #                       ircMsg.userhost, ircMsg.remainder)
        #        chan.deluser(ircMsg.nick)
        # close logging?
        pass

    def do_join(self, channel):
        """
            Invoked when *we* have joined a new channel
        """
        # check if we have a window with this name
        if self.channels.has_key(channel):
            newchan = self.channels[channel]
        else:
            newchan = self.viewtext.create_channel(channel)
            self.channels[channel] = newchan

        # check if channel available in model
        c = self.serverState.getChannel(channel)
        if not c:
             c = model.channel(channel)
        c.setstate(model.channel.STATE_ACTIVE)
        #
        # Request channelmodes for this channel
        self.irc.mode(channel)
        #
        # Request banlist as well
        self.irc.mode(channel, 'b')
        # Set 'awaiting 324 flag' in model?
        self.serverState.addChannel(c)
        #
        # Enable logging
        self.logger.new_channel(channel)

    irc_002 = show_main        # servername
    irc_003 = show_main        # created
    irc_004 = ignore           # servername/version/user/chanmodes

    irc_251 = show_main        # number of clients/services
    irc_252 = show_main        # number of operators online        
    irc_253 = show_main        # number of unknown connections
    irc_254 = show_main        # number of channels formed
    irc_255 = show_main        # local clients / servers

    # all kinds of stats replies. Let's hope we can just insert them
    irc_213 = show_main        # STATS C LINE
    irc_214 = show_main        # STATS N LINE
    irc_215 = show_main        # STATS I LINE
    irc_216 = show_main        # STATS K LINE
    irc_217 = show_main        # STATS Q LINE
    irc_218 = show_main        # STATS Y LINE
    irc_240 = show_main        # STATS V LINE
    irc_241 = show_main        # STATS L LINE
    irc_242 = show_main        # ?
    irc_243 = show_main        # ?
    irc_244 = show_main        # STATS H LINE
    irc_245 = show_main        # STATS S LINE
    irc_246 = show_main        # STATS PING
    irc_247 = show_main        # STATS B LINE
    irc_248 = show_main        # ?
    irc_249 = show_main        # ?
    irc_250 = show_main        # STATS D LINE
    
    irc_265 = show_main        # some gnome.org message
    irc_266 = show_main        # some gnome.org message

    irc_315 = ignore           # end of who list
    # "318":self.ignore,           # end of whois
    irc_366 = ignore           # rpl endofnames
    irc_368 = ignore           # rpl endofbanlist
    irc_369 = ignore           # end of whowas

    irc_372 = show_main        # rpl motd
    irc_375 = show_main        # motd start
    irc_376 = ignore           # motd end
