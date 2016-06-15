#!/usr/bin/python

import sys
import os
import time
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pix_threading import MyQThread
from pix_utils import toint, dropbadframes, FrameAnalysisTypes, FrameTimer, get_timer_data

printThreadInfo = False


class FrameWorker(QObject):
    """Process frames."""

    debug = False

    def __init__(self,name, frame):
        super(FrameWorker, self).__init__()
        self.name = name
        self.drop_bad_frames = False
        self.drop_bad_frames_2 = False
        self.do_dark_subtraction = True
        self.do_bad_pixel_map_subtraction = True
        self.drop_max_pixels_threshold = 100
        self.drop_max_pixels_count = 1000
        self.flip_frame = 1
        self.n_sent = 0
        self.n_drop = 0
        self.n_busy = 0
        self.n_process = 0
        self.__t0_ana_sum = 0
        self.__n_ana_sum = 0
        self.frame = frame
        self.dark_frame_mean = None
        self.bad_pixel_map = None
        self.selected_asic = -1
        self.process_timers = []
        self.form_busy = False
        self.frame_analysis = FrameAnalysisTypes.get('none')
        self.frame_id = -1

    def print_debug(self,msg,force=False):
        """Print decorated debug message."""
        if self.debug or force:
            print('[FrameWorker]: \"' + self.name + '\" : ' + msg )

    def print_thread(self,msg, force=True):
        """Print thread information to std out."""
        global printThreadInfo
        if printThreadInfo or force:
            self.print_debug(msg + ' in thread ' + str(QThread.currentThread()), force=True)
    
    def set_form_busy(self,a):
        """ Set busy word from form."""
        self.print_debug('set form busy to  ' + str(a) )
        self.form_busy = a

    def set_dark_mean(self, dark_frame_mean):
        self.dark_frame_mean = dark_frame_mean

    def set_bad_pixel_map(self, bad_pixel_map):
        self.bad_pixel_map = bad_pixel_map

    def read_dark_file(self,filename):
        """Read the dark file and extract the mean."""

        dark_filename = os.path.splitext( filename )[0] + '-summary.npz'
        print('read dark file from ' + dark_filename)
        if not os.path.isfile( dark_filename ):
            print('file ' + dark_filename + ' is not a file?!')
        else:
            # load the file
            dark_file = np.load(dark_filename)
            print('loaded dark file with median frame')
            print(str(dark_file['dark_frame_median']))
            self.set_dark_mean(dark_file['dark_frame_median'])
            if 'dark_frame_bad_pixel_map' in dark_file:
                print('loaded dark file with bad pixel map')
                print(str(dark_file['dark_frame_bad_pixel_map']))
                self.set_bad_pixel_map(dark_file['dark_frame_bad_pixel_map'])
    
    def select_asic(self, asic):
        """Select which asic to read data from."""
        self.print_debug('select asic ' + str(asic))
        self.selected_asic = asic

    def set_flip_frames(self,n_rotations):
        """Set number of pi/2 rotations of the frame."""
        self.flip_frame = n_rotations

    def select_analysis(self,a):
        """ Set analysis to be applied to frames."""
        self.print_debug('set frame analysis to ' + str(a.name) )
        self.frame_analysis = a
    

    def process(self,frame_id, data):
        """Process a frame."""

        drop_frame = False

        self.print_thread('process', False)

        self.emit(SIGNAL('busy'),True)

        t_process = FrameTimer('process')
        t_process.start()
        
        self.n_process += 1

        # build frame
        t1 = FrameTimer('epixFrameFill frame_id ' + str(frame_id))
        t1.start()
        self.frame.reset()
        self.frame.set_data_fast( data )
        self.frame_id = frame_id
        t1.stop()

        self.print_debug(t1.toString(), force=False)
                
        # add a dimension to fit the existing function
        if self.drop_bad_frames:
            t1=time.clock()
            tmp = np.empty([1,self.frame.super_rows.shape[0],self.frame.super_rows.shape[1]])
            tmp[0] = self.frame.super_rows
            tmp, dropped = dropbadframes(tmp)
            if tmp.size == 0:
                self.print_debug('WARNING dropped frame')
                self.n_drop += 1
                return
            else:
                self.print_debug('not a bad frame')

            self.print_debug('Drop time total is ' + str( time.clock() - t1) + ' s')

        if self.drop_bad_frames_2:
            s = np.sum(np.abs(np.diff(np.median(self.frame.super_rows, axis=0))))
            print('s = ' + str(s))
            if s > 10000:
                self.print_debug(' dropped frame s = ' + str(s))
                self.n_drop += 1
                return
        
        if self.do_dark_subtraction:

            t_dark = FrameTimer('dark subtraction')
            t_dark.start()
            if self.dark_frame_mean == None:
                self.print_debug('no dark frame is available!', True)
            else:
                self.frame.super_rows -= toint( self.dark_frame_mean )
            t_dark.stop()
            self.print_debug(t_dark.toString())

            # option to drop frames with too many pixels firing.
            if self.drop_max_pixels_count > 0:
                frame_tmp = (self.frame.super_rows > self.drop_max_pixels_threshold)
                tmpx, tmpy = np.nonzero( frame_tmp )
                # tmpx and tmpy is same length
                if len(tmpy) > self.drop_max_pixels_count:
                    self.print_debug('DROPPED MAX PIXELS frame (' + str(len(tmpy)) + '(count ' + str( self.drop_max_pixels_count) + ' thresh ' + str(self.drop_max_pixels_threshold) + '))', True)
                    self.n_drop += 1
                    return

        if self.do_bad_pixel_map_subtraction:

            t_bad_pixel_map = FrameTimer('bad_pixel_map')
            t_bad_pixel_map.start()
            if self.bad_pixel_map == None:
                self.print_debug('no bad pixel map is available!', True)
            else:
                sr = (self.bad_pixel_map < 1).astype(np.int16)
                #srs = self.frame.super_rows * sr                
                self.frame.super_rows *= sr
            t_bad_pixel_map.stop()
            self.print_debug(t_bad_pixel_map.toString())
            
        if self.flip_frame > 0:
            self.frame.super_rows = np.rot90(self.frame.super_rows, self.flip_frame)
            #print("shape " + str(np.shape(self.frame.super_rows)))
        
        # do analysis
        # this should ne pass by ref so even if no analysis is made should be fast?
        t_ana = FrameTimer('analysis')
        t_ana.start()
        self.frame.super_rows, self.frame.clusters = self.frame_analysis.process(self.frame.super_rows)
        t_ana.stop()
        self.__t0_ana_sum += t_ana.diff()
        self.__n_ana_sum += len(self.frame.clusters)

        self.print_debug(t_ana.toString(), force=False)

        if self.form_busy:
            self.print_debug('form is busy.',force=False)
            self.n_busy += 1
        else:
            self.print_debug('sending frame', force=False)
            self.emit_data()
            self.n_sent += 1
        


        # print timing if applicable
        if self.n_sent % 10 == 0 and self.n_sent > 0:
            tot, n = get_timer_data(self.process_timers)
            self.print_debug('n_process {0} n_sent {1} n_busy {2} i.e. {3}% at {4} sec/frame.  w/ ana={5}sec/frame ~{6}cl/frame ({7})'.format( self.n_process, self.n_sent, self.n_busy, float(self.n_busy)/float(self.n_sent+self.n_busy), float(tot)/n, float(self.__t0_ana_sum)/10.0, float(self.__n_ana_sum)/10.0, str(QThread.currentThread())), force=True)
            del self.process_timers[:]
            self.__t0_ana_sum = 0
            self.__n_ana_sum = 0
            self.n_busy = 0
            self.n_drop = 0
            self.n_sent = 0
    
        self.emit(SIGNAL('busy'),False)

        # stop timer
        t_process.stop()
        # add this timer to list
        self.process_timers.append(t_process)
        self.print_debug(t_process.toString())

        self.print_thread('process DONE',False)



    def emit_data(self):
        """ Emit data
        """

        self.print_debug (' on_draw ')


        t0 = FrameTimer('emit_data')
        t0.start()

        # check that there is a data to be drawn
        if self.frame != None:
            
            # send data 

            #QApplication.processEvents()

            #print (' get_data from frame')

            # make sure the corret asic is extracted
            sel_asic = self.selected_asic

            data = self.frame.get_data(sel_asic, self.flip_frame)

            self.emit(SIGNAL('new_data'), self.frame_id, data)

            self.emit(SIGNAL('new_clusters'), self.frame_id, self.frame.clusters)

            self.emit(SIGNAL('cluster_count'), self.frame_id, len(self.frame.clusters))

        t0.stop()

        self.print_debug(t0.toString(),force=False)





