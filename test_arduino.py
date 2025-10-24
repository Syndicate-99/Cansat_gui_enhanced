import serial
import time

# Change to YOUR port and baud rate
PORT = 'COM3'
BAUD_RATE = 9600

print(f"Connecting to {PORT}...")

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino reset
    print(" Connected!")
    print("\nReading data (press Ctrl+C to stop):\n")
    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(line)
            
except KeyboardInterrupt:
    print("\n\nStopped by user")
    ser.close()
except Exception as e:
    print(f" Error: {e}")
    
