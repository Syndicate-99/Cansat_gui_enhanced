# 🔌 Arduino Connection Guide - Complete Setup

## 📦 What You Got - New Version v2.0

✨ **NEW FEATURES:**
- ✅ Real Arduino/COM port support
- ✅ Press 'S' key to toggle serial ON/OFF
- ✅ Visual serial status indicator (green/red)
- ✅ Auto-detect and list available COM ports
- ✅ Configurable baud rate
- ✅ Proper data parsing
- ✅ All previous bug fixes included

---

## 🚀 Quick Start (3 Options)

### Option 1: Test with Simulator (No Arduino)
```python
# Line 613 in cansat_gui_enhanced.py:
self.ser = Communication(use_simulator=True)
```
**Run:** `python cansat_gui_enhanced.py`

---

### Option 2: Connect to Real Arduino
```python
# Line 613 in cansat_gui_enhanced.py:
self.ser = Communication(port='COM3', baudrate=9600, use_simulator=False)
```
**Change `COM3` to YOUR port!**

---

### Option 3: Auto-detect Port
```python
# Add at the start of your code:
available_ports = Communication.list_ports()
print(f"Available ports: {available_ports}")

# Use first available port:
if available_ports:
    self.ser = Communication(port=available_ports[0], baudrate=9600)
```

---

## 🎮 Keyboard Controls

**Press 'S' key** → Toggle serial communication ON/OFF

**Visual Indicator:**
- 🟢 **Green "Serial ON"** → Receiving data
- 🔴 **Red "Serial OFF"** → Paused

**When to use:**
- Start/stop receiving data without closing GUI
- Pause to check Arduino code
- Save bandwidth when not recording
- Debug connection issues

---

## 📋 Step-by-Step Arduino Setup

### Step 1: Install pyserial
```bash
pip install pyserial
```

### Step 2: Find Your COM Port

**Method A - Windows Device Manager:**
1. Connect Arduino
2. Open Device Manager
3. Expand "Ports (COM & LPT)"
4. Look for "Arduino" → Note the COM number (e.g., COM3)

**Method B - Python Script:**
```python
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"{port.device} - {port.description}")
```

**Method C - Arduino IDE:**
1. Open Arduino IDE
2. Tools → Port
3. Your Arduino port is listed there

---

### Step 3: Check Your Baud Rate

**Look in your Arduino sketch for:**
```cpp
void setup() {
    Serial.begin(9600);  // ← This is your baud rate!
}
```

Common baud rates:
- 9600 (default, most common)
- 115200 (faster, recommended for CanSat)
- 57600
- 38400

---

### Step 4: Format Your Arduino Data

Your Arduino must send data as **comma-separated values (CSV)** with 13 values:

```cpp
void loop() {
    // Read sensors
    float currentTime = millis() / 1000.0;
    float altitude = readAltitude();       // BMP280, BME280, etc.
    float temperature = readTemperature();  // BME280, DHT22, etc.
    float pressure = readPressure();        // BMP280, BME280
    float humidity = readHumidity();        // BME280, DHT22
    float gyro_x = readGyroX();            // MPU6050, MPU9250, etc.
    float gyro_y = readGyroY();
    float gyro_z = readGyroZ();
    float accel_x = readAccelX();          // MPU6050, MPU9250
    float accel_y = readAccelY();
    float accel_z = readAccelZ();
    float latitude = readGPS_Lat();        // GPS module
    float longitude = readGPS_Lon();
    
    // Send as CSV (13 values, comma-separated)
    Serial.print(currentTime); Serial.print(",");
    Serial.print(altitude); Serial.print(",");
    Serial.print(temperature); Serial.print(",");
    Serial.print(pressure); Serial.print(",");
    Serial.print(humidity); Serial.print(",");
    Serial.print(gyro_x); Serial.print(",");
    Serial.print(gyro_y); Serial.print(",");
    Serial.print(gyro_z); Serial.print(",");
    Serial.print(accel_x); Serial.print(",");
    Serial.print(accel_y); Serial.print(",");
    Serial.print(accel_z); Serial.print(",");
    Serial.print(latitude); Serial.print(",");
    Serial.println(longitude);  // println adds newline at end
    
    delay(500);  // Send data every 500ms (2 Hz)
}
```

