class msgSupport:
    def __init__(self):
        pass

    def insert(self, msg):
        self.write(msg)

    def msg(self, nick, msg, isme = 0):
        self.write("<%s> %s" % (nick, msg))

    def notice(self, nick, msg, isme = 0):
        self.write("-%s- %s" % (nick, msg))

    def action(self, nick, msg, isme = 0):
        self.write("-> %s %s" % (nick, msg))

    def announce(self, msg):
        self.write("*** " + msg)

    def sendmsg(self, nick, msg):
        """ insert a message *to* someone """
        self.write("-> <%s> %s" % (nick, msg))

    def sendaction(self, nick, target, msg):
        """ insert a message *to* someone """
        self.write("-> <%s> %s %s" % (target, nick, msg))

    def write(self, msg):
        print msg

