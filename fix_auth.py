#!/usr/bin/env python3
"""
Fix authentication issues by setting proper environment variables
"""

import os
import subprocess
import sys

def set_environment_variables():
    """Set the required environment variables"""
    env_vars = {
        'DB_HOST': 'postgres',
        'DB_NAME': 'green_engine',
        'DB_USER': 'green_user',
        'DB_PASSWORD': 'green_pass',
        'DB_PORT': '5432',
        'JWT_SECRET_KEY': 'your-super-secret-jwt-key-change-this-in-production',
        'JWT_ALGORITHM': 'HS256',
        'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'MQTT_BROKER_HOST': 'mqtt',
        'MQTT_BROKER_PORT': '1883',
        'MQTT_USE_TLS': 'false',
        'MQTT_CMD_BASE': 'greenengine',
        'AUTH_REQUIRED': 'true',
        'ENCRYPTION_KEY': 'your-encryption-key-for-passwords'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}={value}")

def test_api_connection():
    """Test API connection"""
    import requests
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8010/health", timeout=5)
        print(f"Health check: {response.status_code}")
        
        # Test login endpoint
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(
            "http://localhost:8010/api/v1/auth/login",
            json=login_data,
            timeout=5
        )
        print(f"Login test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Login successful! Token: {data.get('access_token', 'No token')[:20]}...")
        else:
            print(f"Login failed: {response.text}")
            
    except Exception as e:
        print(f"API test failed: {e}")

if __name__ == "__main__":
    print("🔧 Fixing authentication configuration...")
    set_environment_variables()
    print("\n🧪 Testing API connection...")
    test_api_connection()
