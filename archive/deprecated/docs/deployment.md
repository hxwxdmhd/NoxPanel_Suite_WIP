# 🚀 Deployment Guide

This guide provides comprehensive instructions for deploying Heimnetz in various environments, from simple home setups to advanced configurations.

## 🎯 Quick Start Deployment

### **Option 1: One-Click Local Install (Recommended for Beginners)**

#### **Windows Installation**
```powershell
# Download and run the automated installer
Invoke-WebRequest -Uri "https://github.com/HobeLab-Projects/Heimnetz/releases/latest/download/heimnetz-installer-windows.ps1" -OutFile "heimnetz-installer.ps1"

# Run installer with elevated privileges
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\heimnetz-installer.ps1
```

#### **macOS Installation**
```bash
# Download and run the automated installer
curl -L https://github.com/HobeLab-Projects/Heimnetz/releases/latest/download/heimnetz-installer-macos.sh -o heimnetz-installer.sh

# Make executable and run
chmod +x heimnetz-installer.sh
sudo ./heimnetz-installer.sh
```

#### **Linux Installation**
```bash
# Download and run the automated installer
wget https://github.com/HobeLab-Projects/Heimnetz/releases/latest/download/heimnetz-installer-linux.sh

# Make executable and run
chmod +x heimnetz-installer-linux.sh
sudo ./heimnetz-installer-linux.sh
```

### **Option 2: Docker Deployment (Recommended for Advanced Users)**

#### **Quick Docker Setup**
```bash
# Clone repository
git clone https://github.com/HobeLab-Projects/Heimnetz.git
cd Heimnetz

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f heimnetz
```

#### **Docker Compose Configuration**
```yaml
# docker-compose.yml
version: '3.8'

services:
  heimnetz:
    build: .
    container_name: heimnetz
    restart: unless-stopped
    ports:
      - "8080:8080"    # Web interface
      - "8443:8443"    # HTTPS interface
      - "1883:1883"    # MQTT (if enabled)
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock  # For container management
    environment:
      - HEIMNETZ_ENV=production
      - HEIMNETZ_LOG_LEVEL=INFO
      - HEIMNETZ_ENABLE_AI=true
      - HEIMNETZ_ENABLE_VOICE=false  # Disable voice in container by default
    networks:
      - heimnetz-network
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    container_name: heimnetz-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15-alpine
    container_name: heimnetz-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: heimnetz
      POSTGRES_USER: heimnetz
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secure_default_password}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d

  ollama:
    image: ollama/ollama:latest
    container_name: heimnetz-ollama
    restart: unless-stopped
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    command: ["ollama", "serve"]

volumes:
  redis-data:
  postgres-data:
  ollama-data:

networks:
  heimnetz-network:
    driver: bridge
```

### **Option 3: Manual Installation**

#### **Prerequisites**
```bash
# Python 3.9 or higher
python3 --version

# Node.js 16 or higher (for web interface)
node --version

# Git for cloning repository
git --version

# Optional: Docker for containerized AI models
docker --version
```

#### **Step-by-Step Manual Installation**
```bash
# 1. Clone the repository
git clone https://github.com/HobeLab-Projects/Heimnetz.git
cd Heimnetz

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install development dependencies (optional)
pip install -r requirements-dev.txt

# 5. Install Node.js dependencies for web interface
cd htdocs
npm install
npm run build
cd ..

# 6. Set up configuration
cp config/heimnetz_unified.json.example config/heimnetz_unified.json

# 7. Initialize database
python scripts/init_database.py

# 8. Install AI models (optional but recommended)
python scripts/install_ai_models.py

# 9. Run initial setup
python main.py --setup

# 10. Start Heimnetz
python main.py
```

## 🏠 Environment-Specific Deployments

### **Home Network Deployment**

#### **Single Device Setup (Most Common)**
```bash
# Configuration for typical home router setup
{
  "deployment": {
    "type": "home_single",
    "network_interface": "auto",
    "discovery_range": "192.168.1.0/24",
    "web_port": 8080,
    "https_port": 8443,
    "enable_upnp": true,
    "auto_device_discovery": true
  },
  "features": {
    "ai_assistance": true,
    "voice_interface": true,
    "guest_network_monitoring": true,
    "parental_controls": true,
    "automatic_updates": true
  },
  "security": {
    "require_authentication": true,
    "session_timeout": 3600,
    "enable_2fa": false,
    "auto_block_threats": true
  }
}
```

