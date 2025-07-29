# NoxPanel Test Runner - PowerShell Edition
# ADHD-friendly test execution with clear progress indicators

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Quick,
    [switch]$Coverage,
    [switch]$CheckDeps,
    [switch]$Install,
    [switch]$Help
)

# ADHD-friendly output with emojis and clear formatting
function Write-Progress-Message {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    switch ($Type) {
        "Success" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "Error"   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "Info"    { Write-Host "[$timestamp] 🔵 $Message" -ForegroundColor Cyan }
        "Running" { Write-Host "[$timestamp] 🏃 $Message" -ForegroundColor Blue }
    }
}

function Show-Help {
    Write-Host @"
🎯 NoxPanel Test Runner - PowerShell Edition

USAGE:
    .\run_tests.ps1 [OPTIONS]

OPTIONS:
    -Backend        Run backend API tests only
    -Frontend       Run frontend component tests only  
    -Quick          Run quick smoke tests for rapid feedback
    -Coverage       Generate coverage reports
    -CheckDeps      Check if test dependencies are installed
    -Install        Install missing test dependencies
    -Help           Show this help message

EXAMPLES:
    .\run_tests.ps1                    # Run all tests
    .\run_tests.ps1 -Backend          # Backend tests only
    .\run_tests.ps1 -Quick            # Quick smoke tests
    .\run_tests.ps1 -Coverage         # With coverage report
    .\run_tests.ps1 -CheckDeps        # Check dependencies
    .\run_tests.ps1 -Install          # Install dependencies

📋 ADHD-FRIENDLY FEATURES:
    • Clear progress indicators with emojis
    • Estimated time remaining
    • Simple pass/fail feedback
    • Minimal cognitive load
    • Quick interrupt recovery

"@
}

function Test-PythonPackage {
    param([string]$PackageName)
    
    try {
        $result = & python -c "import $($PackageName.Replace('-', '_')); print('OK')" 2>$null
        return $result -eq "OK"
    }
    catch {
        return $false
    }
}

function Install-Dependencies {
    Write-Progress-Message "Installing test dependencies..." "Running"
    
    $dependencies = @(
        "pytest",
        "pytest-cov", 
        "pytest-html",
        "pytest-asyncio",
        "faker",
        "requests"
    )
    
    $toInstall = @()
    
    foreach ($dep in $dependencies) {
        if (-not (Test-PythonPackage $dep)) {
            $toInstall += $dep
            Write-Progress-Message "Missing: $dep" "Warning"
        }
        else {
            Write-Progress-Message "Found: $dep" "Success"
        }
    }
    
    if ($toInstall.Count -eq 0) {
        Write-Progress-Message "All dependencies are already installed" "Success"
        return $true
    }
    
    Write-Progress-Message "Installing: $($toInstall -join ', ')" "Running"
    
    try {
        $installArgs = @("install") + $toInstall
        & pip $installArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Progress-Message "Dependencies installed successfully" "Success"
            return $true
        }
        else {
            Write-Progress-Message "Failed to install dependencies" "Error"
            return $false
        }
    }
    catch {
        Write-Progress-Message "Error installing dependencies: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Test-Dependencies {
    Write-Progress-Message "Checking test dependencies..." "Running"
    
    $dependencies = @("pytest", "pytest-cov", "faker")
    $allPresent = $true
    
    foreach ($dep in $dependencies) {
        if (Test-PythonPackage $dep) {
            Write-Progress-Message "$dep is installed" "Success"
        }
        else {
            Write-Progress-Message "$dep is missing" "Error"
            $allPresent = $false
        }
    }
    
    if (-not $allPresent) {
        Write-Progress-Message "Some dependencies are missing. Run with -Install to fix." "Warning"
    }
    
    return $allPresent
}

