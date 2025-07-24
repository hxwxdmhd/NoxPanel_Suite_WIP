# Simple Docker Network Diagnostics (PowerShell)
# Part of Ultimate Suite v11.0

Write-Host "🔧 Docker Network Diagnostics" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Test Docker installation
Write-Host "`n📦 Testing Docker Installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker is not installed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker is not installed or not accessible" -ForegroundColor Red
    exit 1
}

# Test Docker daemon
Write-Host "`n🐳 Testing Docker Daemon..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>$null
    if ($dockerInfo) {
        Write-Host "✅ Docker daemon is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker daemon is not running" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Cannot connect to Docker daemon" -ForegroundColor Red
    exit 1
}

# Test Docker Compose
Write-Host "`n🔧 Testing Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✅ Docker Compose is installed: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker Compose is not installed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Docker Compose is not accessible" -ForegroundColor Red
}

# List Docker networks
Write-Host "`n🌐 Docker Networks:" -ForegroundColor Yellow
try {
    docker network ls
    Write-Host "✅ Docker networks listed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to list Docker networks" -ForegroundColor Red
}

# Test port availability
Write-Host "`n🔌 Testing Port Availability..." -ForegroundColor Yellow
$ports = @(5000, 5001, 5002, 5003, 6379, 6380, 3000, 8081, 9090)

foreach ($port in $ports) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ReceiveTimeout = 1000
        $tcpClient.SendTimeout = 1000
        $connection = $tcpClient.ConnectAsync("localhost", $port)
        
        if ($connection.Wait(1000)) {
            Write-Host "⚠️ Port $port is occupied" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Port $port is available" -ForegroundColor Green
        }
        $tcpClient.Close()
    } catch {
        Write-Host "✅ Port $port is available" -ForegroundColor Green
    }
}

# Test Redis connectivity
Write-Host "`n📡 Testing Redis Connectivity..." -ForegroundColor Yellow
$redisHosts = @("localhost", "127.0.0.1", "host.docker.internal", "172.17.0.1")
$redisPorts = @(6379, 6380)

foreach ($redisHost in $redisHosts) {
    foreach ($redisPort in $redisPorts) {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 2000
            $tcpClient.SendTimeout = 2000
            $connection = $tcpClient.ConnectAsync($redisHost, $redisPort)
            
            if ($connection.Wait(2000)) {
                Write-Host "✅ Redis connection successful: $redisHost`:$redisPort" -ForegroundColor Green
            } else {
                Write-Host "❌ Redis connection failed: $redisHost`:$redisPort" -ForegroundColor Red
            }
            $tcpClient.Close()
        } catch {
            Write-Host "❌ Redis connection failed: $redisHost`:$redisPort" -ForegroundColor Red
        }
    }
}

# Test if Redis container is running
Write-Host "`n🔍 Checking Redis Containers..." -ForegroundColor Yellow
try {
    $redisContainers = docker ps -a --filter "name=redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    if ($redisContainers) {
        Write-Host "Redis containers found:" -ForegroundColor Green
        Write-Host $redisContainers
    } else {
        Write-Host "❌ No Redis containers found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to check Redis containers" -ForegroundColor Red
}

# Summary
Write-Host "`n📊 Diagnostic Summary:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "✅ Docker installation: OK" -ForegroundColor Green
Write-Host "✅ Docker daemon: Running" -ForegroundColor Green

# Check if we found any Redis connections
$redisFound = $false
foreach ($redisHost in $redisHosts) {
    foreach ($redisPort in $redisPorts) {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connection = $tcpClient.ConnectAsync($redisHost, $redisPort)
            if ($connection.Wait(1000)) {
                $redisFound = $true
                break
            }
            $tcpClient.Close()
        } catch {
            # Ignore errors for summary
        }
    }
    if ($redisFound) { break }
}

if ($redisFound) {
    Write-Host "✅ Redis connectivity: Available" -ForegroundColor Green
} else {
    Write-Host "❌ Redis connectivity: Not available" -ForegroundColor Red
    Write-Host "💡 Recommendation: Start Redis with docker-compose or install Redis locally" -ForegroundColor Yellow
}

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan
Write-Host "1. To start Redis development stack:" -ForegroundColor White
Write-Host "   docker-compose -f docker-compose.dev-networking.yml up -d redis-dev" -ForegroundColor Gray
Write-Host "2. To start the enhanced server:" -ForegroundColor White
Write-Host "   python server_enhanced.py" -ForegroundColor Gray
Write-Host "3. To test network connectivity:" -ForegroundColor White
Write-Host "   Access http://localhost:5003 in your browser" -ForegroundColor Gray

Write-Host "`n✅ Diagnostics completed successfully!" -ForegroundColor Green
