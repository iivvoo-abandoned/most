"""
   Logging facilities for most
"""

# $Id: Log.py,v 1.7 2001/11/29 12:09:18 ivo Exp $

import os, sys

from util.casedict import casedict
from util.cfg import getCfg
from util.debug import debug, DEBUG, NOTICE, ERROR

from time import time, ctime
from string import lower
#
# Make loggin of notices optional (but that's handled elsewhere anyway)
#
# Timestamping?
#
# Define Source, Target, Params, Remainder?
# define logtypes, on which can be filtered (i.e. log privmsg, action, etc, but
# no CTCP, DCC, WHOIS)
# How about concurrency? Two threads (connections) connected to the same server
# (weird situation, but still)

class Channel:
    def __init__(self, name, filename, use_timestamp=0):
        self.name = name
        self.filename = filename
        self.file = None
        self.linecount = 0              # number of unflushed lines
        self.cfg = getCfg()
        self.use_timestamp = use_timestamp

    def open(self):
        """ open file, write date """
        self.file = open(lower(self.filename), "a+")
        self.file.write("Log starting at %s\n" % ctime(time()))
        
    def __del__(self):
        self.close()

    def close(self):
        """ write date, close file """
        if self.file:
            self.file.write("Log ending at %s\n" % ctime(time()))
            self.file.close()
            self.file = None

    def log(self, msg):
        """ log message, optionally with timestamp """
        if self.file:
            if self.use_timestamp:
                self.file.write("%s [%s]" % (msg, ctime(time())))
            else:
                self.file.write("%s\n" % msg)
            self.linecount = self.linecount + 1
            c = self.cfg("logging.flush_after_lines", 0)
            if c and self.linecount >= c:
                self.file.flush()
                self.linecount = 0
              
    

class Log:
    def __init__(self, handle):
        self.handle = handle
        self.channels = casedict()      # logging channels, not irc channels
        self.cfg = getCfg()
        self.disabled = 0               # disabled for whatever reason
        self.reset()

    def new_channel(self, channel):
        if self.disabled:
            return None

        chan = self.channels.get(channel, None)
        if not chan:
            chan = Channel(channel, "%s/%s" % \
                           (self.cfg("logging.log_base"), channel))
            chan.open()
            self.channels[channel] = chan
        return chan

    def close_channel(self, channel):
        # closing is ok, even if logging is disabled.
        chan = self.channels.get(channel, None)
        if chan:
            chan.close()
            del self.channels[channel]

    def log(self, channel, msg):
        if self.disabled:
            return
        chan = self.new_channel(channel)
        chan.log(msg)

    def close(self):
        """ close all channels """
        for i in self.channels.keys():
            self.close_channel(i)

    def reset(self):
        path = self.cfg("logging.log_base")
        if os.path.isdir(path):
            if sys.platform[:4] == 'java':
                import java
                if java.io.File(path).canWrite():
                    self.disabled = 0
                else:
                    self.disabled = 1
            elif os.access(path, os.W_OK):
                self.disabled = 0
            else:
                self.disabled = 1
                debug(ERROR, "%s is not a writable directory - logging disabled" % path)
        else:
            self.disabled = 1
            debug(ERROR, "%s is not a directory - logging disabled" % path)
