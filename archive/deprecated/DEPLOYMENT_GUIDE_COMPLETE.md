# Heimnetz Enterprise Suite - Complete Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the complete Heimnetz Enterprise Suite, including AetherCore MSP Server, ContextForge MCP Server, and all integrated services.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **Memory**: Minimum 8GB RAM, Recommended 16GB+
- **Storage**: Minimum 20GB free space
- **CPU**: Multi-core processor (4+ cores recommended)
- **GPU**: Optional CUDA-compatible GPU for AI acceleration

### Software Dependencies
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: Version 3.8+
- **Git**: For source code management
- **Node.js**: Version 16+ (for web interface)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-org/heimnetz-enterprise.git
cd heimnetz-enterprise
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Docker Setup
```bash
# Build Docker images
docker-compose build

# Create networks and volumes
docker-compose up --no-start
```

## Configuration

### Environment Variables (.env)
```env
# Core Configuration
HEIMNETZ_ENV=production
HEIMNETZ_DEBUG=false
HEIMNETZ_HOST=0.0.0.0
HEIMNETZ_SECRET_KEY=your-secret-key-here

# AetherCore Configuration
AETHERCORE_HOST=0.0.0.0
AETHERCORE_PORT=8001
AETHERCORE_WORKERS=4
AETHERCORE_LOG_LEVEL=INFO
AETHERCORE_GPU_ENABLED=auto
AETHERCORE_MODEL_CACHE_SIZE=2GB

# ContextForge Configuration
CONTEXTFORGE_HOST=0.0.0.0
CONTEXTFORGE_PORT=8000
CONTEXTFORGE_WORKERS=2
CONTEXTFORGE_LOG_LEVEL=INFO
CONTEXTFORGE_MCP_VERSION=v1.0

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=heimnetz
POSTGRES_USER=heimnetz
POSTGRES_PASSWORD=your-secure-password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_SECRET=your-api-key-secret

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin-password

# Storage Configuration
STORAGE_TYPE=local
STORAGE_PATH=/app/storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
AWS_BUCKET_NAME=heimnetz-storage
```

### Service Configuration

#### AetherCore Models (aethercore/config/models.yaml)
```yaml
models:
  bert-base-uncased:
    name: "BERT Base Uncased"
    model_type: "transformer"
    source: "huggingface"
    model_path: "bert-base-uncased"
    device: "auto"
    max_memory: "1GB"
    auto_load: true
    
  gpt2:
    name: "GPT-2"
    model_type: "transformer"
    source: "huggingface"
    model_path: "gpt2"
    device: "auto"
    max_memory: "1GB"
    auto_load: false
    
  custom-onnx:
    name: "Custom ONNX Model"
    model_type: "onnx"
    source: "local"
    model_path: "/app/models/custom-model.onnx"
    device: "cpu"
    providers: ["CPUExecutionProvider"]
    auto_load: false
```

#### ContextForge Configuration (contextforge/config/context.yaml)
```yaml
context:
  max_context_length: 8192
  default_model: "bert-base-uncased"
  embedding_cache_size: 1000
  similarity_threshold: 0.8
  
protocols:
  mcp:
    version: "v1.0"
    features:
      - context_management
      - protocol_compliance
      - real_time_updates
    
integrations:
  redis:
    enabled: true
    cache_ttl: 3600
    
  postgres:
    enabled: true
    connection_pool_size: 10
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### Development Deployment
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Production Deployment
```bash
# Start production services
docker-compose up -d

# Scale services
docker-compose up -d --scale aethercore=3 --scale contextforge=2

# Monitor services
docker-compose logs -f --tail=100
```

### Option 2: Kubernetes

#### Prepare Kubernetes Manifests
```bash
# Create namespace
kubectl create namespace heimnetz

# Apply configurations
kubectl apply -f k8s/
```

#### Deploy Services
```bash
# Deploy database
kubectl apply -f k8s/postgres/

# Deploy Redis
kubectl apply -f k8s/redis/

# Deploy AetherCore
kubectl apply -f k8s/aethercore/

# Deploy ContextForge
kubectl apply -f k8s/contextforge/

# Deploy monitoring
kubectl apply -f k8s/monitoring/
```

### Option 3: Manual Installation

#### Database Setup
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb heimnetz

# Run migrations
python manage.py migrate
```

#### Redis Setup
```bash
# Start Redis
sudo systemctl start redis

# Verify connection
redis-cli ping
```

#### Service Startup
```bash
# Start AetherCore
cd aethercore
python index.py

# Start ContextForge
cd contextforge
python index.py

# Start monitoring
python monitoring/prometheus_exporter.py
```

## Service Management

### CLI Commands

#### System Operations
```bash
# Check overall status
python heimnetz_cli.py status

# System health check
python heimnetz_cli.py system health

# Service information
python heimnetz_cli.py system services
```

