# Green Engine API Documentation

## Overview

The Green Engine API provides a comprehensive RESTful interface for managing IoT devices, sensor data, analytics, machine learning predictions, and user authentication in a smart greenhouse environment.

## Base URL

- **Development**: `http://localhost:8010`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. **Login** to get a JWT token:
   ```bash
   curl -X POST "http://localhost:8010/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}'
   ```

2. **Use the token** in subsequent requests:
   ```bash
   curl -X GET "http://localhost:8010/api/v1/sensor-data" \
        -H "Authorization: Bearer <your-token>"
   ```

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@greenengine.com",
    "roles": ["admin"],
    "permissions": {...}
  }
}
```

#### POST /api/v1/auth/logout
Logout user and invalidate token.

#### GET /api/v1/auth/me
Get current user information.

### Sensor Data Endpoints

#### GET /api/v1/sensor-data
Retrieve sensor data with optional filtering.

**Query Parameters:**
- `device_id` (string): Filter by device ID
- `start_time` (datetime): Start time for data range
- `end_time` (datetime): End time for data range
- `limit` (int): Maximum number of records (default: 100)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "device_id": "GH-A1-DEV-01",
      "timestamp": "2025-01-15T10:30:00Z",
      "temperature": 23.5,
      "humidity": 68.0,
      "par": 450.0,
      "soil_moisture": 35.0,
      "ec": 1.2,
      "co2": 650.0
    }
  ],
  "total": 1,
  "message": "Sensor data retrieved successfully"
}
```

#### POST /api/v1/sensor-data
Create new sensor reading (requires authentication).

**Request Body:**
```json
{
  "device_id": "GH-A1-DEV-01",
  "timestamp": "2025-01-15T10:30:00Z",
  "temperature": 23.5,
  "humidity": 68.0,
  "par": 450.0,
  "soil_moisture": 35.0,
  "ec": 1.2,
  "co2": 650.0
}
```

### Tray Management Endpoints

#### GET /api/v1/trays
Retrieve all trays.

**Response:**
```json
{
  "data": [
    {
      "tray_id": 1,
      "tray_code": "TRAY-001",
      "device_id": "GH-A1-DEV-01",
      "crop_type": "lettuce",
      "planted_on": "2025-01-01",
      "expected_harvest": "2025-02-15",
      "grow_medium": "coco_coir",
      "batch_lot": "BATCH-2025-001",
      "seed_density": 25,
      "lighting_profile": "18/6",
      "notes": "First batch of lettuce"
    }
  ],
  "total": 1
}
```

#### POST /api/v1/trays
Create new tray (requires authentication).

**Request Body:**
```json
{
  "tray_code": "TRAY-002",
  "device_id": "GH-A1-DEV-01",
  "crop_type": "tomato",
  "planted_on": "2025-01-15",
  "expected_harvest": "2025-03-15",
  "grow_medium": "hydroponic",
  "batch_lot": "BATCH-2025-002",
  "seed_density": 12,
  "lighting_profile": "16/8",
  "notes": "Tomato seedlings"
}
```

### Alert Management Endpoints

#### GET /api/v1/alerts
Retrieve alerts with optional filtering.

**Query Parameters:**
- `status` (string): Filter by status (active, acknowledged, resolved)
- `level` (string): Filter by level (info, warning, critical)
- `device_id` (string): Filter by device ID

#### POST /api/v1/alerts/{alert_id}/ack
Acknowledge an alert (requires operator or admin role).

#### POST /api/v1/alerts/{alert_id}/resolve
Resolve an alert (requires operator or admin role).

### Device Command Endpoints

#### GET /api/v1/commands
Retrieve device command history.

#### POST /api/v1/commands
Send command to device (requires operator or admin role).

**Request Body:**
```json
{
  "device_id": "GH-A1-DEV-01",
  "command_type": "irrigation",
  "parameters": {
    "duration": 300,
    "intensity": "medium"
  }
}
```

#### POST /api/v1/commands/requeue
Requeue failed commands (requires operator or admin role).

### Configuration Endpoints

#### GET /api/v1/config/thresholds
Retrieve sensor thresholds configuration.

#### PUT /api/v1/config/thresholds
Update sensor thresholds (requires admin role).

**Request Body:**
```json
{
  "temperature": {
    "min": 18.0,
    "max": 28.0
  },
  "humidity": {
    "min": 40.0,
    "max": 80.0
  },
  "soil_moisture": {
    "min": 20.0,
    "max": 60.0
  }
}
```

### Machine Learning Endpoints

#### GET /api/v1/ml/predictions/yield
Get yield predictions for trays.

#### GET /api/v1/ml/predictions/growth-trajectory
Get growth trajectory predictions.

#### GET /api/v1/ml/models/status
Get ML model status and performance metrics.

#### POST /api/v1/ml/models/retrain
Trigger model retraining (requires admin role).

### Analytics Endpoints

#### GET /api/v1/analytics/summary
Get analytics summary with key metrics.

**Response:**
```json
{
  "total_devices": 2,
  "active_alerts": 1,
  "total_trays": 5,
  "avg_temperature": 23.5,
  "avg_humidity": 65.0,
  "growth_rate": 0.15,
  "yield_prediction": 2.3
}
```

### User Management Endpoints

#### GET /api/v1/users
Retrieve all users (requires admin role).

#### POST /api/v1/users
Create new user (requires admin role).

#### PUT /api/v1/users/{user_id}
Update user (requires admin role).

#### DELETE /api/v1/users/{user_id}
Delete user (requires admin role).

### System Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### GET /metrics
Prometheus metrics endpoint.

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

## SDKs and Libraries

### Python
```python
import requests

# Login
response = requests.post('http://localhost:8010/api/v1/auth/login', 
                        json={'username': 'admin', 'password': 'admin123'})
token = response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8010/api/v1/sensor-data', headers=headers)
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

// Login
const loginResponse = await axios.post('http://localhost:8010/api/v1/auth/login', {
  username: 'admin',
  password: 'admin123'
});

const token = loginResponse.data.access_token;

// Make authenticated request
const response = await axios.get('http://localhost:8010/api/v1/sensor-data', {
  headers: { Authorization: `Bearer ${token}` }
});
```

## WebSocket Support

Real-time updates are available via WebSocket connection:

```javascript
const ws = new WebSocket('ws://localhost:8010/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

## Changelog

### Version 1.0.0
- Initial API release
- Authentication and authorization
- Sensor data management
- Tray management
- Alert system
- Device commands
- Machine learning predictions
- User management
- Analytics and reporting
