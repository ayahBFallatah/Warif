"""
Streamlit Dashboard for Green Engine
Real-time monitoring and analytics for microgreen growth
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
from typing import Optional, Dict, Any

# Page configuration
st.set_page_config(
    page_title="Green Engine Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8020"

# Authentication configuration
AUTH_REQUIRED = False  # Set to False to disable authentication

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
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Login user and return authentication data"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Login error: {e}")
        return None

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user information"""
    if not st.session_state.get("auth_token"):
        return None
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def check_permission(user: Dict[str, Any], resource: str, action: str) -> bool:
    """Check if user has permission for resource and action"""
    if not user:
        return False
    
    # Admin has all permissions
    if "admin" in user.get("roles", []):
        return True
    
    # Check specific permissions
    permissions = user.get("permissions", {})
    resource_permissions = permissions.get(resource, [])
    return action in resource_permissions

def render_login_form():
    """Render login form"""
    st.markdown('<h1 class="main-header">🌱 Green Engine Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Login Required")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if username and password:
                    auth_data = login_user(username, password)
                    
                    if auth_data:
                        st.session_state.authenticated = True
                        st.session_state.user = auth_data["user"]
                        st.session_state.auth_token = auth_data["access_token"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
                else:
                    st.error("Please enter both username and password.")
        
        # Demo credentials
        st.info("""
        **Demo Credentials:**
        - **Admin:** admin / admin123
        - **Operator:** operator1 / operator123
        - **Viewer:** viewer1 / viewer123
        """)

def render_logout_button():
    """Render logout button in sidebar"""
    if st.session_state.get("authenticated"):
        with st.sidebar:
            st.markdown("---")
            user = st.session_state.get("user", {})
            st.write(f"👤 **{user.get('username', 'Unknown')}**")
            st.write(f"🔑 **{', '.join(user.get('roles', []))}**")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.auth_token = None
                st.success("Logged out successfully!")
                st.rerun()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_sensor_data(location: str, hours_back: int = 24):
    """Fetch sensor data from API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        response = requests.get(
            f"{API_BASE_URL}/api/v1/sensor-data",
            params={
                "location": location,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": 1000
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            st.error(f"Failed to fetch sensor data: {response.status_code}")
            return pd.DataFrame()
    
    except Exception as e:
        st.error(f"Error fetching sensor data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_processed_features(location: str, hours_back: int = 24):
    """Fetch processed features from API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        response = requests.get(
            f"{API_BASE_URL}/api/v1/processed-features",
            params={
                "location": location,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": 1000
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_growth_measurements(location: str):
    """Fetch growth measurements from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/growth-measurements",
            params={"location": location, "limit": 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_alerts(location: str):
    """Fetch alerts from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/alerts",
            params={"location": location, "limit": 50}
        )
        
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_thresholds():
    try:
        r = requests.get(f"{API_BASE_URL}/api/v1/config/thresholds")
        if r.status_code == 200:
            return r.json()
        return {"source": "unknown", "thresholds": {}}
    except Exception:
        return {"source": "unknown", "thresholds": {}}

def update_thresholds_api(thresholds: dict) -> bool:
    try:
        r = requests.put(
            f"{API_BASE_URL}/api/v1/config/thresholds",
            json=thresholds,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False

def acknowledge_alert_api(alert_id: int) -> bool:
    try:
        r = requests.post(f"{API_BASE_URL}/api/v1/alerts/{alert_id}/ack")
        return r.status_code == 200
    except Exception:
        return False

def resolve_alert_api(alert_id: int) -> bool:
    try:
        r = requests.post(f"{API_BASE_URL}/api/v1/alerts/{alert_id}/resolve")
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=60)
def fetch_commands(status: str | None = None, limit: int = 50):
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        r = requests.get(f"{API_BASE_URL}/api/v1/commands", params=params)
        if r.status_code == 200:
            return r.json()
        return {"data": [], "count": 0}
    except Exception:
        return {"data": [], "count": 0}

def requeue_command_api(cmd_id: int) -> bool:
    try:
        r = requests.post(f"{API_BASE_URL}/api/v1/commands/requeue", json={"id": cmd_id})
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=300)
def fetch_analytics_summary(location: str):
    """Fetch analytics summary from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/analytics/summary",
            params={"location": location}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def fetch_trays():
    """Fetch trays data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/trays")
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_forecasts(location: str, days_ahead: int = 30):
    """Fetch forecast data from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/predictions/growth-forecast",
            params={
                "location": location,
                "days_ahead": days_ahead
            }
        )
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def create_sensor_chart(df: pd.DataFrame, sensor_type: str):
    """Create time series chart for sensor data"""
    if df.empty:
        return go.Figure()
    
    sensor_data = df[df['sensor_type'] == sensor_type].copy()
    if sensor_data.empty:
        return go.Figure()
    
    sensor_data['timestamp'] = pd.to_datetime(sensor_data['timestamp'])
    sensor_data = sensor_data.sort_values('timestamp')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sensor_data['timestamp'],
        y=sensor_data['value'],
        mode='lines+markers',
        name=sensor_type.title(),
        line=dict(color='#2E8B57', width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title=f"{sensor_type.title()} Over Time",
        xaxis_title="Time",
        yaxis_title=f"{sensor_type.title()} ({sensor_data['unit'].iloc[0] if not sensor_data.empty else ''})",
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_multi_sensor_chart(df: pd.DataFrame):
    """Create multi-sensor dashboard chart"""
    if df.empty:
        return go.Figure()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Get unique sensor types
    sensor_types = df['sensor_type'].unique()
    
    # Create subplots
    fig = make_subplots(
        rows=len(sensor_types), cols=1,
        subplot_titles=[sensor_type.title() for sensor_type in sensor_types],
        vertical_spacing=0.1
    )
    
    colors = ['#2E8B57', '#4682B4', '#DAA520', '#CD5C5C', '#9370DB', '#20B2AA']
    
    for i, sensor_type in enumerate(sensor_types):
        sensor_data = df[df['sensor_type'] == sensor_type].sort_values('timestamp')
        
        fig.add_trace(
            go.Scatter(
                x=sensor_data['timestamp'],
                y=sensor_data['value'],
                mode='lines+markers',
                name=sensor_type.title(),
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=3)
            ),
            row=i+1, col=1
        )
    
    fig.update_layout(
        title="Multi-Sensor Dashboard",
        height=200 * len(sensor_types),
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_growth_chart(df: pd.DataFrame):
    """Create growth measurement chart"""
    if df.empty:
        return go.Figure()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Plant Height', 'Biomass', 'Yield', 'Germination Rate'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Plant Height
    if 'plant_height_cm' in df.columns:
        height_data = df.dropna(subset=['plant_height_cm'])
        if not height_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=height_data['timestamp'],
                    y=height_data['plant_height_cm'],
                    mode='lines+markers',
                    name='Height (cm)',
                    line=dict(color='#2E8B57')
                ),
                row=1, col=1
            )
    
    # Biomass
    if 'biomass_g' in df.columns:
        biomass_data = df.dropna(subset=['biomass_g'])
        if not biomass_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=biomass_data['timestamp'],
                    y=biomass_data['biomass_g'],
                    mode='lines+markers',
                    name='Biomass (g)',
                    line=dict(color='#4682B4')
                ),
                row=1, col=2
            )
    
    # Yield
    if 'yield_g' in df.columns:
        yield_data = df.dropna(subset=['yield_g'])
        if not yield_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=yield_data['timestamp'],
                    y=yield_data['yield_g'],
                    mode='lines+markers',
                    name='Yield (g)',
                    line=dict(color='#DAA520')
                ),
                row=2, col=1
            )
    
    # Germination Rate
    if 'germination_rate' in df.columns:
        germ_data = df.dropna(subset=['germination_rate'])
        if not germ_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=germ_data['timestamp'],
                    y=germ_data['germination_rate'],
                    mode='lines+markers',
                    name='Germination Rate (%)',
                    line=dict(color='#CD5C5C')
                ),
                row=2, col=2
            )
    
    fig.update_layout(
        title="Growth Measurements",
        height=600,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_tray_form():
    """Create form for adding/editing trays"""
    with st.form("tray_form"):
        st.subheader("Add/Edit Tray")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tray_code = st.text_input("Tray Code", placeholder="e.g., TRAY-001")
            location = st.text_input("Location", placeholder="e.g., Zone A")
            device_id = st.text_input("Device ID", placeholder="e.g., GH-A1-DEV-01")
            crop_type = st.selectbox(
                "Crop Type",
                ["Microgreens", "Sprouts", "Herbs", "Lettuce", "Kale", "Other"],
                index=0
            )
            planted_on = st.date_input("Planted On")
        
        with col2:
            expected_harvest = st.date_input("Expected Harvest")
            grow_medium = st.selectbox(
                "Grow Medium",
                ["Coco Coir", "Rockwool", "Soil", "Hydroponic", "Other"],
                index=0
            )
            batch_code = st.text_input("Batch/Lot Code", placeholder="e.g., BATCH-2024-01")
            seed_density = st.number_input("Seed Density (seeds/cm²)", min_value=0.1, value=2.0, step=0.1)
            lighting_profile = st.selectbox(
                "Lighting Profile",
                ["18/6", "16/8", "12/12", "24/0", "Custom"],
                index=1
            )
        
        notes = st.text_area("Notes", placeholder="Additional information...")
        
        submitted = st.form_submit_button("Save Tray")
        
        if submitted:
            if tray_code and location:
                tray_data = {
                    "tray_code": tray_code,
                    "location": location,
                    "device_id": device_id if device_id else None,
                    "crop_type": crop_type,
                    "planted_on": planted_on.isoformat() if planted_on else None,
                    "expected_harvest": expected_harvest.isoformat() if expected_harvest else None,
                    "grow_medium": grow_medium,
                    "batch_code": batch_code if batch_code else None,
                    "seed_density": float(seed_density),
                    "lighting_profile": lighting_profile,
                    "notes": notes if notes else None
                }
                
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/trays",
                        json=tray_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 201:
                        st.success("Tray created successfully!")
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Failed to create tray: {response.status_code}")
                except Exception as e:
                    st.error(f"Error creating tray: {e}")
            else:
                st.error("Tray Code and Location are required fields")

def create_forecast_chart(df: pd.DataFrame):
    """Create forecast visualization chart"""
    if df.empty:
        return go.Figure()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    # Add actual values if available
    if 'actual_value' in df.columns:
        actual_data = df.dropna(subset=['actual_value'])
        if not actual_data.empty:
            fig.add_trace(go.Scatter(
                x=actual_data['timestamp'],
                y=actual_data['actual_value'],
                mode='lines+markers',
                name='Actual',
                line=dict(color='#2E8B57', width=3),
                marker=dict(size=6)
            ))
    
    # Add predicted values
    if 'predicted_value' in df.columns:
        pred_data = df.dropna(subset=['predicted_value'])
        if not pred_data.empty:
            fig.add_trace(go.Scatter(
                x=pred_data['timestamp'],
                y=pred_data['predicted_value'],
                mode='lines+markers',
                name='Predicted',
                line=dict(color='#4682B4', width=2, dash='dash'),
                marker=dict(size=4)
            ))
    
    # Add confidence intervals if available
    if 'confidence_lower' in df.columns and 'confidence_upper' in df.columns:
        conf_data = df.dropna(subset=['confidence_lower', 'confidence_upper'])
        if not conf_data.empty:
            fig.add_trace(go.Scatter(
                x=conf_data['timestamp'],
                y=conf_data['confidence_upper'],
                mode='lines',
                name='Confidence Upper',
                line=dict(color='#4682B4', width=1, dash='dot'),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=conf_data['timestamp'],
                y=conf_data['confidence_lower'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(70, 130, 180, 0.1)',
                name='Confidence Interval',
                line=dict(color='#4682B4', width=1, dash='dot'),
                showlegend=False
            ))
    
    fig.update_layout(
        title="Growth Forecast",
        xaxis_title="Time",
        yaxis_title="Value",
        height=500,
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='x unified'
    )
    
    return fig

def main():
    """Main dashboard function"""
    
    # Check authentication
    if AUTH_REQUIRED and not st.session_state.get("authenticated"):
        render_login_form()
        return
    
    # Header
    st.markdown('<h1 class="main-header">🌱 Green Engine Dashboard</h1>', unsafe_allow_html=True)
    
    # Render logout button
    render_logout_button()
    
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
        ["Last 6 hours", "Last 24 hours", "Last 7 days", "Last 14 days", "Last 30 days", "Last 90 days", "Last 365 days"],
        index=1
    )
    
    # Convert time range to hours
    time_mapping = {
        "Last 6 hours": 6,
        "Last 24 hours": 24,
        "Last 7 days": 168,
        "Last 14 days": 336,
        "Last 30 days": 720,
        "Last 90 days": 2160,
        "Last 365 days": 8760,
    }
    hours_back = time_mapping[time_range]
    
    # Auto-refresh (render page first, then rerun at end)
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.caption("Auto-refreshing every 30s")
    
    # Fetch data with error handling
    try:
        sensor_data = fetch_sensor_data(location, hours_back)
        st.sidebar.success("✅ Sensor data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Sensor data error: {e}")
        sensor_data = pd.DataFrame()
    
    try:
        processed_features = fetch_processed_features(location, hours_back)
        st.sidebar.success("✅ Processed features fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Processed features error: {e}")
        processed_features = pd.DataFrame()
    
    try:
        growth_data = fetch_growth_measurements(location)
        st.sidebar.success("✅ Growth data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Growth data error: {e}")
        growth_data = pd.DataFrame()
    
    try:
        alerts_data = fetch_alerts(location)
        st.sidebar.success("✅ Alerts data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Alerts error: {e}")
        alerts_data = pd.DataFrame()
    
    try:
        summary_data = fetch_analytics_summary(location)
        st.sidebar.success("✅ Summary data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Summary error: {e}")
        summary_data = {}
    
    try:
        trays_data = fetch_trays()
        st.sidebar.success("✅ Trays data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Trays error: {e}")
        trays_data = pd.DataFrame()
    
    try:
        forecasts_data = fetch_forecasts(location, 30)  # 30 days forecast
        st.sidebar.success("✅ Forecasts data fetched")
    except Exception as e:
        st.sidebar.error(f"❌ Forecasts error: {e}")
        forecasts_data = pd.DataFrame()
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics
    with col1:
        if not sensor_data.empty:
            temp_data = sensor_data[sensor_data['sensor_type'] == 'temperature']
            if not temp_data.empty:
                current_temp = temp_data['value'].iloc[-1]
                st.metric("Temperature", f"{current_temp:.1f}°C")
            else:
                st.metric("Temperature", "N/A")
        else:
            st.metric("Temperature", "N/A")
    
    with col2:
        if not sensor_data.empty:
            humidity_data = sensor_data[sensor_data['sensor_type'] == 'humidity']
            if not humidity_data.empty:
                current_humidity = humidity_data['value'].iloc[-1]
                st.metric("Humidity", f"{current_humidity:.1f}%")
            else:
                st.metric("Humidity", "N/A")
        else:
            st.metric("Humidity", "N/A")
    
    with col3:
        if not sensor_data.empty:
            light_data = sensor_data[sensor_data['sensor_type'] == 'light']
            if not light_data.empty:
                current_light = light_data['value'].iloc[-1]
                st.metric("Light", f"{current_light:.0f} lux")
            else:
                st.metric("Light", "N/A")
        else:
            st.metric("Light", "N/A")
    
    with col4:
        if not sensor_data.empty:
            soil_data = sensor_data[sensor_data['sensor_type'] == 'soil_moisture']
            if not soil_data.empty:
                current_soil = soil_data['value'].iloc[-1]
                st.metric("Soil Moisture", f"{current_soil:.1f}%")
            else:
                st.metric("Soil Moisture", "N/A")
        else:
            st.metric("Soil Moisture", "N/A")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 Sensor Data", "🌱 Growth Analytics", "⚠️ Alerts", "📈 Analytics", "🛠️ Admin", "🌿 Trays", "🔮 Forecasts"])
    
    with tab1:
        st.subheader("Real-time Sensor Monitoring")
        
        # Multi-sensor chart
        if not sensor_data.empty:
            fig = create_multi_sensor_chart(sensor_data)
            st.plotly_chart(fig, use_container_width=True)
        
        # Individual sensor charts
        if not sensor_data.empty:
            sensor_types = sensor_data['sensor_type'].unique()
            
            cols = st.columns(2)
            for i, sensor_type in enumerate(sensor_types):
                with cols[i % 2]:
                    fig = create_sensor_chart(sensor_data, sensor_type)
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Growth Measurements & Analytics")
        
        if not growth_data.empty:
            # Growth chart
            fig = create_growth_chart(growth_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Growth data table
            st.subheader("Recent Growth Measurements")
            display_cols = ['timestamp', 'tray_id', 'crop_type', 'plant_height_cm', 
                           'biomass_g', 'yield_g', 'growth_stage']
            display_cols = [col for col in display_cols if col in growth_data.columns]
            
            st.dataframe(
                growth_data[display_cols].head(10),
                use_container_width=True
            )
        else:
            st.info("No growth measurement data available")
    
    with tab3:
        st.subheader("System Alerts & Notifications")
        
        if not alerts_data.empty:
            # Filter active alerts
            active_alerts = alerts_data[alerts_data['status'] == 'active']
            
            if not active_alerts.empty:
                for _, alert in active_alerts.iterrows():
                    # Use Streamlit's built-in styling instead of custom CSS
                    severity = alert['severity'].title()
                    timestamp = alert['timestamp']
                    
                    # Create a container for each alert
                    with st.container():
                        # Alert header with severity color
                        if severity.lower() == 'critical':
                            st.error(f"🚨 **{alert['title']}**")
                        elif severity.lower() == 'high':
                            st.warning(f"⚠️ **{alert['title']}**")
                        else:
                            st.info(f"ℹ️ **{alert['title']}**")
                        
                        # Alert details
                        st.write(f"**Description:** {alert['description']}")
                        st.write(f"**Severity:** {severity} | **Time:** {timestamp}")
                        
                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("Acknowledge", key=f"ack_{alert['id']}_{alert['timestamp']}"):
                                if acknowledge_alert_api(int(alert.get('id', 0))):
                                    st.success("Alert acknowledged")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Failed to acknowledge")
                        with btn_col2:
                            if st.button("Resolve", key=f"resolve_{alert['id']}_{alert['timestamp']}"):
                                if resolve_alert_api(int(alert.get('id', 0))):
                                    st.success("Alert resolved")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Failed to resolve")
                        
                        st.divider()  # Add separator between alerts
            else:
                st.success("No active alerts")
            
            # All alerts table
            st.subheader("📋 All Alerts History")
            if not alerts_data.empty:
                # Display alerts in a more readable format
                for _, alert in alerts_data.head(10).iterrows():
                    with st.expander(f"{alert['title']} - {alert['timestamp']}"):
                        st.write(f"**Type:** {alert['alert_type']}")
                        st.write(f"**Severity:** {alert['severity'].title()}")
                        st.write(f"**Status:** {alert['status'].title()}")
                        st.write(f"**Description:** {alert['description']}")
                        st.write(f"**Time:** {alert['timestamp']}")
            else:
                st.info("No alerts found")
        else:
            st.info("No alert data available")
    
    with tab4:
        st.subheader("Analytics Summary")
        
        if summary_data:
            # Sensor summary
            if 'sensor_summary' in summary_data:
                st.subheader("Sensor Summary (Last 24h)")
                sensor_summary = pd.DataFrame(summary_data['sensor_summary'])
                if not sensor_summary.empty:
                    st.dataframe(sensor_summary, use_container_width=True)
            
            # Growth summary
            if 'growth_summary' in summary_data:
                st.subheader("Growth Summary (Last 7 days)")
                growth_summary = pd.DataFrame(summary_data['growth_summary'])
                if not growth_summary.empty:
                    st.dataframe(growth_summary, use_container_width=True)
            
            # Active alerts count
            if 'active_alerts' in summary_data:
                st.subheader("System Status")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Active Alerts", summary_data['active_alerts'])
                with col2:
                    st.metric("System Status", "🟢 Healthy" if summary_data['active_alerts'] == 0 else "🟡 Warning")
        else:
            st.info("No analytics summary available")

    with tab5:
        st.subheader("Admin: Sensor Thresholds")
        current = fetch_thresholds()
        src = current.get("source", "unknown")
        thresholds = current.get("thresholds", {}) or {}
        st.caption(f"Source: {src}")

        sensors = [
            ("temperature", "°C"),
            ("humidity", "%"),
            ("light", "lux"),
            ("soil_moisture", "%"),
            ("ec", "mS/cm"),
            ("co2", "ppm"),
        ]

        updated: dict = {}
        for name, unit in sensors:
            col_min, col_max = st.columns(2)
            current_min = (thresholds.get(name, {}) or {}).get("min")
            current_max = (thresholds.get(name, {}) or {}).get("max")
            with col_min:
                min_val = st.number_input(f"{name.title()} min ({unit})", value=float(current_min) if current_min is not None else 0.0, key=f"min_{name}")
            with col_max:
                max_val = st.number_input(f"{name.title()} max ({unit})", value=float(current_max) if current_max is not None else 0.0, key=f"max_{name}")
            updated[name] = {"min": float(min_val), "max": float(max_val)}

        if st.button("Save Thresholds"):
            if update_thresholds_api(updated):
                st.success("Thresholds updated")
                st.cache_data.clear()
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to update thresholds")

        st.markdown("---")
        st.subheader("Device Commands")
        status_filter = st.selectbox("Filter status", ["", "queued", "failed", "sent", "acknowledged"], index=0)
        cmds = fetch_commands(status_filter or None, limit=50)
        df_cmds = pd.DataFrame(cmds.get("data", []))
        if not df_cmds.empty:
            st.dataframe(df_cmds, use_container_width=True)
            to_requeue = st.text_input("Command ID to requeue", value="")
            if st.button("Requeue Command"):
                try:
                    cid = int(to_requeue)
                    if requeue_command_api(cid):
                        st.success("Requeued")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to requeue")
                except ValueError:
                    st.error("Enter a valid numeric ID")
        else:
            st.info("No commands found")
    
    with tab6:
        st.subheader("Tray Management")
        
        # Create/Edit Tray Form
        create_tray_form()
        
        st.markdown("---")
        
        # Display existing trays
        st.subheader("Existing Trays")
        if not trays_data.empty:
            # Filter trays by location if needed
            location_trays = trays_data[trays_data['location'] == location] if 'location' in trays_data.columns else trays_data
            
            if not location_trays.empty:
                # Display trays in a nice format
                for _, tray in location_trays.iterrows():
                    with st.expander(f"🌿 {tray.get('tray_code', 'Unknown')} - {tray.get('crop_type', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Location:** {tray.get('location', 'N/A')}")
                            st.write(f"**Device ID:** {tray.get('device_id', 'N/A')}")
                            st.write(f"**Crop Type:** {tray.get('crop_type', 'N/A')}")
                            st.write(f"**Planted On:** {tray.get('planted_on', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Expected Harvest:** {tray.get('expected_harvest', 'N/A')}")
                            st.write(f"**Grow Medium:** {tray.get('grow_medium', 'N/A')}")
                            st.write(f"**Batch Code:** {tray.get('batch_code', 'N/A')}")
                            st.write(f"**Seed Density:** {tray.get('seed_density', 'N/A')} seeds/cm²")
                            st.write(f"**Lighting Profile:** {tray.get('lighting_profile', 'N/A')}")
                        
                        if tray.get('notes'):
                            st.write(f"**Notes:** {tray.get('notes')}")
                
                # Also show as a table
                st.subheader("Trays Table View")
                display_cols = ['tray_code', 'location', 'crop_type', 'planted_on', 'expected_harvest', 'grow_medium', 'batch_code', 'seed_density', 'lighting_profile']
                display_cols = [col for col in display_cols if col in location_trays.columns]
                
                st.dataframe(
                    location_trays[display_cols],
                    use_container_width=True
                )
            else:
                st.info(f"No trays found for location: {location}")
        else:
            st.info("No tray data available")
    
    with tab7:
        st.subheader("Growth Forecasts")
        
        # Forecast controls
        col1, col2 = st.columns(2)
        with col1:
            forecast_days = st.selectbox(
                "Forecast Horizon",
                [7, 14, 30, 60, 90],
                index=2,
                help="Number of days to forecast ahead"
            )
        
        with col2:
            if st.button("Refresh Forecasts", key="refresh_forecasts"):
                st.cache_data.clear()
                st.rerun()
        
        # Fetch forecasts with selected horizon
        if forecast_days != 30:  # Only refetch if different from default
            forecasts_data = fetch_forecasts(location, forecast_days)
        
        if not forecasts_data.empty:
            # Forecast chart
            fig = create_forecast_chart(forecasts_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast summary
            st.subheader("Forecast Summary")
            if 'predicted_value' in forecasts_data.columns:
                latest_forecast = forecasts_data[forecasts_data['predicted_value'].notna()].iloc[-1] if not forecasts_data[forecasts_data['predicted_value'].notna()].empty else None
                
                if latest_forecast is not None:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Latest Prediction", f"{latest_forecast['predicted_value']:.2f}")
                    with col2:
                        if 'confidence_lower' in latest_forecast and 'confidence_upper' in latest_forecast:
                            confidence_range = latest_forecast['confidence_upper'] - latest_forecast['confidence_lower']
                            st.metric("Confidence Range", f"±{confidence_range:.2f}")
                        else:
                            st.metric("Confidence Range", "N/A")
                    with col3:
                        if 'model_accuracy' in latest_forecast:
                            st.metric("Model Accuracy", f"{latest_forecast['model_accuracy']:.1f}%")
                        else:
                            st.metric("Model Accuracy", "N/A")
            
            # Forecast data table
            st.subheader("Forecast Data")
            display_cols = ['timestamp', 'predicted_value', 'confidence_lower', 'confidence_upper', 'model_accuracy']
            display_cols = [col for col in display_cols if col in forecasts_data.columns]
            
            st.dataframe(
                forecasts_data[display_cols].head(20),
                use_container_width=True
            )
        else:
            st.info("No forecast data available. This could mean:")
            st.write("• No ML models have been trained yet")
            st.write("• Insufficient historical data for predictions")
            st.write("• The forecast service is not running")
            st.write("• Check the ML pipeline and ensure models are trained")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Green Engine Dashboard - IoT Microgreen Monitoring System</p>",
        unsafe_allow_html=True
    )

    # Defer auto-refresh until after the page is fully drawn
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
