# ContextForge MCP Server Documentation

## Overview

ContextForge is a comprehensive Model Context Protocol (MCP) server implementation designed for enterprise-grade AI model integration. It provides dynamic context analysis, intelligent routing, and seamless integration with the Heimnetz Enterprise Suite.

## Architecture

### Core Components

1. **ContextForge Server** (`context/index.py`)
   - Main MCP server implementation
   - Request processing and context analysis
   - Model compatibility checking
   - Embedding management
   - Protocol versioning

2. **Dynamic Router** (`context/router.py`)
   - Intelligent request routing
   - Load balancing and failover
   - Performance optimization
   - Health monitoring

3. **Protocol Schemas** (`context/protocols/schema.py`)
   - MCP v1.0, v1.1, v2.0 compliance
   - Message validation
   - Capability management
   - Version compatibility

4. **Service Integration** (`context/service_integration.py`)
   - Enterprise service integration
   - Health monitoring
   - Metrics collection
   - Test execution

5. **API Endpoints** (`context/api_endpoints.py`)
   - FastAPI HTTP interface
   - RESTful API endpoints
   - WebSocket support
   - Real-time updates

6. **Deployment Tools** (`context/deploy.py`)
   - Automated deployment
   - Pre-deployment checks
   - Health validation
   - Configuration management

7. **Monitoring Dashboard** (`context/monitor.py`)
   - Real-time monitoring
   - Performance visualization
   - System metrics
   - Activity tracking

## Features

### Protocol Support

- **MCP v1.0**: Basic context processing and model compatibility
- **MCP v1.1**: Enhanced routing and performance optimization
- **MCP v2.0**: Full enterprise features with monitoring and analytics

### Dynamic Routing

- **Load Balancing**: Distribute requests across available models
- **Failover**: Automatic fallback to backup models
- **Adaptive Routing**: Route based on model capabilities and load
- **Performance Monitoring**: Track and optimize routing decisions

### Context Analysis

- **Prompt Analysis**: Analyze prompt complexity and requirements
- **Model Compatibility**: Match prompts to optimal models
- **Context Embeddings**: Generate contextual embeddings for better routing
- **Complexity Assessment**: Evaluate computational requirements

### Enterprise Integration

- **Service Registry**: Centralized service configuration
- **Health Monitoring**: Continuous health and performance tracking
- **Metrics Collection**: Comprehensive metrics and analytics
- **Security**: Enterprise-grade security and access control

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Project\ Heimnetz

# Install dependencies
pip install -r requirements.txt

# Install ContextForge-specific dependencies
pip install fastapi uvicorn pydantic httpx typer loguru
```

### Configuration

1. **Service Registry**: Configure models and routing in `context/context_registry.json`
2. **Environment**: Set up environment variables for API keys and endpoints
3. **Security**: Configure authentication and authorization settings

### Deployment

```bash
# Run pre-deployment checks and deploy
python enterprise/context/deploy.py

# Alternative: Manual deployment
python -m uvicorn context.api_endpoints:app --host 0.0.0.0 --port 8000
```

### Monitoring

```bash
# Start real-time monitoring dashboard
python enterprise/context/monitor.py

# Check health via CLI
python enterprise/heimnetz_cli.py context health
```

## API Reference

### Core Endpoints

#### Context Analysis
```http
POST /context/analyze
Content-Type: application/json

{
  "prompt": "Your prompt here",
  "model_preference": "gpt-4",
  "complexity_threshold": 0.8,
  "context_sources": ["knowledge_base", "recent_conversations"],
  "max_context_length": 4000
}
```

#### Model Compatibility
```http
POST /context/compatibility
Content-Type: application/json

{
  "agent_call": "analyze_data",
  "available_models": ["gpt-4", "claude-3", "llama-2"]
}
```

#### Request Routing
```http
POST /context/route
Content-Type: application/json

{
  "request_type": "context_analysis",
  "load_factor": 0.7,
  "preferences": {
    "prefer_local": true,
    "max_latency": 1000
  }
}
```

### Monitoring Endpoints

#### Health Check
```http
GET /context/health
```

#### Metrics
```http
GET /context/metrics
```

#### Available Models
```http
GET /context/models
```

#### Supported Protocols
```http
GET /context/protocols
```

### Management Endpoints

#### Configuration
```http
GET /context/config
POST /context/config
```

#### Testing
```http
POST /context/test?test_name=basic_functionality
```

## CLI Commands

### ContextForge Management

```bash
# Get service information
python heimnetz_cli.py context info

# Check health status
python heimnetz_cli.py context health

# Run tests
python heimnetz_cli.py context test basic_functionality
python heimnetz_cli.py context test routing_performance
python heimnetz_cli.py context test integration_health

