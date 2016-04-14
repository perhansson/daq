import sys
import os
import time
import numpy as np
from frame import EpixFrame, EpixIntegratedFrame
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pix_utils import toint, dropbadframes, FrameAnalysisTypes

class EpixReader(QThread):
    """ Base class for reading epix data"""
    debug = False
    def __init__(self,parent=None):
        QThread.__init__(self, parent)
        
        # state
        self.state = 'Stopped'

        # type of analysis
        self.frame_analysis = FrameAnalysisTypes.get('none')

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
        self.n_sent = 0
        self.n_sent_busy = 0

        # number of frames not sent due to busy
        self.n_busy = 0

        # number of frames sent

        # time to build and send frame
        self.__t0_sum_send_data = 0.

        # form busy
        self.form_busy = False
    

    def set_form_busy(self,a):
        """ Set busy word from form."""
        if EpixReader.debug: 
            print('[EpixReader]: set form busy to  ' + str(a) )
        self.form_busy = a
    
    def select_analysis(self,a):
        """ Set analysis to be applied to frames."""
        if EpixReader.debug: print('[EpixReader]: set frame analysis to ' + a.name )
        self.frame_analysis = a

    def set_integration(self,count):
        """ Set number of frames to integrate."""
        if EpixReader.debug: print('[EpixReader]: set integration to ', count, ' frames')
        self.integrate = count

    def select_asic(self, asic):
        """Select which asic to read data from."""
        if EpixReader.debug: print('[EpixReader]: select asic ', asic)
        self.selected_asic = asic

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

    
    def send_data(self, data):
        """Send data to other objects using emit """

        t0=time.clock();

        t1=time.clock();
        frame = EpixIntegratedFrame( data, self.selected_asic )

        if EpixReader.debug: print('[EpixReader]: Built EpixFrame in ' +  str( time.clock() - t1) + ' s')

        
        # add a dimension to fit the existing function
        t1=time.clock()
        tmp = np.empty([1,frame.super_rows.shape[0],frame.super_rows.shape[1]])
        tmp[0] = frame.super_rows
        tmp, dropped = dropbadframes(tmp)
        if tmp.size == 0:
            print '[ EpixReader ] : WARNING dropped frame'
            return
        else:
            if EpixReader.debug: print ('not a bad frame')
        
        if EpixReader.debug: print('[EpixReader]: Drop time total is ' + str( time.clock() - t1) + ' s')

        if self.do_dark_subtraction:
            if EpixReader.debug: print('[EpixReader]: subtract dark frame')
            #print('[EpixReader]: 1,727 raw ', frame.super_rows[1][727], ' dark mean ', self.dark_frame_mean[1][727])
            if self.dark_frame_mean == None:
                print('[EpixReader]: no dark frame is available!')
                #sys.exit(1)
            else:
                # subtract pixel by pixel
                frame.super_rows -= toint( self.dark_frame_mean )
                if EpixReader.debug: print('[EpixReader]: subtraction done')
                #print('[EpixReader]: 1,727 after ', frame.super_rows[1][727], ' dark mean ', self.dark_frame_mean[1][727])
        
        # do analysis
        frame.super_rows, frame.clusters = self.frame_analysis.process(frame.super_rows)

        # it's the first frame
        if self.frame == None:
            if EpixReader.debug: print('[EpixReader]: first frame')
            self.frame = frame
        else:
            if EpixReader.debug: print('[EpixReader]: add frame to ', self.frame.n, ' previous frames')
            self.frame.add_frame( frame )

        #check if we are ready to send data
        if self.frame.n >= self.integrate:

            if self.form_busy:
                print('[EpixReader]: form is busy.')
                self.n_busy += 1
            else:
                if EpixReader.debug: 
                    print('[EpixReader]: sending frame after ', self.frame.n, ' integrations')
                    print('[EpixReader]: data ', self.frame.super_rows)
                self.emit(SIGNAL("newDataFrame"),self.frame)
                # timers
                self.n_sent += 1
                self.n_sent_busy +=1
                self.__t0_sum_send_data += time.clock() - t0
                
            # reset fames
            self.frame = None
            #self.frame.n = 0

        # print timing
        if self.n_sent % 10 == 0:
            print('[EpixReader]: sent total of {0} frames with {1} sec/frame. busy {2} of {3} or {4}% busy in thread {5}'.format( self.n_sent, self.__t0_sum_send_data/10., self.n_busy, self.n_sent_busy+self.n_busy, 100*float(self.n_busy)/float(self.n_sent_busy+self.n_busy), str(QThread.currentThread())))
            #print('[EpixReader]: send_data current thread ' + str(QThread.currentThread()))
            self.__t0_sum_send_data = 0.
            self.n_busy = 0
            self.n_sent_busy = 0
        


    def add_dark_file(self, filename, maxFrames=10, alg='mean'):
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
                        fs = np.fromfile(f, dtype=np.uint32, count=4)[0]

                        # read the data
                        ret = np.fromfile(f, dtype=np.uint32, count=(4*fs) )

                        #print ('got a frame of data from file ', self.filename, ' with shape: ', ret.shape)
                        if fs == EpixFrame.framesize:

                            print (n, ' got frame with ', fs, ' words')

                            frame = EpixFrame(ret)

                            print (n, ' created EpixFrame')

                            tmp = np.empty([1,frame.super_rows.shape[0],frame.super_rows.shape[1]])
                            tmp[0] = frame.super_rows
                            tmp, dropped = dropbadframes(tmp)
                            if tmp.size == 0:
                                print 'dropped frame'
                                continue
                            else:
                                print 'not a bad frame'

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
                self.dark_frame_mean = dark_frame_sum / n_frames
                # enable by default
                self.do_dark_frame_subtraction = True

                # calculate the median
                self.dark_frame_median = np.median(dark_frames, axis=0)
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
            self.dark_frame_mean = dark_file['dark_frame_mean']
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
                #print('n ' + str(n) + ' / ' + str(n_target))
                #if n > self.frame_sleep:
                #    print('WHATA F')
                #if n > 100:
                #    print('WHATA F2')
    
            #if n_frames % 10 == 0: print('[EpixShMemReader] sleeps for {0} sec before reading'.format(self.frame_sleep))
    

        
        
