"""
@author phansson
"""

import sys
import argparse
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from DarkReader import DarkFileReader
from PixFileReader import FileReader
from PixShMemReader import ShMemReader
from CpixMainWindow import *
from daq_worker import DaqWorker
from frame_worker import CpixFrameWorkerController
import frame as camera_frames

def get_args():
    parser = argparse.ArgumentParser('cPix online monitoring.')
    parser.add_argument('--light','-l', help='Data file with exposure.')
    parser.add_argument('--dark','-d', help='Data file with no signal (dark file).')
    parser.add_argument('--go','-g',action='store_true',help='start acquisition')
    parser.add_argument('--debug',action='store_true',help='debug toggle')
    parser.add_argument('--asic','-a', type=int, default=0, help='ASIC to read data from (0-3, -1 for all).')
    parser.add_argument('--update','-u', type=int, default=0, help='Time in in milliseconds to sleep between reading a frame.')
    parser.add_argument('--integration','-i', default=1, help='Number of frames to integrate.')
    args = parser.parse_args()
    print( args )
    return args


def main():

    # create the Qapp
    app = QApplication(sys.argv)

    # get the frame type from camera arg
    camera = 'cpix'
    frame = camera_frames.CpixFrame()

    # create the data reader
    reader = None
    if args.light:
        reader = FileReader(args.light, frame.get_framesize())
        # use a standard hold-off time if not given
        if args.update == 0:
            args.update = 200
    else:        
        reader = ShMemReader(frame.get_framesize())

    # create the dark file reader
    darkReader = DarkFileReader(camera)

    # set a sleep timer in sec's between frame reads
    reader.set_frame_sleep(args.update)

    # set debug flag for the reader
    reader.debug = args.debug

    # initialize the state (need to set the GUI status...)
    reader.set_state('Stopped')

    #### create the data frame processor
    frameProcessor = CpixFrameWorkerController('cpix_frame_processor', frame)

    # connect the data frame from reader to processor
    reader.connect(reader, SIGNAL('data_frame'), frameProcessor.worker.process)

    # read only selected asic
    frameProcessor.worker.select_asic( args.asic )

    #### create the main GUI
    form = CpixMainWindow(parent=None, debug=False)

    # this might be a little weird but I need to connect signals firectly 
    # from widgets started inside the gui to the frame processor...
    form.frame_processor = frameProcessor

    # set the form at startup
    form.combo_select_asic.setCurrentIndex( args.asic + 1 )

    # set the integration for the start
    form.set_integration( args.integration )
    
    # Connect reader to the GUI
    form.connect(reader,SIGNAL('newState'),form.newState)

    # Connect GUI to the reader
    form.connect(form, SIGNAL('acqState'),reader.change_state)
    form.connect(form, SIGNAL('createDarkFile'),darkReader.create_dark_file)
    form.connect(form, SIGNAL('readDarkFile'), frameProcessor.worker.read_dark_file)    

    # Connect data processor to the GUI
    frameProcessor.worker.connect(frameProcessor.worker,SIGNAL('new_data'), form.newDataFrame)
    form.connect(form, SIGNAL('selectASIC'),frameProcessor.worker.select_asic)
    form.connect(form, SIGNAL('selectAnalysis'),frameProcessor.worker.select_analysis)
    #form.connect(form, SIGNAL('formBusy'),frameProcessor.worker.set_form_busy)


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
        #reader.add_dark_file( args.dark, 10, 'median' )
        #reader.do_dark_frame_subtraction = True


    # show the form
    form.show()

    # start the acquizition of frame (should go into GUI button I guess)

    if args.go:
        reader.set_state('Running')


    print ('[run_cpix_gui]: main thread ' , app.instance().thread())


    # run the app
    sys.exit( app.exec_() )


if __name__ == "__main__":
    print ('Just Go')

    args = get_args()
    
    main()
