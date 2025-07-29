#!/usr/bin/env python3
"""
Legacy File Re-entry Prevention System
Monitors project for re-introduction of legacy patterns and files

This watchdog system prevents legacy files from being accidentally
reintroduced after the comprehensive cleanup.

Usage:
    python scripts/watch_legacy_reentry.py
    python scripts/watch_legacy_reentry.py --scan
    python scripts/watch_legacy_reentry.py --monitor
"""

import os
import sys
import time
import fnmatch
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple

# Legacy patterns to monitor for
LEGACY_PATTERNS = {
    'rlvr_backup': '*.rlvr_backup',
    'versioned_files': '*_v[0-9]*.py',
    'old_configs': '*.old',
    'backup_files': '*.bak',
    'temp_files': '*~',
    'deprecated_modules': [
        'app.py',  # Replaced by app_v5.py
        'main.py.old',
        'ultra_secure_server.py.backup',
        'api_bridge.py.deprecated'
    ]
}

# Directories to monitor
MONITOR_PATHS = [
    "K:\\Project Heimnetz\\AI\\NoxPanel",
    "K:\\Project Heimnetz\\scripts",
    "K:\\Project Heimnetz\\docs", 
    "K:\\Project Heimnetz\\powershell"
]

# Ignore patterns (legitimate files)
IGNORE_PATTERNS = [
    "*node_modules*",
    "*venv*",
    "*__pycache__*",
    "*.git*",
    "*archive*"
]

