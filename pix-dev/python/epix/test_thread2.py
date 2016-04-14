import time, sys
from PyQt4.QtCore  import *
from PyQt4.QtGui import * 


class MyQThread(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
    def start(self):
        QThread.start(self)
    def run(self):
        QThread.run(self)

class SimulRunner(QObject):
    'Object managing the simulation'

    stepIncreased = pyqtSignal(int, name = 'stepIncreased')
    def __init__(self):
        super(SimulRunner, self).__init__()
        self._step = 0
        self._isRunning = True
        self._maxSteps = 20

    def longRunning(self):

        # reset
        if not self._isRunning:
            self._isRunning = True
            self._step = 0

        while self._step  < self._maxSteps  and self._isRunning == True:
            self._step += 1
            self.stepIncreased.emit(self._step)
            time.sleep(0.1)

        print('finished...')

    def stop(self):
        self._isRunning = False

class SimulationUi(QDialog):
    'PyQt interface'

    def __init__(self):
        super(SimulationUi, self).__init__()

        self.goButton = QPushButton('Go')
        self.stopButton = QPushButton('Stop')
        self.quitButton = QPushButton('Quit')
        self.currentStep = QSpinBox()

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.goButton)
        self.layout.addWidget(self.stopButton)
        self.layout.addWidget(self.quitButton)
        self.layout.addWidget(self.currentStep)
        self.setLayout(self.layout)

        self.simulThread = MyQThread()
        self.simulThread.start()

        self.simulRunner = SimulRunner()
        self.simulRunner.moveToThread(self.simulThread)
        self.simulRunner.stepIncreased.connect(self.currentStep.setValue)

        # call stop on simulRunner from this (main) thread on click
        self.stopButton.clicked.connect(lambda: self.simulRunner.stop())
        self.goButton.clicked.connect(self.simulRunner.longRunning)
        self.quitButton.clicked.connect(self.stop_thread)

    def stop_thread(self):
        self.simulRunner.stop()
        self.simulThread.quit()
        self.simulThread.wait()
    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = SimulationUi()
    simul.show()
    sys.exit(app.exec_())
