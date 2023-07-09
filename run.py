# Ryan Wans 2023 for South River Solar Hawks C2

import sys
from datetime import datetime as dt
from PyQt5 import QtWidgets, uic, QtCore
from decimal import *

import images

import system

# Global Variables
__state__ = {
    "data_visible": True,
    "sat_num": 0,
    "tel_stat": False
}

# Buffer for smoothing input streams (probably just use kalman filter)
buffer = []

# Worker for 'Fast' Thread: ~500mS Interval (but just runs itself upon finishing, see below)
class FastUpdate(QtCore.QObject):

    # Signals
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

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
        except Exception as e:
            # uh oh
            system.log("error", "FastThread internal function exceution error!" + e)
            self.error.emit("FastThread internal function exceution error! " + str(e))

# Same but for the slow-updating functions: ~5S Interval
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

# Main Qt Application
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        # QtWidgets.QMainWindow.__init__(self, parent)
        super(MainWindow, self).__init__(parent)
        # Load UI from QtDesigner XML file (qtdesigner > coding an interface)
        uic.loadUi("./v01pre.ui", self)
        self.reset_but.clicked.connect(self.toggle_data_visibility)

        # Start slow timer
        timerSlow = QtCore.QTimer(self)
        timerSlow.setSingleShot(False)
        timerSlow.timeout.connect(self.startSlowWorker)
        # Saw somewhere that using prime numbers for intervals was better???
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
        # Explained below
        self.startFastWorker()
        system.log("info", "FastUpdate Worker connected to timerFast Interval: 500mS")

    # Show/Hide data aquisition on the dashboard
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

    # Start the Fast Thread
    @QtCore.pyqtSlot()
    def startFastWorker(self):
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
        # Re-run thread upon completition (good idea or bad????)
        self.threadFast.finished.connect(self.startFastWorker)
        self.fastWorker.error.connect(self.stopError)
        # Start thread
        self.threadFast.start()

    # Start the Slow Thread
    @QtCore.pyqtSlot()
    def startSlowWorker(self):
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

    # Function that gets run by the Slow Thread
    def slowEventTrigger(self):
        # Read the state of IO pins on the RPI
        dataStatus = system.__state__
        # Read sensors
        # dataTemps = self.updateTemps()          # commented out: errors out when no temp sensors plugged in
        dataArduino = self.updateArduino()
        dataSwitch = self.updateSwitches()
        # Pass to the slot function
        return [dataStatus, None, dataArduino, dataSwitch]

    # Signal that gets run by Slow Thread to update the display
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
        if(int(__state__["sat_num"]) > 0):
            self.tel_status.setText("NO SIGNAL")
            self.tel_status.setStyleSheet("font: 600 30pt \"Open Sans\"; \
                                            color: red;")
        else:
            self.tel_status.setText("GOOD: " + str(__state__["sat_num"]) + "-SAT")
            self.tel_status.setStyleSheet("font: 600 30pt \"Open Sans\"; \
                                            color: green;")
    
    # Function that gets run by the Fast Thread
    def fastEventTrigger(self):
        # temporary solution to monitor memory leaks (poor mans fix)
        system.log("memory", str(self.getCurrentMemoryUsage()) + " kB")
        system.log("info", "Starting Fast Update Event")
        # confirmed no memory leak (yay python) but leaving in for now anyways
        # Gets RTC data
        raw = self.updateRTC()
        # Encapsulating this all in a try/catch b/c sometimes it reads jargled data
        # If fails, the previous data persists in the display
        try:
            system.log("info", "Trying to read NMEA data")
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
                return [raw, [type(nmea).__name__], nmea]
        except:
            system.log("error", "Failed to read NMEA data")
            return [raw, [None], None]
    
    # Signal that gets run by Fast Thread to update the display
    @QtCore.pyqtSlot(object)
    def fastEventUpdate(self, result):
        # confirm that this shit actually runs
        system.log("info", "Running Display Updaters!")
        # Update Times
        self.time.setText(result[0][0])
        self.runTime.setText(result[0][1])
        # Treat GPS Data
        # another poor mans way to persist older data when new data is bad
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
                system.log("data", "Satellites: " + __state__["sat_num"])
            else:
                system.log("warn", "MSG TYPE: " + result[1][0])
        except:
            system.log("error", "Failed to write GPS data; falling back on previous buffer state.")

    # Will (eventually) get implemented to filter out noisy GPS readings
    def dataSmoothing(self, speed):
        if len(buffer) == 3:
            buffer.pop(0)
        buffer.append(speed)
        system.log("data", repr(buffer))

    # All the functions that collect data from the system.py implementation (IO interface)
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
    
    # Fatal error exiting for threads since you cant log outside of main thread
    @QtCore.pyqtSlot(str)
    def stopError(self, error):
        system.log("fatal", error)
        exit()

    # aforementioned memory monitoring 
    def getCurrentMemoryUsage(self):
        ''' Memory usage in kB '''

        with open('/proc/self/status') as f:
            memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

        return int(memusage.strip())

# run and pray
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec()

if __name__ == '__main__':
	main()