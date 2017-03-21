
import sys
import os
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar



d = np.load(sys.argv[1])
# plot channel 1,2,3
fig1 = plt.figure(3)
plt.hist(d.T[1:]) 
plt.hist(d.T[2:]) 
plt.hist(d.T[3:]) 



fig2 = plt.figure(4)
ax2 = fig2.add_subplot(111)

# new histogram
nbins = 50 # adc bins
h2d = np.zeros([d.shape[0],nbins])
#range of "image": x are channels, y is the ADC range
xmin = 0
xmax = d.shape[0]
ymin=9900
ymax=10500
# go through each channel and find the histogram (array) and assign to 2D "image"
for i in range(d.shape[0]):
    h,b = np.histogram(d[i:i+1],bins=nbins, range=(ymin,ymax))
    print(str(i) + ' h ' + str(h)+ ' b ' + str(b))
    h2d[i] = h

# range of z-axis
zmax = np.max(h2d)
zmin = np.min(h2d)
# plot as image
img2 = ax2.imshow(h2d.T, vmin=zmin,vmax=zmax,extent=[xmin, xmax, ymin, ymax], aspect='auto') #, interpolation='nearest', cmap='somemap')
# try also "pcolor", something similar, not sure what the difference is
fig2.colorbar(img2)
#plt.tight_layout()
plt.show()

