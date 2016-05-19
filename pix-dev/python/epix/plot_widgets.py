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

    def clear_data(self):
        """Abstract function to reset data in the widgets"""
        #print('abstract clear_data function called!')

        

class PlotWidget(QWidget):

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

    def clear_figure(self):
        """Clear figure and it's axes"""
        # clear figure with all it's axes
        self.fig.clear()
        # set axes to none to force it to redraw on next call
        self.ax = None
    

    def on_scale_slider(self, value):
        """Set new axis limits and clear the figure so that it get's updated on next call. 

        Ignore value and which wone that sent the update.
        """

        #print('[PlotWidget] : \"' + self.name + '\" on_scale_slider')
        if self.slider_zscale_min.value() < self.slider_zscale_max.value():
            self.zscale_min = self.slider_zscale_min.value()
            self.zscale_max = self.slider_zscale_max.value()
            self.textbox_zscale_min.setText(str(self.zscale_min))
            self.textbox_zscale_max.setText(str(self.zscale_max))

            self.clear_figure()
        
        else:
            print('[PlotWidget] : \"' + self.name + '\" WARNING z-scale is undefined min= ' + str(self.slider_zscale_min.value()) + ' max=' + str(self.slider_zscale_max.value()))


    def on_scale_text(self):
        """Set new axis limits and clear the figure so that it get's updated on next call. 
        """

        #print('[PlotWidget] : \"' + self.name + '\" on_scale_text')
        if int(self.textbox_zscale_min.text()) < int(self.textbox_zscale_max.text()):
            self.zscale_min = int(self.textbox_zscale_min.text())
            self.zscale_max = int(self.textbox_zscale_max.text())
            self.slider_zscale_min.setValue(self.zscale_min)
            self.slider_zscale_max.setValue(self.zscale_min)

            self.clear_figure()
        
        else:
            print('[PlotWidget] : \"' + self.name + '\" WARNING z-scale is undefined min= ' + str(self.slider_zscale_min.value()) + ' max=' + str(self.slider_zscale_max.value()))

        

    
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



    def create_zscale(self):
        """Abstract function"""
        return None
    


    def create_main(self):

        # main vertical layout
        vbox  = QVBoxLayout()

        # canvas horizontal layout
        hbox = QHBoxLayout()

        # create plot canvas
        #self.dpi = 100
        #self.fig = plt.Figure(figsize=(20, 20), dpi=150)
        self.fig = plt.Figure() #figsize=(10, 5), dpi=150)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.ax = None #self.fig.add_subplot(111)        
        self.img = None


        vbox_canvas = QVBoxLayout()
        vbox_canvas.addWidget( self.canvas )

        # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        
        vbox_canvas.addWidget( self.mpl_toolbar )

        hbox.addLayout( vbox_canvas)

        vbox_zscale = self.create_zscale()
        
        if vbox_zscale != None:
            hbox.addLayout(vbox_zscale)
        
        vbox.addLayout(hbox)



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

    def __init__(self, name, bins, parent = None, n_integrate = 1):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.bins =  bins
        self.y = np.zeros_like(bins)

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        #self.print_thread('new_data')
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
            #print('cl signal ' + str(cl.signal) + ' idx ' + str(idx))
        #x = [ (cl.signal) for cl in data ]
        self.n += 1
        if self.n >= self.n_integrate:
            #print('self.y')
            #print(self.y)
            self.emit(SIGNAL('data'), frame_id, self.y)
            self.n = 0
            #self.y.fill(0)
            self.y = np.zeros_like(self.bins)
        
        self.print_thread('new_data done')



