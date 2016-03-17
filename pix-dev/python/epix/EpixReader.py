import sys
import os
import time
import numpy as np
import matplotlib
from frame import EpixFrame
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class EpixReader(QThread):
    """ Base class for reading epix data"""
    def __init__(self,parent=None):
        QThread.__init__(self, parent)
        # state
        self.state = 'Stopped'
        self.dark_frame_mean = None
        self.do_dark_subtraction = True
    

    def change_state(self):
        print('changing state from ', self.state)
        if self.state == 'Stopped':
            self.state = 'Running'
        elif self.state == 'Running':
            self.state = 'Stopped'
        else:
            print('Wrong state ', self.state)
            sys.exit(1)
        print('changing state to   ', self.state)
    
    def send_data(self, data):
        """Send data to other object using emit """

        print('Build the EpixFrame')
        frame = EpixFrame( data )

        if self.do_dark_subtraction:
            print('subtract dark frame')
            if self.dark_frame_mean == None:
                print('print no dark frame was available!')
                sys.exit(1)
            # subtract pixel by pixel
            frame.super_rows -= self.dark_frame_mean
            print('subtraction done')

        #send signal to GUIs with the data
        self.emit(SIGNAL("newDataFrame"),frame)
    

    def add_dark_file(self, filename, maxFrames=-1):
        """ Process dark file """
        print('Adding dark file from', filename)
        dark_frame_sum = None

        # check if that dark summary file already exists
        dark_filename = os.path.splitext( filename )[0] + '-summary.npz'

        if not os.path.isfile( dark_filename ):
            
            # number of reads from the file
            n = 0
            #number of frames read
            n_frames = 0
            
            with open(filename,'rb') as f:
                # read until the read function throws an exception
                try:
                    while True:
                        # read one word from file
                        fs = np.fromfile(f, dtype=np.uint32, count=4)[0]

                        # read the data
                        ret = np.fromfile(f, dtype=np.uint32, count=(4*fs) )

                        #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                        if fs == EpixFrame.framesize:

                            print (n, ' got frame with ', fs, ' words')

                            frame = EpixFrame(ret)

                            print (n, ' created EpixFrame')

                            # create the dark sum frame
                            if dark_frame_sum == None:
                                # use a 64 bit counter - not sure it matters
                                dark_frame_sum = np.zeros( frame.super_rows.shape, dtype=np.float64 )

                            # add frame to dark frame
                            dark_frame_sum += frame.super_rows

                            print (n, ' added to dark frame')


                            n_frames += 1

                        else:
                            print(n, ' got weird size from file fs ', fs , ' ret ', ret)

                        #ans = raw_input('next frame?')
                        #time.sleep(self.period)
                        print(' - got ', n_frames,' EpixFrames')

                        if maxFrames > 0 and n_frames >= maxFrames:
                            print('Reach frames needed')
                            break
                        n += 1
                except IndexError:
                    print(' - read ', n, ' times and got ', n_frames,' frames from file')

            # calculate mean for each pixel
            self.dark_frame_mean = dark_frame_sum / n_frames
            # enable by default
            self.do_dark_frame_subtraction = True

            # save to file
            np.savez( dark_filename, dark_frame_mean = self.dark_frame_mean)


        else:
            print ('dark file already exists ', dark_filename)
            dark_file = np.load(dark_filename)
            print ('loaded dark file')
            print dark_file.files
            print dark_file['dark_frame_mean']
            self.dark_frame_mean = dark_file['dark_frame_mean']
            dark_file.close()
            # enable by default
            self.do_dark_frame_subtraction = True
        print 'Done loading dark frame'


class EpixFileReader(EpixReader):
    """ Read epix data from a file"""
    def __init__(self,filename, parent=None):
        EpixReader.__init__(self, parent)
        # time in seconds between frame reads
        self.period = 5
        self.filename = filename
        # start the thread
        self.start()


    def run(self):

        print('Read frames from ', self.filename)

        # number of reads from the file
        n = 0
        #number of frames read
        n_frames = 0
        
        with open(self.filename,'rb') as f:
            # read until the read function throws an exception
            try:

                    
                while True:

                    # wait until state is correct
                    if self.state != 'Running':
                        print('EpixFileReader thread sleeping')
                        time.sleep(1.0)
                        continue
                                
                    # read one word from file
                    fs = np.fromfile(f, dtype=np.uint32, count=4)[0]

                    # read the data
                    ret = np.fromfile(f, dtype=np.uint32, count=(4*fs) )

                    #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                    if fs == EpixFrame.framesize:
                        print (n, ' got frame with ', fs, ' words')
                        n_frames += 1

                        # send the data
                        self.send_data( ret )
                    else:
                        print(n, ' got weird size from file fs ', fs , ' ret ', ret)
                    
                    #ans = raw_input('next frame?')
                    time.sleep(self.period)
                    n += 1
            except IndexError:
                print(' - read ', n, ' times and got ', n_frames,' frames from file')
    
        
        
