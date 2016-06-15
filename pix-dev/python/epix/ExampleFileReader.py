import sys
import numpy as np
from PixDataFileReader import FileReader as reader
import frame as camera_frame
import matplotlib.pyplot as plt


nx = 768
ny = 708


if __name__ == '__main__':

    print('Read frames from file \"' + sys.argv[1] + '\"')

    reader = reader(sys.argv[1], camera_frame.EpixFrame())

    reader.open()

    n = 0
    n_max = 10

    data_frames = None

    while n < n_max:

        print('read frame ' + str(n))

        # read next frame
        reader.read_next()

        # get a reference to the data frame object
        frame = reader.frame

        if frame == None:
            print('frame ' + str(n) + ' is corrupted? Skip')
            continue        

        # get a refence to the actual pixel matrix
        data  = frame.super_rows
        
        print(data)

        # first frame
        if n == 0:
            data_frames = np.zeros( (n_max, np.shape(data)[0], np.shape(data)[1]) )

        data_frames[n] = data

        n += 1

    print('Read ' + str(n) + ' frames')

    reader.close()

    data_sum = np.rint(np.sum(data_frames, axis=0)).astype(np.float64)

    fig1 = plt.figure(1)
    ax221 = fig1.add_subplot(2,3,1)
    img221 = ax221.imshow(data_sum[ny/2: , nx/2:], vmin=0,vmax=16000) #, interpolation='nearest') #, cmap='viridis')
    #fig1.colorbar( img1 )
    ax221.set_title('sum')

    ax222 = fig1.add_subplot(2,3,2)
    img222 = ax222.imshow(np.mean(data_frames, axis=0)[ny/2: , nx/2:], vmin=0,vmax=16000) #, interpolation='nearest') #, cmap='viridis')
    #fig1.colorbar( img1 )
    ax222.set_title('average')
    fig1.show()

    ax223 = fig1.add_subplot(2,3,3)
    img223 = ax223.imshow(np.median(data_frames, axis=0)[ny/2: , nx/2:], vmin=0,vmax=16000) #, interpolation='nearest') #, cmap='viridis')
    #fig1.colorbar( img1 )
    ax223.set_title('median')
    fig1.show()

    ax224 = fig1.add_subplot(2,3,4)
    img224 = ax224.imshow((data_sum - np.median(data_frames, axis=0)*n)[ny/2: , nx/2:], vmin=-10,vmax=10) #, interpolation='nearest') #, cmap='viridis')
    fig1.colorbar( img224 )
    ax224.set_title('median sub sum')
    fig1.show()






    fig2 = plt.figure(2)
    ax2 = fig2.add_subplot(2,2,1)
    img2 = ax2.imshow(np.std(data_frames, axis=0)[ny/2: , nx/2:], vmin=0,vmax=500,cmap='Reds') #, interpolation='nearest') #, cmap='viridis')
    fig2.colorbar( img2 )
    ax2.set_title('std dev')


    std_dev = np.std(data_frames , axis=0)
    mean_std_dev = np.mean(std_dev)
    ax22 = fig2.add_subplot(2,2,2)
    ne, bins, patches = plt.hist(np.ravel(std_dev[ny/2: , nx/2:]), bins=100, range=(0,500))
    plt.title('std dev hist')
    #plt.axis([0,500,1,np.max(std_dev[ny/2: , nx/2:])*10])
    #ax22.set_yscale('log')
    ax22.text(0.35,0.8,'mean {0:.1f}'.format(mean_std_dev),transform=ax22.transAxes)

    thresh = 10.*mean_std_dev
    ax22.text(0.35,0.7,'std dev thresh = {0:.1f}'.format(thresh),transform=ax22.transAxes)
    
    bad_pixels = (std_dev > thresh).astype(np.int16)
    xi,yi = np.nonzero(bad_pixels)
    ax22.text(0.35,0.6,'{0:d} pixels ({1:.2f}%)'.format(len(xi),len(xi)/float(nx/2*ny/2)*100),transform=ax22.transAxes)


    ax23 = fig2.add_subplot(2,2,3)
    img23= ax23.imshow(bad_pixels[ny/2: , nx/2:], vmin=0,vmax=1, cmap='Greys')
    plt.colorbar( img23 )
    plt.title('bad pixels')


    d_bad = bad_pixels*std_dev

    ax24 = fig2.add_subplot(2,2,4)
    img24= ax24.imshow(d_bad[ny/2: , nx/2:], vmin=0,vmax=500, cmap='Reds')
    plt.colorbar( img24 )
    plt.title('bad pixels std dev')

    fig2.show()


    plt.figure(fig1.number)


    #ans = raw_input('pause')
    dark_good = (bad_pixels < 1).astype(np.int16)
    db = data_sum - np.median(data_frames, axis=0)*n
    dark_sub_bad_sub = db * dark_good


    ax225 = fig1.add_subplot(2,3,5)
    img225 = ax225.imshow(dark_sub_bad_sub[ny/2: , nx/2:], vmin=-10,vmax=10) #, interpolation='nearest') #, cmap='viridis')
    fig1.colorbar( img225 )
    ax225.set_title('dark & bad subtracted')
    fig1.show()

    std_dev_dark = np.std(dark_sub_bad_sub , axis=0)
    #mean_std_dev = np.mean(std_dev)
    ax226 = fig1.add_subplot(2,3,6)
    nee, bins2, patches2 = plt.hist(np.ravel(dark_sub_bad_sub[ny/2: , nx/2:]), bins=100, range=(0,500))
    plt.title('std dev dark hist')
    #plt.axis([0,500,1,np.max(dark_sub_bad_sub[ny/2: , nx/2:])*10])
    #ax226.set_yscale('log')

    fig1.show()




    ans = raw_input('pause')

