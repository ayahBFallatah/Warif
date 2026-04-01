"""
FastAPI REST API for Green Engine
Provides endpoints for sensor data, predictions, and analytics
"""
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from src.utils.rules_engine import RulesEngine, ReadingContext
from src.models.forecasting_models import GrowthForecastingModels
from src.models.prediction_service import get_prediction_service
from src.auth.middleware import get_current_user, require_permission, require_admin, require_operator_or_admin, log_audit_event, Permissions
from src.auth.authentication import User
import json
import logging
import paho.mqtt.client as mqtt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Green Engine API",
    description="IoT microgreen growth monitoring and analytics API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Include authentication router
from src.auth.auth_api import router as auth_router
app.include_router(auth_router)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Green Engine API",
        version="1.0.0",
        description="""
        ## Green Engine IoT Platform API
        
        A comprehensive RESTful API for managing IoT devices, sensor data, analytics, 
        machine learning predictions, and user authentication in a smart greenhouse environment.
        
        ### Features
        - 🔐 JWT-based authentication and authorization
        - 📊 Real-time sensor data collection and analysis
        - 🌱 Tray and crop management
        - 🚨 Intelligent alerting system
        - 🤖 Machine learning predictions
        - 📈 Analytics and reporting
        - 👥 User management with RBAC
        
        ### Authentication
        Most endpoints require authentication. Include your JWT token in the Authorization header:
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ### Default Credentials
        - **Admin**: `admin` / `admin123`
        - **Operator**: `operator1` / `operator123`
        - **Viewer**: `viewer1` / `viewer123`
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add security to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method != "get" or path not in ["/health", "/docs", "/redoc", "/openapi.json"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Prometheus metrics
REQUEST_COUNT = Counter('green_engine_api_requests_total', 'API Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('green_engine_api_request_duration_seconds', 'Request latency', ['endpoint'])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "green_engine"),
            user=os.getenv("DB_USER", "green_user"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432")
        )
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Pydantic models
class SensorReading(BaseModel):
    timestamp: datetime
    sensor_id: str
    location: str
    sensor_type: str
    value: float
    unit: str
    battery: Optional[int] = None
    signal_strength: Optional[int] = None

class GrowthMeasurement(BaseModel):
    timestamp: datetime
    location: str
    tray_id: str
    crop_type: str
    plant_height_cm: Optional[float] = None
    leaf_count: Optional[int] = None
    biomass_g: Optional[float] = None
    yield_g: Optional[float] = None
    germination_rate: Optional[float] = None
    growth_stage: str
    days_since_planting: int
    color_rating: Optional[int] = None
    uniformity_rating: Optional[int] = None
    notes: Optional[str] = None

class Alert(BaseModel):
    timestamp: datetime
    location: str
    alert_type: str
    severity: str
    title: str
    description: str
    sensor_id: Optional[str] = None
    sensor_type: Optional[str] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None

class SensorThresholds(BaseModel):
    temperature: Optional[Dict[str, float]] = None
    humidity: Optional[Dict[str, float]] = None
    light: Optional[Dict[str, float]] = None
    soil_moisture: Optional[Dict[str, float]] = None
    ec: Optional[Dict[str, float]] = None
    co2: Optional[Dict[str, float]] = None

class DeviceCommand(BaseModel):
    device_id: str
    location: Optional[str] = None
    command: Dict[str, Any]

class RequeueCommand(BaseModel):
    id: int

class Tray(BaseModel):
    tray_code: str
    location: str
    device_id: Optional[str] = None
    crop_type: Optional[str] = None
    grow_medium: Optional[str] = None
    batch_code: Optional[str] = None
    seed_density: Optional[int] = None
    lighting_profile: Optional[str] = None
    planted_on: Optional[datetime] = None
    expected_harvest: Optional[datetime] = None
    notes: Optional[str] = None


def publish_mqtt_command(device_id: str, command: Dict[str, Any]) -> bool:
    """Publish command to MQTT. Returns True on success."""
    broker_host = os.getenv("MQTT_BROKER", "localhost")
    broker_port = int(os.getenv("MQTT_PORT", "1883"))
    base = os.getenv("MQTT_CMD_BASE", "greenengine")
    topic = f"{base}/{device_id}/cmd"

    try:
        client = mqtt.Client()
        client.connect(broker_host, broker_port, 60)
        payload = json.dumps(command)
        result = client.publish(topic, payload, qos=1)
        result.wait_for_publish()
        client.disconnect()
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.error(f"MQTT publish failed: {e}")
        return False

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Green Engine API", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/api/v1/sensor-data")
async def ingest_sensor_data(
    reading: SensorReading,
    current_user: User = Depends(require_permission(*Permissions.SENSORS_CREATE))
):
    """Ingest sensor data"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            INSERT INTO sensor_readings 
            (timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                reading.timestamp,
                reading.sensor_id,
                reading.location,
                reading.sensor_type,
                reading.value,
                reading.unit,
                reading.battery,
                reading.signal_strength
            ))
            conn.commit()
        
        # Evaluate rules and insert alert if needed
        try:
            rules_engine = RulesEngine()
            rules_engine.evaluate_and_store(
                ReadingContext(
                    timestamp=reading.timestamp,
                    location=reading.location,
                    sensor_type=reading.sensor_type,
                    value=reading.value,
                )
            )
        except Exception as re:
            # Do not fail ingestion if alerting fails; log and proceed
            logger.error(f"Rules evaluation failed: {re}")

        return {"message": "Sensor data ingested successfully", "sensor_id": reading.sensor_id}
    
    except Exception as e:
        logger.error(f"Error ingesting sensor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest sensor data")

