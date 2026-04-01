# Green Engine: High-Level Architecture

## System Overview
Green Engine is a comprehensive IoT data pipeline designed for microgreen growth monitoring and optimization. The system processes real-time sensor data, applies machine learning for forecasting and anomaly detection, and provides actionable insights through an interactive dashboard.

## Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Sensors   │    │   Edge Device   │    │   Cloud/Server  │
│                 │    │   (Optional)    │    │                 │
│ • Temperature   │───▶│ • Data Buffer   │───▶│ • MQTT Broker   │
│ • Humidity      │    │ • Preprocessing │    │ • HTTP API      │
│ • Light         │    │ • Local Storage │    │ • Load Balancer │
│ • Soil Moisture │    │                 │    │                 │
│ • CO₂           │    └─────────────────┘    └─────────────────┘
└─────────────────┘                                    │
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   ML Pipeline   │    │   Data Storage  │
│                 │    │                 │    │                 │
│ • Streamlit UI  │◀───│ • Feature Eng.  │◀───│ • PostgreSQL    │
│ • Real-time     │    │ • Model Training│    │ • Time-series   │
│ • Analytics     │    │ • Forecasting   │    │ • Processed     │
│ • Alerts        │    │ • Anomaly Det.  │    │ • Features      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Details

### 1. IoT Layer
**Sensors**: Multi-parameter environmental monitoring
- **Temperature**: Range -10°C to 50°C, accuracy ±0.5°C
- **Humidity**: Range 0-100% RH, accuracy ±3%
- **Light**: PAR (Photosynthetically Active Radiation), 400-700nm
- **Soil Moisture**: Volumetric water content, 0-100%
- **Electrical Conductivity (EC)**: 0-5 mS/cm
- **CO₂**: 400-2000 ppm, accuracy ±50 ppm

**Communication**: MQTT over WiFi/LoRaWAN
- **Protocol**: MQTT 3.1.1 with QoS 1
- **Frequency**: Every 5-15 minutes (configurable)
- **Payload**: JSON format, ~200 bytes per message

### 2. Data Ingestion Layer
**MQTT Broker**: Mosquitto or HiveMQ
- **Authentication**: Username/password + TLS
- **Topics**: `sensors/{location}/{sensor_type}/{sensor_id}`
- **Message Format**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "sensor_id": "temp_001",
  "location": "greenhouse_a",
  "value": 23.5,
  "unit": "celsius",
  "battery": 85,
  "signal_strength": -45
}
```

**HTTP API**: FastAPI-based REST endpoint
- **Endpoint**: `POST /api/v1/sensor-data`
- **Rate Limiting**: 1000 requests/minute
- **Validation**: Pydantic models for data integrity

### 3. Data Processing Layer
**ETL Pipeline**: Apache Airflow or custom Python scheduler
- **Raw Data Storage**: PostgreSQL with TimescaleDB extension
- **Data Cleaning**: Outlier detection, missing value imputation
- **Aggregation**: Hourly/daily summaries for analytics
- **Feature Engineering**: Rolling statistics, lag features, seasonal patterns

**Database Schema**:
```sql
-- Raw sensor data
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    location VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    value DECIMAL(10,3) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    battery INTEGER,
    signal_strength INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Processed features
CREATE TABLE processed_features (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    location VARCHAR(50) NOT NULL,
    temp_avg_1h DECIMAL(5,2),
    temp_avg_24h DECIMAL(5,2),
    humidity_avg_1h DECIMAL(5,2),
    light_sum_1h DECIMAL(10,2),
    soil_moisture_avg_1h DECIMAL(5,2),
    ec_avg_1h DECIMAL(5,2),
    co2_avg_1h DECIMAL(6,2),
    temp_variance_24h DECIMAL(5,2),
    light_variance_24h DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. Machine Learning Layer
**Models**:
1. **Short-term Forecasting (24-72h)**: Prophet or SARIMA
2. **Long-term Yield Prediction**: XGBoost with feature engineering
3. **Anomaly Detection**: Isolation Forest + LSTM autoencoder
4. **Prescriptive Analytics**: Rule-based + ML optimization

**Model Pipeline**:
- **Training**: Daily retraining with new data
- **Validation**: Time-series cross-validation
- **Deployment**: Model versioning with MLflow
- **Monitoring**: Model drift detection

### 5. Analytics Dashboard
**Streamlit Application**:
- **Real-time Monitoring**: Live sensor data visualization
- **Historical Analysis**: Time-series plots with forecasting
- **Anomaly Alerts**: Interactive alert management
- **Growth Optimization**: Prescriptive recommendations

**Key Visualizations**:
- Multi-sensor time-series charts
- Correlation heatmaps
- Growth stage tracking
- Yield prediction curves
- Anomaly detection plots

### 6. Infrastructure
**Deployment**: Single VM with Docker Compose
- **CPU**: 4 vCPUs minimum
- **RAM**: 8GB minimum
- **Storage**: 100GB SSD
- **OS**: Ubuntu 20.04 LTS

**Services**:
```yaml
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest
    environment:
      POSTGRES_DB: green_engine
      POSTGRES_USER: green_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mqtt:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf

  api:
    build: ./src/api
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://green_user:${DB_PASSWORD}@postgres:5432/green_engine

  dashboard:
    build: ./dashboard
    ports:
      - "8501:8501"
    depends_on:
      - api
    environment:
      API_URL: http://api:8000

  ml_pipeline:
    build: ./src/models
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://green_user:${DB_PASSWORD}@postgres:5432/green_engine
```

## Data Flow
1. **Ingestion**: Sensors → MQTT/HTTP → Raw Database
2. **Processing**: Raw Data → ETL → Processed Features
3. **ML**: Features → Model Training → Predictions
4. **Analytics**: Predictions → Dashboard → Insights
5. **Actions**: Insights → Alerts → Recommendations

## Security Considerations
- **Authentication**: JWT tokens for API access
- **Encryption**: TLS for all communications
- **Data Privacy**: Local processing, optional cloud sync
- **Access Control**: Role-based permissions

## Scalability
- **Horizontal**: Multiple sensor locations
- **Vertical**: Enhanced VM resources
- **Database**: Read replicas for analytics
- **Caching**: Redis for frequently accessed data
