"""
@author phansson
"""


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

    def __init__(self,data):
        self.raw_data = data
        self.super_rows =  None
        self.__set_super_rows()
    

    def __set_super_rows(self):
        """ Organize into pixel super rows """
        #print('set super rows')
        self.super_rows =  np.zeros([EpixFrame.ny, EpixFrame.nx], dtype=np.uint16)
        for i in range( EpixFrame.ny ):
            self.__set_super_row(i)

    def __set_super_row(self,idx):
        """ Read a super row pf pixel data """

        # offset start with header words
        offset_start = idx*EpixFrame.len_super_row/2 +  EpixFrame.n_head
        offset_end = (idx+1)*EpixFrame.len_super_row/2 + EpixFrame.n_head
        
        #print('offset_start ', offset_start, ' offset_end ', offset_end)
        i = 0
        a = self.raw_data[offset_start:offset_end]
        #print('a ', a, ' len(a) ', len(a))
        #print ('i ', i)
        for val in self.raw_data[offset_start:offset_end]:            
            # bits[31:16]
            self.super_rows[idx][i] = ( (val >> 16) & 0xFFFF  )
            i += 1
            # bits[15:0] 
            self.super_rows[idx][i] = ( val & 0xFFFF  )
            i += 1
            #print(val,' ' , i)
            #if (i % 10) == 0:
            #    print('super row ', idx, ' x ', i, ' -> ', self.super_rows[idx][i]  )

        
        




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
        index=np.zeros((65536)).astype(np.uint64);
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
        index=np.zeros((65536)).astype(np.uint64);
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
    