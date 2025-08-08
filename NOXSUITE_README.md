# 🧠 NoxSuite + AI Dev Infrastructure

**The Ultimate ADHD-Friendly, AI-Powered Infrastructure Management Platform**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/noxpanel/noxsuite)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://docker.com)
[![AI](https://img.shields.io/badge/AI-powered-purple.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🎯 What is NoxSuite?

NoxSuite is a comprehensive, next-generation infrastructure management platform that combines the battle-tested reliability of Heimnetz with cutting-edge AI capabilities, modern React interfaces, and ADHD-friendly design principles.

### ✨ Key Features

🛡️ **Security-First Architecture**
- Real-time threat detection and response
- Automated security scanning and compliance
- Zero-trust network principles

🤖 **AI-Powered Automation** 
- Local LLM integration (Ollama, Mistral, Gemma)
- Visual workflow builder (Langflow)
- Intelligent system optimization
- Natural language interactions

🎨 **ADHD-Friendly Design**
- Spicy vs Steady visual modes
- Clear information hierarchy
- Reduced cognitive load
- Accessible interfaces

⚡ **Real-Time Everything**
- WebSocket-powered live updates
- Instant notifications
- Dynamic dashboards
- Progressive web app (PWA)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     🌐 Frontend Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  React UI (3000)    │  Mobile PWA (3002)  │  Grafana (3001)   │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                     🔀 API Gateway (Nginx)                     │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    ⚡ Backend Services                          │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI (8000)     │  Flask Legacy (5000) │  Worker (Celery) │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                     🤖 AI & Agent Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Ollama (11434)     │  Langflow (7860)     │  AetherCore (8001)│
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                      💾 Data Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (5432)  │  Redis (6379)       │  InfluxDB (8086)  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Interactive Installer (Recommended)

```bash
# Clone or download NoxSuite
git clone https://github.com/noxpanel/noxsuite.git
cd noxsuite

# Run the intelligent installer
python3 noxsuite-installer.py
```

The installer will:
- ✅ Auto-detect your system
- ✅ Install missing dependencies  
- ✅ Configure all services
- ✅ Download AI models
- ✅ Generate startup scripts
- ✅ Open your browser when ready

### Option 2: Quick Setup Script

```bash
# Run the setup script
./setup-noxsuite.sh

# Start services with Docker Compose
docker-compose -f docker-compose.noxsuite.yml --profile ai up -d
```

### Option 3: Manual Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start services with AI features
docker-compose -f docker-compose.noxsuite.yml --profile ai up -d

# Wait for services to initialize
sleep 60

# Install AI models
./scripts/install-models.sh
```

## 🌐 Access Points

Once installation is complete, access NoxSuite at:

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Main UI** | http://localhost:3000 | Primary React dashboard |
| 🔧 **API Docs** | http://localhost:8000/api/docs | Interactive API documentation |
| 📊 **Grafana** | http://localhost:3001 | Monitoring dashboards (admin/noxsuite123) |
| 🤖 **Langflow** | http://localhost:7860 | AI workflow builder (admin/noxsuite123) |
| 🦙 **Ollama** | http://localhost:11434 | Local LLM API |
| 📱 **Mobile PWA** | http://localhost:3002 | Mobile companion app |

## 🧩 Module Ecosystem

### Core Infrastructure Modules

#### 🛡️ **NoxGuard** (Security & Monitoring)
- Real-time threat detection
- Configuration drift monitoring  
- Vulnerability scanning
- Compliance reporting
- Automated incident response

#### 📊 **NoxPanel** (Dashboard & Control)
- Customizable drag-drop widgets
- Real-time system metrics
- ADHD-friendly themes (Spicy/Steady)
- Mobile-responsive design
- Voice command support

#### 🔍 **AutoImport** (Device Discovery)
- Automatic network scanning
- Device fingerprinting
- Unknown device alerts
- Asset inventory management
- Integration with routers/switches

#### 📈 **PowerLog** (System Health)
- Cross-platform monitoring (Windows/Linux)
- Performance metrics collection
- Uptime tracking
- Resource utilization
- Automated maintenance scheduling

### AI & Automation Modules

#### 🤖 **Langflow Hub** (Visual AI Workflows)
- Drag-drop workflow builder
- Pre-built automation templates
- Multi-model LLM integration
- Real-time flow execution
- Version control and rollback

#### 🧠 **AI Models** (Local LLM Management)
- Ollama integration
- Model download and versioning
- Performance monitoring
- Usage analytics
- Custom model deployment

#### 🧹 **AutoCleaner** (Intelligent Optimization)
- Smart file analysis and cleanup
- Disk health monitoring
- Performance optimization
- Scheduled maintenance
- OS-specific tuning

#### 🌐 **HeimnetzScanner** (Network Intelligence)
- Service discovery and mapping
- Port scanning and analysis
- Bandwidth monitoring
- Network topology visualization
- Performance testing

### System Modules

#### 🔧 **Plugin System v2**
- Hot-reloadable plugins
- Version management
- Dependency resolution
- Sandboxed execution
- Community marketplace

#### 📱 **NoxGo Mobile** (Companion App)
- React Native/PWA hybrid
- QR code quick actions
- Push notifications
- Offline functionality
- Voice interactions

#### 🔄 **Update Manager**
- Automated updates
- Dependency checking
- Staged deployments
- Health validation
- Rollback capability

## 🎛️ Management Commands

NoxSuite includes a powerful CLI tool for easy management:

```bash
# System status and health
./nox-cli.py status
./nox-cli.py health

# Service management
./nox-cli.py start
./nox-cli.py stop
./nox-cli.py restart

# AI model management
./nox-cli.py install-model mistral:7b-instruct
./nox-cli.py list-models

# Monitoring and logs
./nox-cli.py ps
./nox-cli.py logs noxsuite-api

# Backup and restore
./nox-cli.py backup --backup-name my-backup
./nox-cli.py restore my-backup

# System maintenance
./nox-cli.py update
./nox-cli.py report --output system-report.json
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Core Settings
NOXSUITE_ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/noxsuite

# AI Features
ENABLE_AI=true
ENABLE_VOICE=false
AI_MODELS=mistral:7b-instruct,gemma:7b-it

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Features
ENABLE_MOBILE=true
ENABLE_LEGACY_SUPPORT=true
```

### Docker Profiles

Use Docker Compose profiles to customize deployment:

```bash
# Minimal deployment (no AI)
docker-compose -f docker-compose.noxsuite.yml up -d

# Full AI stack
docker-compose -f docker-compose.noxsuite.yml --profile ai up -d

# Development with mobile
docker-compose -f docker-compose.noxsuite.yml --profile ai --profile mobile up -d

# Production with monitoring
docker-compose -f docker-compose.noxsuite.yml --profile ai --profile monitoring up -d
```

## 🔧 Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ 
- Node.js 18+
- 8GB+ RAM (recommended)

### Development Workflow

```bash
# Clone repository
git clone https://github.com/noxpanel/noxsuite.git
cd noxsuite

# Install development dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Frontend development
cd frontend/noxpanel-ui
npm install
npm run dev

# Backend development
cd backend/fastapi
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
npm test
```

### Code Quality

NoxSuite maintains high code quality standards:

```bash
# Format code
black .
isort .
prettier --write frontend/

# Lint code
flake8
eslint frontend/

# Type checking
mypy backend/
tsc --noEmit

# Security scanning
bandit -r backend/
npm audit
```

## 📊 Monitoring & Observability

### Built-in Monitoring

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visual dashboards and analytics
- **Health Checks**: Comprehensive service monitoring
- **Log Aggregation**: Centralized logging with rotation
- **Performance Metrics**: Real-time system resource tracking

### Custom Dashboards

Pre-configured Grafana dashboards for:
- System overview and health
- Docker container metrics
- Network performance
- AI model usage
- Security alerts
- User activity

## 🔐 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- LDAP/Active Directory integration
- OAuth2 provider support

### Network Security
- TLS encryption throughout
- Network segmentation
- Intrusion detection
- Automated threat response
- Security compliance reporting

### Data Protection
- Encryption at rest
- Secure backup procedures
- Audit logging
- Data anonymization
- Privacy controls

## 🌍 Deployment Options

### Docker Compose (Recommended)
- Single-machine deployment
- Easy configuration
- Automatic service discovery
- Volume persistence
- Health monitoring

### Kubernetes
- Multi-node clusters
- Auto-scaling
- High availability
- Advanced networking
- Enterprise features

### Manual Installation
- Custom configurations
- Legacy system support
- Development environments
- Educational purposes

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Guidelines

1. **Code Style**: Follow Black, Prettier, and ESLint configurations
2. **Testing**: Maintain >90% test coverage
3. **Documentation**: Update docs for all changes
4. **Security**: Follow secure coding practices
5. **Accessibility**: Ensure ADHD-friendly design principles

### Plugin Development

Create custom plugins using our plugin system:

```python
from noxsuite.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my-plugin", "1.0.0")
    
    async def initialize(self):
        # Plugin initialization
        pass
    
    async def process(self, data):
        # Main plugin logic
        return processed_data
```

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Detailed setup instructions
- **[API Reference](docs/API.md)**: Complete API documentation
- **[Plugin Development](docs/PLUGINS.md)**: Creating custom plugins
- **[Configuration Guide](docs/CONFIG.md)**: Advanced configuration
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Architecture Deep Dive](NOXSUITE_ARCHITECTURE.md)**: Technical architecture

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker status
docker info

# Check logs
./nox-cli.py logs noxsuite-api

# Restart services
./nox-cli.py restart
```

**AI models not loading:**
```bash
# Check Ollama status
curl http://localhost:11434/api/version

# Reinstall models
./scripts/install-models.sh

# Check model status
./nox-cli.py list-models
```

**Frontend not accessible:**
```bash
# Check if React dev server is running
docker logs noxsuite-ui

# Verify network connectivity
curl http://localhost:3000
```

## 📞 Support

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/noxpanel/noxsuite/issues)
- **Discussions**: [Community support and questions](https://github.com/noxpanel/noxsuite/discussions)
- **Documentation**: [Comprehensive guides and tutorials](https://docs.noxsuite.com)
- **Discord**: [Real-time community chat](https://discord.gg/noxsuite)

## 📜 License

NoxSuite is released under the [MIT License](LICENSE). See the LICENSE file for details.

## 🙏 Acknowledgments

NoxSuite builds upon excellent open-source projects:

- **React & Next.js**: Modern web framework
- **FastAPI**: High-performance Python API framework
- **Docker**: Containerization platform
- **Ollama**: Local LLM serving
- **Langflow**: Visual AI workflow builder
- **Prometheus & Grafana**: Monitoring stack
- **PostgreSQL**: Reliable database
- **Redis**: High-performance caching

Special thanks to the ADHD community for inspiring accessible design principles.

---

**Built with ♥️ for developers and system administrators who value intelligent automation, beautiful design, and cognitive accessibility.**

## 🗺️ Roadmap

### v2.1 (Q2 2024)
- [ ] Enhanced mobile app with React Native
- [ ] Advanced AI model fine-tuning
- [ ] Kubernetes operator
- [ ] Enterprise SSO integration

### v2.2 (Q3 2024)
- [ ] Multi-tenant architecture
- [ ] Advanced analytics and reporting
- [ ] Custom workflow templates
- [ ] Plugin marketplace

### v2.3 (Q4 2024)
- [ ] Edge computing support
- [ ] Advanced AI reasoning
- [ ] Integration ecosystem
- [ ] Cloud deployment options

---

🧠 **NoxSuite - Where Intelligence Meets Infrastructure**