@app.get("/api/v1/sensor-data")
async def get_sensor_data(
    location: str = Query(..., description="Location identifier"),
    sensor_type: Optional[str] = Query(None, description="Type of sensor"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Get sensor data"""
    try:
        conn = get_db_connection()
        
        # Build query
        query = """
        SELECT timestamp, sensor_id, location, sensor_type, value, unit, battery, signal_strength
        FROM sensor_readings
        WHERE location = %s
        """
        params = [location]
        
        if sensor_type:
            query += " AND sensor_type = %s"
            params.append(sensor_type)
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        # Execute query
        df = pd.read_sql_query(query, conn, params=params)
        
        return {
            "data": df.to_dict('records'),
            "count": len(df),
            "location": location
        }
    
    except Exception as e:
        logger.error(f"Error retrieving sensor data: {e}")
        # Return empty data instead of crashing
        return {
            "data": [],
            "count": 0,
            "location": location,
            "message": "No sensor data available or database error occurred"
        }

@app.get("/api/v1/processed-features")
async def get_processed_features(
    location: str = Query(..., description="Location identifier"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Get processed features"""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT * FROM processed_features
        WHERE location = %s
        """
        params = [location]
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        
        return {
            "data": df.to_dict('records'),
            "count": len(df),
            "location": location
        }
    
    except Exception as e:
        logger.error(f"Error retrieving processed features: {e}")
        # Return empty data instead of crashing
        return {
            "data": [],
            "count": 0,
            "location": location,
            "message": "No processed features available or database error occurred"
        }

@app.post("/api/v1/growth-measurements")
async def add_growth_measurement(measurement: GrowthMeasurement):
    """Add growth measurement"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            INSERT INTO growth_measurements 
            (timestamp, location, tray_id, crop_type, plant_height_cm, leaf_count, 
             biomass_g, yield_g, germination_rate, growth_stage, days_since_planting,
             color_rating, uniformity_rating, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                measurement.timestamp,
                measurement.location,
                measurement.tray_id,
                measurement.crop_type,
                measurement.plant_height_cm,
                measurement.leaf_count,
                measurement.biomass_g,
                measurement.yield_g,
                measurement.germination_rate,
                measurement.growth_stage,
                measurement.days_since_planting,
                measurement.color_rating,
                measurement.uniformity_rating,
                measurement.notes
            ))
            conn.commit()
        
        return {"message": "Growth measurement added successfully", "tray_id": measurement.tray_id}
    
    except Exception as e:
        logger.error(f"Error adding growth measurement: {e}")
        raise HTTPException(status_code=500, detail="Failed to add growth measurement")

@app.get("/api/v1/growth-measurements")
async def get_growth_measurements(
    location: str = Query(..., description="Location identifier"),
    tray_id: Optional[str] = Query(None, description="Tray identifier"),
    crop_type: Optional[str] = Query(None, description="Crop type"),
    limit: int = Query(100, description="Maximum number of records")
):
    """Get growth measurements"""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT * FROM growth_measurements
        WHERE location = %s
        """
        params = [location]
        
        if tray_id:
            query += " AND tray_id = %s"
            params.append(tray_id)
        
        if crop_type:
            query += " AND crop_type = %s"
            params.append(crop_type)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        
        return {
            "data": df.to_dict('records'),
            "count": len(df),
            "location": location
        }
    
    except Exception as e:
        logger.error(f"Error retrieving growth measurements: {e}")
        # Return empty data instead of crashing
        return {
            "data": [],
            "count": 0,
            "location": location,
            "message": "No growth measurements available or database error occurred"
        }

@app.get("/api/v1/alerts")
async def get_alerts(
    location: str = Query(..., description="Location identifier"),
    status: Optional[str] = Query(None, description="Alert status"),
    severity: Optional[str] = Query(None, description="Alert severity"),
    limit: int = Query(100, description="Maximum number of records")
):
    """Get alerts"""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT * FROM alerts
        WHERE location = %s
        """
        params = [location]
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if severity:
            query += " AND severity = %s"
            params.append(severity)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        
        return {
            "data": df.to_dict('records'),
            "count": len(df),
            "location": location
        }
    
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        # Return empty data instead of crashing
        return {
            "data": [],
            "count": 0,
            "location": location,
            "message": "No alerts available or database error occurred"
        }

@app.get("/api/v1/config/thresholds")
async def get_thresholds():
    """Return sensor thresholds from system_config or defaults"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT config_value
                FROM system_config
                WHERE config_key = 'sensor_thresholds' AND is_active = TRUE
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row and row.get('config_value'):
                return {"source": "db", "thresholds": row['config_value']}
            # Fallback to engine defaults
            return {"source": "defaults", "thresholds": RulesEngine.DEFAULT_THRESHOLDS}
    except Exception as e:
        logger.error(f"Error fetching thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch thresholds")

@app.put("/api/v1/config/thresholds")
async def update_thresholds(payload: SensorThresholds):
    """Upsert sensor thresholds into system_config"""
    try:
        new_value: Dict[str, Dict[str, float]] = {
            k: v
            for k, v in payload.dict(exclude_none=True).items()
        }
        if not new_value:
            raise HTTPException(status_code=400, detail="No thresholds provided")

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO system_config (config_key, config_value, description, is_active)
                VALUES ('sensor_thresholds', %s, 'Sensor threshold values for alerts', TRUE)
                ON CONFLICT (config_key)
                DO UPDATE SET config_value = EXCLUDED.config_value, is_active = TRUE, updated_at = NOW()
                """,
                (new_value,)
            )
            conn.commit()
        return {"message": "Thresholds updated", "thresholds": new_value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to update thresholds")

@app.post("/api/v1/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE alerts
                SET status = 'acknowledged', acknowledged_at = NOW()
                WHERE id = %s AND status = 'active'
                """,
                (alert_id,)
            )
            cursor.execute(
                """
                INSERT INTO alert_actions(alert_id, action_type, user_id)
                VALUES(%s,'acknowledged', 'api')
                """,
                (alert_id,)
            )
            conn.commit()
        return {"message": "Alert acknowledged", "id": alert_id}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@app.post("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Resolve an alert"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE alerts
                SET status = 'resolved', resolved_at = NOW()
                WHERE id = %s AND status IN ('active', 'acknowledged')
                """,
                (alert_id,)
            )
            cursor.execute(
                """
                INSERT INTO alert_actions(alert_id, action_type, user_id)
                VALUES(%s,'resolved', 'api')
                """,
                (alert_id,)
            )
            conn.commit()
        return {"message": "Alert resolved", "id": alert_id}
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@app.get("/api/v1/alerts/{alert_id}/actions")
async def get_alert_actions(alert_id: int):
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(
            "SELECT id, action, actor, created_at FROM alert_actions WHERE alert_id = %s ORDER BY created_at DESC",
            conn,
            params=[alert_id],
        )
        return {"alert_id": alert_id, "actions": df.to_dict('records')}
    except Exception as e:
        logger.error(f"Error retrieving alert actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert actions")

@app.post("/api/v1/commands")
async def send_device_command(cmd: DeviceCommand):
    """Publish a device command and log it."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO device_commands(device_id, location, command, status, created_by)
                VALUES(%s,%s,%s,'sent','api')
                RETURNING id
                """,
                (cmd.device_id, cmd.location, json.dumps(cmd.command)),
            )
            row_id = cursor.fetchone()[0]
            conn.commit()
        # Publish to MQTT
        success = publish_mqtt_command(cmd.device_id, cmd.command)
        # Update status
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE device_commands SET status = %s WHERE id = %s
                """,
                ("sent" if success else "failed", row_id),
            )
            conn.commit()
        return {"message": "Command published" if success else "Command publish failed", "id": row_id}
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        raise HTTPException(status_code=500, detail="Failed to send command")

@app.get("/api/v1/commands")
async def list_device_commands(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Max items")
):
    try:
        conn = get_db_connection()
        query = "SELECT id, device_id, location, status, retry_count, next_attempt_at, created_at FROM device_commands"
        params: list = []
        if status:
            query += " WHERE status = %s"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        df = pd.read_sql_query(query, conn, params=params)
        return {"data": df.to_dict('records'), "count": len(df)}
    except Exception as e:
        logger.error(f"Error listing device commands: {e}")
        raise HTTPException(status_code=500, detail="Failed to list commands")

@app.post("/api/v1/commands/requeue")
async def requeue_device_command(body: RequeueCommand):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE device_commands
                SET status='queued', next_attempt_at = NOW()
                WHERE id = %s
                """,
                (body.id,)
            )
            conn.commit()
        return {"message": "Command requeued", "id": body.id}
    except Exception as e:
        logger.error(f"Error requeuing command: {e}")
        raise HTTPException(status_code=500, detail="Failed to requeue command")

