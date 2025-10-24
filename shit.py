import serial
ser = serial.Serial('COM8', 9600, timeout=1)
print("Connected to", ser.portstr)
import serial
import time

try:
    ser = serial.Serial(port='COM8', baudrate=9600, timeout=1)
    time.sleep(2)
    print(" Connected successfully to", ser.portstr)
    ser.close()
except Exception as e:
    print(" Connection failed:", e)
