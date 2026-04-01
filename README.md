# 🌱 Green Engine - Smart Greenhouse Management System

A comprehensive IoT-based smart greenhouse management system with real-time monitoring, automated controls, and machine learning-powered analytics.

## 🚀 Features

- **Real-time Sensor Monitoring**: Temperature, humidity, light, soil moisture, EC, and CO2
- **Automated Alert System**: Threshold-based alerts with Slack notifications
- **Actuator Control**: Remote control of irrigation, ventilation, and lighting
- **Machine Learning**: Yield prediction and growth trajectory forecasting
- **Dashboard**: Beautiful Streamlit-based web interface
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Security**: JWT authentication, RBAC, and audit logging
- **Monitoring**: Prometheus metrics and Grafana dashboards

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Devices   │───▶│   MQTT Broker   │───▶│   API Server    │
│   (Sensors)     │    │   (Mosquitto)   │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐            │
                       │   Dashboard     │◀───────────┘
                       │   (Streamlit)   │
                       └─────────────────┘
                                 │
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   + TimescaleDB │
                       └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Python (FastAPI)
- **Frontend**: Streamlit
- **Database**: PostgreSQL + TimescaleDB
- **IoT Protocol**: MQTT (Eclipse Mosquitto)
- **ML/AI**: scikit-learn, XGBoost, Prophet
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

## 📦 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional)
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/green-engine.git
   cd green-engine
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb green_engine
   
   # Run database setup
   python scripts/setup_db_local.py
   python scripts/populate_sample_data.py
   ```

5. **Configure environment**
   ```bash
   # Copy and edit environment file
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Start the system**
   ```bash
   # Start API server
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8020 --reload
   
   # In another terminal, start dashboard
   cd dashboard
   streamlit run app.py --server.port 8501
   ```

7. **Access the system**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8020
   - API Docs: http://localhost:8020/docs

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /api/v1/sensor-data` - Get sensor readings
- `GET /api/v1/alerts` - Get alerts
- `POST /api/v1/alerts/{id}/ack` - Acknowledge alert
- `POST /api/v1/alerts/{id}/resolve` - Resolve alert

### Management Endpoints
- `GET /api/v1/trays` - Get growing trays
- `POST /api/v1/trays` - Create new tray
- `GET /api/v1/commands` - Get device commands
- `POST /api/v1/commands` - Send device command

### ML Endpoints
- `GET /api/v1/ml/predictions/yield` - Get yield predictions
- `GET /api/v1/ml/predictions/growth-trajectory` - Get growth forecasts
- `POST /api/v1/ml/models/retrain` - Retrain ML models

### Configuration
- `GET /api/v1/config/thresholds` - Get sensor thresholds
- `PUT /api/v1/config/thresholds` - Update thresholds

## 🔧 Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_NAME=green_engine
DB_USER=green_user
DB_PASSWORD=green_pass

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password

# Slack (optional)
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

## 📈 Monitoring

The system includes comprehensive monitoring:

- **Prometheus Metrics**: Available at `/metrics` endpoint
- **Grafana Dashboards**: Pre-configured dashboards for system monitoring
- **Health Checks**: Built-in health monitoring for all services
- **Logging**: Structured logging with different levels

## 🔒 Security Features

- **JWT Authentication**: Secure API access
- **Role-Based Access Control**: Admin, Operator, Viewer roles
- **Audit Logging**: Complete audit trail of all actions
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries
- **CORS Configuration**: Secure cross-origin requests

## 🤖 Machine Learning

The system includes several ML models:

- **Yield Prediction**: RandomForest, XGBoost, Linear Regression
- **Growth Forecasting**: Prophet time-series forecasting
- **Anomaly Detection**: Isolation Forest, Local Outlier Factor
- **Automated Retraining**: Scheduled model updates

## 📱 IoT Device Integration

### Supported Sensors
- Temperature & Humidity (DHT22, SHT30)
- Light/PAR (BH1750, TSL2591)
- Soil Moisture (Capacitive sensors)
- EC (Electrical Conductivity)
- CO2 (MH-Z19, SCD30)

### Actuators
- Irrigation pumps
- Ventilation fans
- LED grow lights
- CO2 injection systems

### MQTT Topics
- `greenengine/{device_id}/telemetry` - Sensor data
- `greenengine/{device_id}/cmd` - Device commands
- `greenengine/{device_id}/status` - Device status

## 🧪 Testing

```bash
# Run integration tests
python tests/test_integration.py

# Run performance tests
python scripts/performance_test.py

# Run device simulator
python scripts/device_simulator.py
```

## 📚 Documentation

- [API Documentation](docs/api_documentation.md)
- [User Manual](docs/user_manual.md)
- [Device Onboarding](docs/device_onboarding.md)
- [Troubleshooting Guide](docs/troubleshooting_guide.md)
- [Deployment Guide](docs/deployment_guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, Streamlit, and PostgreSQL
- IoT protocols powered by MQTT
- Machine learning with scikit-learn and XGBoost
- Monitoring with Prometheus and Grafana

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the [troubleshooting guide](docs/troubleshooting_guide.md)
- Review the [documentation](docs/)

---

**Green Engine** - Growing the future, one plant at a time! 🌱✨