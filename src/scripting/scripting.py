#!/usr/bin/python

"""
    Implementation of a scripting interface for most

"""

# $Id: scripting.py,v 1.1 2002/02/25 17:52:09 ivo Exp $

import os
import sys
import traceback
from util.debug import *
from StringIO import StringIO

class scripting:
    def __init__(self):
        self.scriptdir = "scripts"
        self.scripts = []

    def rescan(self):
        # loosely based on Zope's import mechanism
        raise_exc = 1
        global_dict=globals()
        silly=('__doc__',)

        exists = os.path.exists
        path_join = os.path.join

        for i in os.listdir(self.scriptdir):
            self.scripts.append(i)
        self.scripts.sort()

        for i in self.scripts:
            script_dir = path_join(self.scriptdir, i)
            if not os.path.isdir(script_dir):
                continue
            if not exists(path_join(script_dir, '__init__.py')) and \
               not exists(path_join(script_dir, '__init__.pyc')) and \
               not exists(path_join(script_dir, '__init__.pyo')):
                continue

            pname = "scripts.%s" % i

            try:
                product=__import__(pname, global_dict, global_dict, silly)
            except:
                exc = sys.exc_info()
                debug(ERROR, 'Could not import %s: %s' % (pname, exc))
                f=StringIO()
                traceback.print_exc(100,f)
                f=f.getvalue()
                if raise_exc:
                    raise exc[0], exc[1], exc[2]


if __name__ == '__main__':
    s = scripting()
    s.rescan()
