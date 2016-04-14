import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time


class MyQThread(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
    def start(self):
        QThread.start(self)
    def run(self):
        QThread.run(self)
    def quit(self):
        print('stop call')
        QThread.stop(self)
        print('wait call')
        QThread.wait(self)
        print('terminate call')
        QThread.terminate(self)
        print('terminate called')


class Worker(QObject):
    finished = pyqtSignal()
    
    def __init__(self):
        super(Worker,self).__init__()
        self.running = True

    @pyqtSlot()
    def longRunning(self):
        while self.running:
            i = 0
            while i < 2:
                print('yes')
                time.sleep(1.0)
                i += 1
            #self.finished.emit()
            self.emit(SIGNAL('stop'))
            print('after emit')            
        print('finished')
        self.emit(SIGNAL('stopthread'))
    
    def stop(self):
        self.running = False
        


if __name__ == '__main__':
    app  = QApplication(sys.argv)
    worker = Worker()
    thread = MyQThread()
    worker.moveToThread(thread)    
    worker.finished.connect(thread.quit)
    #worker.finished.connect(worker.stop)
    worker.connect(worker,SIGNAL('stop'),worker.stop)
    worker.connect(worker,SIGNAL('stopthread'),thread.quit)
    thread.started.connect(worker.longRunning)
    thread.start()
    


    r = app.exec_()
    #app.deleteLater()

    sys.exit( r )

