#!/usr/bin/env python3
"""
Database setup script for Green Engine
Creates database schema and initializes tables
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_schema():
    """Create the complete database schema"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'green_engine'),
        'user': os.getenv('DB_USER', 'green_user'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Create TimescaleDB extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        logger.info("TimescaleDB extension created")
        
        # Create sensor_readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                sensor_id VARCHAR(50) NOT NULL,
                location VARCHAR(50) NOT NULL,
                sensor_type VARCHAR(20) NOT NULL CHECK (sensor_type IN ('temperature', 'humidity', 'light', 'soil_moisture', 'ec', 'co2')),
                value DECIMAL(10,3) NOT NULL,
                unit VARCHAR(10) NOT NULL,
                battery INTEGER CHECK (battery >= 0 AND battery <= 100),
                signal_strength INTEGER CHECK (signal_strength >= -100 AND signal_strength <= 0),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                
                CONSTRAINT idx_sensor_readings_timestamp UNIQUE (timestamp, sensor_id)
            );
        """)
        logger.info("sensor_readings table created")
        
        # Create processed_features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_features (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location VARCHAR(50) NOT NULL,
                
                -- Temperature features
                temp_avg_1h DECIMAL(5,2),
                temp_min_1h DECIMAL(5,2),
                temp_max_1h DECIMAL(5,2),
                temp_std_1h DECIMAL(5,2),
                temp_avg_24h DECIMAL(5,2),
                temp_variance_24h DECIMAL(5,2),
                
                -- Humidity features
                humidity_avg_1h DECIMAL(5,2),
                humidity_min_1h DECIMAL(5,2),
                humidity_max_1h DECIMAL(5,2),
                humidity_std_1h DECIMAL(5,2),
                
                -- Light features
                light_sum_1h DECIMAL(10,2),
                light_avg_1h DECIMAL(10,2),
                light_max_1h DECIMAL(10,2),
                light_variance_24h DECIMAL(10,2),
                light_hours_above_threshold INTEGER,
                
                -- Soil features
                soil_moisture_avg_1h DECIMAL(5,2),
                soil_moisture_min_1h DECIMAL(5,2),
                soil_moisture_max_1h DECIMAL(5,2),
                ec_avg_1h DECIMAL(5,2),
                ec_min_1h DECIMAL(5,2),
                ec_max_1h DECIMAL(5,2),
                
                -- CO2 features
                co2_avg_1h DECIMAL(6,2),
                co2_min_1h DECIMAL(6,2),
                co2_max_1h DECIMAL(6,2),
                co2_std_1h DECIMAL(6,2),
                
                -- Derived features
                temp_humidity_ratio DECIMAL(8,4),
                light_temp_ratio DECIMAL(10,4),
                vpd DECIMAL(6,2),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("processed_features table created")
        
        # Create growth_measurements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_measurements (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location VARCHAR(50) NOT NULL,
                tray_id VARCHAR(50) NOT NULL,
                crop_type VARCHAR(50) NOT NULL,
                
                -- Growth metrics
                plant_height_cm DECIMAL(5,2),
                leaf_count INTEGER,
                biomass_g DECIMAL(8,3),
                yield_g DECIMAL(8,3),
                germination_rate DECIMAL(5,2),
                
                -- Growth stage
                growth_stage VARCHAR(20) CHECK (growth_stage IN ('germination', 'vegetative', 'mature', 'harvest')),
                days_since_planting INTEGER,
                
                -- Quality metrics
                color_rating INTEGER CHECK (color_rating >= 1 AND color_rating <= 5),
                uniformity_rating INTEGER CHECK (uniformity_rating >= 1 AND uniformity_rating <= 5),
                notes TEXT,
                
                created_at TIMESTAMPTZ DEFAULT NOW(),
                created_by VARCHAR(50)
            );
        """)
        logger.info("growth_measurements table created")
        
        # Create ml_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location VARCHAR(50) NOT NULL,
                model_name VARCHAR(50) NOT NULL,
                model_version VARCHAR(20) NOT NULL,
                prediction_type VARCHAR(30) NOT NULL CHECK (prediction_type IN ('short_term_forecast', 'long_term_yield', 'anomaly_score')),
                
                -- Prediction values
                predicted_value DECIMAL(10,3),
                confidence_interval_lower DECIMAL(10,3),
                confidence_interval_upper DECIMAL(10,3),
                anomaly_score DECIMAL(5,4),
                
                -- Model metadata
                features_used JSONB,
                model_performance_metrics JSONB,
                
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("ml_predictions table created")
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location VARCHAR(50) NOT NULL,
                alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN ('anomaly', 'threshold', 'system', 'maintenance')),
                severity VARCHAR(10) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
                
                -- Alert details
                title VARCHAR(200) NOT NULL,
                description TEXT,
                sensor_id VARCHAR(50),
                sensor_type VARCHAR(20),
                threshold_value DECIMAL(10,3),
                actual_value DECIMAL(10,3),
                
                -- Status
                status VARCHAR(15) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
                acknowledged_at TIMESTAMPTZ,
                resolved_at TIMESTAMPTZ,
                acknowledged_by VARCHAR(50),
                
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("alerts table created")
        
        # Create alert_actions table (audit log for alert acknowledgements/resolutions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_actions (
                id SERIAL PRIMARY KEY,
                alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
                action VARCHAR(20) NOT NULL CHECK (action IN ('acknowledged', 'resolved')),
                actor VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("alert_actions table created")
        
        # Create device_commands table (audit log for actuator commands)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_commands (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(100) NOT NULL,
                location VARCHAR(50),
                command JSONB NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (status IN ('queued','sent','failed','acknowledged')),
                response JSONB,
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TIMESTAMPTZ,
                next_attempt_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                created_by VARCHAR(50)
            );
        """)
        logger.info("device_commands table created")

        # Create trays table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trays (
                id SERIAL PRIMARY KEY,
                tray_code TEXT UNIQUE NOT NULL,
                location VARCHAR(50) NOT NULL,
                device_id TEXT,
                crop_type VARCHAR(50),
                grow_medium TEXT,
                batch_code TEXT,
                seed_density INTEGER,
                lighting_profile TEXT,
                planted_on DATE,
                expected_harvest DATE,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("trays table created")
        
        # Create system_config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value JSONB NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("system_config table created")
        
        # Convert tables to hypertables
        try:
            cursor.execute("SELECT create_hypertable('sensor_readings', 'timestamp', chunk_time_interval => INTERVAL '1 day');")
            logger.info("sensor_readings converted to hypertable")
        except Exception as e:
            logger.info(f"sensor_readings hypertable already exists: {e}")
        
        try:
            cursor.execute("SELECT create_hypertable('processed_features', 'timestamp', chunk_time_interval => INTERVAL '1 day');")
            logger.info("processed_features converted to hypertable")
        except Exception as e:
            logger.info(f"processed_features hypertable already exists: {e}")
        
        try:
            cursor.execute("SELECT create_hypertable('ml_predictions', 'timestamp', chunk_time_interval => INTERVAL '1 day');")
            logger.info("ml_predictions converted to hypertable")
        except Exception as e:
            logger.info(f"ml_predictions hypertable already exists: {e}")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_id ON sensor_readings (sensor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_location ON sensor_readings (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_type ON sensor_readings (sensor_type);")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_features_location ON processed_features (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_features_timestamp ON processed_features (timestamp);")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_growth_measurements_location ON growth_measurements (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_growth_measurements_tray_id ON growth_measurements (tray_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_growth_measurements_crop_type ON growth_measurements (crop_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_growth_measurements_timestamp ON growth_measurements (timestamp);")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_predictions_location ON ml_predictions (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_predictions_model_name ON ml_predictions (model_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_predictions_prediction_type ON ml_predictions (prediction_type);")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_location ON alerts (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON alerts (alert_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_commands_status ON device_commands (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_commands_next_attempt ON device_commands (next_attempt_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trays_location ON trays (location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trays_crop_type ON trays (crop_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trays_batch_code ON trays (batch_code);")
        
        logger.info("All indexes created")
        
        # Insert default configurations
        cursor.execute("""
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('sensor_thresholds', '{"temperature": {"min": 15, "max": 30}, "humidity": {"min": 40, "max": 80}, "soil_moisture": {"min": 20, "max": 80}, "light": {"min": 100, "max": 1000}, "co2": {"min": 400, "max": 1500}}', 'Sensor threshold values for alerts')
            ON CONFLICT (config_key) DO NOTHING;
        """)
        
        cursor.execute("""
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('ml_model_config', '{"forecast_horizon": 72, "retrain_frequency": "daily", "confidence_level": 0.95}', 'Machine learning model configuration')
            ON CONFLICT (config_key) DO NOTHING;
        """)
        
        cursor.execute("""
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('dashboard_config', '{"refresh_interval": 30, "chart_time_range": "24h", "max_data_points": 1000}', 'Dashboard display configuration')
            ON CONFLICT (config_key) DO NOTHING;
        """)
        
        cursor.execute("""
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('notification_config', '{"email_enabled": true, "sms_enabled": false, "webhook_url": null}', 'Notification system configuration')
            ON CONFLICT (config_key) DO NOTHING;
        """)
        
        logger.info("Default configurations inserted")
        
        # Commit changes
        conn.commit()
        logger.info("Database schema created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")
        raise
    finally:
        if conn:
            conn.close()

def insert_sample_data():
    """Insert sample data for testing"""
    
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'green_engine'),
        'user': os.getenv('DB_USER', 'green_user'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Insert sample sensor readings
        cursor.execute("""
            INSERT INTO sensor_readings (timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength) VALUES
            (NOW() - INTERVAL '1 hour', 'temp_001', 'greenhouse_a', 'temperature', 23.5, 'celsius', 85, -45),
            (NOW() - INTERVAL '1 hour', 'humidity_001', 'greenhouse_a', 'humidity', 65.2, 'percent', 90, -42),
            (NOW() - INTERVAL '1 hour', 'light_001', 'greenhouse_a', 'light', 450.0, 'lux', 88, -48),
            (NOW() - INTERVAL '1 hour', 'soil_001', 'greenhouse_a', 'soil_moisture', 35.8, 'percent', 92, -40),
            (NOW() - INTERVAL '1 hour', 'co2_001', 'greenhouse_a', 'co2', 650.0, 'ppm', 87, -44)
            ON CONFLICT DO NOTHING;
        """)
        
        # Insert sample growth measurements
        cursor.execute("""
            INSERT INTO growth_measurements (timestamp, location, tray_id, crop_type, plant_height_cm, leaf_count, biomass_g, yield_g, germination_rate, growth_stage, days_since_planting, color_rating, uniformity_rating) VALUES
            (NOW() - INTERVAL '1 day', 'greenhouse_a', 'tray_001', 'pea_shoots', 8.5, 12, 45.2, 42.1, 95.0, 'mature', 10, 4, 4),
            (NOW() - INTERVAL '1 day', 'greenhouse_a', 'tray_002', 'sunflower', 12.3, 8, 78.9, 75.2, 92.0, 'mature', 12, 5, 4)
            ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
        logger.info("Sample data inserted successfully")
        
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Setting up Green Engine database...")
    create_database_schema()
    insert_sample_data()
    print("Database setup completed successfully!")