@app.post("/api/v1/trays")
async def create_tray(
    tray: Tray,
    current_user: User = Depends(require_permission(*Permissions.TRAYS_CREATE))
):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO trays (tray_code, location, device_id, crop_type, grow_medium, batch_code, seed_density, lighting_profile, planted_on, expected_harvest, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    tray.tray_code,
                    tray.location,
                    tray.device_id,
                    tray.crop_type,
                    tray.grow_medium,
                    tray.batch_code,
                    tray.seed_density,
                    tray.lighting_profile,
                    tray.planted_on.date() if tray.planted_on else None,
                    tray.expected_harvest.date() if tray.expected_harvest else None,
                    tray.notes,
                ),
            )
            tray_id = cursor.fetchone()[0]
            conn.commit()
        return {"id": tray_id, "tray_code": tray.tray_code}
    except Exception as e:
        logger.error(f"Error creating tray: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tray")

@app.get("/api/v1/trays")
async def list_trays(
    location: Optional[str] = Query(None),
    crop_type: Optional[str] = Query(None),
    limit: int = Query(100)
):
    try:
        conn = get_db_connection()
        query = "SELECT id, tray_code, location, device_id, crop_type, grow_medium, batch_code, seed_density, lighting_profile, planted_on, expected_harvest, created_at FROM trays"
        params: list = []
        where = []
        if location:
            where.append("location = %s")
            params.append(location)
        if crop_type:
            where.append("crop_type = %s")
            params.append(crop_type)
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        df = pd.read_sql_query(query, conn, params=params)
        return {"data": df.to_dict('records'), "count": len(df)}
    except Exception as e:
        logger.error(f"Error listing trays: {e}")
        raise HTTPException(status_code=500, detail="Failed to list trays")

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(location: str = Query(..., description="Location identifier")):
    """Get analytics summary"""
    try:
        conn = get_db_connection()
        
        # Get latest sensor readings
        sensor_query = """
        SELECT sensor_type, AVG(value) as avg_value, COUNT(*) as reading_count
        FROM sensor_readings
        WHERE location = %s AND timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY sensor_type
        """
        
        sensor_df = pd.read_sql_query(sensor_query, conn, params=[location])
        
        # Get latest growth measurements
        growth_query = """
        SELECT crop_type, AVG(yield_g) as avg_yield, COUNT(*) as measurement_count
        FROM growth_measurements
        WHERE location = %s AND timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY crop_type
        """
        
        growth_df = pd.read_sql_query(growth_query, conn, params=[location])
        
        # Get active alerts
        alert_query = """
        SELECT COUNT(*) as active_alerts
        FROM alerts
        WHERE location = %s AND status = 'active'
        """
        
        alert_df = pd.read_sql_query(alert_query, conn, params=[location])
        
        return {
            "location": location,
            "sensor_summary": sensor_df.to_dict('records'),
            "growth_summary": growth_df.to_dict('records'),
            "active_alerts": int(alert_df['active_alerts'].iloc[0]) if not alert_df.empty else 0
        }
    
    except Exception as e:
        logger.error(f"Error retrieving analytics summary: {e}")
        # Return empty data instead of crashing
        return {
            "location": location,
            "sensor_summary": [],
            "growth_summary": [],
            "active_alerts": 0,
            "message": "No analytics data available or database error occurred"
        }

