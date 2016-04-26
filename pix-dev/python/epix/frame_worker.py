#!/usr/bin/python

import sys
import os
import time
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pix_threading import MyQThread
from frame import EpixFrame
from pix_threading import MyQThread
from pix_utils import toint, dropbadframes, FrameAnalysisTypes, FrameTimer, get_timer_data

printThreadInfo = False



class FrameWorker(QObject):
    """Process frames."""

    debug = False

    def __init__(self,name):
        super(FrameWorker, self).__init__()
        self.name = name
        self.drop_bad_frames = False
        self.drop_bad_frames_2 = False
        self.do_dark_subtraction = True
        self.n_sent = 0
        self.n_busy = 0
        self.n_process = 0
        self.__t0_ana_sum = 0
        self.__n_ana_sum = 0
        self.frame = EpixFrame()
        self.dark_frame_mean = None
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

    def select_asic(self, asic):
        """Select which asic to read data from."""
        self.print_debug('select asic ' + str(asic))
        self.selected_asic = asic

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
        #self.frame.set_data( data, self.selected_asic )
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
                return
            else:
                self.print_debug('not a bad frame')

            self.print_debug('Drop time total is ' + str( time.clock() - t1) + ' s')

        if self.drop_bad_frames_2:
            s = np.sum(np.abs(np.diff(np.median(self.frame.super_rows, axis=0))))
            print('s = ' + str(s))
            if s > 10000:
                drop_frame = True

        if self.do_dark_subtraction:

            t_dark = FrameTimer('analysis')
            t_dark.start()
            #self.print_debug('subtract dark frame', True)
            if self.dark_frame_mean == None:
                self.print_debug('no dark frame is available!', True)
            else:
                # subtract pixel by pixel
                #np.savez('dark_worker_frame_' + str(frame_id) + '.npz',dmean=self.dark_frame_mean)
                #self.print_debug('dark ' + str(toint(self.dark_frame_mean)) , True)
                #self.print_debug('before ' + str(self.frame.super_rows) , True)
                #np.savez('loght_worker_frame_' + str(frame_id) + '.npz',frame=self.frame.super_rows)
                #print('dark:')
                #print(self.dark_frame_mean)
                self.frame.super_rows -= toint( self.dark_frame_mean )
                #self.print_debug('subtraction done', True)
                #self.print_debug('after ' + str(self.frame.super_rows) , True)
            t_dark.stop()
            self.print_debug(t_dark.toString())

        #self.frame.super_rows -= toint(self.dark_frame_mean)
        
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
        elif drop_frame:
            self.print_debug('dropped frame_2',force=True)
            self.n_busy += 1            
        else:
            self.print_debug('sending frame', force=False)
            #self.emit(SIGNAL("newDataFrame"),self.frame)
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

            data = self.frame.get_data(self.selected_asic)

            #print (' emit data frame id ' + str(self.frame_id))
            #print (np.shape(data))
            #print (data)
            #np.savez( 'frame_' + str(self.frame_id) + '.npz', frame = data )

            self.emit(SIGNAL('new_data'), self.frame_id, data)

            #print (' emit new_clusters')

            self.emit(SIGNAL('new_clusters'), self.frame_id, self.frame.clusters)

            #print (' emit cluster_count')

            self.emit(SIGNAL('cluster_count'), self.frame_id, len(self.frame.clusters))

            #print (' DONE emit')

        t0.stop()

        self.print_debug(t0.toString(),force=False)





class FrameWorkerController(QObject):
    def __init__(self, name):
        super(FrameWorkerController, self).__init__()
        self.thread = MyQThread()
        self.thread.start()
        self.worker = FrameWorker(name)
        self.worker.moveToThread( self.thread )

