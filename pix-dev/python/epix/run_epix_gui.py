"""
@author phansson
"""

import sys
import argparse
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from EpixReader import EpixReader, EpixFileReader
from online_gui_epix import EpixEsaForm

def get_args():
    parser = argparse.ArgumentParser('ePix online monitoring.')
    parser.add_argument('--light','-l', help='Data file with exposure.')
    parser.add_argument('--dark','-d', help='Data file with no signal (dark file).')
    args = parser.parse_args()
    print( args )
    return args


def main():

    # create the Qapp
    app = QApplication(sys.argv)

    # create the GUI
    form = EpixEsaForm()

    # create the data reader
    epixReader = None
    if args.light:
        epixReader = EpixFileReader(args.light)
    else:        
        raise NotImplementedError

    # add a dark frame if supplied
    if args.dark != None:
        epixReader.add_dark_file( args.dark, 10 )
        #epixReader.do_dark_frame_subtraction = True


    # Connect data to the GUI
    form.connect(epixReader,SIGNAL('newDataFrame'),form.newDataFrame)

    # Connect acq control to the reader
    form.connect(form, SIGNAL('acqState'),epixReader.change_state)

    # show the form
    form.show()

    # start the acquizition of frame (should go into GUI button I guess)
    epixReader.state = 'Running'

    # run the app
    sys.exit( app.exec_() )


if __name__ == "__main__":
    print ('Just Go')

    args = get_args()
    
    main()