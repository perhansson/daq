"""
Classes to handle data formats for different cameras.
@author phansson
"""


import time
import numpy as np
from epix import Epix100a, fmap
from pix_utils import FrameTimer as timer


class EpixFrame(object):
    '''Convert readout order into an ordered pixel image for Epix100a.'''
    nx = 768
    ny = 708
    n_head=8
    n_super_rows = 710
    n_env_super_rows = 2
    n_tps_words = 2
    n_footer_words = 1
    len_super_row = nx
    #nblocks=16;
    #nbcols=92;
    npix=nx*ny;
    framesize= n_head + n_super_rows*len_super_row/2 + n_tps_words + n_footer_words
    n_asics = 4

    def __init__(self,data = None, asic=-1):

        # store a full readout frame
        self.super_rows = np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.int16)

        # set the data if available
        if data != None:
            self.set_data_fast(data)        
            #self.set_data(data,asic)        

        # clusters
        self.clusters = []


    def add(self,other):
        """Add another frame to the current one"""
        self.super_rows += other.super_rows
        self.clusters.extend(other.clusters)
        
    def get_data(self,asic):
        """Return data for a given asic or the full frame."""
        # see if we want all of them
        if asic < 0:            
            return self.super_rows
        elif asic == 0:            
            return self.super_rows[EpixFrame.ny/2: , EpixFrame.nx/2:]
        elif asic == 1:            
            return self.super_rows[:EpixFrame.ny/2 , EpixFrame.nx/2:]
        elif asic == 2:            
            return self.super_rows[:EpixFrame.ny/2 , :EpixFrame.nx/2]
        elif asic == 3:            
            return self.super_rows[EpixFrame.ny/2: , :EpixFrame.nx/2]
        else:
            print('ERROR invalid asic nr \"', asic, '\", must be less than ', EpixFrame.n_asics )
    
                
    def __get_unscrambled_row(self, super_row):      
        k = super_row/2
        r = super_row%2
        if r != 0:
            i = EpixFrame.ny/2 - ( k + r)
        else:
            i = EpixFrame.ny/2 + ( k + r)
        return i


    def reset(self):
        """Fill frame with zeroes."""
        self.super_rows.fill(0)
    

    #def set_data_fast(self, data, asic):
    #    #np.concatenate(( np.flipud(out[:,nx:2*nx]), out[:,0:nx]), axis=0)
    
    def set_data(self, data, asic):
        """Organize data into an unscrambled image."""

        # Note that I don't clear the frame here explicitly
        #self.super_rows =  np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.int16)

        # Set only the data for the asic selected
        # this is kind of hacky now.

        for i in range( EpixFrame.ny ):

            # offset start with header words
            offset_start = i*EpixFrame.nx/2 +  EpixFrame.n_head 
            offset_end = (i+1)*EpixFrame.nx/2 + EpixFrame.n_head

            # get the correct id
            idx = self.__get_unscrambled_row( i )
            
            # reject the row if it's not on the selected half of the sensor
            if (asic == 0 or asic == 3) and idx < EpixFrame.ny/2:
                continue
            if (asic == 1 or asic == 2) and idx >= EpixFrame.ny/2:
                continue

            #print( i, ' -> idx ', idx, ' ok')

            # pixel index along x
            iword = 0
            ix = 0
            reject = False
            # loop over 32bit words            
            for val in data[offset_start:offset_end]:
                
                # reject the column if not on the selected asic
                reject = False
                if (asic == 0 or asic == 1) and iword < EpixFrame.nx/4:
                    reject = True
                if (asic == 2 or asic == 3) and iword >= EpixFrame.nx/4:
                    reject = True
                
                if reject:
                    iword += 1
                    ix += 2
                    continue
            
                # set the data finally
                # bits[31:16]
                self.super_rows[idx][ix] = ( val & 0xFFFF  )
                ix += 1
                # bits[15:0] 
                self.super_rows[idx][ix] = ( (val >> 16) & 0xFFFF  )
                ix += 1
                
                iword += 1
        
                   
    
    def set_data_fast(self,data):
        """ Organize into raw super rows """
        #print('set super rows')

        t0 = timer('set_data_fast')
        t0.start()
        
        nx = EpixFrame.nx
        ny = EpixFrame.ny
        i = 0

        # find the pixel data only
        offset_start = EpixFrame.n_head 
        #offset_start = i*EpixFrame.nx/2 +  EpixFrame.n_head 
        #offset_end = (i+1)*EpixFrame.nx/2 + EpixFrame.n_head
        #frame_data2 = data[offset_start:offset_end]        
        #frame_data2 = data[offset_start:offset_end]        
        # convert to array!
        frame_data = np.asarray(data[offset_start:((nx/2)*ny+offset_start)],dtype=np.uint32)

        # read out the packed pixel adc values
        frame_data_odd = (frame_data >> 16) & 0xFFFF 
        frame_data_even  = frame_data & 0xFFFF 
        #frame_data_even = (frame_data >> 16) & 0xFFFF 
        #frame_data_odd  = frame_data & 0xFFFF 

        # new int16 array to hold final result
        frame_data_new = np.empty(ny*nx, dtype=np.int16)

        #print('frame_data ' + str(np.shape(frame_data)))
        #print('frame_data_even ' + str(np.shape(frame_data_even)))
        #print('frame_data_odd ' + str(np.shape(frame_data_odd)))
        #print('frame_data_new ' + str(np.shape(frame_data_new)))
        #print('frame_data_new[::2] ' + str(np.shape(frame_data_new[::2])))
        #print('frame_data_new[1::2] ' + str(np.shape(frame_data_new[1::2])))

        # set even and odd columns
        frame_data_new[::2] = frame_data_even.astype(np.int16)
        frame_data_new[1::2] = frame_data_odd.astype(np.int16)
        
        # do some magic to reshape the super rows
        out = np.reshape(frame_data_new, (ny//2, nx*2))
        out = np.concatenate( (np.flipud( out[:,nx:2*nx] ), out[:,0:nx]), axis=0)
        
        self.super_rows = out

        t0.stop()
        #print('[EpixFrame]: ' + t0.toString())
    

    def __set_raw_super_row(self,idx,data):
        """ Read a super row pf pixel data """

        # offset start with header words
        offset_start = idx*EpixFrame.len_super_row/2 +  EpixFrame.n_head
        offset_end = (idx+1)*EpixFrame.len_super_row/2 + EpixFrame.n_head
        
        #print('offset_start ', offset_start, ' offset_end ', offset_end)
        i = 0
        a = data[offset_start:offset_end]
        #print('a ', a, ' len(a) ', len(a))
        #print ('i ', i)
        for val in data[offset_start:offset_end]:            
            # bits[31:16]
            self.super_rows[idx][i] = ( (val >> 16) & 0xFFFF  )
            i += 1
            # bits[15:0] 
            self.super_rows[idx][i] = ( val & 0xFFFF  )
            i += 1
            #print(val,' ' , i)
            #if (i % 10) == 0:
            #    print('super row ', idx, ' x ', i, ' -> ', self.super_rows[idx][i]  )

        
        
class EpixIntegratedFrame(EpixFrame):
    """ Hold integrated EpixFrames"""
    def __init__(self,data=None,asic=-1):
        EpixFrame.__init__(self,data,asic)
        if data != None:
            self.n = 1
        else:
            self.n = 0
    
    
    def add_frame(self, frame):
        """
        Add the pixel data

        Note, do not add clusters.
        
        """
        self.super_rows += frame.super_rows
        self.n += 1




    
