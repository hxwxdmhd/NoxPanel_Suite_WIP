# AetherCore MSP Server Integration

## Overview

AetherCore MSP (Model Serving Protocol) Server is a comprehensive model serving platform integrated with the Heimnetz Enterprise Suite. It provides efficient model loading, inference processing, and management capabilities for AI/ML models.

## Features

### Core Capabilities
- **Multi-Model Support**: Transformer, ONNX, PyTorch models
- **Async Processing**: Non-blocking model operations
- **Model Management**: Dynamic loading/unloading
- **Inference Serving**: REST API for model inference
- **Health Monitoring**: Comprehensive health checks
- **Performance Metrics**: Real-time performance tracking
- **Memory Management**: Efficient resource utilization
- **GPU Acceleration**: CUDA support for compatible models

### Enterprise Features
- **Docker Integration**: Containerized deployment
- **Service Discovery**: Automatic service registration
- **Load Balancing**: Distributed request handling
- **Monitoring**: Prometheus metrics integration
- **Logging**: Structured logging with Loguru
- **Security**: Enterprise-grade security features
- **CLI Management**: Rich CLI interface
- **WebSocket Support**: Real-time streaming inference

## Architecture

```
AetherCore MSP Server
├── Core Server (index.py)
│   ├── FastAPI application
│   ├── Health monitoring
│   ├── Metrics collection
│   └── Request routing
├── Model Service (model_service.py)
│   ├── Model loading/unloading
│   ├── Memory management
│   ├── Performance tracking
│   └── Health monitoring
├── Inference Service (inference_service.py)
│   ├── Request processing
│   ├── Batch inference
│   ├── Streaming responses
│   └── Error handling
├── API Routes
│   ├── Model management (models.py)
│   ├── Inference serving (serve.py)
│   └── System monitoring
└── Docker Integration
    ├── Multi-service orchestration
    ├── Health checks
    ├── Resource management
    └── Service discovery
```

## Installation

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- CUDA (optional, for GPU acceleration)

### Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configurations
```

3. Start services:
```bash
docker-compose up -d
```

## Usage

### CLI Commands

#### System Status
```bash
# Overall system status
python heimnetz_cli.py system status

# Service health check
python heimnetz_cli.py system health

# Detailed service information
python heimnetz_cli.py system services
```

#### AetherCore Management
```bash
# AetherCore status
python heimnetz_cli.py aethercore info

# Health check
python heimnetz_cli.py aethercore health

# List available models
python heimnetz_cli.py aethercore models

# Load a model
python heimnetz_cli.py aethercore load <model_id>

# Unload a model
python heimnetz_cli.py aethercore unload <model_id>

# Serve inference request
python heimnetz_cli.py aethercore serve <model_id> --text "Your input text"
```

#### ContextForge Management
```bash
# ContextForge status
python heimnetz_cli.py context info

# Health check
python heimnetz_cli.py context health

# Run tests
python heimnetz_cli.py context test <test_name>
```

### API Endpoints

#### Core Endpoints
- `GET /health` - Health check
- `GET /heartbeat` - Service heartbeat
- `GET /metrics` - Performance metrics
- `GET /models` - List available models

#### Model Management
- `POST /models/{model_id}/load` - Load a model
- `POST /models/{model_id}/unload` - Unload a model
- `GET /models/{model_id}/status` - Get model status
- `GET /models/{model_id}/info` - Get model information

#### Inference Serving
- `POST /serve` - Serve inference request
- `POST /serve/batch` - Batch inference
- `WS /serve/stream` - Streaming inference

### Direct API Usage

#### Load a Model
```bash
curl -X POST "http://localhost:8001/models/bert-base-uncased/load"
```

#### Serve Inference
```bash
curl -X POST "http://localhost:8001/serve" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "bert-base-uncased",
    "inputs": {"text": "Hello world"},
    "parameters": {"max_length": 100}
  }'
