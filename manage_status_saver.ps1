# 🚀 ULTIMATE SUITE v11.0 - STATUS SAVER MANAGEMENT
# ==================================================
# PowerShell script for managing the automated status saver

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "status", "test", "help")]
    [string]$Action = "help"
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "🎯 $Text" -ForegroundColor $Cyan
    Write-Host ("=" * ($Text.Length + 3)) -ForegroundColor $Cyan
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $Red
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠️ $Text" -ForegroundColor $Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️ $Text" -ForegroundColor $Cyan
}

function Test-PythonEnvironment {
    Write-Header "Testing Python Environment"
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python found: $pythonVersion"
        
        # Test required packages
        $packages = @("docker", "psutil", "requests", "asyncio")
        foreach ($package in $packages) {
            try {
                python -c "import $package; print('$package: OK')" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "$package package available"
                } else {
                    Write-Error "$package package missing"
                    return $false
                }
            } catch {
                Write-Error "$package package missing"
                return $false
            }
        }
        
        return $true
    } catch {
        Write-Error "Python not found or not accessible"
        return $false
    }
}

function Test-DockerEnvironment {
    Write-Header "Testing Docker Environment"
    
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker found: $dockerVersion"
            
            # Test Docker daemon
            docker ps >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Docker daemon is running"
                return $true
            } else {
                Write-Warning "Docker daemon not running - some features may be limited"
                return $true
            }
        } else {
            Write-Error "Docker not found"
            return $false
        }
    } catch {
        Write-Error "Docker not accessible"
        return $false
    }
}

function Start-StatusSaver {
    Write-Header "Starting Ultimate Suite Status Saver"
    
    # Check if already running
    $existing = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*status_saver_service.py*" }
    if ($existing) {
        Write-Warning "Status saver appears to already be running (PID: $($existing.Id))"
        return
    }
    
    # Test environment
    if (-not (Test-PythonEnvironment)) {
        Write-Error "Python environment check failed"
        return
    }
    
    Test-DockerEnvironment | Out-Null
    
    # Create status directory
    if (-not (Test-Path "data\status_snapshots")) {
        New-Item -ItemType Directory -Path "data\status_snapshots" -Force | Out-Null
        Write-Success "Created status snapshots directory"
    }
    
    try {
        Write-Info "Starting status saver service..."
        Start-Process -FilePath "python" -ArgumentList "status_saver_service.py" -WindowStyle Hidden -PassThru
        
        # Wait a moment and check if it started
        Start-Sleep -Seconds 3
        
        $process = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*status_saver_service.py*" }
        if ($process) {
            Write-Success "Status saver started successfully (PID: $($process.Id))"
            Write-Info "Service will save status every 12 minutes"
            Write-Info "Check 'data\status_snapshots\' for saved snapshots"
            Write-Info "Check 'status_saver_service.log' for service logs"
        } else {
            Write-Error "Failed to start status saver service"
        }
    } catch {
        Write-Error "Error starting status saver: $($_.Exception.Message)"
    }
}

function Stop-StatusSaver {
    Write-Header "Stopping Ultimate Suite Status Saver"
    
    try {
        $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*status_saver_service.py*" }
        
        if ($processes) {
            foreach ($process in $processes) {
                Write-Info "Stopping process PID: $($process.Id)"
                $process.Kill()
                Write-Success "Process stopped"
            }
        } else {
            Write-Warning "No running status saver processes found"
        }
    } catch {
        Write-Error "Error stopping status saver: $($_.Exception.Message)"
    }
}