**Example output:**
```
123.45,456.78,25.3,1013.2,50.5,10.2,20.5,15.8,0.5,0.3,9.8,13.3379,74.7461
124.45,458.12,25.4,1013.1,50.4,11.5,19.8,16.2,0.6,0.2,9.7,13.3379,74.7461
```

---

### Step 5: Test Arduino Connection

**Create `test_serial.py`:**
```python
import serial
import time

PORT = 'COM3'  # Change to your port!
BAUDRATE = 9600  # Match your Arduino

print(f"Connecting to {PORT} at {BAUDRATE} baud...")

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)  # Wait for Arduino reset
    print("✅ Connected! Reading data:\n")
    
    for i in range(20):  # Read 20 lines
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"[{i+1}] {line}")
        time.sleep(0.5)
    
    ser.close()
    print("\n✅ Test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

**Run it:**
```bash
python test_serial.py
```

**Expected output:**
```
Connecting to COM3 at 9600 baud...
✅ Connected! Reading data:

[1] 10.23,152.45,24.8,1012.5,52.3,8.5,12.3,9.8,0.4,0.2,9.81,13.3379,74.7461
[2] 10.73,153.12,24.9,1012.4,52.2,9.1,11.8,10.2,0.5,0.3,9.79,13.3379,74.7461
...
```

---

### Step 6: Configure the GUI

Open `cansat_gui_enhanced.py` and find line ~613:

**Change this:**
```python
# OLD (simulator):
self.ser = Communication(use_simulator=True)
```

**To this (real Arduino):**
```python
# NEW (real Arduino):
self.ser = Communication(port='COM3', baudrate=9600, use_simulator=False)
```

**Replace:**
- `'COM3'` with YOUR COM port
- `9600` with YOUR baud rate

---

### Step 7: Run the GUI

**IMPORTANT:** Close Arduino Serial Monitor first! (It blocks the port)

```bash
python cansat_gui_enhanced.py
```

**What you should see in console:**
```
✅ Connected to COM3 at 9600 baud
```

**In the GUI:**
- 🟢 "Serial ON" indicator (top right)
- Graphs updating with real data
- Packet counter increasing

---

## 🎯 Testing Checklist

- [ ] Install pyserial (`pip install pyserial`)
- [ ] Find COM port (e.g., COM3)
- [ ] Check baud rate in Arduino code
- [ ] Test with `test_serial.py` first
- [ ] Close Arduino Serial Monitor
- [ ] Update port in `cansat_gui_enhanced.py`
- [ ] Run GUI
- [ ] Press 'S' to test pause/resume

---

## ⚙️ Customizing Data Format

If your Arduino sends data differently, modify the `parse_data()` function:

**Example 1: Key-Value Format**
Arduino sends: `ALT:456.78,TEMP:25.3,GX:10.5`

```python
def parse_data(self, line):
    try:
        data = [0] * 13  # Initialize with zeros
        parts = line.split(',')
        for part in parts:
            if ':' in part:
                key, value = part.split(':')
                if key == 'ALT':
                    data[1] = float(value)
                elif key == 'TEMP':
                    data[2] = float(value)
                # ... add more mappings
        return data
    except:
        return None
```

**Example 2: JSON Format**
Arduino sends: `{"alt":456.78,"temp":25.3}`

```python
def parse_data(self, line):
    try:
        import json
        obj = json.loads(line)
        data = [
            obj.get('time', 0),
            obj.get('alt', 0),
            obj.get('temp', 0),
            # ... map all 13 fields
        ]
        return data
    except:
        return None
