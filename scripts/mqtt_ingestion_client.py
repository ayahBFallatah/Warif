#!/usr/bin/env python3
"""
Green Engine MQTT Ingestion Client
Receives MQTT telemetry data from devices and stores it in the database
"""

import paho.mqtt.client as mqtt
import json
import psycopg2
import logging
import time
import sys
import signal
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MQTTIngestionClient:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.running = False
        self.db_connection = None
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            if not self.db_connection or self.db_connection.closed:
                self.db_connection = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    database=os.getenv("DB_NAME", "green_engine"),
                    user=os.getenv("DB_USER", "green_user"),
                    password=os.getenv("DB_PASSWORD", "password"),
                    port=os.getenv("DB_PORT", "5432")
                )
            return self.db_connection
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            return None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info("✅ Connected to MQTT broker successfully")
            # Subscribe to all telemetry topics
            client.subscribe("greenengine/+/telemetry", qos=1)
            logger.info("📡 Subscribed to telemetry topics: greenengine/+/telemetry")
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"📨 Received telemetry from {topic}")
            
            # Process the telemetry data
            self._process_telemetry_data(payload)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in message from {topic}: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message from {topic}: {e}")
    
    def _process_telemetry_data(self, data: Dict[str, Any]):
        """Process and store telemetry data in the database"""
        try:
            device_id = data.get("device_id")
            location = data.get("location")
            timestamp = data.get("timestamp")
            readings = data.get("readings", {})
            battery = data.get("battery", 0)
            signal_strength = data.get("signal_strength", 0)
            
            if not all([device_id, location, timestamp, readings]):
                logger.error("❌ Missing required fields in telemetry data")
                return
            
            # Parse timestamp
            try:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif isinstance(timestamp, datetime):
                    pass
                else:
                    timestamp = datetime.now()
            except Exception as e:
                logger.error(f"❌ Error parsing timestamp: {e}")
                timestamp = datetime.now()
            
            # Store each sensor reading
            conn = self.get_db_connection()
            if not conn:
                logger.error("❌ No database connection available")
                return
            
            cursor = conn.cursor()
            
            for sensor_type, value in readings.items():
                try:
                    # Insert sensor reading
                    cursor.execute("""
                        INSERT INTO sensor_readings 
                        (timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        timestamp,
                        device_id,
                        location,
                        sensor_type,
                        value,
                        self._get_sensor_unit(sensor_type),
                        battery,
                        signal_strength
                    ))
                    
                    logger.debug(f"📊 Stored {sensor_type} reading: {value} for {device_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Error storing {sensor_type} reading: {e}")
                    conn.rollback()
                    continue
            
            # Commit all readings for this device
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Successfully stored {len(readings)} sensor readings for {device_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing telemetry data: {e}")
            if conn:
                conn.rollback()
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """Get the unit for a sensor type"""
        units = {
            "temperature": "°C",
            "humidity": "%",
            "light": "μmol/m²/s",
            "soil_moisture": "%",
            "ec": "mS/cm",
            "co2": "ppm"
        }
        return units.get(sensor_type, "unknown")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects"""
        if rc != 0:
            logger.warning(f"⚠️ Unexpected disconnection from MQTT broker. Return code: {rc}")
        else:
            logger.info("🔌 Disconnected from MQTT broker")
    
    def start_ingestion(self):
        """Start the MQTT ingestion client"""
        logger.info("🚀 Starting MQTT Ingestion Client...")
        
        # Create MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        try:
            # Connect to broker
            logger.info(f"🔌 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the client loop
            self.client.loop_start()
            
            # Wait for connection
            time.sleep(2)
            
            self.running = True
            logger.info("✅ MQTT ingestion client started successfully")
            logger.info("🔄 Listening for telemetry data...")
            logger.info("🛑 Press Ctrl+C to stop")
            
            # Keep the main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, stopping ingestion...")
                self.stop_ingestion()
                
        except Exception as e:
            logger.error(f"❌ Failed to start ingestion client: {e}")
            self.stop_ingestion()
    
    def stop_ingestion(self):
        """Stop the MQTT ingestion client"""
        logger.info("🛑 Stopping MQTT ingestion client...")
        self.running = False
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🔌 Disconnected from MQTT broker")
        
        if self.db_connection:
            self.db_connection.close()
            logger.info("🔌 Closed database connection")
        
        logger.info("✅ MQTT ingestion client stopped")
    
    def get_ingestion_stats(self) -> Dict:
        """Get ingestion statistics"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"error": "No database connection"}
            
            cursor = conn.cursor()
            
            # Get total readings count
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            total_readings = cursor.fetchone()[0]
            
            # Get readings from last hour
            cursor.execute("""
                SELECT COUNT(*) FROM sensor_readings 
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """)
            recent_readings = cursor.fetchone()[0]
            
            # Get unique devices
            cursor.execute("SELECT COUNT(DISTINCT sensor_id) FROM sensor_readings")
            unique_devices = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                "total_readings": total_readings,
                "recent_readings_1h": recent_readings,
                "unique_devices": unique_devices,
                "status": "running" if self.running else "stopped"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting ingestion stats: {e}")
            return {"error": str(e)}

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("🛑 Received interrupt signal")
    if 'ingestion_client' in globals():
        ingestion_client.stop_ingestion()
    sys.exit(0)

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Green Engine MQTT Ingestion Client")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start ingestion client
    global ingestion_client
    ingestion_client = MQTTIngestionClient(args.broker, args.port)
    
    try:
        ingestion_client.start_ingestion()
    except Exception as e:
        logger.error(f"❌ Ingestion client failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
