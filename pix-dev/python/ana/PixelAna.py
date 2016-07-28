import sys
import os
import numpy as np
#sys.path.append(os.path.join(os.environ.get('DAQ'),python))
sys.path.append('../epix')
from PixDataFileReader import FileReader
import frame as camera_frame


class PixelData(object):
    def __init__(self,x,y,data):
        self.x = x
        self.y = y
        self.data = data

        


def get_data_frames(file_name, n_max):
    """Get data from file"""
    print('Read frames from file \"' + file_name + '\"')

    reader = FileReader(file_name, camera_frame.EpixFrame())

    reader.open()

    n = 0

    data_frames = None

    while n < n_max:

        print('read frame ' + str(n))

        # read next frame
        reader.read_next()

        # get a reference to the data frame object
        frame = reader.frame

        if frame == None:
            print('frame ' + str(n) + ' is corrupted? Skip')
            continue        

        # get a refence to the actual pixel matrix
        data  = frame.super_rows
        
        print(data)

        # first frame
        if n == 0:
            data_frames = np.zeros( (n_max, np.shape(data)[0], np.shape(data)[1]) )

        data_frames[n] = data

        n += 1

    print('Read ' + str(n) + ' frames')

    reader.close()

    return data_frames


