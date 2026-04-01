# Green Engine: Data Schema & SQL Tables

## Database Overview
The Green Engine system uses PostgreSQL with TimescaleDB extension for efficient time-series data storage and querying. The schema is designed to handle high-frequency sensor data, processed features, and machine learning predictions.

## Core Tables

### 1. Raw Sensor Data
```sql
-- Raw sensor readings from IoT devices
CREATE TABLE sensor_readings (
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
    
    -- Indexes for efficient querying
    CONSTRAINT idx_sensor_readings_timestamp UNIQUE (timestamp, sensor_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('sensor_readings', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for common queries
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings (sensor_id);
CREATE INDEX idx_sensor_readings_location ON sensor_readings (location);
CREATE INDEX idx_sensor_readings_sensor_type ON sensor_readings (sensor_type);
```

### 2. Processed Features
```sql
-- Hourly aggregated features for ML models
CREATE TABLE processed_features (
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
    vpd DECIMAL(6,2), -- Vapor Pressure Deficit
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('processed_features', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Indexes
CREATE INDEX idx_processed_features_location ON processed_features (location);
CREATE INDEX idx_processed_features_timestamp ON processed_features (timestamp);
```

### 3. Growth Measurements
```sql
-- Manual growth measurements and yield data
CREATE TABLE growth_measurements (
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

-- Indexes
CREATE INDEX idx_growth_measurements_location ON growth_measurements (location);
CREATE INDEX idx_growth_measurements_tray_id ON growth_measurements (tray_id);
CREATE INDEX idx_growth_measurements_crop_type ON growth_measurements (crop_type);
CREATE INDEX idx_growth_measurements_timestamp ON growth_measurements (timestamp);
```

### 4. ML Predictions
```sql
-- Machine learning model predictions
CREATE TABLE ml_predictions (
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

-- Convert to hypertable
SELECT create_hypertable('ml_predictions', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Indexes
CREATE INDEX idx_ml_predictions_location ON ml_predictions (location);
CREATE INDEX idx_ml_predictions_model_name ON ml_predictions (model_name);
CREATE INDEX idx_ml_predictions_prediction_type ON ml_predictions (prediction_type);
```

### 5. Alerts and Notifications
```sql
-- System alerts and notifications
CREATE TABLE alerts (
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

-- Indexes
CREATE INDEX idx_alerts_location ON alerts (location);
CREATE INDEX idx_alerts_alert_type ON alerts (alert_type);
CREATE INDEX idx_alerts_severity ON alerts (severity);
CREATE INDEX idx_alerts_status ON alerts (status);
CREATE INDEX idx_alerts_timestamp ON alerts (timestamp);
```

### 6. System Configuration
```sql
-- System configuration and settings
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default configurations
INSERT INTO system_config (config_key, config_value, description) VALUES
('sensor_thresholds', '{"temperature": {"min": 15, "max": 30}, "humidity": {"min": 40, "max": 80}, "soil_moisture": {"min": 20, "max": 80}, "light": {"min": 100, "max": 1000}, "co2": {"min": 400, "max": 1500}}', 'Sensor threshold values for alerts'),
('ml_model_config', '{"forecast_horizon": 72, "retrain_frequency": "daily", "confidence_level": 0.95}', 'Machine learning model configuration'),
('dashboard_config', '{"refresh_interval": 30, "chart_time_range": "24h", "max_data_points": 1000}', 'Dashboard display configuration'),
('notification_config', '{"email_enabled": true, "sms_enabled": false, "webhook_url": null}', 'Notification system configuration');
```

## Sample Data

### Example Sensor Readings
```sql
INSERT INTO sensor_readings (timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength) VALUES
('2024-01-15 10:00:00+00', 'temp_001', 'greenhouse_a', 'temperature', 23.5, 'celsius', 85, -45),
('2024-01-15 10:00:00+00', 'humidity_001', 'greenhouse_a', 'humidity', 65.2, 'percent', 90, -42),
('2024-01-15 10:00:00+00', 'light_001', 'greenhouse_a', 'light', 450.0, 'lux', 88, -48),
('2024-01-15 10:00:00+00', 'soil_001', 'greenhouse_a', 'soil_moisture', 35.8, 'percent', 92, -40),
('2024-01-15 10:00:00+00', 'co2_001', 'greenhouse_a', 'co2', 650.0, 'ppm', 87, -44);
```

### Example Growth Measurements
```sql
INSERT INTO growth_measurements (timestamp, location, tray_id, crop_type, plant_height_cm, leaf_count, biomass_g, yield_g, germination_rate, growth_stage, days_since_planting, color_rating, uniformity_rating) VALUES
('2024-01-15 14:00:00+00', 'greenhouse_a', 'tray_001', 'pea_shoots', 8.5, 12, 45.2, 42.1, 95.0, 'mature', 10, 4, 4),
('2024-01-15 14:00:00+00', 'greenhouse_a', 'tray_002', 'sunflower', 12.3, 8, 78.9, 75.2, 92.0, 'mature', 12, 5, 4);
```

### Example ML Predictions
```sql
INSERT INTO ml_predictions (timestamp, location, model_name, model_version, prediction_type, predicted_value, confidence_interval_lower, confidence_interval_upper, anomaly_score) VALUES
('2024-01-15 10:00:00+00', 'greenhouse_a', 'temperature_forecast', 'v1.0', 'short_term_forecast', 24.2, 23.1, 25.3, NULL),
('2024-01-15 10:00:00+00', 'greenhouse_a', 'anomaly_detection', 'v1.0', 'anomaly_score', NULL, NULL, NULL, 0.023);
```

## Data Retention Policy
- **Raw sensor data**: 90 days (then archived)
- **Processed features**: 1 year
- **ML predictions**: 6 months
- **Alerts**: 1 year
- **Growth measurements**: Permanent

## Backup Strategy
- **Daily**: Automated backups to cloud storage
- **Weekly**: Full database backup with verification
- **Monthly**: Disaster recovery testing
