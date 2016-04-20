# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 08:43:35 2016

@author: blaj
@author: phansson
"""

import numpy as np
import os.path
import time
from Photons import Photons
from clustering import find_seed_clusters, SimpleCluster, find_fixedwindow_clusters, find_meanshift_clusters, find_pixels_above_threshold


class FrameTimer(object):
    def __init__(self, name):
        self.name = name
        self.t0 = 0
        self.t1 = 0
    def start(self):
        self.t0 = time.clock()
    def stop(self):
        self.t1 = time.clock()
    def diff(self):
        return self.t1 - self.t0
    def toString(self):
        return '[Timer]: \"{0}\" {1} sec'.format(self.name, self.diff())


def get_timer_data(timers):
    """Return the sum of time in the timers and the number of them."""
    tot = 0
    for t in timers:
        tot += t.diff()
    return tot, len(timers)

class FrameAnalysis(object):
    """Analysis to run on a frame."""
    def __init__(self, name=''):
        self.name = name
    def process(self, frame):
        """Subclasses should override this method.
        
        Should return a tuple with the new frame and a list of cluster objects.
        This implementation simply passes the frame through.
        """
        return frame, []



class CheapPhotonAnalysis(FrameAnalysis):
    """Cheap photon analysis."""
    def __init__(self):
        FrameAnalysis.__init__(self, 'cheap_photons')
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        photon=Photons(1,frame);
        electronlist=photon.blobs(frame);
        #and it will return a photon list in a numpy array, with one row for each "electron" (as defined above) and 4 columns: [isize,iy,ix,E[ipart]]. isize means it fits in an isize*isize box, not that it's s
        #You can use any number over 1 to define the maximum cluster size you care about. Probably a 4 (as in 4x4) is sufficient for electrons.
        #data is a 2D numpy array containing one frame. It's there only to provide the right number of rows and columns.
        print('got ' + str(np.shape(electronlist)) + ' Photons')
        cluster_frame = np.zeros_like(frame,dtype=int16)
        clusters = []
        for i in range(np.shape(electronlist)[0]):
            iy = electronlist[i][1]
            ix = electronlist[i][2]
            cluster_frame[iy,ix] = electronlist[i][3]
            clusters.append( SimpleCluster(ix,iy,electronlist[i][3],electronlist[i][0]) )
        print('got ' + str(np.shape(electronlist)) + ' clusters')
        return cluster_frame, clusters

class SimpleSeedAnalysis(FrameAnalysis):
    """Find pixels with large signals, really stupidly complicated."""
    def __init__(self):
        FrameAnalysis.__init__(self, 'simple_seed')
        # noise level in ADC counts
        self.noise_level = 20
        # seed size in nr of  pixels (not really used at the moment...)
        self.seed_size = 3
        # required threshold in number of noise levels units
        self.n_sigma = 1
        # how many pixels that need to be above the threshold
        self.n_pixels = 1
    
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        return find_seed_clusters(frame,  self.noise_level, self.seed_size, self.n_sigma, self.n_pixels)



class SimpleFixedWindowClusterAnalysis(FrameAnalysis):
    """
    Fixed window cluster search.

    Pixels have a single configurable threshold.
    Window size is configurable.    
    """

    def __init__(self, name = 'fixed_window', noise_level=100, n_sigma=3, window_size=3):
        FrameAnalysis.__init__(self, name)
        # noise level in ADC counts
        self.noise_level = noise_level
        # windows size
        self.window_size = window_size
        # required threshold in number of noise levels units or "sigmas"
        self.n_sigma = n_sigma
    
    
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        return find_fixedwindow_clusters(frame,  self.noise_level, self.n_sigma, self.window_size)




class MeanShiftClusterAnalysis(FrameAnalysis):
    """
    Mean shift cluster search.

    """

    def __init__(self, name = 'mean_shift'):
        FrameAnalysis.__init__(self, name)
    
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        return find_meanshift_clusters(frame)


class PixelThresholdAnalysis(FrameAnalysis):
    """
    Apply a simple threshold to pixels.
    """

    def __init__(self, name = 'pixel_thresh', threshold=1000):
        FrameAnalysis.__init__(self, name)
        self.threshold = threshold
    
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        return find_pixels_above_threshold( frame, self.threshold )




class FrameAnalysisTypes(object):
    """Hold all frame analysis to allow easy listing in GUIs."""
    types = [ FrameAnalysis('none'), \
              PixelThresholdAnalysis(), \
              SimpleSeedAnalysis() , \
              CheapPhotonAnalysis(), \
              MeanShiftClusterAnalysis(), \
              SimpleFixedWindowClusterAnalysis()]
    @staticmethod
    def get(s):
        for t in FrameAnalysisTypes.types:
            if t.name == s:
                return t
        raise NotImplementedError





def get_flat_filename(name,tag):
    return  os.path.join( os.path.split( name )[0],  os.path.splitext(  os.path.basename( name ) )[0] + '_' + tag +  os.path.splitext(  os.path.basename( name ) )[1] )


def toint(a):
    return np.rint(a).astype(np.int16);


def dropbadframes(a):
    maxdif=5;
    t0=time.clock();
    nframes,my,mx=a.shape;
    idx=np.arange(nframes);
    bm=np.median(a,axis=0);
    btrace=np.zeros(nframes);
    ndropped=0;
    idrop=np.zeros(nframes)
    for iframe in range(nframes):
        btrace[iframe]=np.median(np.maximum(maxdif,np.abs(bm-a[iframe])));
        if (btrace[iframe]>2*maxdif):
            idrop[ndropped]=iframe;
            ndropped+=1;
    if ndropped>0:
        a=np.delete(a,idrop[0:ndropped],0);
        idx=np.delete(idx,idrop[0:ndropped]);
    #print ('Dropped '+str(ndropped)+' bad frames in '+str(time.clock()-t0)+' s')
    return a,idx;




def cmnoise(a):
    noise=12; #12 ADUs
    nframes=a.shape[0];
    cm=np.zeros(nframes);
    for iframe in range(nframes):
        b=a[iframe,:,:];
        b=b[abs(b)<noise];
        cm[iframe]=np.median(b);
    return cm;

#def kde_sklearn(x, x_grid, bandwidth, **kwargs):
#    """Kernel Density Estimation with Scikit-learn"""
#    kde_skl = KernelDensity(bandwidth=bandwidth, **kwargs)
#    kde_skl.fit(x[:, np.newaxis])
#    # score_samples() returns the log-likelihood of the samples
#    log_pdf = kde_skl.score_samples(x_grid[:, np.newaxis]);
#    return np.exp(log_pdf);

def generalfit(x,a1,a2,a3,a4,a5):
    return (a1*x+a2*x**2)/(a3+a4*x+a5*x**2);

def Iextrap(I,n):
    I1=generalfit(I,88.624,-20.604,95.091,-27.3789,1.047487);
    I2=np.random.poisson(I1);
    return I2

def cheapphotons(a0, E, my, mx):
    Estart=E/4;
    Enoise=E/4;
    r=1;
    pm0=np.maximum(0,a0//E);
    a1=a0-pm0*E;
    a1r=a1.ravel();
    idx,=np.where(a1r>Estart);
    idx2=np.flipud(np.argsort(a1r[idx]));
    pm1=np.zeros_like(pm0);
    for i in idx[idx2]:
        ix=i%mx; iy=i//mx;
        ix1=np.maximum(0,ix-r); ix2=np.minimum(mx,ix+r+1);
        iy1=np.maximum(0,iy-r); iy2=np.minimum(my,iy+r+1);
        tl=np.sum(a1[iy1:iy,ix1:ix]);
        tr=np.sum(a1[iy1:iy,ix:ix2]);
        bl=np.sum(a1[iy:iy2,ix1:ix]);
        br=np.sum(a1[iy:iy2,ix:ix2]);
        idx3=np.argsort(np.abs(a1[iy,ix]-np.asarray([tl,tr,bl,br])));
        pm1[iy,ix]+=1;
        if(idx3[0]==0):
            a1[iy1:iy,ix1:ix]=0;
        elif(idx3[0]==1):
            a1[iy1:iy,ix:ix2]=0;
        elif(idx3[0]==2):
            a1[iy:iy2,ix1:ix]=0;
        else:
            a1[iy:iy2,ix:ix2]=0;
    pm=pm0+pm1;
    idx2,=np.where(pm.ravel()>=4);    
    pm1=np.zeros_like(pm0);
    for i in idx2:
        r=3;
        ix=i%mx; iy=i//mx;
        ix1=np.maximum(0,ix-r); ix2=np.minimum(mx,ix+r+1);
        iy1=np.maximum(0,iy-r); iy2=np.minimum(my,iy+r+1);
        bmean=np.mean(pm[iy1:iy2,ix1:ix2]);
        pm1[iy,ix]=Iextrap(bmean,5);
        print( i, bmean,pm[iy,ix],pm1[iy,ix])
    pm+=pm1;
    return pm;

