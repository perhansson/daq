#!/usr/bin/python

from PyQt4.QtCore import QThread

class MyQThread(QThread):
    """Only needed for Qt 4.6"""
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
    def start(self):
        QThread.start(self)
    def run(self):
        QThread.run(self)