#### **Multi-Node Home Setup**
```yaml
# docker-compose.yml for distributed home setup
version: '3.8'

services:
  heimnetz-main:
    image: heimnetz:latest
    hostname: heimnetz-main
    environment:
      - HEIMNETZ_ROLE=coordinator
      - HEIMNETZ_NODE_ID=main
    volumes:
      - ./config/main:/app/config
    ports:
      - "8080:8080"
    networks:
      - heimnetz-cluster

  heimnetz-node1:
    image: heimnetz:latest
    hostname: heimnetz-node1
    environment:
      - HEIMNETZ_ROLE=agent
      - HEIMNETZ_COORDINATOR=heimnetz-main:8080
      - HEIMNETZ_NODE_ID=node1
    volumes:
      - ./config/node1:/app/config
    networks:
      - heimnetz-cluster
    depends_on:
      - heimnetz-main

  heimnetz-node2:
    image: heimnetz:latest
    hostname: heimnetz-node2
    environment:
      - HEIMNETZ_ROLE=agent
      - HEIMNETZ_COORDINATOR=heimnetz-main:8080
      - HEIMNETZ_NODE_ID=node2
    volumes:
      - ./config/node2:/app/config
    networks:
      - heimnetz-cluster
    depends_on:
      - heimnetz-main

networks:
  heimnetz-cluster:
    driver: bridge
```

### **Small Business Deployment**

#### **Professional Configuration**
```json
{
  "deployment": {
    "type": "business_small",
    "network_segments": [
      {
        "name": "office",
        "range": "192.168.10.0/24",
        "security_level": "high"
      },
      {
        "name": "guest",
        "range": "192.168.20.0/24",
        "security_level": "medium",
        "isolated": true
      },
      {
        "name": "iot",
        "range": "192.168.30.0/24",
        "security_level": "high",
        "restricted": true
      }
    ],
    "monitoring": {
      "deep_packet_inspection": true,
      "bandwidth_monitoring": true,
      "application_monitoring": true,
      "user_activity_tracking": true
    }
  },
  "compliance": {
    "data_retention_days": 90,
    "audit_logging": true,
    "encrypted_storage": true,
    "backup_schedule": "daily"
  },
  "integrations": {
    "active_directory": false,
    "siem_export": true,
    "email_alerts": true,
    "slack_notifications": false
  }
}
```

#### **Kubernetes Deployment for Business**
```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heimnetz
  namespace: monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: heimnetz
  template:
    metadata:
      labels:
        app: heimnetz
    spec:
      containers:
      - name: heimnetz
        image: heimnetz:latest
        ports:
        - containerPort: 8080
        env:
        - name: HEIMNETZ_ENV
          value: "production"
        - name: HEIMNETZ_LOG_LEVEL
          value: "INFO"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: heimnetz-secrets
              key: database-url
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: heimnetz-config
      - name: data
        persistentVolumeClaim:
          claimName: heimnetz-data

---
apiVersion: v1
kind: Service
metadata:
  name: heimnetz-service
  namespace: monitoring
spec:
  selector:
    app: heimnetz
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: heimnetz-ingress
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - heimnetz.yourdomain.com
    secretName: heimnetz-tls
  rules:
  - host: heimnetz.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: heimnetz-service
            port:
              number: 80
```

### **Enterprise Deployment**

#### **High Availability Setup**
```yaml
# docker-swarm-stack.yml
version: '3.8'

services:
  heimnetz:
    image: heimnetz:latest
    deploy:
      replicas: 5
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
    environment:
      - HEIMNETZ_ENV=production
      - HEIMNETZ_CLUSTER_MODE=true
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/heimnetz
    networks:
      - heimnetz-backend
      - heimnetz-frontend
    configs:
      - source: heimnetz-config
        target: /app/config/heimnetz.json

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
    networks:
      - heimnetz-backend
    volumes:
      - redis-data:/data

  postgres:
    image: postgres:15-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    environment:
      POSTGRES_DB: heimnetz
      POSTGRES_USER: heimnetz
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres-password
    networks:
      - heimnetz-backend
    volumes:
      - postgres-data:/var/lib/postgresql/data
    secrets:
      - postgres-password

  nginx:
    image: nginx:alpine
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == worker
    ports:
      - "80:80"
      - "443:443"
    networks:
      - heimnetz-frontend
    configs:
      - source: nginx-config
        target: /etc/nginx/nginx.conf
    secrets:
      - ssl-cert
      - ssl-key

networks:
  heimnetz-backend:
    driver: overlay
    internal: true
  heimnetz-frontend:
    driver: overlay

volumes:
  redis-data:
  postgres-data:

configs:
  heimnetz-config:
    external: true
  nginx-config:
    external: true

secrets:
  postgres-password:
    external: true
  ssl-cert:
    external: true
  ssl-key:
    external: true
```

