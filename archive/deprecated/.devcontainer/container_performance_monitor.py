#!/usr/bin/env python3
"""
NoxPanel Container Performance Monitor & Resource Manager
Dynamically adjusts container resources based on system capabilities and workload
"""

import json
import os
import sys
import time
import subprocess
import psutil
from pathlib import Path

class ContainerResourceManager:
    def __init__(self):
        self.workspace_path = Path("/workspace")
        self.results_file = self.workspace_path / ".devcontainer" / "resource_optimization.json"
        
    def get_system_specs(self):
        """Get container system specifications"""
        try:
            memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
            cpu_count = psutil.cpu_count()
            
            # Get Docker host specs if available
            try:
                host_memory = subprocess.check_output([
                    "docker", "system", "info", "--format", "{{.MemTotal}}"
                ], text=True).strip()
                host_memory_gb = int(host_memory) / (1024**3) if host_memory.isdigit() else memory_gb
            except:
                host_memory_gb = memory_gb
                
            return {
                "container_memory_gb": memory_gb,
                "host_memory_gb": host_memory_gb,
                "cpu_count": cpu_count,
                "recommended_memory": min(max(4, host_memory_gb * 0.6), 8),  # 60% of host, min 4GB, max 8GB
                "recommended_cpus": min(cpu_count, max(2, cpu_count * 0.7))  # 70% of CPUs, min 2
            }
        except Exception as e:
            print(f"⚠️ Error getting system specs: {e}")
            return {"container_memory_gb": 4, "cpu_count": 2, "recommended_memory": 4, "recommended_cpus": 2}
    
    def analyze_workspace(self):
        """Analyze workspace for performance bottlenecks"""
        print("🔍 Analyzing workspace structure...")
        
        file_stats = {
            "python_files": 0,
            "js_files": 0,
            "php_files": 0,
            "total_files": 0,
            "large_directories": {},
            "heavy_modules": []
        }
        
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            'docker', 'volumes', 'prometheus_data', 'grafana_data',
            'logs', 'archive', 'test_reports'
        }
        
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path = Path(root)
            rel_path = root_path.relative_to(self.workspace_path)
            
            file_count = len(files)
            file_stats["total_files"] += file_count
            
            # Track large directories (>100 files)
            if file_count > 100:
                file_stats["large_directories"][str(rel_path)] = file_count
            
            # Count by file type
            for file in files:
                ext = Path(file).suffix.lower()
                if ext == '.py':
                    file_stats["python_files"] += 1
                elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                    file_stats["js_files"] += 1
                elif ext == '.php':
                    file_stats["php_files"] += 1
        
        # Identify heavy modules that could be containerized separately
        for dir_name, file_count in file_stats["large_directories"].items():
            if file_count > 500:  # Very large modules
                file_stats["heavy_modules"].append({
                    "name": dir_name,
                    "file_count": file_count,
                    "containerize_recommendation": True
                })
        
        return file_stats
    
    def run_performance_benchmark(self):
        """Run comprehensive performance benchmark"""
        print("⚡ Running performance benchmark...")
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "benchmarks": {}
        }
        
        # Test 1: VS Code indexing simulation
        start_time = time.time()
        try:
            # Simulate file tree traversal
            subprocess.run([
                "find", str(self.workspace_path), 
                "-name", "*.py", "-o", "-name", "*.js", "-o", "-name", "*.php"
            ], capture_output=True, text=True, timeout=30)
            indexing_time = time.time() - start_time
        except subprocess.TimeoutExpired:
            indexing_time = 30.0  # Timeout indicates performance issue
        
        results["benchmarks"]["file_indexing_seconds"] = round(indexing_time, 2)
        
        # Test 2: Python import performance
        start_time = time.time()
        try:
            subprocess.run([
                "python", "-c", 
                "import sys, json, requests, flask, sqlalchemy; print('OK')"
            ], capture_output=True, timeout=10)
            python_time = time.time() - start_time
        except subprocess.TimeoutExpired:
            python_time = 10.0
        
        results["benchmarks"]["python_imports_seconds"] = round(python_time, 2)
        
        # Test 3: Git operations
        start_time = time.time()
        try:
            subprocess.run(["git", "status"], 
                         cwd=self.workspace_path, capture_output=True, timeout=5)
            git_time = time.time() - start_time
        except subprocess.TimeoutExpired:
            git_time = 5.0
        
        results["benchmarks"]["git_status_seconds"] = round(git_time, 2)
        
        # Performance assessment
        performance_score = self.calculate_performance_score(results["benchmarks"])
        results["performance_score"] = performance_score
        results["performance_rating"] = self.get_performance_rating(performance_score)
        
        return results
    
    def calculate_performance_score(self, benchmarks):
        """Calculate overall performance score (0-100)"""
        # Scoring thresholds (lower is better for times)
        thresholds = {
            "file_indexing_seconds": {"excellent": 2.0, "good": 5.0, "fair": 10.0},
            "python_imports_seconds": {"excellent": 1.0, "good": 2.0, "fair": 5.0},
            "git_status_seconds": {"excellent": 0.5, "good": 1.0, "fair": 2.0}
        }
        
        total_score = 0
        for metric, value in benchmarks.items():
            if metric in thresholds:
                if value <= thresholds[metric]["excellent"]:
                    total_score += 100
                elif value <= thresholds[metric]["good"]:
                    total_score += 75
                elif value <= thresholds[metric]["fair"]:
                    total_score += 50
                else:
                    total_score += 25
        
        return round(total_score / len(thresholds), 1)
    
    def get_performance_rating(self, score):
        """Get performance rating based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"
    
    def generate_optimization_recommendations(self, system_specs, workspace_stats, benchmark_results):
        """Generate optimization recommendations"""
        recommendations = []
        
        # Memory recommendations
        if system_specs["container_memory_gb"] < system_specs["recommended_memory"]:
            recommendations.append({
                "type": "memory",
                "priority": "high",
                "description": f"Increase container memory to {system_specs['recommended_memory']:.1f}GB",
                "action": f"Add 'runArgs': ['--memory={system_specs['recommended_memory']:.0f}g'] to devcontainer.json"
            })
        
        # CPU recommendations
        if system_specs["cpu_count"] < system_specs["recommended_cpus"]:
            recommendations.append({
                "type": "cpu",
                "priority": "medium", 
                "description": f"Allocate {system_specs['recommended_cpus']:.0f} CPU cores",
                "action": f"Add '--cpus={system_specs['recommended_cpus']:.1f}' to runArgs"
            })
        
        # File exclusion recommendations
        if workspace_stats["total_files"] > 2000:
            recommendations.append({
                "type": "files",
                "priority": "high",
                "description": f"Large workspace ({workspace_stats['total_files']} files) may slow indexing",
                "action": "Implement stricter file exclusions in VS Code settings"
            })
        
        # Module containerization recommendations
        if workspace_stats["heavy_modules"]:
            for module in workspace_stats["heavy_modules"]:
                recommendations.append({
                    "type": "containerization",
                    "priority": "medium",
                    "description": f"Module '{module['name']}' has {module['file_count']} files",
                    "action": f"Consider separate dev container for {module['name']}"
                })
        
        # Performance-based recommendations
        if benchmark_results["performance_score"] < 50:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "description": f"Poor performance score: {benchmark_results['performance_score']}/100",
                "action": "Consider WSL2 or native development as fallback"
            })
        
        return recommendations
    
    def save_results(self, results):
        """Save optimization results to file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to {self.results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def run_analysis(self):
        """Run complete performance analysis"""
        print("🚀 NoxPanel Container Performance Analysis")
        print("=" * 50)
        
        # Get system specifications
        system_specs = self.get_system_specs()
        print(f"💻 Container Memory: {system_specs['container_memory_gb']}GB")
        print(f"⚙️ CPU Cores: {system_specs['cpu_count']}")
        print(f"📊 Recommended Memory: {system_specs['recommended_memory']:.1f}GB")
        
        # Analyze workspace
        workspace_stats = self.analyze_workspace()
        print(f"📁 Total Files: {workspace_stats['total_files']}")
        print(f"🐍 Python Files: {workspace_stats['python_files']}")
        print(f"📦 JS/TS Files: {workspace_stats['js_files']}")
        print(f"🐘 PHP Files: {workspace_stats['php_files']}")
        
        # Run benchmarks
        benchmark_results = self.run_performance_benchmark()
        print(f"⚡ Performance Score: {benchmark_results['performance_score']}/100 ({benchmark_results['performance_rating']})")
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(
            system_specs, workspace_stats, benchmark_results
        )
        
        # Compile results
        results = {
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_specs": system_specs,
            "workspace_stats": workspace_stats,
            "benchmark_results": benchmark_results,
            "recommendations": recommendations
        }
        
        # Save and display results
        self.save_results(results)
        
        print("\n🎯 OPTIMIZATION RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"{i}. {priority_icon} {rec['description']}")
            print(f"   → {rec['action']}")
        
        return results

def main():
    if "--container-mode" in sys.argv:
        manager = ContainerResourceManager()
        results = manager.run_analysis()
        
        # Auto-apply high priority optimizations if possible
        high_priority_recs = [r for r in results["recommendations"] if r["priority"] == "high"]
        if high_priority_recs:
            print(f"\n⚠️ Found {len(high_priority_recs)} high-priority performance issues")
            print("🔧 Consider applying the recommended optimizations")
    else:
        print("Usage: python container_performance_monitor.py --container-mode")

if __name__ == "__main__":
    main()
