import sys
import os
import time
import numpy as np
from frame import EpixFrame
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pix_utils import FrameTimer, get_timer_data

class EpixReader(QThread):
    """ Base class for reading epix data"""
    debug = False
    def __init__(self, framesize, parent=None):
        QThread.__init__(self, parent)

        # size of the data frame to read
        self.framesize = framesize

        # state
        self.state = 'Stopped'

        # mean of dark frames
        self.dark_frame_mean = None

        # time in seconds between frame reads
        self.frame_sleep = 0
        
        # integrate 'n' number of frames before sending
        self.integrate = 1
    
        # frame holding the data
        self.frame = None

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


    #def select_dark_file(self,t):
    #    """Select a new dark file."""
    #    #if EpixReader.debug: 
    #    print('[EpixReader]: select dark file ' + t)
    #    self.add_dark_file(t)

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
        #print('[EpixReader]: emit data done, ' + t0.toString() + ' (' + str(QThread.currentThread()) + ')')
        if self.n_emit % 10 == 0:
            tot, n = get_timer_data(self.timers)
            print('[EpixReader]: n_emit {0} n_emit_busy {1} i.e. {2}% busy in {3} sec/frame ({4}) '.format( self.n_emit, self.n_emit_busy, 100*float(self.n_emit_busy)/float(self.n_emit_busy + self.n_emit), float(tot)/float(n), str(QThread.currentThread())))
            del self.timers[:]
            self.n_emit = 0
            self.n_emit_busy = 0
        self.n += 1
    

    def set_frame_sleep(self, val_msec):
        """Set the number of msec to sleep extra between reading frames."""
        self.frame_sleep = val_msec

    def do_frame_sleep(self):
        """Sleep for a some time."""
        if self.frame_sleep > 0:
            n = 0
            n_target = self.frame_sleep
            #print('sleep ' + str(self.frame_sleep))
            while (n < self.frame_sleep):
                time.sleep(0.001)
                n += 1
            #if n_frames % 10 == 0: print('[EpixShMemReader] sleeps for {0} sec before reading'.format(self.frame_sleep))


        
        
