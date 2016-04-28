import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from frame import EpixFrame
from plots import EpixPlots, EpixPlot
import epix_style
from pix_utils import FrameAnalysisTypes
from daq_worker_gui import *
from plot_widgets import *
from pix_threading import MyQThread


class EpixEsaMainWindow(QMainWindow):

    __datadir = '/home/epix/data'

    def __init__(self, parent=None, debug=False):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('ePix ESA Live Display')

        self.debug = debug
        #plt.ion()

        # run state 
        self.run_state = 'Undefined'

        # Selected ASIC
        # -1 if all of them
        self.select_asic = -1

        # timer
        self.__t0_sum = 0.
        self.t0_frame = None
        self.t0_frame_diff = -1.0

        self.integration_count = 1
        
        # hold latest data frame
        self.last_frame = None

        # counters
        self.nframes = 0

        # period to update plots in second, None if not used
        self.period = None

        # setup plot style
        epix_style.setup_color_map(plt)

        # GUI stuff        
        self.create_daq_worker_gui()
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        # keep references to the open plot widgets
        self.plot_widgets = []

        # data processor
        self.frame_processor = None

        # text box to display messages
        self.textbox.setText('Uninitialized...')




    def create_daq_worker_gui(self, daq_worker=None, show=False):                
        # create the widget
        self.daq_worker_widget  = DaqWorkerWidget()
        # add the daq connection
        if daq_worker != None:
            self.connect_daq_worker_gui(daq_worker)
        

    def connect_daq_worker_gui(self, daq_worker):        
        self.daq_worker_widget.connect_workers( daq_worker )
    
    

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

       # print('[EpixEsaMainWindow]: newDataFrame frame_id ' + str(frame_id) + ' t_now ' + str(t_now) + ' (' + str(self.t0_frame_diff) + ')')

        #QApplication.processEvents()

        if self.t0_frame_diff == 0:
            rate = -1
        else :
            rate = 1000.0/float(self.t0_frame_diff)
        self.textbox.setText('Processed frame {0} ( {1:.1f}msec/{2:.1f}Hz,  processed {3})'.format(frame_id,self.t0_frame_diff, rate, self.nframes ))

        self.nframes += 1

        QApplication.processEvents()


    def newState(self,state_str):
        self.run_state = state_str
        #update GUI
        self.statusBar().showMessage('Run status: ' + self.run_state)
    
    def on_about(self):
        msg = """ ESA ePix online display."""
        QMessageBox.about(self, "About the app", msg.strip())


    def on_pick(self, event):
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on something with coords:\n %s" % box_points        
        QMessageBox.information(self, "Click!", msg)


    def send_busy(self, flag):
        if self.debug: print('[EpixEsaMainWindow]: send busy ' + str(flag))
        self.emit(SIGNAL("formBusy"), flag)

    def on_acq(self):
        """ Start or stop the acquisition of data"""
        if self.debug: print('[EpixEsaMainWindow]: on acq')
        self.emit(SIGNAL("acqState"),1)

    def set_integration(self,n):
        """Update the integration count."""
        self.textbox_integration.setText( str(n) )
        self.on_integration()
    
    def on_integration(self):
        """ update the integration"""
        if self.debug: print('[EpixEsaMainWindow]: on integration')
        try:
            str = unicode(self.textbox_integration.text())
            c = int(str)
            self.integration_count = c            
            self.emit(SIGNAL("integrationCount"), self.integration_count)
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad integration input \"' + self.textbox_integration.text() + '\"\n Need to be an integer only')


    def on_select_asic(self):
        """ update the selected asic"""
        if self.debug: print('[EpixEsaMainWindow]: on select asic')
        try:
            s = str(self.combo_select_asic.currentText())
            if s == 'ALL':
                self.select_asic = -1
            else:
                c = int(s)
                self.select_asic = c
            # should send this to the reader to avoid reading all of the data
            self.emit(SIGNAL("selectASIC"), self.select_asic)
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad ASIC selection input \"' + str(self.combo_select_asic.currentText()) + '\"\n Need to be an integer only')

    
    def on_select_analysis(self):
        """ update the selected analysis"""
        if self.debug: print('[EpixEsaMainWindow]: on select analysis')
        try:
            s = str(self.combo_select_analysis.currentText())
            a = FrameAnalysisTypes.get( s )
            self.emit(SIGNAL("selectAnalysis"), a)
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad analysis selection input \"' + str(self.combo_select_analysis.currentText()) + '\"')
    

    def on_dark_file_select(self):
        #if self.debug: 
        print('[EpixEsaMainWindow]:  on_dark_file_select')
        t = self.textbox_dark_file.text()
        self.emit(SIGNAL('selectDarkFile'), str(t))

    


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
        
        self.form_layout = QFormLayout()

        # Other GUI controls
        textbox_label = QLabel('Info:')
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(100)

        textbox_integration_label = QLabel('Integrate frames (#):')
        self.textbox_integration = QLineEdit()
        self.textbox_integration.setText(str(self.integration_count))
        self.textbox_integration.setMaximumWidth(30)
        self.connect(self.textbox_integration, SIGNAL('editingFinished ()'), self.on_integration)

        textbox_select_asic_label = QLabel('Select ASIC (0-3, -1 for ALL):')
        self.combo_select_asic = QComboBox(self)
        for i in range(-1,EpixFrame.n_asics):
            if i == -1:                
                self.combo_select_asic.addItem("ALL")
            else:
                self.combo_select_asic.addItem(str(i))
        self.combo_select_asic.setCurrentIndex(self.select_asic + 1)
        self.combo_select_asic.currentIndexChanged['QString'].connect(self.on_select_asic)

        textbox_select_analysis_label = QLabel('Select frame analysis:')
        self.combo_select_analysis = QComboBox(self)
        for a in FrameAnalysisTypes.types:
            self.combo_select_analysis.addItem( a.name )
        self.combo_select_analysis.setCurrentIndex(0)
        self.combo_select_analysis.currentIndexChanged['QString'].connect(self.on_select_analysis)
        
        self.acq_button = QPushButton("&Acquire Start/Stop")
        self.connect(self.acq_button, SIGNAL('clicked()'), self.on_acq)

        textbox_plot_options_label = QLabel('Plotting options:')
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        
        vbox = QVBoxLayout()
        self.form_layout_info = QFormLayout()
        self.form_layout_info.addRow( textbox_label, self.textbox)
        vbox.addLayout(self.form_layout_info)
        vbox.addWidget(self.textbox)
        #vbox.addWidget(self.canvas)
        #vbox.addWidget(self.mpl_toolbar)


        self.quit_button = QPushButton("&Quit")
        self.quit_button.clicked.connect(self.on_quit)
        self.daq_button = QPushButton("&DAQ Control GUI")
        self.daq_button.clicked.connect(self.on_daq_control)

        hbox_cntrl = QHBoxLayout()
        hbox_cntrl.addWidget( self.acq_button)
        hbox_cntrl.addWidget( self.daq_button )        
        vbox.addLayout( hbox_cntrl )
        vbox.addStretch(1)

        hbox_dark = QHBoxLayout()
        textbox_dark_file_label = QLabel('Dark file:')
        self.textbox_dark_file = QLineEdit()
        #self.textbox_dark_file.setMaximumWidth(100)
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
        hbox_dark.addStretch()
        vbox.addLayout(hbox_dark)
        hbox_dark1 = QHBoxLayout()        
        hbox_dark1.addWidget(textbox_dark_file_label)
        hbox_dark1.addWidget(self.textbox_dark_file)
        vbox.addLayout(hbox_dark1)
        vbox.addStretch()
        hbox_dark_integration = QHBoxLayout()
        hbox_dark_integration.addWidget( textbox_integration_label )
        hbox_dark_integration.addWidget(  self.textbox_integration )
        hbox_dark_integration.addStretch()
        vbox.addLayout( hbox_dark_integration )
        self.form_layout.addRow(textbox_select_asic_label, self.combo_select_asic)
        self.form_layout.addRow(textbox_select_analysis_label, self.combo_select_analysis) 
        self.form_layout.addRow(self.b_open_dark, self.textbox_dark_file)
        self.form_layout.addRow( textbox_plot_options_label, self.grid_cb)
        vbox.addLayout( self.form_layout )

        vbox.addWidget( QLabel('Plots') )
        self.frame_button = QPushButton("&Frame")
        self.frame_button.clicked.connect(self.on_frame)
        self.cluster_signal_hist_button = QPushButton("&Cluster signal")
        self.cluster_signal_hist_button.clicked.connect(self.on_cluster_signal_hist)
        self.cluster_count_hist_button = QPushButton("&Cluster count")
        self.cluster_count_hist_button.clicked.connect(self.on_cluster_count_hist)
        self.cluster_strip_count_hist_button = QPushButton("&Cluster strip_count")
        self.cluster_strip_count_hist_button.clicked.connect(self.on_cluster_strip_count_hist)
        hbox_plots = QHBoxLayout()
        hbox_plots.addWidget( self.frame_button)
        hbox_plots.addWidget( self.cluster_signal_hist_button) 
        hbox_plots.addWidget( self.cluster_count_hist_button) 
        hbox_plots2 = QHBoxLayout()
        hbox_plots2.addWidget( self.cluster_strip_count_hist_button) 
        hbox_plots2.addStretch(2)
        vbox.addLayout( hbox_plots )
        vbox.addLayout( hbox_plots2 )

        hbox_quit = QHBoxLayout()
        hbox_quit.addStretch(2)
        hbox_quit.addWidget( self.quit_button)                            
        
        vbox.addLayout( hbox_quit )

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


    def connect_function(self, sig, fnc):
        self.connect(self, sig, fnc)
    
    def on_cluster_signal_hist(self):
        w = HistogramWidget('cluster signal hist', np.arange(0,6000,100), None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_clusters'), w.worker.new_data )
        self.connect_function(SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_clusters')]) )
    
    def on_cluster_count_hist(self):
        w = CountHistogramWidget('cluster count hist',np.arange(0, 500), None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('cluster_count'), w.worker.new_data )
        self.connect_function(SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('cluster_count')]) )
    
    def on_cluster_strip_count_hist(self):
        w = StripWidget('cluster strip_count hist',None, True, self.integration_count,50)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('cluster_count'), w.worker.new_data )
        self.connect_function(SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('cluster_count')]) )
    

    def on_frame(self):
        w = ImageWidget('frame',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data'), w.worker.new_data )
        self.connect_function(SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data')]) )
        
    def on_plot_widget_quit(self, name):
        print('[EpixEsaMainWindow]: disconnect widget ' + name )
        for w in self.plot_widgets:
            print('[EpixEsaMainWindow]: check {0}'.format(w[0].name))
            if w[0].name == name:
                for signal in w[1]:
                    self.disconnect(self, signal, w.thread.new_data)
                    print('[EpixEsaMainWindow]: disconnected {0} from signal {1}'.format(w.name, str(signal)))
    
    def on_cluster_signal_hist_quit(self):
        print('[EpixEsaMainWindow]: disconnect cluster signal_hist')
        # loop through all threads
        for thr in self.plot_threads:
            # find the widget worker
            w = thr[1]            
            print('[EpixEsaMainWindow]: check {0}'.format(w.name))
            # check if it's the one we want to quit
            if w.name == 'cluster signal hist':                
                # loop through all signals connected to frame processor and disconnect them
                signals = thr[2]
                for sig in signals:
                    self.frame_processor.worker.disconnect(self, sig, w.thread.new_data)
                    print('[EpixEsaMainWindow]: disconnected {0} signal \"{1}\"'.format(w.name, str(sig)))
    

#    def on_cluster_signal_hist_quit(self):
#        print('[EpixEsaMainWindow]: disconnect cluster signal_hist')
#        for w in self.plot_widgets:
#            print('[EpixEsaMainWindow]: check {0}'.format(w.name))
#            if w.name == 'cluster signal hist':
#                self.frame_processor.worker.disconnect(self, SIGNAL('new_clusters'), w.thread.new_data)
#                print('[EpixEsaMainWindow]: disconnected {0}'.format(w.name))

    
    def on_cluster_count_hist_quit(self):
        print('[EpixEsaMainWindow]: disconnect cluster count_hist')
        for w in self.plot_widgets:
            print('[EpixEsaMainWindow]: check {0}'.format(w.name))
            if w.name == 'cluster count hist':
                self.frame_processor.worker.disconnect(self, SIGNAL('cluster_count'), w.thread.new_data)
                print('[EpixEsaMainWindow]: disconnected {0}'.format(w.name))

    def on_cluster_strip_count_hist_quit(self):
        print('[EpixEsaMainWindow]: disconnect cluster strip_count_hist')
        for w in self.plot_widgets:
            print('[EpixEsaMainWindow]: check {0}'.format(w.name))
            if w.name == 'cluster strip_count hist':
                self.frame_processor.worker.disconnect(self, SIGNAL('cluster_count'), w.thread.new_data)
                print('[EpixEsaMainWindow]: disconnected {0}'.format(w.name))
    

    def on_frame_quit(self):
        print('[EpixEsaMainWindow]: disconnect frame')
        for w in self.plot_widgets:
            print('[EpixEsaMainWindow]: check {0}'.format(w.name))
            if w.name == 'frame':
                self.frame_processor.worker.disconnect(self, SIGNAL('new_data'), w.thread.new_data)
                print('[EpixEsaMainWindow]: disconnected {0}'.format(w.name))
    


    def closeEvent(self, event):
        can_exit = True
        self.on_quit()
        if can_exit:
            event.accept()
        else:
            event.ignore()

    def on_quit(self):
        print('[EpixEsaMainWindow]: on_quit')
        self.daq_worker_widget.close()
        print('[EpixEsaMainWindow]: quit ' + str(len(self.plot_widgets)) + ' widgets')
        for w in self.plot_widgets:
            #self.on_plot_widget_quit(w)
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
            print('[EpixEsaMainWindow]: update dark file to \"' + str(t) + '\" (prev was \"' + str(self.textbox_dark_file.text()) + '\")')
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
    
    def create_status_bar(self):
        self.status_text = QString('Run status: ' + self.run_state)
        #self.statusBar().addWidget(self.status_text, 1)
        self.statusBar().showMessage(self.status_text, 0)


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
