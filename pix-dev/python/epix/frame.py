"""
@author phansson
"""


import time
import numpy as np
from epix import Epix100a, fmap


class EpixFrame(object):
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

    def __init__(self,data, asic=-1):
        # save the data in raw format
        self.raw_data = None #data

        # store the data in super rows
        self.super_rows =  None

        # setup data in raw order
        #self.__set_raw_super_rows()        

        # setup data in unscrambled order
        t0 = time.clock()
        #self.__set_super_rows(data)        
        self.__set_data(data,asic)        
        print('__set_super_rows in ', str( time.clock() - t0) + ' s')


    def add(self,other):
        """Add another frames data to the current one"""
        self.super_rows += other.super_rows
    

    def __get_asic_indexes(self, asic_nr):
        """ Return a tuple with indices"""
        return 0
        
    def get_data(self,asic):
        """Return data"""
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


    def __set_data(self, data, asic):
        """Organize data into a pixel image"""

        self.super_rows =  np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.int16)

        # Set only the data for the asic selected
        # right now I just loop through the super rows/columns and 
        # reject rows when they don't match the asic, if selected
        # Could just define the range in both super rows and columns 
        # directly here but I'm lazy and this is not that slow right now.

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
                self.super_rows[idx][ix] = ( (val >> 16) & 0xFFFF  )
                ix += 1
                # bits[15:0] 
                self.super_rows[idx][ix] = ( val & 0xFFFF  )
                ix += 1
                
                iword += 1
        
    
        
        
        
    def __set_super_rows(self,data):
        """ Organize into a pixel image """
        #print('set super rows')
        self.super_rows =  np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.int16)

        # read data super row by super row
        #print('SR -> R') 
        t0_sum = 0.
        for i in range( EpixFrame.ny ):

            t0 = time.clock()

            # offset start with header words
            offset_start = i*EpixFrame.nx/2 +  EpixFrame.n_head
            offset_end = (i+1)*EpixFrame.nx/2 + EpixFrame.n_head

            # get the correct id
            idx = self.__get_unscrambled_row( i )

            #print( i, ' -> ', idx)

            # set the data
            # pixel index along x
            ix = 0
            # loop over 32bit words
            for val in data[offset_start:offset_end]:
                # bits[31:16]
                self.super_rows[idx][ix] = ( (val >> 16) & 0xFFFF  )
                ix += 1
                # bits[15:0] 
                self.super_rows[idx][ix] = ( val & 0xFFFF  )
                ix += 1
            
            #print('set super row ', i ,' in ', str( time.clock() - t0) + ' s')
            t0_sum +=  (time.clock() - t0)
        print('set super rows with average time ', str( t0_sum/EpixFrame.ny), ' s')
    
    
    def __set_raw_super_rows(self,data):
        """ Organize into raw super rows """
        #print('set super rows')
        self.super_rows =  np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.int16)
        for i in range( EpixFrame.ny ):
            self.__set_raw_super_row(i,data)

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
    def __init__(self,data,asic=-1):
        EpixFrame.__init__(self,data,asic)
        self.n = 1
    
    def add_frame(self, frame):
        """Add the pixel data"""
        self.super_rows += frame.super_rows
        self.n += 1




