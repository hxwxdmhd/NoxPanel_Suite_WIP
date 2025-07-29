#Requires -Version 5.0

<#
.SYNOPSIS
    Project Cleanup and Migration Script
    Implements the cleanup strategy from the analysis report

.DESCRIPTION
    This script performs:
    - KEEP: Preserves active and essential files
    - MIGRATE/REFACTOR: Handles legacy feature migration
    - DELETE: Removes outdated, duplicated, superseded files
    - Includes dry-run capability and rollback functionality

.PARAMETER DryRun
    Performs a dry run without making actual changes

.PARAMETER BackupPath
    Path to create backups before deletion

.PARAMETER LogPath
    Path for operation log file

.EXAMPLE
    .\project_cleanup_migration_final.ps1 -DryRun
    .\project_cleanup_migration_final.ps1 -BackupPath "C:\Backup\ProjectCleanup"
#>

param(
    [switch]$DryRun = $false,
    [string]$BackupPath,
    [string]$LogPath
)

# Set default paths if not provided
if (-not $BackupPath) {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $BackupPath = "./backup_$timestamp"
}

if (-not $LogPath) {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $LogPath = "./cleanup_log_$timestamp.txt"
}

# Check and set execution policy if needed
$currentPolicy = Get-ExecutionPolicy -Scope Process
if ($currentPolicy -eq 'Restricted' -or $currentPolicy -eq 'AllSigned') {
    Write-Host "Setting execution policy for this session..."
    try {
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
        Write-Host "✅ Execution policy set to Bypass for this session"
    }
    catch {
        Write-Host "❌ Failed to set execution policy. Please run PowerShell as Administrator" -ForegroundColor Red
        exit 1
    }
}

# Initialize logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage -ErrorAction SilentlyContinue
}

# Create backup directory if not in dry run mode
if (-not $DryRun) {
    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
        Write-Log "Created backup directory: $BackupPath"
    }
}

Write-Log "Starting Project Cleanup and Migration Script"
Write-Log "Current User: $env:USERNAME"
Write-Log "Current Directory: $(Get-Location)"
Write-Log "Mode: $(if($DryRun){'DRY RUN'}else{'LIVE EXECUTION'})"

# ===== KEEP (Active & Essential) =====
Write-Log "=== KEEP PHASE: Validating essential files ===" "INFO"

$keepPaths = @(
    "AetherCore",
    "NoxGuard/",
    "NoxPanel", 
    "fritzwatcher_plugin",
    "api/",
    "web/",
    "frontend",
    "multi_tenant",
    "voice",
    "webrtc",
    "v52_enhancement",
    "docker-compose.yml",
    ".env",
    "main.py",
    "performance_enhanced_web_server.py",
    "plugin_framework_core.py",
    "plugin_framework_v2.py",
    "plugin_architecture.py",
    "agents",
    "app_v5.py"
)

$missingEssential = @()
foreach ($path in $keepPaths) {
    if (-not (Test-Path $path)) {
        $missingEssential += $path
        Write-Log "WARNING: Essential path missing: $path" "WARN"
    }
    else {
        Write-Log "✅ Essential path validated: $path"
    }
}

if ($missingEssential.Count -gt 0) {
    Write-Log "Found $($missingEssential.Count) missing essential paths. Please verify project structure." "WARN"
}

# ===== MIGRATE/REFACTOR PHASE =====
Write-Log "=== MIGRATE/REFACTOR PHASE: Processing legacy features ===" "INFO"

$migrationTasks = @{
    "legacy_fritz_api.py" = @{
        "target" = "fritzwatcher_plugin.py"
        "action" = "Compare and migrate unique FRITZ!Box logic"
    }
    "test_server.py" = @{
        "target" = "main.py"
        "action" = "Merge test/dev logic into main application"
    }
    "ultra_secure_server.py" = @{
        "target" = "app_v5.py"
        "action" = "Merge security features if missing"
    }
    "api_bridge.py" = @{
        "target" = "api/"
        "action" = "Integrate unique API routes into unified backend"
    }
    "scripts/implementation_status_analyzer.py" = @{
        "target" = "main pipeline"
        "action" = "Merge analysis logic if not present"
    }
}

foreach ($file in $migrationTasks.Keys) {
    if (Test-Path $file) {
        Write-Log "📋 MIGRATION NEEDED: $file -> $($migrationTasks[$file].target)"
        Write-Log "   Action: $($migrationTasks[$file].action)"
        
        # Create migration backup
        if (-not $DryRun) {
            $migrationBackup = Join-Path $BackupPath "migration"
            if (-not (Test-Path $migrationBackup)) {
                New-Item -ItemType Directory -Path $migrationBackup -Force | Out-Null
            }
            Copy-Item $file $migrationBackup -Recurse -Force
            Write-Log "   Backed up to: $migrationBackup"
        }
    }
    else {
        Write-Log "   File not found for migration: $file" "INFO"
    }
}

