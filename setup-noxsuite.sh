#!/bin/bash

# NoxSuite + AI Dev Infrastructure - Quick Setup Script
# Cross-platform setup for the complete NoxSuite ecosystem

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                    🧠 NoxSuite + AI Dev Infrastructure            ║
║                        Intelligent Auto-Setup                    ║
╠═══════════════════════════════════════════════════════════════════╣
║  • ADHD-Friendly Design      • AI-Powered Automation            ║
║  • Cross-Platform Support    • Self-Healing Infrastructure      ║
║  • Docker-Native Deployment  • Local LLM Integration            ║
║  • Modular Architecture      • Real-time Monitoring             ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            OS="ubuntu"
        elif command_exists yum; then
            OS="centos"
        elif command_exists dnf; then
            OS="fedora"
        elif command_exists pacman; then
            OS="arch"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    
    print_status "Detected OS: $OS"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check for Docker
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker found: $DOCKER_VERSION"
    else
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check for Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose found"
    else
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Check for Python 3.10+
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_warning "Python 3 not found. Some features may not work."
    fi
    
    # Check for Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js found: $NODE_VERSION"
    else
        print_warning "Node.js not found. Frontend features may not work."
    fi
    
    # Check available memory (Linux)
    if [[ "$OS" == "linux" ]] || [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "centos" ]] || [[ "$OS" == "fedora" ]]; then
        MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
        if [ "$MEMORY_GB" -lt 4 ]; then
            print_warning "Low memory detected: ${MEMORY_GB}GB. Recommend 8GB+ for optimal performance."
        else
            print_success "Memory check passed: ${MEMORY_GB}GB"
        fi
    fi
}

# Install dependencies based on OS
install_dependencies() {
    print_status "Installing system dependencies..."
    
    case $OS in
        ubuntu)
            sudo apt-get update
            sudo apt-get install -y curl wget git make build-essential
            ;;
        centos|fedora)
            if command_exists dnf; then
                sudo dnf install -y curl wget git make gcc gcc-c++
            else
                sudo yum install -y curl wget git make gcc gcc-c++
            fi
            ;;
        macos)
            if command_exists brew; then
                brew install curl wget git make
            else
                print_warning "Homebrew not found. Please install dependencies manually."
            fi
            ;;
        *)
            print_warning "Unknown OS. Please ensure curl, wget, git, and make are installed."
            ;;
    esac
}

# Create directory structure
setup_directories() {
    print_status "Setting up directory structure..."
    
    # Create main directories
    mkdir -p frontend/noxpanel-ui/{components,pages,hooks,lib,types,styles,public}
    mkdir -p frontend/noxgo-mobile/{src,public}
    mkdir -p backend/fastapi/{routers,core,models,services,utils}
    mkdir -p backend/flask-legacy
    mkdir -p services/{langflow,ollama}
    mkdir -p data/{postgres,redis,logs,ollama,langflow,grafana,prometheus}
    mkdir -p config/{nginx,grafana,prometheus,langflow}
    mkdir -p scripts
    mkdir -p plugins
    mkdir -p backups
    mkdir -p ssl
    mkdir -p sql
    
    print_success "Directory structure created"
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Create main .env file
    cat > .env << EOF
# NoxSuite Configuration
NOXSUITE_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:noxsuite123@localhost:5432/noxsuite
POSTGRES_PASSWORD=noxsuite123

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# AI Configuration
ENABLE_AI=true
ENABLE_VOICE=false
OLLAMA_HOST=http://localhost:11434
AI_MODELS=mistral:7b-instruct,gemma:7b-it

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=noxsuite123
LANGFLOW_PASSWORD=noxsuite123

# Logging
LOG_LEVEL=INFO
LOG_FILE=data/logs/noxsuite.log

# Feature Flags
ENABLE_MOBILE=true
ENABLE_LEGACY_SUPPORT=true
ENABLE_EXPERIMENTAL_FEATURES=true
EOF
    
    print_success "Environment configuration created"
}

# Setup Docker configuration
setup_docker() {
    print_status "Setting up Docker configuration..."
    
    # Copy Docker Compose file
    if [ -f "docker-compose.noxsuite.yml" ]; then
        print_success "Docker Compose configuration found"
    else
        print_error "Docker Compose configuration missing!"
        exit 1
    fi
    
    # Create Docker network
    docker network create noxsuite-network 2>/dev/null || print_warning "Network already exists"
    
    print_success "Docker configuration ready"
}

