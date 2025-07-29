Start-Process python -ArgumentList "ultra_fast_server.py" -WindowStyle Hidden
Write-Host "🚀 Ultra-Fast Server starting in background..."
Start-Sleep -Seconds 3
Write-Host "🌐 Server should be running on http://localhost:5000"

# Test if server is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 2
    Write-Host "✅ Server is responding: $($response.StatusCode)"
} catch {
    Write-Host "⚠️ Server may still be starting or failed to start"
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "🔄 Ready for Gate 3 audit!"
