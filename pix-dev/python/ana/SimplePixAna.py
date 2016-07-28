import sys
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
sys.path.append('../epix')
import PixelAna as utils


nx = 768
ny = 708

def get_args():
    parser = argparse.ArgumentParser('Simple analysis.')
    parser.add_argument('-f', help='File name.')
    parser.add_argument('--save', action='store_true', help='File name.')
    parser.add_argument('-n', default=10, type=int, help='Number of frames.')
    parser.add_argument('-p', type=str, help='List of pixels  x and y in quotes.')
    args = parser.parse_args()
    print( args )
    return args


if __name__ == '__main__':


    args = get_args()

    print('Read ' + str(args.n) + ' frames from file \"' + sys.argv[1] + '\"')


    data_frames = utils.get_data_frames(args.f, args.n)

    
    data_sum = np.rint(np.sum(data_frames, axis=0)).astype(np.float64)[ny/2: , nx/2:]

    data_mean = np.mean(data_frames, axis=0)[ny/2: , nx/2:]

    data_rms = np.std(data_frames, axis=0)[ny/2: , nx/2:]

    
    

    fig1 = plt.figure(1)
    ax221 = fig1.add_subplot(2,2,1)
    img221 = ax221.imshow(data_sum, vmin=0,vmax=16000) #, interpolation='nearest') #, cmap='viridis')
    #fig1.colorbar( img1 )
    ax221.set_title('sum')

    ax222 = fig1.add_subplot(2,2,2)
    img222 = ax222.imshow(data_mean, vmin=4000,vmax=6000) #, interpolation='nearest') #, cmap='viridis')
    fig1.colorbar( img222 )
    ax222.set_title('average')

    ax223 = fig1.add_subplot(2,2,3)
    img223 = ax223.imshow(data_rms, vmin=0,vmax=100) #, interpolation='nearest') #, cmap='viridis')
    fig1.colorbar( img223 )
    ax223.set_title('std dev')

    fig1.show()


    pixel_data = []

    if args.p != None:
        print 'look at pixels ' + str(args.p.split())
        for p in args.p.split():
            c = p.split(',')
            print 'data for ' + str(c)
            d = data_frames[:,c[0],c[1]]            
            print d
            pixel_data.append(utils.PixelData(int(c[0]),int(c[1]),d))

    print('got ' + str(len(pixel_data)) + ' pixels')

    fig2 = plt.figure(2)
    ax2_221 = fig2.add_subplot(2,1,1)
    plt.ylabel('Number of frames')
    plt.xlabel('ADC Value')
    ax2_221.text(0.7,0.9,'{0:d} pixels'.format(len(pixel_data)),transform=ax2_221.transAxes)
    i = 1
    for p in pixel_data:
        ne, bins, patches = plt.hist(np.ravel(p.data), bins=100, range=(4500,5500))
        ax2_221.text(0.7,0.9-0.1*i,'({0:d},{0:d})'.format(p.x,p.y),transform=ax2_221.transAxes)
        i += 1

    ax2_222 = fig2.add_subplot(2,1,2)
    ax2_222.grid(True)
    plt.xlabel('Frame')
    plt.ylabel('ADC Value')
    ax2_222.text(0.7,0.9,'{0:d} pixels'.format(len(pixel_data)),transform=ax2_222.transAxes)
    i = 1
    for p in pixel_data:
        plt.plot(p.data)
        ax2_222.text(0.7,0.9-0.1*i,'({0:d},{0:d})'.format(p.x,p.y),transform=ax2_222.transAxes)
        i += 1
    
    fig2.show()


    if args.save:
        fig1.savefig('fig1.png')
        fig2.savefig('fig2.png')

    ans = raw_input('pause')

   


   

