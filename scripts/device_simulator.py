#!/usr/bin/env python3
"""
Warif Device Simulator
Simulates real IoT devices sending MQTT telemetry data
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime, timedelta
import os
import sys
import signal
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeviceSimulator:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.devices = {}
        self.running = False
        self.client = None
        
        # Initialize simulated devices
        self._initialize_devices()
        
    def _initialize_devices(self):
        """Initialize simulated IoT devices"""
        self.devices = {
            "GH-A1-DEV-01": {
                "location": "greenhouse_a",
                "device_type": "sensor_hub",
                "firmware_version": "1.2.3",
                "battery_level": 95,
                "signal_strength": 85,
                "last_seen": datetime.now(),
                "sensor_config": {
                    "temperature": {"min": 18, "max": 28, "unit": "°C"},
                    "humidity": {"min": 60, "max": 80, "unit": "%"},
                    "light": {"min": 400, "max": 600, "unit": "μmol/m²/s"},
                    "soil_moisture": {"min": 30, "max": 50, "unit": "%"},
                    "ec": {"min": 1.0, "max": 2.0, "unit": "mS/cm"},
                    "co2": {"min": 400, "max": 800, "unit": "ppm"}
                }
            },
            "GH-A1-DEV-02": {
                "location": "greenhouse_a",
                "device_type": "sensor_hub",
                "firmware_version": "1.2.3",
                "battery_level": 88,
                "signal_strength": 92,
                "last_seen": datetime.now(),
                "sensor_config": {
                    "temperature": {"min": 18, "max": 28, "unit": "°C"},
                    "humidity": {"min": 60, "max": 80, "unit": "%"},
                    "light": {"min": 400, "max": 600, "unit": "μmol/m²/s"},
                    "soil_moisture": {"min": 30, "max": 50, "unit": "%"},
                    "ec": {"min": 1.0, "max": 2.0, "unit": "mS/cm"},
                    "co2": {"min": 400, "max": 800, "unit": "ppm"}
                }
            },
            "GH-B1-DEV-01": {
                "location": "greenhouse_b",
                "device_type": "sensor_hub",
                "firmware_version": "1.1.8",
                "battery_level": 76,
                "signal_strength": 78,
                "last_seen": datetime.now(),
                "sensor_config": {
                    "temperature": {"min": 18, "max": 28, "unit": "°C"},
                    "humidity": {"min": 60, "max": 80, "unit": "%"},
                    "light": {"min": 400, "max": 600, "unit": "μmol/m²/s"},
                    "soil_moisture": {"min": 30, "max": 50, "unit": "%"},
                    "ec": {"min": 1.0, "max": 2.0, "unit": "mS/cm"},
                    "co2": {"min": 400, "max": 800, "unit": "ppm"}
                }
            }
        }
        
        logger.info(f"Initialized {len(self.devices)} simulated devices")
    
    def _generate_realistic_sensor_data(self, device_id: str) -> Dict:
        """Generate realistic sensor data for a device"""
        device = self.devices[device_id]
        config = device["sensor_config"]
        current_time = datetime.now()
        
        # Add time-based variations (day/night cycles)
        hour = current_time.hour
        is_daytime = 6 <= hour <= 18
        
        readings = {}
        
        for sensor_type, sensor_config in config.items():
            base_value = random.uniform(sensor_config["min"], sensor_config["max"])
            
            # Add realistic time-based variations
            if sensor_type == "temperature":
                if is_daytime:
                    base_value += random.uniform(2, 4)  # Warmer during day
                else:
                    base_value -= random.uniform(1, 3)  # Cooler at night
                    
            elif sensor_type == "light":
                if not is_daytime:
                    base_value = 0  # No light at night
                else:
                    # Peak light at noon
                    noon_diff = abs(hour - 12)
                    base_value += (6 - noon_diff) * 20
                    
            elif sensor_type == "humidity":
                if not is_daytime:
                    base_value += random.uniform(5, 10)  # Higher humidity at night
                    
            elif sensor_type == "soil_moisture":
                # Gradual decrease over time (simulating water consumption)
                base_value -= random.uniform(0.1, 0.3)
                base_value = max(sensor_config["min"], base_value)
                
            elif sensor_type == "ec":
                # Slight variations in electrical conductivity
                base_value += random.uniform(-0.1, 0.1)
                
            elif sensor_type == "co2":
                # CO2 levels vary with plant activity
                if is_daytime:
                    base_value -= random.uniform(10, 30)  # Plants consume CO2 during day
                else:
                    base_value += random.uniform(5, 15)   # Plants release CO2 at night
            
            # Add some random noise
            noise = random.uniform(-sensor_config["min"]*0.05, sensor_config["max"]*0.05)
            final_value = base_value + noise
            final_value = max(sensor_config["min"], min(sensor_config["max"], final_value))
            
            readings[sensor_type] = round(final_value, 2)
        
        # Update device status
        device["battery_level"] = max(10, device["battery_level"] - random.uniform(0.01, 0.05))
        device["signal_strength"] = max(50, device["signal_strength"] + random.uniform(-2, 2))
        device["last_seen"] = current_time
        
        return readings
    
    def _create_telemetry_message(self, device_id: str) -> Dict:
        """Create a telemetry message for a device"""
        device = self.devices[device_id]
        readings = self._generate_realistic_sensor_data(device_id)
        
        message = {
            "device_id": device_id,
            "location": device["location"],
            "timestamp": datetime.now().isoformat(),
            "readings": readings,
            "battery": round(device["battery_level"], 1),
            "firmware_version": device["firmware_version"],
            "signal_strength": round(device["signal_strength"], 1),
            "device_type": device["device_type"]
        }
        
        return message
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info("✅ Connected to MQTT broker successfully")
            # Subscribe to command topics for each device
            for device_id in self.devices.keys():
                command_topic = f"warif/{device_id}/cmd"
                client.subscribe(command_topic)
                logger.info(f"📡 Subscribed to command topic: {command_topic}")
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"📨 Received command on {topic}: {payload}")
            
            # Extract device ID from topic
            device_id = topic.split('/')[1]
            
            if device_id in self.devices:
                # Simulate device response to command
                self._simulate_command_response(device_id, payload)
            
        except Exception as e:
            logger.error(f"❌ Error processing command message: {e}")
    
    def _simulate_command_response(self, device_id: str, command: Dict):
        """Simulate device response to a command"""
        device = self.devices[device_id]
        
        # Simulate command execution
        command_type = command.get("action", "unknown")
        
        if command_type == "irrigate":
            # Simulate irrigation - increase soil moisture
            device["sensor_config"]["soil_moisture"]["min"] = 45
            device["sensor_config"]["soil_moisture"]["max"] = 55
            logger.info(f"💧 Device {device_id} executing irrigation command")
            
        elif command_type == "ventilate":
            # Simulate ventilation - decrease temperature and humidity
            device["sensor_config"]["temperature"]["max"] = 24
            device["sensor_config"]["humidity"]["max"] = 75
            logger.info(f"🌪️ Device {device_id} executing ventilation command")
            
        elif command_type == "light_on":
            # Simulate turning on lights
            device["sensor_config"]["light"]["min"] = 500
            device["sensor_config"]["light"]["max"] = 700
            logger.info(f"💡 Device {device_id} turning on lights")
            
        elif command_type == "light_off":
            # Simulate turning off lights
            device["sensor_config"]["light"]["min"] = 0
            device["sensor_config"]["light"]["max"] = 50
            logger.info(f"🌙 Device {device_id} turning off lights")
    
    def _publish_telemetry(self, device_id: str):
        """Publish telemetry data for a device"""
        try:
            message = self._create_telemetry_message(device_id)
            topic = f"warif/{device_id}/telemetry"
            
            # Publish with QoS 1 for reliability
            result = self.client.publish(topic, json.dumps(message), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"📤 Published telemetry for {device_id}: {message['readings']}")
            else:
                logger.error(f"❌ Failed to publish telemetry for {device_id}")
                
        except Exception as e:
            logger.error(f"❌ Error publishing telemetry for {device_id}: {e}")
    
    def _device_worker(self, device_id: str, interval: float = 30.0):
        """Worker thread for a single device"""
        logger.info(f"🚀 Starting device worker for {device_id} (interval: {interval}s)")
        
        while self.running:
            try:
                self._publish_telemetry(device_id)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"❌ Error in device worker for {device_id}: {e}")
                time.sleep(5)  # Wait before retrying
    
    def start_simulation(self, telemetry_interval: float = 30.0):
        """Start the device simulation"""
        logger.info("🚀 Starting Warif Device Simulation...")
        
        # Create MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        try:
            # Connect to broker
            logger.info(f"🔌 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the client loop
            self.client.loop_start()
            
            # Wait for connection
            time.sleep(2)
            
            self.running = True
            
            # Start device worker threads
            threads = []
            for device_id in self.devices.keys():
                thread = threading.Thread(
                    target=self._device_worker,
                    args=(device_id, telemetry_interval),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
                logger.info(f"📡 Started worker for device: {device_id}")
            
            logger.info(f"✅ Device simulation started with {len(self.devices)} devices")
            logger.info(f"📊 Telemetry interval: {telemetry_interval} seconds")
            logger.info("🔄 Press Ctrl+C to stop simulation")
            
            # Keep the main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, stopping simulation...")
                self.stop_simulation()
                
        except Exception as e:
            logger.error(f"❌ Failed to start simulation: {e}")
            self.stop_simulation()
    
    def stop_simulation(self):
        """Stop the device simulation"""
        logger.info("🛑 Stopping device simulation...")
        self.running = False
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🔌 Disconnected from MQTT broker")
        
        logger.info("✅ Device simulation stopped")
    
    def get_device_status(self) -> Dict:
        """Get status of all simulated devices"""
        status = {}
        for device_id, device in self.devices.items():
            status[device_id] = {
                "location": device["location"],
                "battery_level": round(device["battery_level"], 1),
                "signal_strength": round(device["signal_strength"], 1),
                "firmware_version": device["firmware_version"],
                "last_seen": device["last_seen"].isoformat(),
                "device_type": device["device_type"]
            }
        return status

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("🛑 Received interrupt signal")
    if 'simulator' in globals():
        simulator.stop_simulation()
    sys.exit(0)

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Warif Device Simulator")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--interval", type=float, default=30.0, help="Telemetry interval in seconds")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start simulator
    global simulator
    simulator = DeviceSimulator(args.broker, args.port)
    
    try:
        simulator.start_simulation(args.interval)
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
