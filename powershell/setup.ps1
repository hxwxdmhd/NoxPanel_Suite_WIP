# setup.ps1 - Heimnetz PowerShell Auto Import and Health Check Script

# Import devices from devices.json (expects array of objects with Name and IP)
$devices = Get-Content -Raw -Path "./data/devices.json" | ConvertFrom-Json

# Initialize log array
$log = @()

# Loop through each device and perform ping health check
foreach ($device in $devices) {
    # Ping device (2 attempts, quiet mode)
    $status = Test-Connection -ComputerName $device.IP -Count 2 -Quiet
    $state = if ($status) { "Online" } else { "Offline" }
    # Add result to log
    $log += [PSCustomObject]@{
        Name = $device.Name
        IP = $device.IP
        Status = $state
    }
}

# Output log to CSV
if (!(Test-Path "./logs")) { New-Item -ItemType Directory -Path "./logs" | Out-Null }
$log | Export-Csv -Path "./logs/healthcheck.csv" -NoTypeInformation

# Output summary
$online = ($log | Where-Object { $_.Status -eq 'Online' }).Count
$offline = ($log | Where-Object { $_.Status -eq 'Offline' }).Count
Write-Host "Health check complete. Devices online: $online, offline: $offline"
