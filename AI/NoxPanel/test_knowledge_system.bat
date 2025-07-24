@echo off
echo ============================================================
echo NoxPanel Knowledge Base - Comprehensive System Test
echo ============================================================

echo.
echo Step 1: Testing conversation processor...
python conversation_processor.py --help

echo.
echo Step 2: Starting NoxPanel v5.0 with enhanced knowledge management...
python webpanel\app_v5.py

pause
