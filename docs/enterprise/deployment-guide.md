# 🚀 NoxPanel Suite Enterprise Deployment Guide

## Overview

This guide covers enterprise-grade deployment of NoxPanel Suite with high availability, security, and scalability considerations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     🌐 Load Balancer (Nginx)                   │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Tier                                                 │
│  ├── React UI (Port 3000)                                      │
│  ├── Mobile PWA (Port 3002)                                    │
│  └── Grafana Dashboards (Port 3001)                            │
├─────────────────────────────────────────────────────────────────┤
│  Application Tier                                              │
│  ├── FastAPI Services (Port 8000)                              │
│  ├── Flask Legacy (Port 5000)                                  │
│  ├── Background Workers (Celery)                               │
│  └── AI Services (Port 8001)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Data Tier                                                     │
│  ├── PostgreSQL (Port 5432)                                    │
│  ├── Redis (Port 6379)                                         │
│  ├── InfluxDB (Port 8086)                                      │
│  └── Ollama AI Models (Port 11434)                             │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- 1 Gbps network

**Recommended (Production):**
- 8+ CPU cores
- 32+ GB RAM
- 500+ GB SSD storage
- 10 Gbps network
- Redundant power supplies

**Enterprise (High Availability):**
- 16+ CPU cores per node
- 64+ GB RAM per node
- 1+ TB NVMe storage per node
- Multiple data centers
- Load balancers and failover systems

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- Kubernetes 1.25+ (for container orchestration)
- Linux kernel 5.4+ (Ubuntu 20.04+ or CentOS 8+)

## Quick Start (Single Node)

### 1. Download and Setup

```bash
# Clone the repository
git clone https://github.com/noxpanel/noxsuite.git
cd noxsuite

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment

```bash
# Core Settings
NOXSUITE_ENV=production
DEBUG=false
SECRET_KEY=<generate-random-key>

# Database Configuration
DATABASE_URL=postgresql://noxpanel:password@postgres:5432/noxpanel
REDIS_URL=redis://redis:6379/0

# Security Settings
ENABLE_2FA=true
SESSION_TIMEOUT=3600
CORS_ORIGINS=["https://your-domain.com"]

# AI Features
ENABLE_AI=true
AI_MODELS=mistral:7b-instruct,gemma:7b-it
OLLAMA_HOST=http://ollama:11434

# Monitoring
ENABLE_MONITORING=true
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### 3. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Wait for services to initialize
./scripts/wait-for-services.sh

# Install AI models
./scripts/install-models.sh

# Create admin user
./scripts/create-admin-user.sh
```

## High Availability Deployment

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace noxpanel

# Deploy configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy data tier
kubectl apply -f k8s/postgres-cluster.yaml
kubectl apply -f k8s/redis-cluster.yaml

# Deploy application tier
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml

# Deploy frontend tier
kubectl apply -f k8s/ui-deployment.yaml
kubectl apply -f k8s/nginx-ingress.yaml

# Verify deployment
kubectl get pods -n noxpanel
kubectl get services -n noxpanel
```

### Load Balancer Configuration

```nginx
upstream noxpanel_api {
    least_conn;
    server api1.noxpanel.local:8000 max_fails=3 fail_timeout=30s;
    server api2.noxpanel.local:8000 max_fails=3 fail_timeout=30s;
    server api3.noxpanel.local:8000 max_fails=3 fail_timeout=30s;
}

upstream noxpanel_ui {
    least_conn;
    server ui1.noxpanel.local:3000 max_fails=3 fail_timeout=30s;
    server ui2.noxpanel.local:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name noxpanel.yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location /api/ {
        proxy_pass http://noxpanel_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
    
    # UI proxy
    location / {
        proxy_pass http://noxpanel_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Database Setup

### PostgreSQL Configuration

```sql
-- Create database and user
CREATE DATABASE noxpanel;
CREATE USER noxpanel WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE noxpanel TO noxpanel;

-- Enable required extensions
\c noxpanel;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Run migrations
python manage.py migrate
```

### Redis Configuration

```bash
# redis.conf optimizations
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Security Configuration

### SSL/TLS Setup

```bash
# Generate certificates with Let's Encrypt
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d noxpanel.yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Firewall Configuration

```bash
# UFW configuration
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Application-specific rules
ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
ufw allow from 10.0.0.0/8 to any port 6379  # Redis
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'noxpanel-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'noxpanel-workers'
    static_configs:
      - targets: ['worker:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

Pre-configured dashboards available:
- System Overview
- API Performance
- Database Metrics
- AI Model Usage
- Security Events
- Network Monitoring

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup-noxpanel.sh

BACKUP_DIR="/backup/noxpanel"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -h postgres -U noxpanel noxpanel | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Configuration backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/noxpanel/config/

# File storage backup
rsync -av /opt/noxpanel/data/ "$BACKUP_DIR/data_$DATE/"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "data_*" -mtime +30 -exec rm -rf {} \;
```

### Disaster Recovery

```bash
# Database restore
gunzip -c db_backup.sql.gz | psql -h postgres -U noxpanel noxpanel

# Configuration restore
tar -xzf config_backup.tar.gz -C /

# Service restart
docker-compose restart
```

## Performance Tuning

### Application Optimization

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 120
```

### Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

## Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   # Check logs
   docker-compose logs noxpanel-api
   
   # Check resource usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

2. **Database connection issues**
   ```bash
   # Test connection
   psql -h postgres -U noxpanel -d noxpanel
   
   # Check database logs
   docker logs postgres_container
   ```

3. **Performance issues**
   ```bash
   # Monitor resource usage
   htop
   iotop
   
   # Check application metrics
   curl http://localhost:8000/metrics
   ```

## Support and Maintenance

### Health Checks

```bash
# API health check
curl -f http://localhost:8000/health || exit 1

# Database health check
pg_isready -h postgres -p 5432

# Redis health check
redis-cli -h redis ping
```

### Maintenance Schedule

- **Daily:** Log rotation, backup verification
- **Weekly:** Security updates, performance review
- **Monthly:** Full system backup, capacity planning
- **Quarterly:** Security audit, disaster recovery testing

## Additional Resources

- [API Reference](./api-reference.md)
- [Security Guide](./security-guide.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Performance Tuning](./performance-tuning.md)

---

For support, contact the NoxPanel team or create an issue on GitHub.
