import sys
import os
import time
import numpy as np
import matplotlib
from frame import EpixFrame, EpixIntegratedFrame
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class EpixReader(QThread):
    """ Base class for reading epix data"""
    def __init__(self,parent=None):
        QThread.__init__(self, parent)
        
        # state
        self.state = 'Stopped'

        # mean of dark frames
        self.dark_frame_mean = None

        # switch to turn on/off subtraction
        self.do_dark_subtraction = True

        # time in seconds between frame reads
        self.frame_sleep = 1
        
        # integrate 'n' number of frames before sending
        self.integrate = 1
    
        # frame holding the data
        self.frame = None

    def set_integration(self,count):
        """ Set number of frames to integrate."""
        print('set integration to ', count, ' frames')
        self.integrate = count


    def set_state(self, state):
        print('set state \"', state,'\" from \"', self.state,'\"')
        if state != 'Running' and state != 'Stopped':
            print('\n\nERROR: Invalid state change to ', state)
        else:
            self.state = state
            self.emit(SIGNAL("newState"),self.state)


    def change_state(self):
        """ Change state of the GUI acquizition"""
        
        print('changing state from ', self.state)
        if self.state == 'Stopped':
            self.set_state('Running')
        elif self.state == 'Running':
            self.set_state('Stopped')
        else:
            print('Wrong state ', self.state)
            sys.exit(1)

    
    def send_data(self, data):
        """Send data to other objects using emit """

        print('Build the EpixFrame')
        frame = EpixIntegratedFrame( data )

        if self.do_dark_subtraction:
            print('subtract dark frame')
            if self.dark_frame_mean == None:
                print('print no dark frame was available!')
                sys.exit(1)
            # subtract pixel by pixel
            frame.super_rows -= self.dark_frame_mean
            print('subtraction done')

        # it's the first frame
        if self.frame == None:
            print('first frame')
            self.frame = frame
        else:
            print('add frame to ', self.frame.n, ' previous frames')
            self.frame.add_frame( frame )

        #check if we are ready to send data
        if self.frame.n >= self.integrate:
            print('sending frame after ', self.frame.n, ' integrations')
            self.emit(SIGNAL("newDataFrame"),self.frame)
            # reset frames
            self.frame = None
            #self.frame.n = 0
    
        
    

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

    def set_frame_period(self, val_sec):
        self.frame_sleep= val_sec

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
                    time.sleep(self.frame_sleep)
                    n += 1
            except IndexError:
                print(' - read ', n, ' times and got ', n_frames,' frames from file')
    
        
        
