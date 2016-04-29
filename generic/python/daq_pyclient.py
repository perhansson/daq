import sys
import pythonDaq
import time
sys.path.append('/home/epix/devel/epix_software_trunk_devel/python/pylib')
from daq_client import DaqClient, DaqClientException


if __name__ == '__main__':
    print('Open client')
    client = DaqClient('localhost',8090)

    #client.addStatusCallback(print_stuff)

    nodes = ['RunState', 'DataFileCount']

    print ('enable')
    client.enable()

    i = 0
    while i < 20:

        for node in nodes:
            res = client.daqReadStatusNode(node)
            if res != None:
                print('Node: \"' + res + '\"')
            else:
                print('Node: no result')
        time.sleep(1)
        i += 1
    
    client.disable()

    ans = raw_input('push anything to quit')


    print('Done')
    
    
