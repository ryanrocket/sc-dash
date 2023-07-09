# debug gps over serial
import time, serial, io, pynmea2

ser = serial.Serial(
    port = '/dev/ttyAMA0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1)

sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
ser.reset_input_buffer()

while True:
    line = sio.readline()
    msg = pynmea2.parse(line)
    print(repr(msg))
    time.sleep(0.5)