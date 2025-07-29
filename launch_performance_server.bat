@echo off
echo Starting NoxPanel Performance-Enhanced Web Server...
echo ==========================================

cd /d "k:\Project Heimnetz"

echo Current Directory: %CD%
echo.

echo Checking Python availability...
python --version
echo.

echo Launching performance-enhanced web server...
echo Server will be available at: http://localhost:5000
echo.
echo Features enabled:
echo - Real-time performance monitoring
echo - Workspace performance comparison
echo - LSP behavior tracking
echo - Adaptive cache validation
echo - FRITZWATCHER plugin integration
echo - Multi-workspace launch capabilities
echo.

python performance_enhanced_web_server.py --host 127.0.0.1 --port 5000

echo.
echo Server stopped. Press any key to exit...
pause > nul
