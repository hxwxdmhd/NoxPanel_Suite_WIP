# Docker Network Diagnostics and Fix Script (PowerShell)
# Part of Ultimate Suite v11.0

param(
    [string]$Action = "menu"
)

# Colors for output
$RED = "`e[31m"
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$NC = "`e[0m"

function Print-Success($message) {
    Write-Host "$GREEN✅ $message$NC" -ForegroundColor Green
}

function Print-Warning($message) {
    Write-Host "$YELLOW⚠️ $message$NC" -ForegroundColor Yellow
}

function Print-Error($message) {
    Write-Host "$RED❌ $message$NC" -ForegroundColor Red
}

function Print-Info($message) {
    Write-Host "ℹ️ $message" -ForegroundColor Cyan
}

# Check if Docker is installed
function Test-Docker {
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Print-Success "Docker is installed: $dockerVersion"
            return $true
        } else {
            Print-Error "Docker is not installed"
            return $false
        }
    } catch {
        Print-Error "Docker is not installed or not in PATH"
        return $false
    }
}

# Check if Docker Compose is installed
function Test-DockerCompose {
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Print-Success "Docker Compose is installed: $composeVersion"
            return $true
        } else {
            Print-Error "Docker Compose is not installed"
            return $false
        }
    } catch {
        Print-Error "Docker Compose is not installed or not in PATH"
        return $false
    }
}

# Check Docker daemon
function Test-DockerDaemon {
    try {
        $dockerInfo = docker info 2>$null
        if ($dockerInfo) {
            Print-Success "Docker daemon is running"
            return $true
        } else {
            Print-Error "Docker daemon is not running"
            return $false
        }
    } catch {
        Print-Error "Cannot connect to Docker daemon"
        return $false
    }
}

# List Docker networks
function Get-DockerNetworks {
    Print-Info "Listing Docker networks..."
    try {
        docker network ls
        Print-Success "Docker networks listed"
    } catch {
        Print-Error "Failed to list Docker networks"
    }
}

# Check port availability
function Test-PortAvailability {
    Print-Info "Checking port availability..."
    
    $ports = @(5000, 5001, 5002, 5003, 6379, 6380, 3000, 8081, 9090)
    
    foreach ($port in $ports) {
        try {
            $connection = Test-NetConnection -ComputerName "localhost" -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($connection) {
                Print-Warning "Port $port is occupied"
            } else {
                Print-Success "Port $port is available"
            }
        } catch {
            Print-Success "Port $port is available"
        }
    }
}

# Test Redis connectivity
function Test-RedisConnectivity {
    Print-Info "Testing Redis connectivity..."
    
    $redisHosts = @("localhost", "127.0.0.1", "host.docker.internal", "172.17.0.1")
    $redisPorts = @(6379, 6380)
    
    foreach ($host in $redisHosts) {
        foreach ($port in $redisPorts) {
            try {
                $connection = Test-NetConnection -ComputerName $host -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
                if ($connection) {
                    Print-Success "Redis connection successful: $host`:$port"
                } else {
                    Print-Warning "Redis connection failed: $host`:$port"
                }
            } catch {
                Print-Warning "Redis connection failed: $host`:$port"
            }
        }
    }
}

# Start Redis development stack
function Start-RedisStack {
    Print-Info "Starting Redis development stack..."
    
    if (Test-Path "docker-compose.dev-networking.yml") {
        try {
            docker-compose -f docker-compose.dev-networking.yml up -d redis-dev redis-commander
            Print-Success "Redis development stack started"
        } catch {
            Print-Error "Failed to start Redis development stack"
        }
    } else {
        Print-Error "docker-compose.dev-networking.yml not found"
        
        # Create minimal Redis container
        Print-Info "Creating minimal Redis container..."
        try {
            docker run -d --name heimnetz-redis-dev -p 6379:6379 -e REDIS_PASSWORD=dev_redis_password redis:7-alpine redis-server --requirepass dev_redis_password
            Print-Success "Minimal Redis container created"
        } catch {
            Print-Error "Failed to create minimal Redis container"
        }
    }
}

