# Heimnetz (NoxGuard/NoxPanel) 🛡️

[![Code Quality](https://github.com/noxpanel/heimnetz/workflows/Code%20Quality%20Checks/badge.svg)](https://github.com/noxpanel/heimnetz/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Comprehensive ADHD-friendly network management and monitoring system with AI-powered automation and microservices architecture.**

## 🚀 Recent Major Overhaul (2025)

The entire codebase has undergone a comprehensive overhaul with significant improvements:

- ✅ **All critical syntax errors fixed** (reduced from 199+ to 0)
- ✅ **Deprecated patterns updated** (datetime handling, imports)
- ✅ **Code quality tools enhanced** with better analysis
- ✅ **65+ empty files archived** for better organization  
- ✅ **Structured logging implemented** throughout
- ✅ **CI/CD pipeline improved** with automated quality checks

## 🏗️ Architecture

**Microservices-based system** deployed via Docker Compose:

- **Heimnetz Core**: Main Flask application (web interface, core functionality)
- **AetherCore MSP Server**: AI/ML processing for intelligent network analysis
- **ContextForge MCP Server**: Knowledge management and context processing
- **Redis**: Caching and session management
- **PostgreSQL**: Advanced data storage (enterprise features)
- **Ollama**: Local AI model serving (9 different models supported)
- **Nginx**: Reverse proxy and load balancer
- **Prometheus/Grafana**: Monitoring and observability

## 🎯 Key Features

### Network Management
- **ADHD-Friendly Interface**: Specialized design for users with ADHD
- **Real-time Monitoring**: Network devices, bandwidth, security
- **FritzBox Integration**: Deep integration with AVM FritzBox routers
- **Plugin Ecosystem**: Extensible architecture for custom functionality

### AI & Automation
- **9 AI Models**: PyTorch, Transformers, Ollama integration
- **Voice Interface**: Speech recognition and text-to-speech
- **Intelligent Analysis**: Automated network pattern recognition
- **Context-Aware Responses**: Smart assistance based on network state

### Enterprise Features
- **Multi-Tenancy**: Resource isolation for multiple organizations
- **Advanced Analytics**: Comprehensive reporting and dashboards  
- **Security Scanning**: Built-in vulnerability assessment
- **Compliance Reporting**: Audit trails and compliance dashboards

## 🛠️ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for development)
- 8GB+ RAM recommended
- Modern web browser

### Production Deployment
```bash
# Clone repository
git clone https://github.com/noxpanel/heimnetz.git
cd heimnetz

# Start production stack
docker-compose -f docker-compose.production.yml up -d

# Access web interface
open http://localhost
```

### Development Setup
```bash
# Install dependencies
pip install -e .[dev,ai]

# Install pre-commit hooks
pre-commit install

# Run code analysis
python run_code_analysis.py

# Start development server
cd NoxPanel
python -m flask run --debug
```

## 📊 Code Quality

The project maintains high code quality standards:

```bash
# Run comprehensive analysis
python run_code_analysis.py --only-active

# Format code
black .
isort .

# Security scan
bandit -r NoxPanel/

# Type checking
mypy NoxPanel/
```

## 🔧 Configuration

### Environment Variables
```bash
# Core settings
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/noxpanel

# Redis
REDIS_URL=redis://localhost:6379

# AI Features
OLLAMA_HOST=http://localhost:11434
ENABLE_VOICE_INTERFACE=true

# Enterprise
ENABLE_MULTI_TENANT=true
LDAP_SERVER=ldap://your-ldap-server
```

### Plugin Development
```python
from NoxPanel.noxcore.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my-plugin", "1.0.0")
    
    def initialize(self):
        # Plugin initialization
        pass
    
    def process(self, data):
        # Main plugin logic
        return processed_data
```

## 📁 Project Structure

```
heimnetz/
├── NoxPanel/                 # Core application
│   ├── noxcore/             # Core modules
│   │   ├── utils/           # Utility modules
│   │   ├── database.py      # Database layer
│   │   └── migrations.py    # Schema migrations
│   ├── webpanel/            # Web interface
│   └── tests/               # Test suite
├── aethercore/              # AI processing server
├── dashboard/               # Monitoring dashboards
├── docker/                  # Docker configurations
├── .github/workflows/       # CI/CD pipelines
├── archive/                 # Archived code
└── run_code_analysis.py     # Code quality tool
```

## 🧪 Testing

```bash
# Run test suite
pytest NoxPanel/tests/

# With coverage
pytest --cov=NoxPanel --cov-report=html

# Integration tests
pytest -m integration

# Performance tests
pytest -m slow
```

## 🚀 Deployment Options

### Docker Compose (Recommended)
- **Simple**: `docker-compose.yml` (basic setup)
- **Production**: `docker-compose.production.yml` (full stack)
- **Development**: `docker-compose.dev.yml` (development mode)

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n noxpanel
```

### Manual Installation
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 📚 Documentation

- **[API Documentation](docs/API.md)**: REST API reference
- **[Plugin Development](docs/PLUGINS.md)**: Creating custom plugins
- **[Configuration Guide](docs/CONFIG.md)**: Detailed configuration options
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run code quality checks
5. Submit a pull request

### Code Standards
- **Black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

## 📈 Performance

- **Lightweight**: Optimized Docker images
- **Scalable**: Microservices architecture
- **Efficient**: Connection pooling, caching
- **Monitored**: Prometheus metrics, health checks

## 🔐 Security

- **Security Scanning**: Automated with Bandit
- **Dependency Checks**: Safety integration
- **Input Validation**: Comprehensive sanitization
- **Authentication**: LDAP/OAuth2 support
- **Encryption**: TLS/SSL throughout

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AVM FritzBox**: Router integration
- **Flask**: Web framework
- **Docker**: Containerization
- **Prometheus**: Monitoring
- **Ollama**: AI model serving

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/noxpanel/heimnetz/issues)
- **Discussions**: [Community support](https://github.com/noxpanel/heimnetz/discussions)
- **Documentation**: [Wiki](https://github.com/noxpanel/heimnetz/wiki)

---

**Built with ♥️ for network administrators who need ADHD-friendly tools and intelligent automation.**
