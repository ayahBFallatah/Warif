#!/bin/bash

# Set environment variables
export DB_HOST=postgres
export DB_NAME=green_engine
export DB_USER=green_user
export DB_PASSWORD=green_pass
export DB_PORT=5432
export JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
export JWT_ALGORITHM=HS256
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
export MQTT_BROKER_HOST=localhost
export MQTT_BROKER_PORT=1883
export MQTT_USE_TLS=false
export MQTT_CMD_BASE=greenengine
export AUTH_REQUIRED=true
export ENCRYPTION_KEY=your-encryption-key-for-passwords

echo "🚀 Starting Green Engine API Server..."
echo "Environment variables set:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_NAME: $DB_NAME"
echo "  DB_USER: $DB_USER"
echo "  JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:20}..."
echo "  AUTH_REQUIRED: $AUTH_REQUIRED"

# Start the API server
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload
