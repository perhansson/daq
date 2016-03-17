# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 08:43:35 2016

@author: blaj
"""
#This should be cleaned up, formatting consolidated etc.

import numpy as np;
import os.path;
import time;
    
def dmap(fmt):
    nb=16;nbs=96;
    idx=np.zeros((354,nb*nbs));
    bo=np.arange(16).astype(np.uint32);
    for ir in range(354):
        for ib in range(nb):
            ib0=nbs*ib;ib1=ib0+nbs;
            idx[ir,ib0:ib1]=bo[ib]*nbs+np.arange(nbs)+ir*nb*nbs;
    idxtop=np.flipud(idx[:,768:1536]);
    idxbot=idx[:,0:768];
    idx=np.concatenate((idxtop,idxbot),axis=0);
    idx=idx.astype(np.uint32);
    return idx;
    
def roi(fmap):
    return fmap[354:768,384:768];
    #return fmap;

def fmap(data,iframes):
    nframes=np.size(iframes);
    if (nframes>1):
        idx=np.zeros((nframes,data.my,data.mx)).astype(np.uint64);
        for iframe in range(nframes):
            idx[iframe,:,:]=data.f1map+data.index[iframes[iframe]];
    else:
        idx=data.f1map+data.index[iframes];
    return idx;

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
    print ('Dropped '+str(ndropped)+' bad frames in '+str(time.clock()-t0)+' s')
    return a,idx;
    
class Epix100a(object):
    def __init__(self,fname):
        self.fname=fname;

        #define format - ugly mess, clean up properly
        self.nblocksize=120;
        self.ny=708; self.nx=768;
        self.nhead=8; self.nfoot=771;
        self.nblocks=16;
        self.nbcols=92;
        self.npix=self.nx*self.ny;
        self.framesize=(self.nhead+self.nfoot+self.npix//2);
        
        fmt=np.zeros((8,2));
        fmt[0,0]=0;
        fmt[0,1]=self.framesize;
        fmt[1,0]=self.nhead;
        fmt[1,1]=self.nfoot;
        fmt[2,0]=self.ny;
        fmt[2,1]=self.nx;
        fmt[3,0]=self.nblocks;
        fmt[3,1]=self.nbcols;
        fmt=fmt.astype(np.uint32);
        self.fmt=fmt;
        
        #create LUT
        self.f1map=roi(dmap(self.fmt));
        self.my=self.f1map.shape[0]; self.mx=self.f1map.shape[1];

        # throw the error after initializing (yeah, not great...)
        if (not os.path.isfile(fname)):
            raise ValueError('File not found: '+fname);
        
        #read index
        index=np.zeros((65536)).astype(np.uint64);
        nframes=0;
        nerrors=0;
        idx=0;
        fin=open(fname,'rb');
        try:
            while True:
                fs=np.fromfile(fin,dtype=np.uint32,count=1)[0];
                if (fs==self.framesize):
                    index[nframes]=idx+2*self.nhead+2;
                    nframes=nframes+1;
                    #print nframes;
                else:
                    nerrors=nerrors+1;
                    print (nframes,nerrors,fs)
                fin.seek(4*fs,1);
                idx=idx+2*fs+2;
        except IndexError:
            print (' - indexing found '+str(nframes)+' frames.')
            #print 'index= '+str(idx);
        finally:
            fin.close();
        index=index[0:nframes];
        self.index=index;
        self.nframes=nframes;
        self.fmt[0,0]=nframes;
        
        #memmap file
        self.fin=np.memmap(self.fname,dtype=np.int16,mode='r');
        
    def frame(self, iframe):
        print('get frame ' + str(iframe) + ' out of nframes ' + str(self.nframes))
        #iframes=np.asarray(iframe);
        #iframes=iframes[iframes<self.nframes];
        return self.fin[fmap(self,iframe)];

    def close(self):
        del self.fin;
        
class Binary(object):
    def __init__(self,fdata,fndata):
        #dump to binary
        print('Initialize binary from ' + fdata)

        if (not os.path.isfile(fndata)):

            print('create Epix100a flat file ' + fndata + ' from ' + fdata)
            
            datain=Epix100a(fdata);

            #write header
            binheader=np.zeros(16).astype(np.uint32);
            binheader[0:6]=[datain.nframes, datain.my*datain.mx, datain.my, datain.mx, datain.nblocks, datain.nbcols];
            binheader.tofile(fndata);    

            #write data
            dataout=np.memmap(fndata,dtype=np.int16,mode='r+', shape=(datain.nframes,datain.my,datain.mx),offset=64);
            t0=time.clock();
            for iframe in range(datain.nframes):
                dataout[iframe]=datain.frame(iframe);
                if (iframe%100==0):
                    #progress(iframe,nframes,iframe);
                    print (str(iframe)+' - '+str(1000*(time.clock()-t0)/(iframe+1))+' ms. average frame: '+str(np.mean(datain.frame(iframe))))
            dataout.flush();
            
            del dataout;
            del datain;
        
        #get nr of frames
        else:
            print(fndata + ' file already exists.')
        data=np.memmap(fndata,dtype=np.uint32,mode='r',shape=((64)),offset=0); 
        self.nframes=data[0]; self.nframesize=data[1]; self.my=data[2]; self.mx=data[3]; self.nblocks=data[4]; self.nbcols=data[5];
        self.data=np.memmap(fndata,dtype=np.int16,mode='c',shape=(self.nframes,self.my,self.mx),offset=64);
        
class Dark(object):
    def __init__(self, fdark, fndark, nblocksize):
        if (os.path.isfile(fndark+'-dark.npz')):
            npzfile=np.load(fndark+'-dark.npz');
            self.dmean=npzfile['dmean'];
            self.dstd=npzfile['dstd'];
            self.dbpm=npzfile['dbpm'];
        else:
            print('Creating Binary from ' + fdark)
            dark=Binary(fdark,fndark);
            nframes=dark.nframes; my=dark.my; mx=dark.mx;
            nblocks=nframes//nblocksize;
            
            bmed=np.zeros((nblocks,my,mx));
            bstd=np.zeros((nblocks,my,mx));
            for iblock in range(nblocks):
                t0=time.clock();
                a=dark.data[iblock*nblocksize:(iblock+1)*nblocksize];
                a,idx=dropbadframes(a);
                print ('- read block, dropped bad, subtracted dark in '+str(time.clock()-t0)+'s')
                nfb=a.shape[0];                
                bmed[iblock,:,:]=np.median(a,axis=0);
                bstd[iblock,:,:]=np.std(a,axis=0);
            self.dmean=np.mean(bmed,axis=0);
            self.dstd=np.sqrt(np.sum((bstd)**2,axis=0));
            self.dbpm=self.dstd<(np.median(self.dstd)+5*np.std(self.dstd));
            self.dbpm=self.dstd<(np.median(self.dstd*self.dbpm)+5*np.std(self.dstd*self.dbpm));
            
            np.savez(fndark+'-dark',dmean=self.dmean,dstd=self.dstd,dbpm=self.dbpm);
            del dark;

