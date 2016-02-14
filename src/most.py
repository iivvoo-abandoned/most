#!/usr/bin/python
##!/usr/local/python2.1/bin/python

# $Id: most.py,v 1.25 2002/03/26 14:46:20 ivo Exp $

import sys, os, string

from util import debug
from util.cfg import getCfg

from view import metaHandler
#
# TODO: install sigint handler to properly close

#
# Initially create model, view, controller(s)?
class most(metaHandler):
    def __init__(self):
	self.nick = "MostUser"
	self.ircname = "MOST irc, http://www.amaze.nl/~ivo/most/"
	self.ircserver = "127.0.0.1"
	self.ircport = 6667
	self.controllers = []
	#debug.current = debug.SILENT
	debug.current = debug.DEBUG

    def run(self):
        # load config?
	# load scripts?
        global_cfg = "../rc/mostrc"
        if os.environ.has_key('MOSTRC'):
            global_cfg = os.environ['MOSTRC']

        config = getCfg()
        try:
            config.load(global_cfg)
        except IOError:
            print "Failed to load global configuration file."
            print "Please set the MOSTRC environment variable appropriately."
            sys.exit()

        try:
            config.load_home(".mostrc")
        except IOError:
            print "Failed to load user configurationfile."

	if os.environ.has_key("IRCNICK"):
	    self.nick = os.environ["IRCNICK"]
	if os.environ.has_key("IRCNAME"):
	    self.ircname = os.environ["IRCNAME"]

	if os.environ.has_key("IRCSERVER"):
	    server = os.environ["IRCSERVER"]
            items = string.split(server, ":")
	    self.ircserver=items[0]
	    if len(items) > 1:
	        self.ircport = string.atoi(items[1])

        if len(sys.argv) > 1:
	    self.nick = sys.argv[1]
        if len(sys.argv) > 2:
	    server = sys.argv[2]
            items = string.split(server, ":")
	    self.ircserver=items[0]
	    if len(items) > 1:
	        self.ircport = string.atoi(items[1])


        # create main view. Importing must be done after initial loading of config 
        from view import ircView
        from controller import ircController, msnController

        ircView.parse_config()
	self.view = ircView.getIrcView()
	self.view.set_handler(self)

	c1 = ircController(self.ircserver)

        c1.run(config.globals['servers'].nick, self.ircname, 
	                    self.ircserver, self.ircport)
        c1.set_handler(self)
	self.controllers.append(c1)

        handle = config('msn.handle', None)
        password = config('msn.password', None)

        if handle and password:
            m1 = msnController(handle, password)
            m1.run()

	self.view.mainloop()

    def meta_close(self, source, text):
	debug.debug(debug.DEBUG, "QUIT")
	for c in self.controllers:
	    c.quit(text)
	debug.debug(debug.DEBUG, "ALL CONNECTIONS HAVE QUIT")
	self.view.mainquit()

    meta_quit = meta_close

    def meta_new(self, source, data):
        """ create a new (extra) connection """
        # don't init host/port
        host = data[0]
        if len(data) > 1:
            port = data[1]
        else:
            port = 6667
        from controller import ircController
	c = ircController(host)
	c.run(self.nick, self.ircname, host, port)
	c.set_handler(self)
	self.controllers.append(c)


def main():
    m = most()
    m.run()

if __name__ == '__main__':
    main()