class FrameWorkerController(QObject):
    """Controller class that wraps the actual work into it's own thread."""
    def __init__(self, name, frame):
        super(FrameWorkerController, self).__init__()
        self.thread = MyQThread()
        self.thread.start()
        self.worker = self.init_frame_worker(name, frame)
        self.worker.moveToThread( self.thread )

    def init_frame_worker(self, name, frame):
        print('init frame_worker framecontroller')
        return FrameWorker(name, frame)



class CpixFrameWorker(FrameWorker):
    """Process Cpix frames."""
    
    def __init__(self,name, frame):
        FrameWorker.__init__(self,name, frame)
        
    def emit_data(self):
        """ Emit data
        """
        
        self.print_debug ('emit_data')

        t0 = FrameTimer('emit_data')
        t0.start()

        # check that there is a data to be drawn
        if self.frame != None:
            
            counter_type = self.frame.get_counter_type()
            data = self.frame.get_data(self.selected_asic)

            self.emit(SIGNAL('new_data'), self.frame_id, data)
            
            #print('[frame_worker]: counter_type ' + str(counter_type))

            if counter_type == 1:
                self.emit(SIGNAL('new_data_A'), self.frame_id, data)
            elif counter_type == 0:
                self.emit(SIGNAL('new_data_B'), self.frame_id, data)
            else:
                raise RuntimeError('this counter option ' + counter_type + ' is not valid')

            self.emit(SIGNAL('new_data_diff'), self.frame_id, counter_type, data)
            
            self.emit(SIGNAL('new_clusters'), self.frame_id, self.frame.clusters)

            self.emit(SIGNAL('cluster_count'), self.frame_id, len(self.frame.clusters))

        t0.stop()

        self.print_debug(t0.toString(),force=False)



class CpixFrameWorkerController(FrameWorkerController):
    """Cpix controller class."""
    def __init__(self, name, frame):
        FrameWorkerController.__init__(self, name, frame)
        print('init cpixframecontroller')
    
    def init_frame_worker(self, name, frame):
        print('init frame_worker cpixframecontroller')
        return CpixFrameWorker(name, frame)


