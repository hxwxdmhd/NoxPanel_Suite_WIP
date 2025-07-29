@echo off
setlocal

:: Ensure we're running as admin
fltmc >nul 2>&1 || (
    echo This script must be run as administrator.
    pause
    exit /b 1
)

echo Backing up current hosts file...
set HOSTS_PATH=%SystemRoot%\System32\drivers\etc\hosts
copy "%HOSTS_PATH%" "%HOSTS_PATH%.bak" >nul

echo.
echo Adding NoxGuard host entries...

>> "%HOSTS_PATH%" echo.
>> "%HOSTS_PATH%" echo # --- NoxGuard Entries ---
>> "%HOSTS_PATH%" echo 127.0.0.1    dashboard.noxguard.local
>> "%HOSTS_PATH%" echo 127.0.0.1    vault.noxguard.local
>> "%HOSTS_PATH%" echo 127.0.0.1    media.noxguard.local
>> "%HOSTS_PATH%" echo 127.0.0.1    proxy.noxguard.local
>> "%HOSTS_PATH%" echo 127.0.0.1    sentinel.noxguard.local
>> "%HOSTS_PATH%" echo 127.0.0.1    node01.noxguard.local

echo.
echo ✅ NoxGuard entries added successfully.
echo Backup saved as hosts.bak in the same folder.
pause
