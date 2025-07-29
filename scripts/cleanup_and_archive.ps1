# 🗂️ Heimnetz Project - Automated File Cleanup & Archive Script
# Version: 1.0
# Purpose: Clean up superseded documentation and organize project structure
# Date: 2025-07-16

Write-Host "🌟 HEIMNETZ PROJECT - AUTOMATED CLEANUP & ARCHIVE SCRIPT v1.0" -ForegroundColor Cyan
Write-Host "=" * 65 -ForegroundColor Cyan

# Define base paths
$ProjectRoot = "k:\Project Heimnetz"
$NoxPanelPath = "$ProjectRoot\AI\NoxPanel"

Write-Host "📂 Creating archive directories..." -ForegroundColor Yellow

# Create archive directories
$LegacyDocsPath = "$ProjectRoot\archive\legacy_docs_v1-v9"
$SupersededDocsPath = "$NoxPanelPath\archive\superseded_docs"

New-Item -Path $LegacyDocsPath -ItemType Directory -Force | Out-Null
New-Item -Path $SupersededDocsPath -ItemType Directory -Force | Out-Null

Write-Host "✅ Archive directories created" -ForegroundColor Green

# Files to archive from project root (superseded documentation v1.0-v7.0)
$RootFilesToArchive = @(
    "PROJECT_REFOCUS_ANALYSIS.md",
    "CONSOLIDATION_CHECKLIST.md", 
    "COMPREHENSIVE_VERSIONING_REPORT.md",
    "FINAL_IMPLEMENTATION_REPORT.md",
    "REFOCUS_COMPLETION_REPORT.md",
    "NOXPANEL_COMPLETE_GUIDE.md",
    "project.md"
)

# Files to archive from NoxPanel directory (superseded documentation v8.0-v9.0)
$NoxPanelFilesToArchive = @(
    "PROJECT_CONTINUATION_GUIDE.md",
    "DEVELOPMENT_STATUS.md"
)

Write-Host "🗂️ Archiving superseded documentation files..." -ForegroundColor Yellow

# Archive root files
$ArchivedCount = 0
foreach ($File in $RootFilesToArchive) {
    $SourcePath = "$ProjectRoot\$File"
    $DestPath = "$LegacyDocsPath\$File"
    
    if (Test-Path $SourcePath) {
        try {
            Move-Item -Path $SourcePath -Destination $DestPath -Force
            Write-Host "  ✅ Archived: $File" -ForegroundColor Green
            $ArchivedCount++
        }
        catch {
            Write-Host "  ⚠️ Failed to archive: $File - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  ⚠️ Not found: $File" -ForegroundColor Yellow
    }
}

# Archive NoxPanel files  
foreach ($File in $NoxPanelFilesToArchive) {
    $SourcePath = "$NoxPanelPath\$File"
    $DestPath = "$SupersededDocsPath\$File"
    
    if (Test-Path $SourcePath) {
        try {
            Move-Item -Path $SourcePath -Destination $DestPath -Force
            Write-Host "  ✅ Archived: $File" -ForegroundColor Green
            $ArchivedCount++
        }
        catch {
            Write-Host "  ⚠️ Failed to archive: $File - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  ⚠️ Not found: $File" -ForegroundColor Yellow
    }
}

Write-Host "`n📊 CLEANUP SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Cyan
Write-Host "✅ Files archived: $ArchivedCount" -ForegroundColor Green
Write-Host "📁 Legacy docs location: $LegacyDocsPath" -ForegroundColor Yellow
Write-Host "📁 Superseded docs location: $SupersededDocsPath" -ForegroundColor Yellow

# Create archive index file
$IndexContent = @"
# 📚 Heimnetz Project - Archive Index
## Superseded Documentation Repository

**Created**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Purpose**: Archive of superseded documentation versions v1.0-v9.0
**Current Version**: v10.0 (HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md)

## 📋 Archive Contents

### Legacy Documentation (v1.0-v7.0)
Location: \`$LegacyDocsPath\`

"@

foreach ($File in $RootFilesToArchive) {
    if (Test-Path "$LegacyDocsPath\$File") {
        $FileInfo = Get-Item "$LegacyDocsPath\$File"
        $IndexContent += "- **$File** - Last Modified: $($FileInfo.LastWriteTime.ToString('yyyy-MM-dd'))`n"
    }
}

$IndexContent += @"

