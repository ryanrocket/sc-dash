# Ryan Wans 2023 for South River Solar Hawks C2

import sys, time
from PyQt5 import QtWidgets, uic, QtCore

import images

import system

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
        # Start slow timer
        timerSlow = QtCore.QTimer(self)
        timerSlow.timeout.connect(self.slowEventTrigger)
        timerSlow.start(5000) 
        # Start fast timers
        timerFast = QtCore.QTimer(self)
        timerFast.timeout.connect(self.fastEventTrigger)
        timerFast.start(500)

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

    def slowEventTrigger(self):
        # Update Status
        if(system.__globals__["status"]):
            self.sys_status.setText("SYSTEM READY")
            self.sys_status.setStyleSheet("font: 500 30pt \"Open Sans\"; \
                                            color: green;")
        # Update Temperatures
        temps = system.read_temperatures()
        self.temp_internal.setText((str(round(temps["cabin"], 1)) + " F"))
        self.temp_battery.setText((str(round(temps["battery"], 1)) + " F"))

    def fastEventTrigger(self):
        # Update RTC
        current_time = QtCore.QTime.currentTime()
        label_time = current_time.toString('hh:mm:ss')
        self.time.setText(label_time)
        run_time = (time.time() - system.__globals__["start_time"])
        self.runTime.setText(run_time.strftime("%H:%M:%S"))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
	main()