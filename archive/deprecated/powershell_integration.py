#!/usr/bin/env python3
"""
SysAdmin Copilot - PowerShell Integration Module

This module provides deep integration with PowerShell for Windows system administration tasks.
It extends the base SysAdmin Copilot with Windows-specific capabilities and PowerShell
script generation, execution, and management.

Key Features:
- Advanced PowerShell script generation
- Windows-specific system administration
- Active Directory integration
- Registry management with safety controls
- Windows Update automation
- Service management
- Performance monitoring with PowerShell cmdlets
"""

import asyncio
import json
import logging
import subprocess
import platform
import base64
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sysadmin_copilot import (
    SysAdminCopilot, Task, TaskType, TaskPriority, TaskStatus, ScriptType,
    SystemOS, SystemContext, SystemContextManager
)

# Configure logging
logger = logging.getLogger("PowerShellIntegration")


# ============================================================================
# PowerShell-Specific Types and Enums
# ============================================================================

class PowerShellExecutionPolicy(Enum):
    """PowerShell execution policies"""
    RESTRICTED = "Restricted"
    ALL_SIGNED = "AllSigned"
    REMOTE_SIGNED = "RemoteSigned"
    UNRESTRICTED = "Unrestricted"
    BYPASS = "Bypass"
    UNDEFINED = "Undefined"


class WindowsServiceStatus(Enum):
    """Windows service status"""
    STOPPED = "Stopped"
    RUNNING = "Running"
    PAUSED = "Paused"
    PENDING_START = "StartPending"
    PENDING_STOP = "StopPending"
    PENDING_CONTINUE = "ContinuePending"
    PENDING_PAUSE = "PausePending"


@dataclass
class PowerShellProfile:
    """PowerShell execution profile"""
    execution_policy: PowerShellExecutionPolicy = PowerShellExecutionPolicy.REMOTE_SIGNED
    use_elevated_privileges: bool = False
    timeout_seconds: int = 300
    working_directory: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    modules_to_import: List[str] = field(default_factory=list)


@dataclass
class WindowsSystemInfo:
    """Windows-specific system information"""
    windows_version: str
    build_number: str
    edition: str
    architecture: str
    domain_joined: bool
    domain_name: Optional[str]
    computer_name: str
    last_boot_time: datetime
    windows_update_status: str
    defender_status: str
    firewall_status: str
    pending_reboot: bool
    installed_features: List[str]
    running_services_count: int
    stopped_services_count: int


@dataclass
class RegistryOperation:
    """Registry operation details"""
    hive: str  # HKLM, HKCU, etc.
    key_path: str
    operation: str  # read, write, delete, create
    value_name: Optional[str] = None
    value_data: Optional[str] = None
    value_type: str = "String"  # String, DWORD, QWORD, Binary, etc.
    backup_created: bool = False
    safety_level: str = "medium"  # low, medium, high


# ============================================================================
# PowerShell Script Templates
# ============================================================================

