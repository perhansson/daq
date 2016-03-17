import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import numpy as np
from frame import EpixFrame



class EpixEsaForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('ePix ESA Live Display')

        # hold data
        self.frame = None

        # counter
        self.nframes = 0

        # period to update plots in second, None if not used
        self.period = None

        # GUI stuff
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        self.textbox.setText('Initializing...')

        # image to be displayed
        self.img = None

        self.on_draw()

        

    def newDataFrame(self,data_frame):
        """ Receives new data and creates a new frame"""

        print('newDataFrame')

        self.frame = data_frame #EpixFrame( data )
        self.nframes += 1

        
        # if a period is set, use that to determine when to update plots
        if self.period:
            if time.time() - self.lastTime > self.period:
                self.lastTime = time.time()
                self.on_draw()
        # otherwise try to update plots whenever there is new data
        else:
            print('draw it')
            self.on_draw()
            
    def on_about(self):
        msg = """ ESA ePix online display
        """
        QMessageBox.about(self, "About the app", msg.strip())


    def on_pick(self, event):
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on something with coords:\n %s" % box_points        
        QMessageBox.information(self, "Click!", msg)


    def on_acq(self):
        """ starts or stop the acquisition of data"""
        print('on acq')
        self.emit(SIGNAL("acqState"),1)
    
    def on_draw(self):
        """ Redraws the figure
        """

        if self.frame != None:

            print ('on_draw data len ', len( self.frame.super_rows ))

            # data to be plotted
            data = self.frame.super_rows #self.frame.super_rows[:3,:3]

            #data = np.mean( data2, axis=1)
            print ('data ', data)
            
            # update status
            self.textbox.setText('Redrawing figure')

            self.axes.grid(self.grid_cb.isChecked())
            self.axes.set_title('Frame ' + str( self.nframes ) );

            #self.axes.plot(data)
            
            if self.img:
                self.img.set_data( data )
            else:
                self.axes.clear()        
                self.img = self.axes.imshow( data, interpolation='none' )
            
            self.canvas.draw()
            print ('done drawing')
            self.textbox.setText('Figure updated with data from frame ' + str( self.nframes ))
        
        else:
            self.textbox.setText('No data available, frames processed: ' + str( self.nframes ))
    

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


    def create_main_frame(self):
        self.main_frame = QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = plt.Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        # add a plot
        self.axes = self.fig.add_subplot(111)
        
        # Bind the 'pick' event for clicking on the plot         
        self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)
        
        self.acq_button = QPushButton("&Acquire Start/Stop")
        self.connect(self.acq_button, SIGNAL('clicked()'), self.on_acq)
        
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)
        
        slider_label = QLabel('Bar width (%):')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(20)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.on_draw)
        
        
        # Layout with box sizers         
        hbox = QHBoxLayout()
        
        for w in [  self.textbox, self.acq_button, self.grid_cb,
                    slider_label, self.slider]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    
    def create_status_bar(self):
        self.status_text = QLabel("This is a status text")
        self.statusBar().addWidget(self.status_text, 1)


    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
