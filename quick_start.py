#!/usr/bin/env python3
"""
Quick start script for Green Engine Demo
Simplified version that avoids dependency conflicts
"""

import subprocess
import sys
import os

def install_packages():
    """Install required packages one by one"""
    packages = [
        "streamlit",
        "plotly", 
        "pandas",
        "numpy"
    ]
    
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "--upgrade", "--no-cache-dir", package
            ], check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not install {package}: {e}")
            print("Continuing with available packages...")

def check_packages():
    """Check if required packages are available"""
    required = ["streamlit", "plotly", "pandas"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is missing")
    
    return len(missing) == 0

def main():
    print("🌱 Green Engine - Quick Start")
    print("=" * 40)
    
    # Install packages
    install_packages()
    
    # Check if packages are available
    if not check_packages():
        print("\n❌ Some required packages are missing.")
        print("Please install them manually:")
        print("python3 -m pip install streamlit plotly pandas numpy")
        return
    
    print("\n🚀 Starting Green Engine Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("⏹️ Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        # Start the dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard_local.py", "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error starting demo: {e}")

if __name__ == "__main__":
    main()
