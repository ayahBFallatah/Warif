# Green Engine: Technical Framework Architecture

## Overview

The Green Engine is designed as a modern, scalable IoT platform with a multi-layered architecture that separates concerns and enables independent scaling, maintenance, and evolution of each layer.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  (Cloud & Dashboard Layer - User Interface & Visualization)     │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│        (API Gateway, Business Logic, Authentication)             │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    AI/ML LAYER                                   │
│     (Analytics, Predictions, Anomaly Detection, Optimization)    │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
│         (Time-Series DB, Feature Store, Model Registry)          │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                   IOT DEVICE LAYER                               │
│        (Sensors, Actuators, Edge Devices, MQTT Broker)           │
└─────────────────────────────────────────────────────────────────┘
```

---

# LAYER 1: IoT-Based Layer (Edge & Device Layer)

## 1.1 Physical Components

### **Sensors (Data Collection)**
```
Environmental Sensors:
├── Temperature Sensors (DHT22, DS18B20)
│   ├── Range: -40°C to +80°C
│   ├── Accuracy: ±0.5°C
│   └── Sampling Rate: 1 Hz
│
├── Humidity Sensors (DHT22, SHT31)
│   ├── Range: 0-100% RH
│   ├── Accuracy: ±2% RH
│   └── Sampling Rate: 1 Hz
│
├── Light/PAR Sensors (BH1750, Apogee SQ-500)
│   ├── Range: 0-2000 μmol/m²/s
│   ├── Spectral Range: 400-700nm (PAR)
│   └── Sampling Rate: 0.1 Hz
│
├── CO2 Sensors (MH-Z19B, SCD30)
│   ├── Range: 400-5000 ppm
│   ├── Accuracy: ±50 ppm
│   └── Sampling Rate: 0.05 Hz (every 20s)
│
├── Soil Moisture Sensors (Capacitive)
│   ├── Range: 0-100%
│   ├── Depth: 10cm
│   └── Sampling Rate: 0.1 Hz
│
├── EC/TDS Sensors (DFRobot)
│   ├── Range: 0-10 mS/cm
│   ├── For nutrient monitoring
│   └── Sampling Rate: 0.1 Hz
│
└── pH Sensors (Atlas Scientific)
    ├── Range: 0-14 pH
    ├── Accuracy: ±0.1 pH
    └── Sampling Rate: 0.1 Hz
```

### **Actuators (Control & Automation)**
```
Control Systems:
├── HVAC Controls
│   ├── Exhaust Fans (PWM controlled)
│   ├── Circulation Fans
│   ├── Heaters (relay controlled)
│   └── Coolers/Evaporative cooling
│
├── Irrigation System
│   ├── Water Pumps (relay controlled)
│   ├── Solenoid Valves (zone control)
│   ├── Misting Systems
│   └── Drip Irrigation
│
├── Lighting Systems
│   ├── LED Grow Lights (PWM dimming)
│   ├── Photoperiod Control
│   ├── Spectral Control (RGB channels)
│   └── Emergency Lighting
│
├── Nutrient Dosing
│   ├── Peristaltic Pumps (EC control)
│   ├── pH Adjustment Pumps
│   └── Mixing Systems
│
└── Monitoring Equipment
    ├── IP Cameras (time-lapse)
    ├── Audio Alerts
    └── Status LEDs
```

## 1.2 Edge Computing Devices

### **Microcontrollers & SBCs**
```
Device Options:
├── ESP32 (Primary IoT Node)
│   ├── Dual-core 240 MHz
│   ├── Wi-Fi + Bluetooth
│   ├── Low power consumption
│   ├── Cost: $5-10
│   └── Use Case: Individual sensor nodes
│
├── ESP8266 (Budget Option)
│   ├── Single-core 80 MHz
│   ├── Wi-Fi only
│   ├── Cost: $2-5
│   └── Use Case: Simple sensor nodes
│
├── Raspberry Pi 4 (Zone Controller)
│   ├── Quad-core ARM Cortex-A72
│   ├── 2-8 GB RAM
│   ├── Full Linux OS
│   ├── Cost: $35-75
│   └── Use Case: Zone gateway, edge processing
│
└── Arduino Nano/Mega (Legacy Support)
    ├── ATmega328P/2560
    ├── Simple, reliable
    ├── Cost: $5-20
    └── Use Case: Actuator control, legacy systems
```

### **Edge Processing Capabilities**
```
Edge Functions:
├── Data Preprocessing
│   ├── Sensor calibration
│   ├── Noise filtering
│   ├── Data aggregation (1-minute averages)
│   └── Outlier detection
│
├── Local Control Logic
│   ├── Emergency shutoffs
│   ├── PID control loops
│   ├── Rule-based automation
│   └── Failsafe mechanisms
│
├── Data Buffering
│   ├── Local storage (SD card)
│   ├── Queue management
│   ├── Retry logic for connectivity loss
│   └── Offline operation mode
│
└── Security
    ├── Certificate storage
    ├── Encrypted communication
    ├── Device authentication
    └── Firmware OTA updates
```

## 1.3 Communication Protocols

### **MQTT Architecture**
```
MQTT Structure:
├── Broker: Eclipse Mosquitto
│   ├── Port 8883 (MQTTS - TLS encrypted)
│   ├── Port 1883 (MQTT - dev only)
│   └── Port 9001 (WebSocket - dashboard)
│
├── Topic Hierarchy
│   ├── greenengine/{location}/telemetry
│   │   └── Sensor data publishing (QoS 1)
│   │
│   ├── greenengine/{location}/cmd
│   │   └── Actuator commands (QoS 1)
│   │
│   ├── greenengine/{location}/status
│   │   └── Device health/heartbeat (QoS 0)
│   │
│   └── greenengine/{location}/alert
│       └── Critical alerts (QoS 2)
│
└── Security Features
    ├── TLS 1.3 encryption
    ├── Client certificate authentication
    ├── Username/password backup auth
    └── ACL-based topic permissions
