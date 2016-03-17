"""
@author phansson
"""

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from GUIForm import EsaEpixForm


def main():
    app = QApplication(sys.argv)
    form = EsaEpixForm()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
