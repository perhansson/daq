#!/usr/bin/env python
##############################################################################
## This file is part of 'LCLS2 LLRF Test Software'
## It is subject to the license terms in the LICENSE.txt file found in the
## top-level directory of this distribution and at:
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
## No part of 'LCLS LLRF Test Software', including this file,
## may be copied, modified, propagated, or distributed except according to
## the terms contained in the LICENSE.txt file.
##############################################################################

import sys, os, csv
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pythonDaq
import time

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
#import matplotlib.pyplot as plt

class DataReader(QThread):
   def __init__(self, parent=None):
      QThread.__init__(self,parent)
      self.start()

   def run(self):

      pythonDaq.daqSharedDataOpen("epix",1);

      while True:
      
         ret = pythonDaq.daqSharedDataRead();
         if ret[0] > 0:
            #print ret
            if ret[0] != 272651:
               print ret[0]
         if ret[0] == 0:
             time.sleep(.001)
         elif ret[1] == 0:
             self.emit(SIGNAL("newData"),ret[2])
         else:
            print "Got %i %i" % (ret[0],ret[1])

class Form(QMainWindow):
    def __init__(self, period, parent=None):
        super(Form, self).__init__(parent)
        self.period = period
        self.lastTime = time.time()

        self.setWindowTitle('EPIX100a Live ADC Data')

        self.main_frame = QWidget()
        
        self.dpi = 100

        self.figA = Figure((6.0, 4.0), dpi=self.dpi)
        self.canvasA = FigureCanvas(self.figA)
        self.canvasA.setParent(self.main_frame)

        self.figB = Figure((6.0, 4.0), dpi=self.dpi)
        self.canvasB = FigureCanvas(self.figB)
        self.canvasB.setParent(self.main_frame)

        self.axesA = self.figA.add_subplot(111)
        self.axesB = self.figB.add_subplot(111)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvasA)
        vbox.addWidget(self.canvasB)

        self.main_frame.setLayout(vbox)

        self.setCentralWidget(self.main_frame)

        self.plotDataA = None
        self.plotDataB = None
        self.on_show()

    def newData(self,data):
        newVal = []
        newVal1 = []
        
        #print data[len(data)-2]
        #print data[len(data)-1]

        #for val in data[8:len(data)-384*2-3]:
        
        #4 super rows in two datasets to plot
        for val in data[8:8+384*2]:
            newVal.append((val >> 16) & 0xFFFF)
            newVal.append(val & 0xFFFF)
        for val in data[8+384*2:8+384*4]:
            newVal1.append((val >> 16) & 0xFFFF)
            newVal1.append(val & 0xFFFF)

        if data[0] == 0:
           self.plotDataA = newVal
           self.plotDataB = newVal1
        else:
           print "Unknown frame"

        if time.time() - self.lastTime > self.period:
           self.lastTime = time.time()
           self.on_show()

    def on_show(self):
        self.axesA.clear()        
        self.axesB.clear()        
        self.axesA.grid(True)
        self.axesB.grid(True)

        if self.plotDataA:
            self.axesA.plot(self.plotDataA)
        if self.plotDataB:
            self.axesB.plot(self.plotDataB)
        self.canvasA.draw()
        self.canvasB.draw()

def main():
    app = QApplication(sys.argv)
    form = Form(0.1)
    form.show()
    dread = DataReader()
    form.connect(dread,SIGNAL('newData'),form.newData)
    app.exec_()

if __name__ == "__main__":
    main()
    
