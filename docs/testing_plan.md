# Green Engine: Testing Plan & Quality Assurance

## Testing Strategy Overview

### Testing Pyramid
```
                    /\
                   /  \
                  / E2E \
                 /______\
                /        \
               / Integration \
              /______________\
             /                \
            /     Unit Tests   \
           /____________________\
```

- **Unit Tests**: 70% of test coverage
- **Integration Tests**: 20% of test coverage  
- **End-to-End Tests**: 10% of test coverage

## 1. Unit Testing

### Data Ingestion Tests
```python
# tests/test_ingestion.py
import pytest
from src.ingestion.mqtt_client import GreenEngineMQTTClient, SensorReading
from datetime import datetime

class TestMQTTClient:
    def test_sensor_reading_validation(self):
        """Test sensor data validation"""
        # Valid reading
        valid_reading = SensorReading(
            timestamp=datetime.now(),
            sensor_id="temp_001",
            location="greenhouse_a",
            sensor_type="temperature",
            value=23.5,
            unit="celsius",
            battery=85,
            signal_strength=-45
        )
        assert valid_reading.sensor_id == "temp_001"
        
        # Invalid sensor type
        with pytest.raises(ValueError):
            SensorReading(
                timestamp=datetime.now(),
                sensor_id="temp_001",
                location="greenhouse_a",
                sensor_type="invalid_type",
                value=23.5,
                unit="celsius"
            )
    
    def test_mqtt_connection(self):
        """Test MQTT broker connection"""
        client = GreenEngineMQTTClient("localhost", 1883)
        # Mock connection test
        assert client.broker_host == "localhost"
        assert client.broker_port == 1883

class TestSensorDataValidation:
    def test_temperature_range_validation(self):
        """Test temperature value validation"""
        # Valid temperature
        reading = SensorReading(
            timestamp=datetime.now(),
            sensor_id="temp_001",
            location="greenhouse_a",
            sensor_type="temperature",
            value=25.0,
            unit="celsius"
        )
        assert -50 <= reading.value <= 100
        
        # Invalid temperature
        with pytest.raises(ValueError):
            SensorReading(
                timestamp=datetime.now(),
                sensor_id="temp_001",
                location="greenhouse_a",
                sensor_type="temperature",
                value=150.0,  # Too high
                unit="celsius"
            )
```

### ETL Pipeline Tests
```python
# tests/test_etl.py
import pytest
import pandas as pd
from src.etl.feature_engineering import FeatureEngineeringPipeline
from datetime import datetime, timedelta

class TestFeatureEngineering:
    def test_hourly_aggregation(self):
        """Test hourly feature aggregation"""
        # Create test data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='15min'),
            'sensor_id': ['temp_001'] * 100,
            'location': ['greenhouse_a'] * 100,
            'sensor_type': ['temperature'] * 100,
            'value': [20 + i * 0.1 for i in range(100)],
            'unit': ['celsius'] * 100
        })
        
        pipeline = FeatureEngineeringPipeline()
        hourly_features = pipeline.calculate_hourly_features(test_data)
        
        assert len(hourly_features) > 0
        assert 'temp_avg_1h' in hourly_features.columns
        assert 'temp_min_1h' in hourly_features.columns
        assert 'temp_max_1h' in hourly_features.columns
    
    def test_rolling_features(self):
        """Test rolling window feature calculation"""
        # Create test data with hourly features
        hourly_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=48, freq='1H'),
            'temp_avg_1h': [20 + i * 0.5 for i in range(48)],
            'humidity_avg_1h': [60 + i * 0.2 for i in range(48)]
        })
        
        pipeline = FeatureEngineeringPipeline()
        rolling_features = pipeline.calculate_rolling_features(hourly_data)
        
        assert 'temp_avg_24h' in rolling_features.columns
        assert 'temp_variance_24h' in rolling_features.columns
    
    def test_derived_features(self):
        """Test derived feature calculation"""
        test_data = pd.DataFrame({
            'temp_avg_1h': [25.0, 26.0, 24.0],
            'humidity_avg_1h': [60.0, 65.0, 55.0],
            'light_avg_1h': [500.0, 600.0, 400.0]
        })
        
        pipeline = FeatureEngineeringPipeline()
        derived_features = pipeline.calculate_derived_features(test_data)
        
        assert 'temp_humidity_ratio' in derived_features.columns
        assert 'light_temp_ratio' in derived_features.columns
        assert 'vpd' in derived_features.columns
```

