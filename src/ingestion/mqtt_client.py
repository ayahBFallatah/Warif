"""
MQTT Client for Green Engine Sensor Data Ingestion
Handles real-time sensor data collection from IoT devices
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from src.utils.rules_engine import RulesEngine, ReadingContext

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorReading(BaseModel):
    """Pydantic model for sensor data validation"""
    timestamp: datetime
    sensor_id: str = Field(..., min_length=1, max_length=50)
    location: str = Field(..., min_length=1, max_length=50)
    sensor_type: str = Field(..., regex='^(temperature|humidity|light|soil_moisture|ec|co2)$')
    value: float = Field(..., ge=-100, le=10000)
    unit: str = Field(..., min_length=1, max_length=10)
    battery: Optional[int] = Field(None, ge=0, le=100)
    signal_strength: Optional[int] = Field(None, ge=-100, le=0)

class GreenEngineMQTTClient:
    """MQTT client for ingesting sensor data from IoT devices"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.db_connection = None
        self.setup_mqtt_callbacks()
        self.setup_database()
    
    def setup_mqtt_callbacks(self):
        """Configure MQTT client callbacks"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def setup_database(self):
        """Initialize database connection"""
        try:
            self.db_connection = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "green_engine"),
                user=os.getenv("DB_USER", "green_user"),
                password=os.getenv("DB_PASSWORD", "password"),
                port=os.getenv("DB_PORT", "5432")
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to sensor topics
            topics = [
                "sensors/+/+/+",  # sensors/location/sensor_type/sensor_id
                "greenhouse/+/sensors/+",  # Alternative topic structure
            ]
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received from MQTT broker"""
        try:
            logger.info(f"Received message on topic: {msg.topic}")
            
            # Parse JSON payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Validate sensor data
            sensor_data = SensorReading(**payload)
            
            # Store in database
            self.store_sensor_reading(sensor_data)
            
            logger.info(f"Successfully processed sensor reading: {sensor_data.sensor_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def store_sensor_reading(self, sensor_data: SensorReading):
        """Store sensor reading in PostgreSQL database"""
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                INSERT INTO sensor_readings 
                (timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    sensor_data.timestamp,
                    sensor_data.sensor_id,
                    sensor_data.location,
                    sensor_data.sensor_type,
                    sensor_data.value,
                    sensor_data.unit,
                    sensor_data.battery,
                    sensor_data.signal_strength
                ))
                self.db_connection.commit()
            # Evaluate rules and store alerts (non-blocking with best effort)
            try:
                rules_engine = RulesEngine()
                rules_engine.evaluate_and_store(
                    ReadingContext(
                        timestamp=sensor_data.timestamp,
                        location=sensor_data.location,
                        sensor_type=sensor_data.sensor_type,
                        value=sensor_data.value,
                    )
                )
            except Exception as re:
                logger.error(f"Rules evaluation failed: {re}")

        except Exception as e:
            logger.error(f"Database error storing sensor reading: {e}")
            self.db_connection.rollback()
    
    def start(self):
        """Start the MQTT client"""
        try:
            # Connect to MQTT broker
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the loop
            self.client.loop_start()
            logger.info("MQTT client started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT client"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            if self.db_connection:
                self.db_connection.close()
            logger.info("MQTT client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping MQTT client: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Create and start MQTT client
    mqtt_client = GreenEngineMQTTClient()
    
    try:
        mqtt_client.start()
        
        # Keep the client running
        while True:
            asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down MQTT client...")
        mqtt_client.stop()
