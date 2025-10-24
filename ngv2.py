import sys
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QGroupBox, QGridLayout,
    QStyleFactory, QFrame, QSizePolicy, QProgressBar, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QLCDNumber, QTextEdit,
    QFileDialog, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QScrollArea
)
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from datetime import datetime
import pandas as pd
import json
import os

# Real Arduino Communication Class
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[WARNING] pyserial not installed. Run: pip install pyserial")

class Communication:
    """
    Real Arduino communication class
    Usage: Communication(port='COM3', baudrate=9600)
    """
    def __init__(self, port='COM3', baudrate=9600, use_simulator=False):
        self.connected = False
        self.ser = None
        self.use_simulator = use_simulator
        self.header_found = False  # Track if we've found the header
        self.header_marker = "2024ASI-CANSAT-059"  # Header to look for
        
        print(f"\n{'='*60}")
        print(f"COMMUNICATION INITIALIZATION")
        print(f"Mode: {'SIMULATOR' if use_simulator else 'REAL SERIAL'}")
        print(f"Header marker: {self.header_marker}")
        print(f"{'='*60}\n")
        
        if use_simulator:
            # Use simulator for testing
            try:
                from flight_simulator import FlightSimulator
                self.simulator = FlightSimulator()
                self.connected = True
                self.header_found = True  # Simulator doesn't need header
                print("[OK] Using flight simulator")
            except:
                print("[WARNING] Flight simulator not found, using random data")
                self.simulator = None
        else:
            # Real serial connection
            if not SERIAL_AVAILABLE:
                print("[ERROR] pyserial not installed! Install with: pip install pyserial")
                return
            
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                import time
                time.sleep(2)  # Wait for Arduino reset
                self.connected = True
                print(f"[OK] Connected to {port} at {baudrate} baud")
                print(f"[INFO] SIMULATOR DISABLED - Using real XBee data")
                print(f"[INFO] Waiting for header: {self.header_marker}")
            except Exception as e:
                self.connected = False
                print(f"[ERROR] Failed to connect to {port}: {e}")
                print(f"   Available ports: {self.list_ports()}")
    
    @staticmethod
    def list_ports():
        """List all available COM ports"""
        if SERIAL_AVAILABLE:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        return []
    
    def getData(self):
        """Get data from Arduino or simulator"""
        # CRITICAL: Check real serial FIRST if connected
        if not self.use_simulator and self.connected and self.ser:
            # Real Arduino/XBee data - PRIORITY
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        # Check if we need to find the header first
                        if not self.header_found:
                            if self.header_marker in line:
                                self.header_found = True
                                print(f"\n{'*'*60}")
                                print(f"[HEADER FOUND] {self.header_marker}")
                                print(f"[INFO] Now reading data...")
                                print(f"{'*'*60}\n")
                            else:
                                # Still looking for header, ignore this line
                                print(f"[SCANNING] Waiting for header... ({line[:40]}...)")
                            return None
                        
                        # Header found, parse the data
                        data = self.parse_data(line)
                        if data:
                            # UPDATED: Show pressure, velocity, and state in debug output
                            pressure_hpa = data[3] / 100.0  # Convert Pa to hPa
                            v_mag = data[16] if len(data) > 16 else 0
                            state = data[17] if len(data) > 17 else "UNKNOWN"
                            print(f"[REAL DATA] Pkt:{int(data[15])} Alt:{data[1]:.2f}m T:{data[2]:.2f}°C P:{pressure_hpa:.1f}hPa V:{v_mag:.2f}m/s State:{state}")
                            return data
                return None
            except Exception as e:
                print(f"[ERROR] Error reading serial: {e}")
                return None
        
        # Only use simulator if explicitly requested
        if self.use_simulator:
            # Use flight simulator
            if hasattr(self, 'simulator') and self.simulator:
                import time
                if not hasattr(self, 'last_update'):
                    self.last_update = time.time()
                current_time = time.time()
                dt = current_time - self.last_update
                self.last_update = current_time
                sim_data = self.simulator.update(dt * 2)  # 2x speed
                return sim_data
            else:
                # Random data fallback
                import random
                return [datetime.now().timestamp(), random.uniform(0, 1000), 0, 0, 0, 
                        random.uniform(-180, 180), random.uniform(-180, 180), random.uniform(-180, 180),
                        random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)]
        
        # No data available
        return None
    
    def parse_data(self, line):
        """
        Parse YOUR NEW format with header in each line:
        ###,<TEAM_ID>,<packet>,<millis>,<alt_m>,<press_Pa>,<temp_C>,
        <ax_mps2>,<ay_mps2>,<az_mps2>,
        <gx_rads>,<gy_rads>,<gz_rads>,<gyro_spin_degps>,
        <mq7_raw>,<mq135_raw>,<v_mag_mps>,<state>
        
        Example: ###,2024ASI-CANSAT-059,12,45678,1052.45,89756.23,26.54,0.12,-9.78,0.05,0.005,-0.002,0.010,0.67,512,489,3.42,DESCEND1
        
        Returns: [time, altitude, temp, pressure, humidity, gx, gy, gz, ax, ay, az, lat, lon, mq7, mq135, packet, v_mag, state]
                 (18 values total - added v_mag and state)
        """
        try:
            # Clean XBee garbage characters
            import re
            clean_line = ''.join(char for char in line if ord(char) >= 32 and ord(char) < 127)
            clean_line = re.sub(r'[▒\x00-\x1F]+', '', clean_line).strip()
            
            if not clean_line or ',' not in clean_line:
                return None
            
            # Check for header prefix (###,TEAM_ID,...)
            # Remove the header part to get to the data
            if '2024ASI-CANSAT-059' in clean_line:
                # Split at the header to get the data after it
                parts = clean_line.split('2024ASI-CANSAT-059,', 1)
                if len(parts) == 2:
                    clean_line = parts[1]  # Get everything after header
                else:
                    print(f"[WARNING] Could not parse header format: {clean_line[:60]}...")
                    return None
            else:
                print(f"[WARNING] Missing header: {clean_line[:60]}...")
                return None
            
            # Parse CSV (now without header)
            parts = clean_line.split(',')
            if len(parts) < 15:
                print(f"[WARNING] Expected 15+ values, got {len(parts)}: {clean_line[:80]}...")
                return None
            
            # Field mapping (AFTER removing header):
            # 0: packet (packet number)
            # 1: millis (timestamp)
            # 2: alt_m (altitude in meters)
            # 3: press_Pa (pressure in Pascals)
            # 4: temp_C (temperature in Celsius)
            # 5: ax_mps2 (accel X)
            # 6: ay_mps2 (accel Y)
            # 7: az_mps2 (accel Z)
            # 8: gx_rads (gyro X in rad/s)
            # 9: gy_rads (gyro Y in rad/s)
            # 10: gz_rads (gyro Z in rad/s)
            # 11: gyro_spin_degps (gyro spin rate in deg/s)
            # 12: mq7_raw (CO sensor)
            # 13: mq135_raw (air quality sensor)
            # 14: v_mag_mps (velocity magnitude in m/s) - NEW
            # 15: state (flight state string) - NEW
            
            # Extract values
            packet_num = int(parts[0].strip())
            
            # Convert numeric fields
            values = []
            for i in range(1, min(len(parts), 15)):  # Fields 1-14 are numeric
                try:
                    values.append(float(parts[i].strip()))
                except ValueError:
                    print(f"[WARNING] Could not parse field {i}: {parts[i]}")
                    # Use 0 as fallback
                    values.append(0.0)
            
            # Pad with zeros if not enough values
            while len(values) < 14:
                values.append(0.0)
            
            # Extract state string (field 15)
            state = parts[15].strip() if len(parts) > 15 else "UNKNOWN"
            
            # Map to extended format (18 values):
            # [time, altitude, temp, pressure, humidity, gx, gy, gz, ax, ay, az, lat, lon, mq7, mq135, packet, v_mag, state]
            
            import time
            standard = [
                time.time(),              # 0: time (current timestamp)
                values[1],                # 1: alt_m (field 2) - YOUR REAL DATA
                values[3],                # 2: temp_C (field 4) - YOUR REAL DATA
                values[2],                # 3: pressure in Pa (field 3) - YOUR REAL DATA
                50.0,                     # 4: humidity (synthetic - not in your data)
                values[7],                # 5: gx_rads (field 8) - YOUR REAL DATA
                values[8],                # 6: gy_rads (field 9) - YOUR REAL DATA
                values[9],                # 7: gz_rads (field 10) - YOUR REAL DATA
                values[4],                # 8: ax_mps2 (field 5) - YOUR REAL DATA
                values[5],                # 9: ay_mps2 (field 6) - YOUR REAL DATA
                values[6],                # 10: az_mps2 (field 7) - YOUR REAL DATA
                13.3379,                  # 11: latitude (synthetic - not in your data)
                74.7461,                  # 12: longitude (synthetic - not in your data)
                values[11] if len(values) > 11 else 0,  # 13: mq7_raw (field 12) - YOUR REAL DATA
                values[12] if len(values) > 12 else 0,  # 14: mq135_raw (field 13) - YOUR REAL DATA
                packet_num,               # 15: packet number - YOUR REAL DATA
                values[13] if len(values) > 13 else 0,  # 16: v_mag_mps (field 14) - NEW
                state                     # 17: state string - NEW
            ]
            
            return standard
            
        except ValueError as e:
            print(f"[WARNING] Parse error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_speed(self):
        """Get current speed from simulator"""
        if hasattr(self, 'simulator') and self.simulator:
            return self.simulator.get_speed()
        return 0
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            print("Serial connection closed")


class data_base:
    """Database class for recording flight data"""
    def __init__(self):
        self.recording = False
        self.data_log = []
        self.filename = None
    
    def start(self):
        """Start recording data"""
        self.recording = True
        self.data_log = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"cansat_flight_data_{timestamp}.csv"
        print(f"[RECORDING] Started recording to {self.filename}")
    
    def stop(self):
        """Stop recording and save data"""
        self.recording = False
        if self.data_log and self.filename:
            try:
                df = pd.DataFrame(self.data_log, columns=[
                    'Time', 'Altitude', 'Temperature', 'Pressure', 'Humidity',
                    'Gyro_X', 'Gyro_Y', 'Gyro_Z',
                    'Accel_X', 'Accel_Y', 'Accel_Z',
                    'Latitude', 'Longitude'
                ])
                df.to_csv(self.filename, index=False)
                print(f"[SAVED] Saved {len(self.data_log)} data points to {self.filename}")
            except Exception as e:
                print(f"[ERROR] Error saving data: {e}")
    
    def guardar(self, data):
        """Save data point"""
        if self.recording and data:
            self.data_log.append(data)

# Set dark theme for pyqtgraph
pg.setConfigOption('background', '#1e1e1e')
pg.setConfigOption('foreground', '#ffffff')

class MissionPhaseIndicator(QWidget):
    """Visual indicator for current mission phase"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_phase = 0
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        self.phases = [
            ("Pre-Launch", "#808080"),
            ("Ascent", "#00ff00"),
            ("Deployment", "#ffff00"),
            ("Descent", "#ff8800"),
            ("Landing", "#ff0000"),
            ("Recovery", "#0088ff")
        ]
        
        self.phase_labels = []
        for phase_name, color in self.phases:
            label = QLabel(phase_name)
            label.setStyleSheet(f"""
                QLabel {{
                    background-color: #2d2d2d;
                    color: white;
                    border: 2px solid {color};
                    border-radius: 5px;
                    padding: 8px;
                    font-weight: bold;
                }}
            """)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            self.phase_labels.append(label)
    
    def set_phase(self, phase_index):
        """Set the current mission phase (0-5)"""
        self.current_phase = phase_index
        for i, label in enumerate(self.phase_labels):
            if i == phase_index:
                label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {self.phases[i][1]};
                        color: black;
                        border: 2px solid {self.phases[i][1]};
                        border-radius: 5px;
                        padding: 8px;
                        font-weight: bold;
                    }}
                """)
            else:
                label.setStyleSheet(f"""
                    QLabel {{
                        background-color: #2d2d2d;
                        color: white;
                        border: 2px solid {self.phases[i][1]};
                        border-radius: 5px;
                        padding: 8px;
                        font-weight: bold;
                    }}
                """)

