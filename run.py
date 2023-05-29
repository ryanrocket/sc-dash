# Ryan Wans 2023 for South River Solar Hawks C2

import sys
from PyQt5 import QtWidgets, uic, QtCore

import images

from system import *

__state__ = {
    "data_visible": True,
    "gear": "PARK"
}

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        # QtWidgets.QMainWindow.__init__(self, parent)
        super(MainWindow, self).__init__(parent)
        uic.loadUi("./v01pre.ui", self)
        print(self)
        self.reset_but.clicked.connect(self.toggle_data_visibility)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.mainEventTrigger)
        timer.start(1000)

    @QtCore.pyqtSlot()
    def toggle_data_visibility(self):
        print("Toggling Data Group")
        if(__state__["data_visible"]):
            self.data.hide()
            self.data_div.hide()
        else:
            self.data.show()
            self.data_div.show()
        __state__["data_visible"] = not __state__["data_visible"]

    def mainEventTrigger(self):
        # Update RTC
        current_time = QtCore.QTime.currentTime()
        label_time = current_time.toString('hh:mm:ss')
        self.time.setText(label_time)
        # Update Temperatures
        temps = read_temperatures()
        self.temp_internal.setText(str(round(temps["cabin"], 1)))
        self.temp_battery.setText(str(round(temps["battery"], 1)))

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
	main()