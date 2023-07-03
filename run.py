# Ryan Wans 2023 for South River Solar Hawks C2

import sys
from datetime import datetime as dt
from PyQt5 import QtWidgets, uic, QtCore

import images

import system

__state__ = {
    "data_visible": True
}

class FastUpdate(QtCore.QRunnable):
    def __init__(self, *args, **kwargs):
        super(FastUpdate, self).__init__()
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        # Fast Update Execution

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
        if(system.__state__["status"]):
            self.sys_status.setText("SYSTEM READY")
            self.sys_status.setStyleSheet("font: 600 30pt \"Open Sans\"; \
                                            color: green;")
        
        # Update Temperatures
        # self.updateTemps()

        # Update Arduino Sensor Readings
        self.updateArduino()

        # Update Switches
        self.updateSwitches()

        # Warnings 
        if (system.__state__["message"] != False):
            self.messageBut.setText(system.__state__["message"][0])
            self.messageBut.setStyleSheet(self.messageBut.styleSheet().replace("color: rgb(154, 153, 150);", "color: rgb(255, 120, 0);"))
            system.alarm(True)
        else:
            self.messageBut.setText("NO SYSTEM MESSAGES")
            self.messageBut.setStyleSheet(self.messageBut.styleSheet().replace("color: rgb(255, 120, 0);", "color: rgb(154, 153, 150);"))
            system.alarm(False)

    def fastEventTrigger(self):
        # Update RTC
        self.updateRTC()

    def updateArduino(self):
        data = system.sanatize_arduino(system.read_arduino())
        self.dataBatteryVolt.setText(str(data["motorV"]) + " V")
        self.dataSolarVolt.setText(str(data["solarV"]) + " V")
        self.dataBatteryDraw.setText(str(data["motorI"]) + " A")
        self.dataSolarDraw.setText(str(data["solarI"]) + " A")
        self.dataAccDraw.setText(str(data["accsyI"]) + " A")

    def updateTemps(self):
        temps = system.read_temperatures()
        self.temp_internal.setText((str(round(temps["cabin"], 1)) + " F"))
        self.temp_battery.setText((str(round(temps["battery"], 1)) + " F"))

    def updateSwitches(self):
        switches = system.read_switches()
        print(switches)
        for label in switches:
            if (switches[label] != 0):
                getattr(self, label).setStyleSheet(getattr(self, label).styleSheet().replace("143, 240, 164, 0.3", "143, 240, 164, 1"))
            else:
                getattr(self, label).setStyleSheet(getattr(self, label).styleSheet().replace("143, 240, 164, 1", "143, 240, 164, 0.3"))
        if (switches["fwd"] != 0) or (switches["rev"] != 0):
                getattr(self, "park").setStyleSheet(getattr(self, "park").styleSheet().replace("143, 240, 164, 1", "143, 240, 164, 0.3"))
        else:
                getattr(self, "park").setStyleSheet(getattr(self, "park").styleSheet().replace("143, 240, 164, 0.3", "143, 240, 164, 1"))

    def updateRTC(self):
        current_time = QtCore.QTime.currentTime()
        label_time = current_time.toString('hh:mm:ss')
        self.time.setText(label_time)
        run_time = (dt.now() - system.__globals__["start_time"]).seconds
        hours, remainder = divmod(run_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.runTime.setText('{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
	main()