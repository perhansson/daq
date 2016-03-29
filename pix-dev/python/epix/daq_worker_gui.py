#!/usr/bin/python

import sys
import os
import datetime
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from daq_worker import DaqWorker


class DaqWorkerWidget(QWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, parent=None):
        QWidget.__init__(self,parent)
        self.set_geometry()
        self.create_control()        
        self.show()

    def set_geometry(self):
        self.setGeometry(10,10,500,300)
        self.setWindowTitle('Esa Daq Control')

    def create_control(self):

        hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        label = QLabel('Generate a dark file: leave empty for auto name or supply a file name.')
        vbox.addWidget(label)

        hbox_get_dark = QHBoxLayout()
        self.b_get_dark = QPushButton(self)
        self.b_get_dark.setText('Start new dark file run')
        self.connect(self.b_get_dark,SIGNAL('clicked()'), self.on_get_dark)
        self.b_stop_get_dark = QPushButton(self)
        self.b_stop_get_dark.setText('Stop') # new dark file run')
        self.connect(self.b_stop_get_dark,SIGNAL('clicked()'), self.on_stop)

        hbox_get_dark.addWidget(self.b_get_dark)
        hbox_get_dark.addWidget(self.b_stop_get_dark)
        vbox.addLayout(hbox_get_dark)
        
        hbox_dark_file= QHBoxLayout()
        self.b_open_dark = QPushButton(self)
        self.b_open_dark.setText('Select dark file')
        self.b_open_dark.clicked.connect(self.showDarkFileDialog)

        #label_dark_file = QLabel('Dark file:')
        self.textbox_dark_file = QLineEdit()
        self.textbox_dark_file.setMinimumWidth(200)
        #self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)

        #hbox_dark_file.addWidget(label_dark_file)
        hbox_dark_file.addWidget(self.b_open_dark)
        hbox_dark_file.addWidget(self.textbox_dark_file)
        #hbox_dark_file.addStretch()

        vbox.addLayout(hbox_dark_file)        

        #self.connect(self.b_get_dark,SIGNAL('clicked()'), self.on_get_dark)
        #openFile = QAction(QIcon('open.png'), 'Open', self)
        #openFile.setShortcut('Ctrl+O')
        #openFile.setStatusTip('Open new Dark File')
        #openFile.triggered.connect(self.showDarkFileDialog)
        #menubar = self.menuBar()
        #fileMenu = menubar.addMenu('&File')
        #fileMenu.addAction(openFile)
        vbox.addStretch()

        vbox.addWidget(QLabel('Start/stop DAQ with beam trigger'))
        
        self.b_configure = QPushButton(self)
        self.b_configure.setText('Configure')
        self.connect(self.b_configure,SIGNAL('clicked()'), self.on_configure)

        vbox.addWidget(self.b_configure)

        hbox_light_file= QHBoxLayout()
        self.b_open_light = QPushButton(self)
        self.b_open_light.setText('Save to file')
        self.b_open_light.clicked.connect(self.showLightFileDialog)

        #label_dark_file = QLabel('Dark file:')
        self.textbox_light_file = QLineEdit()
        self.textbox_light_file.setMinimumWidth(200)
        #self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)

        #hbox_light_file.addWidget(label_dark_file)
        hbox_light_file.addWidget(self.b_open_light)
        hbox_light_file.addWidget(self.textbox_light_file)
        #hbox_light_file.addStretch()

        vbox.addLayout(hbox_light_file)        

        hbox_get_light = QHBoxLayout()
        
        self.b_start = QPushButton(self)
        self.b_start.setText('Start')
        self.connect(self.b_start,SIGNAL('clicked()'), self.on_start)

        hbox_get_light.addWidget(self.b_start)

        self.b_stop = QPushButton(self)
        self.b_stop.setText('Stop')
        self.connect(self.b_stop,SIGNAL('clicked()'), self.on_stop)
        
        hbox_get_light.addWidget(self.b_stop)                

        vbox.addLayout(hbox_get_light)


        self.b_quit = QPushButton(self)
        self.b_quit.setText('Quit')
        self.b_quit.clicked.connect(self.close)
        vbox.addWidget(self.b_quit)       

        hbox.addLayout(vbox)

        self.setLayout(hbox)


    def showDarkFileDialog(self):
        """Open file dialog to select a dark file."""
        file_name = QFileDialog.getOpenFileName(self,'Open dark file',DaqWorkerWidget.__datadir)
        self.textbox_dark_file.setText(file_name)


    def showLightFileDialog(self):
        """Open file dialog to select a light file."""
        file_name = QFileDialog.getOpenFileName(self,'Open light file',DaqWorkerWidget.__datadir)
        self.textbox_light_file.setText(file_name)
    

    def on_start(self):
        """Start the run."""
        args = {'filepath':str(self.textbox_light_file.text()),'rate':'Beam','count':1000000}
        print('start run with opetions')
        print args
        self.emit(SIGNAL('start_run'), args)
    
    def on_stop(self):
        """Stop the run."""
        self.emit(SIGNAL('stop_run'),'')

    def on_configure(self):
        """Configure the DAQ."""
        self.emit(SIGNAL('configure'),1)

    def on_get_dark(self):
        """Generate a dark file."""
        fname = str(self.textbox_dark_file.text())
        if fname == '':
            fname = os.path.join(DaqWorkerWidget.__datadir,'{0}_dark.bin'.format( datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') ))
            self.textbox_dark_file.setText(fname)
        #print('[ on_get_dark ]: generate dark file "{0}"'.format(fname))        
        args = {'filepath':fname, 'rate':'Dark', 'count':10}
        self.emit(SIGNAL('generate_dark'),args)
    

    def connect_workers(self, daq_worker):        
        self.connect(self, SIGNAL('configure'), daq_worker.configure)
        self.connect(self, SIGNAL('start_run'), daq_worker.start_run)
        self.connect(self, SIGNAL('stop_run'), daq_worker.stop_run)
        self.connect(self, SIGNAL('generate_dark'), daq_worker.generate_dark)



def main():

    app = QApplication(sys.argv)
    widget  = DaqWorkerWidget()
    daq_worker = DaqWorker()
    widget.connect_workers( daq_worker )
    sys.exit( app.exec_() )
    
    

if __name__ == '__main__':
    #args = get_args()
    main()