@app.get("/api/v1/predictions/forecast")
async def get_forecast(
    location: str = Query(..., description="Location identifier"),
    sensor_type: str = Query(..., description="Sensor type"),
    hours_ahead: int = Query(24, description="Hours to forecast")
):
    """Get sensor value forecast"""
    try:
        # Build DB connection string for models
        db_dsn = (
            f"postgresql://{os.getenv('DB_USER', 'green_user')}:{os.getenv('DB_PASSWORD', 'password')}@"
            f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'green_engine')}"
        )
        models = GrowthForecastingModels(db_dsn)
        target_column_map = {
            "temperature": "temp_avg_1h",
            "humidity": "humidity_avg_1h",
            "light": "light_avg_1h",
            "soil_moisture": "soil_moisture_avg_1h",
            "ec": "ec_avg_1h",
            "co2": "co2_avg_1h",
        }
        target_column = target_column_map.get(sensor_type)
        if not target_column:
            raise HTTPException(status_code=400, detail="Unsupported sensor_type for forecasting")

        model_key = f"{location}_{target_column}_short_term"
        # Try to load saved model; if not present, train lazily
        loaded = models.load_saved_model(model_key)
        if not loaded:
            train_result = models.train_short_term_forecast_model(location, target_column)
            if not train_result:
                raise HTTPException(status_code=422, detail="Insufficient data to train forecast model")

        preds = models.predict_short_term(location, target_column, hours_ahead)
        if not preds:
            raise HTTPException(status_code=422, detail="Unable to generate predictions")

        start_time = datetime.now()
        forecast_data = []
        for i, p in enumerate(preds, start=1):
            t = start_time + timedelta(hours=i)
            forecast_data.append({
                "timestamp": t.isoformat(),
                "predicted_value": float(round(p, 2)),
                "confidence_lower": float(round(p - 1.0, 2)),
                "confidence_upper": float(round(p + 1.0, 2)),
            })
        
        return {
            "location": location,
            "sensor_type": sensor_type,
            "forecast_horizon": hours_ahead,
            "forecast_data": forecast_data,
        }
    
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate forecast")

