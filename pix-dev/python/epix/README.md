
Instructions on how to start and stop a run with the ePix camera for ESA test beam.


Step 1. Log in to host 172.27.100.29

Step 2. Start the DAQ expert GUI

Start a terminal
$ cd /home/epix/run_software
$ source setup_env_esa.csh

Start DAQ expert GUI (this step will be removed later)
$ ./bin/epixEsaGui

Step 3. Start the ESA ePix monitoring and control tool

Start a new terminal
$ cd /home/epix/epix_gui
$ source setup.sh
$ cd daq_repo/pix-dev/python/epix

Start the software.
$ python run_epix_gui -i 5

The '-i' option tells you how many frames to integrate before updating plots. This can be changed from the GUI later. 

See more options with $ python run_epix_gui --help.

Select dark file:
Two options. 1) Click the button "Select dark file". Select the ".bin" dark file you want to use. 2) Click Get from DAQ Control. The latter will try to grab it from the DAQ control GUI (see later). 
The software will build the dark frame summary file automatically if it's not existing already.

Start monitoring:
Click "Acquire Start/Stop".
The bottom part of the GUI tells you which state the monitoring is in.
The text line at the top should indicate the frame ID (starts from 0 after each start of the GUI) it's processing and the approximate rate of the online monitoring. 

Open plots:
Click the individual plots. 
"Frame" is the regular image.

Select clustering:
Use the drop down menu to select which clustering. 

"None": no clustering (the cluster plots will be empty but frame image should work)
"Simple threshold": applies a threshold on all pixels. Should be configurable in the future. 


Step 4. Take a run with beam trigger
Click "DAQ Control GUI". A new GUI should pop up. 

The run number should be pre-filled and correspond to the latest run in the data directory.

Click "Start New Run"
NOTE: If the fields for dark and light files are empty (recommended!) filenames will be generated and displayed automatically.

Click "Start New Run"
The DAQ will be configured and a run will be started behind the scenes. A dark run will be taken first.
NOTE: Keep the DAQ expert GUI (from step 2) visible at this moment to see that the run has started and see the event count. 
Take about 300 events. This will be updated in the future to have all info in one place.

Click "Stop Dark Run" to end the dark run and automatically begin taking data. 

Click "Stop Run" to end the run. 

The run number will be automatically bumped if you follow step 4. 




