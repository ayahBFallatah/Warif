# Device Onboarding Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Device Registration](#device-registration)
4. [Network Configuration](#network-configuration)
5. [Security Setup](#security-setup)
6. [Testing and Validation](#testing-and-validation)
7. [Troubleshooting](#troubleshooting)
8. [Device Management](#device-management)

## Overview

This guide walks you through the process of onboarding new IoT devices to the Green Engine platform. The system supports various sensor types and communication protocols, with MQTT being the primary method for data transmission.

### Supported Device Types

- **Environmental Sensors**: Temperature, humidity, light (PAR), CO2
- **Soil Sensors**: Moisture, electrical conductivity (EC), pH
- **Actuators**: Irrigation systems, grow lights, ventilation fans
- **Gateways**: MQTT brokers, data concentrators

### Communication Protocols

- **MQTT**: Primary protocol for sensor data and commands
- **MQTT over TLS**: Secure communication with client certificates
- **HTTP/HTTPS**: For device management and configuration
- **WebSocket**: Real-time bidirectional communication

## Prerequisites

### Hardware Requirements

- **IoT Device**: Compatible sensor or actuator
- **Network Connectivity**: WiFi or Ethernet connection
- **Power Supply**: Adequate power for continuous operation
- **Storage**: Sufficient memory for firmware and data buffering

### Software Requirements

- **Firmware**: Latest compatible firmware version
- **MQTT Client**: Built-in or installable MQTT client
- **TLS Support**: For secure communication
- **JSON Parser**: For data format compatibility

### Network Requirements

- **Internet Access**: For cloud connectivity
- **MQTT Broker Access**: Connection to Green Engine MQTT broker
- **Port Access**: Outbound connections on ports 8883 (MQTTS) and 443 (HTTPS)
- **DNS Resolution**: Ability to resolve broker hostname

## Device Registration

### Step 1: Create Device Entry

1. **Access the Admin Panel**
   - Login as Administrator
   - Navigate to Admin → Device Management

2. **Add New Device**
   - Click "Add Device"
   - Fill in device information:
     ```
     Device ID: GH-A1-DEV-01
     Device Name: Greenhouse A Sensor 1
     Device Type: Environmental Sensor
     Location: Greenhouse A
     Model: GreenSense Pro
     Firmware Version: 1.2.3
     ```

3. **Configure Device Settings**
   - Set data transmission interval (e.g., 60 seconds)
   - Configure sensor parameters
   - Set alert thresholds
   - Enable/disable specific sensors

### Step 2: Generate Device Credentials

1. **Create Device Certificate**
   ```bash
   # Generate device private key
   openssl genrsa -out device.key 2048
   
   # Create certificate signing request
   openssl req -new -key device.key -out device.csr \
     -subj "/CN=GH-A1-DEV-01/O=GreenEngine/OU=Devices"
   
   # Sign certificate with CA
   openssl x509 -req -in device.csr -CA ca.crt -CAkey ca.key \
     -CAcreateserial -out device.crt -days 365
   ```

2. **Store Credentials Securely**
   - Save device.crt, device.key, and ca.crt
   - Use secure file transfer to device
   - Set appropriate file permissions (600 for keys)

### Step 3: Device Configuration

1. **Configure MQTT Settings**
   ```json
   {
     "mqtt": {
       "broker": "mqtt.greenengine.local",
       "port": 8883,
       "use_tls": true,
       "ca_cert": "/certs/ca.crt",
       "client_cert": "/certs/device.crt",
       "client_key": "/certs/device.key",
       "client_id": "GH-A1-DEV-01",
       "keepalive": 60,
       "clean_session": true
     }
   }
   ```

2. **Configure Data Format**
   ```json
   {
     "telemetry": {
       "topic": "greenengine/GH-A1-DEV-01/telemetry",
       "qos": 1,
       "retain": false,
       "interval": 60
     },
     "commands": {
       "topic": "greenengine/GH-A1-DEV-01/commands",
       "qos": 1
     }
   }
   ```

## Network Configuration

### WiFi Configuration

1. **Connect to Device**
   - Use device's WiFi hotspot or serial connection
   - Access device configuration interface

2. **Configure Network Settings**
   ```
   SSID: YourWiFiNetwork
   Password: YourWiFiPassword
   Security: WPA2-PSK
   IP Mode: DHCP (recommended) or Static
   ```

3. **Test Connectivity**
   - Ping gateway: `ping 192.168.1.1`
   - Test DNS: `nslookup mqtt.greenengine.local`
   - Check internet: `ping 8.8.8.8`

### Static IP Configuration (Optional)

If using static IP addressing:

```
IP Address: 192.168.1.100
Subnet Mask: 255.255.255.0
Gateway: 192.168.1.1
DNS Server: 192.168.1.1, 8.8.8.8
```

### Firewall Configuration

Ensure the following ports are accessible:

- **Outbound 8883**: MQTT over TLS
- **Outbound 443**: HTTPS for device management
- **Outbound 53**: DNS resolution
- **Outbound 80**: HTTP (if needed for updates)

## Security Setup

### TLS Certificate Installation

1. **Copy Certificates to Device**
   ```bash
   # Secure copy to device
   scp ca.crt device.crt device.key user@device-ip:/certs/
   
   # Set proper permissions
   chmod 600 /certs/device.key
   chmod 644 /certs/device.crt
   chmod 644 /certs/ca.crt
   ```

2. **Verify Certificate Installation**
   ```bash
   # Check certificate validity
   openssl x509 -in /certs/device.crt -text -noout
   
   # Verify certificate chain
   openssl verify -CAfile /certs/ca.crt /certs/device.crt
   ```

### Device Authentication

1. **Configure Client Certificate Authentication**
   - Device must present valid certificate
   - Certificate must be signed by trusted CA
   - Device ID must match certificate CN

2. **Enable Mutual TLS**
   - Server verifies client certificate
   - Client verifies server certificate
   - Encrypted communication channel

### Access Control

1. **Device Permissions**
   - Read access to own telemetry topic
   - Write access to own command topic
   - No access to other devices' topics

2. **Topic Structure**
   ```
   greenengine/{device_id}/telemetry    # Device publishes data
   greenengine/{device_id}/commands     # Device receives commands
   greenengine/{device_id}/status       # Device publishes status
   ```

## Testing and Validation

### Step 1: Connection Test

1. **Test MQTT Connection**
   ```bash
   # Using mosquitto client
   mosquitto_pub -h mqtt.greenengine.local -p 8883 \
     --cafile ca.crt --cert device.crt --key device.key \
     -t "greenengine/GH-A1-DEV-01/test" -m "Hello World"
   ```

2. **Verify Connection in Dashboard**
   - Check device status in Admin panel
   - Verify "Online" status
   - Check last seen timestamp

### Step 2: Data Transmission Test

1. **Send Test Telemetry**
   ```json
   {
     "device_id": "GH-A1-DEV-01",
     "timestamp": "2025-01-15T10:30:00Z",
     "readings": {
       "temperature_c": 23.5,
       "humidity_pct": 68.0,
       "par_umol_m2_s": 450.0,
       "soil_moisture_pct": 35.0,
       "ec_ms_cm": 1.2,
       "co2_ppm": 650.0
     },
     "battery": 98,
     "firmware_version": "1.2.3"
   }
   ```

2. **Verify Data Reception**
   - Check Sensors tab in dashboard
   - Verify data appears in charts
   - Confirm data accuracy

### Step 3: Command Reception Test

1. **Send Test Command**
   ```json
   {
     "command_type": "test",
     "parameters": {
       "message": "Test command received"
     },
     "timestamp": "2025-01-15T10:30:00Z"
   }
   ```

2. **Verify Command Processing**
   - Check device logs for command reception
   - Verify appropriate response
   - Test command acknowledgment

### Step 4: Alert System Test

1. **Trigger Test Alert**
   - Send data outside normal thresholds
   - Verify alert generation
   - Check alert notification

2. **Test Alert Resolution**
   - Send data back to normal range
   - Verify alert resolution
   - Check alert history

## Troubleshooting

### Common Connection Issues

#### Device Cannot Connect to MQTT Broker

**Symptoms:**
- Device shows "Offline" status
- Connection timeout errors
- Certificate verification failures

**Solutions:**
1. **Check Network Connectivity**
   ```bash
   ping mqtt.greenengine.local
   telnet mqtt.greenengine.local 8883
   ```

2. **Verify Certificate Configuration**
   ```bash
   openssl s_client -connect mqtt.greenengine.local:8883 \
     -cert device.crt -key device.key -CAfile ca.crt
   ```

3. **Check Firewall Settings**
   - Ensure port 8883 is open
   - Verify outbound connections allowed
   - Check for proxy interference

#### Certificate Errors

**Symptoms:**
- "Certificate verification failed"
- "Untrusted certificate"
- "Certificate expired"

**Solutions:**
1. **Check Certificate Validity**
   ```bash
   openssl x509 -in device.crt -dates -noout
   ```

2. **Verify Certificate Chain**
   ```bash
   openssl verify -CAfile ca.crt device.crt
   ```

3. **Regenerate Certificates**
   - Create new certificate request
   - Sign with current CA
   - Update device configuration

#### Data Not Appearing in Dashboard

**Symptoms:**
- Device shows online but no data
- Data appears delayed or incomplete
- Charts show no data points

**Solutions:**
1. **Check Topic Configuration**
   - Verify correct topic format
   - Check QoS settings
   - Confirm message format

2. **Verify Data Format**
   ```json
   {
     "device_id": "GH-A1-DEV-01",
     "timestamp": "2025-01-15T10:30:00Z",
     "readings": {
       "temperature_c": 23.5,
       "humidity_pct": 68.0
     }
   }
   ```

3. **Check Database Connection**
   - Verify API connectivity
   - Check database status
   - Review error logs

### Performance Issues

#### High Latency

**Symptoms:**
- Data appears with significant delay
- Commands take long to execute
- Dashboard updates slowly

**Solutions:**
1. **Optimize Network Settings**
   - Reduce keepalive interval
   - Increase buffer sizes
   - Use QoS 0 for non-critical data

2. **Check System Resources**
   - Monitor CPU usage
   - Check memory consumption
   - Review disk I/O

#### Data Loss

**Symptoms:**
- Missing data points
- Incomplete sensor readings
- Gaps in time series data

**Solutions:**
1. **Implement Data Buffering**
   - Store data locally during outages
   - Retry failed transmissions
   - Use QoS 1 for reliable delivery

2. **Monitor Connection Quality**
   - Track connection stability
   - Monitor packet loss
   - Check signal strength

## Device Management

### Firmware Updates

1. **Check Current Version**
   - Review device information in dashboard
   - Check firmware version in telemetry data

2. **Download New Firmware**
   - Access device manufacturer website
   - Download latest compatible version
   - Verify firmware integrity

3. **Deploy Update**
   - Use device management interface
   - Follow manufacturer instructions
   - Monitor update progress

4. **Verify Update**
   - Check new firmware version
   - Test all functionality
   - Monitor for issues

### Configuration Management

1. **Backup Current Configuration**
   ```bash
   # Export device settings
   curl -X GET "https://device-ip/api/config" \
     -H "Authorization: Bearer token" > config.json
   ```

2. **Update Configuration**
   ```bash
   # Apply new settings
   curl -X PUT "https://device-ip/api/config" \
     -H "Content-Type: application/json" \
     -d @new_config.json
   ```

3. **Verify Changes**
   - Check configuration in dashboard
   - Test device functionality
   - Monitor for errors

### Monitoring and Maintenance

1. **Regular Health Checks**
   - Monitor device uptime
   - Check data quality
   - Review error logs

2. **Preventive Maintenance**
   - Clean sensors regularly
   - Check power connections
   - Update firmware as needed

3. **Performance Monitoring**
   - Track data transmission rates
   - Monitor battery levels
   - Check signal strength

### Device Decommissioning

1. **Backup Data**
   - Export historical data
   - Save configuration settings
   - Document device history

2. **Revoke Access**
   - Remove device certificates
   - Delete device from system
   - Update access control lists

3. **Physical Removal**
   - Power down device safely
   - Remove from network
   - Dispose of hardware properly

---

*For additional support or questions about device onboarding, contact your system administrator or refer to the device manufacturer's documentation.*