function Invoke-TestCommand {
    param(
        [string[]]$Command,
        [string]$Description,
        [int]$TimeoutSeconds = 300
    )
    
    Write-Progress-Message "$Description..." "Running"
    $startTime = Get-Date
    
    try {
        $process = Start-Process -FilePath $Command[0] -ArgumentList $Command[1..($Command.Length-1)] -NoNewWindow -Wait -PassThru
        
        $duration = (Get-Date) - $startTime
        
        if ($process.ExitCode -eq 0) {
            Write-Progress-Message "$Description completed in $($duration.TotalSeconds.ToString('F1'))s" "Success"
            return $true
        }
        else {
            Write-Progress-Message "$Description failed after $($duration.TotalSeconds.ToString('F1'))s (Exit code: $($process.ExitCode))" "Error"
            return $false
        }
    }
    catch {
        Write-Progress-Message "$Description crashed: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Invoke-BackendTests {
    param([bool]$WithCoverage = $false)
    
    $args = @("python", "-m", "pytest", "tests\backend\", "-v", "--tb=short")
    
    if ($WithCoverage) {
        $args += @(
            "--cov=noxcore",
            "--cov=webpanel", 
            "--cov-report=html:test-results\coverage",
            "--cov-report=term-missing"
        )
    }
    
    return Invoke-TestCommand -Command $args -Description "Backend API Tests"
}

function Invoke-FrontendTests {
    $frontendDir = "tests\frontend"
    
    if (-not (Test-Path $frontendDir)) {
        Write-Progress-Message "Frontend test directory not found, skipping..." "Warning"
        return $true
    }
    
    # Check if npm is available
    try {
        & npm --version > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "npm not found"
        }
    }
    catch {
        Write-Progress-Message "npm not found, skipping frontend tests..." "Warning"
        return $true
    }
    
    # Install dependencies if needed
    $nodeModules = Join-Path $frontendDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Progress-Message "Installing frontend dependencies..." "Running"
        Push-Location $frontendDir
        try {
            $success = Invoke-TestCommand -Command @("npm", "install") -Description "Frontend Dependencies Install"
            if (-not $success) {
                return $false
            }
        }
        finally {
            Pop-Location
        }
    }
    
    # Run tests
    Push-Location $frontendDir
    try {
        return Invoke-TestCommand -Command @("npm", "test", "--", "--ci", "--watchAll=false", "--coverage") -Description "Frontend Component Tests"
    }
    finally {
        Pop-Location
    }
}

function Invoke-QuickTests {
    Write-Progress-Message "Running quick smoke tests..." "Running"
    
    $args = @(
        "python", "-m", "pytest",
        "tests\backend\",
        "-m", "smoke",  # Pytest marker for quick tests
        "-v",
        "--tb=short"
    )
    
    $success = Invoke-TestCommand -Command $args -Description "Quick Smoke Tests"
    
    if ($success) {
        Write-Progress-Message "All quick tests passed!" "Success"
    }
    
    return $success
}

function Invoke-AllTests {
    param([bool]$WithCoverage = $false)
    
    Write-Progress-Message "Running complete NoxPanel test suite..." "Running"
    $startTime = Get-Date
    
    $results = @()
    
    # Backend tests
    $results += Invoke-BackendTests -WithCoverage $WithCoverage
    
    # Frontend tests (if available)
    $results += Invoke-FrontendTests
    
    # Summary
    $totalDuration = (Get-Date) - $startTime
    $passedCount = ($results | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host ""
    Write-Progress-Message "Test Suite Summary:" "Info"
    Write-Host "   ✅ Passed: $passedCount/$totalCount"
    Write-Host "   ⏱️  Duration: $($totalDuration.TotalSeconds.ToString('F1'))s"
    
    $allPassed = $results | ForEach-Object { $_ } | Measure-Object -Sum | Select-Object -ExpandProperty Sum
    
    if ($allPassed -eq $totalCount) {
        Write-Progress-Message "All tests passed!" "Success"
        return $true
    }
    else {
        Write-Progress-Message "Some tests failed!" "Error"
        return $false
    }
}

# Main script logic
if ($Help) {
    Show-Help
    exit 0
}

# Change to project root directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $scriptDir) -eq "tests") {
    $projectRoot = Split-Path -Parent $scriptDir
}
else {
    $projectRoot = $scriptDir
}

Set-Location $projectRoot

# Handle install dependencies
if ($Install) {
    $success = Install-Dependencies
    exit $(if ($success) { 0 } else { 1 })
}

# Handle check dependencies
if ($CheckDeps) {
    $success = Test-Dependencies
    exit $(if ($success) { 0 } else { 1 })
}

# Run tests based on parameters
$success = $false

if ($Quick) {
    $success = Invoke-QuickTests
}
elseif ($Backend) {
    $success = Invoke-BackendTests -WithCoverage $Coverage
}
elseif ($Frontend) {
    $success = Invoke-FrontendTests
}
else {
    # Run all tests
    $success = Invoke-AllTests -WithCoverage $Coverage
}

# Exit with appropriate code
exit $(if ($success) { 0 } else { 1 })
