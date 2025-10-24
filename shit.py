import serial
import time

try:
    ser = serial.Serial(port='COM8', baudrate=9600, timeout=1)
    time.sleep(2)  # Give time for Arduino to reset
    ser.flush()
    print("Connected successfully to", ser.portstr)

    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8', errors='ignore').strip()
            print("Received:", data)
        time.sleep(0.5)
except Exception as e:
    print("Connection failed:", e)
