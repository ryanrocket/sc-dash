# Ryan Wans 2023 for South River Solar Hawks C2

import sys
from datetime import datetime as dt
from PyQt5 import QtWidgets, uic, QtCore
from decimal import *

import images

import system

__state__ = {
    "data_visible": True,
    "sat_num": 0,
    "tel_stat": False
}

buffer = []

class FastUpdate(QtCore.QObject):

    finished = QtCore.pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super(FastUpdate, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        # Fast Update Execution print(args, kwargs)
        try:
            data = self.fn(*self.args, **self.kwargs)
            self.finished.emit(data)
        except:
            system.log("error", "FastThread internal function exceution error!")

class SlowUpdate(QtCore.QRunnable):

    finished = QtCore.pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super(SlowUpdate, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        # Slow Update Execution print(args, kwargs)
        try:
            data = self.fn(*self.args, **self.kwargs)
            self.finished.emit(data)
        except:
            system.log("error", "SlowThread internal function exceution error!")
'''
class GPSUpdate(QtCore.QObject):

    write = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super(GPSUpdate, self).__init__()
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        # Run continuous GPS unit readings
'''

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        # QtWidgets.QMainWindow.__init__(self, parent)
        super(MainWindow, self).__init__(parent)
        uic.loadUi("./v01pre.ui", self)
        self.reset_but.clicked.connect(self.toggle_data_visibility)
        self.threadpool = QtCore.QThreadPool()
        system.log("info", "Multithreading with maximum of: %d Threads" % self.threadpool.maxThreadCount())

        # Start slow timer
        timerSlow = QtCore.QTimer(self)
        timerSlow.setSingleShot(False)
        timerSlow.timeout.connect(self.startSlowWorker)
        timerSlow.setInterval(4999)
        timerSlow.start() 
        system.log("info", "SlowUpdate Worker connected to timerSlow Interval: 5000mS")

        # Start fast timers
        '''
        timerFast = QtCore.QTimer(self)
        timerFast.setSingleShot(False)
        timerFast.timeout.connect(self.startFastWorker)
        timerFast.setInterval(499)
        timerFast.start()
        '''
        self.startFastWorker()
        system.log("info", "FastUpdate Worker connected to timerFast Interval: 500mS")

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

    @QtCore.pyqtSlot()
    def startFastWorker(self):
        # Create Multithreaded Workers
        # system.log("info", "Using " + str(self.threadpool.activeThreadCount()) + " (+1) of " + str(self.threadpool.maxThreadCount()) + " Available Threads")
        # Create Instantiations
        self.threadFast = QtCore.QThread()
        self.fastWorker = FastUpdate(self.fastEventTrigger)
        # Move to selected thread
        self.fastWorker.moveToThread(self.threadFast)
        # Create signal connections
        self.threadFast.started.connect(self.fastWorker.run)
        self.fastWorker.finished.connect(self.fastEventUpdate)
        self.fastWorker.finished.connect(self.threadFast.quit)
        self.fastWorker.finished.connect(self.fastWorker.deleteLater)
        self.threadFast.finished.connect(self.threadFast.deleteLater)
        self.threadFast.finished.connect(self.startFastWorker)
        # Start thread
        self.threadFast.start()

    @QtCore.pyqtSlot()
    def startSlowWorker(self):
        # Create Multithreaded Workers
        # system.log("info", "Using " + str(self.threadpool.activeThreadCount()) + " (+1) of " + str(self.threadpool.maxThreadCount()) + " Available Threads")
        # Create Instantiations
        self.threadSlow = QtCore.QThread()
        self.slowWorker = FastUpdate(self.slowEventTrigger)
        # Move to selected thread
        self.slowWorker.moveToThread(self.threadSlow)
        # Create signal connections
        self.threadSlow.started.connect(self.slowWorker.run)
        self.slowWorker.finished.connect(self.slowEventUpdate)
        self.slowWorker.finished.connect(self.threadSlow.quit)
        self.slowWorker.finished.connect(self.slowWorker.deleteLater)
        self.threadSlow.finished.connect(self.threadSlow.deleteLater)
        # Start thread
        self.threadSlow.start()

    def slowEventTrigger(self):
        # Update Status
        dataStatus = system.__state__
        # dataTemps = self.updateTemps()
        dataArduino = self.updateArduino()
        dataSwitch = self.updateSwitches()
        return [dataStatus, None, dataArduino, dataSwitch]

    @QtCore.pyqtSlot(object)
    def slowEventUpdate(self, result):
        # Update Arduino
        self.dataBatteryVolt.setText(str(result[2]["motorV"]) + " V")
        self.dataSolarVolt.setText(str(result[2]["solarV"]) + " V")
        self.dataBatteryDraw.setText(str(result[2]["motorI"]) + " A")
        self.dataSolarDraw.setText(str(result[2]["solarI"]) + " A")
        self.dataAccDraw.setText(str(result[2]["accsyI"]) + " A")
        # Update Temps
        # self.temp_internal.setText((str(round(result[1]["cabin"], 1)) + " F"))
        # self.temp_battery.setText((str(round(result[1]["battery"], 1)) + " F"))
        # Update Switches
        for label in result[3]:
            if (result[3][label] != 0):
                getattr(self, label).setStyleSheet(getattr(self, label).styleSheet().replace("143, 240, 164, 0.3", "143, 240, 164, 1"))
            else:
                getattr(self, label).setStyleSheet(getattr(self, label).styleSheet().replace("143, 240, 164, 1", "143, 240, 164, 0.3"))
        if (result[3]["fwd"] != 0) or (result[3]["rev"] != 0):
                getattr(self, "park").setStyleSheet(getattr(self, "park").styleSheet().replace("143, 240, 164, 1", "143, 240, 164, 0.3"))
        else:
                getattr(self, "park").setStyleSheet(getattr(self, "park").styleSheet().replace("143, 240, 164, 0.3", "143, 240, 164, 1"))
        # Update Warnings
        if(result[0]["status"]):
            self.sys_status.setText("SYSTEM READY")
            self.sys_status.setStyleSheet("font: 600 30pt \"Open Sans\"; \
                                            color: green;")
        if (result[0]["message"] != False):
            self.messageBut.setText(result[0]["message"][0])
            self.messageBut.setStyleSheet(self.messageBut.styleSheet().replace("color: rgb(154, 153, 150);", "color: rgb(255, 120, 0);"))
            system.alarm(True)
        else:
            self.messageBut.setText("NO SYSTEM MESSAGES")
            self.messageBut.setStyleSheet(self.messageBut.styleSheet().replace("color: rgb(255, 120, 0);", "color: rgb(154, 153, 150);"))
            system.alarm(False)
    
    def fastEventTrigger(self):
        # Update RTC & GPS Data
        # system.log("info", "Starting Fast Update Event")
        raw = self.updateRTC()
        try:
            # system.log("info", "Trying to read NMEA data")
            nmea = system.read_gps()
            if type(nmea).__name__ == "RMC":
                gps = ["RMC", nmea.timestamp, nmea.spd_over_grnd]
                return [raw, gps, nmea]
            elif type(nmea).__name__ == "VTG":
                gps = ["VTG", nmea.spd_over_grnd_kts]
                return [raw, gps, nmea]
            elif type(nmea).__name__ == "GGA":
                gps = ["GGA", nmea.timestamp, nmea.num_sats]
                return [raw, gps, nmea]
            else:
                return [raw, [None], nmea]
        except:
            system.log("error", "Failed to read NMEA data")
            return [raw, [None], None]
    
    @QtCore.pyqtSlot(object)
    def fastEventUpdate(self, result):
        # system.log("info", "Running Display Updaters!")
        # Update Times
        self.time.setText(result[0][0])
        self.runTime.setText(result[0][1])
        # Treat GPS Data
        try: 
            if (result[1][0] == "RMC"):
                # Speed Data
                system.log("data", repr(result[2]))
                speed = int(float(result[1][2]) * 1.151)
                if speed < 10:
                    speed = "0" + str(speed)
                    self.speed.setText(speed)
                else:
                    self.speed.setText(str(speed))
            elif (result[1][0] == "VTG"):
                # Speed Data
                system.log("data", repr(result[2]))
                speed = int(float(result[1][1]) * 1.151)
                if speed < 10:
                    speed = "0" + str(speed)
                    self.speed.setText(speed)
                else:
                    self.speed.setText(str(speed))
            elif (result[1][0] == "GGA"):
                # Sat Data
                __state__["sat_num"] = int(result[1][2])
        except:
            system.log("error", "Failed to write GPS data; falling back on previous buffer state.")

    def dataSmoothing(self, speed):
        if len(buffer) == 3:
            buffer.pop(0)
        buffer.append(speed)
        system.log("data", repr(buffer))

    def updateArduino(self):
        data = system.sanatize_arduino(system.read_arduino())
        return data

    def updateTemps(self):
        temps = system.read_temperatures()
        return temps

    def updateSwitches(self):
        switches = system.read_switches()
        return switches
        
    def updateRTC(self):
        current_time = QtCore.QTime.currentTime()
        label_time = current_time.toString('hh:mm:ss')
        run_time = (dt.now() - system.__globals__["start_time"]).seconds
        hours, remainder = divmod(run_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        runTime = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
        return [label_time, runTime]

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
	main()