# Monitor performance
python heimnetz_cli.py context monitor
```

## Configuration

### Service Registry (`context_registry.json`)

```json
{
  "model_registry": {
    "gpt-4": {
      "type": "openai",
      "capabilities": ["text_generation", "analysis", "reasoning"],
      "max_context_length": 8192,
      "cost_per_token": 0.00003,
      "latency_ms": 800
    }
  },
  "routing_strategies": {
    "load_balanced": {
      "type": "round_robin",
      "health_check": true,
      "failover": true
    },
    "performance_optimized": {
      "type": "adaptive",
      "metrics": ["latency", "cost", "accuracy"],
      "weights": [0.4, 0.3, 0.3]
    }
  },
  "context_sources": {
    "knowledge_base": {
      "type": "vector_db",
      "endpoint": "http://localhost:6333",
      "collection": "heimnetz_knowledge"
    }
  }
}
```

### Environment Variables

```bash
# API Configuration
CONTEXTFORGE_API_HOST=0.0.0.0
CONTEXTFORGE_API_PORT=8000
CONTEXTFORGE_LOG_LEVEL=info

# Model API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
HUGGINGFACE_API_KEY=your_huggingface_key

# Database Configuration
VECTOR_DB_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_jwt_secret
API_RATE_LIMIT=100
```

## Protocol Compliance

### MCP v1.0 Features

- ✅ Basic request/response handling
- ✅ Model compatibility checking
- ✅ Simple routing
- ✅ Error handling
- ✅ Health checks

### MCP v1.1 Features

- ✅ Enhanced routing strategies
- ✅ Performance optimization
- ✅ Metrics collection
- ✅ Load balancing
- ✅ Failover support

### MCP v2.0 Features

- ✅ Real-time monitoring
- ✅ Advanced analytics
- ✅ Enterprise security
- ✅ Custom protocols
- ✅ Multi-tenant support

## Testing

### Unit Tests

```bash
# Run all tests
python -m pytest enterprise/tests/context/test_contextforge.py

# Run specific test categories
python -m pytest enterprise/tests/context/test_contextforge.py::TestContextForge
python -m pytest enterprise/tests/context/test_contextforge.py::TestRouter
python -m pytest enterprise/tests/context/test_contextforge.py::TestProtocols
```

### Integration Tests

```bash
# Test service integration
python -m pytest enterprise/tests/context/test_contextforge.py::TestServiceIntegration

# Test API endpoints
python -m pytest enterprise/tests/context/test_contextforge.py::TestAPIEndpoints
```

### Performance Tests

```bash
# Run performance benchmarks
python -m pytest enterprise/tests/context/test_contextforge.py::TestPerformance

# Load testing
python -m pytest enterprise/tests/context/test_contextforge.py::TestLoadBalancing
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8000
   
   # Kill the process or use a different port
   python -m uvicorn context.api_endpoints:app --port 8001
   ```

2. **Missing Dependencies**
   ```bash
   # Install missing packages
   pip install -r requirements.txt
   
   # Verify installation
   python -c "import fastapi, uvicorn, pydantic, httpx"
   ```

3. **Configuration Errors**
   ```bash
   # Validate configuration
   python enterprise/context/deploy.py --check-config
   
   # Reset to defaults
   python enterprise/context/deploy.py --reset-config
   ```

### Debug Mode

```bash
# Enable debug logging
export CONTEXTFORGE_LOG_LEVEL=debug

# Run with debug server
python -m uvicorn context.api_endpoints:app --reload --log-level debug
```

## Security

### Authentication

- JWT token-based authentication
- API key validation
- Rate limiting
- Request signing

### Authorization

- Role-based access control
- Resource-level permissions
- Audit logging
- Compliance tracking

### Network Security

- HTTPS/TLS encryption
- CORS configuration
- IP whitelisting
- Firewall rules

## Performance Optimization

### Caching

- Response caching
- Model result caching
- Context embedding caching
- Configuration caching

### Scaling

- Horizontal scaling with load balancers
- Vertical scaling with resource allocation
- Auto-scaling based on metrics
- Container orchestration support

### Monitoring

- Real-time performance metrics
- Error rate monitoring
- Resource utilization tracking
- Custom alerting rules

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests to ensure everything works
5. Make your changes
6. Add tests for new features
7. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints
- Write comprehensive docstrings
- Add unit tests for new functionality
- Update documentation as needed

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the troubleshooting guide
- Review the API documentation
- Contact the development team

---

*ContextForge is part of the Heimnetz Enterprise Suite - Making AI integration seamless and enterprise-ready.*
