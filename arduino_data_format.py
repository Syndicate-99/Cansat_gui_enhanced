import serial
import time

# TRY THESE PORTS ONE BY ONE
PORTS_TO_TRY = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7']  # Windows
# PORTS_TO_TRY = ['/dev/ttyUSB0', '/dev/ttyACM0']  # Linux/Mac

# TRY THESE BAUD RATES
BAUDS_TO_TRY = [9600, 115200]

print(" Scanning for Arduino...\n")

for port in PORTS_TO_TRY:
    for baud in BAUDS_TO_TRY:
        try:
            print(f"Trying {port} at {baud} baud...", end=' ')
            ser = serial.Serial(port, baud, timeout=2)
            time.sleep(2)  # Wait for Arduino reset
            # Try to read 5 lines
            lines_read = 0
            for _ in range(10):  # Try 10 times
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        if lines_read == 0:
                            print(f"\n FOUND IT!")
                            print(f"\n Port: {port}")
                            print(f" Baud: {baud}")
                            print(f"\n DATA FORMAT:\n")
                        print(f"  {line}")
                        lines_read += 1
                        if lines_read >= 5:
                            break
                time.sleep(0.1)

            ser.close()

            if lines_read > 0:
                print("\n" + "="*50)
                print("COPY THE LINES ABOVE AND SHOW THEM!")
                print("="*50)
                exit()
            else:
                print("No data")
        except Exception as e:
            print(f"✗")

print("\n Arduino not found. Check:")
print("  1. Arduino is plugged in")
print("  2. Drivers are installed")
print("  3. No other program is using it (close Arduino Serial Monitor!)")