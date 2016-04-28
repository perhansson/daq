#!/usr/bin/python

import sys
import os
import datetime
import re
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from daq_worker import DaqWorker


class DaqWorkerWidget(QWidget):

    __datadir = '/home/epix/data'
    
    def __init__(self, parent=None, show=False):
        QWidget.__init__(self,parent)
        self.set_geometry()
        self.create_control()        
        if show:
            self.show()
    
    def set_geometry(self):
        self.setGeometry(10,10,500,300)
        self.setWindowTitle('Esa Daq Control')

    def create_control(self):

        #hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        label = QLabel('Epix100a DAQ Control for ESA Beam')
        label2 = QLabel('Note 1: after sufficient dark events please hit "Stop Dark" to start the normal run')
        label3 = QLabel('Note 2: Run numbers are updated automatically.')
        label4 = QLabel('Note 3: Dark and light files are automatically generated unless given.')
        vbox.addWidget(label)
        vbox.addWidget(label2)
        vbox.addWidget(label3)
        vbox.addWidget(label4)



        hbox_control_run = QHBoxLayout()
        self.b_control_run = QPushButton(self)
        self.b_control_run.setText('New Run')
        self.connect(self.b_control_run,SIGNAL('clicked()'), self.on_control_run)
        self.b_stop_dark_control_run = QPushButton(self)
        self.b_stop_dark_control_run.setText('Stop Dark')
        self.connect(self.b_stop_dark_control_run,SIGNAL('clicked()'), self.on_control_dark_stop)
        self.b_stop_control_run = QPushButton(self)
        self.b_stop_control_run.setText('Stop Run')
        self.connect(self.b_stop_control_run,SIGNAL('clicked()'), self.on_stop)

        hbox_control_run.addWidget(self.b_control_run)
        hbox_control_run.addWidget(self.b_stop_dark_control_run)
        hbox_control_run.addWidget(self.b_stop_control_run)
        vbox.addLayout(hbox_control_run)

        hbox_run= QHBoxLayout()
        label_run = QLabel('Run')
        self.textbox_run = QLineEdit()
        self.textbox_run.setMinimumWidth(10)
        label_nevents = QLabel('Events')
        self.textbox_nevents = QLineEdit()
        self.textbox_nevents.setMinimumWidth(10)
        label_rate = QLabel('Rate')
        self.textbox_rate = QLineEdit()
        self.textbox_rate.setMinimumWidth(10)
        hbox_run.addWidget(label_run)
        hbox_run.addWidget(self.textbox_run)
        hbox_run.addWidget(label_nevents)
        hbox_run.addWidget(self.textbox_nevents)
        hbox_run.addWidget(label_rate)
        hbox_run.addWidget(self.textbox_rate)
        vbox.addLayout(hbox_run)     
        r = self.find_run_number()
        self.textbox_run.setText(str(r))
        self.textbox_nevents.setText('not impl.')
        self.textbox_nevents.setText('not impl.')
        self.textbox_rate.setText('not impl.')


        hbox_dark_file= QHBoxLayout()
        self.b_open_dark = QPushButton(self)
        self.b_open_dark.setText('Dark file')
        self.b_open_dark.clicked.connect(self.showDarkFileDialog)
        self.textbox_dark_file = QLineEdit()
        self.textbox_dark_file.setMinimumWidth(200)
        hbox_dark_file.addWidget(self.b_open_dark)
        hbox_dark_file.addWidget(self.textbox_dark_file)
        vbox.addLayout(hbox_dark_file)        

        hbox_light_file= QHBoxLayout()
        self.b_open_light = QPushButton(self)
        self.b_open_light.setText('Save to file')
        self.b_open_light.clicked.connect(self.showLightFileDialog)
        self.textbox_light_file = QLineEdit()
        self.textbox_light_file.setMinimumWidth(200)
        hbox_light_file.addWidget(self.b_open_light)
        hbox_light_file.addWidget(self.textbox_light_file)

        vbox.addLayout(hbox_light_file)        

        self.b_configure = QPushButton(self)
        self.b_configure.setText('Configure')
        self.connect(self.b_configure,SIGNAL('clicked()'), self.on_configure)

        vbox.addWidget(self.b_configure)

        self.b_quit = QPushButton(self)
        self.b_quit.setText('Quit')
        self.b_quit.clicked.connect(self.close)
        vbox.addWidget(self.b_quit)       

        #hbox.addLayout(vbox)

        self.setLayout(vbox)


    def showDarkFileDialog(self):
        """Open file dialog to select a dark file."""
        file_name = QFileDialog.getOpenFileName(self,'Open dark file',self.__datadir)
        self.textbox_dark_file.setText(file_name)


    def showLightFileDialog(self):
        """Open file dialog to select a light file."""
        file_name = QFileDialog.getOpenFileName(self,'Open light file',DaqWorkerWidget.__datadir)
        self.textbox_light_file.setText(file_name)
    

    def on_start(self, ignoreTextField=True):
        """Generate a dark file."""
        if ignoreTextField:
            # create a new file based on date and run text field
            run = self.textbox_run.text()
            fname = os.path.join(DaqWorkerWidget.__datadir,'{0}_run{1}.bin'.format( datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'), run ))
        else:
            # use the given name in the text box
            fname = str(self.textbox_light_file.text())
            if fname == '':
                self.on_start(True)

        # update the text field for the dark
        self.textbox_light_file.setText(fname)
        
        # send the worker the instructions on the run
        args = {'filepath':str(self.textbox_light_file.text()),'rate':'Beam','count':1000000}
        print('start run with opetions')
        print args
        self.emit(SIGNAL('start_run'), args)


    def on_stop(self):
        """Stop the run."""
        self.emit(SIGNAL('stop_run'),'')

    def on_control_dark_stop(self):
        """Stop the dark run and continue with beam."""
        print('[daq_worker_gui]: on_control_dark_stop')

        # stop the run
        self.emit(SIGNAL('stop_run'),'')

        # start a new run with default arguments = beam
        self.on_start()
    

    def on_configure(self):
        """Configure the DAQ."""
        self.emit(SIGNAL('configure'),1)

    def find_run_number(self):
        # parse the data directory and find the last run number
        runs = []
        #print('self.__datadir ' + self.__datadir)
        #print('os.listdir(self.__datadir) ' + str(os.listdir(self.__datadir)))
        for file_name in os.listdir(self.__datadir):
            #print ('test ' + file_name)
            m = re.match('.*run_?(\d+).*', file_name)
            if m != None:
                run = int(m.group(1))
                runs.append(run)
        if runs:            
            r = max(runs)
        else:
            print ('[daq_worker_gui] : find_run_number : WARNING no runs found in ' + self.__datadir)
            r = -1
        print ('[daq_worker_gui] : find_run_number :  found max run ' + str(r) + ' from ' + str(len(runs)) + ' runs')
        return r
    


    def on_control_run(self):
        """Start a new run including dark file."""
        # find run number to use and increment
        run = self.find_run_number() + 1
        print ('[daq_worker_gui] : on_control_run : start run ' + str(run))

        if run < 0:
            print ('[daq_worker_gui] : ERROR not a valid run_number' + str(run))
            return

        # clear textboxes for dark and light
        self.textbox_dark_file.setText('')
        self.textbox_light_file.setText('')

        # set textbox for run
        self.textbox_run.setText(str(run))
        
        # generate the dark file
        self.on_get_dark(True)

        # here I should be able to find when it's done but can't right now
        # FIX THIS!
    
        

    def on_get_dark(self, ignoreTextField=True):
        """Generate a dark file."""
        if ignoreTextField:
            # create a new file based on date and run text field
            run = self.textbox_run.text()
            fname = os.path.join(DaqWorkerWidget.__datadir,'{0}_run{1}_dark.bin'.format( datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'), run ))
        else:
            # use the given name in the text box
            fname = str(self.textbox_dark_file.text())
            if fname == '':
                self.on_get_dark(True)

        # update the text field for the dark
        self.textbox_dark_file.setText(fname)
        
        # send the worker the instructions on the run
        args = {'filepath':fname, 'rate':'Dark', 'count':10}
        self.emit(SIGNAL('start_run'),args)
    

    def connect_workers(self, daq_worker):        
        self.connect(self, SIGNAL('configure'), daq_worker.configure)
        self.connect(self, SIGNAL('start_run'), daq_worker.start_run)
        self.connect(self, SIGNAL('stop_run'), daq_worker.stop_run)



def main():

    app = QApplication(sys.argv)
    widget  = DaqWorkerWidget()
    daq_worker = DaqWorker()
    widget.connect_workers( daq_worker )
    widget.show()
    sys.exit( app.exec_() )
    
    

if __name__ == '__main__':
    #args = get_args()
    main()
