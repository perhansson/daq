

Instructions on how to start and stop a run with the ePix camera for ESA test beam.


1. Log in to host 172.27.100.29

2. Start the DAQ control

Start a terminal
$ cd /home/epix/run_software
$ source setup_env_esa.csh

Start DAQ expert GUI (this step will be removed later)
$ ./bin/epixEsaGui

3. Start the ESA monitoring and control tool

Start a new terminal
$ cd epix_gui
$ source setup.sh
$ cd daq_repo/pix-dev/python/epix

Start the software.
$ python run_epix_gui -i 5

The '-i' option tells you how many frames to integrate before updating plots. 

See more options with $ python run_epix_gui --help.

Select dark file:
Click the button "Select dark file". Select the ".bin" dark file you want to use. 
The software will build the dark frame summary file automatically if it's not existing already.
NOTE: the selected file won't be shown in the text field directly here but will update once the data is coming in.

Start monitoring:
Click "Acquire Start/Stop".
The bottom part of the GUI tells you which state the monitoring is in.
The text line at the top should indicate the frame ID it's processing and the approximate rate. 

Open plots:
Click the individual plots. 
"Frame" is the regular image.

Select clustering:
Use the drop down menu to select which clustering. 

The only one to use right now is:
"None": no clustering (the cluster plots will be empty but frame is OK)
"Simple threshold": applies a threshold on all pixels. Typically 100ADC counts but can be configured.


4. Take a dark run with beam
Click "DAQ Control GUI". A new GUI should pop up.

Click "Select dark file" and/or specify a full path to a new dark file name that you want to save the data to. 
NOTE: If the field is empty a new filename will be automatically generated.

Click "Start"
The DAQ will be confiugured and a run will be started behind the scenes.
NOTE: Keep the DAQ expert GUI (from step 2) visible at this moment to see that the run has started and see the event count. 
Take about 300 events.  

Click "Stop" to end the dark run.

5. Take a normal run with beam
On the "DAQ Control GUI" under the beamtrigger section: click "Configure"
Wait for about 10s
NOTE: Keep the DAQ expert GUI (from step 2) visible at this moment to see that the run is being configured and controlled properly. This will not be needed in the future.

Select a file or type in a full path to a file where you want to save the data.

Click "Start". 

NOTE: The online monitoring needs to be running to see update to plots (see step 3).