## 🔧 Configuration Management

### **Environment Variables**

#### **Core Configuration**
```bash
# Core application settings
HEIMNETZ_ENV=production          # Environment: development, staging, production
HEIMNETZ_LOG_LEVEL=INFO         # Logging level: DEBUG, INFO, WARNING, ERROR
HEIMNETZ_HOST=0.0.0.0           # Host to bind to
HEIMNETZ_PORT=8080              # Primary port
HEIMNETZ_HTTPS_PORT=8443        # HTTPS port

# Feature toggles
HEIMNETZ_ENABLE_AI=true         # Enable AI features
HEIMNETZ_ENABLE_VOICE=true      # Enable voice interface
HEIMNETZ_ENABLE_ANALYTICS=true  # Enable usage analytics
HEIMNETZ_ENABLE_UPDATES=true    # Enable automatic updates

# Security settings
HEIMNETZ_SECRET_KEY=your-secret-key-here  # Application secret key
HEIMNETZ_SESSION_TIMEOUT=3600             # Session timeout in seconds
HEIMNETZ_ENABLE_2FA=false                 # Two-factor authentication
HEIMNETZ_CSRF_PROTECTION=true             # CSRF protection

# Database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/heimnetz
REDIS_URL=redis://localhost:6379/0

# AI model configuration
OLLAMA_HOST=localhost:11434     # Ollama server
AI_MODEL_PATH=/app/models       # Local AI model storage
DEFAULT_AI_MODEL=llama2:7b      # Default AI model

# Network configuration
NETWORK_INTERFACE=auto          # Network interface to monitor
DISCOVERY_RANGE=auto            # IP range for device discovery
SCAN_INTERVAL=300               # Device scan interval in seconds

# External integrations
SMTP_HOST=smtp.gmail.com        # Email server
SMTP_PORT=587                   # Email port
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=your-email-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### **Configuration Files**

#### **Main Configuration (heimnetz_unified.json)**
```json
{
  "application": {
    "name": "Heimnetz",
    "version": "2.0.0",
    "environment": "production",
    "debug": false,
    "log_level": "INFO"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "https_port": 8443,
    "ssl_cert": "/app/certs/cert.pem",
    "ssl_key": "/app/certs/key.pem",
    "workers": 4,
    "timeout": 30
  },
  "database": {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "name": "heimnetz",
    "username": "heimnetz",
    "password": "${DB_PASSWORD}",
    "pool_size": 20,
    "ssl_mode": "prefer"
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": "${REDIS_PASSWORD}",
    "ssl": false
  },
  "ai": {
    "enabled": true,
    "provider": "ollama",
    "ollama_host": "localhost:11434",
    "models": [
      "llama2:7b",
      "mistral",
      "codellama",
      "dolphin",
      "neural-chat"
    ],
    "default_model": "llama2:7b",
    "max_tokens": 2048,
    "temperature": 0.7,
    "timeout": 30
  },
  "security": {
    "secret_key": "${SECRET_KEY}",
    "session_timeout": 3600,
    "max_login_attempts": 5,
    "lockout_duration": 900,
    "password_policy": {
      "min_length": 8,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_numbers": true,
      "require_symbols": false
    },
    "two_factor_auth": {
      "enabled": false,
      "provider": "totp",
      "backup_codes": 10
    },
    "csrf_protection": true,
    "secure_headers": true
  },
  "network": {
    "interface": "auto",
    "discovery_range": "auto",
    "scan_interval": 300,
    "deep_scan_interval": 3600,
    "port_scan_timeout": 5,
    "max_concurrent_scans": 50,
    "enable_upnp": true,
    "monitor_external_connections": true
  },
  "features": {
    "device_discovery": true,
    "security_scanning": true,
    "performance_monitoring": true,
    "ai_assistance": true,
    "voice_interface": true,
    "guest_network": true,
    "parental_controls": true,
    "bandwidth_monitoring": true,
    "intrusion_detection": true
  },
  "notifications": {
    "email": {
      "enabled": false,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "",
      "password": "${EMAIL_PASSWORD}",
      "from_address": "heimnetz@yourdomain.com",
      "tls": true
    },
    "slack": {
      "enabled": false,
      "webhook_url": "${SLACK_WEBHOOK}",
      "channel": "#network-alerts"
    },
    "webhook": {
      "enabled": false,
      "url": "",
      "headers": {},
      "retry_attempts": 3
    }
  },
  "backup": {
    "enabled": true,
    "schedule": "daily",
    "retention_days": 30,
    "location": "/app/backups",
    "compress": true,
    "encrypt": true
  },
  "logging": {
    "level": "INFO",
    "format": "structured",
    "output": "file",
    "file_path": "/app/logs/heimnetz.log",
    "max_file_size": "100MB",
    "backup_count": 5,
    "rotate_daily": true
  }
}
```

### **Docker Environment Configuration**

#### **.env File for Docker Compose**
```bash
# .env file for docker-compose
COMPOSE_PROJECT_NAME=heimnetz