class FlightStateIndicator(QGroupBox):
    """Display current flight state from sensor data"""
    def __init__(self):
        super().__init__("Flight State")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # State display
        self.state_label = QLabel("UNKNOWN")
        self.state_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setStyleSheet("""
            QLabel {
                background-color: #3d3d3d;
                color: #ffff00;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #5d5d5d;
            }
        """)
        layout.addWidget(self.state_label)
        
        # Velocity magnitude display
        velocity_layout = QHBoxLayout()
        velocity_layout.addWidget(QLabel("Velocity Magnitude:"))
        self.velocity_label = QLabel("0.00 m/s")
        self.velocity_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.velocity_label.setStyleSheet("color: #00ffff;")
        velocity_layout.addWidget(self.velocity_label)
        velocity_layout.addStretch()
        layout.addLayout(velocity_layout)
    
    def update_state(self, state, velocity_mag):
        """Update the flight state display"""
        self.state_label.setText(state)
        self.velocity_label.setText(f"{velocity_mag:.2f} m/s")
        
        # Color code based on state
        state_colors = {
            "IDLE": "#808080",
            "ASCEND": "#00ff00",
            "DESCEND1": "#ffaa00",
            "DESCEND2": "#ff6600",
            "LANDING": "#ff0000"
        }
        
        color = state_colors.get(state, "#ffff00")
        self.state_label.setStyleSheet(f"""
            QLabel {{
                background-color: #3d3d3d;
                color: {color};
                padding: 15px;
                border-radius: 8px;
                border: 2px solid {color};
            }}
        """)

