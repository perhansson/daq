#!/usr/bin/python

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class DaqWorkerWidget(QWidget):
    
    def __init__(self, parent=None):
        QWidget.__init__(self,parent)
        self.set_geometry()
        self.create_control()        
        self.show()

    def set_geometry(self):
        self.setGeometry(10,10,300,200)
        self.setWindowTitle('Esa Daq Control')

    def create_control(self):

        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        label = QLabel('DAQ Control')
        vbox.addStretch()
        vbox.addWidget(label)
        self.b_get_dark = QPushButton(self)
        self.b_get_dark.setText('Generate new dark file')
        self.b_start = QPushButton(self)
        self.b_start.setText('Start run')
        self.b_stop = QPushButton(self)
        self.b_stop.setText('Stop run')

        hbox_dark_file= QHBoxLayout()
        label_dark_file = QLabel('Dark file:')
        self.textbox_dark_file = QLineEdit()
        self.textbox_dark_file.setMinimumWidth(200)
        #self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)
        hbox_dark_file.addWidget(label_dark_file)
        hbox_dark_file.addWidget(self.textbox_dark_file)
        vbox.addWidget(self.b_get_dark)
        vbox.addLayout(hbox_dark_file)        
        vbox.addWidget(self.b_start)
        vbox.addWidget(self.b_stop)                
        hbox.addLayout(vbox)
        self.setLayout(hbox)
    

if __name__ == '__main__':

    app = QApplication(sys.argv)
    widget  = DaqWorkerWidget()
    sys.exit( app.exec_() )