function Get-StatusSaverStatus {
    Write-Header "Ultimate Suite Status Saver Status"
    
    # Check for running processes
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*status_saver_service.py*" }
    
    if ($processes) {
        Write-Success "Status Saver Service: RUNNING"
        foreach ($process in $processes) {
            $startTime = $process.StartTime
            $runTime = (Get-Date) - $startTime
            Write-Info "PID: $($process.Id)"
            Write-Info "Started: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
            Write-Info "Runtime: $($runTime.ToString('hh\:mm\:ss'))"
            Write-Info "Memory: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB"
        }
    } else {
        Write-Warning "Status Saver Service: NOT RUNNING"
    }
    
    Write-Host ""
    
    # Check status directory
    if (Test-Path "data\status_snapshots") {
        $snapshots = Get-ChildItem "data\status_snapshots\*.json" | Sort-Object LastWriteTime -Descending
        Write-Info "Status Snapshots Directory: data\status_snapshots\"
        Write-Info "Total snapshots: $($snapshots.Count)"
        
        if ($snapshots.Count -gt 0) {
            $latest = $snapshots[0]
            Write-Info "Latest snapshot: $($latest.Name)"
            Write-Info "Last saved: $($latest.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
            Write-Info "File size: $([math]::Round($latest.Length / 1KB, 2)) KB"
        }
    } else {
        Write-Warning "Status snapshots directory not found"
    }
    
    # Check log file
    if (Test-Path "status_saver_service.log") {
        $logFile = Get-Item "status_saver_service.log"
        Write-Info "Service log: status_saver_service.log ($([math]::Round($logFile.Length / 1KB, 2)) KB)"
    }
}

function Test-StatusSaver {
    Write-Header "Testing Status Saver Components"
    
    # Test Python environment
    $pythonOk = Test-PythonEnvironment
    
    # Test Docker environment
    $dockerOk = Test-DockerEnvironment
    
    # Test manual snapshot creation
    Write-Header "Testing Manual Snapshot Creation"
    try {
        Write-Info "Creating test snapshot..."
        python -c "import asyncio; from auto_status_saver import UltimateSuiteStatusSaver; asyncio.run(UltimateSuiteStatusSaver().save_status_snapshot())"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Test snapshot created successfully"
        } else {
            Write-Error "Failed to create test snapshot"
        }
    } catch {
        Write-Error "Error testing snapshot creation: $($_.Exception.Message)"
    }
    
    Write-Header "Test Results Summary"
    Write-Host "Python Environment: $(if ($pythonOk) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($pythonOk) { $Green } else { $Red })
    Write-Host "Docker Environment: $(if ($dockerOk) { 'PASS' } else { 'PASS (Limited)' })" -ForegroundColor $(if ($dockerOk) { $Green } else { $Yellow })
}

function Show-Help {
    Write-Header "Ultimate Suite Status Saver Management"
    
    Write-Host "USAGE:" -ForegroundColor $Cyan
    Write-Host "  .\manage_status_saver.ps1 [action]" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor $Cyan
    Write-Host "  start   - Start the automated status saver service" -ForegroundColor $Yellow
    Write-Host "  stop    - Stop the running status saver service" -ForegroundColor $Yellow
    Write-Host "  status  - Show current service status and statistics" -ForegroundColor $Yellow
    Write-Host "  test    - Test all components and create a test snapshot" -ForegroundColor $Yellow
    Write-Host "  help    - Show this help message" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "FEATURES:" -ForegroundColor $Cyan
    Write-Host "  • Automatic status snapshots every 12 minutes" -ForegroundColor $Green
    Write-Host "  • System metrics (CPU, Memory, Disk, GPU)" -ForegroundColor $Green
    Write-Host "  • Container status monitoring" -ForegroundColor $Green
    Write-Host "  • Service health checks" -ForegroundColor $Green
    Write-Host "  • Project files tracking" -ForegroundColor $Green
    Write-Host "  • Performance metrics collection" -ForegroundColor $Green
    Write-Host "  • Automatic cleanup of old snapshots" -ForegroundColor $Green
    Write-Host ""
    Write-Host "FILES:" -ForegroundColor $Cyan
    Write-Host "  • Snapshots: data\status_snapshots\" -ForegroundColor $Yellow
    Write-Host "  • Service log: status_saver_service.log" -ForegroundColor $Yellow
    Write-Host "  • Auto-saver log: auto_status_saver.log" -ForegroundColor $Yellow
}

# Main execution
switch ($Action.ToLower()) {
    "start" { Start-StatusSaver }
    "stop" { Stop-StatusSaver }
    "status" { Get-StatusSaverStatus }
    "test" { Test-StatusSaver }
    "help" { Show-Help }
    default { Show-Help }
}

Write-Host ""
