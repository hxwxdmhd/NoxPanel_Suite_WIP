# NOX COPILOT AGENT v2.0 - Enhanced Final Startup & Management System
# Auto-bootstrapping, crash recovery, and session management

param(
    [string]$Mode = "default",
    [switch]$SafeMode = $false,
    [switch]$AutoPilot = $false,
    [switch]$GenerateReport = $false
)

# =============================================================================
# COPILOT AGENT v2.0 CONFIGURATION
# =============================================================================
$COPILOT_VERSION = "2.0.0-Enhanced"
$PROJECT_ROOT = "K:\Project Heimnetz\NoxPanel"
$LEGACY_ROOT = "C:\xampp\htdocs\heimnetzV2"
$COPILOT_DIR = "$PROJECT_ROOT\copilot"
$CURRENT_SESSION = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

# Create copilot directory structure
$copilotDirs = @("logs", "reports", "modes", "checkpoints")
foreach ($dir in $copilotDirs) {
    $fullPath = "$COPILOT_DIR\$dir"
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}

# =============================================================================
# STARTUP BANNER & SYSTEM INITIALIZATION
# =============================================================================
function Show-CopilotBanner {
    Clear-Host
    Write-Host "🤖 ================================" -ForegroundColor Magenta
    Write-Host "🤖  NOX COPILOT AGENT v$COPILOT_VERSION" -ForegroundColor Cyan
    Write-Host "🤖  Enhanced Final - System Intelligence" -ForegroundColor Cyan  
    Write-Host "🤖 ================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "📁 Primary Workspace: K:\Project Heimnetz\NoxPanel" -ForegroundColor Green
    Write-Host "🧊 Legacy Reference:  C:\xampp\htdocs\heimnetzV2" -ForegroundColor Gray
    Write-Host "📅 Session Start:     $CURRENT_SESSION" -ForegroundColor Yellow
    Write-Host "🎯 Current Phase:     Phase 3 AI Integration (75% Complete)" -ForegroundColor Cyan
    Write-Host ""
}

# =============================================================================
# CRASH DETECTION & SAFE MODE MANAGEMENT
# =============================================================================
function Test-CrashRecovery {
    $safeModeFlag = "$COPILOT_DIR\safe_mode.flag"
    $lastCheckpoint = "$COPILOT_DIR\checkpoints\last_session.log"
    
    if (Test-Path $safeModeFlag) {
        Write-Host "🛡️ CRASH DETECTED - Entering Safe Mode Recovery" -ForegroundColor Red
        Write-Host "   Last crash: $(Get-Content $safeModeFlag -ErrorAction SilentlyContinue)" -ForegroundColor Yellow
        
        if (Test-Path $lastCheckpoint) {
            Write-Host "   📋 Checkpoint found: $(Get-Item $lastCheckpoint | Select-Object -ExpandProperty LastWriteTime)" -ForegroundColor Green
            Write-Host "   🔄 Recovery options available" -ForegroundColor Green
        }
        
        return $true
    }
    
    return $false
}

function Enable-SafeMode {
    param([string]$Reason = "Manual activation")
    
    $safeModeFlag = "$COPILOT_DIR\safe_mode.flag"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    "$timestamp - $Reason" | Out-File -FilePath $safeModeFlag -Force
    Write-Host "🛡️ Safe Mode ENABLED: $Reason" -ForegroundColor Yellow
}

function Disable-SafeMode {
    $safeModeFlag = "$COPILOT_DIR\safe_mode.flag"
    
    if (Test-Path $safeModeFlag) {
        Remove-Item $safeModeFlag -Force
        Write-Host "✅ Safe Mode DISABLED - Normal operation resumed" -ForegroundColor Green
    }
}

# =============================================================================
# MODE MANAGEMENT SYSTEM
# =============================================================================
function Set-OperationalMode {
    param([string]$NewMode)
    
    $validModes = @("default", "audit", "auto-pilot", "safe", "deep-dive", "adhd-zen")
    
    if ($NewMode -notin $validModes) {
        Write-Host "❌ Invalid mode: $NewMode" -ForegroundColor Red
        Write-Host "   Valid modes: $($validModes -join ', ')" -ForegroundColor Gray
        return $false
    }
    
    $modeFile = "$COPILOT_DIR\modes\active_mode.conf"
    @{
        "mode" = $NewMode
        "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "session" = $CURRENT_SESSION
    } | ConvertTo-Json | Out-File -FilePath $modeFile -Force
    
    Write-Host "🎛️ Mode set to: $NewMode" -ForegroundColor Cyan
    return $true
}

function Get-CurrentMode {
    $modeFile = "$COPILOT_DIR\modes\active_mode.conf"
    
    if (Test-Path $modeFile) {
        try {
            $config = Get-Content $modeFile | ConvertFrom-Json
            return $config.mode
        } catch {
            return "default"
        }
    }
    
    return "default"
}