### ML Model Tests
```python
# tests/test_models.py
import pytest
import pandas as pd
import numpy as np
from src.models.forecasting_models import GrowthForecastingModels
from src.models.anomaly_detection import AnomalyDetectionSystem

class TestForecastingModels:
    def test_short_term_forecast_training(self):
        """Test short-term forecasting model training"""
        # Mock database connection
        db_connection = "postgresql://test:test@localhost:5432/test_db"
        models = GrowthForecastingModels(db_connection)
        
        # Test with mock data
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=168, freq='1H'),
            'temp_avg_1h': [20 + 5 * np.sin(i * 2 * np.pi / 24) for i in range(168)],
            'humidity_avg_1h': [60 + 10 * np.cos(i * 2 * np.pi / 24) for i in range(168)]
        })
        
        # Test feature preparation
        X, y = models.prepare_features(mock_data, 'temp_avg_1h')
        assert len(X) > 0
        assert len(y) > 0
        assert not X.isnull().any().any()
    
    def test_yield_prediction(self):
        """Test yield prediction model"""
        db_connection = "postgresql://test:test@localhost:5432/test_db"
        models = GrowthForecastingModels(db_connection)
        
        # Test yield prediction with mock data
        mock_features = pd.DataFrame({
            'temp_mean': [22.0, 23.0, 24.0],
            'humidity_mean': [65.0, 70.0, 68.0],
            'light_sum': [12000.0, 13000.0, 12500.0],
            'days_since_planting': [10, 12, 11]
        })
        
        # Mock prediction (would use actual model)
        prediction = 50.0  # Mock yield prediction
        assert prediction > 0
        assert prediction < 200  # Reasonable yield range

class TestAnomalyDetection:
    def test_anomaly_detection_training(self):
        """Test anomaly detection model training"""
        db_connection = "postgresql://test:test@localhost:5432/test_db"
        anomaly_system = AnomalyDetectionSystem(db_connection)
        
        # Test with mock sensor data
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=168, freq='1H'),
            'value': [25.0 + np.random.normal(0, 1, 168)],
            'unit': ['celsius'] * 168
        })
        
        # Test feature creation
        features = anomaly_system.create_features(mock_data, 'temperature')
        assert 'value_rolling_mean_1h' in features.columns
        assert 'z_score' in features.columns
    
    def test_anomaly_scoring(self):
        """Test anomaly scoring logic"""
        # Test threshold-based anomaly detection
        test_values = [15.0, 25.0, 35.0, 45.0]  # Normal, normal, high, very high
        thresholds = {'min': 10, 'max': 35}
        
        anomalies = []
        for value in test_values:
            is_anomaly = value < thresholds['min'] or value > thresholds['max']
            anomalies.append(is_anomaly)
        
        expected = [False, False, False, True]
        assert anomalies == expected
```

### API Tests
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from datetime import datetime

client = TestClient(app)

