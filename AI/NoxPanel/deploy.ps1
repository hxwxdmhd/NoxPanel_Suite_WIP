# NoxPanel Ultimate Suite - Quick Deploy Script
# PowerShell deployment automation

param(
    [string]$Action = "status",
    [switch]$Build,
    [switch]$Deploy,
    [switch]$Stop,
    [switch]$Monitor
)

Write-Host "NoxPanel Ultimate Suite Deployment Manager" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Show-Status {
    Write-Host "Checking system status..." -ForegroundColor Yellow
    
    # Check if services are running
    $services = @(
        @{Name="Ultimate Suite v8.0"; URL="http://localhost:5000/api/models"; Port=5000},
        @{Name="Enhanced Dashboard"; URL="http://localhost:8002/api/system/status"; Port=8002}
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ $($service.Name): RUNNING" -ForegroundColor Green
            } else {
                Write-Host "! $($service.Name): UNHEALTHY" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "✗ $($service.Name): OFFLINE" -ForegroundColor Red
        }
    }
}

function Start-Services {
    Write-Host "Starting NoxPanel services..." -ForegroundColor Green
    
    # Start Ultimate Suite v8.0
    Write-Host "Starting Ultimate Suite v8.0..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-Command", "cd 'k:\Project Heimnetz\AI\NoxPanel'; python ultimate_webapp_v8.py" -WindowStyle Minimized
    
    Start-Sleep -Seconds 5
    
    # Start Enhanced Dashboard
    Write-Host "Starting Enhanced Master Dashboard..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-Command", "cd 'k:\Project Heimnetz\AI\NoxPanel'; python enhanced_master_dashboard.py" -WindowStyle Minimized
    
    Start-Sleep -Seconds 3
    
    Write-Host "Services startup initiated!" -ForegroundColor Green
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Show-Status
}

function Stop-Services {
    Write-Host "Stopping NoxPanel services..." -ForegroundColor Red
    
    # Kill Python processes running our services
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*ultimate_webapp*" -or 
        $_.CommandLine -like "*enhanced_master_dashboard*"
    } | Stop-Process -Force
    
    Write-Host "Services stopped!" -ForegroundColor Yellow
}

function Show-Monitor {
    Write-Host "NoxPanel System Monitor" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    
    while ($true) {
        Clear-Host
        Write-Host "NoxPanel Live Monitor - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
        Write-Host "=====================================================" -ForegroundColor Cyan
        
        Show-Status
        
        Write-Host "`nAccess URLs:" -ForegroundColor Yellow
        Write-Host "  Enhanced Dashboard: http://localhost:8002" -ForegroundColor White
        Write-Host "  Ultimate Suite: http://localhost:5000" -ForegroundColor White
        
        Write-Host "`nPress Ctrl+C to exit monitor..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
    }
}

# Main execution
switch ($Action.ToLower()) {
    "status" { Show-Status }
    "start" { Start-Services }
    "stop" { Stop-Services }
    "restart" { 
        Stop-Services
        Start-Sleep -Seconds 3
        Start-Services 
    }
    "monitor" { Show-Monitor }
    default {
        Write-Host "Usage: .\deploy.ps1 -Action [status|start|stop|restart|monitor]" -ForegroundColor Yellow
        Write-Host "  or: .\deploy.ps1 -Build -Deploy -Monitor" -ForegroundColor Yellow
    }
}

if ($Build) {
    Write-Host "Build process would create Docker containers here..." -ForegroundColor Green
}

if ($Deploy) {
    Start-Services
}

if ($Monitor) {
    Show-Monitor
}

Write-Host "`nDeployment script completed!" -ForegroundColor Green