```

---

## 🐛 Troubleshooting

### Issue 1: "Serial port not found"
**Cause:** Wrong COM port or Arduino not connected

**Fix:**
```python
# List available ports
print(Communication.list_ports())
```

### Issue 2: "Permission denied" or "Access denied"
**Cause:** Port is being used by another program

**Fix:**
- Close Arduino Serial Monitor
- Close other serial programs (PuTTY, etc.)
- Unplug and replug Arduino
- Restart computer if needed

### Issue 3: Getting garbage data
**Cause:** Wrong baud rate

**Fix:**
- Check `Serial.begin(XXXX)` in Arduino
- Match baud rate in GUI: `Communication(port='COM3', baudrate=XXXX)`

### Issue 4: "Not enough values" warning
**Cause:** Arduino not sending 13 values

**Fix:**
- Check Arduino output with `test_serial.py`
- Count commas (should be 12 commas = 13 values)
- Ensure using `Serial.println()` at the end (adds newline)

### Issue 5: Data not updating
**Cause:** Serial is paused

**Fix:**
- Check indicator: Should be 🟢 "Serial ON"
- Press 'S' key to resume
- Look for alert: "Serial STARTED"

---

## 📊 Data Requirements Summary

**Your Arduino MUST send:**
1. **13 values** separated by commas
2. **One line per packet** (use `Serial.println()` at end)
3. **Numbers as text** (e.g., "123.45" not binary)
4. **Every 500ms** (2 Hz minimum, 10 Hz max recommended)

**Order of values:**
```
0:  Time (seconds since start)
1:  Altitude (meters)
2:  Temperature (Celsius)
3:  Pressure (hPa or mbar)
4:  Humidity (%)
5:  Gyroscope X (deg/s)
6:  Gyroscope Y (deg/s)
7:  Gyroscope Z (deg/s)
8:  Accelerometer X (m/s²)
9:  Accelerometer Y (m/s²)
10: Accelerometer Z (m/s²)
11: GPS Latitude (decimal degrees)
12: GPS Longitude (decimal degrees)
```

---

## 💡 Pro Tips

1. **Use 115200 baud** for faster data transmission
2. **Send data every 500ms** (2 Hz) for smooth graphs
3. **Test without sensors** first (send dummy values)
4. **Add checksum** for data integrity (optional)
5. **Use hardware serial** if available (not software serial)
6. **Close Arduino Serial Monitor** before running GUI!

---

## 🎓 Example Arduino Sketch (Minimal)

```cpp
void setup() {
    Serial.begin(9600);  // or 115200 for faster
}

void loop() {
    // Dummy data for testing (replace with real sensor reads)
    float time = millis() / 1000.0;
    float altitude = 100.0 + random(0, 50);  // Random 100-150m
    float temp = 25.0;
    float pressure = 1013.0;
    float humidity = 50.0;
    float gx = 0.0, gy = 0.0, gz = 0.0;
    float ax = 0.0, ay = 0.0, az = 9.8;
    float lat = 13.3379, lon = 74.7461;
    
    // Send CSV format
    Serial.print(time); Serial.print(",");
    Serial.print(altitude); Serial.print(",");
    Serial.print(temp); Serial.print(",");
    Serial.print(pressure); Serial.print(",");
    Serial.print(humidity); Serial.print(",");
    Serial.print(gx); Serial.print(",");
    Serial.print(gy); Serial.print(",");
    Serial.print(gz); Serial.print(",");
    Serial.print(ax); Serial.print(",");
    Serial.print(ay); Serial.print(",");
    Serial.print(az); Serial.print(",");
    Serial.print(lat); Serial.print(",");
    Serial.println(lon);
    
    delay(500);  // 2 Hz
}
```

---

## ✅ Final Checklist

Before competition day:

- [ ] pyserial installed
- [ ] COM port identified
- [ ] Baud rate matched
- [ ] Arduino sends 13 CSV values
- [ ] Tested with test_serial.py
- [ ] GUI receives real data
- [ ] Keyboard toggle ('S' key) works
- [ ] Data export tested
- [ ] Have backup cable!
- [ ] Know how to reconnect quickly

---

**You're ready! Good luck with your CanSat! 🚀🛰️**
