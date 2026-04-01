#!/bin/bash

# Green Engine Production Deployment Script
# This script deploys the Green Engine system to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="green_engine"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env file not found. Creating from template..."
        if [ -f "env.production" ]; then
            cp env.production .env
            log_warning "Please update the .env file with your production values before continuing."
            exit 1
        else
            log_error "No environment template found. Please create a .env file."
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    # Create infrastructure directories
    mkdir -p infrastructure/postgres/backups
    mkdir -p infrastructure/postgres/init
    mkdir -p infrastructure/mosquitto/config
    mkdir -p infrastructure/mosquitto/data
    mkdir -p infrastructure/mosquitto/logs
    mkdir -p infrastructure/mosquitto/certs
    mkdir -p infrastructure/monitoring/prometheus/rules
    mkdir -p infrastructure/monitoring/grafana/datasources
    mkdir -p infrastructure/monitoring/grafana/dashboards
    
    # Create application directories
    mkdir -p data/models
    mkdir -p data/processed
    mkdir -p logs
    
    log_success "Directories created"
}

generate_ssl_certificates() {
    log_info "Generating SSL certificates for MQTT..."
    
    CERT_DIR="infrastructure/mosquitto/certs"
    
    if [ ! -f "$CERT_DIR/ca.crt" ]; then
        # Generate CA
        openssl genrsa -out "$CERT_DIR/ca.key" 4096
        openssl req -x509 -new -nodes -key "$CERT_DIR/ca.key" -sha256 -days 3650 -out "$CERT_DIR/ca.crt" -subj "/CN=GreenEngine CA"
        
        # Generate server certificate
        openssl genrsa -out "$CERT_DIR/server.key" 4096
        openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" -subj "/CN=mosquitto.local"
        openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/server.crt" -days 365 -sha256
        
        # Generate device certificates
        for device in "GH-A1-DEV-01" "GH-A1-DEV-02" "GH-B1-DEV-01"; do
            openssl genrsa -out "$CERT_DIR/${device}.key" 2048
            openssl req -new -key "$CERT_DIR/${device}.key" -out "$CERT_DIR/${device}.csr" -subj "/CN=${device}"
            openssl x509 -req -in "$CERT_DIR/${device}.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/${device}.crt" -days 365 -sha256
        done
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

setup_mosquitto_config() {
    log_info "Setting up Mosquitto configuration..."
    
    cat > infrastructure/mosquitto/config/mosquitto.conf << EOF
# Mosquitto Configuration for Green Engine

# General settings
pid_file /var/run/mosquitto.pid
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/logs/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Network settings
listener 1883
allow_anonymous true

# TLS settings
listener 8883
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
require_certificate true
use_identity_as_username true

# WebSocket
listener 9001
protocol websockets

# Access control
acl_file /mosquitto/config/acl.conf
EOF

    cat > infrastructure/mosquitto/config/acl.conf << EOF
# Access Control List for Green Engine

# Allow all users to read from telemetry topics
topic read greenengine/+/telemetry

# Allow all users to write to telemetry topics
topic write greenengine/+/telemetry

# Allow all users to read from command topics
topic read greenengine/+/cmd

# Allow all users to write to command topics
topic write greenengine/+/cmd

# Allow all users to read from status topics
topic read greenengine/+/status

# Allow all users to write to status topics
topic write greenengine/+/status
EOF

    log_success "Mosquitto configuration created"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build all images
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    log_success "Docker images built"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services deployed"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for database..."
    timeout 60 bash -c 'until docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U green_user -d green_engine; do sleep 2; done'
    
    # Wait for API
    log_info "Waiting for API..."
    timeout 60 bash -c 'until curl -f http://localhost:8010/health; do sleep 2; done'
    
    # Wait for dashboard
    log_info "Waiting for dashboard..."
    timeout 60 bash -c 'until curl -f http://localhost:8501/healthz; do sleep 2; done'
    
    log_success "All services are ready"
}

setup_database() {
    log_info "Setting up database..."
    
    # Run database setup
    docker-compose -f "$COMPOSE_FILE" exec postgres psql -U green_user -d green_engine -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
    
    # Run database initialization
    if [ -f "scripts/setup_db.py" ]; then
        docker-compose -f "$COMPOSE_FILE" exec api python3 scripts/setup_db.py
    fi
    
    # Populate sample data
    if [ -f "scripts/populate_sample_data.py" ]; then
        docker-compose -f "$COMPOSE_FILE" exec api python3 scripts/populate_sample_data.py
    fi
    
    log_success "Database setup completed"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Check API health
    if curl -f http://localhost:8010/health > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check dashboard health
    if curl -f http://localhost:8501/healthz > /dev/null 2>&1; then
        log_success "Dashboard health check passed"
    else
        log_error "Dashboard health check failed"
        return 1
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_success "Prometheus health check passed"
    else
        log_error "Prometheus health check failed"
        return 1
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        log_success "Grafana health check passed"
    else
        log_error "Grafana health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

show_deployment_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "🌐 Service URLs:"
    echo "  • API: http://localhost:8010"
    echo "  • Dashboard: http://localhost:8501"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000 (admin/admin_secure_123)"
    echo "  • Traefik Dashboard: http://localhost:8080"
    echo
    echo "📊 Monitoring:"
    echo "  • Prometheus metrics: http://localhost:9090/metrics"
    echo "  • Grafana dashboards: http://localhost:3000"
    echo
    echo "🔧 Management:"
    echo "  • View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  • Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  • Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo
    echo "📋 Next steps:"
    echo "  1. Update your DNS to point to this server"
    echo "  2. Configure SSL certificates for production"
    echo "  3. Set up monitoring alerts"
    echo "  4. Configure backup schedules"
    echo "  5. Review security settings"
}

# Main deployment function
main() {
    log_info "Starting Green Engine production deployment..."
    
    check_prerequisites
    create_directories
    generate_ssl_certificates
    setup_mosquitto_config
    build_images
    deploy_services
    wait_for_services
    setup_database
    run_health_checks
    show_deployment_info
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"