class PowerShellTemplates:
    """
    Collection of PowerShell script templates for common administrative tasks.
    """
    
    @staticmethod
    def get_system_information() -> str:
        """Comprehensive Windows system information script"""
        return '''
# Comprehensive Windows System Information Script
$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Windows System Information Report   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Basic System Information
Write-Host "=== Basic System Information ===" -ForegroundColor Green
$computerInfo = Get-ComputerInfo
Write-Host "Computer Name: $($computerInfo.CsName)"
Write-Host "OS Name: $($computerInfo.WindowsProductName)"
Write-Host "OS Version: $($computerInfo.WindowsVersion)"
Write-Host "Build Number: $($computerInfo.WindowsBuildLabEx)"
Write-Host "Architecture: $($computerInfo.CsSystemType)"
Write-Host "Domain: $($computerInfo.CsDomain)"
Write-Host "Total RAM: $([math]::Round($computerInfo.TotalPhysicalMemory/1GB,2)) GB"
Write-Host "CPU: $($computerInfo.CsProcessors[0].Name)"
Write-Host "Last Boot: $($computerInfo.CsBootupState)"
Write-Host ""

# Windows Update Status
Write-Host "=== Windows Update Status ===" -ForegroundColor Yellow
try {
    $updateSession = New-Object -ComObject Microsoft.Update.Session
    $updateSearcher = $updateSession.CreateUpdateSearcher()
    $searchResult = $updateSearcher.Search("IsInstalled=0")
    Write-Host "Pending Updates: $($searchResult.Updates.Count)"
    
    if ($searchResult.Updates.Count -gt 0) {
        Write-Host "Recent pending updates:"
        $searchResult.Updates | Select-Object -First 5 | ForEach-Object {
            Write-Host "  - $($_.Title)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "Could not retrieve Windows Update status: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Disk Usage
Write-Host "=== Disk Usage ===" -ForegroundColor Magenta
Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
    $freePercent = [math]::Round(($_.FreeSpace / $_.Size) * 100, 2)
    $usedPercent = 100 - $freePercent
    $sizeGB = [math]::Round($_.Size / 1GB, 2)
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    
    Write-Host "Drive $($_.DeviceID)"
    Write-Host "  Size: $sizeGB GB"
    Write-Host "  Free: $freeGB GB ($freePercent%)"
    Write-Host "  Used: $usedPercent%" -ForegroundColor $(if ($usedPercent -gt 90) {"Red"} elseif ($usedPercent -gt 80) {"Yellow"} else {"Green"})
}
Write-Host ""

# Memory Usage
Write-Host "=== Memory Usage ===" -ForegroundColor Blue
$memory = Get-WmiObject -Class Win32_OperatingSystem
$totalMemory = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
$freeMemory = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
$usedMemory = $totalMemory - $freeMemory
$memoryPercent = [math]::Round(($usedMemory / $totalMemory) * 100, 2)

Write-Host "Total Memory: $totalMemory GB"
Write-Host "Used Memory: $usedMemory GB ($memoryPercent%)"
Write-Host "Free Memory: $freeMemory GB"
Write-Host ""

# Services Status
Write-Host "=== Services Status ===" -ForegroundColor Cyan
$runningServices = Get-Service | Where-Object {$_.Status -eq "Running"}
$stoppedServices = Get-Service | Where-Object {$_.Status -eq "Stopped"}

Write-Host "Running Services: $($runningServices.Count)"
Write-Host "Stopped Services: $($stoppedServices.Count)"
Write-Host ""

Write-Host "Top 10 CPU Consuming Processes:"
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet | Format-Table -AutoSize

Write-Host "=== Security Status ===" -ForegroundColor Red
# Windows Defender Status
try {
    $defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
    if ($defenderStatus) {
        Write-Host "Windows Defender Status:"
        Write-Host "  Antivirus Enabled: $($defenderStatus.AntivirusEnabled)"
        Write-Host "  Real-time Protection: $($defenderStatus.RealTimeProtectionEnabled)"
        Write-Host "  Last Full Scan: $($defenderStatus.FullScanEndTime)"
    }
} catch {
    Write-Host "Could not retrieve Windows Defender status"
}

# Firewall Status
try {
    $firewallProfiles = Get-NetFirewallProfile
    Write-Host "Windows Firewall Status:"
    foreach ($profile in $firewallProfiles) {
        Write-Host "  $($profile.Name): $($profile.Enabled)"
    }
} catch {
    Write-Host "Could not retrieve Windows Firewall status"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           Report Complete              " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
'''
    
    @staticmethod
    def cleanup_system() -> str:
        """System cleanup and optimization script"""
        return '''
# Windows System Cleanup and Optimization Script
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "    Windows System Cleanup Utility     " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$totalCleaned = 0
$cleanupResults = @()

# Function to safely clean directory
function Clean-Directory {
    param(
        [string]$Path,
        [string]$Description
    )
    
    if (Test-Path $Path) {
        try {
            $sizeBefore = (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($sizeBefore -eq $null) { $sizeBefore = 0 }
            
            Write-Host "Cleaning: $Description..." -ForegroundColor Yellow
            Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
            
            $sizeAfter = (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($sizeAfter -eq $null) { $sizeAfter = 0 }
            
            $cleaned = $sizeBefore - $sizeAfter
            $cleanedMB = [math]::Round($cleaned / 1MB, 2)
            
            Write-Host "  Cleaned: $cleanedMB MB" -ForegroundColor Green
            
            return @{
                Location = $Description
                CleanedMB = $cleanedMB
                Success = $true
            }
        } catch {
            Write-Host "  Error cleaning $Description : $($_.Exception.Message)" -ForegroundColor Red
            return @{
                Location = $Description
                CleanedMB = 0
                Success = $false
                Error = $_.Exception.Message
            }
        }
    } else {
        Write-Host "  Path not found: $Path" -ForegroundColor Yellow
        return @{
            Location = $Description
            CleanedMB = 0
            Success = $false
            Error = "Path not found"
        }
    }
}

# Cleanup locations
$cleanupLocations = @(
    @{Path = "$env:TEMP"; Description = "User Temp Files"},
    @{Path = "$env:TMP"; Description = "System Temp Files"},
    @{Path = "C:\\Windows\\Temp"; Description = "Windows Temp"},
    @{Path = "$env:LOCALAPPDATA\\Temp"; Description = "Local App Data Temp"},
    @{Path = "C:\\Windows\\Prefetch"; Description = "Prefetch Files"},
    @{Path = "C:\\Windows\\SoftwareDistribution\\Download"; Description = "Windows Update Cache"},
    @{Path = "$env:LOCALAPPDATA\\Microsoft\\Windows\\INetCache"; Description = "Internet Cache"},
    @{Path = "$env:APPDATA\\Microsoft\\Windows\\Recent"; Description = "Recent Items"}
)

# Perform cleanup
foreach ($location in $cleanupLocations) {
    $result = Clean-Directory -Path $location.Path -Description $location.Description
    $cleanupResults += $result
    $totalCleaned += $result.CleanedMB
}

Write-Host ""
Write-Host "=== Cleanup Summary ===" -ForegroundColor Cyan
Write-Host "Total Space Cleaned: $([math]::Round($totalCleaned, 2)) MB" -ForegroundColor Green

foreach ($result in $cleanupResults) {
    if ($result.Success) {
        Write-Host "✓ $($result.Location): $($result.CleanedMB) MB" -ForegroundColor Green
    } else {
        Write-Host "✗ $($result.Location): Failed - $($result.Error)" -ForegroundColor Red
    }
}

# Empty Recycle Bin (requires confirmation in interactive mode)
Write-Host ""
Write-Host "=== Additional Cleanup ===" -ForegroundColor Yellow
try {
    $recycleBin = (New-Object -ComObject Shell.Application).Namespace(0xA)
    $recycleBinItems = $recycleBin.Items()
    if ($recycleBinItems.Count -gt 0) {
        Write-Host "Recycle Bin contains $($recycleBinItems.Count) items"
        Write-Host "To empty Recycle Bin manually, run: Clear-RecycleBin -Force"
    } else {
        Write-Host "Recycle Bin is already empty" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not check Recycle Bin status" -ForegroundColor Yellow
}

# Disk Cleanup utility
Write-Host ""
Write-Host "=== Running Windows Disk Cleanup ===" -ForegroundColor Blue
try {
    $cleanmgr = Start-Process -FilePath "cleanmgr.exe" -ArgumentList "/sagerun:1" -WindowStyle Hidden -PassThru
    Write-Host "Windows Disk Cleanup started (Process ID: $($cleanmgr.Id))"
    Write-Host "Note: Disk Cleanup is running in the background"
} catch {
    Write-Host "Could not start Windows Disk Cleanup: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "         Cleanup Complete               " -ForegroundColor Green
Write-Host "   Total Cleaned: $([math]::Round($totalCleaned, 2)) MB" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
'''
    
    @staticmethod
    def service_management() -> str:
        """Windows service management script"""
        return '''
# Windows Service Management Script
param(
    [string]$Action = "Status",  # Status, Start, Stop, Restart
    [string]$ServiceName = "",
    [switch]$ShowAll = $false
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      Windows Service Management        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Show-ServiceStatus {
    param([string]$Name = "")
    
    if ($Name) {
        # Show specific service
        try {
            $service = Get-Service -Name $Name -ErrorAction Stop
            Write-Host "Service: $($service.Name)" -ForegroundColor Green
            Write-Host "Display Name: $($service.DisplayName)"
            Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") {"Green"} else {"Red"})
            Write-Host "Start Type: $($service.StartType)"
            Write-Host ""
        } catch {
            Write-Host "Service '$Name' not found or inaccessible" -ForegroundColor Red
            return
        }
    } else {
        # Show all services summary
        $services = Get-Service
        $running = $services | Where-Object {$_.Status -eq "Running"}
        $stopped = $services | Where-Object {$_.Status -eq "Stopped"}
        
        Write-Host "=== Service Summary ===" -ForegroundColor Green
        Write-Host "Total Services: $($services.Count)"
        Write-Host "Running: $($running.Count)" -ForegroundColor Green
        Write-Host "Stopped: $($stopped.Count)" -ForegroundColor Red
        Write-Host ""
        
        if ($ShowAll) {
            Write-Host "=== All Services ===" -ForegroundColor Yellow
            $services | Sort-Object Status, Name | Format-Table Name, Status, StartType -AutoSize
        } else {
            Write-Host "=== Critical Services Status ===" -ForegroundColor Yellow
            $criticalServices = @(
                "Winmgmt", "Spooler", "BITS", "Themes", "AudioSrv", 
                "Dhcp", "Dnscache", "EventLog", "PlugPlay", "RpcSs"
            )
            
            foreach ($serviceName in $criticalServices) {
                try {
                    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
                    if ($service) {
                        $statusColor = if ($service.Status -eq "Running") {"Green"} else {"Red"}
                        Write-Host "  $($service.Name): $($service.Status)" -ForegroundColor $statusColor
                    }
                } catch {
                    # Service doesn't exist, skip
                }
            }
            Write-Host ""
            Write-Host "Use -ShowAll switch to see all services" -ForegroundColor Gray
        }
    }
}

function Start-ServiceSafe {
    param([string]$Name)
    
    try {
        $service = Get-Service -Name $Name -ErrorAction Stop
        if ($service.Status -eq "Running") {
            Write-Host "Service '$Name' is already running" -ForegroundColor Yellow
        } else {
            Write-Host "Starting service '$Name'..." -ForegroundColor Blue
            Start-Service -Name $Name -ErrorAction Stop
            Write-Host "Service '$Name' started successfully" -ForegroundColor Green
        }
    } catch {
        Write-Host "Failed to start service '$Name': $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-ServiceSafe {
    param([string]$Name)
    
    try {
        $service = Get-Service -Name $Name -ErrorAction Stop
        if ($service.Status -eq "Stopped") {
            Write-Host "Service '$Name' is already stopped" -ForegroundColor Yellow
        } else {
            Write-Host "Stopping service '$Name'..." -ForegroundColor Blue
            Stop-Service -Name $Name -Force -ErrorAction Stop
            Write-Host "Service '$Name' stopped successfully" -ForegroundColor Green
        }
    } catch {
        Write-Host "Failed to stop service '$Name': $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Restart-ServiceSafe {
    param([string]$Name)
    
    try {
        Write-Host "Restarting service '$Name'..." -ForegroundColor Blue
        Restart-Service -Name $Name -Force -ErrorAction Stop
        Write-Host "Service '$Name' restarted successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to restart service '$Name': $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main execution
switch ($Action.ToLower()) {
    "status" {
        Show-ServiceStatus -Name $ServiceName
    }
    "start" {
        if ($ServiceName) {
            Start-ServiceSafe -Name $ServiceName
        } else {
            Write-Host "Service name required for start action" -ForegroundColor Red
        }
    }
    "stop" {
        if ($ServiceName) {
            Stop-ServiceSafe -Name $ServiceName
        } else {
            Write-Host "Service name required for stop action" -ForegroundColor Red
        }
    }
    "restart" {
        if ($ServiceName) {
            Restart-ServiceSafe -Name $ServiceName
        } else {
            Write-Host "Service name required for restart action" -ForegroundColor Red
        }
    }
    default {
        Write-Host "Invalid action. Use: Status, Start, Stop, or Restart" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     Service Management Complete        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
'''
    
    @staticmethod
    def performance_monitoring() -> str:
        """Windows performance monitoring script"""
        return '''
# Windows Performance Monitoring Script
param(
    [int]$Duration = 60,  # Duration in seconds
    [int]$Interval = 5,   # Interval between samples in seconds
    [switch]$Detailed = $false
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "    Windows Performance Monitor         " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Monitoring Duration: $Duration seconds"
Write-Host "Sample Interval: $Interval seconds"
Write-Host "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Performance counters to monitor
$counters = @(
    "\\Processor(_Total)\\% Processor Time",
    "\\Memory\\Available MBytes",
    "\\Memory\\% Committed Bytes In Use",
    "\\PhysicalDisk(_Total)\\% Disk Time",
    "\\PhysicalDisk(_Total)\\Disk Read Bytes/sec",
    "\\PhysicalDisk(_Total)\\Disk Write Bytes/sec",
    "\\Network Interface(*)\\Bytes Total/sec"
)

$samples = [math]::Ceiling($Duration / $Interval)
$performanceData = @()

Write-Host "=== Performance Monitoring Started ===" -ForegroundColor Green

for ($i = 1; $i -le $samples; $i++) {
    $timestamp = Get-Date
    Write-Host "Sample $i/$samples - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    
    try {
        # Get performance counters
        $perfCounters = Get-Counter -Counter $counters -ErrorAction SilentlyContinue
        
        # Extract values
        $cpuUsage = ($perfCounters.CounterSamples | Where-Object {$_.Path -like "*Processor(_Total)*Processor Time"}).CookedValue
        $availableMemoryMB = ($perfCounters.CounterSamples | Where-Object {$_.Path -like "*Memory*Available MBytes"}).CookedValue
        $memoryUsage = ($perfCounters.CounterSamples | Where-Object {$_.Path -like "*Memory*% Committed Bytes In Use"}).CookedValue
        $diskTime = ($perfCounters.CounterSamples | Where-Object {$_.Path -like "*PhysicalDisk(_Total)*% Disk Time"}).CookedValue
        
        # Network counters (sum all interfaces)
        $networkCounters = $perfCounters.CounterSamples | Where-Object {$_.Path -like "*Network Interface*Bytes Total/sec"}
        $totalNetworkBytes = ($networkCounters | Measure-Object -Property CookedValue -Sum).Sum
        
        # Create performance sample
        $sample = @{
            Timestamp = $timestamp
            CPUUsage = [math]::Round($cpuUsage, 2)
            AvailableMemoryMB = [math]::Round($availableMemoryMB, 2)
            MemoryUsage = [math]::Round($memoryUsage, 2)
            DiskTime = [math]::Round($diskTime, 2)
            NetworkBytesPerSec = [math]::Round($totalNetworkBytes / 1024 / 1024, 2) # Convert to MB/s
        }
        
        $performanceData += $sample
        
        # Display current values
        Write-Host "  CPU: $($sample.CPUUsage)%" -ForegroundColor $(if ($sample.CPUUsage -gt 80) {"Red"} elseif ($sample.CPUUsage -gt 60) {"Yellow"} else {"Green"})
        Write-Host "  Memory: $($sample.MemoryUsage)% (Available: $($sample.AvailableMemoryMB) MB)" -ForegroundColor $(if ($sample.MemoryUsage -gt 85) {"Red"} elseif ($sample.MemoryUsage -gt 70) {"Yellow"} else {"Green"})
        Write-Host "  Disk: $($sample.DiskTime)%" -ForegroundColor $(if ($sample.DiskTime -gt 80) {"Red"} elseif ($sample.DiskTime -gt 60) {"Yellow"} else {"Green"})
        Write-Host "  Network: $($sample.NetworkBytesPerSec) MB/s"
        
        if ($Detailed) {
            # Show top processes
            Write-Host "  Top CPU Processes:" -ForegroundColor Gray
            Get-Process | Sort-Object CPU -Descending | Select-Object -First 3 | ForEach-Object {
                Write-Host "    $($_.Name): $([math]::Round($_.CPU, 2))s" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        
    } catch {
        Write-Host "  Error collecting performance data: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for next sample (unless this is the last one)
    if ($i -lt $samples) {
        Start-Sleep -Seconds $Interval
    }
}

Write-Host ""
Write-Host "=== Performance Summary ===" -ForegroundColor Green

if ($performanceData.Count -gt 0) {
    # Calculate averages
    $avgCPU = ($performanceData | Measure-Object -Property CPUUsage -Average).Average
    $avgMemory = ($performanceData | Measure-Object -Property MemoryUsage -Average).Average
    $avgDisk = ($performanceData | Measure-Object -Property DiskTime -Average).Average
    $avgNetwork = ($performanceData | Measure-Object -Property NetworkBytesPerSec -Average).Average
    
    # Calculate maximums
    $maxCPU = ($performanceData | Measure-Object -Property CPUUsage -Maximum).Maximum
    $maxMemory = ($performanceData | Measure-Object -Property MemoryUsage -Maximum).Maximum
    $maxDisk = ($performanceData | Measure-Object -Property DiskTime -Maximum).Maximum
    $maxNetwork = ($performanceData | Measure-Object -Property NetworkBytesPerSec -Maximum).Maximum
    
    Write-Host "Average Performance:"
    Write-Host "  CPU Usage: $([math]::Round($avgCPU, 2))%"
    Write-Host "  Memory Usage: $([math]::Round($avgMemory, 2))%"
    Write-Host "  Disk Time: $([math]::Round($avgDisk, 2))%"
    Write-Host "  Network: $([math]::Round($avgNetwork, 2)) MB/s"
    Write-Host ""
    
    Write-Host "Peak Performance:"
    Write-Host "  Max CPU Usage: $([math]::Round($maxCPU, 2))%"
    Write-Host "  Max Memory Usage: $([math]::Round($maxMemory, 2))%"
    Write-Host "  Max Disk Time: $([math]::Round($maxDisk, 2))%"
    Write-Host "  Max Network: $([math]::Round($maxNetwork, 2)) MB/s"
    Write-Host ""
    
    # Performance assessment
    Write-Host "=== Performance Assessment ===" -ForegroundColor Yellow
    
    if ($avgCPU -gt 80) {
        Write-Host "⚠️  HIGH CPU USAGE - Average $([math]::Round($avgCPU, 2))%" -ForegroundColor Red
    } elseif ($avgCPU -gt 60) {
        Write-Host "⚠️  Elevated CPU usage - Average $([math]::Round($avgCPU, 2))%" -ForegroundColor Yellow
    } else {
        Write-Host "✅ CPU usage normal - Average $([math]::Round($avgCPU, 2))%" -ForegroundColor Green
    }
    
    if ($avgMemory -gt 85) {
        Write-Host "⚠️  HIGH MEMORY USAGE - Average $([math]::Round($avgMemory, 2))%" -ForegroundColor Red
    } elseif ($avgMemory -gt 70) {
        Write-Host "⚠️  Elevated memory usage - Average $([math]::Round($avgMemory, 2))%" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Memory usage normal - Average $([math]::Round($avgMemory, 2))%" -ForegroundColor Green
    }
    
    if ($avgDisk -gt 80) {
        Write-Host "⚠️  HIGH DISK USAGE - Average $([math]::Round($avgDisk, 2))%" -ForegroundColor Red
    } elseif ($avgDisk -gt 60) {
        Write-Host "⚠️  Elevated disk usage - Average $([math]::Round($avgDisk, 2))%" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Disk usage normal - Average $([math]::Round($avgDisk, 2))%" -ForegroundColor Green
    }
} else {
    Write-Host "No performance data collected" -ForegroundColor Red
}

Write-Host ""
Write-Host "End Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "    Performance Monitoring Complete     " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
'''


