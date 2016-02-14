# $Id: debug.py,v 1.2 2001/08/04 13:23:46 ivo Exp $

"""
    Debugging support for MOST
"""

SILENT = 0
ERROR = 10
NOTICE = 50
DEBUG = 100
current = SILENT

map = { SILENT:'SILENT', 
        ERROR:'ERROR',
        NOTICE:'NOTICE',
        DEBUG:'DEBUG' }
#
# TODO:
#
# - redirect output to logfile

def debug(priority, str):
    if current >= priority:
        print "[%s] %s" % (map[priority], str)