# Application settings
HEIMNETZ_VERSION=latest
HEIMNETZ_ENV=production
HEIMNETZ_LOG_LEVEL=INFO

# Database settings
DB_PASSWORD=your_secure_database_password
POSTGRES_DB=heimnetz
POSTGRES_USER=heimnetz

# Redis settings
REDIS_PASSWORD=your_secure_redis_password

# Security settings
SECRET_KEY=your_very_long_random_secret_key_here
JWT_SECRET=another_long_random_key_for_jwt_tokens

# Email settings (optional)
EMAIL_PASSWORD=your_email_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# External integrations (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# AI settings
OLLAMA_MODELS=llama2:7b,mistral,codellama
DEFAULT_AI_MODEL=llama2:7b

# Network settings
NETWORK_INTERFACE=auto
DISCOVERY_RANGE=192.168.0.0/16

# Backup settings
BACKUP_LOCATION=/app/backups
BACKUP_ENCRYPTION_KEY=backup_encryption_key_here

# SSL settings (if using custom certificates)
SSL_CERT_PATH=/app/certs/cert.pem
SSL_KEY_PATH=/app/certs/key.pem
```

## 🔄 Update and Maintenance

### **Automated Updates**

#### **Update Configuration**
```json
{
  "updates": {
    "enabled": true,
    "channel": "stable",
    "check_interval": 86400,
    "auto_install": {
      "security_updates": true,
      "minor_updates": false,
      "major_updates": false
    },
    "maintenance_window": {
      "enabled": true,
      "start_time": "02:00",
      "end_time": "04:00",
      "timezone": "UTC",
      "days": ["sunday"]
    },
    "rollback": {
      "enabled": true,
      "keep_versions": 3,
      "auto_rollback_on_failure": true
    }
  }
}
```

#### **Manual Update Process**
```bash
# Check for updates
python main.py --check-updates

# Download updates
python main.py --download-updates

# Apply updates (with backup)
python main.py --update --backup

# Rollback if needed
python main.py --rollback --version 1.9.0

# Check system status after update
python main.py --health-check
```

### **Backup and Recovery**

#### **Automated Backup Configuration**
```python
# backup_config.py
BACKUP_CONFIG = {
    'enabled': True,
    'schedule': {
        'daily': '02:30',
        'weekly': 'sunday:03:00',
        'monthly': '1:04:00'
    },
    'retention': {
        'daily': 7,    # Keep 7 daily backups
        'weekly': 4,   # Keep 4 weekly backups
        'monthly': 12  # Keep 12 monthly backups
    },
    'include': [
        'config/',
        'data/',
        'logs/',
        'user_preferences/',
        'certificates/'
    ],
    'exclude': [
        'data/temp/',
        'logs/debug/',
        'data/cache/'
    ],
    'compression': 'gzip',
    'encryption': True,
    'destinations': [
        {
            'type': 'local',
            'path': '/app/backups'
        },
        {
            'type': 'cloud',
            'provider': 'aws_s3',
            'bucket': 'heimnetz-backups',
            'region': 'us-east-1',
            'encryption': 'AES256'
        }
    ]
}
```

#### **Manual Backup Commands**
```bash
# Create manual backup
python scripts/backup.py --create --name "pre-update-backup"

# List available backups
python scripts/backup.py --list

