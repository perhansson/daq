import sys
import os
import time
import numpy as np
import frame as camera_frame
from pix_utils import FrameTimer, get_timer_data
from PixDataFileReader import FileReader as reader

class DarkReader(object):
    """ Read frames from file"""
    debug = False
    def __init__(self, frame_type):
        print('[DarkReader]: init ' + frame_type)
        self.frame = None
        if frame_type == 'epix100a':
            self.frame = camera_frame.EpixFrame()
        elif frame_type == 'cpix':
            self.frame = camera_frame.CpixFrame()
        print(self.frame)
        
    def init(self,filename):
        self.reader = reader(filename,self.frame)
        self.reader.open()

    def read_next(self):
        """Read next frame from the file to memory."""
        self.reader.read_next()
        return self.reader.frame
    
    def close(self):
        self.reader.close()
    

    def create_dark_file(self, filename, maxFrames=10, alg='median'):
        """ Process dark file """
        print('[DarkReader]: Adding dark file from', filename)
        dark_frame_sum = None

        # check if that dark summary file already exists
        dark_filename = os.path.splitext( filename )[0] + '-summary.npz'

        if not os.path.isfile( dark_filename ):
            
            print('[DarkReader]: create dark file {0}'.format(dark_filename))

            # number of reads from the file
            n = 0
            #number of frames read
            n_frames = 0
            
            # hold all the dark frames in memory ?
            dark_frames = np.zeros( (maxFrames, self.frame.get_ny(), self.frame.get_nx()) )

            # initialize the reader
            self.init(filename)
            
            while n_frames < maxFrames:

                print ('[DarkReader]: read dark frame ' + str(n_frames))

                data_frame = self.read_next()

                print ('[DarkReader]: adding dark frame ' + str( n_frames))
                
                # create the dark sum frame
                if dark_frame_sum == None:
                    # use a 64 bit counter - not sure it matters
                    dark_frame_sum = np.zeros( self.frame.super_rows.shape, dtype=np.float64 )
                    
                # add frame to dark frame
                dark_frame_sum += data_frame.super_rows
                
                # save the frame
                dark_frames[n_frames] = data_frame.super_rows
                
                n_frames += 1

            
            # check that we got frames at all
            ok = False
            if n_frames <= 0:
                print('[EpixReader]: ERROR: no dark frames where found in file.')
            elif n_frames > 0 and n_frames < maxFrames:
                print('[EpixReader]: WARNING: did not find all {0} frames, only got {1}'.format(maxFrames, n_frames))
            else:
                print('[EpixReader]: Got ' + str(n_frames) + ', now calculate stats.') 

                # calculate mean for each pixel
                mean = dark_frame_sum / float(n_frames)

                # calculate the median
                median = np.median(dark_frames, axis=0)
                print('[EpixReader]: save dark frame mean')
                print( mean)
                print('[EpixReader]: save dark frame median')
                print( median)
                # save to file
                np.savez( dark_filename, dark_frame_mean = mean, dark_frame_median = median)
                ok = True
            
            if ok:
                print('[EpixReader]: Dark file created.')
            else:
                print('[EpixReader]: ERROR: Dark file not created.')
        
        else:
            # the dark file summary exists
            print ('[EpixReader]: dark file exists ', dark_filename)
            
        print( '[EpixReader]: Done loading dark frame')
    

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


