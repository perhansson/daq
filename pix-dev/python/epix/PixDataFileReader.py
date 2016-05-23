"""
This file contains a reader of ePix data from a file.
"""
import time
import numpy as np
from EpixReader import *

class FileReader(object):
    """ Read data from a file"""

    def __init__(self,filename, frame):
        self.filename = filename
        self.f = None
        self.frame = frame
        self.n = 0
        self.n_frames = 0

    def open(self):
        self.f = open(self.filename,'rb')

    def close(self):
        self.f.close()

    def read_next(self):

        print('Read frames from ', self.filename)

        # read until the read function throws an exception
        try:
            # read one word from file
            fs = np.fromfile(self.f, dtype=np.uint32, count=1)[0]
            
            # read the data
            # read the whole frame, it's really fast
            ret = np.fromfile(self.f, dtype=np.uint32, count=(1*fs) )
            
            #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
            if fs == self.frame.framesize:
                print (self.n, ' got frame with ', fs, ' words')
                
                # set the data
                self.frame.set_data_fast( ret )

                self.n_frames += 1                        
            else:
                print(self.n, ' got weird size from file fs ', fs , ' ret ', ret)
                
            self.n += 1
        except IndexError:
            print(' - read ', self.n, ' times and got ', self.n_frames,' frames from file')

