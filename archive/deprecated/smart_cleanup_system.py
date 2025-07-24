# 🧹 Smart Repository Cleanup and Archiving System

import os
import shutil
import json
from datetime import datetime
import logging
from pathlib import Path
import zipfile

class SmartRepositoryCleanup:
    """Intelligent cleanup system for NoxPanel/NoxGuard/Heimnetz Suite"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.cleanup_log = []
        self.archived_files = []
        self.deleted_files = []
        self.errors = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Archive directory
        self.archive_dir = self.workspace_path / "archive" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_rlvr_backups(self):
        """Analyze RLVR backup files for cleanup decisions"""
        rlvr_files = list(self.workspace_path.glob("**/*.rlvr_backup"))
        
        analysis = {
            "total_files": len(rlvr_files),
            "total_size": sum(f.stat().st_size for f in rlvr_files),
            "categories": {
                "python_scripts": [],
                "templates": [],
                "configs": [],
                "other": []
            }
        }
        
        for file_path in rlvr_files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            file_info = {
                "path": str(file_path),
                "size_mb": round(size_mb, 2),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Categorize files
            if file_path.suffix in ['.py']:
                analysis["categories"]["python_scripts"].append(file_info)
            elif file_path.suffix in ['.html', '.htm']:
                analysis["categories"]["templates"].append(file_info)
            elif file_path.suffix in ['.json', '.conf', '.cfg']:
                analysis["categories"]["configs"].append(file_info)
            else:
                analysis["categories"]["other"].append(file_info)
        
        return analysis
    
    def analyze_diagnostic_files(self):
        """Analyze large diagnostic files for optimization"""
        diagnostic_files = list(self.workspace_path.glob("**/diagnostics*.json")) + \
                          list(self.workspace_path.glob("**/diagnostics*.log"))
        
        large_files = []
        for file_path in diagnostic_files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > 50:  # Files larger than 50MB
                large_files.append({
                    "path": str(file_path),
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return large_files
    
    def archive_rlvr_backups(self, max_age_days: int = 30):
        """Archive RLVR backup files older than specified days"""
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        rlvr_files = list(self.workspace_path.glob("**/*.rlvr_backup"))
        
        archived_count = 0
        archived_size = 0
        
        # Create zip archive for RLVR backups
        archive_zip = self.archive_dir / "rlvr_backups.zip"
        
        with zipfile.ZipFile(archive_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in rlvr_files:
                if file_path.stat().st_mtime < cutoff_time:
                    # Add to zip with relative path
                    rel_path = file_path.relative_to(self.workspace_path)
                    zipf.write(file_path, rel_path)
                    
                    archived_size += file_path.stat().st_size
                    archived_count += 1
                    
                    self.archived_files.append({
                        "original_path": str(file_path),
                        "archive_path": str(archive_zip),
                        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
                    })
        
        # Remove original files after successful archival
        if archived_count > 0:
            for file_path in rlvr_files:
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        self.deleted_files.append(str(file_path))
                    except Exception as e:
                        self.errors.append(f"Failed to delete {file_path}: {e}")
        
        return {
            "archived_count": archived_count,
            "archived_size_mb": round(archived_size / (1024 * 1024), 2),
            "archive_file": str(archive_zip)
        }
    
    def compress_diagnostic_files(self):
        """Compress large diagnostic files"""
        large_diagnostics = self.analyze_diagnostic_files()
        compressed_files = []
        
        for file_info in large_diagnostics:
            file_path = Path(file_info["path"])
            compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
            
            try:
                import gzip
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original if compression successful
                original_size = file_path.stat().st_size
                compressed_size = compressed_path.stat().st_size
                
                file_path.unlink()
                
                compressed_files.append({
                    "original_path": str(file_path),
                    "compressed_path": str(compressed_path),
                    "original_size_mb": round(original_size / (1024 * 1024), 2),
                    "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
                    "compression_ratio": round((1 - compressed_size/original_size) * 100, 1)
                })
                
            except Exception as e:
                self.errors.append(f"Failed to compress {file_path}: {e}")
        
        return compressed_files
    
    def clean_empty_directories(self):
        """Remove empty directories"""
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.workspace_path, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        empty_dirs.append(str(dir_path))
                except OSError:
                    pass  # Directory not empty or permission issue
        
        return empty_dirs
    
    def validate_import_references(self):
        """Check for broken import references"""
        python_files = list(self.workspace_path.glob("**/*.py"))
        broken_imports = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for potential issues (basic check)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'import' in line and ('deprecated' in line.lower() or 'old' in line.lower()):
                        broken_imports.append({
                            "file": str(py_file),
                            "line": i,
                            "content": line.strip()
                        })
            
            except Exception as e:
                self.errors.append(f"Error checking {py_file}: {e}")
        
        return broken_imports
    
    def generate_cleanup_report(self):
        """Generate comprehensive cleanup report"""
        
        # Perform analyses
        rlvr_analysis = self.analyze_rlvr_backups()
        diagnostic_analysis = self.analyze_diagnostic_files()
        import_issues = self.validate_import_references()
        
        report = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "workspace_path": str(self.workspace_path),
            "analyses": {
                "rlvr_backups": rlvr_analysis,
                "diagnostic_files": diagnostic_analysis,
                "import_references": import_issues
            },
            "actions_taken": {
                "archived_files": self.archived_files,
                "deleted_files": self.deleted_files,
                "errors": self.errors
            },
            "recommendations": self._generate_recommendations(rlvr_analysis, diagnostic_analysis)
        }
        
        return report
    
    def _generate_recommendations(self, rlvr_analysis, diagnostic_analysis):
        """Generate cleanup recommendations"""
        recommendations = []
        
        if rlvr_analysis["total_files"] > 100:
            recommendations.append({
                "priority": "HIGH",
                "action": "Archive RLVR backups",
                "description": f"Found {rlvr_analysis['total_files']} RLVR backup files consuming {round(rlvr_analysis['total_size']/(1024*1024), 2)}MB",
                "command": "cleanup.archive_rlvr_backups(max_age_days=30)"
            })
        
        if diagnostic_analysis:
            total_diagnostic_size = sum(f["size_mb"] for f in diagnostic_analysis)
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Compress diagnostic files",
                "description": f"Found {len(diagnostic_analysis)} large diagnostic files totaling {round(total_diagnostic_size, 2)}MB",
                "command": "cleanup.compress_diagnostic_files()"
            })
        
        return recommendations
    
    def execute_smart_cleanup(self, dry_run: bool = False):
        """Execute smart cleanup with safety checks"""
        
        if dry_run:
            self.logger.info("🧪 DRY RUN MODE - No files will be modified")
        
        results = {
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }
        
        # Archive old RLVR backups
        if not dry_run:
            rlvr_results = self.archive_rlvr_backups(max_age_days=30)
            results["actions"]["rlvr_archival"] = rlvr_results
            self.logger.info(f"✅ Archived {rlvr_results['archived_count']} RLVR backup files ({rlvr_results['archived_size_mb']}MB)")
        
        # Compress large diagnostic files
        if not dry_run:
            compression_results = self.compress_diagnostic_files()
            results["actions"]["diagnostic_compression"] = compression_results
            self.logger.info(f"✅ Compressed {len(compression_results)} diagnostic files")
        
        # Clean empty directories
        if not dry_run:
            empty_dirs = self.clean_empty_directories()
            results["actions"]["empty_directories"] = empty_dirs
            self.logger.info(f"✅ Removed {len(empty_dirs)} empty directories")
        
        # Generate final report
        results["full_report"] = self.generate_cleanup_report()
        
        # Save cleanup log
        log_file = self.archive_dir / "cleanup_log.json"
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"📋 Cleanup report saved to: {log_file}")
        
        return results

def main():
    """Main execution function"""
    workspace_path = "k:\\Project Heimnetz"
    
    print("🧹 SMART REPOSITORY CLEANUP SYSTEM")
    print("=" * 50)
    print(f"Workspace: {workspace_path}")
    print()
    
    cleanup = SmartRepositoryCleanup(workspace_path)
    
    # Ask user for confirmation
    print("This script will:")
    print("• Archive RLVR backup files older than 30 days")
    print("• Compress large diagnostic files")
    print("• Remove empty directories")
    print("• Generate comprehensive cleanup report")
    print()
    
    confirm = input("Proceed with cleanup? (y/N): ").lower().strip()
    
    if confirm == 'y':
        # First run in dry-run mode for preview
        print("🧪 Running analysis (dry-run)...")
        dry_results = cleanup.execute_smart_cleanup(dry_run=True)
        
        print(f"📊 Analysis complete. Check report for details.")
        print(f"Archive directory: {cleanup.archive_dir}")
        
        # Ask for final confirmation
        final_confirm = input("Execute actual cleanup? (y/N): ").lower().strip()
        
        if final_confirm == 'y':
            print("🚀 Executing cleanup...")
            results = cleanup.execute_smart_cleanup(dry_run=False)
            print("✅ Cleanup complete!")
        else:
            print("ℹ️ Cleanup cancelled. Dry-run results preserved.")
    else:
        print("ℹ️ Cleanup cancelled.")

if __name__ == "__main__":
    main()