# Check for legacy JS modules that need migration to JSX/TS
try {
    $legacyJsFiles = Get-ChildItem -Path "." -Filter "*.js" -Recurse -ErrorAction SilentlyContinue | Where-Object {
        $_.FullName -notmatch "node_modules" -and 
        $_.FullName -notmatch "dist" -and
        $_.FullName -notmatch "build"
    }

    if ($legacyJsFiles) {
        Write-Log "📋 Legacy JS files found for potential migration to JSX/TS:"
        foreach ($jsFile in $legacyJsFiles) {
            Write-Log "   $($jsFile.FullName)"
        }
    }
}
catch {
    Write-Log "Error scanning for legacy JS files: $($_.Exception.Message)" "ERROR"
}

# ===== DELETE PHASE =====
Write-Log "=== DELETE PHASE: Removing outdated/superseded files ===" "INFO"

$deleteTargets = @(
    "__pycache__",
    ".pytest_cache", 
    "*.rlvr_backup",
    "scripts/port_mapper.py",
    "scripts/frontend_backend_integrator.py",
    "validate_optimization.py",
    "app.py",
    "ultimate_suite_enhanced_v10.py",
    "rlvr_phase3_advanced_enhancer_fixed.py"
)

$deletedItems = @()
$skippedItems = @()

foreach ($target in $deleteTargets) {
    try {
        $items = @()
        
        # Handle wildcards vs specific paths
        if ($target -contains "*") {
            $items = Get-ChildItem -Path "." -Filter $target -Recurse -ErrorAction SilentlyContinue
        }
        else {
            $items = Get-ChildItem -Path "." -Recurse -ErrorAction SilentlyContinue | Where-Object {
                $_.Name -eq $target -or $_.FullName -like "*\$target" -or $_.FullName -like "*/$target"
            }
        }
        
        foreach ($item in $items) {
            $fullPath = $item.FullName
            
            # Safety check - don't delete if in KEEP list
            $isProtected = $false
            foreach ($keepPath in $keepPaths) {
                if ($fullPath -like "*$keepPath*") {
                    $isProtected = $true
                    break
                }
            }
            
            if ($isProtected) {
                Write-Log "🛡️  PROTECTED: Skipping $fullPath (in KEEP list)" "WARN"
                $skippedItems += $fullPath
                continue
            }
            
            Write-Log "🗑️  MARKED FOR DELETION: $fullPath"
            
            if (-not $DryRun) {
                try {
                    # Create backup before deletion
                    $relativePath = $item.Name
                    $backupTarget = Join-Path $BackupPath $relativePath
                    
                    if ($item.PSIsContainer) {
                        Copy-Item $item.FullName $backupTarget -Recurse -Force -ErrorAction SilentlyContinue
                        Remove-Item $item.FullName -Recurse -Force
                    }
                    else {
                        Copy-Item $item.FullName $backupTarget -Force -ErrorAction SilentlyContinue
                        Remove-Item $item.FullName -Force
                    }
                    $deletedItems += $fullPath
                    Write-Log "   ✅ Deleted and backed up: $fullPath"
                }
                catch {
                    Write-Log "   ❌ Failed to delete: $fullPath - Error: $($_.Exception.Message)" "ERROR"
                }
            }
            else {
                Write-Log "   [DRY RUN] Would delete: $fullPath"
            }
        }
    }
    catch {
        Write-Log "Error processing target '$target': $($_.Exception.Message)" "ERROR"
    }
}

# ===== CLEANUP DIAGNOSTIC FILES =====
Write-Log "=== DIAGNOSTIC FILES CLEANUP ===" "INFO"

try {
    $diagnosticFiles = Get-ChildItem -Path "." -Filter "*.json" -Recurse -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match "(diagnostic|debug|temp|log)" -and
        $_.FullName -notmatch "node_modules" -and
        $_.FullName -notmatch "essential" -and
        $_.FullName -notmatch "config"
    }

    foreach ($diagFile in $diagnosticFiles) {
        Write-Log "📊 Diagnostic file found: $($diagFile.FullName)"
        if (-not $DryRun) {
            try {
                Copy-Item $diagFile.FullName (Join-Path $BackupPath $diagFile.Name) -Force
                Remove-Item $diagFile.FullName -Force
                Write-Log "   ✅ Auto-deleted diagnostic file: $($diagFile.Name)"
            }
            catch {
                Write-Log "   ❌ Failed to delete diagnostic file: $($diagFile.Name)" "ERROR"
            }
        }
    }
}
catch {
    Write-Log "Error processing diagnostic files: $($_.Exception.Message)" "ERROR"
}

