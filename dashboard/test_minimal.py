#!/usr/bin/env python3
"""
Minimal test dashboard to isolate the tabs issue
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Test Dashboard",
    page_icon="🌱",
    layout="wide"
)

# Header
st.markdown('<h1 class="main-header">🌱 Test Dashboard</h1>', unsafe_allow_html=True)

# Simple sidebar
st.sidebar.title("Test Controls")
location = st.sidebar.selectbox("Location", ["greenhouse_a", "greenhouse_b"])

# Test data
test_data = {"location": location, "status": "working"}

# Display test data
st.write("Test Data:", test_data)

# Tabs - This should work even without data
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Sensor Data", 
    "🌱 Growth Analytics", 
    "⚠️ Alerts", 
    "📈 Analytics", 
    "🛠️ Admin", 
    "🌿 Trays", 
    "🔮 Forecasts"
])

with tab1:
    st.subheader("Sensor Data Tab")
    st.write("This is the sensor data tab content")
    st.success("✅ Tab 1 is working!")

with tab2:
    st.subheader("Growth Analytics Tab")
    st.write("This is the growth analytics tab content")
    st.success("✅ Tab 2 is working!")

with tab3:
    st.subheader("Alerts Tab")
    st.write("This is the alerts tab content")
    st.success("✅ Tab 3 is working!")

with tab4:
    st.subheader("Analytics Tab")
    st.write("This is the analytics tab content")
    st.success("✅ Tab 4 is working!")

with tab5:
    st.subheader("Admin Tab")
    st.write("This is the admin tab content")
    st.success("✅ Tab 5 is working!")

with tab6:
    st.subheader("🌿 Trays Tab")
    st.write("This is the NEW trays tab content!")
    st.success("✅ Tab 6 (Trays) is working!")

with tab7:
    st.subheader("🔮 Forecasts Tab")
    st.write("This is the NEW forecasts tab content!")
    st.success("✅ Tab 7 (Forecasts) is working!")

st.success("🎉 All tabs should be visible above!")
