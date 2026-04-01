"""
Simplified Green Engine Dashboard for Local Development
Runs without requiring the full backend infrastructure
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# Page configuration
st.set_page_config(
    page_title="Green Engine Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
</style>
""", unsafe_allow_html=True)

def generate_mock_sensor_data(hours_back=24):
    """Generate mock sensor data for demonstration"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    
    # Generate time series
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15min')
    
    # Generate realistic sensor data
    base_temp = 22.0
    temp_data = [base_temp + 3 * np.sin(i * 2 * np.pi / 96) + np.random.normal(0, 0.5) for i in range(len(timestamps))]
    
    base_humidity = 65.0
    humidity_data = [base_humidity + 10 * np.cos(i * 2 * np.pi / 96) + np.random.normal(0, 2) for i in range(len(timestamps))]
    
    # Light data (more during day, less at night)
    light_data = []
    for ts in timestamps:
        hour = ts.hour
        if 6 <= hour <= 18:  # Daytime
            light = 400 + 200 * np.sin((hour - 6) * np.pi / 12) + np.random.normal(0, 50)
        else:  # Nighttime
            light = 20 + np.random.normal(0, 5)
        light_data.append(max(0, light))
    
    # Soil moisture data
    soil_data = [35 + 10 * np.sin(i * 2 * np.pi / 192) + np.random.normal(0, 2) for i in range(len(timestamps))]
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': temp_data,
        'humidity': humidity_data,
        'light': light_data,
        'soil_moisture': soil_data
    })
    
    return df

def create_sensor_chart(df, sensor_name, color='#2E8B57'):
    """Create time series chart for sensor data"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[sensor_name],
        mode='lines+markers',
        name=sensor_name.title(),
        line=dict(color=color, width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title=f"{sensor_name.title()} Over Time",
        xaxis_title="Time",
        yaxis_title=sensor_name.title(),
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_multi_sensor_chart(df):
    """Create multi-sensor dashboard chart"""
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=['Temperature (°C)', 'Humidity (%)', 'Light (lux)', 'Soil Moisture (%)'],
        vertical_spacing=0.1
    )
    
    colors = ['#2E8B57', '#4682B4', '#DAA520', '#CD5C5C']
    sensors = ['temperature', 'humidity', 'light', 'soil_moisture']
    
    for i, (sensor, color) in enumerate(zip(sensors, colors)):
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df[sensor],
                mode='lines+markers',
                name=sensor.title(),
                line=dict(color=color, width=2),
                marker=dict(size=3)
            ),
            row=i+1, col=1
        )
    
    fig.update_layout(
        title="Multi-Sensor Dashboard",
        height=800,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🌱 Green Engine Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    
    # Location selection
    location = st.sidebar.selectbox(
        "Select Location",
        ["greenhouse_a", "greenhouse_b", "indoor_farm_1"],
        index=0
    )
    
    # Time range selection
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 6 hours", "Last 24 hours", "Last 7 days"],
        index=1
    )
    
    # Convert time range to hours
    time_mapping = {
        "Last 6 hours": 6,
        "Last 24 hours": 24,
        "Last 7 days": 168
    }
    hours_back = time_mapping[time_range]
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(1)  # Small delay for demo
        st.rerun()
    
    # Generate mock data
    sensor_data = generate_mock_sensor_data(hours_back)
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics
    with col1:
        current_temp = sensor_data['temperature'].iloc[-1]
        st.metric("Temperature", f"{current_temp:.1f}°C")
    
    with col2:
        current_humidity = sensor_data['humidity'].iloc[-1]
        st.metric("Humidity", f"{current_humidity:.1f}%")
    
    with col3:
        current_light = sensor_data['light'].iloc[-1]
        st.metric("Light", f"{current_light:.0f} lux")
    
    with col4:
        current_soil = sensor_data['soil_moisture'].iloc[-1]
        st.metric("Soil Moisture", f"{current_soil:.1f}%")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Sensor Data", "🌱 Growth Analytics", "📈 Analytics"])
    
    with tab1:
        st.subheader("Real-time Sensor Monitoring")
        
        # Multi-sensor chart
        fig = create_multi_sensor_chart(sensor_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Individual sensor charts
        cols = st.columns(2)
        
        with cols[0]:
            fig = create_sensor_chart(sensor_data, 'temperature', '#2E8B57')
            st.plotly_chart(fig, use_container_width=True)
        
        with cols[1]:
            fig = create_sensor_chart(sensor_data, 'humidity', '#4682B4')
            st.plotly_chart(fig, use_container_width=True)
        
        with cols[0]:
            fig = create_sensor_chart(sensor_data, 'light', '#DAA520')
            st.plotly_chart(fig, use_container_width=True)
        
        with cols[1]:
            fig = create_sensor_chart(sensor_data, 'soil_moisture', '#CD5C5C')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Growth Measurements & Analytics")
        
        # Mock growth data
        growth_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=30, freq='1D'),
            'plant_height_cm': [5 + i * 0.5 for i in range(30)],
            'biomass_g': [10 + i * 2 for i in range(30)],
            'yield_g': [8 + i * 1.8 for i in range(30)]
        })
        
        # Growth chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=growth_data['timestamp'],
            y=growth_data['plant_height_cm'],
            mode='lines+markers',
            name='Plant Height (cm)',
            line=dict(color='#2E8B57')
        ))
        
        fig.add_trace(go.Scatter(
            x=growth_data['timestamp'],
            y=growth_data['biomass_g'],
            mode='lines+markers',
            name='Biomass (g)',
            line=dict(color='#4682B4')
        ))
        
        fig.add_trace(go.Scatter(
            x=growth_data['timestamp'],
            y=growth_data['yield_g'],
            mode='lines+markers',
            name='Yield (g)',
            line=dict(color='#DAA520')
        ))
        
        fig.update_layout(
            title="Growth Measurements Over Time",
            xaxis_title="Date",
            yaxis_title="Measurement",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth data table
        st.subheader("Recent Growth Measurements")
        st.dataframe(
            growth_data.tail(10),
            use_container_width=True
        )
    
    with tab3:
        st.subheader("Analytics Summary")
        
        # Mock analytics data
        analytics_data = {
            'location': location,
            'sensor_summary': [
                {'sensor_type': 'temperature', 'avg_value': 23.5, 'reading_count': 96},
                {'sensor_type': 'humidity', 'avg_value': 65.2, 'reading_count': 96},
                {'sensor_type': 'light', 'avg_value': 450.0, 'reading_count': 96},
                {'sensor_type': 'soil_moisture', 'avg_value': 35.8, 'reading_count': 96}
            ],
            'growth_summary': [
                {'crop_type': 'pea_shoots', 'avg_yield': 42.1, 'measurement_count': 5},
                {'crop_type': 'sunflower', 'avg_yield': 75.2, 'measurement_count': 3}
            ],
            'active_alerts': 0
        }
        
        # Sensor summary
        st.subheader("Sensor Summary (Last 24h)")
        sensor_summary = pd.DataFrame(analytics_data['sensor_summary'])
        st.dataframe(sensor_summary, use_container_width=True)
        
        # Growth summary
        st.subheader("Growth Summary (Last 7 days)")
        growth_summary = pd.DataFrame(analytics_data['growth_summary'])
        st.dataframe(growth_summary, use_container_width=True)
        
        # System status
        st.subheader("System Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Alerts", analytics_data['active_alerts'])
        with col2:
            st.metric("System Status", "🟢 Healthy")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Green Engine Dashboard - IoT Microgreen Monitoring System (Demo Mode)</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
