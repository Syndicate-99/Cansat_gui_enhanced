# 🚀 CanSat GUI - Quick Reference Card

## One-Line Test Command
```bash
python test_cansat_gui.py
```

---

## 3-Minute Test Checklist

### ✅ Startup (30 seconds)
- [ ] GUI opens without errors
- [ ] All graphs visible
- [ ] Mission phase indicator shows "Pre-Launch"

### ✅ Real-Time Tab (1 minute)
- [ ] Click "Start Mission"
- [ ] Watch altitude graph climb
- [ ] Mission phase changes: Pre-Launch → Ascent → Deployment → Descent → Landing
- [ ] Max altitude updates in stats panel
- [ ] Alerts appear in alerts panel

### ✅ Pre-Flight Tab (30 seconds)
- [ ] Check all checklist items
- [ ] Status turns green "READY FOR LAUNCH"

### ✅ Data Export (1 minute)
- [ ] Click "Export Data"
- [ ] Save CSV file
- [ ] Go to Analysis tab
- [ ] Click "Load Flight Data"
- [ ] Select your CSV
- [ ] Click "Generate Report"

---

## Mission Phases Timeline (Simulated)

```
0s     ⚪ PRE-LAUNCH    On launch pad
│
5s     🟢 ASCENT        Rising to altitude
│      ↗ Altitude: 0m → 1000m
│      ↗ Speed: 0 → 8 m/s
│
120s   🟡 DEPLOYMENT    Parachute opens!
│      ⚠ Alert: "Parachute deployed"
│      ↘ Speed drops quickly
│
125s   🟠 DESCENT       Falling with parachute
│      ↘ Altitude: 1000m → 0m
│      → Speed: ~5 m/s (steady)
│
240s   🔴 LANDING       On ground
       ● All movement stops
```

---

## Expected Values

### Pre-Launch (0-5s)
- Altitude: 0m
- Speed: 0 m/s
- Gyro: ~0 deg/s

### Ascent (5-120s)
- Altitude: 0 → 1000m
- Speed: 0 → 8 m/s
- Gyro: 5-25 deg/s (tumbling)

### Deployment (120-125s)
- Speed: 8 → 0 m/s (quick drop)
- Gyro: 40-80 deg/s (high rotation)
- ⚠ Watch for alert!

### Descent (125-240s)
- Altitude: 1000 → 0m
- Speed: ~5 m/s (steady)
- Gyro: 3-10 deg/s (gentle sway)

### Landing (240s+)
- Altitude: 0m
- Speed: 0 m/s
- Gyro: ~0 deg/s

---

## Key Panels to Watch

### 📊 Real-Time Tab
```
┌─────────────────┬─────────────────┐
│  Altitude Graph │  Mission Stats  │
│  [Rising line]  │  Max: 1000m     │
│                 │  Speed: 8 m/s   │
│  Speed Graph    │  Time: 125s     │
│  [Bell curve]   │                 │
│                 │  Data Quality   │
│  Accel Graph    │  Packets: 250   │
│  [Varying]      │  Loss: 0%       │
│                 │  Status: ●      │
│  Gyro Graph     │                 │
│  [3 lines]      │  🚨 Alerts      │
│                 │  [Messages...]  │
└─────────────────┴─────────────────┘
```

---

## Button Functions

### Real-Time Tab
- **▶ Start Mission** → Begins recording, starts timer
- **⏹ Stop Mission** → Stops recording
- **💾 Export Data** → Saves CSV file

### Pre-Flight Tab
- **Checkboxes** → Mark systems as ready
- **Status Indicator** → Red = Not Ready, Green = Ready

### Analysis Tab
- **📂 Load Flight Data** → Import CSV
- **📄 Generate Report** → Create mission summary

---

## Keyboard Shortcuts (Future Feature)
- `Ctrl+S` → Start Mission
- `Ctrl+E` → Export Data
- `Ctrl+Q` → Quit

---

## Data Quality Indicators

### Connection Status
- 🟢 **Green Dot** → Connected, receiving data
- 🔴 **Red Dot** → Disconnected, no data