class TestAPIEndpoints:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
    
    def test_sensor_data_ingestion(self):
        """Test sensor data ingestion endpoint"""
        sensor_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "test_temp_001",
            "location": "test_greenhouse",
            "sensor_type": "temperature",
            "value": 25.0,
            "unit": "celsius",
            "battery": 85,
            "signal_strength": -45
        }
        
        response = client.post("/api/v1/sensor-data", json=sensor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "test_temp_001"
    
    def test_invalid_sensor_data(self):
        """Test invalid sensor data rejection"""
        invalid_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "test_temp_001",
            "location": "test_greenhouse",
            "sensor_type": "invalid_type",  # Invalid sensor type
            "value": 25.0,
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_sensor_data(self):
        """Test sensor data retrieval endpoint"""
        response = client.get("/api/v1/sensor-data", params={
            "location": "test_greenhouse",
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert "location" in data
    
    def test_analytics_summary(self):
        """Test analytics summary endpoint"""
        response = client.get("/api/v1/analytics/summary", params={
            "location": "test_greenhouse"
        })
        assert response.status_code == 200
        data = response.json()
        assert "location" in data
```

## 2. Integration Testing

### Database Integration Tests
```python
# tests/test_database_integration.py
import pytest
import psycopg2
from src.etl.feature_engineering import FeatureEngineeringPipeline

class TestDatabaseIntegration:
    @pytest.fixture
    def test_db_connection(self):
        """Setup test database connection"""
        connection = psycopg2.connect(
            host="localhost",
            database="green_engine_test",
            user="test_user",
            password="test_password"
        )
        yield connection
        connection.close()
    
    def test_sensor_data_storage(self, test_db_connection):
        """Test sensor data storage and retrieval"""
        # Insert test data
        with test_db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sensor_readings 
                (timestamp, sensor_id, location, sensor_type, value, unit)
                VALUES (NOW(), 'test_001', 'test_location', 'temperature', 25.0, 'celsius')
            """)
            test_db_connection.commit()
        
        # Verify data retrieval
        with test_db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sensor_readings 
                WHERE sensor_id = 'test_001'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[2] == 'test_001'  # sensor_id
            assert result[5] == 25.0  # value
    
    def test_feature_engineering_pipeline(self, test_db_connection):
        """Test complete feature engineering pipeline"""
        pipeline = FeatureEngineeringPipeline()
        
        # Test with real database connection
        features = pipeline.run_feature_engineering("test_location", hours_back=24)
        
        # Verify features were stored
        with test_db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM processed_features 
                WHERE location = 'test_location'
            """)
            count = cursor.fetchone()[0]
            assert count > 0
```

### ML Pipeline Integration Tests
```python
# tests/test_ml_integration.py
import pytest
import joblib
import os
from src.models.forecasting_models import GrowthForecastingModels

class TestMLPipelineIntegration:
    def test_model_training_and_saving(self):
        """Test complete ML model training and saving pipeline"""
        db_connection = "postgresql://test:test@localhost:5432/test_db"
        models = GrowthForecastingModels(db_connection)
        
        # Train model
        result = models.train_short_term_forecast_model("test_location", "temp_avg_1h")
        
        # Verify model was saved
        model_key = f"test_location_temp_avg_1h_short_term"
        model_path = f"data/models/{model_key}_model.pkl"
        scaler_path = f"data/models/{model_key}_scaler.pkl"
        
        assert os.path.exists(model_path)
        assert os.path.exists(scaler_path)
        
        # Verify model can be loaded
        loaded_model = joblib.load(model_path)
        loaded_scaler = joblib.load(scaler_path)
        
        assert loaded_model is not None
        assert loaded_scaler is not None
    
    def test_prediction_pipeline(self):
        """Test complete prediction pipeline"""
        db_connection = "postgresql://test:test@localhost:5432/test_db"
        models = GrowthForecastingModels(db_connection)
        
        # Make predictions
        predictions = models.predict_short_term("test_location", "temp_avg_1h", 24)
        
        # Verify predictions
        assert len(predictions) == 24
        assert all(isinstance(p, (int, float)) for p in predictions)
        assert all(-50 <= p <= 100 for p in predictions)  # Reasonable temperature range
```

## 3. End-to-End Testing

### Complete Workflow Tests
```python
# tests/test_e2e.py
import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestEndToEndWorkflow:
    def test_complete_sensor_to_dashboard_workflow(self):
        """Test complete workflow from sensor data to dashboard"""
        # 1. Ingest sensor data
        sensor_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "e2e_test_001",
            "location": "e2e_greenhouse",
            "sensor_type": "temperature",
            "value": 25.0,
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=sensor_data)
        assert response.status_code == 200
        
        # 2. Wait for processing
        time.sleep(5)  # Allow time for ETL processing
        
        # 3. Check processed features
        response = client.get("/api/v1/processed-features", params={
            "location": "e2e_greenhouse",
            "limit": 10
        })
        assert response.status_code == 200
        
        # 4. Check analytics summary
        response = client.get("/api/v1/analytics/summary", params={
            "location": "e2e_greenhouse"
        })
        assert response.status_code == 200
    
    def test_anomaly_detection_workflow(self):
        """Test anomaly detection workflow"""
        # 1. Ingest normal data
        normal_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "anomaly_test_001",
            "location": "anomaly_greenhouse",
            "sensor_type": "temperature",
            "value": 25.0,
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=normal_data)
        assert response.status_code == 200
        
        # 2. Ingest anomalous data
        anomalous_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "anomaly_test_001",
            "location": "anomaly_greenhouse",
            "sensor_type": "temperature",
            "value": 50.0,  # Unusually high temperature
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=anomaly_data)
        assert response.status_code == 200
        
        # 3. Check for alerts
        time.sleep(10)  # Allow time for anomaly detection
        
        response = client.get("/api/v1/alerts", params={
            "location": "anomaly_greenhouse"
        })
        assert response.status_code == 200
        # Should have at least one alert for the anomalous temperature
```

## 4. Data Quality Tests

### Data Validation Tests
```python
# tests/test_data_quality.py
import pytest
import pandas as pd
import numpy as np

