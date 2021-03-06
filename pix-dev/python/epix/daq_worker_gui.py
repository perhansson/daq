#!/usr/bin/python

import sys
import os
import datetime
import time
import re
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from daq_worker import DaqWorker


class DaqWorkerWidget(QWidget):

    __datadir = os.environ['DATADIR']
    
    def __init__(self, parent=None, show=False):
        QWidget.__init__(self,parent)
        self.set_geometry()
        self.create_control()        
        self.daq_worker = None
        if show:
            self.show()
    
    def set_geometry(self):
        self.setGeometry(10,10,500,300)
        self.setWindowTitle('Pix Daq Control')

    def create_control(self):

        #hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        label = QLabel('DAQ Control for pix DAQ')
        label3 = QLabel('Run numbers are updated automatically.')
        label4 = QLabel('Dark and light files are automatically generated unless given.')
        label2 = QLabel('Note: you can hit "Stop Dark" if you want shorter than default (10) dark runs.')
        vbox.addWidget(label)
        vbox.addWidget(label3)
        vbox.addWidget(label4)
        vbox.addWidget(label2)


        hbox_control_run_params = QHBoxLayout()
        self.combo_select_runtype = QComboBox(self)
        self.combo_select_runtype.addItem('Beam')
        self.combo_select_runtype.addItem('1Hz')
        self.combo_select_runtype.setCurrentIndex(0)
        #self.combo_select_runtype.currentIndexChanged['QString'].connect(self.on_select_runtype)
        self.combo_select_trigtype = QComboBox(self)
        self.combo_select_trigtype.addItem('Evr Running')
        self.combo_select_trigtype.addItem('Running')
        self.combo_select_trigtype.addItem('swRunning')
        self.combo_select_trigtype.setCurrentIndex(0)
        #self.combo_select_trigtype.currentIndexChanged['QString'].connect(self.on_select_trigtype)

        hbox_control_run_params.addWidget(QLabel('Run configuration:'))
        hbox_control_run_params.addWidget(self.combo_select_runtype)
        hbox_control_run_params.addWidget(self.combo_select_trigtype)

        vbox.addLayout(hbox_control_run_params)

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

        hbox_control_run.addWidget(QLabel('Run control:'))
        hbox_control_run.addWidget(self.b_control_run)
        hbox_control_run.addWidget(self.b_stop_dark_control_run)
        hbox_control_run.addWidget(self.b_stop_control_run)
        vbox.addLayout(hbox_control_run)

        hbox_run= QHBoxLayout()
        label_run = QLabel('Run')
        self.textbox_run = QLineEdit()
        self.textbox_run.setMinimumWidth(6)
        label_runstate = QLabel('Run State')
        self.textbox_runstate = QLineEdit()
        self.textbox_runstate.setMinimumWidth(10)
        label_config = QLabel('Config')
        self.textbox_config = QLineEdit()
        self.textbox_config.setMinimumWidth(5)
        label_nevents = QLabel('Events')
        self.textbox_nevents = QLineEdit()
        self.textbox_nevents.setMinimumWidth(7)
        label_rate = QLabel('Rate')
        self.textbox_rate = QLineEdit()
        self.textbox_rate.setMinimumWidth(6)
        hbox_run.addWidget(label_run)
        hbox_run.addWidget(self.textbox_run)
        hbox_run.addWidget(label_config)
        hbox_run.addWidget(self.textbox_config)
        hbox_run.addWidget(label_runstate)
        hbox_run.addWidget(self.textbox_runstate)
        hbox_run.addWidget(label_nevents)
        hbox_run.addWidget(self.textbox_nevents)
        hbox_run.addWidget(label_rate)
        hbox_run.addWidget(self.textbox_rate)
        vbox.addLayout(hbox_run)     
        r = self.find_run_number()
        self.textbox_run.setText(str(r))
        self.textbox_config.setText('-')
        self.textbox_runstate.setText('-')
        self.textbox_nevents.setText('-')
        self.textbox_rate.setText('-')


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
        file_name = QFileDialog.getOpenFileName(self,'Open light file',self.__datadir)
        self.textbox_light_file.setText(file_name)
    

    def on_start(self, ignoreTextField=True):
        """Generate a dark file."""
        if ignoreTextField:
            # create a new file based on date and run text field
            run = self.textbox_run.text()
            fname = os.path.join(self.__datadir,'{0}_run{1}.bin'.format( datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'), run ))
        else:
            # use the given name in the text box
            fname = str(self.textbox_light_file.text())
            if fname == '':
                self.on_start(True)

        # update the text field for the dark
        self.textbox_light_file.setText(fname)
        
        # send the worker the instructions on the run
        args = {'filepath':str(self.textbox_light_file.text()),'rate':self.get_runtype(), 'trigtype':self.get_trigtype(), 'count':1000000}
        print('start run with options')
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

        # start a new run
        self.on_start()

    def on_configure(self):
        """Configure the DAQ."""
        self.emit(SIGNAL('configure'),1)


    def find_run_number(self):
        # parse the data directory and find the last run number
        runs = []
        #print('self.__datadir ' + self.__datadir)
        #print('os.listdir(self.__datadir) ' + str(os.listdir(self.__datadir)))
        if os.path.isdir(self.__datadir):
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
            r = 0
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
    
        
    def get_runtype(self):
        """Return the current run type string from the combo menu."""
        return str(self.combo_select_runtype.currentText())

    def get_trigtype(self):
        """Return the current run type string from the combo menu."""
        return str(self.combo_select_trigtype.currentText())

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
        count = 100
        runtype = None
        trigtype = self.get_trigtype()
        if self.get_runtype() == 'Beam':
            #runtype = 'Dark'
            runtype = '10Hz'
            trigtype = 'Running'
        elif 'Hz' in self.get_runtype():
            runtype = '1Hz'
        else:
            raise NotImplementedError('this run type \"' + self.get_runtype() + '\" is invalid')
        
        args = {'filepath':fname, 'rate':runtype, 'trigtype':trigtype, 'count':count}
        self.emit(SIGNAL('start_run'),args)
        
        # wait until we are running
        while 'Running' not in str(self.textbox_runstate.text()):
            print('wait to start')
            time.sleep(0.5)
            QApplication.processEvents()
        
        print('start to check count')
        while True:
            s = self.textbox_runstate.text()
            print('Run state ' + self.textbox_runstate.text() + ' count ' + str(int(self.textbox_nevents.text())))
            if int(self.textbox_nevents.text()) >= count:
                print('reached needed count')
                break
            QApplication.processEvents()
            time.sleep(0.5)

        # stop dark 
        self.on_control_dark_stop()
    
    

    def update_stats(self,stats):
        """Update the stats."""
        #print('[daq_worker_gui]: update stats ' + str(stats) + ': ' + stats[0] + ', ' +str( stats[1]) + ', ' + str(stats[2]))
        if None not in stats:
            self.textbox_runstate.setText(stats[0])
            self.textbox_nevents.setText(str(stats[1]))
            self.textbox_rate.setText('{0:.1f} Hz'.format(stats[2]))
    

    def connect_workers(self):
        
        self.connect(self, SIGNAL('configure'), self.daq_worker.configure)
        self.connect(self, SIGNAL('start_run'), self.daq_worker.start_run)
        self.connect(self, SIGNAL('stop_run'), self.daq_worker.stop_run)
        self.connect(self.daq_worker, SIGNAL('daq_stats'), self.update_stats)

    def closeEvent(self, event):
        """Close the GUI."""
        can_exit = True
        self.on_quit()
        if can_exit:
            event.accept()
        else:
            event.ignore()

    def on_quit(self):
        """Quit the window."""
        print('[daq_worker_gui]: on_quit')
        #if self.daq_worker != None:
        #    self.daq_worker.quit_this()
        self.close()
    

    def quit_worker_thread(self):
        """Kill the worker thread."""
        if self.daq_worker != None:
            self.daq_worker.quit_thread()
    

def main():

    app = QApplication(sys.argv)
    widget  = DaqWorkerWidget()
    #daq_worker = DaqWorker()
    widget.daq_worker = DaqWorker()
    widget.connect_workers()
    widget.show()
    sys.exit( app.exec_() )
    
    

if __name__ == '__main__':
    #args = get_args()
    main()