# ============================================================================
# PowerShell Integration Engine
# ============================================================================

class PowerShellIntegration:
    """
    Advanced PowerShell integration for Windows system administration.
    """
    
    def __init__(self, base_copilot: SysAdminCopilot):
        self.base_copilot = base_copilot
        self.logger = logging.getLogger("PowerShellIntegration")
        self.templates = PowerShellTemplates()
        
        # Check if running on Windows
        self.is_windows = platform.system() == "Windows"
        if not self.is_windows:
            self.logger.warning("PowerShell integration initialized on non-Windows system")
    
    async def execute_powershell_script(self, script_content: str, 
                                      profile: PowerShellProfile = None) -> Dict[str, Any]:
        """
        Execute PowerShell script with advanced options and safety controls.
        
        Args:
            script_content: PowerShell script to execute
            profile: Execution profile with settings
            
        Returns:
            Execution results dictionary
        """
        
        if not self.is_windows:
            return {
                "success": False,
                "error": "PowerShell integration requires Windows",
                "output": "",
                "exit_code": -1
            }
        
        if profile is None:
            profile = PowerShellProfile()
        
        try:
            self.logger.info("Executing PowerShell script")
            
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                # Add variable definitions if specified
                if profile.variables:
                    for var_name, var_value in profile.variables.items():
                        f.write(f'${var_name} = "{var_value}"\n')
                    f.write('\n')
                
                # Add module imports if specified
                if profile.modules_to_import:
                    for module in profile.modules_to_import:
                        f.write(f'Import-Module {module} -ErrorAction SilentlyContinue\n')
                    f.write('\n')
                
                # Add main script content
                f.write(script_content)
                script_path = f.name
            
            try:
                # Build PowerShell command
                cmd = ["powershell", "-ExecutionPolicy", profile.execution_policy.value]
                
                if profile.use_elevated_privileges:
                    # Note: This would require UAC prompt in interactive mode
                    cmd.extend(["-Verb", "RunAs"])
                
                cmd.extend(["-File", script_path])
                
                # Set working directory
                cwd = profile.working_directory or Path.cwd()
                
                # Execute script
                start_time = datetime.now()
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=profile.timeout_seconds,
                    cwd=cwd
                )
                end_time = datetime.now()
                
                execution_time = (end_time - start_time).total_seconds()
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "exit_code": result.returncode,
                    "execution_time_seconds": execution_time,
                    "script_path": script_path,
                    "command": ' '.join(cmd)
                }
                
            finally:
                # Clean up temporary file
                try:
                    Path(script_path).unlink()
                except Exception:
                    pass
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script execution timed out after {profile.timeout_seconds} seconds",
                "output": "",
                "exit_code": -1,
                "execution_time_seconds": profile.timeout_seconds
            }
            
        except Exception as e:
            self.logger.error(f"Error executing PowerShell script: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "exit_code": -1,
                "execution_time_seconds": 0.0
            }
    
    async def get_windows_system_info(self) -> WindowsSystemInfo:
        """Get comprehensive Windows system information"""
        
        if not self.is_windows:
            raise RuntimeError("Windows system information requires Windows OS")
        
        try:
            script_content = '''
            $info = Get-ComputerInfo
            $output = @{
                WindowsVersion = $info.WindowsProductName
                BuildNumber = $info.WindowsBuildLabEx
                Edition = $info.WindowsEditionId
                Architecture = $info.CsSystemType
                DomainJoined = $info.CsPartOfDomain
                DomainName = $info.CsDomain
                ComputerName = $info.CsName
                LastBootTime = $info.CsBootupState
                WindowsUpdateStatus = "Unknown"
                DefenderStatus = "Unknown"
                FirewallStatus = "Unknown"
                PendingReboot = $false
            }
            
            # Check Windows Update status
            try {
                $updateSession = New-Object -ComObject Microsoft.Update.Session
                $updateSearcher = $updateSession.CreateUpdateSearcher()
                $searchResult = $updateSearcher.Search("IsInstalled=0")
                $output.WindowsUpdateStatus = "$($searchResult.Updates.Count) pending updates"
            } catch {
                $output.WindowsUpdateStatus = "Unable to check"
            }
            
            # Check Defender status
            try {
                $defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
                if ($defenderStatus) {
                    $output.DefenderStatus = if ($defenderStatus.AntivirusEnabled) { "Enabled" } else { "Disabled" }
                }
            } catch {
                $output.DefenderStatus = "Unable to check"
            }
            
            # Check Firewall status
            try {
                $firewallProfiles = Get-NetFirewallProfile -ErrorAction SilentlyContinue
                $enabledProfiles = $firewallProfiles | Where-Object { $_.Enabled -eq $true }
                $output.FirewallStatus = "$($enabledProfiles.Count)/$($firewallProfiles.Count) profiles enabled"
            } catch {
                $output.FirewallStatus = "Unable to check"
            }
            
            # Check for pending reboot
            $pendingReboot = $false
            if (Get-ChildItem "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired" -ErrorAction SilentlyContinue) {
                $pendingReboot = $true
            }
            $output.PendingReboot = $pendingReboot
            
            # Get services count
            $services = Get-Service
            $output.RunningServicesCount = ($services | Where-Object {$_.Status -eq "Running"}).Count
            $output.StoppedServicesCount = ($services | Where-Object {$_.Status -eq "Stopped"}).Count
            
            # Output as JSON
            $output | ConvertTo-Json
            '''
            
            result = await self.execute_powershell_script(script_content)
            
            if result["success"]:
                data = json.loads(result["output"])
                
                return WindowsSystemInfo(
                    windows_version=data.get("WindowsVersion", "Unknown"),
                    build_number=data.get("BuildNumber", "Unknown"),
                    edition=data.get("Edition", "Unknown"),
                    architecture=data.get("Architecture", "Unknown"),
                    domain_joined=data.get("DomainJoined", False),
                    domain_name=data.get("DomainName", ""),
                    computer_name=data.get("ComputerName", ""),
                    last_boot_time=datetime.now(),  # Simplified
                    windows_update_status=data.get("WindowsUpdateStatus", "Unknown"),
                    defender_status=data.get("DefenderStatus", "Unknown"),
                    firewall_status=data.get("FirewallStatus", "Unknown"),
                    pending_reboot=data.get("PendingReboot", False),
                    installed_features=[],  # Would require additional script
                    running_services_count=data.get("RunningServicesCount", 0),
                    stopped_services_count=data.get("StoppedServicesCount", 0)
                )
            else:
                raise RuntimeError(f"Failed to get system info: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Error getting Windows system info: {e}")
            
            # Return minimal info
            return WindowsSystemInfo(
                windows_version="Unknown",
                build_number="Unknown",
                edition="Unknown",
                architecture="Unknown",
                domain_joined=False,
                domain_name=None,
                computer_name="Unknown",
                last_boot_time=datetime.now(),
                windows_update_status="Unknown",
                defender_status="Unknown",
                firewall_status="Unknown",
                pending_reboot=False,
                installed_features=[],
                running_services_count=0,
                stopped_services_count=0
            )
    
    async def manage_windows_service(self, service_name: str, action: str) -> Dict[str, Any]:
        """
        Manage Windows services with PowerShell.
        
        Args:
            service_name: Name of the Windows service
            action: Action to perform (status, start, stop, restart)
            
        Returns:
            Operation result dictionary
        """
        
        if not self.is_windows:
            return {"success": False, "error": "Windows service management requires Windows OS"}
        
        try:
            # Create service management script
            script_content = self.templates.service_management()
            
            # Set up execution profile with parameters
            profile = PowerShellProfile()
            profile.variables = {
                "Action": action,
                "ServiceName": service_name
            }
            
            result = await self.execute_powershell_script(script_content, profile)
            
            return {
                "success": result["success"],
                "service_name": service_name,
                "action": action,
                "output": result["output"],
                "error": result.get("error", ""),
                "execution_time": result["execution_time_seconds"]
            }
            
        except Exception as e:
            self.logger.error(f"Error managing Windows service: {e}")
            return {
                "success": False,
                "service_name": service_name,
                "action": action,
                "error": str(e)
            }
    
    async def create_system_cleanup_task(self) -> Task:
        """Create a comprehensive system cleanup task"""
        
        from sysadmin_copilot import Task, TaskType, TaskPriority, ScriptType
        import hashlib
        
        task = Task(
            id=hashlib.md5(f"windows_cleanup_{datetime.now()}".encode()).hexdigest()[:8],
            name="Windows System Cleanup",
            description="Comprehensive Windows system cleanup including temp files, cache, and optimization",
            task_type=TaskType.MAINTENANCE,
            priority=TaskPriority.MEDIUM,
            script_content=self.templates.cleanup_system(),
            script_type=ScriptType.POWERSHELL,
            requires_admin=True,
            requires_confirmation=True,
            ai_confidence=0.9,
            ai_reasoning="Comprehensive cleanup using proven PowerShell techniques"
        )
        
        return task
    
    async def create_performance_monitoring_task(self, duration: int = 60) -> Task:
        """Create a performance monitoring task"""
        
        from sysadmin_copilot import Task, TaskType, TaskPriority, ScriptType
        import hashlib
        
        # Create script with duration parameter
        script_content = self.templates.performance_monitoring()
        
        task = Task(
            id=hashlib.md5(f"performance_monitor_{datetime.now()}".encode()).hexdigest()[:8],
            name="Windows Performance Monitoring",
            description=f"Monitor Windows system performance for {duration} seconds with detailed analysis",
            task_type=TaskType.MONITORING,
            priority=TaskPriority.MEDIUM,
            script_content=script_content,
            script_type=ScriptType.POWERSHELL,
            requires_admin=False,
            requires_confirmation=False,
            ai_confidence=0.9,
            ai_reasoning="Real-time performance monitoring using Windows performance counters"
        )
        
        # Add duration as a variable
        task.prerequisites = [f"duration:{duration}"]
        
        return task
    
    async def create_system_info_task(self) -> Task:
        """Create comprehensive system information task"""
        
        from sysadmin_copilot import Task, TaskType, TaskPriority, ScriptType
        import hashlib
        
        task = Task(
            id=hashlib.md5(f"windows_sysinfo_{datetime.now()}".encode()).hexdigest()[:8],
            name="Windows System Information",
            description="Comprehensive Windows system information including security status, updates, and performance",
            task_type=TaskType.MONITORING,
            priority=TaskPriority.LOW,
            script_content=self.templates.get_system_information(),
            script_type=ScriptType.POWERSHELL,
            requires_admin=False,
            requires_confirmation=False,
            ai_confidence=0.95,
            ai_reasoning="Comprehensive system information gathering using Windows Management Instrumentation"
        )
        
        return task