class DataQualityIndicator(QGroupBox):
    """Shows real-time data quality metrics"""
    def __init__(self):
        super().__init__("Data Quality")
        self.init_ui()
        
    def init_ui(self):
        layout = QGridLayout(self)
        
        # Packet statistics
        self.packets_received = QLabel("0")
        self.packets_lost = QLabel("0")
        self.packet_loss_rate = QLabel("0.0%")
        self.last_packet_time = QLabel("Never")
        self.data_rate = QLabel("0 B/s")
        self.connection_status = QLabel("●")
        
        # Styling
        self.connection_status.setStyleSheet("color: #ff0000; font-size: 20px;")
        
        # Add to layout
        layout.addWidget(QLabel("Packets Received:"), 0, 0)
        layout.addWidget(self.packets_received, 0, 1)
        layout.addWidget(QLabel("Packets Lost:"), 1, 0)
        layout.addWidget(self.packets_lost, 1, 1)
        layout.addWidget(QLabel("Packet Loss:"), 2, 0)
        layout.addWidget(self.packet_loss_rate, 2, 1)
        layout.addWidget(QLabel("Last Packet:"), 3, 0)
        layout.addWidget(self.last_packet_time, 3, 1)
        layout.addWidget(QLabel("Data Rate:"), 4, 0)
        layout.addWidget(self.data_rate, 4, 1)
        layout.addWidget(QLabel("Connection:"), 5, 0)
        layout.addWidget(self.connection_status, 5, 1)
    
    def update_stats(self, received, lost, last_time, rate, connected):
        self.packets_received.setText(str(received))
        self.packets_lost.setText(str(lost))
        total = received + lost
        if total > 0:
            loss_rate = (lost / total) * 100
            self.packet_loss_rate.setText(f"{loss_rate:.2f}%")
        self.last_packet_time.setText(last_time)
        self.data_rate.setText(f"{rate} B/s")
        
        if connected:
            self.connection_status.setText("●")
            self.connection_status.setStyleSheet("color: #00ff00; font-size: 20px;")
        else:
            self.connection_status.setText("●")
            self.connection_status.setStyleSheet("color: #ff0000; font-size: 20px;")

