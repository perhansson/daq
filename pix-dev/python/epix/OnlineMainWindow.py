import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import time
import numpy as np
import matplotlib.pyplot as plt
import epix_style
from pix_threading import MyQThread


class MainWindow(QMainWindow):

    __datadir = os.environ['DATADIR']

    def __init__(self, parent=None, debug=False):
        QMainWindow.__init__(self, parent)

        self.setWindowTitle(self.get_window_title())

        self.debug = debug
        #plt.ion()

        # run state 
        self.run_state = 'Undefined'

        # Selected ASIC
        # -1 if all of them
        self.select_asic = -1

        # timers
        self.t0_frame = None
        self.t0_frame_diff = -1.0

        # frame integration count
        self.integration_count = 1
        
        # counters
        self.nframes = 0

        # keep list to open plot widgets
        self.plot_widgets = []

        # data processor
        self.frame_processor = None

        # setup plot style
        epix_style.setup_color_map(plt)

        # GUI stuff        
        self.create_daq_worker_gui()
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

    def get_window_title(self):
        """Abstract method."""
        raise NotImplementedError

    def create_daq_worker_gui(self, daq_worker=None, show=False):                
        """Abstract method."""
        raise NotImplementedError
        
    def connect_daq_worker_gui(self, daq_worker):        
        """Connect the DAQ worker widget to it's worker."""
        if self.daq_worker_widget.daq_worker == None:
            self.daq_worker_widget.daq_worker = daq_worker            
        self.daq_worker_widget.connect_workers()
    
    def on_about(self):
        """Abstract method."""
        raise NotImplementedError

    def create_stat_view(self, vbox):
        """Abstract method."""
        raise NotImplementedError

    def create_options_view(self,vbox):
        """Abstract method."""
        raise NotImplementedError

    def create_main_frame(self):
        """This is the main widget."""

        self.main_frame = QWidget()

        # main vertical layot
        vbox = QVBoxLayout()

        # add stat box
        self.create_stat_view(vbox)

        # add control
        hbox_cntrl = QHBoxLayout()
        self.acq_button = QPushButton("&Acquire Start/Stop")
        self.connect(self.acq_button, SIGNAL('clicked()'), self.on_acq)
        self.quit_button = QPushButton("&Quit")
        self.quit_button.clicked.connect(self.on_quit)
        self.daq_button = QPushButton("&DAQ Control GUI")
        self.daq_button.clicked.connect(self.on_daq_control)
        hbox_cntrl.addWidget( self.acq_button)
        hbox_cntrl.addWidget( self.daq_button )        
        vbox.addLayout( hbox_cntrl )

        # add dark control
        hbox_dark = QHBoxLayout()
        textbox_dark_file_label = QLabel('Dark file:')
        self.textbox_dark_file = QLineEdit()
        self.textbox_dark_file.setMinimumWidth(200)
        self.connect(self.textbox_dark_file, SIGNAL('editingFinished ()'), self.on_dark_file_select)
        self.b_open_dark = QPushButton(self)
        self.b_open_dark.setText('Select dark file')
        self.b_open_dark.clicked.connect(self.showDarkFileDialog)
        self.b_open_daq_dark = QPushButton(self)
        self.b_open_daq_dark.setText('Get from DAQ control')
        self.b_open_daq_dark.clicked.connect(self.update_dark_file)
        hbox_dark.addWidget(self.b_open_daq_dark)
        hbox_dark.addWidget(self.b_open_dark)
        hbox_dark1 = QHBoxLayout()        
        hbox_dark1.addWidget(textbox_dark_file_label)
        hbox_dark1.addWidget(self.textbox_dark_file)
        vbox.addLayout(hbox_dark1)
        vbox.addLayout(hbox_dark)


        # add options
        self.create_options_view(vbox)


        # add plots
        self.create_plots_view(vbox)

        hbox_quit = QHBoxLayout()
        hbox_quit.addStretch(2)
        hbox_quit.addWidget( self.quit_button)                            
        
        vbox.addLayout( hbox_quit )

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


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


    def create_status_bar(self):
        self.status_text = QString('Run status: ' + self.run_state)
        #self.statusBar().addWidget(self.status_text, 1)
        self.statusBar().showMessage(self.status_text, 0)
    
    def newDataFrame(self,frame_id, data_frame):
        """ Receives new data frame"""

        # timer
        t_now = int(round(time.time() * 1000))
        if self.t0_frame == None:
            self.t0_frame = t_now
            self.t0_frame_diff = -1
        else:
            self.t0_frame_diff = t_now - self.t0_frame
            self.t0_frame = t_now

       # print('[MainWindow]: newDataFrame frame_id ' + str(frame_id) + ' t_now ' + str(t_now) + ' (' + str(self.t0_frame_diff) + ')')

        #QApplication.processEvents()

        # calculate the rate
        if self.t0_frame_diff == 0:
            rate = -1
        else :
            rate = 1000.0/float(self.t0_frame_diff)

        # update stat counters
        self.updateStats(frame_id, rate, self.nframes)

        # update frame counter
        self.nframes += 1

        QApplication.processEvents()



    def updateStats(self, i, rate, n):
        """Update stat boxes."""
        self.textbox_frameid.setText(str(i))
        self.textbox_framerate.setText('{0:.1f}Hz'.format(rate))
        self.textbox_frameprocessed.setText(str(self.nframes))
    
    def newState(self,state_str):
        self.run_state = state_str
        #update GUI
        self.statusBar().showMessage('Run status: ' + self.run_state)
    

    def on_pick(self, event):
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on something with coords:\n %s" % box_points        
        QMessageBox.information(self, "Click!", msg)


    def send_busy(self, flag):
        if self.debug: print('[MainWindow]: send busy ' + str(flag))
        self.emit(SIGNAL("formBusy"), flag)

    def on_acq(self):
        """ Start or stop the acquisition of data"""
        if self.debug: print('[MainWindow]: on acq')
        self.emit(SIGNAL("acqState"),1)
        
    def on_dark_file_select(self):
        #if self.debug: 
        print('[MainWindow]:  on_dark_file_select')
        t = self.textbox_dark_file.text()
        if t == '':
            print('[MainWindow]:  no dark file selected')
            return
        self.emit(SIGNAL('createDarkFile'), str(t), 100, 'median')
        print('[MainWindow]:  should have created dark file')
        self.emit(SIGNAL('readDarkFile'), str(t))

    def connect_function(self, sig, fnc):
        """Dummy function that doesn't really do anything."""
        self.connect(self, sig, fnc)
    
    def closeEvent(self, event):
        """Close the GUI."""
        can_exit = True
        self.on_quit()
        if can_exit:
            event.accept()
        else:
            event.ignore()

    def on_quit(self):
        """Quit the main window."""
        print('[MainWindow]: on_quit')        
        self.daq_worker_widget.close()
        print('[MainWindow]: kill daq_worker thread')        
        self.daq_worker_widget.quit_worker_thread()            
        print('[MainWindow]: quit ' + str(len(self.plot_widgets)) + ' widgets')
        for w in self.plot_widgets:
            w[0].close()
        self.close()
    
    def on_daq_control(self):
        self.daq_worker_widget.show()
    
    def showDarkFileDialog(self):
        """Open file dialog to select a dark file."""
        # select via dialog
        file_name = QFileDialog.getOpenFileName(self,'Open dark file',self.__datadir)

        # set the textbox
        self.textbox_dark_file.setText(file_name)

        # use the "button" click function to actually apply
        self.on_dark_file_select()
    

    def update_dark_file(self):
        """Update the dark file used."""

        # update from the DAQ worker GUI if it's not empty and different than the one we have
        t = self.daq_worker_widget.textbox_dark_file.text()
        if t != self.textbox_dark_file.text() and str(t) != '':
            print('[MainWindow]: update dark file to \"' + str(t) + '\" (prev was \"' + str(self.textbox_dark_file.text()) + '\")')
            self.textbox_dark_file.setText(t)
            self.on_dark_file_select()    

    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    

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