# ===== GENERATE TODO CHECKLIST =====
Write-Log "=== GENERATING TODO CHECKLIST ===" "INFO"

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$todoPath = "cleanup_todo_$timestamp.md"

# Build TODO content line by line to avoid parsing issues
$todoLines = @()
$todoLines += "# Project Cleanup TODO Checklist"
$todoLines += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$todoLines += ""
$todoLines += "## Migration Tasks"
$todoLines += "- [ ] Compare legacy_fritz_api.py logic and migrate to fritzwatcher_plugin.py"
$todoLines += "- [ ] Merge test_server.py dev/test logic into current test suite"
$todoLines += "- [ ] Integrate api_bridge.py routes into unified backend"
$todoLines += "- [ ] Migrate legacy .js features to .jsx/.ts"
$todoLines += "- [ ] Consolidate implementation_status_analyzer.py logic"
$todoLines += "- [ ] Archive superseded docs to /archive/deprecated/"
$todoLines += "- [ ] Validate all deletions with dry-run capability"
$todoLines += "- [ ] Update documentation references after cleanup"
$todoLines += ""
$todoLines += "## Agent Coordination Tasks"
$todoLines += "- [ ] Configure Supaermaven for code analysis orchestration"
$todoLines += "- [ ] Set up Langflow for dependency visualization"
$todoLines += "- [ ] Implement shared context pool in agents/"
$todoLines += "- [ ] Enable public changelog logging"
$todoLines += "- [ ] Validate migration completeness"
$todoLines += ""
$todoLines += "## Cleanup Summary"
$todoLines += "- Files deleted: $($deletedItems.Count)"
$todoLines += "- Files skipped (protected): $($skippedItems.Count)"
$todoLines += "- Migration tasks identified: $($migrationTasks.Count)"
$legacyJsCount = if($legacyJsFiles){$legacyJsFiles.Count}else{0}
$todoLines += "- Legacy JS files found: $legacyJsCount"

if (-not $DryRun) {
    $todoLines | Out-File -FilePath $todoPath -Encoding UTF8
    Write-Log "📝 TODO checklist generated: $todoPath"
}
else {
    Write-Log "📝 TODO checklist would be generated: $todoPath"
}

# ===== ROLLBACK SCRIPT GENERATION =====
Write-Log "=== GENERATING ROLLBACK SCRIPT ===" "INFO"

$rollbackPath = "rollback_$timestamp.ps1"

# Build rollback script line by line
$rollbackLines = @()
$rollbackLines += "# Rollback Script - Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$rollbackLines += "# Use this script to restore deleted files if needed"
$rollbackLines += ""
$rollbackLines += "`$BackupPath = `"$BackupPath`""
$rollbackLines += "`$OriginalLocation = `"$(Get-Location)`""
$rollbackLines += ""
$rollbackLines += "if (Test-Path `$BackupPath) {"
$rollbackLines += "    Write-Host `"Restoring files from backup...`""
$rollbackLines += "    Copy-Item `"`$BackupPath\*`" `$OriginalLocation -Recurse -Force"
$rollbackLines += "    Write-Host `"Rollback completed. Files restored from: `$BackupPath`""
$rollbackLines += "} else {"
$rollbackLines += "    Write-Host `"Backup path not found: `$BackupPath`""
$rollbackLines += "}"

if (-not $DryRun) {
    $rollbackLines | Out-File -FilePath $rollbackPath -Encoding UTF8
    Write-Log "🔄 Rollback script generated: $rollbackPath"
}
else {
    Write-Log "🔄 Rollback script would be generated: $rollbackPath"
}

# ===== SUMMARY =====
Write-Log "=== CLEANUP SUMMARY ===" "INFO"
Write-Log "Operation completed successfully!"
Write-Log "Mode: $(if($DryRun){'DRY RUN - No files were actually modified'}else{'LIVE EXECUTION'})"
Write-Log "Files deleted: $($deletedItems.Count)"
Write-Log "Files protected/skipped: $($skippedItems.Count)"
Write-Log "Migration tasks identified: $($migrationTasks.Keys.Count)"
Write-Log "Missing essential paths: $($missingEssential.Count)"

if (-not $DryRun) {
    Write-Log "Backup location: $BackupPath"
    Write-Log "Log file: $LogPath"
    Write-Log "TODO checklist: $todoPath"
    Write-Log "Rollback script: $rollbackPath"
}
else {
    Write-Log "This was a DRY RUN - no actual changes were made"
    Write-Log "Run without -DryRun parameter to execute cleanup"
}

Write-Log "Script execution completed."

# Return summary object
$summary = @{
    DeletedItems = $deletedItems
    SkippedItems = $skippedItems
    MigrationTasks = $migrationTasks
    MissingEssential = $missingEssential
    BackupPath = $BackupPath
    LogPath = $LogPath
    DryRun = $DryRun
}

return $summary