# $Id: cfg.py,v 1.9 2001/10/09 22:19:57 ivo Exp $

"""
    Implementation of a globally shared cfg system

    Configurationfiles are stored in the order they're loaded. Each new 
    configuration 'inherits' the globals of the previous cfg, extends it
    (or replaces) with it's own locals and stores the own locals which
    can be stored back to the config later.
"""

#
# TODO: Implement storing of cfgs
#
# Ideas:
# - notify on change of attribute
# 
#
# Every class that uses the cfg class must initialize default values for the
# attributes it accesses to avoid name/attribute errors.

import sys
import os
from string import split

if sys.platform[:4] != 'java':
    import pwd
    home = pwd.getpwuid(os.getuid())[5]
else:
    import java
    home = java.lang.System.getProperty('user.home')

class single_cfg:
    def __init__(self, globals, name):
        self.globals = globals
        self.locals = {}
        self.name = name

    def load(self):
        execfile(self.name, self.globals, self.locals)
        # copy locals to globals
        for i in self.locals.keys():
            self.globals[i] = self.locals[i]

    # how about an empty attr? I.e. entire class?
    def find(self, clazz, attr):               # __hasattr__ ?
        return self.locals.has_key(clazz) and hasattr(self.locals[clazz], attr)

    def get(self, clazz, attr, default=None):
        if self.find(clazz, attr):
            return getattr(self.locals[clazz], attr)
            
        return default

    def store(self):
        """ store everything in 'locals' in 'self.name' """
        pass # not implemented 

class cfg:
    def __init__(self):
        self.globals = { 'home':home } # initialize with most dataset
        self.cfgs = []

    def load_home(self, rcname):
        """ load config 'name' from users homedir """
        # how about windows?
        file = home + "/" + rcname
        self.load(file)

    def load(self, name):
        new_cfg = single_cfg(self.globals, name)
        new_cfg.load() # this should update globals as well..
        self.cfgs.append(new_cfg)

    def __call__(self, itempath, defaultValue=None):
        (clazz, attr) = split(itempath, ".")
        # todo: support longer/deeper paths
        for i in range(len(self.cfgs)-1, -1, -1):
            if self.cfgs[i].find(clazz, attr):
                return self.cfgs[i].get(clazz, attr)
        return defaultValue
_cfg = None

def getCfg():
    global _cfg
    if not _cfg:
        _cfg = cfg()
    return _cfg
        
