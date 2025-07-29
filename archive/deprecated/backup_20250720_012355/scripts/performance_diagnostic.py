#!/usr/bin/env python3
"""
NoxPanel Suite Performance Diagnostic Tool
Analyzes workspace structure and provides optimization recommendations
"""

import os
import json
import time
from pathlib import Path
from collections import defaultdict
import psutil

class NoxPanelPerformanceDiagnostic:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.analysis = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "workspace_path": str(workspace_path),
            "issues": [],
            "recommendations": [],
            "file_stats": {},
            "directory_stats": {},
            "performance_metrics": {}
        }
        
    def analyze_file_structure(self):
        """Analyze file structure for performance issues"""
        print("🔍 Analyzing file structure...")
        
        file_counts = defaultdict(int)
        large_files = []
        total_files = 0
        total_size = 0
        
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            'docker', 'volumes', 'prometheus_data', 'grafana_data',
            'monitoring', 'logs', 'archive', 'test_reports'
        }
        
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path = Path(root)
            rel_path = root_path.relative_to(self.workspace_path)
            
            file_counts[str(rel_path)] = len(files)
            total_files += len(files)
            
            for file in files:
                file_path = root_path / file
                try:
                    size = file_path.stat().st_size
                    total_size += size
                    
                    # Track large files (>10MB)
                    if size > 10 * 1024 * 1024:
                        large_files.append({
                            "path": str(file_path.relative_to(self.workspace_path)),
                            "size_mb": round(size / (1024 * 1024), 2)
                        })
                except OSError:
                    pass
        
        self.analysis["file_stats"] = {
            "total_files": total_files,
            "total_size_gb": round(total_size / (1024**3), 2),
            "large_files": large_files,
            "directory_file_counts": dict(file_counts)
        }
        
        # Performance issue detection
        if total_files > 2000:
            self.analysis["issues"].append({
                "type": "performance",
                "severity": "high", 
                "description": f"Large file count ({total_files}) may slow VS Code indexing",
                "recommendation": "Add more directories to .vscode/settings.json exclusions"
            })
            
        if len(large_files) > 5:
            self.analysis["issues"].append({
                "type": "performance",
                "severity": "medium",
                "description": f"Found {len(large_files)} large files that may impact performance",
                "recommendation": "Consider moving large files to external storage or .gitignore"
            })
    
    def analyze_docker_configuration(self):
        """Analyze Docker configuration for conflicts"""
        print("🐳 Analyzing Docker configuration...")
        
        compose_files = list(self.workspace_path.glob("docker-compose*.yml"))
        
        if len(compose_files) > 4:
            self.analysis["issues"].append({
                "type": "configuration",
                "severity": "medium",
                "description": f"Found {len(compose_files)} docker-compose files - may cause conflicts",
                "recommendation": "Consolidate to: base, dev, prod, and override files only"
            })
        
        # Check for missing override file
        override_file = self.workspace_path / "docker-compose.override.yml"
        if not override_file.exists():
            self.analysis["issues"].append({
                "type": "configuration", 
                "severity": "low",
                "description": "Missing docker-compose.override.yml for local development",
                "recommendation": "Create override file for local customization"
            })
    
    def analyze_vscode_configuration(self):
        """Analyze VS Code configuration for performance"""
        print("⚙️ Analyzing VS Code configuration...")
        
        vscode_settings = self.workspace_path / ".vscode" / "settings.json"
        
        if vscode_settings.exists():
            try:
                with open(vscode_settings, 'r') as f:
                    settings = json.load(f)
                
                # Check for performance settings
                performance_settings = [
                    "search.exclude", "files.exclude", "files.watcherExclude"
                ]
                
                missing_settings = [s for s in performance_settings if s not in settings]
                
                if missing_settings:
                    self.analysis["issues"].append({
                        "type": "performance",
                        "severity": "high",
                        "description": f"Missing VS Code performance settings: {missing_settings}",
                        "recommendation": "Add file exclusion settings to improve indexing performance"
                    })
                    
            except json.JSONDecodeError:
                self.analysis["issues"].append({
                    "type": "configuration",
                    "severity": "medium", 
                    "description": "Invalid JSON in .vscode/settings.json",
                    "recommendation": "Fix JSON syntax errors in VS Code settings"
                })
        else:
            self.analysis["issues"].append({
                "type": "configuration",
                "severity": "medium",
                "description": "Missing .vscode/settings.json",
                "recommendation": "Create VS Code settings file with performance optimizations"
            })
    
    def analyze_system_resources(self):
        """Analyze system resources"""
        print("💻 Analyzing system resources...")
        
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.workspace_path))
            
            self.analysis["performance_metrics"] = {
                "memory_usage_percent": memory.percent,
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
            
            if memory.percent > 80:
                self.analysis["issues"].append({
                    "type": "system",
                    "severity": "high",
                    "description": f"High memory usage ({memory.percent}%)",
                    "recommendation": "Close unnecessary applications or increase system memory"
                })
                
            if disk.percent > 90:
                self.analysis["issues"].append({
                    "type": "system", 
                    "severity": "high",
                    "description": f"Low disk space ({disk.percent}% used)",
                    "recommendation": "Free up disk space or move workspace to larger drive"
                })
                
        except Exception as e:
            print(f"⚠️ Could not analyze system resources: {e}")
    
    def generate_recommendations(self):
        """Generate optimization recommendations"""
        print("💡 Generating recommendations...")
        
        recommendations = [
            "Enable VS Code file exclusions for better performance",
            "Consolidate Docker Compose files to reduce complexity", 
            "Add .vscode/tasks.json for common development tasks",
            "Create .env.example template for configuration",
            "Implement plugin schema validation",
            "Consider workspace folder restructuring for large projects"
        ]
        
        self.analysis["recommendations"] = recommendations
    
    def run_diagnostic(self):
        """Run complete diagnostic"""
        print("🚀 Starting NoxPanel Performance Diagnostic...")
        
        self.analyze_file_structure()
        self.analyze_docker_configuration()
        self.analyze_vscode_configuration() 
        self.analyze_system_resources()
        self.generate_recommendations()
        
        return self.analysis
    
    def save_report(self, output_path=None):
        """Save diagnostic report"""
        if output_path is None:
            output_path = self.workspace_path / "diagnostic_report.json"
            
        with open(output_path, 'w') as f:
            json.dump(self.analysis, f, indent=2)
            
        print(f"📄 Diagnostic report saved to: {output_path}")

def main():
    workspace_path = r"k:\Project Heimnetz"
    
    diagnostic = NoxPanelPerformanceDiagnostic(workspace_path)
    results = diagnostic.run_diagnostic()
    diagnostic.save_report()
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    print(f"📁 Total Files: {results['file_stats']['total_files']}")
    print(f"💾 Total Size: {results['file_stats']['total_size_gb']} GB")
    print(f"⚠️ Issues Found: {len(results['issues'])}")
    print(f"💡 Recommendations: {len(results['recommendations'])}")
    
    if results['issues']:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in results['issues']:
            if issue['severity'] == 'high':
                print(f"  • {issue['description']}")
                print(f"    → {issue['recommendation']}")
    
    print("\n✅ DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()
