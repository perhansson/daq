"""
This file contains a reader of ePix data from shared memory using generic daq tools.
"""
import os
import sys
from EpixReader import *
#sys.path.append(os.path.join(os.environ.get('DAQ'),python))
import pythonDaq

class EpixShMemReader(EpixReader):
    """Read epix data from shared memory"""    
    def __init__(self, parent=None):
        EpixReader.__init__(self, parent)
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

        # timers
        t0_nframes = 0.
        t0_last = 0

        while True:

            # wait until state is correct
            if self.state != 'Running':
                if EpixReader.debug: print('EpixShMemReader thread waiting')
                self.sleep(1)
                continue
 
            # determine read interval
            self.do_frame_sleep()
           
            t0 = time.clock()
            t0_last = t0

            # read from shared memory
            data = pythonDaq.daqSharedDataRead()

            dt = time.clock() - t0
            
            # first word is frame length
            if data[0] == 0:
                if EpixReader.debug: print('Read n ', n, ' found empty frame')
                time.sleep(0.001)
            
            elif data[0] > 0:
                if EpixReader.debug: print('Read n ', n, ' found ', data[0], ' bytes with type ', data[1])
                if data[1] == 0:
                    if data[0] == EpixFrame.framesize:

                        # found a frame of the right size
                        n_frames += 1

                        # update timer sum for a frame
                        t0_nframes += dt
                        if n_frames % 10 == 0:
                            print('Read  {0} frames with {1} frame/sec ({2})'.format(n_frames, t0_nframes/10., str(QThread.currentThread())))
                            t0_nframes = 0.

                        # send the data
                        #self.send_data( data[2] )
                        self.emit_data( data[2] )
                else:
                    print('Read n ', n, ' got type  ', data[1])
            
            else:
                print('Read n ', n, ' got weird size ', data[0])

            n += 1

        