# Stop Redis stack
function Stop-RedisStack {
    Print-Info "Stopping Redis development stack..."
    
    if (Test-Path "docker-compose.dev-networking.yml") {
        try {
            docker-compose -f docker-compose.dev-networking.yml down
            Print-Success "Docker Compose stack stopped"
        } catch {
            Print-Warning "Failed to stop Docker Compose stack"
        }
    }
    
    # Stop individual containers
    try {
        docker stop heimnetz-redis-dev 2>$null
        docker rm heimnetz-redis-dev 2>$null
        Print-Success "Individual Redis containers stopped"
    } catch {
        Print-Info "No individual Redis containers to stop"
    }
}

# Create development network
function New-DevNetwork {
    Print-Info "Creating development network..."
    
    # Remove existing network if it exists
    try {
        docker network rm heimnetz-dev-network 2>$null
        Print-Info "Removed existing development network"
    } catch {
        Print-Info "No existing development network to remove"
    }
    
    # Create new network
    try {
        docker network create --driver bridge --subnet 172.28.0.0/16 --gateway 172.28.0.1 heimnetz-dev-network
        Print-Success "Development network created"
    } catch {
        Print-Error "Failed to create development network"
    }
}

# Test network connectivity
function Test-NetworkConnectivity {
    Print-Info "Testing network connectivity..."
    
    # Start a test container
    try {
        docker run --rm -d --name network-test --network heimnetz-dev-network alpine:latest sh -c "apk add --no-cache curl; tail -f /dev/null"
        
        # Test connectivity
        Start-Sleep -Seconds 5
        
        $pingResult = docker exec network-test ping -c 1 google.com 2>$null
        if ($pingResult) {
            Print-Success "External connectivity works"
        } else {
            Print-Warning "External connectivity issues"
        }
        
        # Clean up
        docker stop network-test 2>$null
        Print-Success "Network connectivity test completed"
    } catch {
        Print-Error "Failed to test network connectivity"
    }
}

# Fix Docker networking issues
function Repair-DockerNetworking {
    Print-Info "Fixing Docker networking issues..."
    
    # Stop existing containers
    Stop-RedisStack
    
    # Create development network
    New-DevNetwork
    
    # Start Redis stack
    Start-RedisStack
    
    # Test connectivity
    Start-Sleep -Seconds 10
    Test-RedisConnectivity
    
    Print-Success "Docker networking fixes applied"
}

# Run diagnostics
function Invoke-Diagnostics {
    Print-Info "Running comprehensive diagnostics..."
    
    Test-Docker
    Test-DockerCompose
    Test-DockerDaemon
    Get-DockerNetworks
    Test-PortAvailability
    Test-RedisConnectivity
    
    Print-Success "Diagnostics complete"
}

# Show menu
function Show-Menu {
    Write-Host ""
    Write-Host "🔧 Docker Network Diagnostics Menu" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "1. Run diagnostics"
    Write-Host "2. Fix networking issues"
    Write-Host "3. Start Redis stack"
    Write-Host "4. Stop Redis stack"
    Write-Host "5. Test Redis connectivity"
    Write-Host "6. Create development network"
    Write-Host "7. Test network connectivity"
    Write-Host "8. Exit"
    Write-Host ""
}

# Main script logic
function Main {
    Write-Host "🔧 Docker Network Diagnostics and Redis Fix Script" -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($Action -eq "menu") {
        # Interactive mode
        while ($true) {
            Show-Menu
            $choice = Read-Host "Select option (1-8)"
            
            switch ($choice) {
                "1" { Invoke-Diagnostics }
                "2" { Repair-DockerNetworking }
                "3" { Start-RedisStack }
                "4" { Stop-RedisStack }
                "5" { Test-RedisConnectivity }
                "6" { New-DevNetwork }
                "7" { Test-NetworkConnectivity }
                "8" { Write-Host "Goodbye!"; exit 0 }
                default { Print-Error "Invalid option" }
            }
            
            Write-Host ""
            Read-Host "Press Enter to continue..."
        }
    } else {
        # Command line mode
        switch ($Action) {
            "diagnostics" { Invoke-Diagnostics }
            "fix" { Repair-DockerNetworking }
            "start" { Start-RedisStack }
            "stop" { Stop-RedisStack }
            "test" { Test-RedisConnectivity }
            "network" { New-DevNetwork }
            "connectivity" { Test-NetworkConnectivity }
            default { 
                Write-Host "Usage: .\docker_network_fix.ps1 [diagnostics|fix|start|stop|test|network|connectivity]"
                exit 1
            }
        }
    }
}

# Run main function
Main