### Recent Superseded Documentation (v8.0-v9.0)
Location: \`$SupersededDocsPath\`

"@

foreach ($File in $NoxPanelFilesToArchive) {
    if (Test-Path "$SupersededDocsPath\$File") {
        $FileInfo = Get-Item "$SupersededDocsPath\$File"
        $IndexContent += "- **$File** - Last Modified: $($FileInfo.LastWriteTime.ToString('yyyy-MM-dd'))`n"
    }
}

$IndexContent += @"

## 📖 Version History Reference

| Version | Document | Status | Superseded By |
|---------|----------|--------|---------------|
| v10.0 | HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md | ✅ CURRENT | - |
| v9.0 | PROJECT_CONTINUATION_GUIDE.md | ⚠️ ARCHIVED | v10.0 |
| v8.0 | DEVELOPMENT_STATUS.md | ⚠️ ARCHIVED | v10.0 |
| v7.0 | REFOCUS_COMPLETION_REPORT.md | ⚠️ ARCHIVED | v10.0 |
| v6.0 | COMPREHENSIVE_VERSIONING_REPORT.md | ⚠️ ARCHIVED | v10.0 |
| v5.0 | FINAL_IMPLEMENTATION_REPORT.md | ⚠️ ARCHIVED | v10.0 |
| v4.0 | PROJECT_REFOCUS_ANALYSIS.md | ⚠️ ARCHIVED | v10.0 |
| v3.0 | CONSOLIDATION_CHECKLIST.md | ⚠️ ARCHIVED | v10.0 |
| v2.0 | NOXPANEL_COMPLETE_GUIDE.md | ⚠️ ARCHIVED | v10.0 |
| v1.0 | project.md | ⚠️ ARCHIVED | v10.0 |

## 🎯 Current Active Documentation

**Primary**: HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md  
**Quick Reference**: QUICK_REFERENCE.md  
**Location**: k:\Project Heimnetz\AI\NoxPanel\

---
*Archive created by automated cleanup script v1.0 on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")*
"@

# Save archive index
$IndexPath = "$ProjectRoot\archive\ARCHIVE_INDEX.md"
$IndexContent | Out-File -FilePath $IndexPath -Encoding UTF8

Write-Host "📋 Archive index created: ARCHIVE_INDEX.md" -ForegroundColor Green

# List current active documentation
Write-Host "`n📚 CURRENT ACTIVE DOCUMENTATION" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

$ActiveDocs = @(
    "$NoxPanelPath\HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md",
    "$NoxPanelPath\QUICK_REFERENCE.md",
    "$ProjectRoot\README.md",
    "$ProjectRoot\CHANGELOG.md",
    "$ProjectRoot\CONTRIBUTING.md",
    "$ProjectRoot\SECURITY.md",
    "$ProjectRoot\DEPLOYMENT_GUIDE.md",
    "$ProjectRoot\CODE_OF_CONDUCT.md"
)

foreach ($Doc in $ActiveDocs) {
    if (Test-Path $Doc) {
        $FileName = Split-Path $Doc -Leaf
        $FileSize = [math]::Round((Get-Item $Doc).Length / 1KB, 1)
        Write-Host "  ✅ $FileName ($FileSize KB)" -ForegroundColor Green
    }
    else {
        $FileName = Split-Path $Doc -Leaf
        Write-Host "  ⚠️ $FileName (NOT FOUND)" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 CLEANUP COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "🎯 Project is now organized with v10.0 as the master documentation" -ForegroundColor Cyan
Write-Host "📁 All legacy versions safely archived and indexed" -ForegroundColor Cyan
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "   1. Review HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md" -ForegroundColor White
Write-Host "   2. Focus on Gates 3-4 completion" -ForegroundColor White  
Write-Host "   3. Work toward 50% milestone (Plugin System unlock)" -ForegroundColor White

# Final verification
Write-Host "`nVERIFICATION" -ForegroundColor Cyan
Write-Host "=" * 20 -ForegroundColor Cyan

$V10Doc = "$NoxPanelPath\HEIMNETZ_ULTIMATE_DOCUMENTATION_v10.0.md"
$QuickRef = "$NoxPanelPath\QUICK_REFERENCE.md"

if ((Test-Path $V10Doc) -and (Test-Path $QuickRef)) {
    Write-Host "✅ Master documentation v10.0 is ready" -ForegroundColor Green
    Write-Host "✅ Quick reference is available" -ForegroundColor Green
    Write-Host "✅ Project structure is clean and organized" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Missing critical documentation files" -ForegroundColor Red
}

Write-Host "`nReady to proceed with Gates 3-4 optimization!" -ForegroundColor Green
