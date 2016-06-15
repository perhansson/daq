import sys
import os
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import matplotlib.pyplot as plt

from frame import EpixFrame
from pix_utils import FrameAnalysisTypes
import plot_widgets
from OnlineMainWindow import MainWindow
from daq_worker_gui import *


class EpixEsaMainWindow(MainWindow):

    __window_title = 'ePix ESA Display'

    def __init__(self, parent=None, debug=False):
        MainWindow.__init__(self,parent, debug)

    def get_window_title(self):
        return EpixEsaMainWindow.__window_title
    
    def create_daq_worker_gui(self, daq_worker=None, show=False):                
        """Create the DAQ worker."""
        # create the widget
        self.daq_worker_widget  = DaqWorkerWidget()
        # add the daq connection
        if daq_worker != None:
            self.connect_daq_worker_gui(daq_worker)

    def on_about(self):
        msg = """ ESA ePix online display."""
        QMessageBox.about(self, "About the app", msg.strip())


    def create_stat_view(self, vbox):

        vbox.addWidget(QLabel('Frame processing statistics:'))
        hbox = QHBoxLayout()
        #hbox.addWidget(QLabel('Processing stats:'))

        #self.form_layout_stat = QFormLayout()
        # frame id
        textbox_frameid_label = QLabel('ID:')
        self.textbox_frameid = QLineEdit()
        self.textbox_frameid.setMinimumWidth(50)
        self.textbox_frameid.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_frameid_label, self.textbox_frameid)
        hbox.addWidget(textbox_frameid_label)
        hbox.addWidget(self.textbox_frameid)

        # frame rate
        textbox_framerate_label = QLabel('Rate:')
        self.textbox_framerate = QLineEdit()
        self.textbox_framerate.setMinimumWidth(50)
        self.textbox_framerate.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_framerate_label, self.textbox_framerate)
        hbox.addWidget(textbox_framerate_label)
        hbox.addWidget(self.textbox_framerate)
        
        # frames processed
        textbox_frameprocessed_label = QLabel('# processed:')
        self.textbox_frameprocessed = QLineEdit()
        self.textbox_frameprocessed.setMinimumWidth(50)
        self.textbox_frameprocessed.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_frameprocessed_label, self.textbox_frameprocessed)
        hbox.addWidget(textbox_frameprocessed_label)
        hbox.addWidget(self.textbox_frameprocessed)

        #vbox.addLayout(self.form_layout_stat)
        vbox.addLayout(hbox)


    def create_options_view(self,vbox):
        """Add options to form."""
                
        textbox_select_asic_label = QLabel('Select ASIC (0-3):')
        self.combo_select_asic = QComboBox(self)
        for i in range(-1,EpixFrame.n_asics):
            if i == -1:                
                self.combo_select_asic.addItem("ALL")
            else:
                self.combo_select_asic.addItem(str(i))
        self.combo_select_asic.setCurrentIndex(self.select_asic + 1)
        self.combo_select_asic.currentIndexChanged['QString'].connect(self.on_select_asic)

        textbox_select_frame_flips_label = QLabel('# 90deg. rotations:')
        self.combo_select_frame_flips = QComboBox(self)
        for i in range(4):
            self.combo_select_frame_flips.addItem(str(i))
        self.combo_select_frame_flips.setCurrentIndex(1)
        self.combo_select_frame_flips.currentIndexChanged['QString'].connect(self.on_select_frame_flips)

        textbox_integration_label = QLabel('Integrate frames (#):')
        self.textbox_integration = QLineEdit()
        self.textbox_integration.setText(str(self.integration_count))
        self.textbox_integration.setMaximumWidth(30)
        self.connect(self.textbox_integration, SIGNAL('editingFinished ()'), self.on_integration)

        textbox_select_analysis_label = QLabel('Select frame analysis:')
        self.combo_select_analysis = QComboBox(self)
        for a in FrameAnalysisTypes.types:
            self.combo_select_analysis.addItem( a.name )
        self.combo_select_analysis.setCurrentIndex(0)
        self.combo_select_analysis.currentIndexChanged['QString'].connect(self.on_select_analysis)

        textbox_plot_options_label = QLabel('Plotting options:')
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)

        self.form_layout = QFormLayout()
        self.form_layout.addRow(textbox_select_asic_label, self.combo_select_asic)
        self.form_layout.addRow(textbox_select_frame_flips_label, self.combo_select_frame_flips)
        self.form_layout.addRow(textbox_select_analysis_label, self.combo_select_analysis) 
        self.form_layout.addRow( textbox_plot_options_label, self.grid_cb)
        self.form_layout.addRow( textbox_integration_label, self.textbox_integration)

        vbox.addLayout( self.form_layout )




    def create_plots_view(self,vbox):
        """Build GUI items for plots."""

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

    def on_cluster_signal_hist(self):
        """Cluster signal histogram."""
        w = plot_widgets.HistogramWidget('cluster signal hist', np.arange(0,6000,100), None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_clusters'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_clusters')]) )
    
    def on_cluster_count_hist(self):
        """Cluster count histogram."""
        w = plot_widgets.CountHistogramWidget('cluster count hist',np.arange(0, 500), None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('cluster_count'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('cluster_count')]) )
    
    def on_cluster_strip_count_hist(self):
        """Cluster count strip chart."""
        w = plot_widgets.StripWidget('cluster strip_count hist',None, True, self.integration_count,50)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('cluster_count'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('cluster_count')]) )
    
    def on_frame(self):
        """Pixel frame image."""
        w = plot_widgets.ImageWidget('frame',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data')]) )

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
            # reset data in case it's not compatible with the new selection
            for w in self.plot_widgets:
                w[0].worker.clear_data()
                w[0].clear_figure()
        
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad ASIC selection input \"' + str(self.combo_select_asic.currentText()) + '\"\n Need to be an integer only')

    def on_select_frame_flips(self):
        """ update the selected asic"""
        if self.debug: print('[EpixEsaMainWindow]: on select asic')
        try:
            self.emit(SIGNAL("selectFrameFlips"),  int(str(self.combo_select_frame_flips.currentText())))
            # reset data in case it's not compatible with the new selection
            for w in self.plot_widgets:
                w[0].worker.clear_data()
                w[0].clear_figure()
        
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad frame flip selection input \"' + str(self.combo_select_frame_flips.currentText()) + '\"\n Need to be an integer only')

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
        
    def on_select_analysis(self):
        """ update the selected analysis"""
        if self.debug: print('[EpixEsaMainWindow]: on select analysis')
        try:
            s = str(self.combo_select_analysis.currentText())
            a = FrameAnalysisTypes.get( s )
            self.emit(SIGNAL("selectAnalysis"), a)
        except ValueError:
            print('[EpixEsaMainWindow]: \n\n========= WARNING, bad analysis selection input \"' + str(self.combo_select_analysis.currentText()) + '\"')
    

