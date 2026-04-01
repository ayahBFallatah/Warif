#!/usr/bin/env python3
"""
Quick start script for Green Engine Demo
"""

import subprocess
import sys
import os

def main():
    print("🌱 Green Engine - Quick Demo Start")
    print("=" * 40)
    
    # Check if required packages are installed
    try:
        import streamlit
        import plotly
        import pandas
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "plotly", "pandas"], check=True)
        print("✅ Packages installed")
    
    print("\n🚀 Starting Green Engine Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("⏹️ Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        # Start the dashboard
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard_local.py", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error starting demo: {e}")

if __name__ == "__main__":
    main()