# ============================================================================
# Enhanced SysAdmin Copilot with PowerShell Integration
# ============================================================================

class EnhancedSysAdminCopilot(SysAdminCopilot):
    """
    Enhanced SysAdmin Copilot with deep PowerShell integration for Windows environments.
    """
    
    def __init__(self):
        super().__init__()
        self.powershell = PowerShellIntegration(self)
        self.logger = logging.getLogger("EnhancedSysAdminCopilot")
        
        if platform.system() == "Windows":
            self.logger.info("Enhanced SysAdmin Copilot initialized with PowerShell integration")
        else:
            self.logger.info("Enhanced SysAdmin Copilot initialized (PowerShell features limited on non-Windows)")
    
    async def suggest_tasks(self, context_description: str = "") -> List[Task]:
        """Enhanced task suggestions with Windows-specific tasks"""
        
        # Get base suggestions
        base_suggestions = await super().suggest_tasks(context_description)
        
        # Add Windows-specific suggestions if on Windows
        if platform.system() == "Windows":
            try:
                # Add Windows cleanup task
                cleanup_task = await self.powershell.create_system_cleanup_task()
                base_suggestions.append(cleanup_task)
                
                # Add system info task
                sysinfo_task = await self.powershell.create_system_info_task()
                base_suggestions.append(sysinfo_task)
                
                # Add performance monitoring if system seems loaded
                context = await self.context_manager.get_system_context()
                health_metrics = await self.health_monitor.collect_metrics()
                
                if (health_metrics.cpu_usage_percent > 70 or 
                    health_metrics.memory_usage_percent > 80):
                    
                    perf_task = await self.powershell.create_performance_monitoring_task(120)  # 2-minute monitoring
                    perf_task.priority = TaskPriority.HIGH
                    perf_task.ai_reasoning = "High resource usage detected - detailed monitoring recommended"
                    base_suggestions.append(perf_task)
                
                self.logger.info(f"Added {len(base_suggestions) - len(base_suggestions)} Windows-specific task suggestions")
                
            except Exception as e:
                self.logger.error(f"Error adding Windows-specific suggestions: {e}")
        
        return base_suggestions
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Enhanced system health with Windows-specific information"""
        
        # Get base health information
        base_health = await super().get_system_health()
        
        # Add Windows-specific health information if on Windows
        if platform.system() == "Windows":
            try:
                windows_info = await self.powershell.get_windows_system_info()
                
                # Add Windows-specific health data
                base_health["windows_info"] = {
                    "version": windows_info.windows_version,
                    "build": windows_info.build_number,
                    "domain_joined": windows_info.domain_joined,
                    "pending_reboot": windows_info.pending_reboot,
                    "windows_update_status": windows_info.windows_update_status,
                    "defender_status": windows_info.defender_status,
                    "firewall_status": windows_info.firewall_status,
                    "services": {
                        "running": windows_info.running_services_count,
                        "stopped": windows_info.stopped_services_count
                    }
                }
                
                # Add Windows-specific recommendations
                if windows_info.pending_reboot:
                    base_health["recommendations"].append("System reboot required - schedule maintenance window")
                
                if "pending" in windows_info.windows_update_status.lower():
                    base_health["recommendations"].append("Windows updates are pending - consider installing")
                
                if "disabled" in windows_info.defender_status.lower():
                    base_health["issues"].append("Windows Defender is disabled")
                    base_health["recommendations"].append("Enable Windows Defender for security protection")
                
                self.logger.info("Enhanced system health with Windows-specific information")
                
            except Exception as e:
                self.logger.error(f"Error getting Windows-specific health info: {e}")
                base_health["windows_info"] = {"error": str(e)}
        
        return base_health
    
    async def execute_powershell_command(self, command: str, 
                                       elevated: bool = False) -> Dict[str, Any]:
        """
        Execute a single PowerShell command with enhanced error handling.
        
        Args:
            command: PowerShell command to execute
            elevated: Whether to run with elevated privileges
            
        Returns:
            Execution result dictionary
        """
        
        profile = PowerShellProfile()
        profile.use_elevated_privileges = elevated
        
        return await self.powershell.execute_powershell_script(command, profile)


# ============================================================================
# Example Usage and Testing
# ============================================================================

async def main():
    """Example usage of the Enhanced SysAdmin Copilot with PowerShell integration"""
    
    print("🚀 Enhanced SysAdmin Copilot - PowerShell Integration")
    print("=" * 80)
    
    if platform.system() != "Windows":
        print("⚠️  PowerShell integration features are limited on non-Windows systems")
        print("Running basic demonstration...")
    
    # Initialize enhanced copilot
    copilot = EnhancedSysAdminCopilot()
    
    # Get enhanced system health
    print("\n📊 Enhanced System Health Analysis:")
    health = await copilot.get_system_health()
    print(f"Health Score: {health['health_score']:.1f}/100")
    
    if "windows_info" in health and "error" not in health["windows_info"]:
        win_info = health["windows_info"]
        print(f"Windows Version: {win_info['version']}")
        print(f"Domain Joined: {win_info['domain_joined']}")
        print(f"Pending Reboot: {win_info['pending_reboot']}")
        print(f"Update Status: {win_info['windows_update_status']}")
        print(f"Defender Status: {win_info['defender_status']}")
        print(f"Services: {win_info['services']['running']} running, {win_info['services']['stopped']} stopped")
    
    # Get enhanced task suggestions
    print(f"\n🎯 Enhanced Task Suggestions:")
    suggestions = await copilot.suggest_tasks("Windows maintenance and optimization")
    
    for i, task in enumerate(suggestions[:4], 1):
        print(f"{i}. {task.name}")
        print(f"   Type: {task.task_type.value}")
        print(f"   Priority: {task.priority.value}")
        print(f"   Requires Admin: {task.requires_admin}")
        print(f"   AI Confidence: {task.ai_confidence:.1f}")
        print()
    
    # Execute a PowerShell command if on Windows
    if platform.system() == "Windows":
        print("🔧 PowerShell Command Execution Example:")
        result = await copilot.execute_powershell_command("Get-Process | Select-Object -First 5 Name, CPU")
        
        if result["success"]:
            print("✅ Command executed successfully!")
            print("Output preview:")
            print(result["output"][:200] + "..." if len(result["output"]) > 200 else result["output"])
        else:
            print("❌ Command failed")
            print(f"Error: {result['error']}")
    
    # Execute a Windows-specific task if available
    windows_tasks = [t for t in suggestions if "Windows" in t.name]
    if windows_tasks and platform.system() == "Windows":
        task = windows_tasks[0]
        print(f"\n⚡ Executing Windows Task: {task.name}")
        
        # Execute without confirmation for demo (normally would require confirmation)
        result = await copilot.execute_task(task, confirm=False)
        
        print(f"Status: {result.status.value}")
        if result.success:
            print("✅ Windows task completed successfully!")
        else:
            print("❌ Windows task failed")
            if result.error_message:
                print(f"Error: {result.error_message}")
    
    print(f"\n🎉 Enhanced SysAdmin Copilot demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())

