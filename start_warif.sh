#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Kill existing processes
pkill -f uvicorn
pkill -f streamlit

# Set environment variables (override in .env for production)
export DB_HOST=${DB_HOST:-localhost}
export DB_NAME=${DB_NAME:-warif}
export DB_USER=${DB_USER:-warif_user}
export DB_PASSWORD=${DB_PASSWORD:-warif_pass}
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-change-this-in-production}
export JWT_ALGORITHM=HS256
export PYTHONPATH=$(pwd)

echo "Starting Warif Digital Twin..."

# Start API server
echo "Starting API on port 8010..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload &
API_PID=$!

sleep 4

# Start dashboard
echo "Starting dashboard on port 8501..."
python3 -m streamlit run dashboard/app.py --server.port 8501 --server.address localhost &
DASHBOARD_PID=$!

echo ""
echo "Warif is running!"
echo "  Dashboard : http://localhost:8501"
echo "  API       : http://localhost:8010"
echo "  API Docs  : http://localhost:8010/docs"
echo ""
echo "Press Ctrl+C to stop"

wait
