
import time
import numpy as np
#from sklearn.cluster import MeanShift, estimate_bandwidth




class SimpleCluster(object):
    def __init__(self,ix,iy,signal,n):
        self.ix = ix
        self.iy = iy
        self.signal = signal
        self.n = n



def find_meanshift_clusters(data):
    t0 = time.clock()
    ms = MeanShift()
    ms.fit(data)
    print('Mean shift in {} sec'.format(time.clock()-t0))
    labels = ms.labels_
    centers = ms.cluster_centers_
     #create a new frame
    cluster_frame = np.zeros(data.shape)
    clusters = []
    print('found {0} centers'.format(len(centers)))
    for c in centers:
        my_members = labels == k
        y_arr = data[ my_members, 0]
        x_arr = data[ my_members, 1]
        print('center ix {0} iy {1} n {2}'.format(centers[k][1],centers[k][1],len(y_arr)))
        print('y_arr')
        print(y_arr)
        print('x_arr')
        print(x_arr)
        signal_sum = 2000.
        cluster.append(SimpleCluster(centers[k][1], centers[k][0],singal_sum,len(y_arr)))
        cluster_frame[centers[k][1]][centers[k][0]] = signal_sum
    print('total Mean shift in {} sec'.format(time.clock()-t0))
    return cluster_frame, clusters

def find_fixedwindow_clusters(a0, noise_level, n_sigma, window_size):

    # timer
    t0 = time.clock()

    #create a new frame
    cluster_frame = np.zeros(a0.shape)

    # select seeds based on this threshold
    threshold = n_sigma*noise_level

    # select the seeds
    seeds = (a0 > threshold).astype(np.int16)

    np.savez('input_frame.npz',frame=a0)

    #print(seeds)

    # number of pixels
    mx = a0.shape[1]
    my = a0.shape[0]

    # slide window across frame
    iy_range = range(0,my,window_size)
    ix_range = range(0,mx,window_size)
    clusters = []
    for iy in iy_range:
        for ix in ix_range:                
            # sum up pixels above threshold in window
            seeds_window = seeds[iy:iy+window_size, ix:ix+window_size]
            #print('seed window')
            #print(seeds_window)
            #print(a0[iy:iy+window_size, ix:ix+window_size])
            n_above = np.sum( seeds_window )
            #print('iy {0} ix {1} n_above {2}'.format(iy,ix,n_above))
            #if iy <my/2 and ix > mx/2:
            #    print('iy {0} ix {1} n_above {2}'.format(iy,ix,n_above))
            #    print('seed window')
            #    print(seeds_window)
            #    print(a0[iy:iy+window_size, ix:ix+window_size])
            if n_above > 0:                    
                signal_sum = np.sum( a0[iy:iy+window_size, ix:ix+window_size] )
                if signal_sum > threshold:
                    #print('found cluster at iy {0} ix {1} with {2} above threshold {3} signal'.format(ix,iy,n_above, signal_sum))
                    #print('seed window')
                    #print(seeds_window)
                    #print(a0[iy:iy+window_size, ix:ix+window_size])
                    cluster_frame[iy+window_size/2,ix+window_size/2] = signal_sum
                    clusters.append( SimpleCluster(ix+window_size/2,iy+window_size/2,signal_sum,n_above))
    print( 'Found ' + str(len(clusters)) + ' clusters in '+str(time.clock()-t0)+' s (total signal: ' + str (np.sum(cluster_frame)) + ' average signal ' + str(np.sum(cluster_frame)/len(clusters)))
    return cluster_frame, clusters






def find_seed_clusters(a0, noise_level, n_sigma, seed_size, n_pixels, max_signal=9999999):
    """
    Find clusters.

    Return new frame and cluster objects.
    """

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
    clusters = []
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
                            clusters.append( SimpleCluster(ix,iy,cluster_signal,n))
                            # no overlaps, this is getting ugly
                            #ix += seed_size
                            #iy += seed_size
                            #continue
    print( 'Found ' + str(len(clusters)) + ' seed clusters in '+str(time.clock()-t0)+' s')
    return sf, clusters
