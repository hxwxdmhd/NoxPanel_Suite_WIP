# HEIMNETZ PROJECT - COMPREHENSIVE CLEANUP SCRIPT v10.1
# PHASE 1: CRITICAL SPACE RECOVERY (1GB+ savings)
# Date: 2025-07-16

param(
    [switch]$DryRun = $false,
    [switch]$Aggressive = $false,
    [switch]$SafeMode = $true
)

Write-Host "HEIMNETZ PROJECT - COMPREHENSIVE CLEANUP v10.1" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ProjectRoot = "k:\Project Heimnetz"
$TotalSaved = 0
$ItemsProcessed = 0

# Create cleanup report
$ReportPath = "$ProjectRoot\AI\NoxPanel\cleanup_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$CleanupReport = @{
    StartTime = Get-Date
    Mode = if ($DryRun) { "DRY RUN" } else { "EXECUTION" }
    Actions = @()
    TotalSaved = 0
    ItemsProcessed = 0
}

function Add-CleanupAction {
    param($Action, $Path, $Size, $Status)
    $CleanupReport.Actions += @{
        Action = $Action
        Path = $Path
        SizeMB = [math]::Round($Size / 1MB, 2)
        Status = $Status
        Timestamp = Get-Date
    }
}

function Get-DirectorySize {
    param([string]$Path)
    if (Test-Path $Path) {
        return (Get-ChildItem $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum
    }
    return 0
}

function Remove-SafeDirectory {
    param([string]$Path, [string]$Description)
    
    if (Test-Path $Path) {
        $Size = Get-DirectorySize $Path
        Write-Host "  ANALYZING: $Description" -ForegroundColor Yellow
        Write-Host "    Path: $Path" -ForegroundColor Gray
        Write-Host "    Size: $([math]::Round($Size / 1MB, 2)) MB" -ForegroundColor Gray
        
        if ($DryRun) {
            Write-Host "    [DRY RUN] Would remove $([math]::Round($Size / 1MB, 2)) MB" -ForegroundColor Blue
            Add-CleanupAction "SIMULATE_REMOVE" $Path $Size "DRY_RUN"
        } else {
            try {
                Remove-Item -Path $Path -Recurse -Force
                Write-Host "    [REMOVED] Freed $([math]::Round($Size / 1MB, 2)) MB" -ForegroundColor Green
                Add-CleanupAction "REMOVE" $Path $Size "SUCCESS"
                $script:TotalSaved += $Size
            }
            catch {
                Write-Host "    [ERROR] Failed to remove: $($_.Exception.Message)" -ForegroundColor Red
                Add-CleanupAction "REMOVE" $Path $Size "FAILED"
            }
        }
        $script:ItemsProcessed++
    } else {
        Write-Host "  [SKIP] Not found: $Description" -ForegroundColor Yellow
        Add-CleanupAction "SKIP" $Path 0 "NOT_FOUND"
    }
}

function Archive-Directory {
    param([string]$SourcePath, [string]$ArchivePath, [string]$Description)
    
    if (Test-Path $SourcePath) {
        $Size = Get-DirectorySize $SourcePath
        Write-Host "  ARCHIVING: $Description" -ForegroundColor Yellow
        
        # Create archive directory
        $ArchiveDir = Split-Path $ArchivePath -Parent
        if (!(Test-Path $ArchiveDir)) {
            New-Item -Path $ArchiveDir -ItemType Directory -Force | Out-Null
        }
        
        if ($DryRun) {
            Write-Host "    [DRY RUN] Would archive $([math]::Round($Size / 1MB, 2)) MB" -ForegroundColor Blue
            Add-CleanupAction "SIMULATE_ARCHIVE" $SourcePath $Size "DRY_RUN"
        } else {
            try {
                Move-Item -Path $SourcePath -Destination $ArchivePath -Force
                Write-Host "    [ARCHIVED] Moved $([math]::Round($Size / 1MB, 2)) MB" -ForegroundColor Green
                Add-CleanupAction "ARCHIVE" $SourcePath $Size "SUCCESS"
            }
            catch {
                Write-Host "    [ERROR] Failed to archive: $($_.Exception.Message)" -ForegroundColor Red
                Add-CleanupAction "ARCHIVE" $SourcePath $Size "FAILED"
            }
        }
        $script:ItemsProcessed++
    }
}

Write-Host ""
Write-Host "PHASE 1: CRITICAL SPACE RECOVERY" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 1.1 Virtual Environment Cleanup
Write-Host ""
Write-Host "1.1 VIRTUAL ENVIRONMENT CONSOLIDATION" -ForegroundColor Cyan

$DuplicateVenv = "$ProjectRoot\NoxPanel\venv"
Remove-SafeDirectory $DuplicateVenv "Duplicate Virtual Environment"

# 1.2 Node Modules Cleanup  
Write-Host ""
Write-Host "1.2 NODE MODULES CLEANUP" -ForegroundColor Cyan

$NodeModules = "$ProjectRoot\AI\NoxPanel\frontend\node_modules"
if ($Aggressive) {
    Remove-SafeDirectory $NodeModules "Frontend Node Modules"
} else {
    Write-Host "  [SKIP] Node modules (use -Aggressive to remove)" -ForegroundColor Yellow
}

# 1.3 Cache Files Purge
Write-Host ""
Write-Host "1.3 CACHE FILES CLEANUP" -ForegroundColor Cyan

$CacheDirectories = @(
    "$ProjectRoot\AI\NoxPanel\__pycache__",
    "$ProjectRoot\AI\NoxPanel\noxcore\__pycache__",
    "$ProjectRoot\AI\NoxPanel\webpanel\__pycache__",
    "$ProjectRoot\AI\NoxPanel\tests\__pycache__",
    "$ProjectRoot\AI\NoxPanel\tests\.pytest_cache",
    "$ProjectRoot\AI\__pycache__",
    "$ProjectRoot\.pytest_cache",
    "$ProjectRoot\NoxPanel\webpanel\__pycache__",
    "$ProjectRoot\NoxPanel\noxcore\__pycache__"
)

foreach ($CacheDir in $CacheDirectories) {
    Remove-SafeDirectory $CacheDir "Python Cache Directory"
}

# Find additional cache directories
$AdditionalCaches = Get-ChildItem $ProjectRoot -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue
foreach ($Cache in $AdditionalCaches) {
    $FullPath = Join-Path $ProjectRoot $Cache
    Remove-SafeDirectory $FullPath "Additional Python Cache"
}

Write-Host ""
Write-Host "PHASE 2: ARCHITECTURE CONSOLIDATION" -ForegroundColor Green  
Write-Host "====================================" -ForegroundColor Green

# 2.1 Multiple NoxPanel Implementations
Write-Host ""
Write-Host "2.1 NOXPANEL IMPLEMENTATION CONSOLIDATION" -ForegroundColor Cyan

$LegacyNoxPanel = "$ProjectRoot\NoxPanel"
$ArchiveTarget = "$ProjectRoot\archive\legacy_implementations\NoxPanel_$(Get-Date -Format 'yyyyMMdd')"

if ($Aggressive) {
    Archive-Directory $LegacyNoxPanel $ArchiveTarget "Legacy NoxPanel Implementation"
} else {
    Write-Host "  [SKIP] Legacy NoxPanel archival (use -Aggressive to archive)" -ForegroundColor Yellow
}

# 2.2 Nested AI Directory
$NestedAI = "$ProjectRoot\AI\AI"
if (Test-Path $NestedAI) {
    Remove-SafeDirectory $NestedAI "Nested AI Directory"
}

# 2.3 Archive Old Test Results
Write-Host ""
Write-Host "2.2 TEST ARTIFACTS CLEANUP" -ForegroundColor Cyan

$TestResultsDir = "$ProjectRoot\AI\NoxPanel\archive\test_results"
if (Test-Path $TestResultsDir) {
    $OldTestFiles = Get-ChildItem $TestResultsDir -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
    foreach ($File in $OldTestFiles) {
        $Size = $File.Length
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would remove old test file: $($File.Name)" -ForegroundColor Blue
        } else {
            Remove-Item $File.FullName -Force
            Write-Host "  [REMOVED] Old test file: $($File.Name)" -ForegroundColor Green
            $TotalSaved += $Size
        }
        $ItemsProcessed++
    }
}