# Restore from backup
python scripts/backup.py --restore --backup-id "backup-20250715-020030"

# Verify backup integrity
python scripts/backup.py --verify --backup-id "backup-20250715-020030"

# Clean old backups
python scripts/backup.py --cleanup --older-than 30
```

### **Health Monitoring**

#### **System Health Checks**
```python
# health_monitor.py
import asyncio
import time
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self.checks = [
            self.check_application_status,
            self.check_database_connection,
            self.check_redis_connection,
            self.check_ai_models,
            self.check_disk_space,
            self.check_memory_usage,
            self.check_network_connectivity,
            self.check_security_services
        ]
    
    async def run_health_check(self) -> dict:
        """Run comprehensive health check."""
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        for check in self.checks:
            try:
                result = await check()
                health_report['checks'][check.__name__] = result
                
                if result['status'] == 'error':
                    health_report['errors'].append(result)
                elif result['status'] == 'warning':
                    health_report['warnings'].append(result)
                    
            except Exception as e:
                health_report['checks'][check.__name__] = {
                    'status': 'error',
                    'message': f'Health check failed: {e}'
                }
                health_report['errors'].append({
                    'check': check.__name__,
                    'error': str(e)
                })
        
        # Determine overall status
        if health_report['errors']:
            health_report['overall_status'] = 'critical'
        elif health_report['warnings']:
            health_report['overall_status'] = 'warning'
        else:
            health_report['overall_status'] = 'healthy'
        
        return health_report
    
    async def check_application_status(self) -> dict:
        """Check if main application is running properly."""
        
        try:
            # Check if web server is responding
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8080/health') as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'message': 'Application responding normally',
                            'response_time': response.headers.get('X-Response-Time', 'unknown')
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Application returned status {response.status}'
                        }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Application not responding: {e}'
            }
    
    async def check_disk_space(self) -> dict:
        """Check available disk space."""
        
        import shutil
        
        try:
            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100
            
            if free_percent < 5:
                return {
                    'status': 'error',
                    'message': f'Critical: Only {free_percent:.1f}% disk space remaining',
                    'free_space_gb': free // (1024**3),
                    'free_percent': free_percent
                }
            elif free_percent < 15:
                return {
                    'status': 'warning',
                    'message': f'Warning: Only {free_percent:.1f}% disk space remaining',
                    'free_space_gb': free // (1024**3),
                    'free_percent': free_percent
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'Disk space OK: {free_percent:.1f}% available',
                    'free_space_gb': free // (1024**3),
                    'free_percent': free_percent
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unable to check disk space: {e}'
            }
```

## 🚨 Troubleshooting

### **Common Deployment Issues**

#### **Port Conflicts**
```bash
# Check if ports are already in use
netstat -tuln | grep :8080
netstat -tuln | grep :8443

# Find what's using the port
lsof -i :8080

# Kill process using port (if safe to do so)
sudo kill -9 $(lsof -t -i:8080)

# Change port in configuration
# Edit config/heimnetz_unified.json
{
  "server": {
    "port": 8081,  # Changed from 8080
    "https_port": 8444  # Changed from 8443
  }
}
```

#### **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) /path/to/heimnetz
chmod -R 755 /path/to/heimnetz

# Fix specific permission issues
chmod +x scripts/*.sh
chmod 600 config/ssl/*.key
chmod 644 config/ssl/*.crt

# SELinux issues (CentOS/RHEL)
sudo setsebool -P httpd_can_network_connect 1
sudo semanage port -a -t http_port_t -p tcp 8080
```

#### **Database Connection Issues**
```bash
# Test database connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://user:pass@localhost:5432/heimnetz')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Reset database if corrupted
python scripts/reset_database.py --confirm

# Restore from backup
python scripts/backup.py --restore --latest --database-only
```

#### **AI Model Issues**
```bash
# Check Ollama status
ollama list
curl http://localhost:11434/api/tags

# Pull missing models
ollama pull llama2:7b
ollama pull mistral

# Test AI functionality
python -c "
import asyncio
from nox_assistant.llm_wrapper import LLMWrapper

async def test_ai():
    llm = LLMWrapper()
    response = await llm.query_model('llama2:7b', 'Hello, are you working?')
    print(f'AI Response: {response}')

asyncio.run(test_ai())
"
```

### **Performance Optimization**

