# HEIMNETZ PROJECT - CLEANUP SAFETY VALIDATOR v10.1
# Pre-cleanup verification and post-cleanup validation
# Date: 2025-07-16

param(
    [switch]$PreCleanup = $false,
    [switch]$PostCleanup = $false,
    [string]$BackupPath = ""
)

$ProjectRoot = "k:\Project Heimnetz"
$ValidationReport = @{
    Timestamp = Get-Date
    Phase = if ($PreCleanup) { "PRE_CLEANUP" } else { "POST_CLEANUP" }
    CriticalFiles = @()
    ConfigurationStatus = @()
    SystemHealth = @()
    Recommendations = @()
}

Write-Host "HEIMNETZ CLEANUP SAFETY VALIDATOR v10.1" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Phase: $($ValidationReport.Phase)" -ForegroundColor Yellow
Write-Host ""

function Test-CriticalFile {
    param([string]$Path, [string]$Description, [bool]$Required = $true)
    
    $Exists = Test-Path $Path
    $Status = if ($Exists) { "FOUND" } else { if ($Required) { "MISSING_CRITICAL" } else { "MISSING_OPTIONAL" } }
    $Color = switch ($Status) {
        "FOUND" { "Green" }
        "MISSING_CRITICAL" { "Red" }
        "MISSING_OPTIONAL" { "Yellow" }
    }
    
    Write-Host "  [$Status] $Description" -ForegroundColor $Color
    if ($Exists) {
        $Size = (Get-Item $Path).Length
        Write-Host "    Size: $([math]::Round($Size / 1KB, 2)) KB" -ForegroundColor Gray
    }
    
    $ValidationReport.CriticalFiles += @{
        Path = $Path
        Description = $Description
        Exists = $Exists
        Required = $Required
        Status = $Status
        Size = if ($Exists) { (Get-Item $Path).Length } else { 0 }
    }
    
    return $Exists
}

function Test-Directory {
    param([string]$Path, [string]$Description, [bool]$Required = $true)
    
    $Exists = Test-Path $Path -PathType Container
    $Status = if ($Exists) { "FOUND" } else { if ($Required) { "MISSING_CRITICAL" } else { "MISSING_OPTIONAL" } }
    $Color = switch ($Status) {
        "FOUND" { "Green" }
        "MISSING_CRITICAL" { "Red" }
        "MISSING_OPTIONAL" { "Yellow" }
    }
    
    Write-Host "  [$Status] $Description" -ForegroundColor $Color
    if ($Exists) {
        $FileCount = (Get-ChildItem $Path -File -Recurse | Measure-Object).Count
        Write-Host "    Files: $FileCount" -ForegroundColor Gray
    }
    
    return $Exists
}