#### AetherCore Management
```bash
# AetherCore status
python heimnetz_cli.py aethercore info

# List models
python heimnetz_cli.py aethercore models

# Load model
python heimnetz_cli.py aethercore load bert-base-uncased

# Serve inference
python heimnetz_cli.py aethercore serve bert-base-uncased --text "Hello world"
```

#### ContextForge Management
```bash
# ContextForge status
python heimnetz_cli.py context info

# Health check
python heimnetz_cli.py context health

# Run tests
python heimnetz_cli.py context test basic_functionality
```

### Docker Service Management

#### Container Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart service
docker-compose restart aethercore

# View logs
docker-compose logs -f aethercore

# Execute commands
docker-compose exec aethercore python heimnetz_cli.py aethercore info
```

#### Scaling Services
```bash
# Scale AetherCore
docker-compose up -d --scale aethercore=3

# Scale ContextForge
docker-compose up -d --scale contextforge=2

# Update configuration
docker-compose up -d --force-recreate
```

## Monitoring and Logging

### Prometheus Metrics
Access Prometheus at: `http://localhost:9090`

Key metrics to monitor:
- `aethercore_requests_total`
- `aethercore_request_duration_seconds`
- `aethercore_model_memory_usage_bytes`
- `contextforge_context_operations_total`
- `contextforge_protocol_compliance_score`

### Grafana Dashboards
Access Grafana at: `http://localhost:3000`

Default credentials:
- Username: `admin`
- Password: `admin-password`

Pre-configured dashboards:
- AetherCore Performance
- ContextForge Operations
- System Resources
- Service Health

### Log Aggregation
```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f aethercore

# Export logs
docker-compose logs --no-color > heimnetz.log
```

## Security Hardening

### SSL/TLS Configuration
```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update docker-compose.yml
```

### Firewall Configuration
```bash
# Allow required ports
sudo ufw allow 8000/tcp  # ContextForge
sudo ufw allow 8001/tcp  # AetherCore
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus

# Block unnecessary ports
sudo ufw deny 5432/tcp   # PostgreSQL (internal only)
sudo ufw deny 6379/tcp   # Redis (internal only)
```

### Authentication Setup
```bash
# Create API keys
python scripts/create_api_key.py --name "production-key"

# Setup JWT secrets
python scripts/generate_jwt_secret.py
```

## Backup and Recovery

### Database Backup
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U heimnetz heimnetz > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U heimnetz heimnetz < backup.sql
```

### Configuration Backup
```bash
# Backup configurations
tar -czf config-backup.tar.gz .env aethercore/config/ contextforge/config/

# Restore configurations
tar -xzf config-backup.tar.gz
```

### Model Backup
```bash
# Backup models
docker-compose exec aethercore tar -czf models-backup.tar.gz /app/models/

# Restore models
docker-compose exec aethercore tar -xzf models-backup.tar.gz -C /app/
```

## Performance Optimization

### Resource Allocation
```yaml
# docker-compose.yml
services:
  aethercore:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: 2.0
        reservations:
          memory: 2G
          cpus: 1.0
```

### Caching Strategy
```bash
# Redis cache optimization
redis-cli config set maxmemory 1gb
redis-cli config set maxmemory-policy allkeys-lru
```

### Model Optimization
```bash
# Model quantization
python scripts/quantize_model.py --model bert-base-uncased --precision int8

# Model pruning
python scripts/prune_model.py --model gpt2 --sparsity 0.9
```

## Troubleshooting

### Common Issues

#### Service Startup Failures
```bash
# Check logs
docker-compose logs service-name

# Verify configuration
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Check port conflicts
netstat -tlnp | grep :8001
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Optimize memory settings
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p
```

#### Network Issues
```bash
# Check network connectivity
docker network ls
docker network inspect heimnetz_default

# Test service communication
docker-compose exec aethercore curl contextforge:8000/health
```

### Health Checks
```bash
# Service health endpoints
curl http://localhost:8001/health    # AetherCore
curl http://localhost:8000/health    # ContextForge

# Database connectivity
docker-compose exec postgres pg_isready

# Redis connectivity
docker-compose exec redis redis-cli ping
```

## Maintenance

### Regular Tasks

#### Daily
- Check service health
- Monitor resource usage
- Review error logs

#### Weekly
- Update security patches
- Backup configurations
- Performance optimization

#### Monthly
- Full system backup
- Security audit
- Dependency updates

### Update Procedures
```bash
# Pull latest images
docker-compose pull

# Update services
docker-compose up -d --force-recreate

# Verify updates
python heimnetz_cli.py version
```

## Support

For additional support:
- Documentation: `/docs/`
- CLI help: `python heimnetz_cli.py --help`
- Health checks: `python heimnetz_cli.py system health`
- Logs: `docker-compose logs -f`

## License

This deployment guide is part of the Heimnetz Enterprise Suite, licensed under the MIT License.
