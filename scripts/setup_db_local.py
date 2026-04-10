#!/usr/bin/env python3
"""
Simplified Warif Database Setup for Local Development
This version doesn't require TimescaleDB extension
"""

import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection"""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            database=os.getenv("DB_NAME", "warif"),
            user=os.getenv("DB_USER", "warif_user"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432")
        )
        print("✅ Connected to database successfully")
        return connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def create_database_schema(connection):
    """Create the database schema without TimescaleDB"""
    try:
        cursor = connection.cursor()
        
        print("🔧 Creating database schema...")
        
        # Create sensor_readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                sensor_id TEXT NOT NULL,
                location TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value DOUBLE PRECISION NOT NULL,
                unit TEXT NOT NULL,
                battery INTEGER,
                signal_strength INTEGER,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create trays table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trays (
                id SERIAL PRIMARY KEY,
                tray_code TEXT UNIQUE NOT NULL,
                location TEXT NOT NULL,
                device_id TEXT,
                crop_type TEXT,
                planted_on DATE,
                expected_harvest DATE,
                grow_medium TEXT,
                batch_code TEXT,
                seed_density DOUBLE PRECISION,
                lighting_profile TEXT,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create growth_measurements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_measurements (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location TEXT NOT NULL,
                tray_id INTEGER REFERENCES trays(id),
                crop_type TEXT,
                plant_height_cm DOUBLE PRECISION,
                biomass_g DOUBLE PRECISION,
                yield_g DOUBLE PRECISION,
                germination_rate DOUBLE PRECISION,
                growth_stage TEXT,
                days_since_planting INTEGER,
                color_rating INTEGER,
                uniformity_rating INTEGER,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create processed_features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_features (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location TEXT NOT NULL,
                temp_avg_1h DOUBLE PRECISION,
                temp_min_1h DOUBLE PRECISION,
                temp_max_1h DOUBLE PRECISION,
                temp_std_1h DOUBLE PRECISION,
                humidity_avg_1h DOUBLE PRECISION,
                humidity_min_1h DOUBLE PRECISION,
                humidity_max_1h DOUBLE PRECISION,
                humidity_std_1h DOUBLE PRECISION,
                light_sum_1h DOUBLE PRECISION,
                light_avg_1h DOUBLE PRECISION,
                light_max_1h DOUBLE PRECISION,
                soil_moisture_avg_1h DOUBLE PRECISION,
                soil_moisture_min_1h DOUBLE PRECISION,
                soil_moisture_max_1h DOUBLE PRECISION,
                ec_avg_1h DOUBLE PRECISION,
                ec_min_1h DOUBLE PRECISION,
                ec_max_1h DOUBLE PRECISION,
                co2_avg_1h DOUBLE PRECISION,
                co2_min_1h DOUBLE PRECISION,
                co2_max_1h DOUBLE PRECISION,
                co2_std_1h DOUBLE PRECISION,
                temp_avg_24h DOUBLE PRECISION,
                temp_variance_24h DOUBLE PRECISION,
                humidity_avg_24h DOUBLE PRECISION,
                humidity_variance_24h DOUBLE PRECISION,
                light_sum_24h DOUBLE PRECISION,
                light_variance_24h DOUBLE PRECISION,
                soil_moisture_avg_24h DOUBLE PRECISION,
                soil_moisture_variance_24h DOUBLE PRECISION,
                ec_avg_24h DOUBLE PRECISION,
                ec_variance_24h DOUBLE PRECISION,
                co2_avg_24h DOUBLE PRECISION,
                co2_variance_24h DOUBLE PRECISION,
                temp_humidity_ratio DOUBLE PRECISION,
                light_temp_ratio DOUBLE PRECISION,
                vpd DOUBLE PRECISION,
                light_hours_above_threshold INTEGER,
                hour INTEGER,
                day_of_week INTEGER,
                is_daytime BOOLEAN,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                sensor_id TEXT,
                sensor_type TEXT,
                threshold_value DOUBLE PRECISION,
                actual_value DOUBLE PRECISION,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create system_config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key TEXT UNIQUE NOT NULL,
                config_value JSONB NOT NULL,
                description TEXT,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create alert_actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_actions (
                id SERIAL PRIMARY KEY,
                alert_id INTEGER REFERENCES alerts(id),
                action_type TEXT NOT NULL,
                action_timestamp TIMESTAMPTZ DEFAULT NOW(),
                user_id TEXT,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create device_commands table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_commands (
                id SERIAL PRIMARY KEY,
                device_id TEXT NOT NULL,
                command_type TEXT NOT NULL,
                command_data JSONB NOT NULL,
                status TEXT DEFAULT 'queued',
                mqtt_topic TEXT,
                mqtt_message TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                next_attempt_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create ml_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                location TEXT NOT NULL,
                tray_id INTEGER REFERENCES trays(id),
                prediction_type TEXT NOT NULL,
                predicted_value DOUBLE PRECISION NOT NULL,
                confidence_interval_lower DOUBLE PRECISION,
                confidence_interval_upper DOUBLE PRECISION,
                model_version TEXT,
                features_used JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create indexes for better performance
        print("🔍 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_location ON sensor_readings(location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_type ON sensor_readings(sensor_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trays_location ON trays(location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_growth_measurements_tray_id ON growth_measurements(tray_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_commands_status ON device_commands(status);")
        
        connection.commit()
        print("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        connection.rollback()
        return False

def insert_initial_config(connection):
    """Insert initial configuration data"""
    try:
        cursor = connection.cursor()
        
        print("⚙️ Inserting initial configuration...")
        
        # Insert default sensor thresholds
        cursor.execute("""
            INSERT INTO system_config (config_key, config_value, description)
            VALUES ('sensor_thresholds', %s, 'Default sensor thresholds for alerts')
            ON CONFLICT (config_key) DO UPDATE SET 
                config_value = EXCLUDED.config_value,
                updated_at = NOW()
        """, (json.dumps({
            "temperature": {"min": 18.0, "max": 26.0, "unit": "°C"},
            "humidity": {"min": 60.0, "max": 80.0, "unit": "%"},
            "light": {"min": 400.0, "max": 600.0, "unit": "μmol/m²/s"},
            "soil_moisture": {"min": 30.0, "max": 50.0, "unit": "%"},
            "ec": {"min": 1.0, "max": 2.0, "unit": "mS/cm"},
            "co2": {"min": 400.0, "max": 800.0, "unit": "ppm"}
        }),))
        
        connection.commit()
        print("✅ Initial configuration inserted")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting initial config: {e}")
        connection.rollback()
        return False

def main():
    """Main function to set up the database"""
    print("🚀 Setting up Warif Database (Local Development)...")
    print("=" * 60)
    
    # Connect to database
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to database")
        return
    
    try:
        # Create schema
        if not create_database_schema(connection):
            return
        
        # Insert initial config
        if not insert_initial_config(connection):
            return
        
        print("\n🎉 Database setup completed successfully!")
        print("=" * 60)
        print("📊 What was created:")
        print("   • sensor_readings table")
        print("   • trays table")
        print("   • growth_measurements table")
        print("   • processed_features table")
        print("   • alerts table")
        print("   • system_config table")
        print("   • alert_actions table")
        print("   • device_commands table")
        print("   • ml_predictions table")
        print("   • Performance indexes")
        print("   • Default sensor thresholds")
        print("\n🔄 Now you can run: python3 scripts/populate_sample_data.py")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        connection.rollback()
    
    finally:
        connection.close()

if __name__ == "__main__":
    import json
    main()
