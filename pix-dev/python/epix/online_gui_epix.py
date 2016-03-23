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

class EpixEsaForm(QMainWindow):

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

        # keep track of which one being plotted
        # work around if we need to know when updating stuff
        self.__asic_plotted = -1

        # timer
        self.__t0_sum = 0.

        self.integration_count = 1
        
        # hold latest data frame
        self.last_frame = None

        # accumulated frames
        self.acc_frame = None

        # counters
        self.nframes = 0
        self.nframes_acc = 0

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

        #if self.debug: print('newDataFrame')

        self.last_frame = data_frame
        if self.acc_frame:
            self.acc_frame.add( data_frame )
            self.nframes_acc += 1
        else:
            self.acc_frame = data_frame
            self.nframes_acc = 1
        self.nframes += 1

        
        # if a period is set, use that to determine when to update plots
        if self.period:
            if time.time() - self.lastTime > self.period:
                self.lastTime = time.time()
                self.on_draw()
        # otherwise try to update plots whenever there is new data
        else:
            #if self.debug: print('draw it')
            self.on_draw()

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


    def on_acq(self):
        """ Start or stop the acquisition of data"""
        if self.debug: print('on acq')
        self.emit(SIGNAL("acqState"),1)

    def on_reset_integration(self):
        """ Reset the integration frame"""
        if self.debug: print('on reset integration')
        self.acc_frame = None
        self.nframes_acc = 0

    def on_integration(self):
        """ update the integration"""
        if self.debug: print('on integration')
        try:
            str = unicode(self.textbox_integration.text())
            c = int(str)
            self.integration_count = c            
            self.emit(SIGNAL("integrationCount"), self.integration_count)
        except ValueError:
            print('\n\n========= WARNING, bad integration input \"' + self.textbox_integration.text() + '\"\n Need to be an integer only')


    def on_select_asic(self):
        """ update the selected asic"""
        if self.debug: print('on select asic')
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
            print('\n\n========= WARNING, bad ASIC selection input \"' + str(self.combo_select_asic.currentText()) + '\"\n Need to be an integer only')

    def on_select_analysis(self):
        """ update the selected analysis"""
        if self.debug: print('on select analysis')
        try:
            s = str(self.combo_select_analysis.currentText())
            a = FrameAnalysisTypes.get( s )
            self.emit(SIGNAL("selectAnalysis"), a)
        except ValueError:
            print('\n\n========= WARNING, bad analysis selection input \"' + str(self.combo_select_analysis.currentText()) + '\"')
    
    
    def on_draw(self):
        """ Redraws the figure
        """

        if self.debug: print ('on_draw ')
        
        t0 = time.clock()


        # check that there is a data to be drawn
        if self.last_frame != None:


            # update status
            self.textbox.setText('Redrawing figure')

            # set plot options
            for ep in self.epix_plots.plots:
                ep.axes.grid(self.grid_cb.isChecked())

            # update the current frame plot
            if self.debug: print('draw current frame')
            data = self.last_frame.get_data(self.select_asic)

            if self.debug: print ('data ', data)

            #np.savez('data_asic' + str(self.select_asic) + '_' + str( self.nframes), data )

            frame_plot_title = 'Last frame'
            if self.integration_count > 1:
                frame_plot_title = 'Last ' + str(self.integration_count) + ' frames'                    
            self.epix_plots.get_plot('frame').axes.set_title( frame_plot_title )
            #'Last ', self.integration, ' frame ' + str( self.nframes ));
            # may need to redraw when a new asic is selected
            # not needed in v10.1 of numpy/matplotlib combo?
            if self.epix_plots.get_plot('frame').img and self.__asic_plotted == self.select_asic:
                self.epix_plots.get_plot('frame').img.set_data( data )
            else:
                self.epix_plots.get_plot('frame').axes.clear()
                self.epix_plots.get_plot('frame').img = self.epix_plots.get_plot('frame').axes.imshow( data, interpolation='nearest', cmap='viridis', vmin=0, vmax=2 )                    
                self.epix_plots.get_plot('frame').axes.xaxis.set_label( 'Pixel X' )
                #plt.gcf().axes.xaxis.set_label( 'Pixel X' )
                #self.epix_plots.get_plot('frame').img.xlabel( 'Pixel X' )
                #self.epix_plots.get_plot('frame').img.ylabel( 'Pixel Y' )
                self.fig.colorbar( self.epix_plots.get_plot('frame').img, cax=self.epix_plots.get_plot('frame').axes)
            #if self.epix_plots.get_plot('frame').cbar:
            #    self.epix_plots.get_plot('frame').cbar 


            # projection
            frame_plot_title = 'Last frame prj X'
            if self.integration_count > 1:
                frame_plot_title = 'Last ' + str(self.integration_count) + ' frames prj X'                    
            self.epix_plots.get_plot('prj_x').axes.set_title( frame_plot_title )
            self.epix_plots.get_plot('prj_x').axes.clear()
            self.epix_plots.get_plot('prj_x').img = self.epix_plots.get_plot('prj_x').axes.plot( np.sum(data, axis=0) )

            frame_plot_title = 'Last frame prj Y'
            if self.integration_count > 1:
                frame_plot_title = 'Last ' + str(self.integration_count) + ' frames prj Y'                    
            self.epix_plots.get_plot('prj_y').axes.set_title( frame_plot_title )
            self.epix_plots.get_plot('prj_y').axes.clear()
            self.epix_plots.get_plot('prj_y').img = self.epix_plots.get_plot('prj_y').axes.plot( np.sum(data, axis=1), range(len(np.sum(data, axis=1))) )



            # update the accumulated frame
            if self.debug: print('draw accumulated frame')
            data = self.acc_frame.get_data(self.select_asic)
            if self.debug: print ('data ', data)
            self.epix_plots.get_plot('integrated').axes.set_title(str( self.nframes_acc) + ' integrated frames ');
            if self.epix_plots.get_plot('integrated').img and self.__asic_plotted == self.select_asic:
                self.epix_plots.get_plot('integrated').img.set_data( data )
            else:
                self.epix_plots.get_plot('integrated').axes.clear()
                self.epix_plots.get_plot('integrated').img = self.epix_plots.get_plot('integrated').axes.imshow( data, interpolation='nearest', cmap='viridis', vmin=0, vmax=2 )
                self.fig.colorbar( self.epix_plots.get_plot('integrated').img, cax=self.epix_plots.get_plot('integrated').axes)



            # projection of accumulated frame
            self.epix_plots.get_plot('integrated_prj_x').axes.set_title(str( self.nframes_acc) + ' integrated frames prj X');
            self.epix_plots.get_plot('integrated_prj_x').axes.set_title( frame_plot_title )
            self.epix_plots.get_plot('integrated_prj_x').axes.clear()
            self.epix_plots.get_plot('integrated_prj_x').img = self.epix_plots.get_plot('integrated_prj_x').axes.plot( np.sum(data, axis=0) )

            self.epix_plots.get_plot('integrated_prj_y').axes.set_title(str( self.nframes_acc) + ' integrated frames prj Y');
            self.epix_plots.get_plot('integrated_prj_y').axes.set_title( frame_plot_title )
            self.epix_plots.get_plot('integrated_prj_y').axes.clear()
            self.epix_plots.get_plot('integrated_prj_y').img = self.epix_plots.get_plot('integrated_prj_y').axes.plot( np.sum(data, axis=1), range(len(np.sum(data, axis=1))) )

            # update the asic being plotted
            self.__asic_plotted = self.select_asic

            self.canvas.draw()
            if self.debug: print ('done drawing')
            self.textbox.setText('Figure updated with data from frame ' + str( self.nframes ))

            # timer info
            self.__t0_sum += time.clock() - t0
            if self.nframes % 10 == 0:
                print('Draw  {0} frames with {1} sec/frame'.format(self.nframes, self.__t0_sum/10.))
                self.__t0_sum = 0.

        else:
            self.textbox.setText('No data available, frames processed: ' + str( self.nframes ))
    
        if self.debug: print('Completed draw in {0} s'.format(time.clock() - t0))
    

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
        self.fig = plt.Figure(figsize=(20, 20), dpi=150)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        epix_style.setup_color_map(plt)

        # add plots
        self.epix_plots = EpixPlots()
        self.epix_plots.add_plot( EpixPlot('frame', self.fig.add_subplot(231)) )
        self.epix_plots.add_plot( EpixPlot('prj_x', self.fig.add_subplot(232)) )
        self.epix_plots.add_plot( EpixPlot('prj_y', self.fig.add_subplot(233)) )
        self.epix_plots.add_plot( EpixPlot('integrated', self.fig.add_subplot(234)) )
        self.epix_plots.add_plot( EpixPlot('integrated_prj_x', self.fig.add_subplot(235)) )
        self.epix_plots.add_plot( EpixPlot('integrated_prj_y', self.fig.add_subplot(236)) )
        
        # Bind the 'pick' event for clicking on the plot         
        self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)

        textbox_integration_label = QLabel('Integrate frames (#):')
        self.textbox_integration = QLineEdit()
        self.textbox_integration.setText('1')
        self.textbox_integration.setMaximumWidth(30)
        self.connect(self.textbox_integration, SIGNAL('editingFinished ()'), self.on_integration)

        textbox_select_asic_label = QLabel('Select ASIC (0-3, -1 for ALL):')
        self.combo_select_asic = QComboBox(self)
        for i in range(-1,EpixFrame.n_asics):
            if i == -1:                
                self.combo_select_asic.addItem("ALL")
            else:
                self.combo_select_asic.addItem(str(i))
        self.combo_select_asic.setCurrentIndex(0)
        self.combo_select_asic.currentIndexChanged['QString'].connect(self.on_select_asic)

        textbox_select_analysis_label = QLabel('Select frame analysis:')
        self.combo_select_analysis = QComboBox(self)
        for a in FrameAnalysisTypes.types:
            self.combo_select_analysis.addItem( a.name )
        self.combo_select_analysis.setCurrentIndex(0)
        self.combo_select_analysis.currentIndexChanged['QString'].connect(self.on_select_analysis)
        
        self.acq_button = QPushButton("&Acquire Start/Stop")
        self.connect(self.acq_button, SIGNAL('clicked()'), self.on_acq)

        self.reset_integration_button = QPushButton("&Reset Integration")
        self.connect(self.reset_integration_button, SIGNAL('clicked()'), self.on_reset_integration)

        textbox_plot_options_label = QLabel('Plotting options:')
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)
        
        # Layout with box sizers         
        hbox_cntrl = QHBoxLayout()
        
        for w in [  textbox_integration_label, self.textbox_integration,
                    textbox_select_asic_label, self.combo_select_asic,
                    textbox_select_analysis_label, self.combo_select_analysis,
                    self.acq_button,
                    self.reset_integration_button]:
            hbox_cntrl.addWidget(w)
            hbox_cntrl.setAlignment(w, Qt.AlignLeft) #Center)
        
        hbox_plotting = QHBoxLayout()
        for w in [  textbox_plot_options_label, self.grid_cb ]:
            hbox_plotting.addWidget(w)
            hbox_plotting.setAlignment(w, Qt.AlignLeft) #Qt.AlignVCenter)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget( self.textbox )
        vbox.addLayout(hbox_cntrl)
        vbox.addLayout(hbox_plotting)
        
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
