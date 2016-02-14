"""
    basic window containing textarea for output and textfield for input,
    includes handling of commands.
"""

# $Id: awtWindow.py,v 1.3 2001/10/12 16:05:28 ivo Exp $

from java.awt import *
from java.awt.event import *

from string import *
from view import guiMessage

class awtWindow(Frame, ActionListener):
    def __init__(self):
        Frame.__init__(self)
        self.setLayout(BorderLayout())
        self.setFont(Font("Helvetica", Font.PLAIN, 10))

        self.ta = TextArea("", 10, 60, TextArea.SCROLLBARS_VERTICAL_ONLY)
        self.ta.enableInputMethods(0)
        self.tf = TextField(60)

        self.add("Center", self.ta)
        self.add("South", self.tf)

        self.tf.addActionListener(self)

        self.pack()
        self.show()

    def actionPerformed(self, e):
        text = self.tf.getText()
        self.tf.setText("")

        if strip(text) != "":
            if text[0] == '/':
                event = guiMessage.guiMessage(text[1:])
            else:
                event = guiMessage.guiMessage()
                event.type = guiMessage.MSG
                if hasattr(self, 'name'):
                    event.source = self.name
                    event.target = self.name # This should invoke some method
                event.data = text
        
            if self.handler:
                self.handler(self, event)

    def write(self, msg):
        self.ta.appendText(msg + "\n")
        # really large, but will fail eventually..
        self.ta.setCaretPosition(9999999) 

    def run(self):
        self.pack()
        self.show()