Write-Host ""
Write-Host "PHASE 3: LOG FILE MANAGEMENT" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

# 3.1 Consolidate and Clean Logs
$LogDirectories = @(
    "$ProjectRoot\data\logs",
    "$ProjectRoot\AI\NoxPanel\logs",
    "$ProjectRoot\NoxPanel\data\logs"
)

foreach ($LogDir in $LogDirectories) {
    if (Test-Path $LogDir) {
        $OldLogs = Get-ChildItem $LogDir -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
        foreach ($Log in $OldLogs) {
            $Size = $Log.Length
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would remove old log: $($Log.Name)" -ForegroundColor Blue
            } else {
                Remove-Item $Log.FullName -Force
                Write-Host "  [REMOVED] Old log file: $($Log.Name)" -ForegroundColor Green
                $TotalSaved += $Size
            }
            $ItemsProcessed++
        }
    }
}

# CLEANUP SUMMARY
Write-Host ""
Write-Host "CLEANUP SUMMARY" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

$CleanupReport.TotalSaved = $TotalSaved
$CleanupReport.ItemsProcessed = $ItemsProcessed
$CleanupReport.EndTime = Get-Date

Write-Host "Mode: $($CleanupReport.Mode)" -ForegroundColor Yellow
Write-Host "Items Processed: $ItemsProcessed" -ForegroundColor White
Write-Host "Total Space Saved: $([math]::Round($TotalSaved / 1MB, 2)) MB" -ForegroundColor Green
Write-Host "Total Space Saved: $([math]::Round($TotalSaved / 1GB, 2)) GB" -ForegroundColor Green

# Save report
$CleanupReport | ConvertTo-Json -Depth 3 | Out-File $ReportPath -Encoding UTF8
Write-Host "Report saved: $ReportPath" -ForegroundColor Gray

# Recommendations
Write-Host ""
Write-Host "NEXT STEPS RECOMMENDED:" -ForegroundColor Yellow
if (-not $Aggressive) {
    Write-Host "  1. Run with -Aggressive for maximum cleanup" -ForegroundColor White
}
Write-Host "  2. Review cleanup report for verification" -ForegroundColor White
Write-Host "  3. Test 8-gate system after cleanup" -ForegroundColor White
Write-Host "  4. Run 'npm install' if frontend development needed" -ForegroundColor White

Write-Host ""
Write-Host "CLEANUP COMPLETED!" -ForegroundColor Green