#### **System Resource Optimization**
```bash
# Monitor resource usage
htop
docker stats  # If using Docker

# Optimize Python memory usage
export PYTHONOPTIMIZE=1
export PYTHONUNBUFFERED=1

# Adjust worker processes based on CPU cores
# In config/heimnetz_unified.json
{
  "server": {
    "workers": 4  # Set to number of CPU cores
  }
}

# Enable compression for web interface
{
  "server": {
    "compression": true,
    "compression_level": 6
  }
}
```

#### **Database Performance Tuning**
```sql
-- PostgreSQL optimization queries
-- Check database performance
SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch 
FROM pg_stat_user_tables 
WHERE schemaname = 'public';

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_devices_last_seen ON devices(last_seen);
CREATE INDEX CONCURRENTLY idx_events_timestamp ON network_events(timestamp);
CREATE INDEX CONCURRENTLY idx_logs_level_timestamp ON logs(level, timestamp);

-- Update table statistics
ANALYZE;

-- Vacuum and reindex
VACUUM ANALYZE;
REINDEX DATABASE heimnetz;
```

### **Monitoring and Alerting**

#### **Log Analysis**
```bash
# View recent logs
tail -f logs/heimnetz.log

# Search for errors
grep "ERROR" logs/heimnetz.log | tail -20

# Monitor specific issues
grep -i "connection\|timeout\|failed" logs/heimnetz.log

# Log rotation check
ls -la logs/
logrotate -d /etc/logrotate.d/heimnetz  # If using logrotate
```

#### **Alert Configuration**
```json
{
  "alerts": {
    "disk_space": {
      "enabled": true,
      "threshold": 15,
      "severity": "warning"
    },
    "memory_usage": {
      "enabled": true,
      "threshold": 85,
      "severity": "warning"
    },
    "cpu_usage": {
      "enabled": true,
      "threshold": 90,
      "severity": "critical"
    },
    "application_errors": {
      "enabled": true,
      "threshold": 10,
      "timeframe": "5m",
      "severity": "critical"
    },
    "security_events": {
      "enabled": true,
      "threshold": 1,
      "severity": "critical"
    }
  }
}
```

## 📊 Production Readiness Checklist

### **Pre-Deployment Checklist**
- [ ] **Security Configuration**
  - [ ] Strong passwords configured
  - [ ] SSL/TLS certificates installed
  - [ ] Firewall rules configured
  - [ ] Security scanning enabled
  - [ ] Backup encryption enabled

- [ ] **Performance Configuration**
  - [ ] Resource limits set appropriately
  - [ ] Database indexes created
  - [ ] Caching configured
  - [ ] Log rotation configured
  - [ ] Monitoring enabled

- [ ] **Reliability Configuration**
  - [ ] Health checks implemented
  - [ ] Backup schedule configured
  - [ ] Auto-restart policies set
  - [ ] Failover procedures documented
  - [ ] Recovery procedures tested

- [ ] **Operational Readiness**
  - [ ] Monitoring dashboards configured
  - [ ] Alert thresholds set
  - [ ] Documentation updated
  - [ ] Team training completed
  - [ ] Support procedures documented

### **Post-Deployment Validation**
```bash
# Run comprehensive system check
python scripts/post_deployment_check.py

# Verify all services are running
systemctl status heimnetz  # If using systemd
docker-compose ps         # If using Docker

# Test critical functionality
python scripts/functional_tests.py

# Verify security configuration
python scripts/security_validation.py

# Check performance baselines
python scripts/performance_baseline.py
```

---

## 🆘 Support and Resources

### **Getting Help**
- 📖 **Documentation**: [Complete user and developer guides](../README.md)
- 💬 **Community Support**: [GitHub Discussions](https://github.com/HobeLab-Projects/Heimnetz/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/HobeLab-Projects/Heimnetz/issues)
- 📧 **Direct Support**: support@heimnetz.org

### **Additional Resources**
- 🎓 **Training Materials**: [Heimnetz University](https://learn.heimnetz.org)
- 🛠️ **Professional Services**: [Deployment Assistance](https://heimnetz.org/services)
- 🤝 **Community Plugins**: [Plugin Repository](https://plugins.heimnetz.org)
- 📱 **Mobile Apps**: [iOS and Android clients](https://heimnetz.org/mobile)

---

**Successful deployment is just the beginning. Heimnetz grows with your network, providing intelligent, adaptive management that learns and improves over time.** 🚀

**Welcome to the future of ADHD-friendly network management!** 🎯
