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
                time.sleep(1.0)
                continue
 
            # determine read interval
            if self.frame_sleep > 0:
                n = 0
                n_target = self.frame_sleep/0.01
                t0_test = time.clock()
                #print('t0_test {0} clock {1} t0_last {2}'.format(t0_test,time.clock(), t0_last))
                while True:
                    if n < n_target:
                        time.sleep(0.01)
                        n += 1
                    else:
                        break
                dt_test = time.clock() - t0_test
                if self.debug: 
                    if n_frames % 10 == 0: print('[EpixShMemReader] sleeps for {0} sec before reading'.format(self.frame_sleep))
           
            t0 = time.clock()
            t0_last = t0

            # read from shared memory
            data = pythonDaq.daqSharedDataRead()

            dt = time.clock() - t0
            
            # first word is frame length
            if data[0] == 0:
                if EpixReader.debug: print('Read n ', n, ' found empty frame')
                time.sleep(0.01)
            
            elif data[0] > 0:
                if EpixReader.debug: print('Read n ', n, ' found ', data[0], ' bytes with type ', data[1])
                if data[1] == 0:
                    if data[0] == EpixFrame.framesize:

                        # found a frame of the right size
                        n_frames += 1

                        # update timer sum for a frame
                        t0_nframes += dt
                        if n_frames % 10 == 0:
                            print('Read  {0} frames with {1} frame/sec'.format(n_frames, t0_nframes/10. ))
                            t0_nframes = 0.

                        # send the data
                        self.send_data( data[2] )
                else:
                    print('Read n ', n, ' got type  ', data[1])
            
            else:
                print('Read n ', n, ' got weird size ', data[0])

            n += 1

        