```

### **Message Format (JSON)**
```json
{
  "device_id": "GH-A1-DEV-01",
  "location_id": "greenhouse_a",
  "timestamp": "2025-09-05T14:23:45.123Z",
  "readings": {
    "temperature_c": 23.5,
    "humidity_pct": 68.2,
    "par_umol_m2_s": 450,
    "soil_moisture_pct": 35.8,
    "ec_ms_cm": 1.2,
    "co2_ppm": 650,
    "ph": 6.5
  },
  "device_status": {
    "battery_pct": 98,
    "rssi_dbm": -45,
    "uptime_seconds": 86400,
    "firmware_version": "0.3.2"
  }
}
```

## 1.4 Network Architecture

### **Network Topology**
```
Network Layout:
├── Greenhouse Local Network (192.168.1.0/24)
│   ├── Gateway/Router
│   ├── MQTT Broker (self-hosted)
│   ├── Edge Gateways (Raspberry Pi)
│   └── IoT Devices (ESP32/ESP8266)
│
├── Connectivity Options
│   ├── Wi-Fi (2.4 GHz - better range)
│   ├── Ethernet (zone controllers)
│   ├── LoRaWAN (future: long-range, low-power)
│   └── Cellular (4G/LTE backup)
│
└── Redundancy
    ├── Dual-band Wi-Fi access points
    ├── Mesh networking capability
    ├── Offline operation mode
    └── Local data logging
```

---

# LAYER 2: AI/ML Layer (Intelligence & Analytics)

## 2.1 Machine Learning Pipeline

### **Data Preprocessing & Feature Engineering**
```
Feature Pipeline:
├── Raw Data Ingestion
│   ├── Real-time sensor streams
│   ├── Historical data retrieval
│   └── External data (weather APIs)
│
├── Feature Engineering
│   ├── Time-based Features
│   │   ├── Hour of day, day of week
│   │   ├── Growing degree days (GDD)
│   │   └── Photoperiod calculations
│   │
│   ├── Statistical Features
│   │   ├── Rolling averages (1h, 6h, 24h)
│   │   ├── Standard deviation
│   │   ├── Min/max values
│   │   └── Rate of change
│   │
│   ├── Domain-Specific Features
│   │   ├── Vapor Pressure Deficit (VPD)
│   │   ├── Daily Light Integral (DLI)
│   │   ├── Nutrient balance ratios
│   │   └── Growth stage indicators
│   │
│   └── Lag Features
│       ├── Previous 24h values
│       ├── Same time yesterday
│       └── Weekly patterns
│
└── Feature Storage
    ├── Feature Store (processed_features table)
    ├── Versioning & lineage tracking
    └── Real-time & batch feature serving
```

## 2.2 ML Models & Algorithms

### **Forecasting Models**
```
Time-Series Prediction:
├── Growth Trajectory Forecasting
│   ├── Model: Prophet (Facebook)
│   │   ├── Handles seasonality
│   │   ├── Holiday effects
│   │   └── Trend changes
│   │
│   ├── Model: XGBoost Regressor
│   │   ├── Non-linear relationships
│   │   ├── Feature interactions
│   │   └── High accuracy
│   │
│   └── Model: LSTM (Future)
│       ├── Deep learning approach
│       ├── Long-term dependencies
│       └── Complex patterns
│
├── Yield Prediction
│   ├── Input Features:
│   │   ├── Historical growth rates
│   │   ├── Environmental conditions
│   │   ├── Nutrient levels
│   │   ├── Crop variety
│   │   └── Days to harvest
│   │
│   ├── Model: Random Forest Regressor
│   │   ├── Ensemble method
│   │   ├── Robust to outliers
│   │   └── Feature importance
│   │
│   └── Output:
│       ├── Expected yield (grams)
│       ├── Confidence interval
│       └── Optimal harvest date
│
└── Environmental Forecasting
    ├── Next 24h temperature prediction
    ├── Humidity trends
    ├── HVAC load prediction
    └── Energy consumption forecast
```

### **Anomaly Detection**
```
Anomaly Detection System:
├── Statistical Methods
│   ├── Isolation Forest
│   │   ├── Detects outliers in sensor data
│   │   ├── Unsupervised learning
│   │   └── Fast, scalable
│   │
│   └── Local Outlier Factor (LOF)
│       ├── Density-based detection
│       ├── Local anomalies
│       └── Contextual outliers
│
├── Pattern-Based Detection
│   ├── Autoencoder Neural Networks
│   │   ├── Learns normal patterns
│   │   ├── Reconstruction error for anomalies
│   │   └── Multivariate analysis
│   │
│   └── ARIMA Residuals
│       ├── Time-series forecasting
│       ├── Deviation from expected
│       └── Seasonality aware
│
├── Anomaly Types Detected
│   ├── Sensor Malfunctions
│   │   ├── Stuck values
│   │   ├── Drift
│   │   └── Out-of-range readings
│   │
│   ├── Environmental Anomalies
│   │   ├── Temperature spikes
│   │   ├── Humidity drops
│   │   ├── CO2 depletion
│   │   └── Unusual patterns
│   │
│   └── Growth Anomalies
│       ├── Stunted growth
│       ├── Disease indicators
│       ├── Pest activity
│       └── Nutrient deficiencies
│
└── Alert Generation
    ├── Severity classification (low/medium/high)
    ├── Root cause analysis
    ├── Recommended actions
    └── Notification routing
