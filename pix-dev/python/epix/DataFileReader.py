import sys, os, csv
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
#import matplotlib.pyplot as plt
from frame import EpixFrame

class DataFileReader(QThread):
    def __init__(self,filename, parent=None):
        QThread.__init__(self,parent)
        self.filename = filename
        self.start()
        
        
    def run(self):

        print('DataFileReader filename ', self.filename)

        n = 0
        n_frames = 0
        with open(self.filename,'rb') as f:
            try:
                while True:
                    # read one word from file
                    fs = np.fromfile(f, dtype=np.uint32, count=4)[0]
                    n += 1
                    # read the data
                    ret = np.fromfile(f, dtype=np.uint32, count=(4*fs) )
                    #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                    if fs == EpixFrame.framesize:
                        print ('Read ', n, ': got a frame length from file ', self.filename, ': ', fs)
                        n_frames += 1
                        self.emit(SIGNAL("newDataFrame"),ret) #[1:len(ret)])
                    else:
                        print('Read ', n, ': Got weird size from file fs ', fs , ' ret ', ret)
                    
                    # update for next read
                    #f.seek(4*fs, 1)
                    #f.seek(4*n_seek, 1)
                    #print('sleep')
                    time.sleep(1.0)
                    #ans = raw_input('Press \'n\' to quit, anything to continue')
                    #if ans == 'n':
                    #    break
            except IndexError:
                print(' - read ', n, ' times and got ', n_frames,' frames from file')
    
        





class EsaEpixForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('ePix ESA Live Display')

        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        self.textbox.setText('1 2 3 4')
        self.on_draw()



    def on_about(self):
        msg = """ ESA ePix online display
        """
        QMessageBox.about(self, "About the app", msg.strip())


    def on_pick(self, event):
        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent
        #
        # It carries lots of information, of which we're using
        # only a small amount here.
        # 
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points
        
        QMessageBox.information(self, "Click!", msg)



    def on_draw(self):
        """ Redraws the figure
        """
        str = unicode(self.textbox.text())
        self.data = map(int, str.split())
        
        x = range(len(self.data))

        # clear the axes and redraw the plot anew
        #
        self.axes.clear()        
        self.axes.grid(self.grid_cb.isChecked())
        
        self.axes.bar(
            left=x, 
            height=self.data, 
            width=self.slider.value() / 100.0, 
            align='center', 
            alpha=0.44,
            picker=5)
        
        self.canvas.draw()


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
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)
        
        # Bind the 'pick' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls
        # 
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)
        
        self.draw_button = QPushButton("&Draw")
        self.connect(self.draw_button, SIGNAL('clicked()'), self.on_draw)
        
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
        
        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()
        
        for w in [  self.textbox, self.draw_button, self.grid_cb,
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


class Form(QMainWindow):
    def __init__(self, period, parent=None):
        super(Form, self).__init__(parent)
        self.period = period
        self.lastTime = time.time()
        self.n = 0
        self.frame = None
        self.imgA = None
        self.figA = None
        self.axesA = None
        self.canvasA = None

        self.setWindowTitle('EPIX100a Live Frames')

        self.main_frame = QWidget()
        
        self.dpi = 100

        self.make_fig(None)

        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvasA)
        #vbox.addWidget(self.canvasB)

        self.main_frame.setLayout(vbox)

        self.setCentralWidget(self.main_frame)

        #self.plotDataA = None
        #self.plotDataB = None
        self.on_show()

    def make_fig(self,data):
        if self.figA:
            self.figA.clf()
        else:
            self.figA = Figure((6.0, 4.0), dpi=self.dpi)
            self.canvasA = FigureCanvas(self.figA)
            self.canvasA.setParent(self.main_frame)
        self.axesA = self.figA.add_subplot(111)
        if data != None:
            self.imgA = self.axesA.imshow(data)
            self.figA.colorbar(self.imgA)
        self.axesA.set_title('Frame ' + str( self.n ) ) 
    

    def newDataFrame(self,data):

        print('newDataFrame with data ', data, ' of length ', len(data))

        self.frame = EpixFrame(data)

        #self.plotDataA = frame.super_rows
        #self.plotDataB = frame.super_rows[1]

        if time.time() - self.lastTime > self.period:
           self.lastTime = time.time()
           self.on_show()

        # update frame counter
        self.n += 1


    def on_show(self):
        #self.axesA.clear()        
        #self.axesB.clear()        
        #self.axesA.grid(False)
        #self.axesB.grid(True)
        
        
        
        if self.frame != None:
            print 'make fig'
            self.make_fig(self.frame.super_rows)
            self.canvasA.draw()
            print ('')
            #if self.imgA:
            #    print 'update img'
            #    # frame is just updating
            #    self.imgA.set_data(self.frame.super_rows)
            #    self.imgA.autoscale()
            #else:
            #    # create a new image
            #    print 'create img'
            #    self.imgA = self.axesA.imshow(self.frame.super_rows)
            #    self.figA.colorbar(self.imgA)
            #    self.axesA.set_title('Frame ' + str( self.n ) )            
            #    self.canvasA.draw()
            
            #print 'create img'
            #self.figA.clf()
            #self.axesA.clear()
            #self.imgA = self.axesA.imshow(self.frame.super_rows)
            #self.figA.colorbar(self.imgA)
            #self.axesA.set_title('Frame ' + str( self.n ) )            
            #self.canvasA.draw()
            #if self.plotDataA:
            #self.axesA.plot(self.plotDataA)
            #objA = self.axesA.imshow(self.frame.super_rows,vmin=0,vmax=2,interpolation='nearest',cmap='viridis')
            #if self.plotDataB:
            #self.axesB.plot(self.plotDataB)
            #self.canvasA.draw()
            #self.canvasB.draw()
