import sys
from PyQt5 import QtWidgets, uic

import images

app = QtWidgets.QApplication(sys.argv)

window = uic.loadUi("./v01pre.ui")
window.show()
app.exec()
