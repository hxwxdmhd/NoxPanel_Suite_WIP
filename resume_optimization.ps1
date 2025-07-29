#!/usr/bin/env powershell
# 🧠 ULTIMATE SUITE v11.0 - POST-REBOOT RESUMPTION SCRIPT
# ========================================================

Write-Host "🧠 ULTIMATE SUITE v11.0 - RESUMING OPTIMIZATION" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

Write-Host "📋 Checking system status after reboot..." -ForegroundColor Yellow

# Check Docker status
Write-Host "`n🐳 DOCKER STATUS:" -ForegroundColor Blue
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
    
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker daemon: Running" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Docker daemon: Starting..." -ForegroundColor Yellow
        Start-Sleep 10
    }
} catch {
    Write-Host "❌ Docker: Not found in PATH" -ForegroundColor Red
}

# Check if performance server is still running
Write-Host "`n⚡ PERFORMANCE SERVER:" -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ FastAPI server: Running" -ForegroundColor Green
    Write-Host "   - Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   - GPU: $($response.gpu_available)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️ FastAPI server: Stopped, restarting..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "performance_server.py" -WindowStyle Hidden
    Start-Sleep 5
}

# Check GPU status
Write-Host "`n🎮 GPU STATUS:" -ForegroundColor Blue
try {
    $gpuTest = python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
    Write-Host "✅ $gpuTest" -ForegroundColor Green
} catch {
    Write-Host "❌ GPU test failed" -ForegroundColor Red
}

Write-Host "`n🚀 READY TO CONTINUE PHASE 2: CONTAINERIZATION" -ForegroundColor Green
Write-Host "`nNext commands to execute:" -ForegroundColor Yellow
Write-Host "1. docker-compose -f docker-compose-optimized.yml up -d" -ForegroundColor White
Write-Host "2. python validate_optimization.py" -ForegroundColor White  
Write-Host "3. Open dashboard: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n🎯 Target: Sub-100ms response times with GPU acceleration" -ForegroundColor Cyan