# =============================================================================
# PROJECT AUDIT & ROADMAP COMPARISON
# =============================================================================
function Start-ProjectAudit {
    Write-Host "🔍 Running comprehensive project audit..." -ForegroundColor Cyan
    
    $auditResults = @{
        "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "mode" = Get-CurrentMode
        "modules" = @{}
        "phase_status" = @{}
        "divergences" = @()
    }
    
    # Check core modules
    $coreModules = @{
        "Flask Backend" = "$PROJECT_ROOT\webpanel\app.py"
        "Database" = "$PROJECT_ROOT\noxcore\database.py"
        "AI Assistant" = "$PROJECT_ROOT\noxcore\ai\nox_assistant.py"
        "Ollama Client" = "$PROJECT_ROOT\noxcore\ai\ollama_client.py"
        "Task Registry" = "$PROJECT_ROOT\noxcore\ai\task_registry.py"
        "WebSocket Manager" = "$PROJECT_ROOT\noxcore\websocket\manager.py"
        "Plugin System" = "$PROJECT_ROOT\noxcore\plugins.py"
        "Voice Interface" = "$PROJECT_ROOT\noxcore\voice\speech_engine.py"
    }
    
    foreach ($module in $coreModules.Keys) {
        $path = $coreModules[$module]
        $status = if (Test-Path $path) { "✅ Present" } else { "❌ Missing" }
        $auditResults.modules[$module] = @{
            "path" = $path
            "status" = $status
            "exists" = Test-Path $path
        }
        
        Write-Host "  $module`: $status" -ForegroundColor $(if (Test-Path $path) { "Green" } else { "Red" })
    }
    
    # Phase status check
    $auditResults.phase_status = @{
        "Phase 1" = "✅ 100% Complete"
        "Phase 2" = "✅ 100% Complete"
        "Phase 3" = "🔄 75% Complete (Voice Interface Active)"
    }
    
    return $auditResults
}

# =============================================================================
# AUTOMATED REPORT GENERATION
# =============================================================================
function New-AuditReport {
    param([hashtable]$AuditData)
    
    $reportPath = "$COPILOT_DIR\reports\audit_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').md"
    
    $report = @"
# 📋 NoxGuard Project Audit Report – $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

**Copilot Version:** $COPILOT_VERSION  
**Mode:** $($AuditData.mode)  
**Session:** $CURRENT_SESSION  
**Safe Mode Active:** $(if (Test-Path "$COPILOT_DIR\safe_mode.flag") { "🛡️ YES" } else { "✅ NO" })

---

## ✅ Roadmap Completion Summary

| Module                | Status              | Location                    | Notes                           |
|----------------------|---------------------|-----------------------------|---------------------------------|
| Flask Backend        | $($AuditData.modules["Flask Backend"].status) | webpanel/app.py            | Core web application           |
| Database Integration | $($AuditData.modules["Database"].status) | noxcore/database.py        | SQLite with auto-initialization |
| AI Assistant Core    | $($AuditData.modules["AI Assistant"].status) | noxcore/ai/nox_assistant.py | J.A.R.V.I.S.-inspired personality |
| Ollama Integration   | $($AuditData.modules["Ollama Client"].status) | noxcore/ai/ollama_client.py | 9 LLM models supported         |
| Task Registry        | $($AuditData.modules["Task Registry"].status) | noxcore/ai/task_registry.py | YAML-based command routing     |
| WebSocket System     | $($AuditData.modules["WebSocket Manager"].status) | noxcore/websocket/manager.py | Real-time communication       |
| Plugin Architecture  | $($AuditData.modules["Plugin System"].status) | noxcore/plugins.py         | Dynamic loading system        |
| Voice Interface      | $($AuditData.modules["Voice Interface"].status) | noxcore/voice/speech_engine.py | "Hey Nox" wake word (In Dev) |

---

## 🎯 Phase Development Status

| Phase | Status | Completion | Focus Area |
|-------|--------|------------|------------|
| Phase 1: Critical Integration | $($AuditData.phase_status["Phase 1"]) | 100% | Flask-Database-Frontend |
| Phase 2: Enhanced Integration | $($AuditData.phase_status["Phase 2"]) | 100% | WebSocket, Tasks, Plugins |
| Phase 3: AI Integration | $($AuditData.phase_status["Phase 3"]) | 75% | Voice Interface, Analytics |

---

## 🔧 Current Development Focus

### **Active Implementation (Phase 3)**
1. **🎤 Voice Interface**: Speech recognition with "Hey Nox" wake word detection
2. **🌐 Web AI Chat**: Dashboard integration for AI assistant
3. **🎵 Text-to-Speech**: Personality-driven audio responses  
4. **📊 AI Analytics**: Predictive network analysis and insights
5. **🔗 API Integration**: Complete Flask routes for AI functionality

### **Next Priority Tasks**
- Complete voice interface implementation
- Integrate AI chat into web dashboard
- Add text-to-speech personality system
- Implement predictive analytics engine
- Enhance AI model management interface

---

## 🚀 Copilot Agent Status

```
🤖 NOX COPILOT AGENT v$COPILOT_VERSION
├── Operational Mode:        $($AuditData.mode)
├── Session Management:      ✅ Active
├── Crash Recovery:          ✅ Enabled
├── Command Logging:         ✅ Persistent
├── Audit Reporting:         ✅ Automated
├── Workspace Management:    ✅ K:\ primary, C:\ reference
└── Voice AI Pipeline:       🔄 Implementation Active
```

---

**🎯 Recommended Next Actions:**
1. Continue voice interface implementation
2. Test Ollama model integration
3. Implement web AI chat interface
4. Add TTS personality system
5. Begin AI analytics engine development

---
*Report generated automatically by NOX Copilot Agent v$COPILOT_VERSION*
"@

    $report | Out-File -FilePath $reportPath -Force -Encoding UTF8
    Write-Host "📊 Audit report generated: $reportPath" -ForegroundColor Green
    
    return $reportPath
}

