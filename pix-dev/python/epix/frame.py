"""
Classes to handle data formats for different cameras.
@author phansson
"""


import time
import numpy as np
from pix_utils import FrameTimer as timer



class PixFrame(object):
    """Base class to store a readout frame."""

    def __init__(self, nx, ny, framesize):
        self.super_rows = np.zeros([ny, nx], dtype=np.int16)
        self.clusters = []
    
    def get_n_asics(self):
        """Abstract method."""
        raise NotImplementedError
    
    def get_nx(self):
        """Abstract method."""
        raise NotImplementedError

    def get_ny(self):
        """Abstract method."""
        raise NotImplementedError

    def get_framesize(self):
        """Abstract method."""
        raise NotImplementedError

    def set_data_fast(self,data):
        """Abstract method."""
        raise NotImplementedError

    def reset(self):
        """Fill frame with zeroes."""
        self.super_rows.fill(0)

    def add(self,other):
        """Add another frame to the current one"""
        self.super_rows += other.super_rows
        self.clusters.extend(other.clusters)
        
    def get_data(self,asic):
        """Abstract method."""
        raise NotImplementedError
    



class EpixFrame(PixFrame):
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
    asic_map = np.array([[2,1],[3,0]])

    def __init__(self):
        super(EpixFrame,self).__init__(EpixFrame.nx, EpixFrame.ny, EpixFrame.framesize)        

    def get_n_asics(self):
        """Abstract method."""
        return EpixFrame.n_asics

    def get_nx(self):
        """Abstract method."""
        return EpixFrame.nx

    def get_ny(self):
        """Abstract method."""
        return EpixFrame.ny

    def get_framesize(self):
        """Abstract method."""
        return EpixFrame.framesize

    def __get_unscrambled_row(self, super_row):      
        k = super_row/2
        r = super_row%2
        if r != 0:
            i = EpixFrame.ny/2 - ( k + r)
        else:
            i = EpixFrame.ny/2 + ( k + r)
        return i

    def get_data(self, asic, rotations=0):
        """Return data for a given asic or the full frame."""
        n_asics = self.get_n_asics()

        if asic >= n_asics:
            print('ERROR invalid asic nr \"', asic, '\", must be less than ', n_asics )
            return 
        
        # see if we want all of them
        if asic < 0:            
            return self.super_rows
        
        nx = self.get_nx()
        ny = self.get_ny()
        
        
        # check if the data frame is rotated, 
        # if so the asic nr and rows and cols needs to be rotated too
        sel_asic = asic
        if rotations > 0:
            asic_map_rot = np.rot90(self.asic_map,rotations)
            xr,yr = np.where(asic_map_rot == asic)
            print ('rotations ' + str(rotations))
            print ('xr,yr = ' + str(xr) + ',' + str(yr))
            sel_asic = self.asic_map[xr[0]][yr[0]]
            print("ROTATION asic " + str(asic) + ' -> ' + str(sel_asic))
            if rotations%2 != 0:
                print("flip nx,ny" + str(nx) + ',' + str(ny))
                ny_new = nx
                nx = ny
                ny = ny_new

        print("nx,ny" + str(nx) + ',' + str(ny))
        if sel_asic == 0:            
            return self.super_rows[ny/2: , nx/2:]
        elif sel_asic == 1:            
            return self.super_rows[:ny/2 , nx/2:]
        elif sel_asic == 2:            
            return self.super_rows[:ny/2 , :nx/2]
        elif sel_asic == 3:            
            return self.super_rows[ny/2: , :nx/2]
        else:
            print('ERROR invalid asic nr \"', sel_asic, '\", must be less than ', n_asics )
    

    def set_data_fast(self,data):
        """ Organize into raw super rows """
        #print('set super rows')

        t0 = timer('set_data_fast')
        t0.start()
        
        nx = self.get_nx()
        ny = self.get_ny()
        i = 0
        
        # find the pixel data only
        offset_start = EpixFrame.n_head 

        # convert to array!
        frame_data = np.asarray(data[offset_start:((nx/2)*ny+offset_start)],dtype=np.uint32)

        # read out the packed pixel adc values
        frame_data_odd = (frame_data >> 16) & 0xFFFF 
        frame_data_even  = frame_data & 0xFFFF 

        # new int16 array to hold final result
        frame_data_new = np.empty(ny*nx, dtype=np.int16)

        # set even and odd columns
        frame_data_new[::2] = frame_data_even.astype(np.int16)
        frame_data_new[1::2] = frame_data_odd.astype(np.int16)
        
        # do some magic to reshape the super rows
        out = np.reshape(frame_data_new, (ny//2, nx*2))
        out = np.concatenate( (np.flipud( out[:,nx:2*nx] ), out[:,0:nx]), axis=0)
        
        self.super_rows = out

        t0.stop()





class CpixFrame(PixFrame):
    '''Convert readout order into an ordered pixel image for Cpix.'''
    nx = 48
    ny = 48
    n_header_words=15
    n_footer_words = 1
    npix=nx*ny
    framesize= n_header_words + ny*nx/2 + n_footer_words
    n_asics = 1
    offset_frame_info_word = 14
    asic_map = [[0]]

    def __init__(self):
        super(CpixFrame,self).__init__(CpixFrame.nx, CpixFrame.ny, CpixFrame.framesize)
        
        # store counter id
        self.counter_id = -1

        # store asic id
        self.asic = -1
    
        # used to store corrected values, see correct function
        self.nx_offset = 16
        nx = self.get_nx()
        self.doff = np.zeros( np.shape(self.super_rows[:,nx-self.nx_offset:]) )

        # counter type
        self.counter_type = -1


    def get_n_asics(self):
        """Abstract method."""
        return CpixFrame.n_asics

    def get_nx(self):
        """Abstract method."""
        return CpixFrame.nx

    def get_ny(self):
        """Abstract method."""
        return CpixFrame.ny

    def get_framesize(self):
        """Abstract method."""
        return CpixFrame.framesize

    def get_data(self,asic):
        """Return data for a given asic or the full frame."""
        n_asics = self.get_n_asics()
        nx = self.get_nx()
        ny = self.get_ny()
        # see if we want all of them
        if asic < 1:            
            return self.super_rows
        else:
            print('ERROR invalid asic nr \"', asic, '\", must be less than ', n_asics )

    def __get_counter_type_from_data(self, data):
        """Extract counter type from the data."""
        return (data[CpixFrame.offset_frame_info_word] >> 4) & 0x00000001         

    def __get_asic_from_data(self, data):
        """Extract ASIC ID from the data."""
        return data[CpixFrame.offset_frame_info_word] & 0x0000000F     


    def set_data_fast(self,data):
        """ Organize into raw super rows """
        #print('set super rows')

        t0 = timer('set_data_fast')
        t0.start()

        i = 0
        ny = self.get_ny()
        nx = self.get_nx()

        # find the counter type
        self.counter_type = self.__get_counter_type_from_data(data)

        # find the asic
        self.asic = self.__get_asic_from_data(data)

        if self.counter_type != 0 and self.counter_type != 1:
            raise RuntimeError('counter type ' + str(self.counter_type) + ' is undefined.(asic ' + self.asic + ' from  word ' + str(data[offset_frame_info_word]) + ')')

        if self.asic < 0 or self.asic >=4:
            raise RuntimeError('asic ' + str(self.asic) + ' is undefined. ( word ' + str(data[offset_frame_info_word]) + ' counter ' + str(self.counter_type) + ')')


        # find the pixel data only
        offset_start = CpixFrame.n_header_words 

        # convert to array!
        frame_data = np.asarray(data[offset_start:(ny*(nx/2) + offset_start)],dtype=np.uint32)

        # read out the packed pixel adc values
        frame_data_odd = (frame_data >> 16) & 0xFFFF 
        frame_data_even  = frame_data & 0xFFFF 

        # new int16 array to hold final result
        frame_data_new = np.empty(ny*nx, dtype=np.int16)

        # set even and odd columns
        frame_data_new[::2] = frame_data_even.astype(np.int16)
        frame_data_new[1::2] = frame_data_odd.astype(np.int16)

        # now reshape into the pixel matrix form
        out = np.reshape(frame_data_new, (ny,nx))

        # set the member variable
        self.super_rows = out

        # apply correction
        self.correct_frame()

        t0.stop()
    

    def correct_frame(self):
        """Shift last self.nx_offset columns down one row."""

        # NOTE: row 0 will just get zeroes in the last self.nx_offset columns

        ny = self.get_ny()
        nx = self.get_nx()

        # fill/reset last self.nx_offset columns with zeroes
        self.doff.fill(0)

        # number of offsets in rows
        r = 1

        # assign the coulmns one row down
        self.doff[r:,:] = self.super_rows[:ny-r,nx-self.nx_offset:]

        # now assign back to the original object
        self.super_rows[:,nx-self.nx_offset:] = self.doff
        

    def get_counter_type(self):
        """Return counter type for the current frame."""
        return self.counter_type
