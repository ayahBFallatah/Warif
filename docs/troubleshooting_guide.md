# Green Engine Troubleshooting Guide

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Dashboard Issues](#dashboard-issues)
3. [API and Backend Issues](#api-and-backend-issues)
4. [Database Issues](#database-issues)
5. [MQTT and Device Connectivity](#mqtt-and-device-connectivity)
6. [Authentication and Security](#authentication-and-security)
7. [Performance Issues](#performance-issues)
8. [Data Quality Issues](#data-quality-issues)
9. [Alert System Issues](#alert-system-issues)
10. [Machine Learning Issues](#machine-learning-issues)
11. [System Logs and Monitoring](#system-logs-and-monitoring)
12. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostic Checklist

### Before Starting Troubleshooting

1. **Check System Status**
   - [ ] API server is running (port 8010)
   - [ ] Database is accessible
   - [ ] MQTT broker is running
   - [ ] Dashboard is accessible (port 8501)

2. **Verify Network Connectivity**
   - [ ] Internet connection is stable
   - [ ] Local network is working
   - [ ] Firewall allows required ports
   - [ ] DNS resolution is working

3. **Check User Access**
   - [ ] Valid login credentials
   - [ ] Appropriate user role
   - [ ] Session not expired
   - [ ] Account is active

## Dashboard Issues

### Dashboard Won't Load

**Symptoms:**
- Blank page or loading spinner
- "Connection refused" error
- Browser shows "This site can't be reached"

**Diagnostic Steps:**
1. **Check if Streamlit is running:**
   ```bash
   ps aux | grep streamlit
   netstat -tlnp | grep 8501
   ```

2. **Verify port availability:**
   ```bash
   lsof -i :8501
   ```

3. **Check Streamlit logs:**
   ```bash
   tail -f ~/.streamlit/logs/streamlit.log
   ```

**Solutions:**
1. **Restart Streamlit:**
   ```bash
   cd /path/to/green_engine/dashboard
   python3 -m streamlit run app.py --server.port 8501
   ```

2. **Check for port conflicts:**
   ```bash
   # Use different port if 8501 is busy
   python3 -m streamlit run app.py --server.port 8502
   ```

3. **Clear browser cache:**
   - Hard refresh (Ctrl+F5 or Cmd+Shift+R)
   - Clear browser cache and cookies
   - Try incognito/private mode

### Dashboard Shows "Failed to fetch" Errors

**Symptoms:**
- "Failed to fetch sensor data: 500"
- "Failed to fetch alerts: 500"
- API connection errors

**Diagnostic Steps:**
1. **Check API server status:**
   ```bash
   curl http://localhost:8010/health
   ```

2. **Verify API logs:**
   ```bash
   # Check API server logs
   tail -f /var/log/green_engine/api.log
   ```

3. **Test API endpoints directly:**
   ```bash
   curl -X GET "http://localhost:8010/api/v1/sensor-data" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

**Solutions:**
1. **Restart API server:**
   ```bash
   cd /path/to/green_engine
   python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload
   ```

2. **Check database connection:**
   ```bash
   # Test database connectivity
   python3 -c "
   import psycopg2
   conn = psycopg2.connect(
       host='localhost',
       database='green_engine',
       user='green_user',
       password='green_pass'
   )
   print('Database connection successful')
   conn.close()
   "
   ```

3. **Verify environment variables:**
   ```bash
   cat .env | grep -E "(DB_|API_)"
   ```

### Dashboard Authentication Issues

**Symptoms:**
- Login form doesn't appear
- "Invalid credentials" error
- Session expires immediately

**Diagnostic Steps:**
1. **Check authentication service:**
   ```bash
   curl -X POST "http://localhost:8010/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

2. **Verify user exists in database:**
   ```sql
   SELECT username, email, is_active FROM users WHERE username = 'admin';
   ```

**Solutions:**
1. **Reset user password:**
   ```sql
   UPDATE users SET password_hash = '$2b$12$...' WHERE username = 'admin';
   ```

2. **Check JWT secret:**
   ```bash
   echo $JWT_SECRET_KEY
   ```

3. **Clear browser session:**
   - Clear cookies for localhost:8501
   - Restart browser
   - Try different browser

## API and Backend Issues

### API Server Won't Start

**Symptoms:**
- "Address already in use" error
- "Module not found" errors
- Server crashes on startup

**Diagnostic Steps:**
1. **Check port availability:**
   ```bash
   lsof -i :8010
   netstat -tlnp | grep 8010
   ```

2. **Check Python dependencies:**
   ```bash
   pip3 list | grep -E "(fastapi|uvicorn|psycopg2)"
   ```

3. **Check environment variables:**
   ```bash
   env | grep -E "(DB_|JWT_|API_)"
   ```

**Solutions:**
1. **Kill existing process:**
   ```bash
   sudo kill -9 $(lsof -t -i:8010)
   ```

2. **Install missing dependencies:**
   ```bash
   pip3 install fastapi uvicorn psycopg2-binary python-dotenv
   ```

3. **Set environment variables:**
   ```bash
   export DB_HOST=postgres
   export DB_NAME=green_engine
   export DB_USER=green_user
   export DB_PASSWORD=green_pass
   export JWT_SECRET_KEY=your-secret-key
   ```

### API Returns 500 Errors

**Symptoms:**
- Internal server errors
- "Database connection failed"
- "Module import error"

**Diagnostic Steps:**
1. **Check API logs:**
   ```bash
   tail -f /var/log/green_engine/api.log
   ```

2. **Test database connection:**
   ```python
   import psycopg2
   try:
       conn = psycopg2.connect(
           host='localhost',
           database='green_engine',
           user='green_user',
           password='green_pass'
       )
       print("Database OK")
       conn.close()
   except Exception as e:
       print(f"Database Error: {e}")
   ```

3. **Check Python path:**
   ```bash
   python3 -c "import sys; print(sys.path)"
   ```

**Solutions:**
1. **Restart database:**
   ```bash
   sudo systemctl restart postgresql
   ```

2. **Fix import paths:**
   ```bash
   export PYTHONPATH=/path/to/green_engine:$PYTHONPATH
   ```

3. **Check file permissions:**
   ```bash
   ls -la src/api/main.py
   chmod +x src/api/main.py
   ```

## Database Issues

### Database Connection Failed

**Symptoms:**
- "Connection refused" to database
- "Authentication failed"
- "Database does not exist"

**Diagnostic Steps:**
1. **Check PostgreSQL status:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Test connection:**
   ```bash
   psql -h localhost -U green_user -d green_engine
   ```

3. **Check database exists:**
   ```bash
   psql -h localhost -U postgres -c "\l" | grep green_engine
   ```

**Solutions:**
1. **Start PostgreSQL:**
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Create database:**
   ```bash
   sudo -u postgres createdb green_engine
   sudo -u postgres createuser green_user
   sudo -u postgres psql -c "ALTER USER green_user PASSWORD 'green_pass';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE green_engine TO green_user;"
   ```

3. **Run database setup:**
   ```bash
   python3 scripts/setup_db_local.py
   ```

### Database Schema Issues

**Symptoms:**
- "Table does not exist" errors
- "Column does not exist" errors
- Data not appearing in dashboard

**Diagnostic Steps:**
1. **Check table existence:**
   ```sql
   \dt
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

2. **Check table structure:**
   ```sql
   \d sensor_readings
   \d users
   \d alerts
   ```

**Solutions:**
1. **Recreate database schema:**
   ```bash
   python3 scripts/setup_db_local.py
   ```

2. **Run migrations:**
   ```bash
   python3 scripts/migrate_database.py
   ```

3. **Check for schema conflicts:**
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   GRANT ALL ON SCHEMA public TO green_user;
   ```

## MQTT and Device Connectivity

### MQTT Broker Issues

**Symptoms:**
- Devices show "Offline" status
- "Connection refused" to MQTT broker
- No data received from devices

**Diagnostic Steps:**
1. **Check MQTT broker status:**
   ```bash
   sudo systemctl status mosquitto
   netstat -tlnp | grep 1883
   ```

2. **Test MQTT connection:**
   ```bash
   mosquitto_pub -h localhost -t "test/topic" -m "test message"
   mosquitto_sub -h localhost -t "test/topic"
   ```

3. **Check broker logs:**
   ```bash
   tail -f /var/log/mosquitto/mosquitto.log
   ```

**Solutions:**
1. **Start MQTT broker:**
   ```bash
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

2. **Configure broker:**
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   # Add:
   # listener 1883
   # allow_anonymous true
   ```

3. **Restart broker:**
   ```bash
   sudo systemctl restart mosquitto
   ```

### Device Connection Issues

**Symptoms:**
- Device shows "Offline" in dashboard
- No telemetry data received
- Device commands not working

**Diagnostic Steps:**
1. **Check device network:**
   ```bash
   ping device_ip_address
   telnet device_ip_address 1883
   ```

2. **Test MQTT from device:**
   ```bash
   mosquitto_pub -h mqtt_broker_ip -t "greenengine/DEVICE_ID/test" -m "test"
   ```

3. **Check device certificates:**
   ```bash
   openssl x509 -in device.crt -text -noout
   ```

**Solutions:**
1. **Restart device:**
   - Power cycle the device
   - Check device logs
   - Verify network configuration

2. **Update device configuration:**
   - Check MQTT broker address
   - Verify topic configuration
   - Update certificates if needed

3. **Check firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 1883
   sudo ufw allow 8883
   ```

## Authentication and Security

### JWT Token Issues

**Symptoms:**
- "Invalid token" errors
- "Token expired" errors
- Authentication failures

**Diagnostic Steps:**
1. **Check JWT secret:**
   ```bash
   echo $JWT_SECRET_KEY
   ```

2. **Decode JWT token:**
   ```bash
   # Use jwt.io or Python
   python3 -c "
   import jwt
   token = 'YOUR_TOKEN'
   decoded = jwt.decode(token, options={'verify_signature': False})
   print(decoded)
   "
   ```

3. **Check token expiration:**
   ```python
   import jwt
   from datetime import datetime
   token = 'YOUR_TOKEN'
   decoded = jwt.decode(token, options={'verify_signature': False})
   exp = datetime.fromtimestamp(decoded['exp'])
   print(f"Token expires: {exp}")
   ```

**Solutions:**
1. **Set JWT secret:**
   ```bash
   export JWT_SECRET_KEY="your-secret-key-here"
   ```

2. **Generate new token:**
   ```bash
   curl -X POST "http://localhost:8010/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

3. **Check system time:**
   ```bash
   date
   # Ensure system time is correct
   ```

### Permission Issues

**Symptoms:**
- "Access denied" errors
- "Insufficient permissions" errors
- Features not available

**Diagnostic Steps:**
1. **Check user role:**
   ```sql
   SELECT u.username, r.role_name 
   FROM users u 
   JOIN user_roles ur ON u.user_id = ur.user_id 
   JOIN roles r ON ur.role_id = r.role_id 
   WHERE u.username = 'username';
   ```

2. **Check permissions:**
   ```sql
   SELECT r.role_name, r.permissions 
   FROM roles r 
   WHERE r.role_name = 'admin';
   ```

**Solutions:**
1. **Update user role:**
   ```sql
   UPDATE user_roles 
   SET role_id = (SELECT role_id FROM roles WHERE role_name = 'admin') 
   WHERE user_id = (SELECT user_id FROM users WHERE username = 'username');
   ```

2. **Check role permissions:**
   ```sql
   UPDATE roles 
   SET permissions = '{"sensors": ["create", "read", "update", "delete"]}' 
   WHERE role_name = 'admin';
   ```

## Performance Issues

### Slow Dashboard Loading

**Symptoms:**
- Dashboard takes long to load
- Charts render slowly
- Timeout errors

**Diagnostic Steps:**
1. **Check system resources:**
   ```bash
   top
   free -h
   df -h
   ```

2. **Check database performance:**
   ```sql
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

3. **Check API response times:**
   ```bash
   time curl http://localhost:8010/api/v1/sensor-data
   ```

**Solutions:**
1. **Optimize database queries:**
   ```sql
   CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp);
   CREATE INDEX idx_sensor_readings_device_id ON sensor_readings(device_id);
   ```

2. **Increase system resources:**
   - Add more RAM
   - Use SSD storage
   - Optimize database configuration

3. **Implement caching:**
   ```python
   # Add Redis caching
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   ```

### High Memory Usage

**Symptoms:**
- System running out of memory
- OOM (Out of Memory) errors
- Slow performance

**Diagnostic Steps:**
1. **Check memory usage:**
   ```bash
   free -h
   ps aux --sort=-%mem | head -10
   ```

2. **Check for memory leaks:**
   ```bash
   valgrind --tool=memcheck python3 src/api/main.py
   ```

**Solutions:**
1. **Restart services:**
   ```bash
   sudo systemctl restart postgresql
   sudo systemctl restart mosquitto
   ```

2. **Optimize database:**
   ```sql
   VACUUM ANALYZE;
   REINDEX DATABASE green_engine;
   ```

3. **Add swap space:**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

## Data Quality Issues

### Missing Sensor Data

**Symptoms:**
- Gaps in sensor readings
- No data for certain time periods
- Incomplete data sets

**Diagnostic Steps:**
1. **Check data gaps:**
   ```sql
   SELECT device_id, 
          MIN(timestamp) as first_reading,
          MAX(timestamp) as last_reading,
          COUNT(*) as total_readings
   FROM sensor_readings 
   GROUP BY device_id;
   ```

2. **Check for null values:**
   ```sql
   SELECT COUNT(*) as null_temperature 
   FROM sensor_readings 
   WHERE temperature IS NULL;
   ```

**Solutions:**
1. **Check device connectivity:**
   - Verify device is online
   - Check MQTT connection
   - Review device logs

2. **Implement data validation:**
   ```python
   def validate_sensor_data(data):
       required_fields = ['temperature', 'humidity', 'timestamp']
       for field in required_fields:
           if field not in data or data[field] is None:
               raise ValueError(f"Missing required field: {field}")
   ```

### Invalid Sensor Readings

**Symptoms:**
- Readings outside expected ranges
- Negative values where not expected
- Unrealistic data points

**Diagnostic Steps:**
1. **Check for outliers:**
   ```sql
   SELECT * FROM sensor_readings 
   WHERE temperature < -10 OR temperature > 50;
   ```

2. **Check data ranges:**
   ```sql
   SELECT 
     MIN(temperature) as min_temp,
     MAX(temperature) as max_temp,
     AVG(temperature) as avg_temp
   FROM sensor_readings;
   ```

**Solutions:**
1. **Implement data validation:**
   ```python
   def validate_temperature(temp):
       if temp < -10 or temp > 50:
           raise ValueError(f"Temperature {temp} outside valid range")
   ```

2. **Add data cleaning:**
   ```sql
   UPDATE sensor_readings 
   SET temperature = NULL 
   WHERE temperature < -10 OR temperature > 50;
   ```

## Alert System Issues

### Alerts Not Triggering

**Symptoms:**
- No alerts generated for threshold violations
- Alerts not appearing in dashboard
- Alert rules not working

**Diagnostic Steps:**
1. **Check alert rules:**
   ```sql
   SELECT * FROM alert_rules WHERE is_active = true;
   ```

2. **Check threshold configuration:**
   ```sql
   SELECT * FROM system_config WHERE key = 'sensor_thresholds';
   ```

3. **Check rules engine:**
   ```python
   from src.utils.rules_engine import RulesEngine
   engine = RulesEngine()
   # Test rule evaluation
   ```

**Solutions:**
1. **Update alert rules:**
   ```sql
   UPDATE alert_rules 
   SET is_active = true 
   WHERE rule_id = 'temperature_high';
   ```

2. **Check rules engine configuration:**
   ```python
   # Verify rules engine is properly initialized
   # Check rule evaluation logic
   ```

### Alert Notifications Not Working

**Symptoms:**
- Alerts generated but no notifications sent
- Email/Slack notifications not received
- Notification service errors

**Diagnostic Steps:**
1. **Check notification configuration:**
   ```bash
   echo $SLACK_WEBHOOK_URL
   echo $EMAIL_SMTP_SERVER
   ```

2. **Test notification service:**
   ```python
   import requests
   webhook_url = "YOUR_SLACK_WEBHOOK"
   response = requests.post(webhook_url, json={"text": "Test message"})
   print(response.status_code)
   ```

**Solutions:**
1. **Configure notification services:**
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
   export EMAIL_SMTP_SERVER="smtp.gmail.com"
   ```

2. **Test notification delivery:**
   ```python
   # Send test notification
   # Verify webhook/email configuration
   ```

## Machine Learning Issues

### ML Predictions Not Working

**Symptoms:**
- "Failed to predict" errors
- No predictions in dashboard
- Model loading errors

**Diagnostic Steps:**
1. **Check model files:**
   ```bash
   ls -la data/models/
   ```

2. **Test model loading:**
   ```python
   from src.models.prediction_service import get_prediction_service
   service = get_prediction_service()
   # Test prediction
   ```

3. **Check training data:**
   ```sql
   SELECT COUNT(*) FROM sensor_readings;
   SELECT COUNT(*) FROM processed_features;
   ```

**Solutions:**
1. **Retrain models:**
   ```bash
   python3 src/models/train_models.py
   ```

2. **Check data quality:**
   ```python
   # Verify training data is complete
   # Check for missing values
   # Validate data format
   ```

3. **Update model service:**
   ```python
   # Restart prediction service
   # Check model file permissions
   ```

## System Logs and Monitoring

### Log File Locations

**System Logs:**
- API logs: `/var/log/green_engine/api.log`
- Database logs: `/var/log/postgresql/postgresql.log`
- MQTT logs: `/var/log/mosquitto/mosquitto.log`
- System logs: `/var/log/syslog`

**Application Logs:**
- Streamlit logs: `~/.streamlit/logs/streamlit.log`
- Python logs: Check application output

### Log Analysis Commands

```bash
# View recent API errors
tail -f /var/log/green_engine/api.log | grep ERROR

# Check database connections
grep "connection" /var/log/postgresql/postgresql.log

# Monitor MQTT activity
tail -f /var/log/mosquitto/mosquitto.log

# Check system resources
top -p $(pgrep -f "python.*api")
```

### Monitoring Commands

```bash
# Check service status
systemctl status postgresql mosquitto

# Monitor disk usage
df -h

# Check memory usage
free -h

# Monitor network connections
netstat -tlnp | grep -E "(8010|8501|1883|5432)"
```

## Emergency Procedures

### Complete System Restart

1. **Stop all services:**
   ```bash
   sudo systemctl stop postgresql
   sudo systemctl stop mosquitto
   pkill -f streamlit
   pkill -f uvicorn
   ```

2. **Clear temporary files:**
   ```bash
   rm -rf /tmp/streamlit*
   rm -rf /tmp/uvicorn*
   ```

3. **Restart services in order:**
   ```bash
   sudo systemctl start postgresql
   sudo systemctl start mosquitto
   # Start API server
   # Start dashboard
   ```

### Database Recovery

1. **Stop services:**
   ```bash
   sudo systemctl stop postgresql
   ```

2. **Restore from backup:**
   ```bash
   sudo -u postgres pg_restore -d green_engine /backup/green_engine_backup.dump
   ```

3. **Start services:**
   ```bash
   sudo systemctl start postgresql
   ```

### Emergency Contact Information

- **System Administrator**: admin@greenengine.com
- **Technical Support**: support@greenengine.com
- **Emergency Hotline**: +1-800-GREEN-ENGINE

---

*For additional troubleshooting assistance, contact your system administrator or refer to the technical documentation.*