class LegacyWatchdog:
    def __init__(self):
        self.baseline_created = False
        self.baseline_file = "K:\\Project Heimnetz\\scripts\\legacy_baseline.json"
        self.alert_log = "K:\\Project Heimnetz\\logs\\legacy_alerts.log"
        self.current_files = {}
        
    def should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored based on ignore patterns"""
        for pattern in IGNORE_PATTERNS:
            if fnmatch.fnmatch(file_path.lower(), pattern.lower()):
                return True
        return False
        
    def is_legacy_pattern(self, file_path: str) -> Tuple[bool, str]:
        """Check if file matches legacy patterns"""
        filename = os.path.basename(file_path)
        
        # Check RLVR backup pattern
        if fnmatch.fnmatch(filename, LEGACY_PATTERNS['rlvr_backup']):
            return True, "RLVR backup file detected"
            
        # Check versioned file pattern
        if fnmatch.fnmatch(filename, LEGACY_PATTERNS['versioned_files']):
            return True, "Versioned legacy file detected"
            
        # Check other patterns
        for pattern_type, pattern in LEGACY_PATTERNS.items():
            if isinstance(pattern, str) and fnmatch.fnmatch(filename, pattern):
                return True, f"{pattern_type} pattern detected"
            elif isinstance(pattern, list) and filename in pattern:
                return True, f"Known deprecated module: {filename}"
                
        return False, ""
        
    def scan_for_legacy_files(self) -> Dict[str, List[str]]:
        """Scan monitored paths for legacy files"""
        print(f"🔍 Scanning for legacy file patterns...")
        
        found_legacy = {}
        total_scanned = 0
        
        for monitor_path in MONITOR_PATHS:
            if not os.path.exists(monitor_path):
                continue
                
            print(f"  📁 Scanning: {monitor_path}")
            
            for root, dirs, files in os.walk(monitor_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_scanned += 1
                    
                    if self.should_ignore(file_path):
                        continue
                        
                    is_legacy, reason = self.is_legacy_pattern(file_path)
                    if is_legacy:
                        category = reason.split()[0].lower()
                        if category not in found_legacy:
                            found_legacy[category] = []
                        found_legacy[category].append(file_path)
                        
        print(f"  📊 Total files scanned: {total_scanned}")
        
        if found_legacy:
            print(f"  ⚠️  Legacy files found: {sum(len(files) for files in found_legacy.values())}")
            for category, files in found_legacy.items():
                print(f"    {category}: {len(files)} files")
        else:
            print(f"  ✅ No legacy files detected")
            
        return found_legacy
        
    def create_baseline(self) -> bool:
        """Create baseline of current clean state"""
        print(f"📋 Creating legacy prevention baseline...")
        
        try:
            import json
            
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(self.alert_log), exist_ok=True)
            
            baseline_data = {
                "created": datetime.now().isoformat(),
                "scan_results": self.scan_for_legacy_files(),
                "monitored_paths": MONITOR_PATHS,
                "legacy_patterns": LEGACY_PATTERNS
            }
            
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
                
            print(f"  ✅ Baseline created: {self.baseline_file}")
            self.baseline_created = True
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating baseline: {e}")
            return False
            
    def load_baseline(self) -> Dict:
        """Load existing baseline"""
        try:
            import json
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"❌ Error loading baseline: {e}")
            return {}
            
    def log_alert(self, alert_type: str, message: str, file_path: str = ""):
        """Log legacy file alert"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_entry = f"[{timestamp}] {alert_type}: {message}"
            if file_path:
                alert_entry += f" | File: {file_path}"
                
            with open(self.alert_log, 'a', encoding='utf-8') as f:
                f.write(alert_entry + "\\n")
                
            print(f"🚨 ALERT LOGGED: {alert_entry}")
            
        except Exception as e:
            print(f"❌ Error logging alert: {e}")
            
    def check_for_new_legacy(self) -> bool:
        """Check for new legacy files since baseline"""
        print(f"🔍 Checking for new legacy files since baseline...")
        
        baseline = self.load_baseline()
        if not baseline:
            print("  ❌ No baseline found. Creating new baseline...")
            return self.create_baseline()
            
        current_scan = self.scan_for_legacy_files()
        baseline_scan = baseline.get("scan_results", {})
        
        new_legacy_found = False
        
        # Compare current scan with baseline
        for category, files in current_scan.items():
            baseline_files = set(baseline_scan.get(category, []))
            current_files = set(files)
            
            new_files = current_files - baseline_files
            if new_files:
                new_legacy_found = True
                for new_file in new_files:
                    self.log_alert("LEGACY_REINTRODUCED", f"New {category} file detected", new_file)
                    
        if not new_legacy_found:
            print("  ✅ No new legacy files detected since baseline")
            
        return not new_legacy_found
        
    def monitor_continuous(self, interval: int = 300):
        """Continuously monitor for legacy file reintroduction"""
        print(f"🔄 Starting continuous legacy monitoring (checking every {interval} seconds)...")
        print(f"Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.check_for_new_legacy()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\\n🛑 Legacy monitoring stopped by user")
            
    def generate_report(self) -> str:
        """Generate legacy monitoring report"""
        print(f"📊 Generating legacy monitoring report...")
        
        baseline = self.load_baseline()
        current_scan = self.scan_for_legacy_files()
        
        report = f"""
# 🛡️ LEGACY FILE MONITORING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 CURRENT SCAN RESULTS
"""
        
        if current_scan:
            for category, files in current_scan.items():
                report += f"\\n### {category.upper()} FILES ({len(files)} found)\\n"
                for file_path in files[:5]:  # Show first 5 files
                    report += f"- {file_path}\\n"
                if len(files) > 5:
                    report += f"- ... and {len(files) - 5} more files\\n"
        else:
            report += "\\n✅ No legacy files detected - System is clean!\\n"
            
        if baseline:
            baseline_date = baseline.get("created", "Unknown")
            report += f"\\n## 📋 BASELINE INFORMATION\\n"
            report += f"Baseline Created: {baseline_date}\\n"
            report += f"Monitored Paths: {len(MONITOR_PATHS)}\\n"
            
        report += f"\\n## 🎯 MONITORING STATUS\\n"
        report += f"System Status: {'✅ CLEAN' if not current_scan else '⚠️ LEGACY FILES DETECTED'}\\n"
        report += f"Alert Log: {self.alert_log}\\n"
        report += f"Baseline File: {self.baseline_file}\\n"
        
        return report

def main():
    watchdog = LegacyWatchdog()
    
    if len(sys.argv) == 1:
        # Default: scan and report
        print("🛡️ Legacy File Re-entry Prevention System")
        print("=" * 50)
        
        # Check if baseline exists
        if not os.path.exists(watchdog.baseline_file):
            print("📋 No baseline found. Creating initial baseline...")
            watchdog.create_baseline()
        else:
            print("📋 Baseline found. Checking for new legacy files...")
            watchdog.check_for_new_legacy()
            
        # Generate report
        report = watchdog.generate_report()
        print(report)
        
    elif len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--scan":
            watchdog.scan_for_legacy_files()
            
        elif command == "--baseline":
            watchdog.create_baseline()
            
        elif command == "--check":
            clean = watchdog.check_for_new_legacy()
            sys.exit(0 if clean else 1)
            
        elif command == "--monitor":
            interval = 300  # 5 minutes default
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    print("❌ Invalid interval. Using default 300 seconds.")
            watchdog.monitor_continuous(interval)
            
        elif command == "--report":
            report = watchdog.generate_report()
            print(report)
            
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python watch_legacy_reentry.py [--scan|--baseline|--check|--monitor [interval]|--report]")
            sys.exit(1)

if __name__ == "__main__":
    main()