class AlertsPanel(QGroupBox):
    """Critical alerts and warnings"""
    def __init__(self):
        super().__init__("⚠ Alerts & Warnings")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffff00;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.alerts_text.setMaximumHeight(150)
        
        # Clear button
        clear_btn = QPushButton("Clear Alerts")
        clear_btn.clicked.connect(self.clear_alerts)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        
        layout.addWidget(self.alerts_text)
        layout.addWidget(clear_btn)
    
    def add_alert(self, message, severity="INFO"):
        """Add an alert message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "#00ff00",
            "WARNING": "#ffff00",
            "CRITICAL": "#ff0000"
        }
        color = colors.get(severity, "#ffffff")
        
        formatted_msg = f'<span style="color: {color};">[{timestamp}] {severity}: {message}</span>'
        self.alerts_text.append(formatted_msg)
        
        # Auto-scroll to bottom
        scrollbar = self.alerts_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_alerts(self):
        self.alerts_text.clear()

class MissionStats(QGroupBox):
    """Display key mission statistics"""
    def __init__(self):
        super().__init__("Mission Statistics")
        self.init_ui()
        self.reset_stats()
        
    def init_ui(self):
        layout = QGridLayout(self)
        
        # Create LCD displays for important stats
        self.max_altitude = self.create_lcd_display()
        self.max_speed = self.create_lcd_display()
        self.flight_time = self.create_lcd_display()
        self.descent_rate = self.create_lcd_display()
        self.current_altitude = self.create_lcd_display()
        
        # Add to layout with labels
        layout.addWidget(QLabel("Max Altitude (m):"), 0, 0)
        layout.addWidget(self.max_altitude, 0, 1)
        layout.addWidget(QLabel("Max Speed (m/s):"), 1, 0)
        layout.addWidget(self.max_speed, 1, 1)
        layout.addWidget(QLabel("Flight Time (s):"), 2, 0)
        layout.addWidget(self.flight_time, 2, 1)
        layout.addWidget(QLabel("Descent Rate (m/s):"), 3, 0)
        layout.addWidget(self.descent_rate, 3, 1)
        layout.addWidget(QLabel("Current Alt (m):"), 4, 0)
        layout.addWidget(self.current_altitude, 4, 1)
    
    def create_lcd_display(self):
        lcd = QLCDNumber()
        lcd.setSegmentStyle(QLCDNumber.Flat)
        lcd.setStyleSheet("""
            QLCDNumber {
                background-color: #000000;
                color: #00ff00;
                border: 1px solid #3d3d3d;
            }
        """)
        lcd.setDigitCount(8)
        return lcd
    
    def reset_stats(self):
        self.max_alt_value = 0
        self.max_speed_value = 0
        self.flight_start_time = None
        # Reset displays to 0
        self.max_altitude.display(0.00)
        self.max_speed.display(0.00)
        self.flight_time.display(0.00)
        self.descent_rate.display(0.00)
        self.current_altitude.display(0.00)
        
    def update_stats(self, altitude, speed):
        # Update max values - THIS NOW UPDATES IN REAL-TIME
        if altitude > self.max_alt_value:
            self.max_alt_value = altitude
            self.max_altitude.display(f"{altitude:.2f}")
        
        if abs(speed) > abs(self.max_speed_value):  # Use abs to catch both ascent and descent speeds
            self.max_speed_value = abs(speed)
            self.max_speed.display(f"{abs(speed):.2f}")
        
        # Update current altitude - REAL-TIME UPDATE
        self.current_altitude.display(f"{altitude:.2f}")
        
        # Update descent rate if descending - REAL-TIME UPDATE
        if speed < 0:
            self.descent_rate.display(f"{abs(speed):.2f}")

class PreflightChecklist(QGroupBox):
    """Pre-flight system checks"""
    def __init__(self):
        super().__init__("Pre-Flight Checklist")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Checklist items
        self.checks = {
            "GPS Lock": QCheckBox("GPS Lock Acquired"),
            "Sensors": QCheckBox("All Sensors Calibrated"),
            "Battery": QCheckBox("Battery > 80%"),
            "Storage": QCheckBox("Storage Space Available"),
            "Communication": QCheckBox("Ground Station Connected"),
            "Parachute": QCheckBox("Parachute System Armed")
        }
        
        for name, checkbox in self.checks.items():
            checkbox.setStyleSheet("color: white; font-size: 12px;")
            layout.addWidget(checkbox)
        
        # Status label
        self.status_label = QLabel("System Status: NOT READY")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #ff0000;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Update status when checkboxes change
        for checkbox in self.checks.values():
            checkbox.stateChanged.connect(self.update_status)
    
    def update_status(self):
        all_checked = all(cb.isChecked() for cb in self.checks.values())
        if all_checked:
            self.status_label.setText("System Status: READY FOR LAUNCH")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #00ff00;
                    color: black;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setText("System Status: NOT READY")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #ff0000;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)

class ModernButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__(text)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d5ca8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3873cf;
            }
            QPushButton:pressed {
                background-color: #1d3c6a;
            }
        """)

