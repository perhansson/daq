import numpy as np
import matplotlib.pyplot as mpl


#f = np.load('loght_worker_frame_1.npz')
f = np.load('dark_worker_frame_1.npz')

print(f.files)

print f['dmean']


fig = mpl.figure(1)
ax1 = fig.add_subplot(221)
ax1.imshow(f['dmean'])

ax2 = fig.add_subplot(222)
ax2.imshow(f['dmean'][356:,384:])

fig.show()


#fig1 = mpl.figure(2)
#ax1 = fig1.add_subplot(111)
#ax.imshow(f['dmean'])

#fig.show()



ans = raw_input('wh')
