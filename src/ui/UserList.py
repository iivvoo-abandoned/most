# $Id: UserList.py,v 1.7 2002/02/04 08:15:25 ivo Exp $

"""
    Implementation of a userlist. Add sorting, mode and menucapabilities
    to a standard GtkList. Due to glade/gtk's nature, this class is implemented
    as a wrapper around an existing GtkList
"""

# sort orders / options
from gtk import GtkListItem
from string import lower
from util.debug import debug, DEBUG, NOTICE, ERROR

#
# Reorder by nickchange!
class UserList:
    def __init__(self, list):
        self.list = list
        self.items = []
        
    def adduser(self, name, mode=None):
        mode_char = ' '
        if mode:
            mode_char = mode
        item = GtkListItem("%c%s" % (mode_char, name))
        insert_at = -1
        for i in range(len(self.items)):
            if lower(name) <= lower(self.items[i][0]):
                insert_at = i
                break
        if insert_at == -1:
            self.items.append((name, item, mode))
            self.list.append_items([item])
        else:
            self.items.insert(i, (name, item, mode))
            self.list.insert_items([item], insert_at)
        item.show()
        return item

    def hasuser(self, name):
        for i in self.items:
            if lower(i[0]) == lower(name):
                return 1
        return 0

    def deluser(self, name):
        for i in self.items:
            if lower(i[0]) == lower(name):
                self.items.remove(i)
                self.list.remove_items([i[1]])
                return i
        debug(ERROR, "USER %s NOT FOUND IN" % name)
        debug(ERROR,  self.items)

    def nickchange(self, old, new):
        debug(DEBUG,  "Nickchange: %s -> %s" % (old, new))
        item = self.deluser(old)
        return self.adduser(new, item[2])

    def modechange(self, nick, mode):
        # Will this work correctly with selections?
        item = self.deluser(nick)
        return self.adduser(nick, mode)

    def clear(self):
        self.list.remove_items(map(lambda x: x[1], self.items))
        self.items = []
