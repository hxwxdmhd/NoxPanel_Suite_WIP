#!/usr/bin/env bash
# Docker Network Diagnostics and Fix Script
# Part of Ultimate Suite v11.0

set -e

echo "🔧 Docker Network Diagnostics and Redis Fix Script"
echo "=" * 60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️ $1"
}

# Check if Docker is installed
check_docker() {
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed"
        exit 1
    fi
}

# Check if Docker Compose is installed
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is installed"
        docker-compose --version
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
}

# Check Docker daemon
check_docker_daemon() {
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        exit 1
    fi
}

# List Docker networks
list_networks() {
    print_info "Listing Docker networks..."
    docker network ls
}

# Check port availability
check_ports() {
    print_info "Checking port availability..."
    
    ports=(5000 5001 5002 5003 6379 6380 3000 8081 9090)
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            print_warning "Port $port is occupied"
        else
            print_success "Port $port is available"
        fi
    done
}

# Test Redis connectivity
test_redis_connectivity() {
    print_info "Testing Redis connectivity..."
    
    # Test different Redis configurations
    redis_hosts=("localhost" "127.0.0.1" "host.docker.internal" "172.17.0.1")
    redis_ports=(6379 6380)
    
    for host in "${redis_hosts[@]}"; do
        for port in "${redis_ports[@]}"; do
            if timeout 3 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
                print_success "Redis connection successful: $host:$port"
            else
                print_warning "Redis connection failed: $host:$port"
            fi
        done
    done
}

# Start Redis development stack
start_redis_stack() {
    print_info "Starting Redis development stack..."
    
    if [ -f "docker-compose.dev-networking.yml" ]; then
        docker-compose -f docker-compose.dev-networking.yml up -d redis-dev redis-commander
        print_success "Redis development stack started"
    else
        print_error "docker-compose.dev-networking.yml not found"
        
        # Create minimal Redis container
        print_info "Creating minimal Redis container..."
        docker run -d \
            --name heimnetz-redis-dev \
            -p 6379:6379 \
            -e REDIS_PASSWORD=dev_redis_password \
            redis:7-alpine \
            redis-server --requirepass dev_redis_password
        
        print_success "Minimal Redis container created"
    fi
}

# Stop Redis stack
stop_redis_stack() {
    print_info "Stopping Redis development stack..."
    
    if [ -f "docker-compose.dev-networking.yml" ]; then
        docker-compose -f docker-compose.dev-networking.yml down
    fi
    
    # Stop individual containers
    docker stop heimnetz-redis-dev 2>/dev/null || true
    docker rm heimnetz-redis-dev 2>/dev/null || true
    
    print_success "Redis development stack stopped"
}

# Create development network
create_dev_network() {
    print_info "Creating development network..."
    
    # Remove existing network if it exists
    docker network rm heimnetz-dev-network 2>/dev/null || true
    
    # Create new network
    docker network create \
        --driver bridge \
        --subnet 172.28.0.0/16 \
        --gateway 172.28.0.1 \
        heimnetz-dev-network
    
    print_success "Development network created"
}

# Test network connectivity
test_network_connectivity() {
    print_info "Testing network connectivity..."
    
    # Start a test container
    docker run --rm -d \
        --name network-test \
        --network heimnetz-dev-network \
        alpine:latest \
        sh -c "apk add --no-cache curl && tail -f /dev/null"
    
    # Test connectivity
    sleep 5
    
    if docker exec network-test ping -c 1 google.com &> /dev/null; then
        print_success "External connectivity works"
    else
        print_warning "External connectivity issues"
    fi
    
    # Clean up
    docker stop network-test 2>/dev/null || true
}

# Fix Docker networking issues
fix_networking() {
    print_info "Fixing Docker networking issues..."
    
    # Stop existing containers
    stop_redis_stack
    
    # Create development network
    create_dev_network
    
    # Start Redis stack
    start_redis_stack
    
    # Test connectivity
    sleep 10
    test_redis_connectivity
    
    print_success "Docker networking fixes applied"
}

# Run diagnostics
run_diagnostics() {
    print_info "Running comprehensive diagnostics..."
    
    check_docker
    check_docker_compose
    check_docker_daemon
    list_networks
    check_ports
    test_redis_connectivity
    
    print_success "Diagnostics complete"
}

# Main menu
show_menu() {
    echo ""
    echo "🔧 Docker Network Diagnostics Menu"
    echo "=================================="
    echo "1. Run diagnostics"
    echo "2. Fix networking issues"
    echo "3. Start Redis stack"
    echo "4. Stop Redis stack"
    echo "5. Test Redis connectivity"
    echo "6. Create development network"
    echo "7. Test network connectivity"
    echo "8. Exit"
    echo ""
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select option (1-8): " choice
            
            case $choice in
                1) run_diagnostics ;;
                2) fix_networking ;;
                3) start_redis_stack ;;
                4) stop_redis_stack ;;
                5) test_redis_connectivity ;;
                6) create_dev_network ;;
                7) test_network_connectivity ;;
                8) echo "Goodbye!"; exit 0 ;;
                *) print_error "Invalid option" ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            "diagnostics") run_diagnostics ;;
            "fix") fix_networking ;;
            "start") start_redis_stack ;;
            "stop") stop_redis_stack ;;
            "test") test_redis_connectivity ;;
            "network") create_dev_network ;;
            "connectivity") test_network_connectivity ;;
            *) 
                echo "Usage: $0 [diagnostics|fix|start|stop|test|network|connectivity]"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
