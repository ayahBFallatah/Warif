#!/usr/bin/env python3
"""
Local development setup for Green Engine (without Docker)
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_database():
    """Setup SQLite database for local development"""
    print("🗄️ Setting up local SQLite database...")
    try:
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        
        # Run database setup
        subprocess.run([sys.executable, "scripts/setup_db.py"], check=True)
        print("✅ Database setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🚀 Starting Streamlit dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🔗 API will be available at: http://localhost:8000")
    print("⏹️ Press Ctrl+C to stop the application")
    
    try:
        # Start the dashboard
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")

def main():
    """Main setup function"""
    print("🌱 Green Engine - Local Development Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Setup database
    if not setup_database():
        return
    
    # Start dashboard
    start_dashboard()

if __name__ == "__main__":
    main()
