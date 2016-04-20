#!/usr/bin/python

import sys
import os
import time
import datetime
import numpy as np
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from daq_worker import DaqWorker
from pix_threading import MyQThread

printThreadInfo = False


class PlotWorker(QObject):

    def __init__(self, name, parent = None, n_integrate = 1):    
        #QThread.__init__(self, parent)
        super(PlotWorker, self).__init__()
        self.exiting = False
        self.name = name
        self.n_integrate = n_integrate
        self.n = 0
        #self.start()


    def set_integration(self,n):
        self.n_integrate = n
    
    #def __del__(self):    
    #    self.exiting = True
    #    self.wait()

    def print_thread(self,msg):
        global printThreadInfo
        if printThreadInfo:
            print('[PlotWorker]: \"' + self.name + '\" ' + msg + ' in thread ' + str(QThread.currentThread()))

    def new_data(self,frame_id, data):
        """Abstract function"""
        print('abstract new_data function called!')

        

class PlotWidget(QWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, name, parent=None, show=False, n_integrate=1):
        QWidget.__init__(self,parent)
        self.name = name
        self.set_geometry()
        #self.create_menu()
        self.create_main()        
        self.n = 0
        self.t0sum = 0.
        self.debug = False
        self.x_label = ''
        self.y_label = ''
        self.title = self.name 
        self.txt = None
        self.txt_integration = None
        self.thread = MyQThread()
        self.thread.start()
        self.worker = None
        
        if show:
            self.show()
    

    def closeEvent(self, event):
        #self.emit(SIGNAL('on_quit'), self.name)
        print('[PlotWidget] : \"' + self.name + '\" closeEvent')
        self.thread.quit()
        can_exit = self.thread.wait(1000)        
        #can_exit = True
        if can_exit:
            print('[PlotWidget] : \"' + self.name + '\" thread quit successfully')            
            event.accept()
        else:
            print('[PlotWidget] : \"' + self.name + '\" thread quit timed out')
            self.thread.terminate()
            can_exit = self.thread.wait(1000)        
            if can_exit:
                print('[PlotWidget] : \"' + self.name + '\" thread terminated successfully')            
                event.accept()
            else:
                print('[PlotWidget] : ERROR \"' + self.name + '\" thread failed to die')
                #event.ignore()
    

    def set_integration_text(self):
        self.txt_integration = self.ax.text(0.1,0.9,'{0} frames integrated'.format(self.worker.n_integrate),transform=self.ax.transAxes)
    

    def print_thread(self,msg):
        global printThreadInfo
        if printThreadInfo:
            print('[PlotWidget]: \"' + self.name + '\" ' + msg + ' in thread ' + str(QThread.currentThread()))
    
    def set_x_label(self,s):
        self.x_label = s

    def set_y_label(self,s):
        self.y_label = s

    def set_title(self, s):
        self.title = s

    def set_integration(self,n):
        print('[PlotWidget]: set_integration to ' + str(n))
        if self.worker != None:
            self.worker.set_integration( n )
        self.set_integration_text()
    
    def set_geometry(self):
        self.setGeometry(10,10,500,500)
        self.setWindowTitle( self.name )
    
    
    def create_menu(self):        

        self.file_menu = self.menuBar().addMenu("&File")
        
        load_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        
        quit_action = self.create_action("&Quit",
            shortcut="Ctrl+Q", slot=self.close, 
            tip="Close the application")
        
        self.add_actions(self.file_menu, (quit_action,load_file_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About this thing')
        
        self.add_actions(self.help_menu, (about_action,))



    def create_main(self):

        vbox  = QVBoxLayout()

        #self.dpi = 100
        #self.fig = plt.Figure(figsize=(20, 20), dpi=150)
        self.fig = plt.Figure() #figsize=(10, 5), dpi=150)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.ax = None #self.fig.add_subplot(111)        
        self.img = None

         # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        vbox.addWidget( self.canvas )
        vbox.addWidget( self.mpl_toolbar )

        # create quit button
        #self.quit_button = QPushButton(self)
        #self.quit_button.setText('Close')
        #self.quit_button.clicked.connect(self.on_quit)
        #hbox = QHBoxLayout()
        #hbox.addWidget( self.quit_button )
        #hbox.addStretch(2)
        #vbox.addLayout( hbox )

        self.setLayout( vbox )






class HistogramWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.bins =  np.arange(0,6000,100)
        self.y = np.zeros_like(self.bins)

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        #print('HistogramWorker: new_data plot ' + str(len(data)) + ' cluster signals')
        # loop through clusters and fill histogram
        for cl in data:
            # find index closest to signal
            idx = np.abs(self.bins - cl.signal).argmin()
            # "fill histogram", check overflow
            if idx < len(self.bins):
                self.y[idx] += 1
            else:
                self.y[len(self.bins)-1] += 1
        #x = [ (cl.signal) for cl in data ]
        self.n += 1
        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.bins,self.y)
            self.n = 0
            self.y = np.zeros_like(self.bins)
        
        self.print_thread('new_data done')



class HistogramWidget(PlotWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, name, parent=None, show=False, n_integrate = 1):
        PlotWidget.__init__(self,name, parent, show) 
        self.worker = HistogramWorker(self.name, parent, n_integrate)
        self.worker.moveToThread( self.thread )
        #self.thread = HistogramWorker(self.name, None, n_integrate)
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.worker.print_thread('worker init')

    def on_draw(self, frame_id, x, y):

        self.print_thread('on_draw')

        t0 = time.clock()

        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)
            self.img, = self.ax.plot(x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')            
            #self.ax.set_xlabel('Cluster signal', fontsize=14, color='black')
            #self.ax.set_ylabel('Arbitrary units', fontsize=14, color='black')
            self.txt = self.ax.text(0.1,0.8,'',transform=self.ax.transAxes)
            #self.set_integration_text()
            print('got text ')
            print(self.txt)

        else:
            self.img.set_data(x,y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' frame id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        self.set_integration_text()
        if len(x) > 0 and np.max(y) > 0:
            mean = np.average(x,axis=0,weights=y)
            self.txt.set_text('mean {0:.1f}'.format(mean))

        self.canvas.draw()

        self.n += 1
        
        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug: 
            print('HistogramWidget on_draw {0} frames with {1} sec/histogram'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.


#    def on_draw(self, x):
#
#        t0 = time.clock()
#
#        self.x = x
#        if self.debug: print('plot on_draw xlen ' + str(len(self.x)) + ' binslen ' + str(len(self.bins)) )  
#        if len(self.x) > 0:
#            if self.ax == None:
#                self.ax = self.fig.add_subplot(111)
#            else:
#                self.ax.cla()
#                self.ax.hist(self.x, bins=self.bins, facecolor='green', alpha=0.75)
#                self.ax.set_title(str(self.n) + ' frames plotted')
#                self.ax.set_xlabel('Cluster signal (ADC)', fontsize=14, color='black')
#                self.ax.set_ylabel('Arbitrary units', fontsize=14, color='black')
#            self.canvas.draw()
#            self.n += 1
#        
#        # timer stuff
#        dt = time.clock() - t0
#        self.t0sum += dt
#        if self.n % 10 == 0:
#            #if self.debug: 
#            print('HistogramWidget on_draw {0} frames with {1} sec/histogram'.format(self.n, self.t0sum/10.))
#            self.t0sum = 0.
#



class CountHistogramWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.bins = np.arange(0,500)
        #self.x = np.zeros_like(self.bins)
        self.y = np.zeros_like(self.bins)
    
    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        #x = [ data for i in range(data) ]
        #print('[CountHistogramWorker] : histogram data ' + str(data))
        #print(x)
        # reset histogram
        # fill "histogram" , check overflow
        if data < len(self.y):
            self.y[data] += 1
        else:
            self.y[len(self.y) - 1] += 1            

        self.n += 1

        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.bins, self.y)
            self.n = 0
            self.y = np.zeros_like(self.bins)

        self.print_thread('new_data DONE')


class CountHistogramWidget(PlotWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, name, parent=None, show=False, n_integrate = 1):
        PlotWidget.__init__(self, name, parent, show)
        self.worker = CountHistogramWorker(self.name, parent, n_integrate)
        self.worker.moveToThread( self.thread )
        #self.thread = CountHistogramWorker(self.name, None, n_integrate)
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.worker.print_thread('worker init')
    
    def on_draw(self, frame_id, x, y):

        self.print_thread('on_draw')
        #print('x')
        #print(x)
        #print('y')
        #print(y)
        t0 = time.clock()
        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)
            self.img, = self.ax.plot(x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')            
            #self.ax.set_xlabel('Cluster multiplicity', fontsize=14, color='black')
            #self.ax.set_ylabel('Arbitrary units', fontsize=14, color='black')
            self.txt = self.ax.text(0.2,0.8,'',transform=self.ax.transAxes)
            #self.set_integration_text()

        else:
            self.img.set_data(x, y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' frame id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        self.set_integration_text()

        if len(x) > 0 and np.max(y) > 0:
            mean = np.average(x,axis=0,weights=y)
            self.txt.set_text('mean {0:.1f}'.format(mean))
        self.canvas.draw()
        self.n += 1
        
        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug: 
            print('[CountHistogramWidget] : on_draw {0} frames with {1} sec/histogram'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.





class ImageWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.d = None

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        #print('ImageWorker: process frame and send shape ' + str(np.shape(data)))
        if self.d == None:
            self.d = data
        else:
            self.d += data
        self.n += 1

        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.d)
            self.n = 0
            self.d = None

        self.print_thread('new_data DONE')
    

class ImageWidget(PlotWidget):

    def __init__(self, name, parent=None, show=False, n_integrate = 1):
        PlotWidget.__init__(self,name, parent, show)
        self.d = None
        self.worker = ImageWorker(self.name, parent, n_integrate)
        self.worker.moveToThread( self.thread )
        #self.thread = ImageWorker(self.name, None, n_integrate)
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.worker.print_thread('worker init')

    def on_draw(self, frame_id, data):

        self.print_thread('on_draw')
        
        t0 = time.clock()

        if self.ax == None:
            self.d = np.zeros_like( data ) # , dtype=np.int16 )
            self.ax = self.fig.add_subplot(1,1,1)
            self.img = self.ax.imshow(self.d, vmin=0,vmax=500, interpolation='nearest', cmap='viridis')
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')
            self.fig.colorbar( self.img )
        else:
            self.d = data
            self.img.set_data( self.d )
            self.ax.set_title(self.title + ' frame id ' + str(frame_id) + ' (integrate ' + str(self.worker.n_integrate) + ', ' + str(self.n) + ' frames)')
            self.n += 1
            self.canvas.draw()

        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug:
            print('ImageWidget on_draw {0} frames with {1} sec/image'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.
    


class StripWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1, max_hist=100):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        #self.x = []
        self.y = [] 
        for i in range(max_hist):
            self.y.append(0)
        self.max_hist = max_hist

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        #print('StripWorker: process data ' + str(data))
        if len(self.y) >= self.max_hist:
            self.y.pop(0)
            #self.x.pop(0)
        #if self.x:
        #    self.x.append( self.x[len(self.x)-1] + 1)
        #else:
        #    self.x.append(0)            
        self.y.append(data)
        self.n += 1

        if self.n >= self.n_integrate:
            #print('StripWorker: send x and y')
            #print (self.x)
            #print (self.y)
            self.emit(SIGNAL('data'), frame_id, self.y)
            self.n = 0
            #self.d = None
        self.print_thread('new_data DONE')
        

class StripWidget(PlotWidget):

    def __init__(self, name, parent=None, show=False, n_integrate = 1, max_hist=100):
        PlotWidget.__init__(self,name, parent, show)
        self.d = None
        self.worker = StripWorker(self.name, parent, n_integrate, max_hist)
        self.worker.moveToThread( self.thread )
        #self.thread = StripWorker(self.name, None, n_integrate, max_hist)
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.worker.print_thread('worker init')
        self.x = [] 
        for i in range(max_hist):
            self.x.append(i)

    def on_draw(self, frame_id, y):
        
        self.print_thread('on_draw')

        t0 = time.clock()
        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)

            print('x = ' + str(len(self.x)) + '  y = ' + str(len(y))) 
            self.img, = self.ax.plot(self.x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')
            #self.ax.set_xlabel('Time', fontsize=14, color='black')
            #self.ax.set_ylabel('Strip variable value', fontsize=14, color='black')
            #self.set_integration_text()

        else:
            #self.img.set_data(x, y)
            self.img.set_ydata(y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        self.set_integration_text()
        self.canvas.draw()
        self.n += 1

        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug:
            print('StripWidget on_draw {0} frames with {1} sec/image'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.
    
