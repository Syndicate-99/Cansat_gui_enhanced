# 🧪 CanSat GUI Testing Guide

## Quick Start Testing

### Method 1: Automatic Flight Simulation (Recommended)

```bash
# Run the test launcher
python test_cansat_gui.py
```

This will:
- ✅ Launch the GUI with simulated flight data
- ✅ Simulate a complete 250-second flight (runs at 2x speed)
- ✅ Show realistic telemetry from pre-launch to landing
- ✅ Automatically trigger phase changes and alerts

### Method 2: Manual Testing with Random Data

The GUI already includes fallback dummy data if the communication module isn't available.

```bash
# Just run the enhanced GUI directly
python cansat_gui_enhanced.py
```

---

## 📋 What to Test

### 1. Pre-Launch Phase (0-5 seconds)
**What to Check:**
- [ ] Mission Phase shows "Pre-Launch" (gray)
- [ ] Altitude stays at ~0m
- [ ] Gyroscope values are near zero
- [ ] Pre-flight checklist items can be checked
- [ ] "System Status" turns green when all checked

**Actions:**
1. Go to "Pre-Flight" tab
2. Check all checklist items
3. Verify status changes to "READY FOR LAUNCH"

---

### 2. Ascent Phase (5-120 seconds)
**What to Check:**
- [ ] Mission Phase shows "Ascent" (green)
- [ ] Altitude graph shows upward trend
- [ ] Speed increases then stabilizes
- [ ] Gyroscope shows rotation (tumbling)
- [ ] Max Altitude updates in Mission Stats
- [ ] Data Quality shows packets being received

**Expected Values:**
- Altitude: 0m → 1000m (gradually)
- Speed: 0 → 8 m/s
- Gyroscope: Random rotation values

---

### 3. Deployment Phase (120-125 seconds)
**What to Check:**
- [ ] Mission Phase shows "Deployment" (yellow)
- [ ] Alert appears: Check for deployment notification
- [ ] Speed suddenly decreases (parachute opens)
- [ ] Gyroscope shows high rotation values (tumbling)
- [ ] Acceleration shows negative spike

**Expected Behavior:**
- This is a CRITICAL moment judges want to see
- Speed should drop from ~5 m/s to near 0 quickly
- Should see alert message in alerts panel

---

### 4. Descent Phase (125-240 seconds)
**What to Check:**
- [ ] Mission Phase shows "Descent" (orange)
- [ ] Altitude decreases steadily
- [ ] Speed stabilizes around 5 m/s (terminal velocity)
- [ ] Gyroscope shows gentle swaying
- [ ] Descent Rate displays correctly

**Expected Values:**
- Constant descent: ~5 m/s
- Altitude: 1000m → 0m
- Gentle rotation due to parachute spinning

---

### 5. Landing Phase (240+ seconds)
**What to Check:**
- [ ] Mission Phase shows "Landing" (red)
- [ ] Altitude reaches 0m and stays there
- [ ] Speed drops to 0 m/s
- [ ] All movement stops
- [ ] Mission timer continues

---

### 6. Data Export & Analysis
**What to Test:**

1. **During Flight:**
   - Click "Start Mission" → Check recording indicator
   - Let it run for 30+ seconds
   - Click "Stop Mission"
   - Click "Export Data" → Save CSV file

2. **After Flight:**
   - Go to "Analysis" tab
   - Click "Load Flight Data" → Select your exported CSV
   - Click "Generate Report" → Check statistics

**Verify CSV Contains:**
```csv
Time,Altitude,Speed,Acceleration,Gyro_X,Gyro_Y,Gyro_Z
0.0,0.0,0.0,9.8,0.1,0.1,0.1
1.0,0.0,0.0,9.8,0.1,0.1,0.1
...
```

---

## 🔍 Detailed Test Scenarios

### Test Scenario 1: Normal Flight
**Duration:** 5 minutes  
**Goal:** Verify all phases work correctly

1. Start the GUI
2. Go to Real-Time tab
3. Click "Start Mission"
4. Watch the simulation for 5 minutes
5. Verify phase transitions
6. Click "Export Data"
7. Go to Analysis tab and load the data

**Success Criteria:**
- All 6 phases completed
- No crashes or errors
- Data exported successfully
- Graphs show smooth transitions

---

### Test Scenario 2: Alert System
**Duration:** 2 minutes  
**Goal:** Test alert notifications

Watch for these automatic alerts:
1. "Mission started!" (INFO - green)
2. "Approaching maximum altitude!" (WARNING - yellow) at ~900m
3. "Low altitude - Landing phase" (INFO - green) at <100m

**Manual Alert Test:**
You can add this code to trigger custom alerts:
```python
self.alerts_panel.add_alert("Test Warning", "WARNING")
self.alerts_panel.add_alert("Test Critical", "CRITICAL")
```

---

### Test Scenario 3: Data Quality Monitoring
**Duration:** 2 minutes  
**Goal:** Verify packet statistics

Check the Data Quality panel:
1. Packets Received: Should increase continuously
2. Packets Lost: Should stay at 0 (simulator is perfect)
3. Packet Loss: Should show 0.0%
4. Last Packet: Updates every ~0.5s
5. Connection: Green dot (●)

---

### Test Scenario 4: Pre-Flight Checklist
**Duration:** 1 minute  
**Goal:** Test system readiness check

1. Go to "Pre-Flight" tab
2. Initially: Red "NOT READY" status
3. Check each item one by one:
   - GPS Lock Acquired
   - All Sensors Calibrated
   - Battery > 80%
   - Storage Space Available
   - Ground Station Connected
   - Parachute System Armed
4. Verify status turns green: "READY FOR LAUNCH"

---

