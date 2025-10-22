"""
CanSat Flight Simulator
Generates realistic telemetry data for testing the GUI
"""

import numpy as np
from datetime import datetime
import time

class FlightSimulator:
    """Simulates a complete CanSat flight with realistic data"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset simulation to beginning"""
        self.time_elapsed = 0
        self.phase = "pre_launch"  # pre_launch, ascent, deployment, descent, landing
        self.max_altitude = 1000  # meters
        self.launch_time = 0
        self.deployment_time = 120  # seconds
        self.landing_time = 240  # seconds
        
        # Initial conditions
        self.altitude = 0
        self.velocity = 0
        self.acceleration = 0
        self.temperature = 25  # Celsius
        
        # Gyroscope (rotation rates)
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0
        
        # GPS
        self.latitude = 13.3379  # Example: Udupi, Karnataka
        self.longitude = 74.7461
        
        # Add some noise
        self.noise_level = 1.0
        
    def get_phase(self):
        """Determine current flight phase based on time"""
        if self.time_elapsed < 5:
            return "pre_launch"
        elif self.time_elapsed < self.deployment_time:
            return "ascent"
        elif self.time_elapsed < self.deployment_time + 5:
            return "deployment"
        elif self.time_elapsed < self.landing_time:
            return "descent"
        else:
            return "landing"
    
    def simulate_ascent(self, dt):
        """Simulate rocket/balloon ascent phase"""
        # Exponential approach to max altitude
        target_altitude = self.max_altitude
        altitude_rate = 8  # m/s average ascent rate
        
        self.velocity = altitude_rate * (1 - self.altitude / target_altitude)
        self.altitude += self.velocity * dt
        
        # Acceleration (mostly vertical during ascent)
        self.acceleration = 9.8 + np.random.normal(0, 0.5)
        
        # Rotation during ascent (some tumbling)
        self.gyro_x = np.random.normal(10, 5)
        self.gyro_y = np.random.normal(5, 3)
        self.gyro_z = np.random.normal(15, 8)
        
    def simulate_deployment(self, dt):
        """Simulate parachute deployment - sudden deceleration"""
        # Sudden change in acceleration
        self.acceleration = -15 + np.random.normal(0, 2)
        self.velocity = max(self.velocity - 20 * dt, -5)  # Quick deceleration
        self.altitude += self.velocity * dt
        
        # High rotation during deployment
        self.gyro_x = np.random.normal(50, 20)
        self.gyro_y = np.random.normal(40, 15)
        self.gyro_z = np.random.normal(60, 25)
        
    def simulate_descent(self, dt):
        """Simulate parachute descent"""
        # Constant descent rate with parachute
        self.velocity = -5 + np.random.normal(0, 0.3)  # ~5 m/s descent
        self.altitude += self.velocity * dt
        self.altitude = max(0, self.altitude)  # Can't go below ground
        
        # Gentle swaying
        self.gyro_x = np.random.normal(5, 2)
        self.gyro_y = np.random.normal(5, 2)
        self.gyro_z = np.random.normal(10, 4)
        
        # Acceleration mostly gravity
        self.acceleration = 9.8 + np.random.normal(0, 0.3)
        
    def simulate_landing(self, dt):
        """Simulate landing - everything stops"""
        self.altitude = 0
        self.velocity = 0
        self.acceleration = 9.8
        
        # Minimal movement after landing
        self.gyro_x = np.random.normal(0, 0.5)
        self.gyro_y = np.random.normal(0, 0.5)
        self.gyro_z = np.random.normal(0, 0.5)
    
    def update(self, dt=1.0):
        """Update simulation by dt seconds"""
        self.time_elapsed += dt
        self.phase = self.get_phase()
        
        # Update based on phase
        if self.phase == "pre_launch":
            # Sitting on launch pad
            self.altitude = 0
            self.velocity = 0
            self.acceleration = 9.8
            self.gyro_x = np.random.normal(0, 0.1)
            self.gyro_y = np.random.normal(0, 0.1)
            self.gyro_z = np.random.normal(0, 0.1)
            
        elif self.phase == "ascent":
            self.simulate_ascent(dt)
            
        elif self.phase == "deployment":
            self.simulate_deployment(dt)
            
        elif self.phase == "descent":
            self.simulate_descent(dt)
            
        else:  # landing
            self.simulate_landing(dt)
        
        # Update temperature (decreases with altitude)
        self.temperature = 25 - (self.altitude / 1000) * 6.5  # Standard lapse rate
        
        # Update GPS (slight drift during flight)
        if self.phase not in ["pre_launch", "landing"]:
            self.latitude += np.random.normal(0, 0.0001)
            self.longitude += np.random.normal(0, 0.0001)
        
        return self.get_data()
    
    def get_data(self):
        """
        Return data in the format expected by the GUI
        [time, altitude, temp, pressure, humidity, gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, lat, lon]
        """
        # Add some noise to make it realistic
        noise = self.noise_level
        
        return [
            self.time_elapsed,                              # 0: Time
            self.altitude + np.random.normal(0, noise),    # 1: Altitude
            self.temperature + np.random.normal(0, 0.5),   # 2: Temperature
            1013 - (self.altitude * 0.12),                 # 3: Pressure (decreases with altitude)
            50 + np.random.normal(0, 5),                   # 4: Humidity
            self.gyro_x + np.random.normal(0, noise),      # 5: Gyro X
            self.gyro_y + np.random.normal(0, noise),      # 6: Gyro Y
            self.gyro_z + np.random.normal(0, noise),      # 7: Gyro Z
            np.random.normal(0, 0.5),                      # 8: Accel X
            np.random.normal(0, 0.5),                      # 9: Accel Y
            self.acceleration + np.random.normal(0, 0.3),  # 10: Accel Z
            self.latitude,                                  # 11: Latitude
            self.longitude                                  # 12: Longitude
        ]
    
    def get_speed(self):
        """Return current speed"""
        return abs(self.velocity)


