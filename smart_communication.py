"""
Smart Communication Class with Auto-Detection
Automatically learns your Arduino's data format!
"""

import serial
import serial.tools.list_ports
import re
import time
import numpy as np

class SmartCommunication:
    """
    Automatically detects and parses ANY data format from Arduino
    """
    
    def __init__(self, port='COM8', baudrate=9600, auto_detect=True):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
        
        # Auto-detection state
        self.format_detected = False
        self.data_format = None
        self.field_mapping = {}
        self.sample_lines = []
        
        # Try to connect
        self.connect()
        
        # Auto-detect format if requested
        if auto_detect and self.connected:
            print("[AUTO-DETECT] Scanning for data format...")
            self.auto_detect_format()
    
    def connect(self):
        """Connect to serial port"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            self.connected = True
            print(f"[OK] Connected to {port} at {baudrate} baud")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            print(f"[INFO] Available ports: {self.list_available_ports()}")
            return False
    
    @staticmethod
    def list_available_ports():
        """List all available COM ports"""
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except:
            return []
    
    def auto_detect_format(self, sample_count=10):
        """
        Automatically detect data format by analyzing sample lines
        """
        print(f"[AUTO-DETECT] Collecting {sample_count} sample lines...")
        
        # Collect sample lines
        self.sample_lines = []
        attempts = 0
        max_attempts = 50
        
        while len(self.sample_lines) < sample_count and attempts < max_attempts:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line and len(line) > 5:  # Ignore very short lines
                        self.sample_lines.append(line)
                        print(f"  Sample {len(self.sample_lines)}: {line[:80]}...")
                except:
                    pass
            attempts += 1
            time.sleep(0.1)
        
        if len(self.sample_lines) < 3:
            print("[ERROR] Not enough data to detect format")
            return False
        
        # Analyze format
        self.analyze_format()
        return self.format_detected
    
    def analyze_format(self):
        """
        Analyze sample lines to determine data format
        """
        print("[AUTO-DETECT] Analyzing data format...")
        
        # Try different format detectors
        formats_to_try = [
            ('CSV', self.detect_csv_format),
            ('JSON', self.detect_json_format),
            ('Key-Value', self.detect_keyvalue_format),
            ('Space-Separated', self.detect_space_format),
            ('Labeled', self.detect_labeled_format),
        ]
        
        for format_name, detector_func in formats_to_try:
            print(f"[AUTO-DETECT] Trying {format_name} format...")
            if detector_func():
                self.data_format = format_name
                self.format_detected = True
                print(f"[SUCCESS] Detected format: {format_name}")
                self.print_field_mapping()
                return True
        
        print("[WARNING] Could not detect format automatically")
        print("[INFO] Using fallback generic parser")
        self.data_format = 'Generic'
        self.format_detected = True
        return False
    
    def detect_csv_format(self):
        """Detect comma-separated values format"""
        # Check if all lines have commas
        comma_counts = [line.count(',') for line in self.sample_lines]
        
        # Must have consistent comma counts
        if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
            num_fields = comma_counts[0] + 1
            print(f"  -> Found {num_fields} fields (comma-separated)")
            
            # Try to identify field types
            self.identify_csv_fields()
            return True
        
        return False
    
    def identify_csv_fields(self):
        """Identify what each CSV field represents"""
        # Parse first line
        values = self.sample_lines[0].split(',')
        num_fields = len(values)
        
        print(f"  -> Analyzing {num_fields} fields...")
        
        # Collect all values for each field
        field_values = [[] for _ in range(num_fields)]
        for line in self.sample_lines:
            parts = line.split(',')
            if len(parts) == num_fields:
                for i, val in enumerate(parts):
                    try:
                        field_values[i].append(float(val))
                    except:
                        pass
        
        # Analyze each field
        for i, values in enumerate(field_values):
            if len(values) < 2:
                continue
            
            values_arr = np.array(values)
            mean = np.mean(values_arr)
            std = np.std(values_arr)
            min_val = np.min(values_arr)
            max_val = np.max(values_arr)
            range_val = max_val - min_val
            
            # Guess field type based on value ranges and patterns
            field_type = self.guess_field_type(mean, std, min_val, max_val, range_val, values_arr)
            self.field_mapping[i] = field_type
            print(f"    Field {i}: {field_type} (range: {min_val:.2f} to {max_val:.2f})")
    
    def guess_field_type(self, mean, std, min_val, max_val, range_val, values):
        """Guess what a field represents based on its values"""
        
        # Time: Usually increasing, 0-1000+
        if len(values) > 2 and all(values[i] <= values[i+1] for i in range(len(values)-1)):
            if min_val >= 0:
                return 'time'
        
        # Altitude: 0-5000m typically
        if 0 <= mean <= 5000 and range_val > 10:
            if std > 5:  # Must vary
                return 'altitude'
        
        # Temperature: -50 to 85°C typically
        if -50 <= mean <= 85 and range_val < 50:
            return 'temperature'
        
        # Pressure: 800-1100 hPa typically
        if 800 <= mean <= 1100 and range_val < 100:
            return 'pressure'
        
        # Humidity: 0-100%
        if 0 <= mean <= 100 and range_val < 100:
            return 'humidity'
        
        # Gyroscope: -500 to 500 deg/s typically
        if abs(mean) < 100 and -500 <= min_val and max_val <= 500:
            if std > 1:  # Must vary
                return 'gyroscope'
        
        # Accelerometer: -20 to 20 m/s² typically (around 9.8 for Z)
        if -20 <= mean <= 20 and -20 <= min_val and max_val <= 20:
            return 'acceleration'
        
        # GPS Latitude: -90 to 90
        if -90 <= mean <= 90 and range_val < 1:
            return 'latitude'
        
        # GPS Longitude: -180 to 180
        if -180 <= mean <= 180 and range_val < 1:
            return 'longitude'
        
        return 'unknown'
    
    def detect_json_format(self):
        """Detect JSON format"""
        try:
            import json
            # Try parsing first line as JSON
            obj = json.loads(self.sample_lines[0])
            if isinstance(obj, dict):
                print(f"  -> Found JSON with keys: {list(obj.keys())}")
                self.field_mapping = {key: key for key in obj.keys()}
                return True
        except:
            pass
        return False
    
    def detect_keyvalue_format(self):
        """Detect key:value or key=value format"""
        # Check for consistent key:value or key=value patterns
        sample = self.sample_lines[0]
        
        # Try colon separator
        if ':' in sample and ',' in sample:
            parts = sample.split(',')
            if all(':' in part for part in parts):
                print(f"  -> Found key:value format")
                # Extract keys
                keys = [part.split(':')[0].strip() for part in parts]
                self.field_mapping = {i: key for i, key in enumerate(keys)}
                return True
        
        # Try equals separator
        if '=' in sample and ',' in sample:
            parts = sample.split(',')
            if all('=' in part for part in parts):
                print(f"  -> Found key=value format")
                keys = [part.split('=')[0].strip() for part in parts]
                self.field_mapping = {i: key for i, key in enumerate(keys)}
                return True
        
        return False
    
    def detect_space_format(self):
        """Detect space-separated format"""
        # Check if values are space-separated
        sample = self.sample_lines[0]
        if ',' not in sample and ' ' in sample:
            parts = sample.split()
            # Check if they're all numbers
            try:
                [float(p) for p in parts]
                print(f"  -> Found {len(parts)} space-separated fields")
                self.identify_space_fields(parts)
                return True
            except:
                pass
        return False
    
    def identify_space_fields(self, parts):
        """Identify space-separated fields"""
        # Similar to CSV identification
        num_fields = len(parts)
        field_values = [[] for _ in range(num_fields)]
        
        for line in self.sample_lines:
            parts = line.split()
            if len(parts) == num_fields:
                for i, val in enumerate(parts):
                    try:
                        field_values[i].append(float(val))
                    except:
                        pass
        
        for i, values in enumerate(field_values):
            if len(values) >= 2:
                values_arr = np.array(values)
                mean = np.mean(values_arr)
                std = np.std(values_arr)
                min_val = np.min(values_arr)
                max_val = np.max(values_arr)
                range_val = max_val - min_val
                
                field_type = self.guess_field_type(mean, std, min_val, max_val, range_val, values_arr)
                self.field_mapping[i] = field_type
    
    def detect_labeled_format(self):
        """Detect labeled format like 'Altitude: 123.45m'"""
        sample = self.sample_lines[0]
        
        # Look for patterns like "Word: Number" or "Word Number"
        pattern = r'([A-Za-z]+)\s*[:=]?\s*(-?\d+\.?\d*)'
        matches = re.findall(pattern, sample)
        
        if len(matches) >= 3:  # At least 3 labeled values
            print(f"  -> Found labeled format with {len(matches)} fields")
            self.field_mapping = {i: label.lower() for i, (label, value) in enumerate(matches)}
            return True
        
        return False
    
    def print_field_mapping(self):
        """Print detected field mapping"""
        print("\n[FIELD MAPPING]")
        for idx, field_name in self.field_mapping.items():
            print(f"  Field {idx}: {field_name}")
        print()
    
    def getData(self):
        """
        Get data and parse according to detected format
        Returns standard 13-value array for GUI compatibility
        """
        if not self.connected or not self.ser:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    return self.parse_line(line)
        except Exception as e:
            print(f"[ERROR] Read error: {e}")
        
        return None
    
    def parse_line(self, line):
        """
        Parse a line according to detected format
        """
        if not self.format_detected:
            return self.generic_parse(line)
        
        try:
            if self.data_format == 'CSV':
                return self.parse_csv(line)
            elif self.data_format == 'JSON':
                return self.parse_json(line)
            elif self.data_format == 'Key-Value':
                return self.parse_keyvalue(line)
            elif self.data_format == 'Space-Separated':
                return self.parse_space(line)
            elif self.data_format == 'Labeled':
                return self.parse_labeled(line)
            else:
                return self.generic_parse(line)
        except:
            return None
    
    def parse_csv(self, line):
        """Parse CSV format"""
        parts = line.split(',')
        values = []
        for part in parts:
            try:
                values.append(float(part.strip()))
            except:
                values.append(0.0)
        
        return self.map_to_standard_format(values)
    
    def parse_json(self, line):
        """Parse JSON format"""
        import json
        obj = json.loads(line)
        
        # Extract values in order
        values = []
        for key in self.field_mapping.values():
            values.append(float(obj.get(key, 0)))
        
        return self.map_to_standard_format(values)
    
    def parse_keyvalue(self, line):
        """Parse key:value or key=value format"""
        parts = line.split(',')
        values = []
        
        for part in parts:
            if ':' in part:
                _, value = part.split(':', 1)
            elif '=' in part:
                _, value = part.split('=', 1)
            else:
                value = part
            
            try:
                values.append(float(value.strip()))
            except:
                values.append(0.0)
        
        return self.map_to_standard_format(values)
    
    def parse_space(self, line):
        """Parse space-separated format"""
        parts = line.split()
        values = []
        for part in parts:
            try:
                values.append(float(part.strip()))
            except:
                values.append(0.0)
        
        return self.map_to_standard_format(values)
    
    def parse_labeled(self, line):
        """Parse labeled format"""
        pattern = r'([A-Za-z]+)\s*[:=]?\s*(-?\d+\.?\d*)'
        matches = re.findall(pattern, line)
        
        values = [float(value) for _, value in matches]
        return self.map_to_standard_format(values)
    
    def generic_parse(self, line):
        """Generic parser - extract all numbers"""
        # Extract all numbers from the line
        numbers = re.findall(r'-?\d+\.?\d*', line)
        values = [float(n) for n in numbers]
        return self.map_to_standard_format(values)
    
    def map_to_standard_format(self, values):
        """
        Map detected values to standard GUI format:
        [time, altitude, temp, pressure, humidity, gx, gy, gz, ax, ay, az, lat, lon]
        """
        standard = [0.0] * 13  # Initialize with zeros
        
        # Map detected fields to standard positions
        field_positions = {
            'time': 0,
            'altitude': 1,
            'temperature': 2,
            'pressure': 3,
            'humidity': 4,
            'gyroscope': [5, 6, 7],  # Can map to multiple
            'acceleration': [8, 9, 10],
            'latitude': 11,
            'longitude': 12
        }
        
        gyro_idx = 0
        accel_idx = 0
        
        for i, value in enumerate(values):
            if i >= len(values):
                break
            
            # Get field type for this index
            field_type = self.field_mapping.get(i, 'unknown')
            
            if field_type in field_positions:
                pos = field_positions[field_type]
                
                if isinstance(pos, list):
                    # Multiple positions (gyro or accel)
                    if field_type == 'gyroscope' and gyro_idx < 3:
                        standard[pos[gyro_idx]] = value
                        gyro_idx += 1
                    elif field_type == 'acceleration' and accel_idx < 3:
                        standard[pos[accel_idx]] = value
                        accel_idx += 1
                else:
                    standard[pos] = value
            else:
                # Unknown field - try to place it somewhere useful
                if i < 13:
                    standard[i] = value
        
        # Generate time if not present
        if standard[0] == 0:
            standard[0] = time.time()
        
        return standard
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            print("[INFO] Serial connection closed")


def scan_and_connect_auto():
    """
    Scan all ports and auto-detect Arduino
    """
    print("[SCAN] Scanning for Arduino...")
    
    ports = SmartCommunication.list_available_ports()
    
    if not ports:
        print("[ERROR] No serial ports found")
        return None
    
    print(f"[SCAN] Found ports: {ports}")
    
    # Try each port
    for port in ports:
        for baud in [9600, 115200, 57600]:
            print(f"[SCAN] Trying {port} at {baud} baud...")
            
            try:
                comm = SmartCommunication(port=port, baudrate=baud, auto_detect=True)
                if comm.connected and comm.format_detected:
                    print(f"[SUCCESS] Connected and detected format!")
                    return comm
                else:
                    comm.close()
            except:
                pass
    
    print("[ERROR] No Arduino found with detectable data")
    return None


# Test function
if __name__ == "__main__":
    print("="*60)
    print("SMART COMMUNICATION AUTO-DETECTION TEST")
    print("="*60)
    print()
    # Option 1: Specific port
    print("Option 1: Connect to specific port")
    comm = SmartCommunication(port='COM8', baudrate=9600, auto_detect=True)
    # Option 2: Auto-scan
    # comm = scan_and_connect_auto()

    if comm and comm.connected:
        print("\n[TEST] Reading 10 parsed data packets:")
        print("-"*60)
        
        for i in range(10):
            data = comm.getData()
            if data:
                print(f"Packet {i+1}:")
                print(f"  Time: {data[0]:.2f}s")
                print(f"  Altitude: {data[1]:.2f}m")
                print(f"  Temperature: {data[2]:.2f}°C")
                print(f"  Gyro: ({data[5]:.2f}, {data[6]:.2f}, {data[7]:.2f})")
                print()
            time.sleep(0.5)
        
        comm.close()
        print("\n[OK] Test complete!")
    else:
        print("\n[ERROR] Could not establish connection")