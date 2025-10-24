# 🛰️ CanSat Ground Station GUI - Complete Package


# ***The graphs shown are only for demonstration purposes and have no real sensor values ***

## 📦 What's Included

1. **cansat_gui_enhanced.py** - Your improved GUI with competition features
2. **flight_simulator.py** - Realistic flight data generator for testing
3. **test_cansat_gui.py** - Easy test launcher
4. **TESTING_GUIDE.md** - Comprehensive testing instructions
5. **CANSAT_IMPROVEMENTS.md** - Additional features and tips

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install PyQt5 pyqtgraph numpy pandas
```

### Step 2: Run the Test
```bash
python test_cansat_gui.py
```

### Step 3: Explore!
- Watch the automatic flight simulation
- Click "Start Mission" to record data
- Try all three tabs: Real-Time, Pre-Flight, Analysis
- Export data and generate reports

---

## 📁 File Structure

```
your-folder/
├── cansat_gui_enhanced.py     # Main GUI application
├── flight_simulator.py         # Test data generator
├── test_cansat_gui.py          # Test launcher
├── TESTING_GUIDE.md            # How to test everything
└── CANSAT_IMPROVEMENTS.md      # More features to add
```

---

## 🎯 What Each File Does

### cansat_gui_enhanced.py
**Your main GUI with these features:**
- ✅ Mission phase tracking (Pre-Launch → Ascent → Deployment → Descent → Landing)
- ✅ Real-time graphs for altitude, speed, acceleration, gyroscope
- ✅ Mission statistics (max altitude, max speed, flight time)
- ✅ Data quality monitoring (packet loss, connection status)
- ✅ Alert system (color-coded warnings)
- ✅ Pre-flight checklist
- ✅ Data export to CSV
- ✅ Post-flight analysis tools

### flight_simulator.py
**Generates realistic test data:**
- Simulates complete 250-second flight
- Realistic ascent, deployment, descent, landing phases
- Adds sensor noise for realism
- Outputs data in correct format for GUI
- Can be used standalone or with GUI

### test_cansat_gui.py
**Easy launcher for testing:**
- Runs GUI with simulated data
- Shows welcome instructions
- Configures everything automatically
- Perfect for practice and demo

---

## 💻 Usage Examples

### For Testing (Before Launch Day)
```bash
# Test with simulated data
python test_cansat_gui.py

# Test the simulator alone
python flight_simulator.py
```

### For Real Flight (Launch Day)
```bash
# Edit cansat_gui_enhanced.py first:
# Replace the Communication class with your real serial code

python cansat_gui_enhanced.py
```

---

## 🔧 Customization

### Change Flight Parameters
Edit `flight_simulator.py`:
```python
self.max_altitude = 1000        # Change max altitude (meters)
self.deployment_time = 120      # Change when parachute opens (seconds)
self.landing_time = 240         # Change total flight time (seconds)
```

### Connect Real Hardware
Edit `cansat_gui_enhanced.py`, replace Communication class:
```python
import serial

class Communication:
    def __init__(self):
        self.ser = serial.Serial('COM3', 9600)  # Your port
    
    def getData(self):
        # Read from your CanSat
        line = self.ser.readline().decode('utf-8')
        # Parse your telemetry format
        return parsed_data
