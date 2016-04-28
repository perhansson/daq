import sys
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pythonDaq
sys.path.append('/home/epix/run_software/python/pylib')
import daq_client



class DaqWorker(QThread):
    """Control the DAQ in this thread."""
    
    def __init__(self,parent=None):
        QThread.__init__(self,parent)
        self.state = ''
        # start the thread
        self.start()
        self.daq_client = None
        self.running = True
    
    def __del__(self):
        self.running = False
        self.wait()
    
    def run(self):
        """Called once by Qt after things are setup."""
        
        print('DaqWorker: run')

        # open shared memory
        #pythonDaq.daqSharedDataOpen('epix', 1)
        pythonDaq.daqOpen('epix', 1)
        
        print('DaqWorker: open socket client')
        self.daq_client = daq_client.DaqClient('localhost',8090)
        print('DaqWorker: open socket client done')



        # print some status while thread is alove
        while self.running:            
            print('DaqWorker: state "' + pythonDaq.daqGetRunState() + '"')
            time.sleep(2)
    

    def reset(self):
        """Reset the DAQ."""
        print('[daq_worker] : hard reset')
        pythonDaq.daqHardReset()
        print('[daq_worker] : sleep')
        time.sleep(5)
        print('[daq_worker] : reset counters')
        pythonDaq.daqResetCounters()
        print('[daq_worker] : reset done')
    
    def set_defaults(self):
        """Set DAQ defaults."""
        print('DaqWorker: set_defaults')
        pythonDaq.daqSetDefaults()
        print('DaqWorker: set_defaults done')
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
        
        pythonDaq.daqSoftReset()

    def set_run_parameters(self,run_type='',rate=1,count=10):
        """Set parameters for the run."""
        if run_type == 'dark':
            rate_str = 'Dark'
        elif run_type == 'beam':
            rate_str = 'Beam'
            count = 10000000
        else:
            rate_str = str(rate) + 'Hz'
        pythonDaq.daqSetRunParameters(rate_str,count)

    def start_run(self,params):
        """Start a run. """
        print('DaqWorker: start run with params')        
        print(params)

        self.configure()

        #defaults
        rate_str = 'Beam'
        count = 10000000
        
        # custom supplied
        if params != None:
            if params['filepath'] != None and params['filepath'] != '': 
                self.open_file(params['filepath'])
            if params['rate'] != None and params['rate'] != '':
                rate_str = params['rate']
            if params['count'] != None and  params['count'] > 0:
                count = params['count']
        
                
        # set the run parameters
        print('rate_str ' + rate_str + ' count ' + str(count))
        pythonDaq.daqSetRunParameters(rate_str, count)

        # start the run
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

        
    
        