class Frame(Epix100a):
    """Encapsulate reading of a frame."""

    def __init__(self):
        """Initialize the class. """
        print('Initialize Frame')
        try:
            Epix100a.__init__(self,"dummy")
        except ValueError:
            print('Caught error')
        self.debug = False
        self.raw_frame = None
        self.flat_frame = None

    def read_frame_from_file(self, f, idx):
        """ Prepare to read frames from an open file.

        The file pointer will move along so only this function should be used to process the file.

        Args:
            f (file): an open file to read from.
        """
        print('Read frame from file (idx ', idx, ')')
        i = 0
        nframes = 0
        nerrors = 0
        index=np.zeros((65536)).astype(np.int64);
        r = None

        print('Read attempt ' + str(i))

        r = np.fromfile(f, dtype=np.uint32, count=1)

        print('Read \n' , r, '\nfrom file')        

        fs = r[0]

        print('fs ' , fs, ' (framesize is ', self.framesize, ')' )

        if fs == self.framesize:

            # found a frame worth of data, store the index
            index[ nframes ] = idx+2*self.nhead+2;
            print('Store index ', index[ nframes ])

            # increment the frame counter
            nframes=nframes+1;
            #print nframes;

        else:
            # 
            nerrors=nerrors+1;
            print (nframes,nerrors,fs)

        # seek 4 words forward (why?)
        f.seek(4*fs,1);

        # find the next index (why?)
        idx=idx+2*fs+2;

        #except IndexError:
        #    print (' - indexing found '+str(nframes)+' frames.')
            #print 'index= '+str(idx);

        print('found index ', index)
        index=index[0:nframes];
        self.index=index;
        self.nframes=nframes;
        self.fmt[0,0]=nframes;

        print('index ', index, ' nframes ', self.nframes, ' fmt[0,] ', self.fmt[0,0])

        # save the data into a raw frame
        self.raw_frame = r
        print('Got raw frame ', self.raw_frame)

        # there is only one frame 
        raw_frame_index = fmap(self,0)
        print('f1map ', self.f1map)
        print('self.index[0] ', self.index[0])
        print('Got raw_frame_index ', raw_frame_index)
        self.flat_frame = self.raw_frame[raw_frame_index]
        print('Got flat frame ', self.flat_frame)
        
        

        # memmap a temp file -> this is a HACK!
        #print('create tempofile from r ', r
        #self.temp_memmap(r)

        # return the next index
        print('return idx ', idx)
        return idx
    
    def read_raw_frame_from_file(self, f):
        """ Read a frame from an open file.

        The file pointer will move along so only this function should be used to process the file.

        Args:
            f (file): an open file to read from.
        """
        print('Read frame from file')
        i = 0
        nframes = 0
        nerrors = 0
        index=np.zeros((65536)).astype(np.int64);
        r = None

        print('Read attempt ' + str(i))

        result_array = np.fromfile(f, dtype=np.uint32, count=1)

        print('Read array ' , r, 'from file')        

        fs = r[0]

        print('fs ' , fs, ' (framesize is ', self.framesize, ')' )

        if fs == self.framesize:

            # found a frame worth of data, store the index
            index[ nframes ] = idx+2*self.nhead+2;
            print('Store index ', index[ nframes ])

            # increment the frame counter
            nframes=nframes+1;
            #print nframes;

        else:
            # 
            nerrors=nerrors+1;
            print (nframes,nerrors,fs)

        # seek 4 words forward (why?)
        f.seek(4*fs,1);

        # find the next index (why?)
        idx=idx+2*fs+2;

        #except IndexError:
        #    print (' - indexing found '+str(nframes)+' frames.')
            #print 'index= '+str(idx);

        print('found index ', index)
        index=index[0:nframes];
        self.index=index;
        self.nframes=nframes;
        self.fmt[0,0]=nframes;

        print('index ', index, ' nframes ', self.nframes, ' fmt[0,] ', self.fmt[0,0])

        # save the data into a raw frame
        self.raw_frame = r
        print('Got raw frame ', self.raw_frame)

        # there is only one frame 
        raw_frame_index = fmap(self,0)
        print('f1map ', self.f1map)
        print('self.index[0] ', self.index[0])
        print('Got raw_frame_index ', raw_frame_index)
        self.flat_frame = self.raw_frame[raw_frame_index]
        print('Got flat frame ', self.flat_frame)
        
        

        # memmap a temp file -> this is a HACK!
        #print('create tempofile from r ', r
        #self.temp_memmap(r)

        # return the next index
        print('return idx ', idx)
        return idx
    
    def temp_memmap(self,data):
        filename = os.path.join(mkdtemp(), 'tmpmemmap.dat')
        print ('Open ', filename, ' and write ', len(data), ' data to it')
        with open(filename,'wb') as f:
            f.write(data)
        print('Done writing new tempfile')
        if self.fin != None:
            del self.fin
        self.fin = np.memmap(filename, dtype=np.int16, mode='r')
        print('memmap file\n', self.fin)
    
    def debug_print(self,*msg):
        if self.debug:
            s = '[ Frame ] : '
            print(s,msg)
    
