#!/usr/bin/env python3
"""
Debug version of Green Engine Dashboard
This will show us exactly where the code is failing
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
import time
import traceback

# Page configuration
st.set_page_config(
    page_title="Green Engine Dashboard - DEBUG",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8010"

# Debug function
def debug_print(message):
    st.sidebar.write(f"🔍 DEBUG: {message}")

# Main function with debug output
def main():
    """Main dashboard function with debug output"""
    
    st.title("🌱 Green Engine Dashboard - DEBUG MODE")
    st.write("This is the debug version to find errors")
    
    # Debug: Check if we can import everything
    try:
        debug_print("✅ All imports successful")
    except Exception as e:
        st.error(f"❌ Import error: {e}")
        st.code(traceback.format_exc())
        return
    
    # Debug: Check API connection
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            debug_print("✅ API connection successful")
        else:
            debug_print(f"⚠️ API responded with status: {response.status_code}")
    except Exception as e:
        debug_print(f"❌ API connection failed: {e}")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    
    # Location selection
    try:
        location = st.sidebar.selectbox(
            "Select Location",
            ["greenhouse_a", "greenhouse_b", "indoor_farm_1"],
            index=0
        )
        debug_print(f"✅ Location selected: {location}")
    except Exception as e:
        st.error(f"❌ Location selection error: {e}")
        st.code(traceback.format_exc())
        return
    
    # Time range selection
    try:
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last 6 hours", "Last 24 hours", "Last 7 days"],
            index=1
        )
        debug_print(f"✅ Time range selected: {time_range}")
    except Exception as e:
        st.error(f"❌ Time range selection error: {e}")
        st.code(traceback.format_exc())
        return
    
    # Convert time range to hours
    time_mapping = {
        "Last 6 hours": 6,
        "Last 24 hours": 24,
        "Last 7 days": 168,
    }
    hours_back = time_mapping[time_range]
    
    # Debug: Show we're about to create tabs
    debug_print("🔄 About to create tabs...")
    
    # Create tabs - This is where the issue might be
    try:
        st.write("Creating tabs...")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Sensor Data", 
            "🌱 Growth Analytics", 
            "⚠️ Alerts", 
            "📈 Analytics", 
            "🛠️ Admin", 
            "🌿 Trays", 
            "🔮 Forecasts"
        ])
        debug_print("✅ Tabs created successfully!")
        st.success("🎉 Tabs are working!")
    except Exception as e:
        st.error(f"❌ Tab creation failed: {e}")
        st.code(traceback.format_exc())
        return
    
    # Test each tab
    try:
        with tab1:
            st.subheader("📊 Sensor Data Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 1: Sensor Data")
        
        with tab2:
            st.subheader("🌱 Growth Analytics Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 2: Growth Analytics")
        
        with tab3:
            st.subheader("⚠️ Alerts Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 3: Alerts")
        
        with tab4:
            st.subheader("📈 Analytics Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 4: Analytics")
        
        with tab5:
            st.subheader("🛠️ Admin Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 5: Admin")
        
        with tab6:
            st.subheader("🌿 Trays Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 6: Trays")
        
        with tab7:
            st.subheader("🔮 Forecasts Tab")
            st.write("This tab is working!")
            st.success("✅ Tab 7: Forecasts")
            
        debug_print("✅ All tab content populated successfully!")
        
    except Exception as e:
        st.error(f"❌ Tab content population failed: {e}")
        st.code(traceback.format_exc())
        return
    
    # Final success message
    st.success("🎉 Dashboard is fully functional!")
    debug_print("✅ Dashboard completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Fatal error in main: {e}")
        st.code(traceback.format_exc())
