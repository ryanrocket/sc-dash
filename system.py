# Ryan Wans 2023 for South River Solar Hawks C2

###########################################################
# Main System Monitor to Drive Dashboard Display
###########################################################

# Packages
import sys, time, glob
from datetime import datetime as dt
from w1thermsensor import W1ThermSensor as therm

print("SOLAR CAR DASHBOARD 2023")
# Globals
__globals__ = {
    "status": False,
    "sensors": {
        "temp": {
            "dir": [],
            "locations": {
                "28-03059497131c": "cabin",
                "28-0304949749cc": "battery"
            }
        }
    },
    "start_time": dt.now()
}

def log(type, mes):
    print('[' + type.upper() + '] ' + mes)



# Initialization
def init():
    log("info", "Starting initialization process...")

    # Temperature Sensors
    tempsense_dir = '/sys/bus/w1/devices/'
    tempsense_devices = glob.glob(tempsense_dir + '28*')
    __globals__["sensors"]["temp"]["dir"] = tempsense_devices
    log("info", "Found " + str(len(tempsense_devices)) + " temperature sensors!")
    if(len(tempsense_devices) < 2):
        return [False, "Insufficient number of temperature sensors found (<2)!"]

    # Finish
    __globals__["status"] = True
    return [True, ""]



# Sensor Functionality
def read_temperatures():
    devices = __globals__["sensors"]["temp"]["dir"]
    readings = {}
    for sensor in devices:
        # First get name of device
        f = open((sensor + '/name'), 'r')
        lines = f.readlines()
        f.close()
        name = lines[0].strip()
        real_name = __globals__["sensors"]["temp"]["locations"][name]
        # Now get current reading
        f = open((sensor + '/w1_slave'), 'r')
        lines = f.readlines()
        f.close()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            readings[real_name] = temp_f
    # Return output
    return readings



# Data Sanitization



# Main
init()