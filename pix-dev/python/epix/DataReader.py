import sys, os, csv
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#import pythonDaq
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

    def newDataFrame(self,data):

        frame = EpixFrame(data)
        
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

