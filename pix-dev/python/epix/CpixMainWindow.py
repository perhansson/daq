from PyQt4.QtGui import *
from PyQt4.QtCore import *

from EpixEsaMainWindow import EpixEsaMainWindow
import plot_widgets

class CpixMainWindow(EpixEsaMainWindow):

    __window_title = 'cPix Display'

    def __init__(self,parent=None, debug=False):
        EpixEsaMainWindow.__init__(self, parent, debug)
        
    def on_about(self):
        msg = """ cPix online display."""
        QMessageBox.about(self, "About the app", msg.strip())
    
    

    def create_plots_view(self,vbox):
        """Build GUI items for plots."""

        vbox.addWidget( QLabel('Plots') )
        self.frame_button = QPushButton("All frames")
        self.frame_button.clicked.connect(self.on_frame)
        self.frame_a_button = QPushButton("Frame A")
        self.frame_a_button.clicked.connect(self.on_frame_a)
        self.frame_b_button = QPushButton("Frame B")
        self.frame_b_button.clicked.connect(self.on_frame_b)
        self.frame_diff_button = QPushButton("Frame DIFF")
        self.frame_diff_button.clicked.connect(self.on_frame_diff)
        hbox_plots = QHBoxLayout()
        hbox_plots.addWidget( self.frame_button)
        hbox_plots.addWidget( self.frame_a_button)
        hbox_plots.addWidget( self.frame_b_button)
        hbox_plots.addWidget( self.frame_diff_button)
        vbox.addLayout( hbox_plots )

    
    def on_frame(self):
        """Pixel frame image."""
        w = plot_widgets.ImageWidget('All frames',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data')]) )

    def on_frame_a(self):
        """Pixel frame image."""
        w = plot_widgets.ImageWidget('frame A',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data_A'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data_A')]) )
        
    def on_frame_b(self):
        """Pixel frame image."""
        w = plot_widgets.ImageWidget('frame B',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data_B'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data_B')]) )

    def on_frame_diff(self):
        """Pixel frame image."""
        w = plot_widgets.FrameDiffImageWidget('frame A-B',None, True, self.integration_count)
        self.frame_processor.worker.connect( self.frame_processor.worker, SIGNAL('new_data_diff'), w.worker.new_data )
        self.connect(self, SIGNAL('integrationCount'), w.set_integration)
        self.plot_widgets.append( (w, [SIGNAL('new_data_diff')]) )
