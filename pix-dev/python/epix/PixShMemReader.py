"""
This file contains a reader of ePix data from shared memory using generic daq tools.
"""
import os
import sys
import time
from PyQt4.QtCore import QThread
from PixReader import BaseReader
from pix_utils import FrameTimer, get_timer_data
#sys.path.append(os.path.join(os.environ.get('DAQ'),python))
import pythonDaq

class ShMemReader(BaseReader):
    """Read epix data from shared memory"""    
    def __init__(self, frame_size, parent=None):
        BaseReader.__init__(self, frame_size, parent)

        # timer list
        self.sh_timers = []

        # start the thread
        self.start()
        
    def run(self):
        """Read data from shared memory"""

        print('Read frame from shared memory')

        # open shared memory
        pythonDaq.daqSharedDataOpen('epix', 1)
        
        # number of reads
        n = 0

        # number of frames
        n_frames = 0

        while True:

            # wait until state is correct
            if self.state != 'Running':
                if BaseReader.debug: print('EpixShMemReader thread waiting')
                self.sleep(1)
                continue

            # timers
            t0 = FrameTimer('shmem run')
            t0.start()

            # determine read interval
            self.do_frame_sleep()
           
            # read from shared memory
            data = pythonDaq.daqSharedDataRead()

            # first word is frame length
            if data[0] == 0:
                if BaseReader.debug: print('Read n ', n, ' found empty frame')
                time.sleep(0.001)            
            elif data[0] > 0:
                if BaseReader.debug: print('Read n ', n, ' found ', data[0], ' bytes with type ', data[1])
                if data[1] == 0:
                    if data[0] == self.framesize:

                        # send the data
                        #self.send_data( data[2] )
                        self.emit_data( n_frames, data[2] )

                        # found a frame of the right size
                        n_frames += 1
                        
                        # timers
                        t0.stop()
                        self.sh_timers.append(t0)
                        if n_frames % 10 == 0:
                            tot, n = get_timer_data(self.sh_timers)
                            print('[EpixShReader]: n_frames {0} with {1} sec/frame ({2}) '.format( n_frames, float(tot)/float(n), str(QThread.currentThread())))
                            del self.sh_timers[:]
                            
                else:
                    print('Read n ', n, ' got type  ', data[1])
            
            else:
                print('Read n ', n, ' got weird size ', data[0])
            
            n += 1

        

