# NoxSuite Langflow Integration Startup Script for Windows
param(
    [switch]$SkipDocker,
    [switch]$Verbose
)

Write-Host "STARTING: NoxSuite Langflow Integration..." -ForegroundColor Green

# Check if Docker Desktop is running
if (-not $SkipDocker) {
    try {
        docker info | Out-Null
        Write-Host "SUCCESS: Docker is running" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
}

# Create network if it doesn't exist
try {
    docker network create noxsuite-network 2>$null
    Write-Host "NETWORK: Docker network ready" -ForegroundColor Yellow
}
catch {
    # Network might already exist
}

# Load environment variables from config
$envFile = "langflow/config/langflow.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "(.+)=(.+)") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    Write-Host "SUCCESS: Loaded Langflow environment configuration" -ForegroundColor Green
}

# Start the emergency copilot throttler
Write-Host "THROTTLER: Starting Emergency Copilot Throttler..." -ForegroundColor Cyan
$throttlerJob = Start-Job -ScriptBlock { python emergency_copilot_fix.py }

# Initialize component registry
Write-Host "REGISTRY: Initializing NoxSuite Component Registry..." -ForegroundColor Cyan
Push-Location langflow
python component_registry.py
Pop-Location

# Start Docker containers
Write-Host "DOCKER: Starting Docker containers..." -ForegroundColor Cyan
docker-compose -f docker-compose.langflow.yml up -d

# Wait for services to be ready
Write-Host "WAITING: Services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service health
Write-Host "HEALTH: Checking service health..." -ForegroundColor Cyan
docker-compose -f docker-compose.langflow.yml ps

# Start autonomous monitoring
Write-Host "MONITOR: Starting Autonomous Monitoring..." -ForegroundColor Cyan
$monitorJob = Start-Job -ScriptBlock { python autonomous_monitor.py }

Write-Host "SUCCESS: NoxSuite Langflow Integration started successfully!" -ForegroundColor Green
Write-Host "UI: Langflow UI: http://localhost:7860" -ForegroundColor White
Write-Host "LOGIN: Admin Login: noxsuite_admin / noxsuite_secure_2024" -ForegroundColor White
Write-Host "THROTTLER: Emergency Throttler Job ID: $($throttlerJob.Id)" -ForegroundColor White
Write-Host "MONITOR: Autonomous Monitor Job ID: $($monitorJob.Id)" -ForegroundColor White

# Save job IDs for cleanup
$throttlerJob.Id | Out-File -FilePath ".throttler.pid" -Encoding UTF8
$monitorJob.Id | Out-File -FilePath ".monitor.pid" -Encoding UTF8

Write-Host "COMPLETE: Setup complete! NoxSuite is ready for enhanced MCP workflows." -ForegroundColor Green

if ($Verbose) {
    Write-Host "`nJOBS: Active Jobs:" -ForegroundColor Yellow
    Get-Job | Format-Table
}
