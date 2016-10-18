import pythonDaq


def open_file(self,filepath):
    """Open a data file."""
    pythonDaq.daqOpenData(filepath)

def close_file(self):
    """Close a data file."""
    pythonDaq.daqCloseData()

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
    reset()
    set_defaults()

    # verify
    status = 0
    while status != 1:
        status = pythonDaq.daqVerifyConfig()
        print('Veryfying config ' + str(status))
        time.sleep(0.5)

    pythonDaq.daqSoftReset()


def stop_run(self):
    """Stop a run. """                
    close_file()

def set_run_state(self,state):
    """Set the run state of the daq."""
    pythonDaq.daqSetRunState(state)


def start_run(self,params):
    """Start a run. """
    print('DaqWorker: start run with params')        
    print(params)
    
    configure()
    
    #defaults
    rate_str = 'Beam'
    count = 10000
    trigtype = 'Evr Running'
    
    # custom supplied
    if params != None:
        if params['filepath'] != None and params['filepath'] != '': 
            open_file(params['filepath'])
            if params['rate'] != None and params['rate'] != '':
                        rate_str = params['rate']
            if params['count'] != None:
                count = params['count']
            if params['trigtype'] != None:
                trigtype = params['trigtype']
                
        # set the run parameters
        print('trigtype ' + trigtype + ' rate_str ' + rate_str + ' count ' + str(count))
        pythonDaq.daqSetRunParameters(rate_str, count)





if __name__ == '__main__':
    

    # Open shared memory (need expert GUI to be running before this)
    pythonDaq.daqOpen('epix', 1)

    
    
    # this resets (hard and soft) and sets default
    configure()


    pythonDaq.daqOpenData('path_to_file')
    pythonDaq.daqSetRunParameters('10Hz', 100)
    pythonDaq.daqCloseData()
    


    
    
     
