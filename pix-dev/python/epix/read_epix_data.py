# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 11:02:07 2016

@author: blaj
@author: phansson
"""

import sys
import os.path
import numpy as np
from scipy.sparse import lil_matrix,csr_matrix
import time
#from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from epix import Dark, Binary, dropbadframes;
import pix_utils as utils
import argparse
import epix_style

def get_args():
    parser = argparse.ArgumentParser('ePix data reader.')
    parser.add_argument('--light','-l', required=True, help='Data file with exposure.')
    parser.add_argument('--dark','-d', required=True, help='Data file with no exposure (dark file).')
    parser.add_argument('--tag','-t', default='flat',)
    parser.add_argument('--maxframes','-m', type=int, default=-1)    
    args = parser.parse_args()
    print( args )
    return args


def get_flat_filename(name):
    return  os.path.join( os.path.split( name )[0],  os.path.splitext(  os.path.basename( name ) )[0] + '_' + args.tag +  os.path.splitext(  os.path.basename( name ) )[1] )

    

if __name__ == '__main__':
    print('Just Go')

    args = get_args()

    plt.ion()
    plt.ioff()

    fdark = args.dark
    fndark = get_flat_filename( fdark )
    fdata = args.light
    fndata = get_flat_filename( fdata )

    

    #MPI Initialization
    #from mpi4py import MPI
    #comm = MPI.COMM_WORLD
    #rank = comm.Get_rank()
    #size = comm.Get_size()
    comm=0
    rank=0
    size=1

    #execfile("viridis.py")  #just a fancier color map; style to be beautified



    #rank 0 is master, passes references, collects data, etc  

    #Get and broadcast dark
    if(rank==0):
        print( 'Opening file '+fdark+' ...')
        dark=Dark(fdark,fndark,100);
        for irank in range(1,size):
            comm.send(dark,dest=irank,tag=1);
    else:
        dark=comm.recv(source=0,tag=1);
        #print 'received dark, id: '+str(id(dark));

    #Get light file (if it doesn't exist, it will be created: multithreading not safe)
    if(rank==0):
        print ('Opening flat file ' + fndata + ' from ' + fdata)
        print ('Note, this is memory-hungry; maybe you want to slice frames')
        data=Binary(fdata,fndata);
        for irank in range(1,size):
            comm.send('go',dest=irank,tag=2);
    else:
        dark=comm.recv(source=0,tag=2);
        data=Binary(fndata);

    a = data.data;
    a, index = dropbadframes(a);
    a -= utils.toint(dark.dmean);
    print( 'done reading and dropping bad frames')
    nframes, my, mx = a.shape
    print( 'nframes ', nframes, ' my ', my , ' mx ', mx)

    #calculate cm
    t0=time.clock();
    nbanks=4;ncpb=92;
    cm=np.zeros((nframes,nbanks));
    for ibank in range(nbanks):
        i1=ibank*ncpb;i2=(ibank+1)*ncpb;
        cm[:,ibank]=utils.cmnoise(a[:,:,i1:i2]);
    if (rank==0):
        print( 'CM in '+str(time.clock()-t0)+' s')

    #find singles using all processes
    fnsingles=fndata+'-singles';
    if (not os.path.isfile(fnsingles+'.npz')):
        b=lil_matrix((nframes,my*mx),dtype=np.int16);
        t0=time.clock();
        for iframe in range(nframes):
            ncrit=4*dark.dstd;
            a0=a[iframe];
            b0=(a0>ncrit).astype(np.int16);
            for iy in range(1,my-3):
                for ix in range(1,mx-1):
                    if b0[iy,ix]:
                        if np.sum(b0[iy-1:iy+2,ix-1:ix+2])<=1:
                            b[iframe,iy*mx+ix]=a0[iy,ix];
            if (iframe%10==0):
                print( 'singles in frame '+str(iframe)+'/'+str(nframes)+' in '+str(1000*(time.clock()-t0)/(iframe+1))+' ms/frame')
        b=csr_matrix(b);
        np.savez(fnsingles,data=b.data,indices=b.indices,indptr=b.indptr);
    else:
        npzfile=np.load(fnsingles+'.npz');
        b=csr_matrix((npzfile['data'],npzfile['indices'],npzfile['indptr']),(nframes,my*mx));
    bind=np.nonzero(b);bind=bind[0].astype(np.int64)*mx*my+bind[1];
    c=np.ravel(a)[bind];
    #xx=np.arange(16384);
    #ssp=np.bincount(c,minlength=16384);
    #ymax=np.max(ssp[350:]);
    #plt.figure(1);plt.clf();plt.step(xx,ssp);plt.axis([0,5000,0,ymax]);
    #bn=np.asarray((b>1500).sum(0)).squeeze();
    #bs=np.asarray(b.astype(np.float).multiply(b>1500).sum(0)).squeeze();
    #bg=np.zeros_like(bs);
    #bg[bn>1]=bs[bn>1]/bn[bn>1];
    #bg=np.reshape(bg,(my,mx));
    #figure(1);clf();plt.imshow(np.reshape(bn,(my,mx)),vmin=0,vmax=2,interpolation='nearest');colorbar();

    plt.close("all");

    fnamepdf=os.path.join( os.path.split( fdata )[0],'report-'+os.path.basename( fdata )+'.pdf')
    #pp=PdfPages(fnamepdf);

    binsize=32;
    ssp=np.bincount(c//binsize);
    x=np.arange(ssp.shape[0])*binsize+binsize;
    #xx=np.arange(ssp.shape[0]*binsize);
    #yy=kde_sklearn(c.ravel(),xx,bandwidth=binsize)*np.size(c)*binsize;
    #x=x*17.4/300;
    #xx=xx*17.4/300;
    plt.figure(1,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    plt.step(x,ssp,where='mid');#plt.step(x,ssp,xx,yy,where='mid');
    plt.axis([0,8191,0,1.2*np.max(ssp[10:])]);
    plt.title('Spectrum of Single Pixel Events - '+os.path.basename( fdata ));
    plt.xlabel('Energy (ADU)');
    plt.ylabel('Spectrum (a.u.)');
    plt.legend(['Histogram (Bin Width '+str(binsize)+' ADUs)','Kernel Density Estimation']);

    #pp.savefig();

    #binsize=20;
    #ssp=np.bincount(c//binsize,minlength=16384//binsize);
    #xx=np.arange(16384//binsize)*binsize;
    #figure(2);clf();plt.step(xx,ssp,where='mid');
    #plt.axis([0,16384,0,8*binsize]);
    Ee=2808;
    b=np.maximum(0,((a+Ee//2)//Ee).astype(np.int8));
    bmax=np.max(b,axis=0);
    bmask=(bmax<4);
    i=np.sum(b*bmask,axis=(1,2),dtype=np.int32);

    #calculate normalized profile
    bprofile=np.zeros((my,mx));
    bprofilen=np.zeros((my,mx));
    for iframe in range(nframes):
        if (i[iframe]>0):
            bmaski=(b[iframe]<4);
            bprofile += bmaski*b[iframe]/i[iframe];
            bprofilen[bmaski]+=1;
    bprofile/=bprofilen;
    bprofile[bprofilen<1]=0;
    plt.figure(2,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    plt.imshow(bprofile,vmin=0,vmax=np.percentile(bprofile,98),interpolation='nearest');
    plt.colorbar();
    plt.title('Beam Profile - '+os.path.basename( fdata ));
    #pp.savefig();

    epix_style.setup_color_map(plt)


    plt.figure(3,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    px=np.sum(bprofile,axis=0);px=px*my/np.max(px);
    py=np.sum(np.flipud(bprofile),axis=1);py=py*mx/np.max(py);
    plt.plot(np.arange(mx)*0.05,px*0.05);
    plt.plot(py*0.05,np.arange(my)*0.05);
    plt.axis([0,mx*0.05,0,my*0.05]);
    plt.title('Beam Profile '+os.path.basename( fdata ));
    plt.xlabel('X Axis (mm)');
    plt.ylabel('Y Axis (mm)');
    plt.legend(['Projection on X','Projection on Y']);
    #pp.savefig();

    #intensity correction factor
    icf=np.sum(bprofile)/np.sum(bprofile*bmask);
    if np.isfinite(icf):
        inorm=np.rint(i*icf).astype(np.int32);
    else:
        inorm=i;

    #plt.plot(xx,kde_sklearn(c,xx,bandwidth=10));

    plt.figure(4,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    plt.plot(index,inorm,'.');plt.axis([0, nframes, 0, np.max(inorm)]);
    plt.title('Trace - '+os.path.basename( fdata ));
    plt.xlabel('Sample (at ~5 Hz)');
    plt.ylabel('Intensity (Electrons/Frame)');
    #pp.savefig();


    #i=np.sort(i,axis=0);
    #plt.figure(2);plt.clf();plt.plot(i,'.');
    binsize=16;
    di=np.bincount(i//binsize);
    x=np.arange(di.shape[0])*binsize+binsize;
    #xx=np.arange(di.shape[0]*binsize);
    #yy=kde_sklearn(i[i>0],xx,bandwidth=binsize)*np.size(i)*binsize;
    plt.figure(5,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    plt.step(x,di,where='mid');#plt.step(x,di,xx,yy,where='mid');
    plt.axis([0,np.max(x),0,np.max(di)]);
    plt.title('Beam Intensity Distribution');
    plt.xlabel('Beam Intensity (Electrons/Frame)');
    plt.ylabel('Histogram');
    plt.legend(['Histogram (Bin Width '+str(binsize)+' Electrons)','Kernel Density Estimation']);
    #pp.savefig();

    xmax=512;
    di=np.bincount(i);
    x=np.arange(di.shape[0]);
    #xx=np.arange(0,di.shape[0],0.1);
    #yy=kde_sklearn(i[i>0],xx,bandwidth=2)*np.size(i);
    plt.figure(6,facecolor='white',figsize=(11,8.5),dpi=150);plt.clf();
    plt.step(x*icf,di,where='mid');#plt.step(x*icf,di,xx*icf,yy,where='mid');
    plt.axis([0,xmax,0,np.max(di)]);
    plt.title('Beam Intensity Distribution, 0 to '+str(xmax));
    plt.xlabel('Beam Intensity (Electrons/Frame)');
    plt.ylabel('Histogram');
    plt.legend(['Histogram (Electrons)','Kernel Density Estimation']);
    #pp.savefig();

    #pp.close();


    #Fast animation
    #plt.close("all");
    #aroi=np.array([354,0,384,0]);
    #nroi=(aroi[1]-aroi[0])*(aroi[3]-aroi[2]);

    fig1=plt.figure(7,facecolor='white');plt.clf();
    ax1=fig1.add_subplot(111);
    #ax1=fig1.add_subplot(1,2,1);
    obj1=ax1.imshow(a[0],vmin=0,vmax=2,interpolation='nearest',cmap='viridis');
    fig1.colorbar(obj1);
    

    #ax2=fig1.add_subplot(1,2,2);
    #line1,=ax2.step(np.arange(5),np.zeros(5),where='mid');
    #line2,=ax2.step(np.arange(9),np.zeros(9),where='mid');
    #ax2.axis([0,8,0,nroi/3]);

    #list,=np.where(i==0);
    #for iframe in list:
    for iframe in range(nframes):

        #a0=(a[iframe]+Ee//2)//Ee;
        #a0=np.reshape(b[iframe].todense(),(my,mx));
        #frame=a[iframe];

        frame=utils.cheapphotons(a[iframe], 2808, my, mx);

        obj1.set_data(a[iframe]);
        #obj1.set_data(frame);
        #obj1.set_data(a[iframe]);
        ax1.set_title(os.path.basename( fdata)+' '+str(iframe));
        

        #hist1=np.bincount(np.minimum(frame,4).ravel(),minlength=5);
        #hist2=np.bincount(frame.ravel(),minlength=9);
        #line1.set_ydata(hist1[:5]);
        #line2.set_ydata(hist2[:9]);

        #plt.draw()
        fig1.canvas.draw()
        #plt.show()

        #time.sleep(1);
        time.sleep(0.01);

    print( 'RANK '+str(rank)+' DONE!')


