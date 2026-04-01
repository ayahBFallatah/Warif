# Green Engine Runbooks

## Overview

This document contains operational runbooks for the Green Engine system. These runbooks provide step-by-step procedures for common operational tasks, troubleshooting, and emergency response.

## Table of Contents

1. [System Health Checks](#system-health-checks)
2. [Service Management](#service-management)
3. [Database Operations](#database-operations)
4. [MQTT Operations](#mqtt-operations)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Backup and Recovery](#backup-and-recovery)
7. [Security Operations](#security-operations)
8. [Performance Tuning](#performance-tuning)
9. [Emergency Procedures](#emergency-procedures)
10. [Maintenance Procedures](#maintenance-procedures)

## System Health Checks

### Daily Health Check

**Purpose**: Verify all system components are functioning correctly

**Procedure**:

1. **Check Service Status**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Verify API Health**
   ```bash
   curl -f http://localhost:8010/health
   ```

3. **Check Dashboard**
   ```bash
   curl -f http://localhost:8501/healthz
   ```

4. **Verify Database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U green_user -d green_engine
   ```

5. **Check MQTT Broker**
   ```bash
   docker-compose -f docker-compose.prod.yml exec mosquitto mosquitto_pub -h localhost -t test -m "healthcheck"
   ```

6. **Verify Monitoring**
   ```bash
   curl -f http://localhost:9090/-/healthy  # Prometheus
   curl -f http://localhost:3000/api/health  # Grafana
   ```

**Expected Results**:
- All services should be running
- Health checks should return 200 OK
- No error messages in logs

### Weekly Health Check

**Purpose**: Comprehensive system health assessment

**Procedure**:

1. **Resource Usage Check**
   ```bash
   docker stats --no-stream
   free -h
   df -h
   ```

2. **Log Analysis**
   ```bash
   # Check for errors in last 24 hours
   docker-compose -f docker-compose.prod.yml logs --since 24h | grep -i error
   ```

3. **Database Performance**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT * FROM pg_stat_activity;"
   ```

4. **SSL Certificate Check**
   ```bash
   find /etc/ssl -name "*.crt" -exec openssl x509 -in {} -text -noout \; | grep -E "(Not After|Subject:)"
   ```

5. **Backup Verification**
   ```bash
   python3 scripts/backup_database.py list
   ```

## Service Management

### Starting Services

**Purpose**: Start all or specific services

**Procedure**:

1. **Start All Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Start Specific Service**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d service_name
   ```

3. **Verify Startup**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

### Stopping Services

**Purpose**: Gracefully stop services

**Procedure**:

1. **Stop All Services**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Stop Specific Service**
   ```bash
   docker-compose -f docker-compose.prod.yml stop service_name
   ```

3. **Force Stop (Emergency)**
   ```bash
   docker-compose -f docker-compose.prod.yml kill service_name
   ```

### Restarting Services

**Purpose**: Restart services for configuration changes or troubleshooting

**Procedure**:

1. **Restart All Services**
   ```bash
   docker-compose -f docker-compose.prod.yml restart
   ```

2. **Restart Specific Service**
   ```bash
   docker-compose -f docker-compose.prod.yml restart service_name
   ```

3. **Restart with Rebuild**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build service_name
   ```

### Updating Services

**Purpose**: Update services to latest versions

**Procedure**:

1. **Pull Latest Images**
   ```bash
   docker-compose -f docker-compose.prod.yml pull
   ```

2. **Update Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Clean Up Old Images**
   ```bash
   docker image prune -f
   ```

## Database Operations

### Database Backup

**Purpose**: Create database backup

**Procedure**:

1. **Create Backup**
   ```bash
   python3 scripts/backup_database.py backup
   ```

2. **Verify Backup**
   ```bash
   python3 scripts/backup_database.py list
   ```

3. **Check Backup Size**
   ```bash
   ls -lh infrastructure/postgres/backups/
   ```

### Database Restore

**Purpose**: Restore database from backup

**Procedure**:

1. **List Available Backups**
   ```bash
   python3 scripts/backup_database.py list
   ```

2. **Stop Services**
   ```bash
   docker-compose -f docker-compose.prod.yml stop api worker ml_pipeline
   ```

3. **Restore Database**
   ```bash
   python3 scripts/backup_database.py restore --backup-file backup_file.sql.gz
   ```

4. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml start api worker ml_pipeline
   ```

### Database Maintenance

**Purpose**: Perform database maintenance tasks

**Procedure**:

1. **Vacuum Database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "VACUUM ANALYZE;"
   ```

2. **Check Database Size**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT pg_size_pretty(pg_database_size('green_engine'));"
   ```

3. **Check Table Sizes**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
   ```

## MQTT Operations

### MQTT Broker Management

**Purpose**: Manage MQTT broker operations

**Procedure**:

1. **Check Broker Status**
   ```bash
   docker-compose -f docker-compose.prod.yml exec mosquitto mosquitto_pub -h localhost -t test -m "status"
   ```

2. **View Broker Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs mosquitto
   ```

3. **Check Connected Clients**
   ```bash
   docker-compose -f docker-compose.prod.yml exec mosquitto mosquitto_sub -h localhost -t '$SYS/broker/clients/connected' -C 1
   ```

### MQTT Message Testing

**Purpose**: Test MQTT message flow

**Procedure**:

1. **Publish Test Message**
   ```bash
   docker-compose -f docker-compose.prod.yml exec mosquitto mosquitto_pub -h localhost -t "greenengine/test/telemetry" -m '{"device_id":"TEST","timestamp":"2024-01-01T00:00:00Z","readings":{"temperature":25.0}}'
   ```

2. **Subscribe to Messages**
   ```bash
   docker-compose -f docker-compose.prod.yml exec mosquitto mosquitto_sub -h localhost -t "greenengine/+/telemetry" -v
   ```

## Monitoring and Alerting

### Prometheus Management

**Purpose**: Manage Prometheus monitoring

**Procedure**:

1. **Check Prometheus Status**
   ```bash
   curl http://localhost:9090/-/healthy
   ```

2. **View Metrics**
   ```bash
   curl http://localhost:9090/metrics
   ```

3. **Check Targets**
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

### Grafana Management

**Purpose**: Manage Grafana dashboards

**Procedure**:

1. **Access Grafana**
   ```bash
   open http://localhost:3000
   ```

2. **Check Dashboard Status**
   ```bash
   curl -u admin:admin_secure_123 http://localhost:3000/api/health
   ```

3. **Export Dashboard**
   ```bash
   curl -u admin:admin_secure_123 http://localhost:3000/api/dashboards/db/green-engine-overview
   ```

### Alert Management

**Purpose**: Manage system alerts

**Procedure**:

1. **Check Active Alerts**
   ```bash
   curl http://localhost:9090/api/v1/alerts
   ```

2. **View Alert Rules**
   ```bash
   curl http://localhost:9090/api/v1/rules
   ```

3. **Test Alert**
   ```bash
   # Trigger high CPU alert
   stress --cpu 4 --timeout 60s
   ```

## Backup and Recovery

### Automated Backup Setup

**Purpose**: Set up automated backups

**Procedure**:

1. **Create Backup Script**
   ```bash
   cat > /usr/local/bin/green-engine-backup.sh << 'EOF'
   #!/bin/bash
   cd /path/to/green-engine
   python3 scripts/backup_database.py backup
   EOF
   ```

2. **Make Script Executable**
   ```bash
   chmod +x /usr/local/bin/green-engine-backup.sh
   ```

3. **Set Up Cron Job**
   ```bash
   echo "0 2 * * * /usr/local/bin/green-engine-backup.sh" | crontab -
   ```

### Disaster Recovery

**Purpose**: Recover from system failure

**Procedure**:

1. **Assess Damage**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs
   ```

2. **Stop All Services**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

3. **Restore Database**
   ```bash
   python3 scripts/backup_database.py restore --backup-file latest_backup.sql.gz
   ```

4. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Verify Recovery**
   ```bash
   curl http://localhost:8010/health
   curl http://localhost:8501/healthz
   ```

## Security Operations

### Security Audit

**Purpose**: Perform security audit

**Procedure**:

1. **Run Security Script**
   ```bash
   sudo /usr/local/bin/green-engine-security.sh
   ```

2. **Check Firewall Status**
   ```bash
   sudo ufw status
   ```

3. **Check Fail2ban Status**
   ```bash
   sudo fail2ban-client status
   ```

4. **Review Security Logs**
   ```bash
   sudo journalctl -u fail2ban
   sudo tail -f /var/log/auth.log
   ```

### SSL Certificate Management

**Purpose**: Manage SSL certificates

**Procedure**:

1. **Check Certificate Expiry**
   ```bash
   find /etc/ssl -name "*.crt" -exec openssl x509 -in {} -text -noout \; | grep -E "(Not After|Subject:)"
   ```

2. **Renew Certificate**
   ```bash
   # Generate new certificate
   openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt
   ```

3. **Update Certificate**
   ```bash
   # Copy new certificate
   sudo cp new_cert.crt /etc/ssl/certs/
   sudo systemctl reload nginx
   ```

## Performance Tuning

### System Performance

**Purpose**: Optimize system performance

**Procedure**:

1. **Check Resource Usage**
   ```bash
   docker stats --no-stream
   top
   iotop
   ```

2. **Optimize Docker**
   ```bash
   # Clean up unused resources
   docker system prune -f
   docker volume prune -f
   ```

3. **Database Optimization**
   ```bash
   # Analyze query performance
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

### Application Performance

**Purpose**: Optimize application performance

**Procedure**:

1. **Check API Performance**
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8010/health
   ```

2. **Monitor Response Times**
   ```bash
   # Use performance test script
   python3 scripts/performance_test.py --quick
   ```

3. **Optimize Database Queries**
   ```bash
   # Check slow queries
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

## Emergency Procedures

### System Down

**Purpose**: Respond to system failure

**Procedure**:

1. **Assess Situation**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs --tail 100
   ```

2. **Check Resources**
   ```bash
   free -h
   df -h
   top
   ```

3. **Restart Services**
   ```bash
   docker-compose -f docker-compose.prod.yml restart
   ```

4. **Escalate if Needed**
   - Contact system administrator
   - Document incident
   - Follow escalation procedures

### Database Corruption

**Purpose**: Respond to database corruption

**Procedure**:

1. **Stop Services**
   ```bash
   docker-compose -f docker-compose.prod.yml stop api worker ml_pipeline
   ```

2. **Check Database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U green_user -d green_engine -c "SELECT * FROM pg_stat_database;"
   ```

3. **Restore from Backup**
   ```bash
   python3 scripts/backup_database.py restore --backup-file latest_backup.sql.gz
   ```

4. **Verify Recovery**
   ```bash
   docker-compose -f docker-compose.prod.yml start api worker ml_pipeline
   curl http://localhost:8010/health
   ```

### Security Incident

**Purpose**: Respond to security incident

**Procedure**:

1. **Isolate System**
   ```bash
   sudo ufw deny all
   ```

2. **Check Logs**
   ```bash
   sudo journalctl -u fail2ban
   sudo tail -f /var/log/auth.log
   ```

3. **Document Incident**
   - Record timestamp
   - Note symptoms
   - Document actions taken

4. **Contact Security Team**
   - Report incident
   - Provide documentation
   - Follow security procedures

## Maintenance Procedures

### Weekly Maintenance

**Purpose**: Perform weekly maintenance tasks

**Procedure**:

1. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Clean Docker**
   ```bash
   docker system prune -f
   ```

3. **Check Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs --since 7d | grep -i error
   ```

4. **Verify Backups**
   ```bash
   python3 scripts/backup_database.py list
   ```

### Monthly Maintenance

**Purpose**: Perform monthly maintenance tasks

**Procedure**:

1. **Security Audit**
   ```bash
   sudo /usr/local/bin/green-engine-security.sh
   ```

2. **Performance Review**
   ```bash
   python3 scripts/performance_test.py
   ```

3. **Capacity Planning**
   ```bash
   df -h
   free -h
   docker system df
   ```

4. **Documentation Update**
   - Review runbooks
   - Update procedures
   - Document changes

### Quarterly Maintenance

**Purpose**: Perform quarterly maintenance tasks

**Procedure**:

1. **Full System Review**
   - Security assessment
   - Performance analysis
   - Capacity planning

2. **Update Dependencies**
   ```bash
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Disaster Recovery Test**
   - Test backup restoration
   - Verify recovery procedures
   - Document results

4. **Security Updates**
   - Review security patches
   - Update SSL certificates
   - Audit access controls

## Conclusion

These runbooks provide comprehensive procedures for operating and maintaining the Green Engine system. Follow the procedures carefully and document any deviations or issues encountered.

For additional support or clarification, contact the system administration team.