class Communication:
    """Mock communication class that uses the flight simulator"""
    
    def __init__(self, use_simulator=True):
        self.connected = True
        self.use_simulator = use_simulator
        
        if use_simulator:
            self.simulator = FlightSimulator()
            self.last_update = time.time()
    
    def getData(self):
        """Get telemetry data"""
        if self.use_simulator:
            # Update simulator in real-time
            current_time = time.time()
            dt = current_time - self.last_update
            self.last_update = current_time
            
            # Simulate at 2x speed for faster testing
            return self.simulator.update(dt * 2)
        else:
            # Return dummy random data if not using simulator
            import random
            return [
                time.time(),
                random.uniform(0, 1000),
                random.uniform(15, 30),
                random.uniform(900, 1013),
                random.uniform(30, 70),
                random.uniform(-180, 180),
                random.uniform(-180, 180),
                random.uniform(-180, 180),
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                13.3379,
                74.7461
            ]
    
    def reset_simulation(self):
        """Reset the flight simulation"""
        if self.use_simulator:
            self.simulator.reset()
            self.last_update = time.time()


class data_base:
    """Mock database class for testing"""
    
    def __init__(self):
        self.recording = False
        self.data_log = []
        self.filename = None
    
    def start(self):
        """Start recording data"""
        self.recording = True
        self.data_log = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"cansat_test_data_{timestamp}.csv"
        print(f"Started recording to {self.filename}")
    
    def stop(self):
        """Stop recording and save data"""
        self.recording = False
        if self.data_log and self.filename:
            import pandas as pd
            df = pd.DataFrame(self.data_log, columns=[
                'Time', 'Altitude', 'Temperature', 'Pressure', 'Humidity',
                'Gyro_X', 'Gyro_Y', 'Gyro_Z',
                'Accel_X', 'Accel_Y', 'Accel_Z',
                'Latitude', 'Longitude'
            ])
            df.to_csv(self.filename, index=False)
            print(f"Saved {len(self.data_log)} data points to {self.filename}")
    
    def guardar(self, data):
        """Save data point"""
        if self.recording:
            self.data_log.append(data)


if __name__ == "__main__":
    # Test the simulator
    print("Testing Flight Simulator...")
    print("-" * 50)
    
    sim = FlightSimulator()
    
    # Simulate a complete flight
    for i in range(250):  # 250 seconds
        data = sim.update(1.0)
        
        # Print every 10 seconds
        if i % 10 == 0:
            print(f"T={data[0]:6.1f}s | Phase: {sim.phase:12s} | "
                  f"Alt={data[1]:6.1f}m | Vel={sim.velocity:6.2f}m/s | "
                  f"Gyro=({data[5]:5.1f}, {data[6]:5.1f}, {data[7]:5.1f})")
    
    print("-" * 50)
    print("Simulation complete!")
