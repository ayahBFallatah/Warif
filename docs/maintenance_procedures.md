# Green Engine Maintenance Procedures

## Table of Contents

1. [Maintenance Overview](#maintenance-overview)
2. [Daily Maintenance Tasks](#daily-maintenance-tasks)
3. [Weekly Maintenance Tasks](#weekly-maintenance-tasks)
4. [Monthly Maintenance Tasks](#monthly-maintenance-tasks)
5. [Quarterly Maintenance Tasks](#quarterly-maintenance-tasks)
6. [Annual Maintenance Tasks](#annual-maintenance-tasks)
7. [Emergency Maintenance](#emergency-maintenance)
8. [Performance Optimization](#performance-optimization)
9. [Security Maintenance](#security-maintenance)
10. [Backup and Recovery Procedures](#backup-and-recovery-procedures)

## Maintenance Overview

### Maintenance Philosophy

The Green Engine system requires regular maintenance to ensure optimal performance, security, and reliability. This document provides comprehensive maintenance procedures organized by frequency and priority.

### Maintenance Categories

1. **Preventive Maintenance**: Regular tasks to prevent issues
2. **Corrective Maintenance**: Tasks to fix identified problems
3. **Adaptive Maintenance**: Tasks to improve system performance
4. **Perfective Maintenance**: Tasks to enhance system capabilities

### Maintenance Responsibilities

- **System Administrator**: Overall system maintenance and coordination
- **Database Administrator**: Database maintenance and optimization
- **Network Administrator**: Network and security maintenance
- **Application Administrator**: Application and service maintenance

## Daily Maintenance Tasks

### System Health Checks

#### 1. Service Status Verification
```bash
#!/bin/bash
# Daily health check script

echo "=== Green Engine Daily Health Check ==="
echo "Date: $(date)"
echo

# Check API service
if systemctl is-active --quiet green-engine-api; then
    echo "✅ API Service: Running"
else
    echo "❌ API Service: Not running"
    systemctl status green-engine-api
fi

# Check Dashboard service
if systemctl is-active --quiet green-engine-dashboard; then
    echo "✅ Dashboard Service: Running"
else
    echo "❌ Dashboard Service: Not running"
    systemctl status green-engine-dashboard
fi

# Check Database service
if systemctl is-active --quiet postgresql; then
    echo "✅ Database Service: Running"
else
    echo "❌ Database Service: Not running"
    systemctl status postgresql
fi

# Check MQTT service
if systemctl is-active --quiet mosquitto; then
    echo "✅ MQTT Service: Running"
else
    echo "❌ MQTT Service: Not running"
    systemctl status mosquitto
fi

echo
```

#### 2. Disk Space Monitoring
```bash
#!/bin/bash
# Disk space check

echo "=== Disk Space Check ==="
df -h | grep -E "(Filesystem|/dev/)"

# Check for low disk space (< 20%)
df -h | awk 'NR>1 {gsub(/%/, "", $5); if($5 > 80) print "⚠️  Low disk space: " $0}'
```

#### 3. Memory Usage Check
```bash
#!/bin/bash
# Memory usage check

echo "=== Memory Usage Check ==="
free -h

# Check for high memory usage (> 90%)
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "⚠️  High memory usage: ${MEMORY_USAGE}%"
fi
```

#### 4. Database Health Check
```bash
#!/bin/bash
# Database health check

echo "=== Database Health Check ==="

# Check database connectivity
if pg_isready -h localhost -p 5432; then
    echo "✅ Database: Accessible"
else
    echo "❌ Database: Not accessible"
    exit 1
fi

# Check active connections
ACTIVE_CONNECTIONS=$(psql -h localhost -U green_user -d green_engine -t -c "SELECT count(*) FROM pg_stat_activity;")
echo "Active connections: $ACTIVE_CONNECTIONS"

# Check for long-running queries
LONG_QUERIES=$(psql -h localhost -U green_user -d green_engine -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';")
if [ $LONG_QUERIES -gt 0 ]; then
    echo "⚠️  Long-running queries detected: $LONG_QUERIES"
fi
```

#### 5. Application Log Review
```bash
#!/bin/bash
# Application log review

echo "=== Application Log Review ==="

# Check for errors in API logs
API_ERRORS=$(journalctl -u green-engine-api --since "1 day ago" | grep -i error | wc -l)
echo "API errors in last 24h: $API_ERRORS"

# Check for errors in Dashboard logs
DASHBOARD_ERRORS=$(journalctl -u green-engine-dashboard --since "1 day ago" | grep -i error | wc -l)
echo "Dashboard errors in last 24h: $DASHBOARD_ERRORS"

# Check for critical errors
CRITICAL_ERRORS=$(journalctl -u green-engine-api --since "1 day ago" | grep -i "critical\|fatal" | wc -l)
if [ $CRITICAL_ERRORS -gt 0 ]; then
    echo "🚨 Critical errors detected: $CRITICAL_ERRORS"
    journalctl -u green-engine-api --since "1 day ago" | grep -i "critical\|fatal"
fi
```

### Automated Daily Tasks

#### 1. Log Rotation
```bash
#!/bin/bash
# Log rotation script

# Rotate application logs
logrotate /etc/logrotate.d/green-engine

# Clean old log files (keep 30 days)
find /var/log/green-engine -name "*.log" -mtime +30 -delete
find /var/log/mosquitto -name "*.log" -mtime +30 -delete
```

#### 2. Database Maintenance
```bash
#!/bin/bash
# Daily database maintenance

# Update table statistics
psql -h localhost -U green_user -d green_engine -c "ANALYZE;"

# Check for table bloat
psql -h localhost -U green_user -d green_engine -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

#### 3. Security Monitoring
```bash
#!/bin/bash
# Daily security check

# Check for failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | grep "$(date +%b\ %d)" | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "⚠️  High number of failed login attempts: $FAILED_LOGINS"
fi

# Check for suspicious activity
SUSPICIOUS_ACTIVITY=$(grep -i "suspicious\|attack\|intrusion" /var/log/auth.log | grep "$(date +%b\ %d)" | wc -l)
if [ $SUSPICIOUS_ACTIVITY -gt 0 ]; then
    echo "🚨 Suspicious activity detected: $SUSPICIOUS_ACTIVITY"
fi
```

## Weekly Maintenance Tasks

### 1. System Updates
```bash
#!/bin/bash
# Weekly system updates

echo "=== Weekly System Updates ==="

# Update package lists
apt update

# Check for available updates
UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
echo "Available updates: $UPDATES"

# Update security packages only (non-disruptive)
apt upgrade -y --only-upgrade-security

# Update Python packages
pip3 list --outdated
```

### 2. Database Optimization
```bash
#!/bin/bash
# Weekly database optimization

echo "=== Weekly Database Optimization ==="

# Vacuum analyze all tables
psql -h localhost -U green_user -d green_engine -c "VACUUM ANALYZE;"

# Check for unused indexes
psql -h localhost -U green_user -d green_engine -c "
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE idx_tup_read = 0 AND idx_tup_fetch = 0;"

# Check for table bloat
psql -h localhost -U green_user -d green_engine -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
       pg_stat_get_tuples_returned(c.oid) as tuples_returned,
       pg_stat_get_tuples_fetched(c.oid) as tuples_fetched
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
ORDER BY pg_total_relation_size(c.oid) DESC;"
```

### 3. Performance Monitoring
```bash
#!/bin/bash
# Weekly performance monitoring

echo "=== Weekly Performance Monitoring ==="

# Check system load
uptime

# Check disk I/O
iostat -x 1 5

# Check network statistics
netstat -i

# Check database performance
psql -h localhost -U green_user -d green_engine -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

### 4. Security Updates
```bash
#!/bin/bash
# Weekly security updates

echo "=== Weekly Security Updates ==="

# Check for security updates
apt list --upgradable | grep -i security

# Update fail2ban rules
fail2ban-client status

# Check SSL certificate expiration
openssl x509 -in /etc/ssl/certs/your-domain.crt -noout -dates

# Review security logs
grep -i "failed\|denied\|blocked" /var/log/auth.log | tail -20
```

### 5. Backup Verification
```bash
#!/bin/bash
# Weekly backup verification

echo "=== Weekly Backup Verification ==="

# Check backup file integrity
BACKUP_FILE=$(ls -t /backups/green-engine/green_engine_*.sql.gz | head -1)
if [ -f "$BACKUP_FILE" ]; then
    echo "Latest backup: $BACKUP_FILE"
    echo "Backup size: $(du -h $BACKUP_FILE | cut -f1)"
    echo "Backup age: $(stat -c %y $BACKUP_FILE)"
    
    # Test backup restoration (dry run)
    echo "Testing backup integrity..."
    gunzip -t $BACKUP_FILE
    if [ $? -eq 0 ]; then
        echo "✅ Backup integrity: OK"
    else
        echo "❌ Backup integrity: FAILED"
    fi
else
    echo "❌ No backup files found"
fi
```

## Monthly Maintenance Tasks

### 1. Comprehensive System Review
```bash
#!/bin/bash
# Monthly system review

echo "=== Monthly System Review ==="

# System information
echo "System Information:"
uname -a
lsb_release -a

# Hardware information
echo "Hardware Information:"
lscpu
free -h
df -h

# Service status
echo "Service Status:"
systemctl list-units --type=service --state=running | grep green-engine
systemctl list-units --type=service --state=running | grep postgresql
systemctl list-units --type=service --state=running | grep mosquitto
```

### 2. Database Deep Maintenance
```bash
#!/bin/bash
# Monthly database deep maintenance

echo "=== Monthly Database Deep Maintenance ==="

# Full vacuum (requires exclusive lock)
echo "Performing full vacuum..."
psql -h localhost -U green_user -d green_engine -c "VACUUM FULL;"

# Reindex all tables
echo "Reindexing all tables..."
psql -h localhost -U green_user -d green_engine -c "REINDEX DATABASE green_engine;"

# Update table statistics
echo "Updating table statistics..."
psql -h localhost -U green_user -d green_engine -c "ANALYZE;"

# Check for table corruption
echo "Checking for table corruption..."
psql -h localhost -U green_user -d green_engine -c "
SELECT datname, datconnlimit, datallowconn, datlastsysoid, datfrozenxid
FROM pg_database WHERE datname = 'green_engine';"
```

### 3. Security Audit
```bash
#!/bin/bash
# Monthly security audit

echo "=== Monthly Security Audit ==="

# Check user accounts
echo "User accounts:"
cut -d: -f1 /etc/passwd | grep -E "(green|postgres|mosquitto)"

# Check sudo privileges
echo "Sudo privileges:"
grep -E "(green|postgres|mosquitto)" /etc/sudoers

# Check file permissions
echo "Critical file permissions:"
ls -la /home/greenengine/green-engine/
ls -la /etc/postgresql/
ls -la /etc/mosquitto/

# Check SSL certificates
echo "SSL certificate status:"
openssl x509 -in /etc/ssl/certs/your-domain.crt -noout -dates

# Review security logs
echo "Security events in last 30 days:"
grep -i "failed\|denied\|blocked\|attack" /var/log/auth.log | wc -l
```

### 4. Performance Analysis
```bash
#!/bin/bash
# Monthly performance analysis

echo "=== Monthly Performance Analysis ==="

# System performance trends
echo "System load trends:"
uptime
iostat -x 1 1

# Database performance analysis
echo "Database performance analysis:"
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables 
ORDER BY seq_tup_read DESC;"

# Application performance
echo "Application performance:"
journalctl -u green-engine-api --since "30 days ago" | grep -i "slow\|timeout\|error" | wc -l
```

### 5. Capacity Planning
```bash
#!/bin/bash
# Monthly capacity planning

echo "=== Monthly Capacity Planning ==="

# Disk usage trends
echo "Disk usage trends:"
df -h
du -sh /var/lib/postgresql/
du -sh /var/log/
du -sh /backups/

# Database size trends
echo "Database size trends:"
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Growth projections
echo "Growth projections:"
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    COUNT(*) as total_records,
    MIN(timestamp) as oldest_record,
    MAX(timestamp) as newest_record
FROM sensor_readings;"
```

## Quarterly Maintenance Tasks

### 1. System Upgrade Planning
```bash
#!/bin/bash
# Quarterly system upgrade planning

echo "=== Quarterly System Upgrade Planning ==="

# Check for major updates
echo "Available major updates:"
apt list --upgradable

# Check Python package updates
echo "Python package updates:"
pip3 list --outdated

# Check for deprecated packages
echo "Deprecated packages:"
apt list --installed | grep -i "deprecated\|obsolete"
```

### 2. Security Hardening Review
```bash
#!/bin/bash
# Quarterly security hardening review

echo "=== Quarterly Security Hardening Review ==="

# Review firewall rules
echo "Firewall rules:"
ufw status verbose

# Review fail2ban configuration
echo "Fail2ban configuration:"
fail2ban-client status

# Review SSL/TLS configuration
echo "SSL/TLS configuration:"
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -noout -text

# Review user permissions
echo "User permissions:"
getent passwd | grep -E "(green|postgres|mosquitto)"
```

### 3. Disaster Recovery Testing
```bash
#!/bin/bash
# Quarterly disaster recovery testing

echo "=== Quarterly Disaster Recovery Testing ==="

# Test backup restoration
echo "Testing backup restoration..."
BACKUP_FILE=$(ls -t /backups/green-engine/green_engine_*.sql.gz | head -1)
TEST_DB="green_engine_test"

# Create test database
psql -h localhost -U postgres -c "CREATE DATABASE $TEST_DB;"

# Restore backup to test database
gunzip -c $BACKUP_FILE | psql -h localhost -U postgres -d $TEST_DB

# Verify restoration
psql -h localhost -U postgres -d $TEST_DB -c "SELECT COUNT(*) FROM sensor_readings;"

# Clean up test database
psql -h localhost -U postgres -c "DROP DATABASE $TEST_DB;"

echo "✅ Disaster recovery test completed"
```

### 4. Performance Optimization
```bash
#!/bin/bash
# Quarterly performance optimization

echo "=== Quarterly Performance Optimization ==="

# Analyze query performance
echo "Query performance analysis:"
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    query,
    mean_time,
    calls,
    total_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 20;"

# Check for missing indexes
echo "Missing indexes analysis:"
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
AND n_distinct > 100 
AND correlation < 0.1;"
```

## Annual Maintenance Tasks

### 1. Complete System Overhaul
```bash
#!/bin/bash
# Annual complete system overhaul

echo "=== Annual Complete System Overhaul ==="

# System information
echo "System Information:"
uname -a
lsb_release -a
lscpu
free -h
df -h

# Service status
echo "Service Status:"
systemctl list-units --type=service --state=running

# Configuration review
echo "Configuration Review:"
echo "PostgreSQL configuration:"
psql -h localhost -U green_user -d green_engine -c "SHOW ALL;"

echo "Mosquitto configuration:"
cat /etc/mosquitto/mosquitto.conf

echo "Nginx configuration:"
nginx -T
```

### 2. Security Audit and Penetration Testing
```bash
#!/bin/bash
# Annual security audit

echo "=== Annual Security Audit ==="

# Port scan
echo "Port scan:"
nmap -sS -O localhost

# Service enumeration
echo "Service enumeration:"
nmap -sV localhost

# Vulnerability assessment
echo "Vulnerability assessment:"
apt list --upgradable | grep -i security

# Review security logs
echo "Security events in last year:"
grep -i "failed\|denied\|blocked\|attack" /var/log/auth.log | wc -l
```

### 3. Documentation Update
```bash
#!/bin/bash
# Annual documentation update

echo "=== Annual Documentation Update ==="

# Update system documentation
echo "Updating system documentation..."

# Check for configuration changes
echo "Configuration changes:"
git log --oneline --since="1 year ago" -- config/

# Update runbooks
echo "Updating runbooks..."

# Review and update procedures
echo "Reviewing and updating procedures..."
```

## Emergency Maintenance

### 1. System Recovery Procedures
```bash
#!/bin/bash
# Emergency system recovery

echo "=== Emergency System Recovery ==="

# Stop all services
echo "Stopping all services..."
systemctl stop green-engine-api
systemctl stop green-engine-dashboard
systemctl stop postgresql
systemctl stop mosquitto

# Check system resources
echo "Checking system resources..."
df -h
free -h
uptime

# Check for disk errors
echo "Checking for disk errors..."
dmesg | grep -i error
dmesg | grep -i "i/o error"

# Check for memory issues
echo "Checking for memory issues..."
dmesg | grep -i "out of memory"
dmesg | grep -i "oom"

# Restart services in order
echo "Restarting services..."
systemctl start postgresql
sleep 10
systemctl start mosquitto
sleep 5
systemctl start green-engine-api
sleep 5
systemctl start green-engine-dashboard
```

### 2. Database Recovery
```bash
#!/bin/bash
# Emergency database recovery

echo "=== Emergency Database Recovery ==="

# Check database status
echo "Checking database status..."
systemctl status postgresql

# Check database connectivity
echo "Checking database connectivity..."
pg_isready -h localhost -p 5432

# Check for corruption
echo "Checking for database corruption..."
psql -h localhost -U postgres -c "SELECT datname, datconnlimit, datallowconn FROM pg_database WHERE datname = 'green_engine';"

# Restore from backup if needed
echo "Restoring from backup if needed..."
BACKUP_FILE=$(ls -t /backups/green-engine/green_engine_*.sql.gz | head -1)
if [ -f "$BACKUP_FILE" ]; then
    echo "Restoring from: $BACKUP_FILE"
    gunzip -c $BACKUP_FILE | psql -h localhost -U postgres -d green_engine
fi
```

### 3. Application Recovery
```bash
#!/bin/bash
# Emergency application recovery

echo "=== Emergency Application Recovery ==="

# Check application status
echo "Checking application status..."
systemctl status green-engine-api
systemctl status green-engine-dashboard

# Check application logs
echo "Checking application logs..."
journalctl -u green-engine-api -n 50
journalctl -u green-engine-dashboard -n 50

# Restart applications
echo "Restarting applications..."
systemctl restart green-engine-api
systemctl restart green-engine-dashboard

# Check application health
echo "Checking application health..."
curl -f http://localhost:8010/health
curl -f http://localhost:8501
```

## Performance Optimization

### 1. Database Optimization
```bash
#!/bin/bash
# Database performance optimization

echo "=== Database Performance Optimization ==="

# Analyze query performance
echo "Analyzing query performance..."
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check for missing indexes
echo "Checking for missing indexes..."
psql -h localhost -U green_user -d green_engine -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
AND n_distinct > 100 
AND correlation < 0.1;"

# Optimize table statistics
echo "Optimizing table statistics..."
psql -h localhost -U green_user -d green_engine -c "ANALYZE;"
```

### 2. System Optimization
```bash
#!/bin/bash
# System performance optimization

echo "=== System Performance Optimization ==="

# Check system load
echo "System load:"
uptime

# Check disk I/O
echo "Disk I/O:"
iostat -x 1 5

# Check memory usage
echo "Memory usage:"
free -h

# Check network statistics
echo "Network statistics:"
netstat -i

# Optimize system parameters
echo "Optimizing system parameters..."
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
sysctl -p
```

## Security Maintenance

### 1. Security Updates
```bash
#!/bin/bash
# Security updates

echo "=== Security Updates ==="

# Update security packages
echo "Updating security packages..."
apt update
apt upgrade -y --only-upgrade-security

# Update Python packages
echo "Updating Python packages..."
pip3 list --outdated
pip3 install --upgrade package_name

# Update SSL certificates
echo "Updating SSL certificates..."
certbot renew --dry-run
```

### 2. Security Monitoring
```bash
#!/bin/bash
# Security monitoring

echo "=== Security Monitoring ==="

# Check for failed login attempts
echo "Failed login attempts:"
grep "Failed password" /var/log/auth.log | tail -20

# Check for suspicious activity
echo "Suspicious activity:"
grep -i "suspicious\|attack\|intrusion" /var/log/auth.log | tail -20

# Check firewall status
echo "Firewall status:"
ufw status verbose

# Check fail2ban status
echo "Fail2ban status:"
fail2ban-client status
```

## Backup and Recovery Procedures

### 1. Backup Procedures
```bash
#!/bin/bash
# Backup procedures

echo "=== Backup Procedures ==="

# Database backup
echo "Creating database backup..."
pg_dump -h localhost -U green_user -d green_engine | gzip > /backups/green-engine/green_engine_$(date +%Y%m%d_%H%M%S).sql.gz

# Application backup
echo "Creating application backup..."
tar -czf /backups/green-engine/app/green_engine_app_$(date +%Y%m%d_%H%M%S).tar.gz -C /home/greenengine/green-engine .

# Configuration backup
echo "Creating configuration backup..."
tar -czf /backups/green-engine/config/green_engine_config_$(date +%Y%m%d_%H%M%S).tar.gz -C /etc postgresql mosquitto nginx
```

### 2. Recovery Procedures
```bash
#!/bin/bash
# Recovery procedures

echo "=== Recovery Procedures ==="

# Database recovery
echo "Database recovery..."
BACKUP_FILE=$(ls -t /backups/green-engine/green_engine_*.sql.gz | head -1)
gunzip -c $BACKUP_FILE | psql -h localhost -U green_user -d green_engine

# Application recovery
echo "Application recovery..."
APP_BACKUP=$(ls -t /backups/green-engine/app/green_engine_app_*.tar.gz | head -1)
tar -xzf $APP_BACKUP -C /home/greenengine/green-engine/

# Configuration recovery
echo "Configuration recovery..."
CONFIG_BACKUP=$(ls -t /backups/green-engine/config/green_engine_config_*.tar.gz | head -1)
tar -xzf $CONFIG_BACKUP -C /etc/
```

---

*For additional maintenance support, contact the system administrator or refer to the troubleshooting guide.*
