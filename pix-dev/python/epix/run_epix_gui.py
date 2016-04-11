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
from daq_worker import DaqWorker

def get_args():
    parser = argparse.ArgumentParser('ePix online monitoring.')
    parser.add_argument('--daq', type=bool,default=True, help='Data file with exposure.')
    parser.add_argument('--light','-l', help='Data file with exposure.')
    parser.add_argument('--dark','-d', help='Data file with no signal (dark file).')
    parser.add_argument('--go','-g',action='store_true',help='start acquisition')
    parser.add_argument('--debug',action='store_true',help='debug toggle')
    parser.add_argument('--asic','-a', type=int, default=0, help='ASIC to read data from (0-3, -1 for all).')
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

    # set debug flag for the reader
    EpixReader.debug = args.debug

    # initialize the state (need to set the GUI status...)
    epixReader.set_state('Stopped')

    # read only selected asic
    epixReader.select_asic( args.asic )

    # set the form at startup
    form.combo_select_asic.setCurrentIndex( args.asic + 1 )
    print('current index ' + str( form.combo_select_asic.currentIndex() ) )
    
    # Connect data to the GUI
    form.connect(epixReader,SIGNAL('newDataFrame'),form.newDataFrame)
    form.connect(epixReader,SIGNAL('newState'),form.newState)

    # Connect acq control to the reader
    form.connect(form, SIGNAL('acqState'),epixReader.change_state)
    form.connect(form, SIGNAL('integrationCount'),epixReader.set_integration)
    form.connect(form, SIGNAL('selectASIC'),epixReader.select_asic)
    form.connect(form, SIGNAL('selectAnalysis'),epixReader.select_analysis)
    form.connect(form, SIGNAL('selectDarkFile'),epixReader.add_dark_file)
    form.connect(form, SIGNAL('formBusy'),epixReader.set_form_busy)


    # open the control GUI and connection to the DAQ
    # if we are reading from a file then don't use the daq worker
    daq_worker  = None
    if not args.light:
        daq_worker  = DaqWorker()    
        form.connect_daq_worker_gui( daq_worker )
            
    # add a dark frame if supplied
    if args.dark != None:
        form.textbox_dark_file.setText( args.dark)
        form.on_dark_file_select()
        #epixReader.add_dark_file( args.dark, 10, 'median' )
        #epixReader.do_dark_frame_subtraction = True


    # show the form
    form.show()

    # start the acquizition of frame (should go into GUI button I guess)

    if args.go:
        epixReader.set_state('Running')

    print('333')

    # run the app
    sys.exit( app.exec_() )


if __name__ == "__main__":
    print ('Just Go')

    args = get_args()
    
    main()
