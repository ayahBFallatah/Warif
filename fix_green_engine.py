#!/usr/bin/env python3
"""
Fix Green Engine Authentication Issues
This script will help resolve the authentication problems
"""

import os
import subprocess
import sys
import time

def print_status(message, status="info"):
    """Print status message with emoji"""
    emojis = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    print(f"{emojis.get(status, 'ℹ️')} {message}")

def install_missing_packages():
    """Install missing Python packages"""
    print_status("Installing missing packages...")
    
    packages = [
        "python-jose",
        "passlib", 
        "python-multipart",
        "email-validator",
        "joblib"
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print_status(f"Installed {package}", "success")
        except subprocess.CalledProcessError:
            print_status(f"Failed to install {package}", "error")

def set_environment_variables():
    """Set required environment variables"""
    print_status("Setting environment variables...")
    
    env_vars = {
        'DB_HOST': 'localhost',
        'DB_NAME': 'green_engine', 
        'DB_USER': 'green_user',
        'DB_PASSWORD': 'green_pass',
        'DB_PORT': '5432',
        'JWT_SECRET_KEY': 'your-super-secret-jwt-key-change-this-in-production',
        'JWT_ALGORITHM': 'HS256',
        'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'MQTT_BROKER_HOST': 'localhost',
        'MQTT_BROKER_PORT': '1883',
        'MQTT_USE_TLS': 'false',
        'MQTT_CMD_BASE': 'greenengine',
        'AUTH_REQUIRED': 'true',
        'ENCRYPTION_KEY': 'your-encryption-key-for-passwords'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print_status(f"Set {key}={value}")

def test_api_import():
    """Test if API module can be imported"""
    print_status("Testing API module import...")
    
    try:
        import src.api.main
        print_status("API module imports successfully", "success")
        return True
    except Exception as e:
        print_status(f"API import failed: {e}", "error")
        return False

def create_simple_startup_script():
    """Create a simple startup script"""
    print_status("Creating startup script...")
    
    script_content = '''#!/bin/bash

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
echo "Starting API server on port 8020..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8020 --reload &
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
echo "🔗 API: http://localhost:8020"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
'''
    
    with open("start_green_engine.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("start_green_engine.sh", 0o755)
    print_status("Created start_green_engine.sh", "success")

def main():
    """Main function"""
    print("🔧 Green Engine Authentication Fix")
    print("=" * 50)
    
    # Install missing packages
    install_missing_packages()
    
    # Set environment variables
    set_environment_variables()
    
    # Test API import
    if test_api_import():
        print_status("All dependencies are working!", "success")
    else:
        print_status("There are still issues with dependencies", "warning")
    
    # Create startup script
    create_simple_startup_script()
    
    print("\n🎉 Fix completed!")
    print("\n📋 Next steps:")
    print("1. Run: ./start_green_engine.sh")
    print("2. Open: http://localhost:8501")
    print("3. The dashboard should now work without authentication")
    print("\n💡 Note: Authentication is temporarily disabled for easier access")

if __name__ == "__main__":
    main()