```

---

## 🎓 Testing Workflow

1. **First Time Setup** (5 minutes)
   ```bash
   pip install PyQt5 pyqtgraph numpy pandas
   python test_cansat_gui.py
   ```

2. **Daily Testing** (2 minutes)
   - Run simulation
   - Practice explaining features
   - Test data export

3. **Pre-Competition** (10 minutes)
   - Full simulation run
   - Export and verify CSV
   - Generate competition report
   - Take screenshots

4. **Competition Day**
   - Connect real hardware
   - Run pre-flight checklist
   - Monitor during flight
   - Export data immediately after

---

## 📊 Expected Simulation Results

After running the test, you should see:

**Mission Phases:**
- ⚪ Pre-Launch (0-5s) - Sitting on pad
- 🟢 Ascent (5-120s) - Rising to ~1000m
- 🟡 Deployment (120-125s) - Parachute opens
- 🟠 Descent (125-240s) - Falling at ~5m/s
- 🔴 Landing (240s+) - On ground

**Statistics:**
- Max Altitude: ~1000m
- Max Speed: ~8 m/s
- Flight Duration: ~250s
- Packets Received: ~500
- Packet Loss: 0%

---

## ❓ Troubleshooting

### GUI won't start
**Problem:** Import errors or missing modules

**Solution:**
```bash
pip install --upgrade PyQt5 pyqtgraph numpy pandas
```

### No data showing
**Problem:** Simulator not running

**Solution:**
- Use `test_cansat_gui.py` instead of running GUI directly
- Check console for error messages

### Graphs are blank
**Problem:** Data not updating

**Solution:**
- Click "Start Mission" button
- Wait 2-3 seconds for data to accumulate
- Check that simulator is generating data (print statements in console)

---

## 🏆 Competition Tips

### What Judges Look For:
1. ✅ **Professional appearance** - Clean, organized interface
2. ✅ **Real-time monitoring** - Live data updates
3. ✅ **Data quality** - Packet loss tracking
4. ✅ **Phase detection** - Automatic mission tracking
5. ✅ **Data logging** - Proof of recorded data
6. ✅ **Analysis tools** - Post-flight capabilities

### Your Demo Script (60 seconds):
```
"Our ground station features real-time telemetry visualization with 
automatic mission phase detection. You can see we're tracking altitude, 
speed, and orientation data with clear visual indicators for each 
flight phase.

The data quality panel shows we maintained excellent connection with 
only [X]% packet loss. Our pre-flight checklist ensures all systems 
are ready before launch.

After landing, we can export all data to CSV and generate comprehensive 
mission reports with key statistics including maximum altitude of [Y] 
meters and flight duration of [Z] seconds."
```

### Practice Points:
- Show the phase indicator changing colors
- Point out the mission statistics
- Demonstrate data export
- Show the alerts panel with events
- Generate and explain the report

---

## 📚 Documentation

- **Full Testing Guide**: See `TESTING_GUIDE.md`
- **More Features**: See `CANSAT_IMPROVEMENTS.md`
- **Code Comments**: Check the `.py` files for inline explanations

---

## 🆘 Need Help?

**Common Questions:**

**Q: Can I use this for my competition?**  
A: Yes! It's designed specifically for CanSat competitions.

**Q: How do I connect my real CanSat?**  
A: Edit the Communication class in `cansat_gui_enhanced.py` to use your serial connection.

**Q: What format should my telemetry be?**  
A: The simulator shows the expected format - modify to match your CanSat's output.

**Q: Can I add more features?**  
A: Absolutely! Check `CANSAT_IMPROVEMENTS.md` for ideas.

---

## 📈 Next Steps

1. ✅ Run the test simulation (you're here!)
2. ⬜ Study the features and practice demo
3. ⬜ Customize for your CanSat's data format
4. ⬜ Test with real hardware (if available)
5. ⬜ Prepare backup screenshots
6. ⬜ Practice your presentation
7. ⬜ Win the competition! 🏆

---

## 🌟 Features Showcase

### Real-Time Monitoring
![Monitoring](Shows live graphs updating)

### Mission Phases
![Phases](Color-coded progress indicator)

### Data Quality
![Quality](Packet statistics and connection status)

### Pre-Flight Checklist
![Checklist](System readiness verification)

### Mission Statistics
![Stats](LCD displays for key metrics)

### Alert System
![Alerts](Color-coded notifications)

---

**Good luck with your CanSat competition!** 🚀🛰️

*Made for Parikshit Student Satellite Team*
