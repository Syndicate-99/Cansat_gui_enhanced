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
    print(" pyserial not installed. Run: pip install pyserial")

class Communication:
    """
    Real Arduino communication class
    Usage: Communication(port='COM3', baudrate=9600)
    """
    def __init__(self, port='COM3', baudrate=9600, use_simulator=False):
        self.connected = False
        self.ser = None
        self.use_simulator = use_simulator
        
        if use_simulator:
            # Use simulator for testing
            try:
                from flight_simulator import FlightSimulator
                self.simulator = FlightSimulator()
                self.connected = True
                print(" Using flight simulator")
            except:
                print("Flight simulator not found, using random data")
                self.simulator = None
        else:
            # Real serial connection
            if not SERIAL_AVAILABLE:
                print(" pyserial not installed! Install with: pip install pyserial")
                return
            
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                import time
                time.sleep(2)  # Wait for Arduino reset
                self.connected = True
                print(f"Connected to {port} at {baudrate} baud")
            except Exception as e:
                self.connected = False
                print(f"Failed to connect to {port}: {e}")
                print(f"Available ports: {self.list_ports()}")
    
    @staticmethod
    def list_ports():
        """List all available COM ports"""
        if SERIAL_AVAILABLE:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        return []
    
    def getData(self):
        """Get data from Arduino or simulator"""
        if self.use_simulator:
            # Use flight simulator
            if hasattr(self, 'simulator') and self.simulator:
                import time
                if not hasattr(self, 'last_update'):
                    self.last_update = time.time()
                current_time = time.time()
                dt = current_time - self.last_update
                self.last_update = current_time
                return self.simulator.update(dt * 2)  # 2x speed
            else:
                # Random data fallback
                import random
                return [datetime.now().timestamp(), random.uniform(0, 1000), 0, 0, 0, 
                        random.uniform(-180, 180), random.uniform(-180, 180), random.uniform(-180, 180),
                        random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)]
        
        # Real Arduino data
        if not self.connected or self.ser is None:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    # Parse the data
                    data = self.parse_data(line)
                    return data
            return None
        except Exception as e:
            print(f"Error reading serial: {e}")
            return None
    
    def parse_data(self, line):
        """
        Parse data from Arduino
        Expected format (CSV): time,alt,temp,press,humid,gx,gy,gz,ax,ay,az,lat,lon
        
        Modify this function to match YOUR Arduino's data format!
        """
        try:
            # CSV format
            parts = line.split(',')
            if len(parts) >= 11:
                data = [float(x) for x in parts[:13]]
                return data
            else:
                print(f" Expected 13 values, got {len(parts)}: {line}")
                return None
        except ValueError as e:
            print(f" Parse error: {e} | Line: {line}")
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
        print(f" Started recording to {self.filename}")
    
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
                print(f" Saved {len(self.data_log)} data points to {self.filename}")
            except Exception as e:
                print(f" Error saving data: {e}")
    
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
        # Update max values
        if altitude > self.max_alt_value:
            self.max_alt_value = altitude
            self.max_altitude.display(f"{altitude:.2f}")
        
        if speed > self.max_speed_value:
            self.max_speed_value = speed
            self.max_speed.display(f"{speed:.2f}")
        
        # Update current altitude
        self.current_altitude.display(f"{altitude:.2f}")

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
        
        # Mission tracking
        self.packets_received = 0
        self.packets_lost = 0
        self.last_packet_time = None
        self.mission_start_time = None
        self.last_alert_altitude = None

        # Initialize plots
        self.setup_plots()

        # Initialize communication and database
        # CHANGE THIS TO USE YOUR COM PORT:
        # self.ser = Communication(port='COM3', baudrate=9600, use_simulator=False)
        self.ser = Communication(use_simulator=True)  # Using simulator by default
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
        self.speed_plot.setTitle("Speed (m/s)", color='w')
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
        self.gyro_plot.setTitle("Gyroscope (deg/s)", color='w')
        self.gyro_plot.setLabel('left', 'Angular Velocity', units='deg/s')
        self.gyro_plot.setLabel('bottom', 'Time', units='s')
        self.gyro_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gyro_x_line = self.gyro_plot.plot(pen=pg.mkPen(color='r', width=2), name='X')
        self.gyro_y_line = self.gyro_plot.plot(pen=pg.mkPen(color='g', width=2), name='Y')
        self.gyro_z_line = self.gyro_plot.plot(pen=pg.mkPen(color='b', width=2), name='Z')
        self.gyro_plot.addLegend()

    def create_header(self):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        # Logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("logo1.jpg")
            if logo_pixmap.isNull():
                logo_label.setText("🛰️")
                logo_label.setStyleSheet("font-size: 48px;")
            else:
                scaled_logo = logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_logo)
        except:
            logo_label.setText("🛰️")
            logo_label.setStyleSheet("font-size: 48px;")
        
        # Title
        title = QLabel("Parikshit Student Satellite\nCanSat Ground Station")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin: 10px;
        """)
        
        # Serial status indicator
        self.serial_status = QLabel("🟢 Serial ON")
        self.serial_status.setStyleSheet("""
            QLabel {
                background-color: #00ff00;
                color: black;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
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
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.serial_status)
        header_layout.addWidget(QLabel("Mission Time:"))
        header_layout.addWidget(self.mission_timer)
        
        return header

    def create_navigation(self):
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        
        monitoring_btn = ModernButton("📊 Real-Time")
        preflight_btn = ModernButton("✓ Pre-Flight")
        analysis_btn = ModernButton("📈 Analysis")
        
        monitoring_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        preflight_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        analysis_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        nav_layout.addWidget(monitoring_btn)
        nav_layout.addWidget(preflight_btn)
        nav_layout.addWidget(analysis_btn)
        
        return nav

    def create_monitoring_page(self):
        page = QWidget()
        layout = QGridLayout(page)
        
        # Left column - Graphs
        graph_widget = QWidget()
        graph_layout = QGridLayout(graph_widget)
        
        altitude_card = self.create_graph_card("Altitude (m)", self.altitude_plot)
        speed_card = self.create_graph_card("Speed (m/s)", self.speed_plot)
        acceleration_card = self.create_graph_card("Acceleration (m/s²)", self.acceleration_plot)
        gyro_card = self.create_graph_card("Gyroscope", self.gyro_plot)
        
        graph_layout.addWidget(altitude_card, 0, 0)
        graph_layout.addWidget(speed_card, 0, 1)
        graph_layout.addWidget(acceleration_card, 1, 0)
        graph_layout.addWidget(gyro_card, 1, 1)
        
        # Right column - Info panels
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Mission stats
        self.mission_stats = MissionStats()
        info_layout.addWidget(self.mission_stats)
        
        # Data quality
        self.data_quality = DataQualityIndicator()
        info_layout.addWidget(self.data_quality)
        
        # Alerts panel
        self.alerts_panel = AlertsPanel()
        info_layout.addWidget(self.alerts_panel)
        
        # Control buttons
        control_card = DataCard("Mission Control")
        control_layout = QVBoxLayout(control_card)
        
        start_btn = ModernButton("▶ Start Mission")
        stop_btn = ModernButton("⏹ Stop Mission")
        export_btn = ModernButton("💾 Export Data")
        
        # Add keyboard hint
        keyboard_hint = QLabel("💡 Press 'S' to toggle serial ON/OFF")
        keyboard_hint.setStyleSheet("color: #ffff00; font-size: 11px; padding: 5px;")
        
        start_btn.clicked.connect(self.start_mission)
        stop_btn.clicked.connect(self.stop_mission)
        export_btn.clicked.connect(self.export_data)
        
        control_layout.addWidget(start_btn)
        control_layout.addWidget(stop_btn)
        control_layout.addWidget(export_btn)
        control_layout.addWidget(keyboard_hint)
        
        info_layout.addWidget(control_card)
        info_layout.addStretch()
        
        # Add to main layout
        layout.addWidget(graph_widget, 0, 0, 1, 2)
        layout.addWidget(info_widget, 0, 2)
        
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        
        return page

    def create_graph_card(self, title, plot_widget):
        card = DataCard(title)
        layout = QVBoxLayout(card)
        layout.addWidget(plot_widget)
        return card

    def create_preflight_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Checklist
        self.preflight_checklist = PreflightChecklist()
        layout.addWidget(self.preflight_checklist)
        
        # System diagnostics
        diagnostics = DataCard("System Diagnostics")
        diag_layout = QGridLayout(diagnostics)
        
        # Add various diagnostic checks
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("Memory: --")
        self.storage_label = QLabel("Storage: --")
        self.battery_label = QLabel("Battery: --")
        
        diag_layout.addWidget(QLabel("System Health:"), 0, 0)
        diag_layout.addWidget(self.cpu_label, 1, 0)
        diag_layout.addWidget(self.memory_label, 1, 1)
        diag_layout.addWidget(self.storage_label, 2, 0)
        diag_layout.addWidget(self.battery_label, 2, 1)
        
        layout.addWidget(diagnostics)
        layout.addStretch()
        
        return page

    def create_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Analysis tools
        analysis_card = DataCard("Post-Flight Analysis")
        analysis_layout = QGridLayout(analysis_card)
        
        # Load data button
        load_btn = ModernButton("📂 Load Flight Data")
        load_btn.clicked.connect(self.load_flight_data)
        
        # Generate report button
        report_btn = ModernButton("📄 Generate Report")
        report_btn.clicked.connect(self.generate_report)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: monospace;
            }
        """)
        
        analysis_layout.addWidget(load_btn, 0, 0)
        analysis_layout.addWidget(report_btn, 0, 1)
        analysis_layout.addWidget(self.results_text, 1, 0, 1, 2)
        
        layout.addWidget(analysis_card)
        
        return page

    def setup_timers(self):
        # Update timer for sensor data
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(500)  # Starts automatically
        
        # Mission timer update
        self.mission_timer_update = QTimer()
        self.mission_timer_update.timeout.connect(self.update_mission_timer)
        self.mission_timer_update.start(100)

    def update_mission_timer(self):
        if self.mission_start_time:
            elapsed = (datetime.now() - self.mission_start_time).total_seconds()
            self.mission_timer.display(f"{elapsed:.2f}")

    def update_data(self):
        try:
            data = self.ser.getData()
            if data:
                # Update packet statistics
                self.packets_received += 1
                self.last_packet_time = datetime.now()
                
                # Update data buffers
                self.times = np.roll(self.times, -1)
                self.times[-1] = data[0]
                
                self.altitudes = np.roll(self.altitudes, -1)
                self.altitudes[-1] = data[1]
                
                # Calculate speed from data or use provided value
                if hasattr(self.ser, 'simulator'):
                    actual_speed = self.ser.simulator.get_speed()
                else:
                    # Fallback: estimate speed from altitude change
                    if len(self.altitudes) > 1:
                        actual_speed = abs(self.altitudes[-1] - self.altitudes[-2]) / 0.5
                    else:
                        actual_speed = 0
                
                self.speeds = np.roll(self.speeds, -1)
                self.speeds[-1] = actual_speed
                
                self.accelerations = np.roll(self.accelerations, -1)
                self.accelerations[-1] = np.sqrt(data[8]**2 + data[9]**2 + data[10]**2)
                
                self.gyro_x = np.roll(self.gyro_x, -1)
                self.gyro_x[-1] = data[5]
                
                self.gyro_y = np.roll(self.gyro_y, -1)
                self.gyro_y[-1] = data[6]
                
                self.gyro_z = np.roll(self.gyro_z, -1)
                self.gyro_z[-1] = data[7]
                
                # Update plots
                self.update_plots()
                
                # Update mission stats only if mission is running
                if self.mission_start_time:
                    self.mission_stats.update_stats(data[1], actual_speed)
                
                # Update data quality
                last_time_str = self.last_packet_time.strftime("%H:%M:%S") if self.last_packet_time else "Never"
                self.data_quality.update_stats(
                    self.packets_received,
                    self.packets_lost,
                    last_time_str,
                    100,
                    True
                )
                
                # Check for alerts only if mission is running
                if self.mission_start_time:
                    self.check_alerts(data)
                
                # Update mission phase based on altitude
                self.update_mission_phase(data[1])
                
                # Store data
                self.db.guardar(data)
        except Exception as e:
            print(f"Error updating data: {e}")

    def update_plots(self):
        self.altitude_line.setData(self.times, self.altitudes)
        self.speed_line.setData(self.times, self.speeds)
        self.acceleration_line.setData(self.times, self.accelerations)
        self.gyro_x_line.setData(self.times, self.gyro_x)
        self.gyro_y_line.setData(self.times, self.gyro_y)
        self.gyro_z_line.setData(self.times, self.gyro_z)

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

    def start_mission(self):
        self.mission_start_time = datetime.now()
        self.last_alert_altitude = None
        self.db.start()
        self.alerts_panel.add_alert("Mission started!", "INFO")
        self.mission_stats.reset_stats()

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
                df = pd.DataFrame({
                    'Time': self.times,
                    'Altitude': self.altitudes,
                    'Speed': self.speeds,
                    'Acceleration': self.accelerations,
                    'Gyro_X': self.gyro_x,
                    'Gyro_Y': self.gyro_y,
                    'Gyro_Z': self.gyro_z
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
            self.update_timer.start(500)
            self.alerts_panel.add_alert("Serial STARTED (Press S to stop)", "INFO")
            # Update visual indicator
            self.serial_status.setText("🟢 Serial ON")
            self.serial_status.setStyleSheet("""
                QLabel {
                    background-color: #00ff00;
                    color: black;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
            print(" Started listening to COM port")
        else:
            # Stop receiving data
            self.update_timer.stop()
            self.alerts_panel.add_alert("Serial STOPPED (Press S to start)", "WARNING")
            # Update visual indicator
            self.serial_status.setText("🔴 Serial OFF")
            self.serial_status.setStyleSheet("""
                QLabel {
                    background-color: #ff0000;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
            print(" Stopped listening to COM port")

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
