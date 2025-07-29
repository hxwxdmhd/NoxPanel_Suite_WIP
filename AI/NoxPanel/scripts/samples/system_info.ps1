# PowerShell System Information Script
# Displays basic system information

Write-Host "=== PowerShell System Information ===" -ForegroundColor Green
Write-Host "Computer Name: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "OS: $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)"
Write-Host "Current Directory: $(Get-Location)"
Write-Host "Timestamp: $(Get-Date)"
Write-Host "=== End ===" -ForegroundColor Green