### Test Scenario 5: Mission Statistics
**Duration:** 3 minutes  
**Goal:** Verify statistical tracking

Monitor Mission Statistics panel:

**During Flight:**
- Max Altitude should increase during ascent
- Max Altitude should NOT change during descent (it's the max!)
- Max Speed captures highest velocity
- Flight Time increases continuously
- Current Altitude updates in real-time

**At End of Flight:**
- Max Altitude: ~1000m
- Max Speed: ~8 m/s
- Flight Time: ~250 seconds
- Current Altitude: 0m

---

## 🎯 Competition-Ready Tests

### Judge Presentation Test
**What Judges Want to See:**

1. **Clear Visual Indicators**
   - Show the mission phase indicator
   - Point out the color coding (green=good, red=critical)

2. **Data Quality Proof**
   - Show packet statistics (proves reliable telemetry)
   - Show connection status (green dot)

3. **Key Metrics**
   - Max altitude achieved
   - Flight duration
   - Successful parachute deployment

4. **Data Logging**
   - Show that data was recorded throughout flight
   - Export CSV as proof
   - Show analysis capabilities

**Practice Script:**
```
"Our ground station GUI shows real-time telemetry with mission phase 
tracking. As you can see, we successfully reached [X] meters altitude 
and our parachute deployed at [Y] seconds. We achieved a packet loss 
rate of [Z]%, demonstrating reliable communications. All data was 
logged and is available for detailed analysis."
```

---

## 🐛 Common Issues & Fixes

### Issue 1: GUI doesn't start
**Error:** `ModuleNotFoundError: No module named 'PyQt5'`

**Fix:**
```bash
pip install PyQt5 pyqtgraph numpy pandas
```

---

### Issue 2: Blank graphs
**Problem:** Graphs show but no data appears

**Fix:**
- Wait 1-2 seconds for data to accumulate
- Check console for error messages
- Verify simulator is running (print statements)

---

### Issue 3: Mission timer not updating
**Problem:** LCD display shows 0.00

**Fix:**
- Click "Start Mission" button first
- This initializes the mission timer

---

### Issue 4: Alerts panel empty
**Problem:** No alerts appear

**Fix:**
- Alerts only appear during specific events
- Try clicking "Start Mission" (triggers INFO alert)
- Wait for altitude > 900m (triggers WARNING alert)

---

## 📊 Expected Test Results

After a complete 250-second simulation:

```
MISSION STATISTICS:
├─ Max Altitude: ~1000m (± 50m due to noise)
├─ Max Speed: ~8 m/s
├─ Flight Time: ~250 seconds
└─ Descent Rate: ~5 m/s

DATA QUALITY:
├─ Packets Received: ~500 (2 per second)
├─ Packets Lost: 0
├─ Packet Loss Rate: 0.0%
└─ Connection: CONNECTED

PHASES COMPLETED:
✓ Pre-Launch (0-5s)
✓ Ascent (5-120s)
✓ Deployment (120-125s)
✓ Descent (125-240s)
✓ Landing (240s+)
```

---

## 🚀 Advanced Testing

### Add Packet Loss Simulation
Want to test with realistic packet loss?

Add this to `flight_simulator.py`:

```python
def getData(self):
    # Simulate 5% packet loss
    if random.random() < 0.05:
        return None  # Lost packet
    
    return self.simulator.update(dt * 2)
```

Then in the GUI's `update_data()`:
```python
if data is None:  # Lost packet
    self.packets_lost += 1
    return
```

---

### Test with Real Serial Data (When Available)
When you have real hardware:

1. Comment out the simulator in `cansat_gui_enhanced.py`
2. Replace with real serial code:

```python
import serial

class Communication:
    def __init__(self, port='COM3', baudrate=9600):
        self.ser = serial.Serial(port, baudrate)
    
    def getData(self):
        if self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8').strip()
            # Parse your telemetry format
            return parse_telemetry(line)
```

---

## ✅ Final Checklist Before Competition

**Software Tests:**
- [ ] GUI launches without errors
- [ ] All tabs are accessible
- [ ] Graphs update smoothly
- [ ] Data export works
- [ ] Analysis tools functional
- [ ] No lag or freezing

**Presentation Tests:**
- [ ] Screen is readable from 2 meters away
- [ ] Colors are clear (especially phase indicators)
- [ ] Font sizes appropriate
- [ ] Mission timer visible
- [ ] Alerts panel easily readable

**Data Tests:**
- [ ] Can export CSV successfully
- [ ] Can reload exported data
- [ ] Can generate report
- [ ] CSV opens in Excel/Google Sheets

**Backup Tests:**
- [ ] Have screenshots ready
- [ ] Have backup data file
- [ ] Know how to restart GUI quickly
- [ ] Have manual data recording method ready

---

## 💡 Tips for Success

1. **Test Early, Test Often**
   - Run the simulator daily leading up to competition
   - Get familiar with all features

2. **Practice Your Demo**
   - Time yourself explaining the GUI (< 2 minutes)
   - Focus on unique features (mission phases, alerts)

3. **Prepare for Questions**
   - "How do you detect packet loss?" → Show Data Quality panel
   - "How do you know parachute deployed?" → Show alerts & phase change
   - "Can you prove your data is accurate?" → Show exported CSV

4. **Have Contingencies**
   - Print screenshots of a successful flight
   - Have backup data files
   - Know how to demonstrate offline

---

## 📞 Need Help?

If you encounter issues:

1. Check console output for error messages
2. Verify all dependencies are installed
3. Try running the simple flight_simulator.py first
4. Check that all files are in the same directory

**Files needed in same folder:**
- `cansat_gui_enhanced.py`
- `flight_simulator.py`
- `test_cansat_gui.py`

---

Good luck with your testing and competition! 🏆🛰️