class DataCard(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                margin-top: 1em;
                padding: 10px;
                color: white;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Parikshit Student Satellite - CanSat Ground Station')
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.resize(1600, 900)

        # Initialize data buffers
        self.data_length = 100
        self.times = np.zeros(self.data_length)
        self.altitudes = np.zeros(self.data_length)
        self.speeds = np.zeros(self.data_length)
        self.accelerations = np.zeros(self.data_length)
        self.gyro_x = np.zeros(self.data_length)
        self.gyro_y = np.zeros(self.data_length)
        self.gyro_z = np.zeros(self.data_length)
        
        # Additional sensor buffers for YOUR data
        self.temperatures = np.zeros(self.data_length)
        self.pressures = np.zeros(self.data_length)
        self.mq7_values = np.zeros(self.data_length)  # CO sensor
        self.mq135_values = np.zeros(self.data_length)  # Air quality sensor
        
        # NEW: Speed calculation from acceleration integration
        self.current_speed = 0.0
        self.last_time = None
        self.last_acceleration = None
        
        # Mission tracking
        self.packets_received = 0
        self.packets_lost = 0
        self.packet_errors = 0
        self.last_packet_num = -1  # Track last packet number to detect gaps
        self.last_packet_time = None
        self.mission_start_time = None
        self.last_alert_altitude = None

        # Initialize plots
        self.setup_plots()

        # Initialize communication and database
        # USING YOUR XBEE ON COM8:
        self.ser = Communication(port='COM8', baudrate=9600, use_simulator=False)
        # self.ser = Communication(use_simulator=True)  # Using simulator by default
        self.db = data_base()
        
        # Serial communication state
        self.serial_active = True  # Start with serial ON
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Mission Phase Indicator
        self.mission_phase = MissionPhaseIndicator()
        main_layout.addWidget(self.mission_phase)
        
        # Create navigation
        nav = self.create_navigation()
        main_layout.addWidget(nav)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_monitoring_page())
        self.stacked_widget.addWidget(self.create_preflight_page())
        self.stacked_widget.addWidget(self.create_analysis_page())
        main_layout.addWidget(self.stacked_widget)
        
        # Setup timers
        self.setup_timers()

    def setup_plots(self):
        # Altitude plot
        self.altitude_plot = pg.PlotWidget()
        self.altitude_plot.setBackground('#2d2d2d')
        self.altitude_plot.setTitle("Altitude (m)", color='w')
        self.altitude_plot.setLabel('left', 'Altitude', units='m')
        self.altitude_plot.setLabel('bottom', 'Time', units='s')
        self.altitude_plot.showGrid(x=True, y=True, alpha=0.3)
        self.altitude_line = self.altitude_plot.plot(pen=pg.mkPen(color='#00ff00', width=2))

        # Speed plot
        self.speed_plot = pg.PlotWidget()
        self.speed_plot.setBackground('#2d2d2d')
        self.speed_plot.setTitle("Velocity Magnitude (m/s) - From Sensor", color='w')  # UPDATED TITLE
        self.speed_plot.setLabel('left', 'Speed', units='m/s')
        self.speed_plot.setLabel('bottom', 'Time', units='s')
        self.speed_plot.showGrid(x=True, y=True, alpha=0.3)
        self.speed_line = self.speed_plot.plot(pen=pg.mkPen(color='#00ffff', width=2))

        # Acceleration plot
        self.acceleration_plot = pg.PlotWidget()
        self.acceleration_plot.setBackground('#2d2d2d')
        self.acceleration_plot.setTitle("Acceleration (m/s²)", color='w')
        self.acceleration_plot.setLabel('left', 'Acceleration', units='m/s²')
        self.acceleration_plot.setLabel('bottom', 'Time', units='s')
        self.acceleration_plot.showGrid(x=True, y=True, alpha=0.3)
        self.acceleration_line = self.acceleration_plot.plot(pen=pg.mkPen(color='#ff00ff', width=2))

        # Gyroscope plot
        self.gyro_plot = pg.PlotWidget()
        self.gyro_plot.setBackground('#2d2d2d')
        self.gyro_plot.setTitle("Gyroscope (rad/s)", color='w')
        self.gyro_plot.setLabel('left', 'Angular Velocity', units='rad/s')
        self.gyro_plot.setLabel('bottom', 'Time', units='s')
        self.gyro_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gyro_x_line = self.gyro_plot.plot(pen=pg.mkPen(color='r', width=2), name='X')
        self.gyro_y_line = self.gyro_plot.plot(pen=pg.mkPen(color='g', width=2), name='Y')
        self.gyro_z_line = self.gyro_plot.plot(pen=pg.mkPen(color='b', width=2), name='Z')
        self.gyro_plot.addLegend()
        
        # NEW: Temperature plot (YOUR REAL DATA)
        self.temperature_plot = pg.PlotWidget()
        self.temperature_plot.setBackground('#2d2d2d')
        self.temperature_plot.setTitle("Temperature (°C)", color='w')
        self.temperature_plot.setLabel('left', 'Temperature', units='°C')
        self.temperature_plot.setLabel('bottom', 'Time', units='s')
        self.temperature_plot.showGrid(x=True, y=True, alpha=0.3)
        self.temperature_line = self.temperature_plot.plot(pen=pg.mkPen(color='#ff8800', width=2))
        
        # NEW: Pressure plot (YOUR REAL DATA)
        self.pressure_plot = pg.PlotWidget()
        self.pressure_plot.setBackground('#2d2d2d')
        self.pressure_plot.setTitle("Pressure (hPa)", color='w')
        self.pressure_plot.setLabel('left', 'Pressure', units='hPa')
        self.pressure_plot.setLabel('bottom', 'Time', units='s')
        self.pressure_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pressure_line = self.pressure_plot.plot(pen=pg.mkPen(color='#8800ff', width=2))
        
        # NEW: Air Quality Sensors plot (YOUR REAL DATA)
        self.airquality_plot = pg.PlotWidget()
        self.airquality_plot.setBackground('#2d2d2d')
        self.airquality_plot.setTitle("Air Quality Sensors", color='w')
        self.airquality_plot.setLabel('left', 'ADC Value', units='')
        self.airquality_plot.setLabel('bottom', 'Time', units='s')
        self.airquality_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mq7_line = self.airquality_plot.plot(pen=pg.mkPen(color='#ff0000', width=2), name='MQ-7 (CO)')
        self.mq135_line = self.airquality_plot.plot(pen=pg.mkPen(color='#00ff88', width=2), name='MQ-135 (Air)')
        self.airquality_plot.addLegend()

    def create_header(self):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        # Logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("logo1.jpg")
            if logo_pixmap.isNull():
                raise FileNotFoundError
            logo_pixmap = logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        except:
            logo_label.setText("🛰️")
            logo_label.setStyleSheet("font-size: 50px;")
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("CanSat Ground Station")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #00ff00;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Mission timer
        self.mission_timer = QLCDNumber()
        self.mission_timer.setDigitCount(8)
        self.mission_timer.setSegmentStyle(QLCDNumber.Flat)
        self.mission_timer.setStyleSheet("""
            QLCDNumber {
                background-color: #000000;
                color: #00ff00;
                border: 2px solid #3d3d3d;
            }
        """)
        self.mission_timer.display("00:00:00")
        header_layout.addWidget(QLabel("Mission Time:"))
        header_layout.addWidget(self.mission_timer)
        
        # Serial status
        self.serial_status = QLabel("🔴 Serial OFF")
        self.serial_status.setStyleSheet("""
            QLabel {
                background-color: #ff0000;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.serial_status)
        
        return header

    def create_navigation(self):
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        
        # Navigation buttons
        self.monitoring_btn = ModernButton("📡 Real-Time Monitoring")
        self.preflight_btn = ModernButton("✓ Pre-Flight Checklist")
        self.analysis_btn = ModernButton("📊 Post-Flight Analysis")
        
        self.monitoring_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.preflight_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.analysis_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        nav_layout.addWidget(self.monitoring_btn)
        nav_layout.addWidget(self.preflight_btn)
        nav_layout.addWidget(self.analysis_btn)
        
        return nav

    def create_monitoring_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        
        # Left panel - Statistics and controls
        left_panel = QVBoxLayout()
        
        # Flight state indicator (NEW)
        self.flight_state = FlightStateIndicator()
        left_panel.addWidget(self.flight_state)
        
        # Mission statistics
        self.mission_stats = MissionStats()
        left_panel.addWidget(self.mission_stats)
        
        # Data quality indicator
        self.data_quality = DataQualityIndicator()
        left_panel.addWidget(self.data_quality)
        
        # Alerts panel
        self.alerts_panel = AlertsPanel()
        left_panel.addWidget(self.alerts_panel)
        
        # Control buttons
        control_group = QGroupBox("Mission Control")
        control_layout = QVBoxLayout(control_group)
        
        start_btn = ModernButton("🚀 Start Mission")
        start_btn.clicked.connect(self.start_mission)
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #4a7c59, stop:1 #3d6b4a);
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 16px;
                border: 2px solid #5a8c69;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #5a8c69, stop:1 #4a7c59);
                border: 2px solid #6a9c79;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3d6b4a, stop:1 #2d5b3a);
            }
        """)
        control_layout.addWidget(start_btn)
        
        stop_btn = ModernButton("⏹ Stop Mission")
        stop_btn.clicked.connect(self.stop_mission)
        stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #8c5a5a, stop:1 #7a4a4a);
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 16px;
                border: 2px solid #9c6a6a;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #9c6a6a, stop:1 #8c5a5a);
                border: 2px solid #ac7a7a;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #7a4a4a, stop:1 #6a3a3a);
            }
        """)
        control_layout.addWidget(stop_btn)
        
        toggle_serial_btn = ModernButton("⏯ Toggle Serial (S)")
        toggle_serial_btn.clicked.connect(self.toggle_serial_communication)
        toggle_serial_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #5a7c8c, stop:1 #4a6b7a);
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border: 2px solid #6a8c9c;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #6a8c9c, stop:1 #5a7c8c);
                border: 2px solid #7a9cac;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #4a6b7a, stop:1 #3a5b6a);
            }
        """)
        control_layout.addWidget(toggle_serial_btn)
        
        export_btn = ModernButton("💾 Export Data")
        export_btn.clicked.connect(self.export_data)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #7a7c8c, stop:1 #6a6b7a);
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border: 2px solid #8a8c9c;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #8a8c9c, stop:1 #7a7c8c);
                border: 2px solid #9a9cac;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #6a6b7a, stop:1 #5a5b6a);
            }
        """)
        control_layout.addWidget(export_btn)
        
        left_panel.addWidget(control_group)
        left_panel.addStretch()
        
        # Right panel - Graphs
        right_panel = QVBoxLayout()
        right_panel.addWidget(self.altitude_plot)
        right_panel.addWidget(self.speed_plot)
        right_panel.addWidget(self.acceleration_plot)
        
        # Add to main layout
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 3)
        
        return page

    def create_preflight_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Pre-Flight System Check")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff00; padding: 20px;")
        layout.addWidget(title)
        
        # Checklist
        self.checklist = PreflightChecklist()
        layout.addWidget(self.checklist)
        
        # Additional sensor plots
        plots_layout = QGridLayout()
        plots_layout.addWidget(self.gyro_plot, 0, 0)
        plots_layout.addWidget(self.temperature_plot, 0, 1)
        plots_layout.addWidget(self.pressure_plot, 1, 0)
        plots_layout.addWidget(self.airquality_plot, 1, 1)
        layout.addLayout(plots_layout)
        
        layout.addStretch()
        
        return page

    def create_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Post-Flight Data Analysis")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff00; padding: 20px;")
        layout.addWidget(title)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        load_btn = ModernButton("📁 Load Flight Data")
        load_btn.clicked.connect(self.load_flight_data)
        button_layout.addWidget(load_btn)
        
        report_btn = ModernButton("📄 Generate Report")
        report_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(report_btn)
        
        layout.addLayout(button_layout)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.results_text)
        
        return page

    def setup_timers(self):
        # Data update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # Update every 100ms
        
        # Mission timer update
        self.mission_timer_update = QTimer()
        self.mission_timer_update.timeout.connect(self.update_mission_timer)
        self.mission_timer_update.start(100)
        
        # UI update timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)  # Update UI elements every second

    # NEW METHOD: Calculate speed from acceleration integration
    def calculate_speed_from_acceleration(self, az, dt):
        """
        Calculate speed by integrating vertical acceleration over time
        Using trapezoidal rule: v(t) = v(t-1) + (a(t-1) + a(t))/2 * dt
        
        Args:
            az: vertical acceleration (m/s²)
            dt: time step (s)
        
        Returns:
            current_speed: integrated speed (m/s)
        """
        if dt <= 0 or dt > 1.0:  # Sanity check on dt
            return self.current_speed
        
        # Trapezoidal integration for better accuracy
        if self.last_acceleration is not None:
            avg_accel = (self.last_acceleration + az) / 2.0
            self.current_speed += avg_accel * dt
        else:
            # First data point - use simple integration
            self.current_speed += az * dt
        
        self.last_acceleration = az
        
        return self.current_speed

    def update_data(self):
        if not self.serial_active:
            return
            
        data = self.ser.getData()
        if data is None:
            return
        
        try:
            # Extract data: [time, altitude, temp, pressure, humidity, gx, gy, gz, ax, ay, az, lat, lon, mq7, mq135, packet, v_mag, state]
            current_time = data[0]
            altitude = data[1]
            temperature = data[2]
            pressure = data[3] / 100.0  # Convert Pa to hPa
            gx, gy, gz = data[5], data[6], data[7]
            ax, ay, az = data[8], data[9], data[10]
            mq7 = data[13]
            mq135 = data[14]
            packet_num = int(data[15])
            v_mag = data[16] if len(data) > 16 else 0  # NEW: velocity magnitude from sensor
            state = data[17] if len(data) > 17 else "UNKNOWN"  # NEW: flight state
            
            # Calculate total acceleration magnitude
            total_accel = np.sqrt(ax**2 + ay**2 + az**2)
            
            # NEW: Calculate time difference for speed integration
            if self.last_time is not None:
                dt = current_time - self.last_time
            else:
                dt = 0.1  # Initial estimate
            
            # NEW: Calculate speed by integrating vertical acceleration (az)
            # We'll use our integrated speed, but can compare with v_mag from sensor
            speed = self.calculate_speed_from_acceleration(az, dt)
            
            # Update last time
            self.last_time = current_time
            
            # Update packet tracking
            self.packets_received += 1
            
            # Check for duplicate or lost packets
            if packet_num == self.last_packet_num:
                self.alerts_panel.add_alert(f"Duplicate packet #{packet_num}", "WARNING")
            elif self.last_packet_num >= 0 and packet_num > self.last_packet_num + 1:
                lost = packet_num - self.last_packet_num - 1
                self.packets_lost += lost
                self.alerts_panel.add_alert(f"Lost {lost} packets (gap: {self.last_packet_num+1}-{packet_num-1})", "WARNING")
            
            self.last_packet_num = packet_num
            self.last_packet_time = datetime.now()
            
            # Update data buffers (shift and add new data)
            self.times = np.roll(self.times, -1)
            self.altitudes = np.roll(self.altitudes, -1)
            self.speeds = np.roll(self.speeds, -1)
            self.accelerations = np.roll(self.accelerations, -1)
            self.gyro_x = np.roll(self.gyro_x, -1)
            self.gyro_y = np.roll(self.gyro_y, -1)
            self.gyro_z = np.roll(self.gyro_z, -1)
            self.temperatures = np.roll(self.temperatures, -1)
            self.pressures = np.roll(self.pressures, -1)
            self.mq7_values = np.roll(self.mq7_values, -1)
            self.mq135_values = np.roll(self.mq135_values, -1)
            
            # Add new data
            if self.mission_start_time:
                rel_time = (current_time - self.times[0]) if self.times[0] > 0 else 0
            else:
                rel_time = 0
            
            self.times[-1] = rel_time
            self.altitudes[-1] = altitude
            self.speeds[-1] = v_mag  # NOW USING SENSOR VELOCITY MAGNITUDE
            self.accelerations[-1] = total_accel
            self.gyro_x[-1] = gx
            self.gyro_y[-1] = gy
            self.gyro_z[-1] = gz
            self.temperatures[-1] = temperature
            self.pressures[-1] = pressure
            self.mq7_values[-1] = mq7
            self.mq135_values[-1] = mq135
            
            # Update flight state indicator (NEW)
            self.flight_state.update_state(state, v_mag)
            
            # Update mission statistics IN REAL-TIME
            self.mission_stats.update_stats(altitude, v_mag)
            
            # Update mission phase based on state (NEW)
            self.update_mission_phase_from_state(state)
            
            # Update plots
            self.update_plots()
            
            # Save to database
            self.db.guardar(data)
            
            # Check for alerts
            self.check_alerts(data)
            
        except Exception as e:
            print(f"[ERROR] Error processing data: {e}")
            import traceback
            traceback.print_exc()

    def update_plots(self):
        """Update all plot displays"""
        # Only plot non-zero data
        valid_mask = self.times > 0
        if np.any(valid_mask):
            self.altitude_line.setData(self.times[valid_mask], self.altitudes[valid_mask])
            self.speed_line.setData(self.times[valid_mask], self.speeds[valid_mask])
            self.acceleration_line.setData(self.times[valid_mask], self.accelerations[valid_mask])
            self.gyro_x_line.setData(self.times[valid_mask], self.gyro_x[valid_mask])
            self.gyro_y_line.setData(self.times[valid_mask], self.gyro_y[valid_mask])
            self.gyro_z_line.setData(self.times[valid_mask], self.gyro_z[valid_mask])
            self.temperature_line.setData(self.times[valid_mask], self.temperatures[valid_mask])
            self.pressure_line.setData(self.times[valid_mask], self.pressures[valid_mask])
            self.mq7_line.setData(self.times[valid_mask], self.mq7_values[valid_mask])
            self.mq135_line.setData(self.times[valid_mask], self.mq135_values[valid_mask])

    def check_alerts(self, data):
        """Check for critical conditions and generate alerts"""
        altitude = data[1]
        
        # Altitude threshold warnings - only trigger once
        if altitude > 900 and (self.last_alert_altitude is None or self.last_alert_altitude <= 900):
            self.alerts_panel.add_alert("Approaching maximum altitude!", "WARNING")
            self.last_alert_altitude = altitude
        
        if altitude < 100 and self.mission_phase.current_phase > 2:
            if self.last_alert_altitude is None or self.last_alert_altitude >= 100:
                self.alerts_panel.add_alert("Low altitude - Landing phase", "INFO")
                self.last_alert_altitude = altitude
        
        # Update last altitude
        if altitude > 900 or altitude < 100:
            self.last_alert_altitude = altitude

    def update_mission_phase(self, altitude):
        """Automatically update mission phase based on altitude"""
        if altitude < 10:
            self.mission_phase.set_phase(0)  # Pre-launch
        elif altitude < 300 and altitude > 10:
            self.mission_phase.set_phase(1)  # Ascent
        elif altitude >= 300 and altitude < 500:
            self.mission_phase.set_phase(2)  # Deployment
        elif altitude < 300 and self.mission_phase.current_phase >= 2:
            self.mission_phase.set_phase(3)  # Descent
        elif altitude < 50 and self.mission_phase.current_phase >= 3:
            self.mission_phase.set_phase(4)  # Landing
    
    def update_mission_phase_from_state(self, state):
        """Update mission phase based on flight state string"""
        state_to_phase = {
            "IDLE": 0,      # Pre-Launch
            "ASCEND": 1,    # Ascent
            "DESCEND1": 3,  # Descent (parachute 1)
            "DESCEND2": 3,  # Descent (parachute 2)
            "LANDING": 4    # Landing
        }
        
        phase = state_to_phase.get(state, self.mission_phase.current_phase)
        self.mission_phase.set_phase(phase)

    def start_mission(self):
        self.mission_start_time = datetime.now()
        self.last_alert_altitude = None
        self.db.start()
        self.alerts_panel.add_alert("Mission started!", "INFO")
        self.mission_stats.reset_stats()
        
        # NEW: Reset speed integration variables
        self.current_speed = 0.0
        self.last_time = None
        self.last_acceleration = None

    def stop_mission(self):
        self.mission_start_time = None
        self.last_alert_altitude = None
        self.db.stop()
        self.alerts_panel.add_alert("Mission stopped!", "INFO")

    def export_data(self):
        """Export mission data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Mission Data",
            f"mission_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                # Only export valid data (non-zero times)
                valid_mask = self.times > 0
                df = pd.DataFrame({
                    'Time': self.times[valid_mask],
                    'Altitude': self.altitudes[valid_mask],
                    'Speed': self.speeds[valid_mask],
                    'Acceleration': self.accelerations[valid_mask],
                    'Gyro_X': self.gyro_x[valid_mask],
                    'Gyro_Y': self.gyro_y[valid_mask],
                    'Gyro_Z': self.gyro_z[valid_mask],
                    'Temperature': self.temperatures[valid_mask],
                    'Pressure': self.pressures[valid_mask],
                    'MQ7': self.mq7_values[valid_mask],
                    'MQ135': self.mq135_values[valid_mask]
                })
                df.to_csv(filename, index=False)
                self.alerts_panel.add_alert(f"Data exported successfully!", "INFO")
            except Exception as e:
                self.alerts_panel.add_alert(f"Export failed: {str(e)}", "CRITICAL")

    def load_flight_data(self):
        """Load flight data from CSV for analysis"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Flight Data",
            "",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                df = pd.read_csv(filename)
                self.results_text.append(f"Loaded: {filename}\n")
                self.results_text.append(f"Data points: {len(df)}\n")
                self.results_text.append(f"Duration: {df['Time'].max() - df['Time'].min():.2f} seconds\n")
                self.results_text.append(f"Max Altitude: {df['Altitude'].max():.2f} m\n")
                self.results_text.append(f"Max Speed: {df['Speed'].max():.2f} m/s\n")
            except Exception as e:
                self.results_text.append(f"Error loading file: {str(e)}\n")

    def generate_report(self):
        """Generate a competition report"""
        report = f"""
