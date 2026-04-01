#!/bin/bash

# Kill existing processes
pkill -f uvicorn
pkill -f streamlit

# Set environment variables
export DB_HOST=localhost
export DB_NAME=green_engine
export DB_USER=green_user
export DB_PASSWORD=green_pass
export JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
export JWT_ALGORITHM=HS256
export AUTH_REQUIRED=false

echo "🚀 Starting Green Engine..."

# Start API server in background
echo "Starting API server on port 8010..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload &
API_PID=$!

# Wait for API to start
sleep 5

# Start dashboard
echo "Starting dashboard on port 8501..."
cd dashboard
python3 -m streamlit run app.py --server.port 8501 --server.address localhost &
DASHBOARD_PID=$!

echo "✅ Green Engine started successfully!"
echo "📊 Dashboard: http://localhost:8501"
echo "🔗 API: http://localhost:8010"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
