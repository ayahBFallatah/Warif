# Green Engine User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Sensor Data Management](#sensor-data-management)
5. [Tray Management](#tray-management)
6. [Alert System](#alert-system)
7. [Device Commands](#device-commands)
8. [Analytics and Reports](#analytics-and-reports)
9. [Machine Learning Predictions](#machine-learning-predictions)
10. [User Management](#user-management)
11. [System Configuration](#system-configuration)
12. [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing the System

1. **Open your web browser** and navigate to: `http://localhost:8501`
2. **Login** with your credentials:
   - Username: Your assigned username
   - Password: Your assigned password
3. **Click "Login"** to access the dashboard

### Default Credentials

- **Administrator**: `admin` / `admin123`
- **Operator**: `operator1` / `operator123`
- **Viewer**: `viewer1` / `viewer123`

### First Time Setup

1. **Change default passwords** immediately after first login
2. **Configure sensor thresholds** in the Admin panel
3. **Set up your first tray** in the Trays section
4. **Review system alerts** in the Alerts tab

## Dashboard Overview

The Green Engine dashboard provides a comprehensive view of your greenhouse operations:

### Main Navigation Tabs

- **📊 Overview**: System summary and key metrics
- **🌡️ Sensors**: Real-time sensor data and charts
- **🌿 Trays**: Crop and tray management
- **🚨 Alerts**: System alerts and notifications
- **📈 Analytics**: Performance analytics and trends
- **🔮 Forecasts**: ML predictions and forecasting
- **🛠️ Admin**: System administration (Admin/Operator only)

### Dashboard Features

- **Real-time Updates**: Data refreshes automatically
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Interactive Charts**: Click and zoom on data visualizations
- **Export Capabilities**: Download data and reports
- **Time Range Selection**: View data for different periods

## User Roles and Permissions

### Administrator Role

**Full system access including:**
- ✅ Create, edit, and delete users
- ✅ Manage user roles and permissions
- ✅ Configure system settings and thresholds
- ✅ Access all data and features
- ✅ View audit logs and system events
- ✅ Manage device commands and automation

### Operator Role

**Operational access including:**
- ✅ View sensor data and analytics
- ✅ Manage trays and crop information
- ✅ Acknowledge and resolve alerts
- ✅ Send device commands
- ✅ Access ML predictions and forecasts
- ❌ Cannot manage users or system settings

### Viewer Role

**Read-only access including:**
- ✅ View sensor data and analytics
- ✅ View tray information
- ✅ View alerts (cannot acknowledge/resolve)
- ✅ Access ML predictions and forecasts
- ❌ Cannot modify any data or settings
- ❌ Cannot send device commands

## Sensor Data Management

### Viewing Sensor Data

1. **Navigate to Sensors tab**
2. **Select time range** from dropdown (1 hour to 1 year)
3. **Choose device** to filter data (if multiple devices)
4. **View real-time charts** for:
   - Temperature (°C)
   - Humidity (%)
   - PAR (Photosynthetically Active Radiation)
   - Soil Moisture (%)
   - EC (Electrical Conductivity)
   - CO2 (ppm)

### Understanding Sensor Readings

#### Temperature
- **Optimal Range**: 18-28°C
- **Too Low**: <18°C - Growth slows, risk of frost damage
- **Too High**: >28°C - Heat stress, wilting, reduced yield

#### Humidity
- **Optimal Range**: 40-80%
- **Too Low**: <40% - Increased transpiration, water stress
- **Too High**: >80% - Risk of fungal diseases, poor pollination

#### PAR (Light)
- **Optimal Range**: 200-600 μmol/m²/s
- **Too Low**: <200 - Insufficient photosynthesis
- **Too High**: >600 - Light stress, leaf burn

#### Soil Moisture
- **Optimal Range**: 20-60%
- **Too Low**: <20% - Water stress, wilting
- **Too High**: >60% - Root rot, oxygen deprivation

## Tray Management

### Creating a New Tray

1. **Go to Trays tab**
2. **Click "Add New Tray"**
3. **Fill in required information:**
   - Tray Code: Unique identifier
   - Device ID: Associated sensor device
   - Crop Type: Type of crop being grown
   - Planted Date: When seeds were planted
   - Expected Harvest: Estimated harvest date
   - Grow Medium: Growing medium used
   - Batch/Lot: Batch identifier
   - Seed Density: Seeds per unit area
   - Lighting Profile: Light schedule
   - Notes: Additional information
4. **Click "Save Tray"**

### Managing Existing Trays

- **View tray details** by clicking on a tray
- **Edit tray information** using the edit button
- **Delete trays** (Admin/Operator only)
- **Track growth progress** with measurements

### Tray Status Indicators

- 🟢 **Healthy**: All parameters within optimal ranges
- 🟡 **Warning**: Some parameters outside optimal ranges
- 🔴 **Critical**: Multiple parameters in critical ranges
- ⚪ **Inactive**: No recent sensor data

## Alert System

### Types of Alerts

#### System Alerts
- **Device Offline**: Sensor device not responding
- **Data Quality**: Missing or invalid sensor data
- **System Errors**: Application or database errors

#### Environmental Alerts
- **Temperature**: Outside optimal range
- **Humidity**: Too high or too low
- **Light**: Insufficient or excessive
- **Soil Moisture**: Water stress conditions

#### Crop Alerts
- **Growth Rate**: Slower than expected
- **Harvest Prediction**: Early or delayed harvest
- **Disease Risk**: Conditions favorable for disease

### Managing Alerts

#### Acknowledging Alerts
1. **Go to Alerts tab**
2. **Find the alert** you want to acknowledge
3. **Click "Acknowledge"** button
4. **Add optional notes** explaining your action
5. **Alert status changes** to "Acknowledged"

#### Resolving Alerts
1. **After taking corrective action**
2. **Click "Resolve"** button
3. **Add resolution notes** describing what was done
4. **Alert status changes** to "Resolved"

### Alert Levels

- 🔴 **Critical**: Immediate action required
- 🟡 **Warning**: Attention needed soon
- 🔵 **Info**: Informational, no immediate action

## Device Commands

### Sending Commands

1. **Go to Admin tab**
2. **Navigate to Device Commands section**
3. **Click "Send Command"**
4. **Select device** from dropdown
5. **Choose command type:**
   - Irrigation: Control watering systems
   - Lighting: Adjust grow lights
   - Ventilation: Control fans and vents
   - Heating: Adjust temperature systems
6. **Set parameters** (duration, intensity, etc.)
7. **Click "Send Command"**

### Command History

- **View all sent commands** in the command history
- **See command status** (sent, delivered, failed)
- **Requeue failed commands** if needed
- **Track command execution** and results

### Command Types

#### Irrigation Commands
- **Duration**: How long to water (seconds)
- **Intensity**: Water flow rate
- **Zone**: Specific irrigation zone

#### Lighting Commands
- **Brightness**: Light intensity percentage
- **Schedule**: On/off timing
- **Spectrum**: Light color temperature

#### Ventilation Commands
- **Fan Speed**: Fan speed percentage
- **Duration**: How long to run
- **Direction**: Intake or exhaust

## Analytics and Reports

### Key Metrics Dashboard

The Analytics tab provides insights into:

- **Growth Performance**: Average growth rates
- **Yield Predictions**: Expected harvest amounts
- **Environmental Trends**: Temperature, humidity patterns
- **Device Performance**: Sensor accuracy and uptime
- **Alert Frequency**: System health indicators

### Time Range Analysis

Select different time periods to analyze:
- **1 Hour**: Real-time monitoring
- **1 Day**: Daily patterns
- **1 Week**: Weekly trends
- **1 Month**: Monthly performance
- **90 Days**: Seasonal analysis
- **1 Year**: Annual trends

### Exporting Data

1. **Select desired time range**
2. **Choose data type** (sensor data, analytics, etc.)
3. **Click "Export"** button
4. **Download CSV file** for external analysis

## Machine Learning Predictions

### Yield Predictions

The system uses machine learning to predict:
- **Expected yield** for each tray
- **Harvest timing** optimization
- **Growth trajectory** forecasting
- **Quality predictions** based on conditions

### Accessing Predictions

1. **Go to Forecasts tab**
2. **Select tray** to view predictions
3. **Choose prediction type:**
   - Yield forecast
   - Growth trajectory
   - Harvest timing
4. **View confidence intervals** and accuracy metrics

### Model Performance

- **Accuracy metrics** for each model
- **Training data quality** indicators
- **Prediction confidence** levels
- **Model retraining** status

## User Management

### Creating New Users (Admin Only)

1. **Go to Admin tab**
2. **Navigate to User Management**
3. **Click "Add User"**
4. **Fill in user details:**
   - Username: Unique identifier
   - Email: User's email address
   - Password: Initial password
   - Role: Admin, Operator, or Viewer
5. **Click "Create User"**

### Managing User Roles

- **Change user roles** as needed
- **Reset passwords** for users
- **Deactivate users** who no longer need access
- **View user activity** and login history

### Password Management

- **Change your password** in user settings
- **Reset forgotten passwords** via email
- **Enforce password policies** (Admin only)

## System Configuration

### Sensor Thresholds (Admin Only)

Configure alert thresholds for each sensor:

1. **Go to Admin tab**
2. **Navigate to Sensor Thresholds**
3. **Adjust thresholds** for:
   - Temperature (min/max)
   - Humidity (min/max)
   - Soil Moisture (min/max)
   - PAR (min/max)
   - EC (min/max)
   - CO2 (min/max)
4. **Click "Save Thresholds"**

### System Settings

- **Time zone configuration**
- **Data retention policies**
- **Alert notification settings**
- **Backup and maintenance schedules**

## Troubleshooting

### Common Issues

#### Cannot Login
- **Check username/password** spelling
- **Verify account is active**
- **Contact administrator** if locked out

#### No Sensor Data
- **Check device connectivity**
- **Verify device is online**
- **Check sensor thresholds**
- **Review alert notifications**

#### Dashboard Not Loading
- **Refresh the browser page**
- **Check internet connection**
- **Clear browser cache**
- **Try different browser**

#### Commands Not Working
- **Verify device is online**
- **Check command history**
- **Review device logs**
- **Test with simple commands**

### Getting Help

1. **Check this manual** for common solutions
2. **Review system alerts** for error messages
3. **Contact your system administrator**
4. **Check the troubleshooting guide** for detailed solutions

### System Requirements

- **Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Internet Connection**: Stable connection for real-time updates
- **Screen Resolution**: Minimum 1024x768 for optimal display
- **JavaScript**: Must be enabled for full functionality

## Best Practices

### Daily Operations
- **Check alerts** first thing in the morning
- **Review sensor data** for any anomalies
- **Monitor tray progress** and growth rates
- **Acknowledge and resolve** any issues

### Weekly Tasks
- **Review analytics** and performance trends
- **Check ML predictions** for accuracy
- **Update tray information** as needed
- **Review user access** and permissions

### Monthly Maintenance
- **Export data** for backup
- **Review system performance**
- **Update user passwords**
- **Check system logs** for errors

### Security Best Practices
- **Use strong passwords**
- **Log out** when finished
- **Don't share credentials**
- **Report suspicious activity**
- **Keep software updated**

---

*For technical support or additional questions, contact your system administrator or refer to the technical documentation.*