# Setup Nginx configuration
setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    mkdir -p config/nginx/conf.d
    
    cat > config/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Upstream servers
    upstream noxsuite_ui {
        server noxpanel-ui:3000;
    }
    
    upstream noxsuite_api {
        server noxsuite-api:8000;
    }
    
    upstream grafana {
        server grafana:3000;
    }
    
    # Main server block
    server {
        listen 80;
        server_name localhost;
        client_max_body_size 100M;
        
        # Frontend
        location / {
            proxy_pass http://noxsuite_ui;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://noxsuite_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket
        location /ws/ {
            proxy_pass http://noxsuite_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Grafana
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    print_success "Nginx configuration created"
}

# Setup database initialization
setup_database() {
    print_status "Setting up database initialization..."
    
    cat > sql/init.sql << 'EOF'
-- NoxSuite Database Initialization

-- Create databases
CREATE DATABASE IF NOT EXISTS noxsuite;
CREATE DATABASE IF NOT EXISTS langflow;

-- Create users
CREATE USER IF NOT EXISTS 'noxsuite'@'%' IDENTIFIED BY 'noxsuite123';
GRANT ALL PRIVILEGES ON noxsuite.* TO 'noxsuite'@'%';
GRANT ALL PRIVILEGES ON langflow.* TO 'noxsuite'@'%';

FLUSH PRIVILEGES;
EOF
    
    cat > sql/noxsuite-schema.sql << 'EOF'
-- NoxSuite Database Schema

-- System tables
CREATE TABLE IF NOT EXISTS system_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    health_score INTEGER DEFAULT 0,
    active_services INTEGER DEFAULT 0,
    total_services INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users and authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices and network inventory
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    device_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'unknown',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security alerts
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT NOT NULL,
    source VARCHAR(255),
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- System logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI models
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(100),
    status VARCHAR(50) DEFAULT 'inactive',
    model_type VARCHAR(100),
    size_mb INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created ON security_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
EOF
    
    print_success "Database configuration created"
}

# Install Python dependencies
install_python_deps() {
    if command_exists python3 && command_exists pip3; then
        print_status "Installing Python dependencies..."
        
        cat > requirements.txt << 'EOF'
# NoxSuite Backend Dependencies
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9
redis>=5.0.1
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
websockets>=12.0
httpx>=0.25.2
prometheus-client>=0.19.0
pyyaml>=6.0.1
click>=8.1.7
rich>=13.7.0
python-dotenv>=1.0.0

# AI Dependencies
ollama>=0.1.7
langchain>=0.0.350
langchain-community>=0.0.2

# Monitoring
psutil>=5.9.6
docker>=6.1.3

# Development
pytest>=7.4.3
pytest-asyncio>=0.21.1
black>=23.11.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.7.1
EOF
        
        # Install in virtual environment if possible
        if command_exists python3 -m venv; then
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
            print_success "Python dependencies installed in virtual environment"
        else
            pip3 install -r requirements.txt
            print_success "Python dependencies installed globally"
        fi
    else
        print_warning "Python/pip not found. Skipping Python dependencies."
    fi
}

# Install Node.js dependencies
install_node_deps() {
    if command_exists node && command_exists npm; then
        print_status "Installing Node.js dependencies for frontend..."
        
        cd frontend/noxpanel-ui
        if [ -f "package.json" ]; then
            npm install
            print_success "Frontend dependencies installed"
        else
            print_warning "Frontend package.json not found"
        fi
        cd ../..
    else
        print_warning "Node.js/npm not found. Skipping frontend dependencies."
    fi
}

# Create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Linux/Mac startup script
    cat > scripts/start-noxsuite.sh << 'EOF'
#!/bin/bash

echo "🧠 Starting NoxSuite + AI Dev Infrastructure..."
echo "================================================"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.noxsuite.yml --profile ai up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Install AI models if enabled
if [ "$ENABLE_AI" = "true" ]; then
    echo "🤖 Installing AI models..."
    bash scripts/install-models.sh
fi

echo "✅ NoxSuite is starting up!"
echo "🌐 Web UI: http://localhost:3000"
echo "🔧 API Docs: http://localhost:8000/api/docs"
echo "📊 Grafana: http://localhost:3001"
if [ "$ENABLE_AI" = "true" ]; then
    echo "🤖 Langflow: http://localhost:7860"
    echo "🦙 Ollama: http://localhost:11434"
fi

# Open browser if available
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
fi

echo "Press Ctrl+C to stop services..."
EOF
    
    chmod +x scripts/start-noxsuite.sh
    
    # Windows startup script
    cat > scripts/start-noxsuite.bat << 'EOF'
@echo off
echo 🧠 Starting NoxSuite + AI Dev Infrastructure...
echo ================================================

echo 🐳 Starting Docker services...
docker-compose -f docker-compose.noxsuite.yml --profile ai up -d

echo ⏳ Waiting for services to initialize...
timeout /t 30 /nobreak > nul

echo 🤖 Installing AI models...
call scripts\install-models.bat

echo ✅ NoxSuite is starting up!
echo 🌐 Web UI: http://localhost:3000
echo 🔧 API Docs: http://localhost:8000/api/docs
echo 📊 Grafana: http://localhost:3001
echo 🤖 Langflow: http://localhost:7860
echo 🦙 Ollama: http://localhost:11434

start http://localhost:3000

pause
EOF
    
    # Stop script
    cat > scripts/stop-noxsuite.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping NoxSuite services..."
docker-compose -f docker-compose.noxsuite.yml down
echo "✅ Services stopped"
EOF
    
    chmod +x scripts/stop-noxsuite.sh
    
    # Model installation script
    cat > scripts/install-models.sh << 'EOF'
#!/bin/bash

echo "🤖 Installing AI models for NoxSuite..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama service..."
while ! curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 2
done

echo "✅ Ollama is ready, installing models..."

# Install default models
echo "📦 Installing mistral:7b-instruct..."
docker exec noxsuite-ollama ollama pull mistral:7b-instruct

echo "📦 Installing gemma:7b-it..."
docker exec noxsuite-ollama ollama pull gemma:7b-it

echo "🧪 Testing model installation..."
docker exec noxsuite-ollama ollama run mistral:7b-instruct "Hello, this is a test." --timeout 30

echo "🎉 AI model installation complete!"
EOF
    
    chmod +x scripts/install-models.sh
    
    print_success "Startup scripts created"
}

# Create CLI tool
create_cli() {
    print_status "Setting up CLI tool..."
    
    # Make CLI executable
    if [ -f "nox-cli.py" ]; then
        chmod +x nox-cli.py
        
        # Create symlink for easy access
        if [ -w "/usr/local/bin" ]; then
            ln -sf "$(pwd)/nox-cli.py" /usr/local/bin/nox 2>/dev/null || true
        fi
        
        print_success "CLI tool configured (use ./nox-cli.py or nox)"
    else
        print_warning "CLI tool not found"
    fi
}

# Validate installation
validate_installation() {
    print_status "Validating installation..."
    
    # Check required files
    required_files=(
        "docker-compose.noxsuite.yml"
        ".env"
        "scripts/start-noxsuite.sh"
        "config/nginx/nginx.conf"
        "sql/noxsuite-schema.sql"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✓ $file"
        else
            print_error "✗ $file missing"
        fi
    done
    
    # Check Docker
    if docker info > /dev/null 2>&1; then
        print_success "✓ Docker is running"
    else
        print_error "✗ Docker is not running"
    fi
    
    print_success "Installation validation complete"
}

# Main installation function
main() {
    echo -e "${CYAN}Starting NoxSuite installation...${NC}\n"
    
    detect_os
    check_requirements
    install_dependencies
    setup_directories
    setup_environment
    setup_docker
    setup_nginx
    setup_database
    install_python_deps
    install_node_deps
    create_startup_scripts
    create_cli
    validate_installation
    
    echo
    print_success "🎉 NoxSuite installation completed successfully!"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Start NoxSuite: ${GREEN}./scripts/start-noxsuite.sh${NC}"
    echo "2. Access Web UI: ${BLUE}http://localhost:3000${NC}"
    echo "3. Check API docs: ${BLUE}http://localhost:8000/api/docs${NC}"
    echo "4. Monitor with Grafana: ${BLUE}http://localhost:3001${NC}"
    echo
    echo -e "${PURPLE}For help: ./nox-cli.py --help${NC}"
    echo
}

# Run main function
main "$@"
