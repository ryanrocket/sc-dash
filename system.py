# Ryan Wans 2023 for South River Solar Hawks C2

###########################################################
# Main System Monitor to Drive Dashboard Display
###########################################################

# Packages
import sys, time, glob, serial, os, pprint
from datetime import datetime as dt
from w1thermsensor import W1ThermSensor as therm
from gpiozero import Buzzer
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(13, GPIO.IN)
GPIO.setup(19, GPIO.IN)
GPIO.setup(26, GPIO.IN)
GPIO.setup(20, GPIO.IN)
GPIO.setup(21, GPIO.IN)

# Yes this is sphegatt code i dont care

print("SOLAR CAR DASHBOARD 2023")
# Globals
def log(type, mes):
    print('[' + type.upper() + '] ' + mes)

__pins__ = {
    "buzzer": 17,
    "int_fan": 13,
    "bat_fan": 19,
    "int_lts": 26,
    "fwd": 20,
    "rev": 21
}
__globals__ = {
    "sensors": {
        "temp": {
            "dir": [],
            "locations": {
                "28-03059497131c": "cabin",
                "28-0304949749cc": "battery"
            },
            "domains": {
                "cabin": 85,
                "battery": 95
            }
        },
        "buzzer": Buzzer(__pins__["buzzer"]),
        "voltage": {
            "battery": {
                # Format: [100%,  90%, 80%,  70%,  60%,  50%,  40%,  30%,  20%,  15%,  12%,  10%,  5%]
                "curve":   [3.4, 3.22, 3.21, 3.2, 3.19, 3.18, 3.16, 3.15, 3.13, 3.11, 3.10, 3.08, 3.0],
                "warn": 3.1,
                "stop": 2.95
            }
        },
        "switches": {
            "all": ["int_fan", "bat_fan", "int_lts", "fwd", "rev"],
            "int_fan": False,
            "bat_fan": False,
            "int_lts": False,
            "fwd": False,
            "rev": False
        },
        "serial": None,
        "gps": None
    },
    "start_time": dt.now()
}
__state__ = {
    "status": False,
    "gear": "PARK",
    "indicators": {
        "bms": False,
        "bat_circ": False,
        "int_circ": False,
        "ext_lights": False,
        "int_lights": False
    },
    "warnings": {
        "ovht": False,
        "undervolt": False,
        "overdraw": False,
        "reception": False,
        "acc_undervolt": False,
        "acc_overdraw": False,
        "message": False
    },
    "lSignal": False,
    "rSignal": False,
    "message": False
}



# Initialization
def init():
    log("info", "Starting initialization process...")

    # Temperature Sensors
    tempsense_dir = '/sys/bus/w1/devices/'
    tempsense_devices = glob.glob(tempsense_dir + '28*')
    __globals__["sensors"]["temp"]["dir"] = tempsense_devices
    log("info", "Found " + str(len(tempsense_devices)) + " temperature sensors!")
    if(len(tempsense_devices) < 2):
        log("error", "Insufficient number of temperature sensors found (<2)!")
        # return [False, "Insufficient number of temperature sensors found (<2)!"]
        print("NONE")
    
    # Ardiuno Sensors
    if (not os.path.exists('/dev/ttyACM0')):
        log("error", "Arduino board not connected.")
        return [False, "Arduino board not connected."]
    else:
        log("info", "Arduino board connected!")
        __globals__["sensors"]["serial"] = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        __globals__["sensors"]["serial"].reset_input_buffer()
        # Get ALIVE message
        time.sleep(1)
        log("info", "Arduino status: " + __globals__["sensors"]["serial"].readline().decode('utf-8').rstrip())

    # GPS Module
    if (not os.path.exists('/dev/ttyAMA0')):
        log("error", "GPS module not connected.")
        return [False, "GPS module not connected."]
    else:
        log("info", "GPS module connected!")
        time.sleep(1)
        __globals__["sensors"]["gps"] = serial.Serial(
            port = '/dev/ttyAMA0',
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1
        )
        

    # Finish
    __state__["status"] = True
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
        # Format the data
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            readings[real_name] = temp_f
    # Return output
    sanitize_temperatures(readings)
    return readings

def read_switches():
    devices = __globals__["sensors"]["switches"]["all"]
    readings = {}
    for switch in devices:
        readings[switch] = GPIO.input(__pins__[switch])
    # pprint.pprint(readings)
    return readings

def read_arduino():
    # Send request for sensor data
    __globals__["sensors"]["serial"].write(b"?\n")
    # Buffer for ADC delay
    time.sleep(0.5)
    # Read raw data
    dataLine = __globals__["sensors"]["serial"].readline().decode('utf-8').rstrip()
    afrmLine = __globals__["sensors"]["serial"].readline().decode('utf-8').rstrip()
    # Sanatize data
    status = (afrmLine == "DONE")
    rawDataMatrix = dataLine.split(";")
    return [rawDataMatrix, status]

def alarm(state):
    if state:
        __globals__["sensors"]["buzzer"].beep()
    else:
        __globals__["sensors"]["buzzer"].off()



# Data Sanitization
def sanitize_temperatures(temps):
    state = {
        "cabOvh": (temps["cabin"] > __globals__["sensors"]["temp"]["domains"]["cabin"]),
        "batOvh": (temps["battery"] > __globals__["sensors"]["temp"]["domains"]["battery"]),
        "nc": (temps["cabin"] == 32 or temps["battery"] == 32)
    }

    if state["cabOvh"]:
        __state__["warnings"]["ovht"] = True
        __state__["message"] = ["CABIN TEMP OVER LIMIT", "temp"]
    elif state["batOvh"]:
        __state__["warnings"]["ovht"] = True
        __state__["message"] = ["BATTERY TEMP OVER LIMIT", "temp"]
    elif (state["cabOvh"] and state["batOvh"]):
        __state__["warnings"]["ovht"] = True
        __state__["message"] = ["BAT + CAB TEMP OVER LIMIT", "temp"]
    elif (state["nc"]):
        __state__["warnings"]["message"] = True
        __state__["message"] = ["TEMP SENSOR DISCON", "temp"]
    else:
        __state__["warnings"]["ovht"] = False
        if (__state__["message"] != False):
            if(__state__["message"][1] == "temp"):
                __state__["message"] = False

    return state

def sanatize_arduino(raw):
    # Order: Motor Current, Solar Current, Accessory Current, Motor Voltage, Solar Voltage
    data = raw[0]
    state = {
        "motorI": data[0],
        "solarI": data[1],
        "accsyI": data[2],
        "motorV": data[3],
        "solarV": data[4],
        "valid": raw[1]
    }
    return state


# Main
init()