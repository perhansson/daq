import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pythonDaq



class DaqWorker(QThread):
    """Control the DAQ in this thread."""

    def __init__(self,parent=None):
        QThread.__init__(self,parent):
        self.state = ''
        # start the thread
        #self.start()
        self.running = True
    
    def __del__(self):
        self.running = False
        self.wait()
    
    def run(self):
        """Called once by Qt after things are setup."""
        
        print('DaqWorker: run')

        # open shared memory
        pythonDaq.daqSharedDataOpen('epix', 1)
        
        # print some status while thread is alove
        while self.running:            
            print('DaqWorker: daq state "' + pythonDaq.getRunState + '"')
            time.sleep(1)
    

    def reset(self):
        """Reset the DAQ."""
        pythonDaq.HardReset()
        pythonDaq.daqResetCounters()
    
    def set_defaults(self):
        """Set DAQ defaults."""
        print('DaqWorker: set_defaults')
        pythonDaq.daqSetDefaults()
        #pythonDaq.daqLoadSetttings(filepath)
        

    def configure(self):
        """Configure the DAQ."""
        self.reset()
        self.set_defaults()

        # verify
        status = 0
        while status != 1:
            status = pythonDaq.daqVerifyConfig()
            print('Veryfying config ' + str(status))
            time.sleep(0.5)
        
        pythonDaq.SoftReset()

    def produce_dark_file(self, filename):
        """Create a dark file."""
        print('DaqWorker: create dark file ' + filename)
        self.configure()
        #self.set_run_parameters(run_type='dark',rate=1,count=10)
        self.set_run_parameters(run_type='',rate=1,count=10)
        self.start_run(filename)
        self.stop_run()
    
    def set_run_parameters(self,run_type='',rate=1,count=10):
        """Set parameters for the run."""
        if run_type == 'dark':
            rate_str = 'Dark'
        elif run_type == 'beam':
            rate_str = 'Beam'
        else:
            rate_str = str(self.rate) + 'Hz'
        pythonDaq.daqSetRunParameters(rate_str,self.count)

    def start_run(self,filepath=''):
        """Start a run. """
        print('DaqWorker: start run')
        print('DaqWorker: save data to file "' + filepath + '"')
        if filepath != '': 
            self.open_file(filepath)        
        self.set_run_state('Evr Running')
    
    def stop_run(self):
        """Stop a run. """                
        self.set_run_state('Stopped')        
        self.close_file()
    
    def open_file(self,filepath):
        """Open a data file."""
        pythonDaq.daqOpenData(filepath)
    
    def close_file(self):
        """Close a data file."""
        pythonDaq.daqCloseData()
    
    def set_run_state(self,state):
        """Set the run state of the daq."""
        pythonDaq.daqSetRunState(state)

        
    
        
