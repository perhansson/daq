#!/usr/bin/python

import sys
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from daq_worker import DaqWorker

class PlotWidget(QWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, name, parent=None, show=False):
        QWidget.__init__(self,parent)
        self.name = name
        self.set_geometry()
        #self.create_menu()
        self.create_main()        
        if show:
            self.show()
    
    

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
        
        #self.add_actions(self.file_menu, 
        #    (load_file_action, None, quit_action))
        
        self.add_actions(self.file_menu, (quit_action,load_file_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About this thing')
        
        self.add_actions(self.help_menu, (about_action,))



    def create_main(self):

        vbox  = QVBoxLayout()

        self.dpi = 100
        #self.fig = plt.Figure(figsize=(20, 20), dpi=150)
        self.fig = plt.Figure() #figsize=(10, 5), dpi=150)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.ax = None #self.fig.add_subplot(111)        
        self.img = None

        self.bins = np.arange(0,6000,100)
        self.x = np.zeros(len(self.bins),dtype=np.int16)


         # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        vbox.addWidget( self.canvas )
        vbox.addWidget( self.mpl_toolbar )
        
        self.setLayout( vbox )

    
    def new_data(self, frame):
        print('plot ' + str(len(frame.clusters)) + ' cluster signals')
        self.x = [ (cl.signal) for cl in frame.clusters ]
        #mu, sigma = 100, 15
        #x = mu + sigma * np.random.randn(10000)
        self.on_draw()

    def on_draw(self):
        print('plot on_draw xlen ' + str(len(self.x)) + ' binslen ' + str(len(self.bins)) )  
        if len(self.x) > 0:
            #print(self.x)
            #print(self.bins)
            #self.n, self.bins, self.patches = self.ax.hist(x, 50, normed=1, facecolor='g', alpha=0.75        
            if self.ax == None:
                self.ax = self.fig.add_subplot(111)
            else:
                self.ax.cla()
                #self.ax.hist(self.x, facecolor='green', alpha=0.75)
                self.ax.hist(self.x, bins=self.bins, facecolor='green', alpha=0.75)
                self.ax.set_xlabel('Cluster signal (ADC)', fontsize=14, color='black')
                self.ax.set_ylabel('Arbitrary units', fontsize=14, color='black')
                #self.img.set_data(self.x)
                #self.ax.hist(self.x, bins=self.bins, facecolor='green', alpha=0.75)
                #self.n, self.bins, self.patches = self.ax.hist(x, 50, facecolor='green', alpha=0.75)
                #plt.show()
            self.canvas.draw()