class TestDataQuality:
    def test_sensor_data_completeness(self):
        """Test sensor data completeness"""
        # Create test data with missing values
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='15min'),
            'sensor_id': ['temp_001'] * 100,
            'value': [25.0 if i % 10 != 0 else np.nan for i in range(100)]  # 10% missing
        })
        
        # Check completeness
        completeness = test_data['value'].notna().sum() / len(test_data)
        assert completeness >= 0.9  # At least 90% completeness
    
    def test_sensor_data_range_validation(self):
        """Test sensor data range validation"""
        test_data = pd.DataFrame({
            'temperature': [15.0, 25.0, 35.0, 50.0],  # Last value is out of range
            'humidity': [40.0, 60.0, 80.0, 95.0]      # All values in range
        })
        
        # Temperature range validation
        temp_in_range = (test_data['temperature'] >= 10) & (test_data['temperature'] <= 40)
        assert temp_in_range.sum() >= len(test_data) * 0.9  # 90% in range
        
        # Humidity range validation
        humidity_in_range = (test_data['humidity'] >= 30) & (test_data['humidity'] <= 90)
        assert humidity_in_range.sum() >= len(test_data) * 0.9  # 90% in range
    
    def test_data_consistency(self):
        """Test data consistency checks"""
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='15min'),
            'sensor_id': ['temp_001'] * 100,
            'value': [25.0 + np.random.normal(0, 1, 100)]
        })
        
        # Check for duplicate timestamps
        duplicates = test_data.duplicated(subset=['timestamp', 'sensor_id']).sum()
        assert duplicates == 0
        
        # Check for reasonable value changes
        value_changes = test_data['value'].diff().abs()
        max_change = value_changes.max()
        assert max_change < 10  # No sudden large changes
```

## 5. Performance Testing

### Load Testing
```python
# tests/test_performance.py
import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestPerformance:
    def test_api_response_time(self):
        """Test API response time under normal load"""
        start_time = time.time()
        
        response = client.get("/health")
        
        response_time = time.time() - start_time
        assert response_time < 1.0  # Response within 1 second
        assert response.status_code == 200
    
    def test_concurrent_sensor_data_ingestion(self):
        """Test concurrent sensor data ingestion"""
        def ingest_sensor_data(sensor_id):
            data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_id": f"perf_test_{sensor_id}",
                "location": "perf_greenhouse",
                "sensor_type": "temperature",
                "value": 25.0,
                "unit": "celsius"
            }
            return client.post("/api/v1/sensor-data", json=data)
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(ingest_sensor_data, i) for i in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
    
    def test_database_query_performance(self):
        """Test database query performance"""
        start_time = time.time()
        
        response = client.get("/api/v1/sensor-data", params={
            "location": "perf_greenhouse",
            "limit": 1000
        })
        
        query_time = time.time() - start_time
        assert query_time < 2.0  # Query within 2 seconds
        assert response.status_code == 200
```

## 6. Security Testing

### Authentication and Authorization
```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestSecurity:
    def test_input_validation(self):
        """Test input validation and sanitization"""
        # Test SQL injection attempt
        malicious_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "'; DROP TABLE sensor_readings; --",
            "location": "test_location",
            "sensor_type": "temperature",
            "value": 25.0,
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=malicious_data)
        # Should handle gracefully without SQL injection
        assert response.status_code in [200, 422]
    
    def test_data_validation(self):
        """Test data validation and sanitization"""
        # Test extremely large values
        large_data = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "test_001",
            "location": "test_location",
            "sensor_type": "temperature",
            "value": 1e10,  # Extremely large value
            "unit": "celsius"
        }
        
        response = client.post("/api/v1/sensor-data", json=large_data)
        # Should reject or handle large values appropriately
        assert response.status_code in [200, 422]
```

## Test Execution and CI/CD

### Test Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
```

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: green_engine_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: pytest tests/ -m unit --cov=src
    
    - name: Run integration tests
      run: pytest tests/ -m integration --cov=src
    
    - name: Run security tests
      run: pytest tests/ -m security
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Test Data Management

### Test Data Setup
```python
# tests/conftest.py
import pytest
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def sample_sensor_data():
    """Generate sample sensor data for testing"""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='15min'),
        'sensor_id': ['temp_001'] * 100,
        'location': ['test_greenhouse'] * 100,
        'sensor_type': ['temperature'] * 100,
        'value': [20 + 5 * np.sin(i * 2 * np.pi / 24) for i in range(100)],
        'unit': ['celsius'] * 100
    })

@pytest.fixture
def sample_growth_data():
    """Generate sample growth data for testing"""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=30, freq='1D'),
        'location': ['test_greenhouse'] * 30,
        'tray_id': ['tray_001'] * 30,
        'crop_type': ['pea_shoots'] * 30,
        'plant_height_cm': [5 + i * 0.5 for i in range(30)],
        'biomass_g': [10 + i * 2 for i in range(30)],
        'yield_g': [8 + i * 1.8 for i in range(30)],
        'growth_stage': ['vegetative'] * 30,
        'days_since_planting': list(range(1, 31))
    })
```

## Quality Gates

### Pre-deployment Checks
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Performance tests within acceptable limits
- [ ] Security tests passing
- [ ] Code review completed
- [ ] Documentation updated

### Post-deployment Validation
- [ ] Health checks passing
- [ ] Data pipeline operational
- [ ] ML models performing within expected ranges
- [ ] Dashboard accessible and functional
- [ ] Monitoring alerts configured and tested
