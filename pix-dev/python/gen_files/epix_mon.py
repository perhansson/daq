"""
@author: phansson
"""


import sys
import os.path
import argparse
import numpy as np
import pix_utils as utils
import matplotlib.pyplot as plt
from epix import Dark
from frame import Frame
from DataFileReader import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
#import pythonDaq
import time

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
#import matplotlib.pyplot as plt



def get_args():
    parser = argparse.ArgumentParser('ePix monitor reader.')
    parser.add_argument('--ana','-a', action='store_true', help='Run analysis')
    parser.add_argument('--light','-l', help='Data file with exposure.')
    parser.add_argument('--dark','-d', help='Data file with no exposure (dark file).')
    parser.add_argument('--tag','-t', default='flat',)
    args = parser.parse_args()
    print( args )
    return args



def run_analysis():

    # turn on interactive use of pyplot
    plt.ion()

    # read in and process dark file if it's supplied
    dark_frames = None
    if args.dark != None:
        print('Reading dark frames from ', args.dark)
        filename_dark_flat = utils.get_flat_filename( args.dark, args.tag )
        
        #process the dark file
        dark_frames = Dark(args.dark,filename_dark_flat,100)
        
    else:
        print('No dark file supplied.')

    # read frames one by one, either from file or shared memory

    if args.light != None:

        print('Read frames from data file ', args.light)

        # create the frame object that holds the frame
        frame = Frame()
        frame.debug = True
        
        # read the binary file
        idx = 0
        nframes = 0
        with open(args.light,'rb') as f:

            while True:
                try:
                    print('Read frame from file  idx ', idx)
                    # read a frame from the file
                    idx = frame.read_frame_from_file(f, idx)

                    print('frame at index ', frame.index)
                    print('frame nframes ', frame.nframes)
                    print('new idx ', idx)

                    print('raw frame ', frame.raw_frame)
                    print('flat frame ', frame.flat_frame)

                    nframes += frame.nframes
                    print('Read ', nframes, ' so far')
                except IndexError:
                    print(' caught IndexError: found ', nframes, nframes)
                    break
        
    else:
         print('Read frames from shared mem is not implemented yet')



def run_mon():
    app = QApplication(sys.argv)
    form = Form(0.1)
    form.show()
    dread = DataFileReader(args.light)
    form.connect(dread,SIGNAL('newDataFrame'),form.newDataFrame)
    app.exec_()


if __name__ == '__main__':
    print ('Just Go')

    args = get_args()


    if args.ana:
        run_analysis()
    else:
        run_mon()

        

        