```

### **Optimization Models**
```
Control Optimization:
├── Climate Optimization
│   ├── Objective: Maximize growth, minimize cost
│   ├── Method: Reinforcement Learning (DQN)
│   ├── State Space:
│   │   ├── Current environment readings
│   │   ├── Time of day/season
│   │   ├── Energy prices
│   │   └── Growth stage
│   │
│   └── Action Space:
│       ├── HVAC setpoints
│       ├── Lighting intensity
│       ├── Irrigation timing
│       └── CO2 supplementation
│
├── Resource Optimization
│   ├── Water Usage Minimization
│   │   ├── Evapotranspiration models
│   │   ├── Soil moisture prediction
│   │   └── Optimal irrigation scheduling
│   │
│   ├── Energy Cost Reduction
│   │   ├── Peak demand avoidance
│   │   ├── Thermal mass utilization
│   │   └── Natural ventilation timing
│   │
│   └── Nutrient Efficiency
│       ├── Optimal EC levels
│       ├── pH management
│       └── Fertilizer scheduling
│
└── Multi-Objective Optimization
    ├── Pareto-optimal solutions
    ├── Trade-off analysis
    └── Scenario planning
```

## 2.3 Model Training & Deployment

### **Training Pipeline**
```
ML Pipeline Architecture:
├── Data Collection
│   ├── Query historical data (PostgreSQL)
│   ├── External datasets (weather, research)
│   └── Synthetic data augmentation
│
├── Data Preparation
│   ├── Train/validation/test split (70/15/15)
│   ├── Feature scaling (StandardScaler)
│   ├── Missing value imputation
│   └── Class balancing (for classification)
│
├── Model Training
│   ├── Hyperparameter tuning (GridSearchCV)
│   ├── Cross-validation (5-fold)
│   ├── Early stopping (for NN)
│   └── Ensemble methods
│
├── Model Evaluation
│   ├── Regression Metrics:
│   │   ├── RMSE (Root Mean Square Error)
│   │   ├── MAE (Mean Absolute Error)
│   │   ├── R² score
│   │   └── MAPE (Mean Absolute Percentage Error)
│   │
│   ├── Classification Metrics:
│   │   ├── Precision, Recall, F1
│   │   ├── Confusion matrix
│   │   ├── ROC-AUC
│   │   └── PR-AUC
│   │
│   └── Business Metrics:
│       ├── Yield accuracy
│       ├── Cost savings
│       ├── Alert precision
│       └── User satisfaction
│
├── Model Registry
│   ├── Model versioning (joblib serialization)
│   ├── Metadata tracking
│   │   ├── Training date
│   │   ├── Features used
│   │   ├── Performance metrics
│   │   └── Training dataset ID
│   │
│   └── Model storage (ml/models/)
│
└── Model Deployment
    ├── REST API endpoint (/api/v1/predictions/*)
    ├── Batch prediction jobs (nightly)
    ├── Real-time inference (<100ms)
    └── A/B testing framework
```

### **Continuous Learning**
```
Model Improvement Cycle:
├── Performance Monitoring
│   ├── Prediction accuracy tracking
│   ├── Drift detection (data & concept)
│   ├── Error analysis
│   └── User feedback collection
│
├── Automated Retraining
│   ├── Trigger Conditions:
│   │   ├── Performance degradation
│   │   ├── New data threshold reached
│   │   ├── Scheduled (monthly)
│   │   └── Manual trigger
│   │
│   └── Retraining Process:
│       ├── Incremental learning
│       ├── Full retraining
│       ├── Transfer learning
│       └── Online learning (future)
│
└── Model Validation
    ├── Canary deployment
    ├── Shadow mode testing
    ├── Rollback capability
    └── Champion/challenger comparison
```

## 2.4 AI-Powered Features

### **Intelligent Automation**
```
Smart Control Systems:
├── Adaptive Climate Control
│   ├── Learn optimal setpoints per crop
│   ├── Predict climate needs 24h ahead
│   ├── Auto-adjust for weather changes
│   └── Balance comfort vs. cost
│
├── Predictive Maintenance
│   ├── Equipment health monitoring
│   ├── Failure prediction (pumps, fans)
│   ├── Maintenance scheduling
│   └── Parts ordering alerts
│
├── Growth Stage Recognition
│   ├── Computer vision (future)
│   ├── Growth rate analysis
│   ├── Auto-adjust environment by stage
│   └── Harvest readiness detection
│
└── Pest & Disease Detection
    ├── Image analysis (CNN)
    ├── Environmental risk factors
    ├── Early warning system
    └── Treatment recommendations
```

---

# LAYER 3: Cloud & Dashboard Layer (Presentation & Services)

## 3.1 Backend API (FastAPI)

### **API Architecture**
```
API Structure:
├── src/api/main.py (Core Application)
│   ├── FastAPI app initialization
│   ├── CORS middleware
│   ├── Exception handlers
│   └── OpenAPI documentation
│
├── Authentication & Authorization
│   ├── src/auth/authentication.py
│   │   ├── JWT token generation/validation
│   │   ├── Password hashing (bcrypt)
│   │   └── Token refresh mechanism
│   │
│   └── src/auth/middleware.py
│       ├── RBAC middleware
│       ├── Role-based permissions
│       │   ├── Admin: Full access
│       │   ├── Operator: Control + view
│       │   └── Viewer: Read-only
│       └── API key authentication
│
├── API Endpoints (RESTful)
│   ├── /api/v1/sensor-data
│   │   ├── GET: Query sensor readings
│   │   ├── POST: Ingest sensor data (MQTT → API)
│   │   └── Query params: location, time range, limit
│   │
│   ├── /api/v1/alerts
│   │   ├── GET: List alerts (with filters)
│   │   ├── POST: Create manual alert
│   │   ├── POST /{id}/ack: Acknowledge alert
│   │   └── POST /{id}/resolve: Resolve alert
│   │
│   ├── /api/v1/commands
│   │   ├── GET: List command history
│   │   ├── POST: Send actuator command
│   │   └── POST /{id}/requeue: Retry failed command
│   │
│   ├── /api/v1/trays
│   │   ├── GET: List all trays
│   │   ├── POST: Create new tray
│   │   ├── PUT /{id}: Update tray
│   │   └── DELETE /{id}: Archive tray
│   │
│   ├── /api/v1/predictions
│   │   ├── GET /growth-forecast: Growth trajectory
│   │   ├── GET /yield-prediction: Expected yield
│   │   └── POST /train: Trigger model training
│   │
│   ├── /api/v1/config
│   │   ├── GET /thresholds: Alert thresholds
│   │   ├── PUT /thresholds: Update thresholds
│   │   └── GET /system: System configuration
│   │
│   ├── /api/v1/analytics
│   │   ├── GET /summary: Dashboard overview
│   │   ├── GET /trends: Historical trends
│   │   └── GET /reports: Generate reports
│   │
│   └── /api/v1/auth
│       ├── POST /login: User authentication
│       ├── POST /logout: Session termination
│       ├── POST /register: User registration (admin)
│       └── GET /me: Current user info
│
└── API Documentation
    ├── Swagger UI: /docs
    ├── ReDoc: /redoc
    └── OpenAPI schema: /openapi.json
```

### **Background Services**
```
Async Workers:
├── Command Worker (src/services/command_worker.py)
│   ├── MQTT command publisher
│   ├── Retry logic (exponential backoff)
│   ├── Command queue management
│   └── Failure notifications
│
├── Rules Engine (src/utils/rules_engine.py)
│   ├── Threshold monitoring
│   ├── Alert generation
│   ├── Automated actions
│   └── Escalation logic
│
├── ETL Pipeline (src/etl/feature_engineering.py)
│   ├── Batch feature computation
│   ├── Data aggregation (hourly/daily)
│   ├── Data quality checks
│   └── Scheduled execution (cron)
│
└── MQTT Ingestion (src/ingestion/mqtt_client.py)
    ├── Subscribe to telemetry topics
    ├── Data validation
    ├── Database insertion
    └── WebSocket broadcast
```

## 3.2 Frontend Dashboard (Streamlit)

### **Dashboard Architecture**
```
Dashboard Structure (dashboard/app.py):
├── Layout & Navigation
│   ├── Sidebar Navigation
│   │   ├── Location selector
│   │   ├── Time range picker
│   │   └── User profile/logout
│   │
│   └── Multi-tab Interface
│       ├── 📊 Overview (default)
│       ├── 🌡️ Sensors
│       ├── 🌱 Trays
│       ├── 🚨 Alerts
│       ├── 📈 Forecasts
│       ├── 🎛️ Control
│       ├── ⚙️ Admin (role-based)
│       └── 📚 Documentation
│
├── Overview Tab
│   ├── Key Metrics Cards
│   │   ├── Current temperature
│   │   ├── Humidity
│   │   ├── CO2 levels
│   │   ├── Active alerts count
│   │   └── Total trays
│   │
│   ├── Real-time Charts
│   │   ├── Temperature trend (24h)
│   │   ├── Humidity trend
│   │   ├── PAR levels
│   │   └── VPD calculation
│   │
│   └── Recent Alerts Panel
│       ├── Last 5 alerts
│       ├── Severity indicators
│       └── Quick actions
│
├── Sensors Tab
│   ├── Time Range Selector
│   │   ├── Last 1 hour
│   │   ├── Last 24 hours
│   │   ├── Last 7 days
│   │   ├── Last 30 days
│   │   └── Custom range
│   │
│   ├── Interactive Charts (Plotly)
│   │   ├── Multi-axis line charts
│   │   ├── Zoom & pan
│   │   ├── Hover tooltips
│   │   └── Export to image
│   │
│   └── Data Export
│       ├── CSV download
│       ├── Excel export
│       └── API query builder
│
├── Trays Tab
│   ├── Tray List (DataGrid)
│   │   ├── Tray ID & name
│   │   ├── Crop type
│   │   ├── Planted date
│   │   ├── Days to harvest
│   │   └── Status indicator
│   │
│   ├── Create/Edit Form
│   │   ├── Crop selection
│   │   ├── Location assignment
│   │   ├── Growing parameters
│   │   └── Photo upload
│   │
│   └── Growth Tracking
│       ├── Manual measurements
│       ├── Growth curve chart
│       ├── Yield prediction
│       └── Harvest scheduling
│
├── Alerts Tab
│   ├── Active Alerts
│   │   ├── Real-time updates
│   │   ├── Severity filtering
│   │   ├── Acknowledge button
│   │   └── Resolve button
│   │
│   ├── Alert History
│   │   ├── Searchable table
│   │   ├── Time filters
│   │   └── Export capability
│   │
│   └── Alert Analytics
│       ├── Alerts by type (pie chart)
│       ├── Alerts over time
│       └── MTTR (Mean Time To Resolve)
│
├── Forecasts Tab
│   ├── Growth Predictions
│   │   ├── 7-day forecast
│   │   ├── 30-day forecast
│   │   ├── Confidence intervals
│   │   └── Comparison to actual
│   │
│   ├── Yield Estimates
│   │   ├── Per tray predictions
│   │   ├── Total expected yield
│   │   ├── Harvest date estimate
│   │   └── Revenue projection
│   │
│   └── Environmental Forecast
│       ├── Temperature predictions
│       ├── Humidity trends
│       └── Recommended actions
│
├── Control Tab
│   ├── Actuator Controls
│   │   ├── Manual overrides
│   │   ├── HVAC controls
│   │   ├── Irrigation triggers
│   │   ├── Lighting controls
│   │   └── Emergency stop
│   │
│   ├── Command History
│   │   ├── Recent commands
│   │   ├── Status tracking
│   │   └── Retry options
│   │
│   └── Automation Rules
│       ├── View active rules
│       ├── Enable/disable rules
│       └── Rule performance
│
└── Admin Tab (Admin Role Only)
    ├── User Management
    │   ├── User list
    │   ├── Role assignment
    │   ├── Password reset
    │   └── Audit logs
    │
    ├── System Configuration
    │   ├── Alert thresholds
    │   ├── MQTT settings
    │   ├── Notification config
    │   └── Database maintenance
    │
    └── System Health
        ├── API status
        ├── Database metrics
        ├── MQTT broker status
        └── ML model performance
```

### **UI/UX Features**
```
User Experience:
├── Responsive Design
│   ├── Desktop (>1024px)
│   ├── Tablet (768-1024px)
│   └── Mobile (320-767px)
│
├── Real-time Updates
│   ├── Auto-refresh (configurable interval)
│   ├── WebSocket connections
│   └── Live data streaming
│
├── Accessibility
│   ├── Keyboard navigation
│   ├── Screen reader support
│   ├── High contrast mode
│   └── Font size adjustment
│
└── Internationalization (Future)
    ├── Multi-language support
    ├── Date/time localization
    └── Unit conversions (°C/°F)
```

## 3.3 Database Layer (PostgreSQL + TimescaleDB)

### **Schema Design**
```
Database Tables:
├── Core Tables
│   ├── devices
│   │   ├── device_id (PK)
│   │   ├── location_id
│   │   ├── device_type (sensor/actuator)
│   │   ├── model, firmware_version
│   │   └── last_seen, status
│   │
│   ├── sensor_readings (Hypertable)
│   │   ├── id (PK), device_id (FK)
│   │   ├── timestamp (partitioned)
│   │   ├── temperature, humidity, par
│   │   ├── soil_moisture, ec, co2, ph
│   │   ├── raw (JSONB - full payload)
│   │   └── Retention: 90 days raw, 1 year aggregated
│   │
│   └── processed_features (Hypertable)
│       ├── id (PK), location_id
│       ├── timestamp (partitioned)
│       ├── temp_1h_avg, temp_24h_avg
│       ├── vpd, dli, gdd
│       └── Statistical features
│
├── ML Tables
│   ├── ml_predictions
│   │   ├── id (PK), location_id
│   │   ├── prediction_type (growth/yield)
│   │   ├── predicted_value, confidence
│   │   ├── model_name, model_version
│   │   └── created_at
│   │
│   └── model_registry
│       ├── model_id (PK)
│       ├── model_name, version
│       ├── file_path, metrics (JSONB)
│       └── trained_at, is_active
│
├── Operations Tables
│   ├── alerts
│   │   ├── id (PK), rule_id
│   │   ├── severity (low/medium/high)
│   │   ├── message, device_id
│   │   ├── status (active/ack/resolved)
│   │   ├── acknowledged_at, resolved_at
│   │   └── created_at
│   │
│   ├── alert_actions
│   │   ├── id (PK), alert_id (FK)
│   │   ├── action_type, user_id
│   │   └── performed_at
│   │
│   ├── device_commands
│   │   ├── id (PK), device_id (FK)
│   │   ├── command (JSONB)
│   │   ├── status (pending/sent/ack/failed)
│   │   ├── retry_count, next_attempt_at
│   │   └── created_at, completed_at
│   │
│   └── trays
│       ├── tray_id (PK)
│       ├── tray_code, crop_type
│       ├── location_id, device_id
│       ├── planted_on, expected_harvest
│       ├── grow_medium, seed_density
│       └── notes, status
│
├── User Management
│   ├── users
│   │   ├── user_id (PK)
│   │   ├── username (unique), email
│   │   ├── password_hash
│   │   ├── is_active, email_verified
│   │   └── created_at, last_login
│   │
│   ├── roles
│   │   ├── role_id (PK)
│   │   ├── role_name (admin/operator/viewer)
│   │   ├── permissions (JSONB)
│   │   └── description
│   │
│   ├── user_roles (M2M)
│   │   ├── user_id (FK), role_id (FK)
│   │   └── assigned_at
│   │
│   └── sessions
│       ├── session_id (PK)
│       ├── user_id (FK), token_hash
│       ├── expires_at, ip_address
│       └── created_at
│
└── Configuration
    ├── system_config
    │   ├── config_key (PK)
    │   ├── config_value (JSONB)
    │   ├── is_active, description
    │   └── updated_at, updated_by
    │
    └── audit_logs
        ├── log_id (PK)
        ├── user_id (FK), action
        ├── entity_type, entity_id
        ├── changes (JSONB)
        └── timestamp, ip_address
```

### **Data Management**
```
Data Operations:
├── Time-Series Optimization
│   ├── TimescaleDB hypertables
│   ├── Automatic partitioning (1-day chunks)
│   ├── Continuous aggregates (caggs)
│   │   ├── 1-minute averages
│   │   ├── 1-hour aggregates
│   │   └── Daily summaries
│   │
│   └── Data compression (after 7 days)
│
├── Retention Policies
│   ├── Raw sensor data: 90 days
│   ├── Hourly aggregates: 1 year
│   ├── Daily aggregates: 5 years
│   ├── ML predictions: 2 years
│   └── Audit logs: 7 years (compliance)
│
├── Backup Strategy
│   ├── Continuous WAL archiving
│   ├── Daily full backups (pg_dump)
│   ├── Weekly system snapshots
│   ├── Off-site backup replication
│   └── Point-in-time recovery (PITR)
│
└── Performance Optimization
    ├── Indexes on:
    │   ├── timestamp (BRIN for time-series)
    │   ├── device_id, location_id (B-tree)
    │   └── status fields
    │
    ├── Query optimization
    │   ├── Prepared statements
    │   ├── Connection pooling
    │   └── Query result caching
    │
    └── Monitoring
        ├── Slow query logging
        ├── Table bloat monitoring
        └── Index usage statistics
```

## 3.4 Monitoring & Observability

### **Metrics Collection (Prometheus)**
```
Metrics Architecture:
├── API Metrics (/api/v1/metrics)
│   ├── Request Rates
│   │   ├── http_requests_total
│   │   ├── http_request_duration_seconds
│   │   └── http_requests_in_progress
│   │
│   ├── Error Rates
│   │   ├── http_errors_total (by status code)
│   │   ├── http_exceptions_total
│   │   └── Error rate percentage
│   │
│   └── Business Metrics
│       ├── sensor_readings_processed
│       ├── alerts_generated_total
│       ├── commands_sent_total
│       └── predictions_made_total
│
├── System Metrics
│   ├── Database
│   │   ├── db_connections_active
│   │   ├── db_query_duration_seconds
│   │   ├── db_table_size_bytes
│   │   └── db_transactions_total
│   │
│   ├── MQTT Broker
│   │   ├── mqtt_connected_clients
│   │   ├── mqtt_messages_received
│   │   ├── mqtt_messages_sent
│   │   └── mqtt_subscriptions_total
│   │
│   └── ML Service
│       ├── ml_inference_duration_seconds
│       ├── ml_prediction_errors_total
│       ├── ml_model_accuracy (gauge)
│       └── ml_training_duration_seconds
│
└── Infrastructure Metrics
    ├── CPU usage per service
    ├── Memory consumption
    ├── Disk I/O
    ├── Network traffic
    └── Container health
```

### **Visualization (Grafana)**
```
Grafana Dashboards:
├── System Overview
│   ├── Service health status
│   ├── Request rate & latency
│   ├── Error rates
│   └── Resource utilization
│
├── IoT Device Monitoring
│   ├── Connected devices count
│   ├── Message throughput
│   ├── Device battery levels
│   └── Connectivity issues
│
├── Environmental Dashboard
│   ├── Real-time sensor readings
│   ├── Alert frequency
│   ├── Threshold violations
│   └── Environmental trends
│
├── ML Performance
│   ├── Model accuracy over time
│   ├── Prediction latency
│   ├── Feature drift detection
│   └── Training history
│
└── Business Metrics
    ├── Total trays managed
    ├── Yield predictions vs actuals
    ├── Resource usage (water, energy)
    └── Cost per kg of produce
```

### **Alerting & Notifications**
```
Alert Channels:
├── Slack Integration
│   ├── Critical alerts (immediate)
│   ├── Daily summaries
│   └── System health reports
│
├── Email Notifications
│   ├── Alert digests
│   ├── Weekly reports
│   └── User-specific alerts
│
├── SMS (Twilio - Future)
│   ├── Emergency alerts only
│   └── Critical system failures
│
└── In-Dashboard Alerts
    ├── Real-time UI notifications
    ├── Alert history
    └── Action tracking
```

---

# LAYER 4: Data Flow & Integration

## 4.1 Data Flow Diagram

```
┌─────────────┐
│   Sensors   │ ← Physical Environment
└──────┬──────┘
       │ (Analog signals)
       ↓
┌─────────────┐
│ ESP32/IoT   │ ← Edge Processing
│   Device    │   • Calibration
└──────┬──────┘   • Filtering
       │ (JSON via MQTT/TLS)
       ↓
┌─────────────┐
│   MQTT      │ ← Message Broker
│   Broker    │   • Queue management
└──────┬──────┘   • Pub/Sub routing
       │
       ├──────────────────┬─────────────────┐
       ↓                  ↓                 ↓
┌─────────────┐    ┌────────────┐   ┌────────────┐
│ MQTT Client │    │ Dashboard  │   │ External   │
│ (Ingestion) │    │ (WebSocket)│   │ Services   │
└──────┬──────┘    └────────────┘   └────────────┘
       │
       ↓
┌─────────────┐
│   API       │ ← Data Validation
│  (FastAPI)  │   • Schema check
└──────┬──────┘   • Authentication
       │
       ├──────────────────┬─────────────────┐
       ↓                  ↓                 ↓
┌─────────────┐    ┌────────────┐   ┌────────────┐
│ PostgreSQL  │    │ Rules      │   │ ML Service │
│ (Raw Data)  │    │ Engine     │   │ (Predict)  │
└──────┬──────┘    └─────┬──────┘   └─────┬──────┘
       │                  │                │
       │                  ↓                │
       │           ┌────────────┐          │
       │           │   Alerts   │          │
       │           │  (Database)│          │
       │           └─────┬──────┘          │
       │                  │                │
       ↓                  ↓                ↓
┌─────────────────────────────────────────┐
│            Dashboard (Streamlit)         │ ← User Interface
│  • Real-time visualization               │
│  • Control & monitoring                  │
│  • Analytics & reports                   │
└──────────────────────────────────────────┘
```

## 4.2 Integration Points

### **External Integrations**
```
Third-Party Services:
├── Weather APIs (Future)
│   ├── OpenWeatherMap
│   ├── Tomorrow.io
│   └── Purpose: External forecasting
│
├── Energy Management
│   ├── Smart meter integration
│   ├── Solar panel monitoring
│   └── Grid price APIs
│
├── Communication Services
│   ├── Slack API (implemented)
│   ├── Twilio SMS (future)
│   └── SendGrid Email (future)
│
└── Business Systems
    ├── Inventory management
    ├── Harvest scheduling
    └── Sales/CRM integration
```

---

# LAYER 5: Security Architecture

## 5.1 Security Layers

```
Security Model:
├── Device Security
│   ├── Mutual TLS (mTLS)
│   │   ├── Client certificates
│   │   ├── CA-signed certificates
│   │   └── Certificate revocation
│   │
│   ├── Firmware Security
│   │   ├── Signed firmware updates
│   │   ├── OTA with rollback
│   │   └── Secure boot (ESP32)
│   │
│   └── Physical Security
│       ├── Tamper detection
│       ├── Secure storage
│       └── Access logs
│
├── Network Security
│   ├── Encryption
│   │   ├── TLS 1.3 for all communication
│   │   ├── MQTT over TLS (port 8883)
│   │   └── HTTPS for API/dashboard
│   │
│   ├── Firewall Rules
│   │   ├── Whitelist IoT device IPs
│   │   ├── Rate limiting
│   │   └── DDoS protection
│   │
│   └── Network Segmentation
│       ├── IoT VLAN (isolated)
│       ├── Management VLAN
│       └── DMZ for external access
│
├── Application Security
│   ├── Authentication
│   │   ├── JWT tokens (30-min expiry)
│   │   ├── Refresh tokens (7 days)
│   │   ├── Password policy (min 8 chars)
│   │   └── 2FA (future)
│   │
│   ├── Authorization (RBAC)
│   │   ├── Role-based access
│   │   ├── Resource-level permissions
│   │   └── Audit logging
│   │
│   ├── Input Validation
│   │   ├── Pydantic schemas
│   │   ├── SQL injection prevention
│   │   └── XSS protection
│   │
│   └── API Security
│       ├── Rate limiting
│       ├── API key management
│       ├── CORS configuration
│       └── Request signing
│
├── Data Security
│   ├── Encryption at Rest
│   │   ├── Database encryption
│   │   ├── Backup encryption
│   │   └── Credential encryption
│   │
│   ├── Encryption in Transit
│   │   ├── TLS everywhere
│   │   └── VPN for remote access
│   │
│   ├── Data Privacy
│   │   ├── GDPR compliance (future)
│   │   ├── Data anonymization
│   │   └── Right to erasure
│   │
│   └── Backup Security
│       ├── Encrypted backups
│       ├── Off-site storage
│       └── Access control
│
└── Operational Security
    ├── Monitoring
    │   ├── Security event logging
    │   ├── Intrusion detection
    │   └── Anomaly detection
    │
    ├── Incident Response
    │   ├── Incident playbooks
    │   ├── Automated alerts
    │   └── Forensics capability
    │
    └── Compliance
        ├── Security audits
        ├── Penetration testing
        └── Vulnerability scanning
```

---

# LAYER 6: Deployment Architecture

## 6.1 Deployment Options

### **Option A: Single-Server Deployment (Current)**
```
Self-Hosted Setup:
├── Hardware: Single server/NUC
│   ├── CPU: 4+ cores
│   ├── RAM: 8+ GB
│   ├── Storage: 256+ GB SSD
│   └── OS: Ubuntu 22.04 LTS
│
├── Services (Docker Compose)
│   ├── PostgreSQL + TimescaleDB
│   ├── Mosquitto MQTT Broker
│   ├── FastAPI (API)
│   ├── Streamlit (Dashboard)
│   ├── Prometheus
│   └── Grafana
│
├── Pros:
│   ├── Simple setup
│   ├── Low cost
│   ├── Full control
│   └── No cloud dependency
│
└── Cons:
    ├── Single point of failure
    ├── Limited scalability
    └── Manual backup/recovery
```

### **Option B: High-Availability Setup (Future)**
```
Multi-Node Cluster:
├── Load Balancer (HAProxy/Traefik)
│   ├── API traffic distribution
│   ├── SSL termination
│   └── Health checks
│
├── Application Tier (3+ nodes)
│   ├── FastAPI (horizontal scaling)
│   ├── Streamlit (stateless)
│   └── Background workers
│
├── Database Tier
│   ├── PostgreSQL primary
│   ├── Read replicas (2+)
│   └── Automated failover
│
├── Message Broker Tier
│   ├── Mosquitto cluster
│   └── MQTT bridge
│
└── Monitoring Tier
    ├── Prometheus (HA pair)
    ├── Grafana
    └── Log aggregation (ELK)
```

### **Option C: Cloud Deployment (Future)**
```
Cloud Architecture:
├── Compute (AWS/Azure/GCP)
│   ├── Kubernetes (EKS/AKS/GKE)
│   ├── Auto-scaling groups
│   └── Spot instances for ML
│
├── Database
│   ├── Managed PostgreSQL (RDS/Cloud SQL)
│   └── Timescale Cloud
│
├── IoT Services
│   ├── AWS IoT Core / Azure IoT Hub
│   └── Device management
│
└── Benefits:
    ├── Infinite scalability
    ├── Managed services
    ├── Global distribution
    └── Built-in disaster recovery
```

## 6.2 Scalability Considerations

```
Scaling Strategy:
├── Vertical Scaling (Current)
│   ├── Increase server resources
│   ├── Faster storage (NVMe SSD)
│   └── Limit: Single server capacity
│
├── Horizontal Scaling (Future)
│   ├── API: Stateless, easy to scale
│   ├── Dashboard: Can run multiple instances
│   ├── ML Service: GPU nodes
│   └── Database: Read replicas
│
├── Performance Targets
│   ├── API Response: <200ms (p95)
│   ├── Sensor Data Ingestion: 1000 msg/s
│   ├── Dashboard Load: <3s
│   ├── ML Inference: <100ms
│   └── Concurrent Users: 100+
│
└── Bottleneck Analysis
    ├── Database queries (optimize indexes)
    ├── MQTT throughput (cluster)
    ├── ML inference (GPU acceleration)
    └── Dashboard rendering (caching)
```

---

# Technology Stack Summary

## Core Technologies

| **Layer**              | **Technology**           | **Version** | **Purpose**                          |
|------------------------|--------------------------|-------------|--------------------------------------|
| **IoT Devices**        | ESP32                    | -           | Microcontroller platform             |
|                        | Raspberry Pi 4           | -           | Edge gateway, zone controller        |
| **Communication**      | MQTT (Mosquitto)         | 2.0         | IoT messaging protocol               |
| **Backend API**        | Python                   | 3.9+        | Programming language                 |
|                        | FastAPI                  | 0.100+      | REST API framework                   |
|                        | Uvicorn                  | 0.23+       | ASGI server                          |
| **Frontend**           | Streamlit                | 1.25+       | Dashboard framework                  |
|                        | Plotly                   | 5.15+       | Interactive charts                   |
| **Database**           | PostgreSQL               | 15+         | Relational database                  |
|                        | TimescaleDB              | 2.11+       | Time-series extension                |
| **ML/AI**              | scikit-learn             | 1.3+        | Machine learning library             |
|                        | XGBoost                  | 1.7+        | Gradient boosting                    |
|                        | Prophet                  | 1.1+        | Time-series forecasting              |
| **Authentication**     | JWT (python-jose)        | 3.3+        | Token-based auth                     |
|                        | bcrypt (passlib)         | 1.7+        | Password hashing                     |
| **Monitoring**         | Prometheus               | 2.45+       | Metrics collection                   |
|                        | Grafana                  | 10.0+       | Visualization & dashboards           |
| **Deployment**         | Docker                   | 24.0+       | Containerization                     |
|                        | Docker Compose           | 2.20+       | Multi-container orchestration        |

## Python Libraries

```python
# Core API
fastapi==0.100.0
uvicorn[standard]==0.23.0
python-multipart==0.0.6
python-dotenv==1.0.0

# Database
psycopg2-binary==2.9.7
sqlalchemy==2.0.20  # (optional ORM)

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
email-validator==2.0.0

# MQTT
paho-mqtt==1.6.1

# ML & Data Science
scikit-learn==1.3.0
xgboost==1.7.6
prophet==1.1.4
joblib==1.3.2
pandas==2.0.3
numpy==1.25.2

# Dashboard
streamlit==1.25.0
plotly==5.15.0

# Monitoring
prometheus-client==0.17.1

# Utilities
requests==2.31.0
```

---

# Key Design Principles

## 1. **Modularity**
- Each layer is independent and replaceable
- Microservices-ready architecture
- Clear API contracts between layers

## 2. **Scalability**
- Horizontal scaling for stateless services
- Time-series optimized database
- Efficient data aggregation and retention

## 3. **Reliability**
- Fault tolerance at each layer
- Graceful degradation
- Automated retry mechanisms
- Comprehensive error handling

## 4. **Security**
- Defense in depth (multiple security layers)
- Principle of least privilege
- Encryption everywhere
- Comprehensive audit logging

## 5. **Observability**
- Metrics, logs, and traces
- Real-time monitoring
- Proactive alerting
- Performance optimization

## 6. **Maintainability**
- Clean code architecture
- Comprehensive documentation
- Automated testing
- Version control and CI/CD

## 7. **Extensibility**
- Plugin architecture for new sensors
- API-first design
- Model registry for ML
- Configuration-driven behavior

---

# Future Enhancements

## Phase 1: Enhanced ML Capabilities
- Computer vision for plant health
- Reinforcement learning for optimal control
- Federated learning across multiple greenhouses
- AutoML for model optimization

## Phase 2: Advanced IoT Features
- LoRaWAN for long-range sensors
- Edge AI on Raspberry Pi
- Wireless sensor networks (mesh)
- Energy harvesting sensors

## Phase 3: Enterprise Features
- Multi-tenancy support
- White-label dashboard
- Marketplace for integrations
- Mobile app (iOS/Android)

## Phase 4: Sustainability Metrics
- Carbon footprint tracking
- Water usage optimization
- Energy efficiency scoring
- Sustainability reporting

## Phase 5: Market Integration
- Supply chain integration
- Dynamic pricing models
- Demand forecasting
- B2B marketplace connection

---

# Conclusion

This technical framework provides a robust, scalable, and secure foundation for the Green Engine smart greenhouse management system. The layered architecture ensures:

- **IoT Layer**: Reliable sensor data collection and actuator control
- **AI Layer**: Intelligent predictions and automated optimization
- **Cloud & Dashboard Layer**: User-friendly interface and comprehensive analytics

Each layer can evolve independently while maintaining system integrity through well-defined APIs and data contracts. The architecture supports growth from a small-scale deployment (2-4 zones) to enterprise-level operations managing multiple greenhouses.

---

**Document Version**: 1.0  
**Last Updated**: October 9, 2025  
**Author**: Green Engine Development Team

