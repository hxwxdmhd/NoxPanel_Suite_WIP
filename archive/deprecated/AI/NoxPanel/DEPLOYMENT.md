# NoxPanel Production Deployment Guide

## Overview

NoxPanel is a comprehensive system monitoring and management platform with advanced AI capabilities. This guide covers the complete production deployment process.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Monitoring](#monitoring)
6. [Security](#security)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB, recommended 50GB+
- **CPU**: 2+ cores recommended
- **Network**: Internet access for initial setup

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (for key generation)

### Installation Commands

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git openssl curl

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd NoxPanel
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (see Configuration section)
nano .env
```

### 3. Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

### 4. Access Application

- **Web Interface**: http://localhost (or your configured domain)
- **Admin Panel**: Login with credentials from .env file
- **Monitoring**: http://localhost:3000 (Grafana)

## Configuration

### Environment Variables

Edit the `.env` file to configure your deployment:

#### Domain & SSL
```env
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com
```

#### Security Keys
```env
SECRET_KEY=your_ultra_secure_secret_key_here_minimum_32_characters
JWT_SECRET_KEY=your_ultra_secure_jwt_key_here_minimum_32_characters
CSRF_SECRET_KEY=your_ultra_secure_csrf_key_here_minimum_32_characters
```

#### Database
```env
DB_PASSWORD=your_secure_database_password_here
POSTGRES_DB=noxpanel
POSTGRES_USER=noxpanel
```

#### Admin Account
```env
ADMIN_USER=admin
ADMIN_PASS=your_secure_admin_password_here
```

#### Optional Services
```env
# External APIs
OPENAI_API_KEY=your_openai_api_key
OLLAMA_HOST=http://localhost:11434

# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noxpanel@example.com
SMTP_PASSWORD=your_smtp_password
```

### Key Generation

The deployment script automatically generates secure keys, but you can generate them manually:

```bash
# Generate secure keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For CSRF_SECRET_KEY
```

## Deployment

### Production Deployment

```bash
# Full deployment with all services
./scripts/deploy.sh deploy
```

### Available Commands

```bash
./scripts/deploy.sh deploy   # Full deployment
./scripts/deploy.sh start    # Start services
./scripts/deploy.sh stop     # Stop services
./scripts/deploy.sh logs     # View logs
./scripts/deploy.sh health   # Check health
./scripts/deploy.sh backup   # Create backup
./scripts/deploy.sh update   # Update and redeploy
```

### Manual Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

## Architecture

### Services

1. **Frontend** (Port 80/443)
   - React/TypeScript application
   - Nginx reverse proxy
   - SSL termination

2. **Backend** (Port 5002)
   - Flask API server
   - Authentication & authorization
   - AI processing engine

3. **Database** (Port 5432)
   - PostgreSQL 15
   - Persistent data storage
   - Automatic backups

4. **Cache** (Port 6379)
   - Redis for session storage
   - API response caching
   - Real-time data

5. **Reverse Proxy** (Traefik)
   - SSL certificate management
   - Load balancing
   - Automatic service discovery

### Monitoring Stack

1. **Prometheus** - Metrics collection
2. **Grafana** - Visualization dashboards
3. **Loki** - Log aggregation
4. **Promtail** - Log collection

## Monitoring

### Access Monitoring Services

- **Grafana**: https://grafana.your-domain.com
- **Prometheus**: https://prometheus.your-domain.com
- **Traefik Dashboard**: https://traefik.your-domain.com

### Default Dashboards

Grafana comes pre-configured with:
- System metrics dashboard
- Application performance dashboard
- Database monitoring dashboard
- Network traffic dashboard

### Custom Metrics

NoxPanel exposes custom metrics at `/metrics` endpoint:
- Request count and latency
- Error rates
- User sessions
- System resources

### Alerting

Configure alerts in Grafana for:
- High CPU/memory usage
- Database connection issues
- API error rates
- Certificate expiration

## Security

### Security Features

1. **CSRF Protection**
   - Token-based CSRF protection
   - Secure cookie handling
   - Request validation

2. **Content Security Policy**
   - Strict CSP headers
   - XSS prevention
   - Resource loading restrictions

3. **Rate Limiting**
   - Per-IP rate limiting
   - API endpoint protection
   - Brute force prevention

4. **Session Security**
   - Secure session management
   - Session timeout
   - Multi-factor authentication support

### SSL/TLS Configuration

Traefik automatically handles SSL certificates:
- Let's Encrypt integration
- Automatic certificate renewal
- HTTP to HTTPS redirect

### Security Best Practices

1. **Change Default Passwords**
   ```bash
   # Update admin password
   docker-compose exec backend python -c "
   from ultra_optimized_noxpanel import app, db, User
   with app.app_context():
       user = User.query.filter_by(username='admin').first()
       user.password = 'new_secure_password'
       db.session.commit()
   "
   ```

2. **Regular Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y

   # Update NoxPanel
   ./scripts/deploy.sh update
   ```

3. **Firewall Configuration**
   ```bash
   # Configure UFW
   sudo ufw enable
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   ```

4. **Backup Encryption**
   ```bash
   # Encrypt backup files
   gpg --symmetric --cipher-algo AES256 backup.tar.gz
   ```

## Maintenance

### Regular Tasks

#### Daily
- Monitor system health
- Check error logs
- Verify backup completion

#### Weekly
- Review security logs
- Update system packages
- Clean up old logs

#### Monthly
- Review and rotate SSL certificates
- Database maintenance
- Performance optimization

### Backup & Restore

#### Automated Backups
Backups are created automatically during deployment:
```bash
# Manual backup
./scripts/deploy.sh backup
```

#### Restore Process
```bash
# Stop services
docker-compose down

# Restore data
tar -xzf backup.tar.gz -C /

# Start services
docker-compose up -d
```

### Log Management

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

#### Log Rotation
Logs are automatically rotated by Docker. Configure retention:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Performance Optimization

#### Database Optimization
```sql
-- Run in PostgreSQL
VACUUM ANALYZE;
REINDEX DATABASE noxpanel;
```

#### Cache Optimization
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### System Resources
```bash
# Monitor resource usage
docker stats

# Adjust service resources in docker-compose.yml
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs service_name

# Check system resources
df -h
free -h

# Restart specific service
docker-compose restart service_name
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec database pg_isready

# Check connection settings
grep DATABASE_URL .env

# Reset database
docker-compose down
docker volume rm noxpanel_postgres_data
docker-compose up -d
```

#### SSL Certificate Issues
```bash
# Check certificate status
docker-compose logs reverse-proxy

# Force certificate renewal
docker-compose exec reverse-proxy \
  traefik certificates --acme.domains=your-domain.com
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services to clear memory leaks
docker-compose restart

# Adjust memory limits in docker-compose.yml
```

### Debug Mode

Enable debug mode for troubleshooting:
```env
# In .env file
NOXPANEL_ENV=development
LOG_LEVEL=DEBUG
```

### Health Checks

Built-in health check endpoints:
- Frontend: `http://localhost/health`
- Backend: `http://localhost:5002/health`
- Database: `docker-compose exec database pg_isready`

### Support

For additional support:
1. Check logs for specific error messages
2. Review configuration files
3. Consult documentation
4. Contact system administrator

## Upgrade Guide

### Version Upgrades

1. **Backup Current Installation**
   ```bash
   ./scripts/deploy.sh backup
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

3. **Update Dependencies**
   ```bash
   docker-compose build --no-cache
   ```

4. **Deploy Updates**
   ```bash
   ./scripts/deploy.sh deploy
   ```

### Migration Notes

- Database migrations are handled automatically
- Configuration file changes are documented in CHANGELOG.md
- Custom modifications should be backed up before upgrades

## API Documentation

### Authentication
All API requests require authentication via JWT tokens or session cookies.

### Endpoints
- `GET /api/health` - Health check
- `POST /api/auth/login` - User authentication
- `GET /api/users` - User management
- `POST /api/scripts` - Script execution
- `GET /api/metrics` - System metrics

### Rate Limits
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user
- Stricter limits for sensitive endpoints

## Conclusion

This deployment guide provides comprehensive instructions for setting up NoxPanel in a production environment. Follow the security best practices and maintenance procedures to ensure optimal performance and security.

For questions or issues, refer to the troubleshooting section or consult the system logs for detailed error information.