class HistogramWidget(PlotWidget):

    def __init__(self, name, bins, parent=None, show=False, n_integrate = 1):
        PlotWidget.__init__(self,name, parent, show) 
        self.worker = HistogramWorker(self.name, bins, parent, n_integrate)
        self.worker.moveToThread( self.thread )
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.x = bins

    def on_draw(self, frame_id, y):

        self.print_thread('on_draw')
        #print('y')
        #print(y)
        #print('x')
        #print(self.x)
        

        t0 = time.clock()

        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)
            self.img, = self.ax.plot(self.x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')            
            self.txt = self.ax.text(0.1,0.8,'',transform=self.ax.transAxes)
            self.set_integration_text()
        else:
            self.img.set_ydata(y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)

        self.ax.set_title(self.title + ' id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        if len(self.x) > 0 and np.max(y) > 0:
            mean = np.average(self.x,axis=0,weights=y)
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


class CountHistogramWorker(PlotWorker):

    def __init__(self, name, bins, parent = None, n_integrate = 1):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.bins = bins
        self.y = np.zeros_like(self.bins)
    
    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        if data < len(self.y):
            self.y[data] += 1
        else:
            self.y[len(self.y) - 1] += 1            

        self.n += 1

        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.y)
            self.n = 0
            #self.y.fill(0)
            self.y = np.zeros_like(self.bins)

        self.print_thread('new_data DONE')


class CountHistogramWidget(PlotWidget):

    def __init__(self, name, bins, parent=None, show=False, n_integrate = 1):
        PlotWidget.__init__(self, name, parent, show)
        self.worker = CountHistogramWorker(self.name, bins, parent, n_integrate)
        self.worker.moveToThread( self.thread )
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.worker.print_thread('worker init')
        self.x = bins
    
    def on_draw(self, frame_id, y):

        self.print_thread('on_draw')
        #print('x')
        #print(x)
        #print('y')
        #print(y)
        t0 = time.clock()
        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)
            self.img, = self.ax.plot(self.x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')            
            #self.ax.set_xlabel('Cluster multiplicity', fontsize=14, color='black')
            #self.ax.set_ylabel('Arbitrary units', fontsize=14, color='black')
            self.txt = self.ax.text(0.2,0.8,'',transform=self.ax.transAxes)
            self.set_integration_text()

        else:
            self.img.set_ydata(y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' frame id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')

        if np.max(y) > 0:
            mean = np.average(self.x,axis=0,weights=y)
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

    def clear_data(self):
        """Clear the data object"""
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
            self.img = self.ax.imshow(self.d, vmin=self.zscale_min,vmax=self.zscale_max, interpolation='nearest', cmap='viridis')
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')
            self.fig.colorbar( self.img )
        else:
            self.d = data
            self.img.set_data( self.d )
            self.ax.set_title(self.title + ' id ' + str(frame_id) + ' (integrate ' + str(self.worker.n_integrate) + ', ' + str(self.n) + ' frames)')
            self.n += 1
            self.canvas.draw()

        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug:
            print('ImageWidget on_draw {0} frames with {1} sec/image'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.
    
    def create_zscale(self):
        
        vbox_zscale = QVBoxLayout()

        textbox_zscale_label = QLabel('z-scale')
        vbox_zscale.addWidget(textbox_zscale_label)
        
        hbox1_zscale = QHBoxLayout()
        hbox1_zscale.addWidget(QLabel('min'))
        hbox1_zscale.addWidget(QLabel('max'))
        vbox_zscale.addLayout(hbox1_zscale)


        # Create plot adjustments
        self.zscale_min = 0
        self.zscale_max = 500
        self.slider_zscale_min = QSlider(Qt.Vertical)
        self.slider_zscale_min.setRange(-16384,16384)
        self.slider_zscale_min.setValue(self.zscale_min)
        self.slider_zscale_min.setTickPosition(QSlider.TicksLeft)
        self.slider_zscale_min.setTickInterval(1000)
        self.slider_zscale_max = QSlider(Qt.Vertical)
        self.slider_zscale_max.setRange(-16384,16384)
        self.slider_zscale_max.setValue(self.zscale_max)
        self.slider_zscale_max.setTickPosition(QSlider.TicksBothSides)
        self.slider_zscale_max.setTickInterval(1000)
        self.zscale_min = self.slider_zscale_min.value()
        self.zscale_max = self.slider_zscale_max.value()
        # connect sliders to changes on GUI
        self.connect(self.slider_zscale_min, SIGNAL('sliderMoved(int)'), self.on_scale_slider)
        self.connect(self.slider_zscale_max, SIGNAL('sliderMoved(int)'), self.on_scale_slider)
        #self.connect(self.slider_zscale_min, SIGNAL('valueChanged(int)'), self.on_scale_slider)
        #self.connect(self.slider_zscale_max, SIGNAL('valueChanged(int)'), self.on_scale_slider)

        hbox2_zscale = QHBoxLayout()        
        hbox2_zscale.addWidget(self.slider_zscale_min)
        hbox2_zscale.addWidget(self.slider_zscale_max)
        vbox_zscale.addLayout(hbox2_zscale)

        self.textbox_zscale_min = QLineEdit()
        self.textbox_zscale_min.setMinimumWidth(50)
        self.textbox_zscale_min.setMaximumWidth(50)
        self.textbox_zscale_min.setText(str(self.zscale_min))
        self.textbox_zscale_max = QLineEdit()
        self.textbox_zscale_max.setMinimumWidth(50)
        self.textbox_zscale_max.setMaximumWidth(50)
        self.textbox_zscale_max.setText(str(self.zscale_max))
        
        self.connect(self.textbox_zscale_min, SIGNAL('editingFinished ()'), self.on_scale_text)
        self.connect(self.textbox_zscale_max, SIGNAL('editingFinished ()'), self.on_scale_text)

        hbox3_zscale = QHBoxLayout()        
        hbox3_zscale.addWidget(self.textbox_zscale_min)
        hbox3_zscale.addWidget(self.textbox_zscale_max)
        vbox_zscale.addLayout(hbox3_zscale)

        return vbox_zscale


class StripWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1, max_hist=100):    
        PlotWorker.__init__(self, name, parent, n_integrate)
        self.y = [] 
        for i in range(max_hist):
            self.y.append(0)
        self.max_hist = max_hist

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""
        self.print_thread('new_data')
        #print('StripWorker: process data ' + str(data))
        self.y.pop(0)
        self.y.append(data)
        self.n += 1

        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.y)
            self.n = 0
        self.print_thread('new_data DONE')
        

class StripWidget(PlotWidget):

    def __init__(self, name, parent=None, show=False, n_integrate = 1, max_hist=100):
        PlotWidget.__init__(self,name, parent, show)
        self.d = None
        self.worker = StripWorker(self.name, parent, n_integrate, max_hist)
        self.worker.moveToThread( self.thread )
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
            #print('x = ' + str(len(self.x)) + '  y = ' + str(len(y))) 
            self.img, = self.ax.plot(self.x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')
            self.set_integration_text()

        else:
            self.img.set_ydata(y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        self.canvas.draw()
        self.n += 1

        # timer stuff
        dt = time.clock() - t0
        self.t0sum += dt
        if self.n % 10 == 0:
            #if self.debug:
            print('StripWidget on_draw {0} frames with {1} sec/image'.format(self.n, self.t0sum/10.))
            self.t0sum = 0.
    
