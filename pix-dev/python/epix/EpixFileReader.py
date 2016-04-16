"""
This file contains a reader of ePix data from a file.
"""
import time
import numpy as np
from EpixReader import *

class EpixFileReader(EpixReader):
    """ Read epix data from a file"""
    def __init__(self,filename, parent=None):
        EpixReader.__init__(self, parent)
        self.filename = filename
        # start the thread
        self.start()



    def run(self):

        print('Read frames from ', self.filename)

        # number of reads from the file
        n = 0
        #number of frames read
        n_frames = 0
        
        # timers
        t0_last = 0

        with open(self.filename,'rb') as f:
            # read until the read function throws an exception
            try:

                    
                while True:

                    # wait until state is correct
                    if self.state != 'Running':
                        if EpixReader.debug: print('EpixFileReader thread waiting')
                        self.sleep(1)
                        continue


                    # determine read interval
                    self.do_frame_sleep()
                                
                    t0 = time.clock()
                    t0_last = t0

                    # read one word from file
                    fs = np.fromfile(f, dtype=np.uint32, count=4)[0]

                    # read the data
                    # read the whole frame, it's really fast
                    ret = np.fromfile(f, dtype=np.uint32, count=(4*fs) )

                    if EpixReader.debug: print('read data in ', str( time.clock() - t0) + ' s')
                    

                    #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                    if fs == EpixFrame.framesize:
                        if EpixReader.debug: print (n, ' got frame with ', fs, ' words')
                        n_frames += 1
                        
                        # send the data
                        #self.send_data( ret )
                        self.emit_data( ret )
                    else:
                        print(n, ' got weird size from file fs ', fs , ' ret ', ret)
                    
                    #ans = raw_input('next frame?')
                    #time.sleep(self.frame_sleep)
                    n += 1
            except IndexError:
                print(' - read ', n, ' times and got ', n_frames,' frames from file')
    
