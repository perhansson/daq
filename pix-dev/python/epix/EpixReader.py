import sys
import os
import time
import numpy as np
from frame import EpixFrame, EpixIntegratedFrame
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pix_utils import FrameTimer, get_timer_data

class EpixReader(QThread):
    """ Base class for reading epix data"""
    debug = False
    def __init__(self,parent=None):
        QThread.__init__(self, parent)
        
        # state
        self.state = 'Stopped'

        # mean of dark frames
        self.dark_frame_mean = None

        # switch to turn on/off subtraction
        self.do_dark_subtraction = True

        # time in seconds between frame reads
        self.frame_sleep = 0
        
        # integrate 'n' number of frames before sending
        self.integrate = 1
    
        # frame holding the data
        self.frame = None

        # asic to read ( -1 to read all)
        self.selected_asic = -1

        # number of frames sent
        self.n_emit = 0
        self.n_emit_busy = 0        
        self.n = 0

        # time to build and send frame
        self.__t0_sum_send_data = 0.

        # form busy
        self.form_busy = False

        # timers
        self.timers = []
    

    def set_form_busy(self,a):
        """ Set busy word."""
        if EpixReader.debug: print('[EpixReader]: set busy to  ' + str(a) )
        self.form_busy = a

    def set_integration(self,count):
        """ Set number of frames to integrate."""
        if EpixReader.debug: print('[EpixReader]: set integration to ', count, ' frames')
        self.integrate = count

    def set_state(self, state):
        if EpixReader.debug: print('[EpixReader]: set state \"', state,'\" from \"', self.state,'\"')
        if state != 'Running' and state != 'Stopped':
            print('[EpixReader]: \n\nERROR: Invalid state change to ', state)
        else:
            self.state = state
            self.emit(SIGNAL("newState"),self.state)


    def change_state(self):
        """ Change state of the GUI acquizition"""
        
        if EpixReader.debug: print('[EpixReader]: changing state from ', self.state)
        if self.state == 'Stopped':
            self.set_state('Running')
        elif self.state == 'Running':
            self.set_state('Stopped')
        else:
            print('[EpixReader]: Wrong state ', self.state)
            sys.exit(1)


    def select_dark_file(self,t):
        """Select a new dark file."""
        #if EpixReader.debug: 
        print('[EpixReader]: select dark file ' + t)
        self.add_dark_file(t)

    def emit_data(self, frame_id, data):
        """Send out the data to connected slots."""

        #print('[EpixReader]: emit data (' + str(QThread.currentThread()) + ')')
        t0 = FrameTimer('emit ' + str(frame_id))
        t0.start()

        # check busy
        if self.form_busy:
            self.n_emit_busy += 1
        else:
            # actually send the data
            self.emit(SIGNAL('data_frame'),frame_id, data)
            self.n_emit += 1
            
        # timer stuff
        t0.stop()
        self.timers.append(t0)
        print('[EpixReader]: emit data done, ' + t0.toString() + ' (' + str(QThread.currentThread()) + ')')
        if self.n_emit % 10 == 0:
            tot, n = get_timer_data(self.timers)
            print('[EpixReader]: n_emit {0} n_emit_busy {1} i.e. {2}% busy in {3} sec/frame ({4}) '.format( self.n_emit, self.n_emit_busy, 100*float(self.n_emit_busy)/float(self.n_emit_busy + self.n_emit), float(tot)/float(n), str(QThread.currentThread())))
            del self.timers[:]
            self.n_emit = 0
            self.n_emit_busy = 0
        self.n += 1
    


    #def add_dark_file(self, filename, maxFrames=10, alg='mean'):
    def add_dark_file(self, filename, maxFrames=10, alg='median'):
        """ Process dark file """
        print('[EpixReader]: Adding dark file from', filename)
        dark_frame_sum = None

        # check if that dark summary file already exists
        dark_filename = os.path.splitext( filename )[0] + '-summary.npz'

        if not os.path.isfile( dark_filename ):
            
            print('[EpixReader]: create dark file {0}'.format(dark_filename))

            # number of reads from the file
            n = 0
            #number of frames read
            n_frames = 0
            
            # hold all the dark frames in memory ?
            dark_frames = np.zeros( (maxFrames, EpixFrame.ny, EpixFrame.nx) )

            with open(filename,'rb') as f:
                # read until the read function throws an exception
                try:
                    while True:
                        # read one word from file
                        fs = np.fromfile(f, dtype=np.uint32, count=1)[0]

                        # read the data
                        ret = np.fromfile(f, dtype=np.uint32, count=(1*fs) )

                        #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                        if fs == EpixFrame.framesize:

                            print (n, ' got frame with ', fs, ' words')

                            frame = EpixFrame(ret)

                            print (n, ' created EpixFrame')

                            #drop_frame = False                            
                            #s = np.sum(np.abs(np.diff(np.median(frame.super_rows, axis=0))))
                            #if s > 10000:
                            #    drop_frame = True
                            #if drop_frame:
                            #    print('DROP BAD FRAME')
                            #    continue
                            
                            
                            #tmp = np.empty([1,frame.super_rows.shape[0],frame.super_rows.shape[1]])
                            #tmp[0] = frame.super_rows
                            #tmp, dropped = dropbadframes(tmp)
                            #if tmp.size == 0:
                            #    print 'dropped frame'
                            #    continue
                            #else:
                            #    print 'not a bad frame'

                            # create the dark sum frame
                            if dark_frame_sum == None:
                                # use a 64 bit counter - not sure it matters
                                dark_frame_sum = np.zeros( frame.super_rows.shape, dtype=np.float64 )
                            
                            # add frame to dark frame
                            dark_frame_sum += frame.super_rows
                            
                            # save the frame
                            dark_frames[n_frames] = frame.super_rows

                            print (n, ' added to dark frame')


                            n_frames += 1

                        else:
                            print(n, ' got weird size from file fs ', fs , ' ret ', ret)

                        #ans = raw_input('next frame?')
                        #time.sleep(self.period)
                        print('[EpixReader]:  - got ', n_frames,' EpixFrames')

                        if maxFrames > 0 and n_frames >= maxFrames:
                            print('[EpixReader]: Reach frames needed')
                            break
                        n += 1
                except IndexError:
                    print('[EpixReader]:  - read ', n, ' times and got ', n_frames,' frames from file')
            
            # check that we got frames at all
            if n_frames <= 0:
                print('[EpixReader]: ERROR: no dark frames where found in file.')
            elif n_frames > 0 and n_frames < maxFrames:
                print('[EpixReader]: WARNING: did not find all {0} dark frames, only got {1}'.format(maxFrames, n_frames))
            else:
                print('[EpixReader]: Got ' + str(n_frames) + ', now calculate stats.') 

                # calculate mean for each pixel
                self.dark_frame_mean = dark_frame_sum / float(n_frames)
                # enable by default
                self.do_dark_frame_subtraction = True

                # calculate the median
                self.dark_frame_median = np.median(dark_frames, axis=0)
                print('save dark frame mean')
                print( self.dark_frame_mean)
                print('save dark frame median')
                print( self.dark_frame_median)
                # save to file
                np.savez( dark_filename, dark_frame_mean = self.dark_frame_mean, dark_frame_median = self.dark_frame_median)
            
            # now it should be there to be used
            self.add_dark_file( filename, maxFrames, alg)

        else:
            print ('dark file exists ', dark_filename)
            dark_file = np.load(dark_filename)
            print ('loaded dark file')
            print dark_file.files
            print dark_file['dark_frame_mean']
            print dark_file['dark_frame_median']
            #self.dark_frame_median = dark_file['dark_frame_median']
            if alg == 'mean':
                self.dark_frame_mean = dark_file['dark_frame_mean']
                self.emit(SIGNAL('dark_mean'), self.dark_frame_mean)
            elif alg == 'median':
                self.dark_frame_median = dark_file['dark_frame_median']
                self.dark_frame_mean = dark_file['dark_frame_median']
                self.emit(SIGNAL('dark_mean'), self.dark_frame_mean)
            else:
                print('this opt doesnt exist')
                sys.exit(1)
            #dark_file.close()
            # enable by default
            self.do_dark_frame_subtraction = True
        print 'Done loading dark frame'


    

    def set_frame_sleep(self, val_msec):
        self.frame_sleep = val_msec

    def do_frame_sleep(self):
        if self.frame_sleep > 0:
            n = 0
            n_target = self.frame_sleep
            #print('sleep ' + str(self.frame_sleep))
            while (n < self.frame_sleep):
                time.sleep(0.001)
                n += 1
            #if n_frames % 10 == 0: print('[EpixShMemReader] sleeps for {0} sec before reading'.format(self.frame_sleep))


        
        