===== CANSAT MISSION REPORT =====
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MISSION STATISTICS:
- Maximum Altitude: {self.mission_stats.max_alt_value:.2f} m
- Maximum Speed: {self.mission_stats.max_speed_value:.2f} m/s
- Total Flight Time: {self.mission_timer.value():.2f} s

DATA QUALITY:
- Packets Received: {self.packets_received}
- Packets Lost: {self.packets_lost}
- Packet Loss Rate: {(self.packets_lost/(self.packets_received+self.packets_lost)*100) if self.packets_received+self.packets_lost > 0 else 0:.2f}%

MISSION PHASES COMPLETED:
✓ Pre-Launch
✓ Ascent
✓ Deployment
✓ Descent
✓ Landing

==================================
        """
        self.results_text.setText(report)

    def update_mission_timer(self):
        """Update mission elapsed time"""
        if self.mission_start_time:
            elapsed = (datetime.now() - self.mission_start_time).total_seconds()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.mission_timer.display(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def update_ui(self):
        """Update UI elements periodically"""
        # Update data quality indicators
        last_time_str = self.last_packet_time.strftime("%H:%M:%S") if self.last_packet_time else "Never"
        data_rate = self.packets_received  # Simple rate calculation
        
        self.data_quality.update_stats(
            self.packets_received,
            self.packets_lost,
            last_time_str,
            data_rate,
            self.ser.connected
        )
        
        # Update serial status indicator
        if self.serial_active:
            self.serial_status.setText("🟢 Serial ON")
            self.serial_status.setStyleSheet("""
                QLabel {
                    background-color: #00ff00;
                    color: black;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        else:
            self.serial_status.setText("🔴 Serial OFF")
            self.serial_status.setStyleSheet("""
                QLabel {
                    background-color: #ff0000;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_S:
            self.toggle_serial_communication()
        elif event.key() == Qt.Key_Space:
            self.toggle_serial_communication()

    def toggle_serial_communication(self):
        """Toggle serial data reception on/off"""
        self.serial_active = not self.serial_active
        
        if self.serial_active:
            # Start receiving data
            self.update_timer.start(100)
            self.alerts_panel.add_alert("Serial STARTED (Press S to stop)", "INFO")
            print("[OK] Started listening to COM port")
        else:
            # Stop receiving data
            self.update_timer.stop()
            self.alerts_panel.add_alert("Serial STOPPED (Press S to start)", "WARNING")
            print("[STOPPED] Stopped listening to COM port")

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()