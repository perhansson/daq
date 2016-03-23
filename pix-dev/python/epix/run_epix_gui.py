"""
@author phansson
"""

import sys
import argparse
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from EpixReader import EpixReader
from EpixFileReader import EpixFileReader
from EpixShMemReader import EpixShMemReader
from online_gui_epix import EpixEsaForm

def get_args():
    parser = argparse.ArgumentParser('ePix online monitoring.')
    parser.add_argument('--light','-l', help='Data file with exposure.')
    parser.add_argument('--dark','-d', help='Data file with no signal (dark file).')
    parser.add_argument('--go','-g',action='store_true',help='start acquisition')
    args = parser.parse_args()
    print( args )
    return args


def main():

    # create the Qapp
    app = QApplication(sys.argv)

    # create the GUI
    form = EpixEsaForm(parent=None, debug=False)

    # create the data reader
    epixReader = None
    if args.light:
        epixReader = EpixFileReader(args.light)
        # set the simulated trigger rate
        epixReader.set_frame_period(0.1)
    else:        
        epixReader = EpixShMemReader()
    
    # add a dark frame if supplied
    if args.dark != None:
        epixReader.add_dark_file( args.dark, 10 )
        #epixReader.do_dark_frame_subtraction = True

    
    # Connect data to the GUI
    form.connect(epixReader,SIGNAL('newDataFrame'),form.newDataFrame)
    form.connect(epixReader,SIGNAL('newState'),form.newState)

    # Connect acq control to the reader
    form.connect(form, SIGNAL('acqState'),epixReader.change_state)
    form.connect(form, SIGNAL('integrationCount'),epixReader.set_integration)
    form.connect(form, SIGNAL('selectASIC'),epixReader.select_asic)
    form.connect(form, SIGNAL('selectAnalysis'),epixReader.select_analysis)

    # initialize the state (need to set the GUI status...)
    epixReader.set_state('Stopped')

    # show the form
    form.show()

    # start the acquizition of frame (should go into GUI button I guess)

    if args.go:
        epixReader.set_state('Running')

    # run the app
    sys.exit( app.exec_() )


if __name__ == "__main__":
    print ('Just Go')

    args = get_args()
    
    main()
