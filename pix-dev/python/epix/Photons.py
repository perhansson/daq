#!/bin/python
import numpy as np
from scipy.sparse import csr_matrix
import matplotlib.pyplot as plt

class Photons(object):
    def __init__(self,nmax,data):
        mats=[(0,0)];
        my=data.ny; mx=data.nx;
        print 'Generating/reading matrices...'
        for D in range(1,nmax+1):
            fname=fpath+'blob-map-'+str(my)+'-'+str(mx)+'-size-'+str(D);
            if (os.path.isfile(fname+'.npz')):
                npzfile=np.load(fname+'.npz');
                d0=csr_matrix((npzfile['d0data'],npzfile['d0indices'],npzfile['d0indptr']),shape=(my*mx,my*mx));
                d1=csr_matrix((npzfile['d1data'],npzfile['d1indices'],npzfile['d1indptr']),shape=(my*mx,my*mx));
            else:            
                print '\tSize '+str(D);
                n=D+2;
                c=n//2;
                p0=np.zeros((n,n),dtype=np.int8);
                p0[1:-1,1:-1]=1;
                i0,j0,v0=find(1-p0); idx0=i0*mx+j0;
                i1,j1,v1=find(p0);   idx1=i1*mx+j1;
                
                d0=lil_matrix((my*mx,my*mx),dtype=np.int8);
                d1=lil_matrix((my*mx,my*mx),dtype=np.int8);
                for iy in range(my-n):
                    for ix in range(mx-n):
                        ipix1=iy*mx+ix;
                        ipix2=(iy+c)*mx+(ix+c);
                        d0[ipix2,ipix1+idx0]=1;
                        d1[ipix2,ipix1+idx1]=1;
                d0=d0.tocsr();
                d1=d1.tocsr();
                np.savez_compressed(fname,d0data=d0.data,d0indices=d0.indices,d0indptr=d0.indptr,d1data=d1.data,d1indices=d1.indices,d1indptr=d1.indptr);
            mats.append((d0,d1));
        self.nmax=nmax;
        self.mats=mats;
    def blobs(self,frame):
        #ncrit0=12;
        #ncrit1=50;
        ncrit0=400;
        ncrit1=1000;
        display=0;
        
        if (display>0):
            fig1=plt.figure(7,facecolor='white');plt.clf();
            ax1=fig1.add_subplot(1,2,1);
            obj1=ax1.imshow(frame,vmin=-10,vmax=200,interpolation='nearest',cmap='viridis');
            fig1.colorbar(obj1);

        ny,nx=frame.shape;
        frame1=np.copy(frame.ravel());
        blobs=lil_matrix((ny*nx,4),dtype=np.int16);
        nblobs=0;
        for isize in range(1,self.nmax+1):
            print '\tSize '+str(isize)
            d0,d1=self.mats[isize];
            framecrit0=frame1>ncrit0;
            framecrit1=frame1>ncrit1;
            maskD=(framecrit1*d1>0)*(framecrit0*d0==0);
            idx,=np.nonzero(maskD);            
            E=frame1*d1;
            #eventually sort descending
            for ipart in idx:
                iy=ipart//nx; ix=ipart%nx; #eventually go to subpixel
                #i,j,v=find(d1[ipart]==1);
                #frame1[j]=0;
                blobs[nblobs,:]=toint(np.array([isize,iy,ix,E[ipart]]));
                nblobs+=1;
            #obj1.set_data(np.reshape(frame1,(ny,nx)));
            #ax1.set_title('Size '+str(isize));
            #plt.draw();
            #time.sleep(1);
        blobs=blobs[:nblobs,:].toarray();
        
        if (display>0):        
            framephotons=csr_matrix((blobs[:,3],(blobs[:,1],blobs[:,2])),shape=(ny,nx)).toarray();
            ax2=fig1.add_subplot(1,2,2);
            obj2=ax2.imshow(framephotons,vmin=-10,vmax=200,interpolation='nearest',cmap='viridis');
            fig1.colorbar(obj2);        
            time.sleep(1);
        return blobs;      
        
    def singles(self,frame):
        ncrit0=12;
        ncrit1=50;
        ny,nx=frame.shape;
        frame1=frame.ravel();
        d0,d1=self.mats[1];
        framecrit0=frame1>ncrit0;
        framecrit1=frame1>ncrit1;
        maskD=(framecrit1*d1>0)*(framecrit0*d0==0);
        idx,=np.nonzero(maskD);            
        #E=np.reshape(frame1*d1,(ny,nx));
        #return E.ravel()[idx],E;
        return idx,frame1[idx];
