# Ryan Wans 2023 for South River Solar Hawks C2

###########################################################
# Main System Monitor to Drive Dashboard Display
###########################################################

# Packages
import sys, time, glob
from w1thermsensor import W1ThermSensor as therm

print("SOLAR CAR DASHBOARD 2023")
# Globals
__globals__ = {
    "init": False,
    "sensors": {}
}

def log(type, mes):
    print('[' + type.upper() + '] ' + mes)

# Initialization
def init():
    log("info", "Starting initialization process...")

    # Temperature Sensors
    tempsense_dir = '/sys/bus/w1/devices/'
    tempsense_devices = glob.glob(tempsense_dir + '28*')
    __globals__["sensors"]["temp"] = tempsense_devices
    log("info", "Found " + str(len(tempsense_devices)) + " temperature sensors!")

    # Finish
    __globals__["init"] = True

# Sensor Functionality

# Data Sanitization

init()