### Packet Loss
- ✅ **0-2%** → Excellent
- ⚠️ **2-5%** → Good
- ❌ **>5%** → Poor (check connection)

---

## Alert Colors

- 🟢 **INFO** (Green) → Normal operations
  - "Mission started"
  - "Low altitude - Landing phase"

- 🟡 **WARNING** (Yellow) → Attention needed
  - "Approaching maximum altitude"

- 🔴 **CRITICAL** (Red) → Urgent
  - "Connection timeout"
  - "Invalid sensor reading"

---

## File Locations

### Input Files
- `cansat_gui_enhanced.py` → Main GUI
- `flight_simulator.py` → Test data generator
- `test_cansat_gui.py` → Test launcher

### Output Files
- `mission_data_YYYYMMDD_HHMMSS.csv` → Exported telemetry
- `cansat_test_data_YYYYMMDD_HHMMSS.csv` → Auto-saved data

---

## CSV Data Format

```csv
Time,Altitude,Temperature,Pressure,Humidity,Gyro_X,Gyro_Y,Gyro_Z,Accel_X,Accel_Y,Accel_Z,Latitude,Longitude
0.0,0.0,25.0,1013.0,50.0,0.1,0.1,0.1,0.0,0.0,9.8,13.3379,74.7461
1.0,0.0,25.0,1013.0,50.0,0.1,0.1,0.1,0.0,0.0,9.8,13.3379,74.7461
...
```

---

## Common Test Scenarios

### Scenario 1: Quick Demo (2 min)
```
1. python test_cansat_gui.py
2. Click "Start Mission"
3. Watch for 60 seconds
4. Point out phase changes
5. Click "Export Data"
```

### Scenario 2: Full Flight (5 min)
```
1. python test_cansat_gui.py
2. Click "Start Mission"
3. Wait for complete flight (250s)
4. Observe all 5 phases
5. Export and analyze data
```

### Scenario 3: Pre-Flight Check (1 min)
```
1. python test_cansat_gui.py
2. Go to "Pre-Flight" tab
3. Check all items
4. Verify green status
```

---

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| GUI won't start | `pip install PyQt5 pyqtgraph` |
| No data | Click "Start Mission" |
| Blank graphs | Wait 2 seconds for data |
| Can't export | Stop mission first |
| Import error | Check all .py files in same folder |

---

## Competition Day Checklist

### Before Launch
- [ ] Test GUI with simulator
- [ ] Verify all graphs work
- [ ] Test data export
- [ ] Take practice screenshots
- [ ] Prepare backup USB drive

### During Launch
- [ ] Start recording before liftoff
- [ ] Monitor mission phases
- [ ] Watch for alerts
- [ ] Note key events
- [ ] Take screenshots

### After Landing
- [ ] Stop recording
- [ ] Export data immediately
- [ ] Make backup copy
- [ ] Generate report
- [ ] Prepare presentation

---

## Quick Stats Summary

At end of simulation:
```
📊 MISSION SUMMARY
├─ Duration: ~250 seconds
├─ Max Altitude: ~1000m
├─ Max Speed: ~8 m/s
├─ Packets: ~500 received
├─ Loss Rate: 0%
└─ Phases: All completed ✅
```

---

## Important Numbers

- **Update Rate**: 2 Hz (every 0.5s)
- **Simulation Speed**: 2x real-time
- **Max Altitude**: 1000m (configurable)
- **Descent Rate**: 5 m/s with parachute
- **Total Flight Time**: 250 seconds

---

## Pro Tips

💡 **Tip 1**: Let simulation run completely at least once before competition  
💡 **Tip 2**: Export data every 30 seconds during real flight as backup  
💡 **Tip 3**: Keep CSV files organized by timestamp  
💡 **Tip 4**: Take screenshots at key moments (deployment, landing)  
💡 **Tip 5**: Practice your 60-second demo explanation  

---

## Emergency Backup Plan

If GUI fails during competition:
1. Have screenshots ready
2. Have backup CSV file
3. Manual data recording sheet
4. Know how to restart quickly
5. Have explanations prepared

---

**Print this card and keep it handy!** 📋

*Quick Reference v1.0 - Parikshit Student Satellite*
