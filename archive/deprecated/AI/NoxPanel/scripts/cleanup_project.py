#!/usr/bin/env python3
"""
NoxPanel Project Cleanup & Organization Script
============================================

Safely organizes unnecessary files into logical archive directories
without disrupting the core system functionality.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class ProjectCleaner:
    """Organizes project files into logical structure"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.archive_dir = self.project_root / "archive"
        self.log_messages = []
        
        # Create archive structure
        self.archive_dirs = {
            "backups": self.archive_dir / "backups",
            "logs": self.archive_dir / "logs", 
            "test_results": self.archive_dir / "test_results",
            "deprecated": self.archive_dir / "deprecated",
            "reports": self.archive_dir / "reports"
        }
        
        for dir_path in self.archive_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str):
        """Log cleanup actions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        self.log_messages.append(log_msg)
    
    def move_file_safely(self, source: Path, destination: Path) -> bool:
        """Safely move a file with collision handling"""
        try:
            if destination.exists():
                # Add timestamp to avoid collision
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_parts = destination.name.split('.')
                if len(name_parts) > 1:
                    new_name = f"{'.'.join(name_parts[:-1])}_{timestamp}.{name_parts[-1]}"
                else:
                    new_name = f"{destination.name}_{timestamp}"
                destination = destination.parent / new_name
            
            shutil.move(str(source), str(destination))
            self.log(f"✅ Moved: {source.name} → {destination.relative_to(self.project_root)}")
            return True
            
        except Exception as e:
            self.log(f"❌ Error moving {source.name}: {e}")
            return False
    
    def organize_backup_files(self):
        """Move backup files to archive/backups"""
        self.log("🗂️  Organizing backup files...")
        
        backup_patterns = ["*backup*", "*_backup*"]
        backup_count = 0
        
        for pattern in backup_patterns:
            for backup_file in self.project_root.rglob(pattern):
                # Skip files already in archive directory
                if "archive" in str(backup_file):
                    continue
                    
                if backup_file.is_file():
                    destination = self.archive_dirs["backups"] / backup_file.name
                    if self.move_file_safely(backup_file, destination):
                        backup_count += 1
        
        self.log(f"📁 Organized {backup_count} backup files")
    
    def organize_log_files(self):
        """Move log files to archive/logs"""
        self.log("📋 Organizing log files...")
        
        log_count = 0
        for log_file in self.project_root.rglob("*.log"):
            # Skip logs in data/logs (current logs) and archive
            if "data/logs" in str(log_file) or "archive" in str(log_file):
                continue
                
            destination = self.archive_dirs["logs"] / log_file.name
            if self.move_file_safely(log_file, destination):
                log_count += 1
        
        self.log(f"📋 Organized {log_count} log files")
    
    def organize_test_results(self):
        """Move test result files to archive/test_results"""
        self.log("🧪 Organizing test result files...")
        
        test_patterns = ["*test_results*", "*results*.json", "*_results.json"]
        test_count = 0
        
        for pattern in test_patterns:
            for test_file in self.project_root.rglob(pattern):
                # Skip files in archive and docs (audit results)
                if "archive" in str(test_file) or "docs" in str(test_file):
                    continue
                    
                if test_file.is_file():
                    destination = self.archive_dirs["test_results"] / test_file.name
                    if self.move_file_safely(test_file, destination):
                        test_count += 1
        
        self.log(f"🧪 Organized {test_count} test result files")
    
    def organize_reports(self):
        """Move report files to archive/reports"""
        self.log("📊 Organizing report files...")
        
        report_patterns = ["*REPORT*", "*AUDIT*", "*SUMMARY*", "*COMPLETION*"]
        report_count = 0
        
        for pattern in report_patterns:
            for report_file in self.project_root.rglob(pattern):
                # Skip files in archive, docs, and essential reports
                if ("archive" in str(report_file) or 
                    "docs" in str(report_file) or
                    report_file.name in ["README.md", "CHANGELOG.md"]):
                    continue
                    
                if report_file.is_file() and report_file.suffix == ".md":
                    destination = self.archive_dirs["reports"] / report_file.name
                    if self.move_file_safely(report_file, destination):
                        report_count += 1
        
        self.log(f"📊 Organized {report_count} report files")
    
    def organize_deprecated_files(self):
        """Move deprecated/disabled files to archive/deprecated"""
        self.log("🗑️  Organizing deprecated files...")
        
        deprecated_patterns = ["*.disabled", "*_old*", "*_legacy*"]
        deprecated_count = 0
        
        for pattern in deprecated_patterns:
            for dep_file in self.project_root.rglob(pattern):
                if "archive" in str(dep_file):
                    continue
                    
                if dep_file.is_file():
                    destination = self.archive_dirs["deprecated"] / dep_file.name
                    if self.move_file_safely(dep_file, destination):
                        deprecated_count += 1
        
        self.log(f"🗑️  Organized {deprecated_count} deprecated files")
    
    def clean_empty_directories(self):
        """Remove empty directories (except essential ones)"""
        self.log("🧹 Cleaning empty directories...")
        
        essential_dirs = {
            "data", "logs", "docs", "scripts", "webpanel", "noxcore", 
            "templates", "static", "plugins", "tests", "config"
        }
        
        removed_count = 0
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                
                # Skip essential directories and archive
                if (dir_name in essential_dirs or 
                    "archive" in str(dir_path) or
                    "venv" in str(dir_path) or
                    ".git" in str(dir_path)):
                    continue
                
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        self.log(f"🗂️  Removed empty directory: {dir_path.relative_to(self.project_root)}")
                        removed_count += 1
                except (OSError, StopIteration):
                    # Directory not empty or permission issue
                    pass
        
        self.log(f"🧹 Removed {removed_count} empty directories")
    
    def generate_cleanup_report(self):
        """Generate cleanup report"""
        report = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "actions_performed": self.log_messages,
            "archive_structure": {
                name: str(path.relative_to(self.project_root))
                for name, path in self.archive_dirs.items()
            }
        }
        
        report_file = self.archive_dir / "cleanup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📄 Cleanup report saved: {report_file.relative_to(self.project_root)}")
    
    def run_full_cleanup(self):
        """Run complete project cleanup"""
        self.log("=" * 60)
        self.log("🧹 NOXPANEL PROJECT CLEANUP & ORGANIZATION")
        self.log("=" * 60)
        
        # Run cleanup phases
        self.organize_backup_files()
        self.organize_log_files()
        self.organize_test_results()
        self.organize_reports()
        self.organize_deprecated_files()
        self.clean_empty_directories()
        
        # Generate report
        self.generate_cleanup_report()
        
        self.log("=" * 60)
        self.log("✅ PROJECT CLEANUP COMPLETED SUCCESSFULLY")
        self.log("=" * 60)
        
        # Summary
        self.log(f"📁 Archive directory: {self.archive_dir.relative_to(self.project_root)}")
        self.log("🔍 Check cleanup_report.json for detailed actions")

def main():
    """Main cleanup execution"""
    cleaner = ProjectCleaner()
    cleaner.run_full_cleanup()

if __name__ == "__main__":
    main()