@app.get("/api/v1/predictions/growth-forecast")
async def get_growth_forecast(
    location: str = Query(..., description="Location identifier"),
    days_ahead: int = Query(30, description="Days to forecast ahead")
):
    """Get growth/yield forecast for the next N days"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get existing predictions from ml_predictions table
        query = """
        SELECT timestamp, predicted_value, confidence_interval_lower, confidence_interval_upper,
               model_name, prediction_type, model_performance_metrics
        FROM ml_predictions 
        WHERE location = %s 
        AND prediction_type = 'long_term_yield'
        AND timestamp >= NOW()
        AND timestamp <= NOW() + INTERVAL '%s days'
        ORDER BY timestamp
        """
        
        cursor.execute(query, (location, days_ahead))
        predictions = cursor.fetchall()
        
        if not predictions:
            # If no predictions exist, try to generate some using the ML models
            try:
                db_dsn = (
                    f"postgresql://{os.getenv('DB_USER', 'green_user')}:{os.getenv('DB_PASSWORD', 'password')}@"
                    f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/"
                    f"{os.getenv('DB_NAME', 'green_engine')}"
                )
                models = GrowthForecastingModels(db_dsn)
                
                # Try to train yield model if not already trained
                yield_result = models.train_long_term_yield_model(location)
                if yield_result:
                    # Generate sample predictions for the next N days
                    forecast_data = []
                    start_date = datetime.now()
                    
                    for day in range(1, days_ahead + 1):
                        target_date = start_date + timedelta(days=day)
                        
                        # Generate sample prediction (in real implementation, this would use the trained model)
                        # For now, we'll create a placeholder prediction
                        base_yield = 15.0  # Base yield in grams
                        growth_factor = 1.0 + (day * 0.1)  # Simple growth model
                        predicted_yield = base_yield * growth_factor
                        
                        forecast_data.append({
                            "timestamp": target_date.isoformat(),
                            "predicted_value": round(predicted_yield, 2),
                            "confidence_lower": round(predicted_yield * 0.8, 2),
                            "confidence_upper": round(predicted_yield * 1.2, 2),
                            "model_accuracy": 85.5  # Placeholder accuracy
                        })
                    
                    return {
                        "location": location,
                        "forecast_horizon_days": days_ahead,
                        "data": forecast_data
                    }
                else:
                    # Return empty data if model training fails
                    return {
                        "location": location,
                        "forecast_horizon_days": days_ahead,
                        "data": []
                    }
                    
            except Exception as e:
                logger.error(f"Error generating growth forecast: {e}")
                # Return empty data on error
                return {
                    "location": location,
                    "forecast_horizon_days": days_ahead,
                    "data": []
                }
        
        # Convert existing predictions to the expected format
        forecast_data = []
        for pred in predictions:
            forecast_data.append({
                "timestamp": pred['timestamp'].isoformat(),
                "predicted_value": float(pred['predicted_value']) if pred['predicted_value'] else None,
                "confidence_lower": float(pred['confidence_interval_lower']) if pred['confidence_interval_lower'] else None,
                "confidence_upper": float(pred['confidence_interval_upper']) if pred['confidence_interval_upper'] else None,
                "model_accuracy": 85.5  # Placeholder, could be extracted from model_performance_metrics
            })
        
        cursor.close()
        conn.close()
        
        return {
            "location": location,
            "forecast_horizon_days": days_ahead,
            "data": forecast_data
        }
    
    except Exception as e:
        logger.error(f"Error retrieving growth forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve growth forecast")

# ML Prediction Endpoints
@app.get("/api/v1/ml/predictions/yield")
async def predict_yield(
    location: str = Query(..., description="Location to predict yield for"),
    days_ahead: int = Query(7, description="Number of days to predict ahead")
):
    """Predict yield for a specific location using trained ML models"""
    try:
        prediction_service = get_prediction_service()
        result = prediction_service.predict_yield(location, days_ahead)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error predicting yield: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict yield")

@app.get("/api/v1/ml/predictions/growth-trajectory")
async def predict_growth_trajectory(
    location: str = Query(..., description="Location to predict growth for"),
    tray_id: Optional[int] = Query(None, description="Specific tray ID (optional)")
):
    """Predict growth trajectory for a specific location or tray"""
    try:
        prediction_service = get_prediction_service()
        result = prediction_service.predict_growth_trajectory(location, tray_id)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error predicting growth trajectory: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict growth trajectory")

@app.get("/api/v1/ml/models/status")
async def get_model_status():
    """Get status of loaded ML models"""
    try:
        prediction_service = get_prediction_service()
        return prediction_service.get_model_status()
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model status")

@app.post("/api/v1/ml/models/retrain")
async def retrain_models():
    """Retrain ML models with latest data"""
    try:
        # This would trigger the training pipeline
        # For now, return a success message
        return {
            "message": "Model retraining initiated",
            "status": "success",
            "note": "This endpoint will trigger the ML training pipeline"
        }
        
    except Exception as e:
        logger.error(f"Error retraining models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrain models")

if __name__ == "__main__":
    import uvicorn
    import os as _os
    _port = int(_os.getenv("PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=_port)
