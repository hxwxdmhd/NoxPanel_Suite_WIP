# system_health_audit.ps1 - Collects baseline system information

# Gather hardware and OS information
$computerInfo = Get-ComputerInfo

# Gather network configuration
$netInfo = Get-NetIPAddress | Select-Object InterfaceAlias, IPAddress, AddressFamily, PrefixLength

# Gather service status
$services = Get-Service | Select-Object Name, Status, StartType

# Basic connectivity test to default gateway
$defaultGateway = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1).NextHop
$pingResult = $null
if ($defaultGateway) {
    $pingResult = Test-Connection -ComputerName $defaultGateway -Count 2 -ErrorAction SilentlyContinue
}

$report = [PSCustomObject]@{
    Timestamp = Get-Date
    ComputerInfo = $computerInfo
    Network = $netInfo
    Services = $services
    ConnectivityTest = $pingResult
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report | ConvertTo-Json -Depth 4 | Set-Content -Path "system_health_$timestamp.json"
Write-Host "System health report saved to system_health_$timestamp.json"