```

#### Check Health
```bash
curl "http://localhost:8001/health"
```

## Configuration

### Environment Variables
- `AETHERCORE_HOST` - Server host (default: 0.0.0.0)
- `AETHERCORE_PORT` - Server port (default: 8001)
- `AETHERCORE_WORKERS` - Number of workers (default: 1)
- `AETHERCORE_LOG_LEVEL` - Log level (default: INFO)
- `AETHERCORE_REDIS_URL` - Redis connection URL
- `AETHERCORE_GPU_ENABLED` - Enable GPU acceleration (default: auto)
- `AETHERCORE_MODEL_CACHE_SIZE` - Model cache size (default: 1GB)

### Model Configuration
Models are configured in `aethercore/config/models.yaml`:

```yaml
models:
  bert-base-uncased:
    name: "BERT Base Uncased"
    model_type: "transformer"
    source: "huggingface"
    model_path: "bert-base-uncased"
    device: "auto"
    max_memory: "1GB"
    
  custom-onnx-model:
    name: "Custom ONNX Model"
    model_type: "onnx"
    source: "local"
    model_path: "/path/to/model.onnx"
    device: "cpu"
    providers: ["CPUExecutionProvider"]
```

## Docker Deployment

### Single Service
```bash
docker run -d \
  --name aethercore \
  -p 8001:8001 \
  -e AETHERCORE_HOST=0.0.0.0 \
  -e AETHERCORE_PORT=8001 \
  heimnetz/aethercore:latest
```

### Multi-Service Stack
```bash
docker-compose up -d
```

## Development

### Running Tests
```bash
# Run all tests
pytest tests/aethercore/

# Run specific test file
pytest tests/aethercore/test_aethercore.py

# Run with coverage
pytest --cov=aethercore tests/aethercore/
```

### Code Quality
```bash
# Format code
black aethercore/

# Type checking
mypy aethercore/

# Linting
flake8 aethercore/
```

## Performance Optimization

### Model Loading
- Use model caching for frequently accessed models
- Implement lazy loading for large models
- Optimize memory usage with model quantization

### Inference Processing
- Batch requests for improved throughput
- Use async processing for concurrent requests
- Implement request queuing for high load

### System Resources
- Monitor memory usage and implement garbage collection
- Use GPU acceleration when available
- Optimize Docker resource allocation

## Monitoring and Logging

### Metrics
AetherCore exposes Prometheus metrics:
- `aethercore_requests_total` - Total requests
- `aethercore_request_duration_seconds` - Request duration
- `aethercore_model_memory_usage_bytes` - Model memory usage
- `aethercore_active_models` - Number of active models

### Logging
Structured logging with Loguru:
- Request/response logging
- Error tracking
- Performance metrics
- System health monitoring

### Health Checks
- Service health endpoint
- Model health monitoring
- Resource utilization tracking
- Dependency health checks

## Security

### Authentication
- API key authentication
- JWT token support
- Role-based access control

### Data Protection
- Input validation
- Output sanitization
- Secure model storage
- Encrypted communications

## Troubleshooting

### Common Issues

#### Model Loading Failures
```bash
# Check model configuration
python heimnetz_cli.py aethercore models

# Verify model path and permissions
ls -la /path/to/model

# Check system resources
python heimnetz_cli.py system status
```

#### Performance Issues
```bash
# Check system metrics
python heimnetz_cli.py aethercore info

# Monitor resource usage
docker stats aethercore

# Check logs
docker logs aethercore
```

#### Connection Issues
```bash
# Verify service status
python heimnetz_cli.py aethercore health

# Check network connectivity
curl http://localhost:8001/health

# Verify Docker networking
docker network ls
```

## Integration Examples

### Python Client
```python
import httpx
import asyncio

async def serve_inference():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/serve",
            json={
                "model_id": "bert-base-uncased",
                "inputs": {"text": "Hello world"},
                "parameters": {"max_length": 100}
            }
        )
        return response.json()

result = asyncio.run(serve_inference())
print(result)
```

### JavaScript Client
```javascript
const response = await fetch('http://localhost:8001/serve', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model_id: 'bert-base-uncased',
    inputs: { text: 'Hello world' },
    parameters: { max_length: 100 }
  })
});

const result = await response.json();
console.log(result);
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## Support

For support, please contact the development team or create an issue in the project repository.
