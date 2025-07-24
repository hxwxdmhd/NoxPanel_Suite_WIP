#!/bin/bash

# NoxPanel Production Deployment Script
# This script automates the deployment process for NoxPanel

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if Git is installed
    if ! command -v git &> /dev/null; then
        warn "Git is not installed. Some features may not work properly."
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found at $ENV_FILE. Please copy .env.example to .env and configure it."
    fi
    
    log "Prerequisites check completed successfully"
}

# Generate secure keys
generate_keys() {
    log "Generating secure keys..."
    
    # Check if keys already exist
    if grep -q "your_ultra_secure" "$ENV_FILE"; then
        warn "Default keys detected in .env file. Generating new secure keys..."
        
        # Generate random keys
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_KEY=$(openssl rand -hex 32)
        CSRF_KEY=$(openssl rand -hex 32)
        DB_PASS=$(openssl rand -hex 16)
        REDIS_PASS=$(openssl rand -hex 16)
        GRAFANA_PASS=$(openssl rand -hex 12)
        
        # Update .env file
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ENV_FILE"
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_KEY/" "$ENV_FILE"
        sed -i "s/CSRF_SECRET_KEY=.*/CSRF_SECRET_KEY=$CSRF_KEY/" "$ENV_FILE"
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASS/" "$ENV_FILE"
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASS/" "$ENV_FILE"
        sed -i "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=$GRAFANA_PASS/" "$ENV_FILE"
        
        log "Secure keys generated and updated in .env file"
    else
        log "Custom keys detected in .env file. Skipping key generation."
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p "$PROJECT_DIR/data/logs"
    mkdir -p "$PROJECT_DIR/data/uploads"
    mkdir -p "$PROJECT_DIR/data/backups"
    mkdir -p "$PROJECT_DIR/security/tokens"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_DIR/monitoring"
    
    # Set proper permissions
    chmod 755 "$PROJECT_DIR/data"
    chmod 755 "$PROJECT_DIR/security"
    chmod 700 "$PROJECT_DIR/security/tokens"
    chmod 755 "$BACKUP_DIR"
    
    log "Directories created successfully"
}

# Create monitoring configuration
create_monitoring_config() {
    log "Creating monitoring configuration..."
    
    # Prometheus configuration
    cat > "$PROJECT_DIR/monitoring/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'noxpanel-backend'
    static_configs:
      - targets: ['backend:5002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'noxpanel-frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/health'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

    # Loki configuration
    cat > "$PROJECT_DIR/monitoring/loki-config.yaml" << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
EOF

    # Promtail configuration
    cat > "$PROJECT_DIR/monitoring/promtail-config.yml" << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[^|]*))\|
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          stream:
          container_name:
      - output:
          source: output
EOF

    log "Monitoring configuration created successfully"
}

# Backup existing data
backup_data() {
    if [[ -d "$PROJECT_DIR/data" ]]; then
        log "Creating backup of existing data..."
        
        BACKUP_NAME="noxpanel-backup-$(date +%Y%m%d-%H%M%S)"
        tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$PROJECT_DIR" data
        
        log "Backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
    fi
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build backend image
    log "Building backend image..."
    docker build -t noxpanel-backend:latest .
    
    # Build frontend image
    log "Building frontend image..."
    docker build -t noxpanel-frontend:latest ./frontend
    
    log "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    cd "$PROJECT_DIR"
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose down --remove-orphans || true
    
    # Start services
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_health
    
    log "Services deployed successfully"
}

# Check service health
check_health() {
    log "Checking service health..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost/health &>/dev/null; then
            log "Frontend is healthy"
            break
        fi
        
        log "Waiting for frontend to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Frontend health check failed after $max_attempts attempts"
    fi
    
    # Check backend health
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T backend curl -f http://localhost:5002/health &>/dev/null; then
            log "Backend is healthy"
            break
        fi
        
        log "Waiting for backend to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Backend health check failed after $max_attempts attempts"
    fi
    
    log "All services are healthy"
}

# Setup SSL certificates (if domain is configured)
setup_ssl() {
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2)
    
    if [[ "$domain" != "noxpanel.example.com" && -n "$domain" ]]; then
        log "Setting up SSL certificates for domain: $domain"
        
        # Let's Encrypt will handle this automatically via Traefik
        log "SSL certificates will be automatically provisioned by Let's Encrypt"
    else
        log "Using self-signed certificates for development"
    fi
}

# Display deployment summary
display_summary() {
    log "Deployment completed successfully!"
    
    echo -e "\n${BLUE}=== DEPLOYMENT SUMMARY ===${NC}"
    echo -e "${GREEN}✓${NC} NoxPanel has been deployed successfully"
    echo -e "${GREEN}✓${NC} All services are running and healthy"
    echo -e "${GREEN}✓${NC} Monitoring stack is configured"
    
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2)
    
    echo -e "\n${BLUE}Access URLs:${NC}"
    if [[ "$domain" != "noxpanel.example.com" && -n "$domain" ]]; then
        echo -e "  • NoxPanel:    https://$domain"
        echo -e "  • Grafana:     https://grafana.$domain"
        echo -e "  • Prometheus:  https://prometheus.$domain"
        echo -e "  • Traefik:     https://traefik.$domain"
    else
        echo -e "  • NoxPanel:    http://localhost"
        echo -e "  • Grafana:     http://localhost:3000"
        echo -e "  • Prometheus:  http://localhost:9090"
        echo -e "  • Traefik:     http://localhost:8080"
    fi
    
    echo -e "\n${BLUE}Default Credentials:${NC}"
    echo -e "  • Admin User: admin"
    echo -e "  • Admin Pass: $(grep "^ADMIN_PASS=" "$ENV_FILE" | cut -d'=' -f2)"
    echo -e "  • Grafana:    admin / $(grep "^GRAFANA_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)"
    
    echo -e "\n${YELLOW}Important:${NC}"
    echo -e "  • Change default passwords in production"
    echo -e "  • Configure proper domain and SSL certificates"
    echo -e "  • Set up regular backups"
    echo -e "  • Review security settings"
    
    echo -e "\n${BLUE}Logs:${NC}"
    echo -e "  • Deployment log: $LOG_FILE"
    echo -e "  • Service logs:   docker-compose logs"
    
    echo -e "\n${BLUE}Management Commands:${NC}"
    echo -e "  • Start:    docker-compose up -d"
    echo -e "  • Stop:     docker-compose down"
    echo -e "  • Logs:     docker-compose logs -f"
    echo -e "  • Update:   ./scripts/deploy.sh"
}

# Main deployment function
main() {
    log "Starting NoxPanel deployment..."
    
    check_root
    check_prerequisites
    generate_keys
    create_directories
    create_monitoring_config
    backup_data
    build_images
    deploy_services
    setup_ssl
    display_summary
    
    log "Deployment process completed successfully!"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "backup")
        backup_data
        ;;
    "health")
        check_health
        ;;
    "logs")
        cd "$PROJECT_DIR"
        docker-compose logs -f
        ;;
    "stop")
        cd "$PROJECT_DIR"
        docker-compose down
        ;;
    "start")
        cd "$PROJECT_DIR"
        docker-compose up -d
        ;;
    "update")
        log "Updating NoxPanel..."
        git pull origin main
        main
        ;;
    *)
        echo "Usage: $0 {deploy|backup|health|logs|stop|start|update}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  backup  - Create data backup"
        echo "  health  - Check service health"
        echo "  logs    - Show service logs"
        echo "  stop    - Stop all services"
        echo "  start   - Start all services"
        echo "  update  - Update and redeploy"
        exit 1
        ;;
esac