function Test-PythonEnvironment {
    Write-Host ""
    Write-Host "PYTHON ENVIRONMENT STATUS" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    
    try {
        $PythonVersion = python --version 2>&1
        Write-Host "  [FOUND] Python: $PythonVersion" -ForegroundColor Green
        
        # Test pip
        $PipVersion = pip --version 2>&1
        Write-Host "  [FOUND] Pip: $PipVersion" -ForegroundColor Green
        
        # Test critical packages
        $CriticalPackages = @("flask", "requests", "psutil", "cryptography")
        foreach ($Package in $CriticalPackages) {
            try {
                $PackageInfo = pip show $Package 2>&1
                if ($PackageInfo -match "Version:") {
                    $Version = ($PackageInfo -split "`n" | Where-Object { $_ -match "Version:" }).Split(":")[1].Trim()
                    Write-Host "  [FOUND] $Package v$Version" -ForegroundColor Green
                } else {
                    Write-Host "  [MISSING] $Package" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "  [ERROR] Cannot check $Package" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "  [ERROR] Python not found or not in PATH" -ForegroundColor Red
        $ValidationReport.SystemHealth += @{
            Component = "Python"
            Status = "ERROR"
            Message = "Python not accessible"
        }
    }
}

# CRITICAL FILES VALIDATION
Write-Host "CRITICAL FILES VALIDATION" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Core application files
Test-CriticalFile "$ProjectRoot\main.py" "Main Application Entry Point" $true
Test-CriticalFile "$ProjectRoot\api_bridge.py" "API Bridge Module" $true
Test-CriticalFile "$ProjectRoot\integrated_web_server.py" "Integrated Web Server" $true
Test-CriticalFile "$ProjectRoot\requirements.txt" "Python Dependencies" $true

# Configuration files
Test-CriticalFile "$ProjectRoot\config\heimnetz_unified.json" "Unified Configuration" $true
Test-CriticalFile "$ProjectRoot\docker\heimnetz_docker.json" "Docker Configuration" $false

# Active NoxPanel (AI directory)
Test-CriticalFile "$ProjectRoot\AI\NoxPanel\main.py" "Active NoxPanel Entry Point" $true
Test-CriticalFile "$ProjectRoot\AI\NoxPanel\requirements.txt" "NoxPanel Dependencies" $true

# Documentation
Test-CriticalFile "$ProjectRoot\HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md" "Master Documentation v10.0" $true
Test-CriticalFile "$ProjectRoot\README.md" "Project README" $true

Write-Host ""
Write-Host "CRITICAL DIRECTORIES VALIDATION" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Core directories
Test-Directory "$ProjectRoot\AI\NoxPanel" "Active NoxPanel Implementation" $true
Test-Directory "$ProjectRoot\config" "Configuration Directory" $true
Test-Directory "$ProjectRoot\data" "Data Directory" $true
Test-Directory "$ProjectRoot\docs" "Documentation Directory" $true

# Validate that we haven't accidentally removed active components
Test-Directory "$ProjectRoot\AI\NoxPanel\noxcore" "NoxPanel Core" $true
Test-Directory "$ProjectRoot\AI\NoxPanel\webpanel" "NoxPanel Web Interface" $true

if ($PreCleanup) {
    Write-Host ""
    Write-Host "PRE-CLEANUP ANALYSIS" -ForegroundColor Yellow
    Write-Host "====================" -ForegroundColor Yellow
    
    # Calculate current sizes
    $DuplicateVenv = "$ProjectRoot\NoxPanel\venv"
    $NodeModules = "$ProjectRoot\AI\NoxPanel\frontend\node_modules"
    
    if (Test-Path $DuplicateVenv) {
        $VenvSize = Get-ChildItem $DuplicateVenv -Recurse -File | Measure-Object -Property Length -Sum
        Write-Host "  Duplicate venv size: $([math]::Round($VenvSize.Sum / 1MB, 2)) MB" -ForegroundColor Yellow
    }
    
    if (Test-Path $NodeModules) {
        $NodeSize = Get-ChildItem $NodeModules -Recurse -File | Measure-Object -Property Length -Sum
        Write-Host "  Node modules size: $([math]::Round($NodeSize.Sum / 1MB, 2)) MB" -ForegroundColor Yellow
    }
    
    # Check for cache files
    $CacheFiles = Get-ChildItem $ProjectRoot -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue
    Write-Host "  Python cache directories found: $($CacheFiles.Count)" -ForegroundColor Yellow
}

if ($PostCleanup) {
    Write-Host ""
    Write-Host "POST-CLEANUP VALIDATION" -ForegroundColor Green
    Write-Host "=======================" -ForegroundColor Green
    
    # Test system functionality
    Write-Host ""
    Write-Host "SYSTEM FUNCTIONALITY TEST" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    
    # Test if main.py can be imported (syntax check)
    try {
        $SyntaxCheck = python -m py_compile "$ProjectRoot\main.py" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [PASS] main.py syntax valid" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] main.py syntax error: $SyntaxCheck" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  [ERROR] Cannot test main.py syntax" -ForegroundColor Red
    }
    
    # Test if NoxPanel main can be imported
    try {
        $NoxSyntaxCheck = python -m py_compile "$ProjectRoot\AI\NoxPanel\main.py" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [PASS] NoxPanel main.py syntax valid" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] NoxPanel main.py syntax error: $NoxSyntaxCheck" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  [ERROR] Cannot test NoxPanel main.py syntax" -ForegroundColor Red
    }
}

# Python environment check
Test-PythonEnvironment

# SUMMARY AND RECOMMENDATIONS
Write-Host ""
Write-Host "VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

$CriticalMissing = $ValidationReport.CriticalFiles | Where-Object { $_.Required -and -not $_.Exists }
$OptionalMissing = $ValidationReport.CriticalFiles | Where-Object { -not $_.Required -and -not $_.Exists }

Write-Host "Critical files found: $($ValidationReport.CriticalFiles | Where-Object { $_.Required -and $_.Exists } | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Green
Write-Host "Critical files missing: $($CriticalMissing | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Red
Write-Host "Optional files missing: $($OptionalMissing | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Yellow

if ($CriticalMissing.Count -gt 0) {
    Write-Host ""
    Write-Host "CRITICAL ISSUES FOUND:" -ForegroundColor Red
    foreach ($Missing in $CriticalMissing) {
        Write-Host "  - $($Missing.Description): $($Missing.Path)" -ForegroundColor Red
    }
    $ValidationReport.Recommendations += "CRITICAL: Restore missing files before proceeding"
}

if ($PreCleanup) {
    Write-Host ""
    Write-Host "PRE-CLEANUP RECOMMENDATIONS:" -ForegroundColor Yellow
    Write-Host "  1. Create backup of critical configuration files" -ForegroundColor White
    Write-Host "  2. Document current working directory for restoration" -ForegroundColor White
    Write-Host "  3. Test 8-gate system before cleanup" -ForegroundColor White
    Write-Host "  4. Run cleanup in DRY RUN mode first" -ForegroundColor White
}

if ($PostCleanup) {
    Write-Host ""
    Write-Host "POST-CLEANUP RECOMMENDATIONS:" -ForegroundColor Green
    Write-Host "  1. Test complete 8-gate system functionality" -ForegroundColor White
    Write-Host "  2. Verify web interface accessibility" -ForegroundColor White
    Write-Host "  3. Check log files for any new errors" -ForegroundColor White
    Write-Host "  4. Run full integration test suite" -ForegroundColor White
}

# Save validation report
$ReportPath = "$ProjectRoot\AI\NoxPanel\validation_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$ValidationReport | ConvertTo-Json -Depth 3 | Out-File $ReportPath -Encoding UTF8

Write-Host ""
Write-Host "Validation report saved: $ReportPath" -ForegroundColor Gray

# Overall status
if ($CriticalMissing.Count -eq 0) {
    Write-Host ""
    Write-Host "VALIDATION STATUS: PASSED" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "VALIDATION STATUS: FAILED" -ForegroundColor Red
    exit 1
}
