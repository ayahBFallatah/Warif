# Green Engine Deployment Guide

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Development Environment Setup](#development-environment-setup)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Security Configuration](#security-configuration)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup and Recovery](#backup-and-recovery)
10. [Post-Deployment Verification](#post-deployment-verification)

## Deployment Overview

This guide provides comprehensive instructions for deploying the Green Engine IoT platform in various environments, from local development to production cloud deployment.

### Deployment Options

1. **Local Development**: Single-machine setup for development and testing
2. **Docker Deployment**: Containerized deployment for consistent environments
3. **Production Server**: Dedicated server deployment with full monitoring
4. **Cloud Deployment**: Scalable cloud infrastructure deployment

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps connection
- **OS**: Ubuntu 20.04+ or CentOS 8+

#### Recommended Requirements
- **CPU**: 4 cores, 3.0 GHz
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps connection
- **OS**: Ubuntu 22.04 LTS

## Prerequisites

### Software Requirements

#### System Packages
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib \
    mosquitto mosquitto-clients git curl wget unzip

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip postgresql-server postgresql-contrib \
    mosquitto mosquitto-clients git curl wget unzip
```

#### Python Dependencies
```bash
# Core dependencies
pip3 install fastapi uvicorn streamlit psycopg2-binary python-dotenv
pip3 install pandas numpy scikit-learn xgboost prophet joblib
pip3 install paho-mqtt requests prometheus-client
pip3 install python-jose[cryptography] passlib[bcrypt] python-multipart
```

#### Docker (Optional)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Network Requirements

#### Ports to Open
- **8010**: API server (HTTP)
- **8501**: Dashboard (HTTP)
- **5432**: PostgreSQL database
- **1883**: MQTT broker (standard)
- **8883**: MQTT broker (TLS)
- **9090**: Prometheus metrics
- **3000**: Grafana dashboard

#### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 8010/tcp
sudo ufw allow 8501/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 1883/tcp
sudo ufw allow 8883/tcp
sudo ufw allow 9090/tcp
sudo ufw allow 3000/tcp

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=8010/tcp
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --permanent --add-port=1883/tcp
sudo firewall-cmd --permanent --add-port=8883/tcp
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

## Development Environment Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/green-engine.git
cd green-engine
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Environment Variables:**
```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=green_engine
DB_USER=green_user
DB_PASSWORD=green_pass
DB_PORT=5432

# API Configuration
API_HOST=0.0.0.0
API_PORT=8010
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USE_TLS=false
MQTT_CMD_BASE=greenengine

# Security
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ENCRYPTION_KEY=your-encryption-key-here

# Monitoring
WORKER_METRICS_PORT=9101
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Step 4: Database Setup
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE green_engine;
CREATE USER green_user WITH PASSWORD 'green_pass';
GRANT ALL PRIVILEGES ON DATABASE green_engine TO green_user;
\q
EOF

# Run database setup
python3 scripts/setup_db_local.py
```

### Step 5: MQTT Broker Setup
```bash
# Start Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Configure Mosquitto (optional)
sudo nano /etc/mosquitto/mosquitto.conf
```

**Mosquitto Configuration:**
```
listener 1883
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
```

### Step 6: Start Services
```bash
# Terminal 1: API Server
cd /path/to/green-engine
source venv/bin/activate
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload

# Terminal 2: Dashboard
cd /path/to/green-engine/dashboard
source ../venv/bin/activate
python3 -m streamlit run app.py --server.port 8501 --server.address localhost

# Terminal 3: Command Worker (optional)
cd /path/to/green-engine
source venv/bin/activate
python3 src/services/command_worker.py
```

### Step 7: Verify Installation
```bash
# Test API
curl http://localhost:8010/health

# Test Dashboard
curl http://localhost:8501

# Test MQTT
mosquitto_pub -h localhost -t "test/topic" -m "test message"
mosquitto_sub -h localhost -t "test/topic"
```

## Production Deployment

### Step 1: Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib \
    mosquitto mosquitto-clients nginx certbot python3-certbot-nginx \
    fail2ban ufw htop

# Create application user
sudo useradd -m -s /bin/bash greenengine
sudo usermod -aG sudo greenengine
```

### Step 2: Application Deployment
```bash
# Switch to application user
sudo su - greenengine

# Clone repository
git clone https://github.com/your-org/green-engine.git
cd green-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Configure production settings
```

### Step 3: Database Configuration
```bash
# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
```

**PostgreSQL Configuration:**
```
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100
listen_addresses = 'localhost'

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'
log_min_duration_statement = 1000
```

```bash
# Configure authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

**Authentication Configuration:**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

### Step 4: Systemd Service Configuration
```bash
# Create API service
sudo nano /etc/systemd/system/green-engine-api.service
```

**API Service Configuration:**
```ini
[Unit]
Description=Green Engine API Server
After=network.target postgresql.service

[Service]
Type=simple
User=greenengine
Group=greenengine
WorkingDirectory=/home/greenengine/green-engine
Environment=PATH=/home/greenengine/green-engine/venv/bin
ExecStart=/home/greenengine/green-engine/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8010
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create Dashboard service
sudo nano /etc/systemd/system/green-engine-dashboard.service
```

**Dashboard Service Configuration:**
```ini
[Unit]
Description=Green Engine Dashboard
After=network.target green-engine-api.service

[Service]
Type=simple
User=greenengine
Group=greenengine
WorkingDirectory=/home/greenengine/green-engine/dashboard
Environment=PATH=/home/greenengine/green-engine/venv/bin
ExecStart=/home/greenengine/green-engine/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 5: Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/green-engine
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard proxy
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for Streamlit
    location /_stcore/stream {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/green-engine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: SSL Certificate
```bash
# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 7: Start Services
```bash
# Enable and start services
sudo systemctl enable postgresql mosquitto green-engine-api green-engine-dashboard
sudo systemctl start postgresql mosquitto green-engine-api green-engine-dashboard

# Check status
sudo systemctl status green-engine-api
sudo systemctl status green-engine-dashboard
```

## Docker Deployment

### Step 1: Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: green_engine
      POSTGRES_USER: green_user
      POSTGRES_PASSWORD: green_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped

  mosquitto:
    image: eclipse-mosquitto:2.0
    volumes:
      - ./infrastructure/mosquitto/config:/mosquitto/config:ro
      - ./infrastructure/mosquitto/data:/mosquitto/data
      - ./infrastructure/mosquitto/logs:/mosquitto/logs
    ports:
      - "1883:1883"
      - "8883:8883"
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - DB_HOST=postgres
      - DB_NAME=green_engine
      - DB_USER=green_user
      - DB_PASSWORD=green_pass
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8010:8010"
    depends_on:
      - postgres
      - mosquitto
    restart: unless-stopped

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    environment:
      - API_BASE_URL=http://api:8010
    ports:
      - "8501:8501"
    depends_on:
      - api
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DB_HOST=postgres
      - MQTT_BROKER_HOST=mosquitto
    depends_on:
      - postgres
      - mosquitto
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infrastructure/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

### Step 2: Build and Deploy
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Cloud Deployment

### AWS Deployment

#### Step 1: EC2 Instance Setup
```bash
# Launch EC2 instance (t3.medium or larger)
# Security group: Allow ports 22, 80, 443, 8010, 8501, 5432, 1883, 8883

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

#### Step 2: RDS Database Setup
```bash
# Create RDS PostgreSQL instance
# Engine: PostgreSQL 15
# Instance class: db.t3.micro
# Storage: 20 GB
# Security group: Allow port 5432 from EC2 security group
```

#### Step 3: Application Deployment
```bash
# Clone repository
git clone https://github.com/your-org/green-engine.git
cd green-engine

# Configure environment for RDS
nano .env
# Update DB_HOST to RDS endpoint
# Update other production settings

# Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Google Cloud Platform Deployment

#### Step 1: Compute Engine Setup
```bash
# Create VM instance
gcloud compute instances create green-engine \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium \
    --zone=us-central1-a

# Configure firewall
gcloud compute firewall-rules create allow-green-engine \
    --allow tcp:8010,tcp:8501,tcp:1883,tcp:8883 \
    --source-ranges 0.0.0.0/0
```

#### Step 2: Cloud SQL Setup
```bash
# Create Cloud SQL instance
gcloud sql instances create green-engine-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

### Azure Deployment

#### Step 1: Virtual Machine Setup
```bash
# Create VM
az vm create \
    --resource-group green-engine-rg \
    --name green-engine-vm \
    --image UbuntuLTS \
    --size Standard_B2s \
    --admin-username azureuser \
    --generate-ssh-keys
```

#### Step 2: Database Setup
```bash
# Create PostgreSQL database
az postgres server create \
    --resource-group green-engine-rg \
    --name green-engine-db \
    --location eastus \
    --admin-user greenuser \
    --admin-password YourPassword123! \
    --sku-name GP_Gen5_2
```

## Security Configuration

### SSL/TLS Configuration
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure Nginx for SSL
sudo nano /etc/nginx/sites-available/green-engine
```

**SSL Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard proxy
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 1883/tcp
sudo ufw allow 8883/tcp
sudo ufw enable
```

### Fail2ban Configuration
```bash
# Configure Fail2ban
sudo nano /etc/fail2ban/jail.local
```

**Fail2ban Configuration:**
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'green-engine-api'
    static_configs:
      - targets: ['api:8010']
    metrics_path: '/metrics'

  - job_name: 'green-engine-worker'
    static_configs:
      - targets: ['worker:9101']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'mosquitto'
    static_configs:
      - targets: ['mosquitto:1883']
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Green Engine Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(green_engine_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{datname}}"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup-green-engine.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/green-engine"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="green_engine"
DB_USER="green_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/green_engine_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "green_engine_*.sql.gz" -mtime +7 -delete

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_DIR/green_engine_$DATE.sql.gz s3://your-backup-bucket/
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-green-engine.sh

# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-green-engine.sh
```

### Application Backup
```bash
# Create application backup script
sudo nano /usr/local/bin/backup-app.sh
```

**Application Backup Script:**
```bash
#!/bin/bash
APP_DIR="/home/greenengine/green-engine"
BACKUP_DIR="/backups/green-engine/app"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create application backup
tar -czf $BACKUP_DIR/green_engine_app_$DATE.tar.gz -C $APP_DIR .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "green_engine_app_*.tar.gz" -mtime +7 -delete
```

### Recovery Procedures
```bash
# Database recovery
gunzip -c /backups/green-engine/green_engine_20240115_020000.sql.gz | psql -h localhost -U green_user -d green_engine

# Application recovery
tar -xzf /backups/green-engine/app/green_engine_app_20240115_020000.tar.gz -C /home/greenengine/green-engine/
```

## Post-Deployment Verification

### Health Checks
```bash
# API health check
curl -f http://localhost:8010/health || echo "API health check failed"

# Dashboard health check
curl -f http://localhost:8501 || echo "Dashboard health check failed"

# Database health check
pg_isready -h localhost -p 5432 || echo "Database health check failed"

# MQTT health check
mosquitto_pub -h localhost -t "health/check" -m "test" || echo "MQTT health check failed"
```

### Performance Testing
```bash
# API performance test
ab -n 1000 -c 10 http://localhost:8010/health

# Database performance test
pgbench -h localhost -U green_user -d green_engine -c 10 -j 2 -T 60
```

### Security Testing
```bash
# SSL/TLS test
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Port scan
nmap -sS -O your-domain.com

# Security headers test
curl -I https://your-domain.com
```

### Monitoring Verification
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana
curl http://localhost:3000/api/health

# Check logs
sudo journalctl -u green-engine-api -f
sudo journalctl -u green-engine-dashboard -f
```

## Troubleshooting Deployment Issues

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status green-engine-api
sudo systemctl status green-engine-dashboard

# Check logs
sudo journalctl -u green-engine-api -n 50
sudo journalctl -u green-engine-dashboard -n 50

# Check configuration
sudo systemctl daemon-reload
```

#### Database Connection Issues
```bash
# Test database connection
psql -h localhost -U green_user -d green_engine -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tlnp | grep :8010
sudo netstat -tlnp | grep :8501

# Kill conflicting processes
sudo kill -9 $(lsof -t -i:8010)
sudo kill -9 $(lsof -t -i:8501)
```

### Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check database performance
sudo -u postgres psql -d green_engine -c "SELECT * FROM pg_stat_activity;"

# Check application logs for errors
tail -f /var/log/green-engine/api.log | grep ERROR
```

---

*For additional deployment support, contact the system administrator or refer to the troubleshooting guide.*