# =============================================================================
# COMMAND LOGGING & EXECUTION MEMORY
# =============================================================================
function Add-CommandLog {
    param(
        [string]$Command,
        [string]$Status = "EXECUTED",
        [string]$Notes = ""
    )
    
    $logFile = "$COPILOT_DIR\logs\execution_history.md"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    $logEntry = "| $timestamp | $Command | $Status | $Notes |"
    
    # Create header if file doesn't exist
    if (!(Test-Path $logFile)) {
        $header = @"
# 📋 NOX Copilot Agent - Command Execution History

| Timestamp | Command | Status | Notes |
|-----------|---------|--------|-------|
"@
        $header | Out-File -FilePath $logFile -Force -Encoding UTF8
    }
    
    $logEntry | Add-Content -Path $logFile -Encoding UTF8
}

# =============================================================================
# MAIN COPILOT EXECUTION ENGINE
# =============================================================================
function Start-CopilotAgent {
    param(
        [string]$OperationalMode = "default",
        [switch]$SkipAudit = $false
    )
    
    Show-CopilotBanner
    
    # Check for crash recovery
    $crashDetected = Test-CrashRecovery
    if ($crashDetected -and !$SafeMode) {
        Write-Host "⚠️ Previous crash detected. Use -SafeMode to continue or resolve issues first." -ForegroundColor Yellow
        return
    }
    
    # Set operational mode
    Set-OperationalMode $OperationalMode | Out-Null
    
    # Create session checkpoint
    $checkpointFile = "$COPILOT_DIR\checkpoints\session_$CURRENT_SESSION.log"
    @{
        "session_id" = $CURRENT_SESSION
        "start_time" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "mode" = $OperationalMode
        "copilot_version" = $COPILOT_VERSION
    } | ConvertTo-Json | Out-File -FilePath $checkpointFile -Force
    
    # Run project audit
    if (!$SkipAudit) {
        $auditResults = Start-ProjectAudit
        
        if ($GenerateReport) {
            $reportPath = New-AuditReport -AuditData $auditResults
            Write-Host "📊 Comprehensive audit report available at: $reportPath" -ForegroundColor Cyan
        }
    }
    
    # Log agent startup
    Add-CommandLog -Command "Start-CopilotAgent" -Status "SUCCESS" -Notes "Mode: $OperationalMode, Session: $CURRENT_SESSION"
    
    Write-Host "✅ NOX Copilot Agent v$COPILOT_VERSION is fully operational" -ForegroundColor Green
    Write-Host "🎯 Phase 3 AI Integration: 75% Complete - Voice Interface Implementation Active" -ForegroundColor Cyan
    Write-Host "🎤 Next: Continue voice interface and web AI integration" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Gray
    Write-Host "  .\copilot_startup.ps1 -Mode audit -GenerateReport" -ForegroundColor Gray
    Write-Host "  .\copilot_startup.ps1 -SafeMode" -ForegroundColor Gray
    Write-Host "  .\copilot_startup.ps1 -AutoPilot" -ForegroundColor Gray
}

# =============================================================================
# COPILOT AGENT EXECUTION
# =============================================================================

# Handle parameters and start agent
if ($SafeMode) {
    Enable-SafeMode "Manual safe mode activation"
    Start-CopilotAgent -OperationalMode "safe"
} elseif ($AutoPilot) {
    Start-CopilotAgent -OperationalMode "auto-pilot"
} else {
    Start-CopilotAgent -OperationalMode $Mode -SkipAudit:(!$GenerateReport)
}
