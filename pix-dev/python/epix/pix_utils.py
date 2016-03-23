# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 08:43:35 2016

@author: blaj
@author: phansson
"""

import numpy as np
import os.path
import time



class FrameAnalysis(object):
    """Analysis to run on a frame."""
    def __init__(self, name=''):
        self.name = name
    def process(self, frame):
        """Subclasses should override this method.
        
        Should return a tuple with the new frame and number of clusters/photons fiund. 
        This implementation simply passes the frame through.
        """
        return frame, -1



class CheapPhotonAnalysis(FrameAnalysis):
    """Cheap photon analysis."""
    def __init__(self):
        FrameAnalysis.__init__(self, 'cheap_photons')
    
    def process(self,frame):
        """ Do the actual analysis on the frame."""
        raise NotImplementedError



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
    
    @staticmethod
    def find_seed_clusters(a0, noise_level, n_sigma, seed_size, n_pixels, max_signal=9999999):
        t0 = time.clock()
        sf = np.zeros(a0.shape)

        # select seeds based on this threshold
        ncrit = n_sigma*noise_level

        # select the seeds
        sf_seeds = (a0 > ncrit).astype(np.int16)

        print(sf_seeds)

        # number of pixels
        mx = a0.shape[1]
        my = a0.shape[0]

        # loop across the whole frame and find the seeds
        n_clusters = 0
        iy = 1
        for iy in range(1,354):
            for ix in range(384,mx):
                #print('test pixel at [', iy, ',', ix, '] with ', a0[iy,ix], ' signal')
                if sf_seeds[iy,ix]:
                    #print('found seed at [', iy, ',', ix, '] with ', a0[iy,ix], ' signal')
                    if a0[iy,ix] < max_signal:
                        # this is a seed,
                        # calculate how many adjacent pixels in a 3x3 window that are above the seed threshold
                        n = np.sum(sf_seeds[iy-1:iy+1,ix-1:ix+1])
                        if n > (n_pixels-1):
                            #print(' seed accepted')
                            cluster_signal = np.sum(a0[iy-1:iy+1,ix-1:ix+1])
                            if cluster_signal < max_signal:
                                print('accepted seed cluster at [', ix, ',', iy, '] with ', a0[iy,ix], ' signal, cluster_count ', n, ' cluster_signal ', cluster_signal)
                                sf[iy,ix] = a0[iy,ix]
                                n_clusters += 1
                                # no overlaps, this is getting ugly
                                #ix += seed_size
                                #iy += seed_size
                                #continue
        print( 'Found ', n_clusters, ' seed clusters in '+str(time.clock()-t0)+' s')
        return sf, n_clusters

    def process(self,frame):
        """ Do the actual analysis on the frame."""
        return SimpleSeedAnalysis.find_seed_clusters(frame,  self.noise_level, self.seed_size, self.n_sigma, self.n_pixels)




class FrameAnalysisTypes(object):
    """Frame analyses"""
    types = [ FrameAnalysis('none'), \
              SimpleSeedAnalysis() , \
              CheapPhotonAnalysis()]
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

