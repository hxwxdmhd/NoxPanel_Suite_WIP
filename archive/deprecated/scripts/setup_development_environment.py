#!/usr/bin/env python3
"""
NoxPanel Suite Automated Development Environment Setup
Configures optimal development environment with performance validation
"""

import json
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

class NoxPanelEnvironmentSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.devcontainer_path = self.project_root / ".devcontainer"
        self.vscode_path = self.project_root / ".vscode"
        
    def check_docker_availability(self):
        """Check if Docker Desktop is available and running"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Check if Docker daemon is running
                daemon_result = subprocess.run(["docker", "info"], 
                                             capture_output=True, text=True, timeout=10)
                return daemon_result.returncode == 0
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_wsl2_availability(self):
        """Check if WSL2 is available"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(["wsl", "--list", "--verbose"], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0 and "Version: 2" in result.stdout
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def setup_remote_container(self):
        """Setup Remote Container development environment"""
        print("🐳 Setting up Remote Container environment...")
        
        if not self.check_docker_availability():
            print("❌ Docker Desktop not available or not running")
            print("   Please install Docker Desktop and ensure it's running")
            return False
        
        print("✅ Docker Desktop available")
        
        # Ensure devcontainer directory exists
        self.devcontainer_path.mkdir(exist_ok=True)
        
        # The devcontainer.json is already created above
        if (self.devcontainer_path / "devcontainer.json").exists():
            print("✅ devcontainer.json configured")
        else:
            print("❌ devcontainer.json not found")
            return False
        
        # Make setup script executable
        setup_script = self.devcontainer_path / "setup-environment.sh"
        if setup_script.exists():
            try:
                os.chmod(setup_script, 0o755)
                print("✅ Setup script prepared")
            except Exception as e:
                print(f"⚠️ Could not make setup script executable: {e}")
        
        return True
    
    def setup_wsl2_fallback(self):
        """Setup WSL2 development environment"""
        print("🐧 Setting up WSL2 fallback environment...")
        
        if not self.check_wsl2_availability():
            print("❌ WSL2 not available")
            print("   Please install WSL2: wsl --install")
            return False
        
        print("✅ WSL2 available")
        
        # Create WSL setup instructions
        wsl_setup_path = self.project_root / "docs" / "WSL2_SETUP_GUIDE.md"
        if wsl_setup_path.exists():
            print("✅ WSL2 setup guide available")
            print(f"   Follow instructions in: {wsl_setup_path}")
        
        return True
    
    def setup_multi_root_workspace(self):
        """Setup multi-root workspace as fallback"""
        print("📁 Setting up multi-root workspace fallback...")
        
        workspace_file = self.project_root / "noxpanel-modular-workspace.code-workspace"
        if workspace_file.exists():
            print("✅ Multi-root workspace configuration available")
            print(f"   Open workspace: {workspace_file}")
            
            # Create individual folder .vscode settings for optimization
            folders = [
                ("AI/NoxPanel", {"python.analysis.diagnosticMode": "openFilesOnly"}),
                ("plugins", {"python.analysis.diagnosticMode": "openFilesOnly"}),
                ("aethercore", {"python.analysis.diagnosticMode": "workspace"}),
            ]
            
            for folder_path, settings in folders:
                folder_vscode_path = self.project_root / folder_path / ".vscode"
                folder_vscode_path.mkdir(exist_ok=True)
                
                settings_file = folder_vscode_path / "settings.json"
                if not settings_file.exists():
                    with open(settings_file, 'w') as f:
                        json.dump(settings, f, indent=2)
                    print(f"✅ Optimized settings for {folder_path}")
        
        return True
    
    def run_performance_validation(self):
        """Run performance validation to determine best setup"""
        print("⚡ Running performance validation...")
        
        # Create a simple performance test
        start_time = time.time()
        
        # Test 1: File system performance
        try:
            file_count = len(list(self.project_root.rglob("*.py")))
            file_scan_time = time.time() - start_time
            print(f"📁 Python files found: {file_count} (scan time: {file_scan_time:.2f}s)")
        except Exception as e:
            print(f"⚠️ File scan error: {e}")
            file_scan_time = 0
            file_count = 0
        
        # Test 2: Git performance
        git_start = time.time()
        try:
            result = subprocess.run(["git", "status"], 
                                  cwd=self.project_root, capture_output=True, timeout=10)
            git_time = time.time() - git_start
            git_ok = result.returncode == 0
            print(f"🔧 Git status: {'OK' if git_ok else 'FAILED'} ({git_time:.2f}s)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            git_time = 10.0
            git_ok = False
        
        # Performance assessment
        performance_score = 100
        if file_scan_time > 5.0:
            performance_score -= 30
        if git_time > 2.0:
            performance_score -= 20
        if file_count > 2000:
            performance_score -= 25
        
        print(f"📊 Performance Score: {max(0, performance_score)}/100")
        
        return {
            "file_count": file_count,
            "file_scan_time": file_scan_time,
            "git_time": git_time,
            "performance_score": max(0, performance_score)
        }
    
    def recommend_setup(self, performance_results):
        """Recommend optimal development setup"""
        docker_available = self.check_docker_availability()
        wsl2_available = self.check_wsl2_availability()
        performance_score = performance_results["performance_score"]
        
        print("\n🎯 SETUP RECOMMENDATIONS:")
        print("=" * 40)
        
        if docker_available and performance_score >= 60:
            print("✅ RECOMMENDED: Remote Container Development")
            print("   • Best performance and isolation")
            print("   • Automated dependency management")
            print("   • Consistent environment across team")
            print(f"   • Run: code --folder-uri vscode-remote://dev-container%2Bk%3A%5CProject%20Heimnetz")
            return "remote-container"
            
        elif wsl2_available and performance_score >= 40:
            print("🟡 RECOMMENDED: WSL2 Development") 
            print("   • Good performance with native Linux tools")
            print("   • Better Docker integration than Windows")
            print("   • Follow WSL2 setup guide")
            return "wsl2"
            
        else:
            print("🟠 RECOMMENDED: Multi-Root Workspace")
            print("   • Optimized for large Windows projects")
            print("   • Reduced indexing load per workspace")
            print("   • Manual dependency management")
            print(f"   • Open: {self.project_root / 'noxpanel-modular-workspace.code-workspace'}")
            return "multi-root"
    
    def create_quick_start_script(self, recommended_setup):
        """Create quick start script for recommended setup"""
        script_content = {
            "remote-container": '''
echo "🚀 Starting NoxPanel Remote Container Development"
echo "Ensure Docker Desktop is running..."
code --folder-uri "vscode-remote://dev-container+k%3A%5CProject%20Heimnetz"
echo "Container will build automatically on first launch"
''',
            "wsl2": '''
echo "🐧 Starting NoxPanel WSL2 Development"
wsl --cd "/mnt/k/Project Heimnetz"
echo "Follow WSL2_SETUP_GUIDE.md for initial setup"
''',
            "multi-root": '''
echo "📁 Opening NoxPanel Multi-Root Workspace"
code "k:\\Project Heimnetz\\noxpanel-modular-workspace.code-workspace"
echo "Workspace optimized for large project performance"
'''
        }
        
        script_path = self.project_root / f"start-{recommended_setup}.bat"
        with open(script_path, 'w') as f:
            f.write(script_content[recommended_setup])
        
        print(f"✅ Quick start script created: {script_path}")
    
    def run_setup(self):
        """Run complete automated setup"""
        print("🚀 NoxPanel Suite Automated Environment Setup")
        print("=" * 50)
        
        # Run performance validation first
        performance_results = self.run_performance_validation()
        
        # Check available options
        docker_ok = self.setup_remote_container() if self.check_docker_availability() else False
        wsl2_ok = self.setup_wsl2_fallback() if self.check_wsl2_availability() else False
        multiroot_ok = self.setup_multi_root_workspace()
        
        # Get recommendation
        recommended_setup = self.recommend_setup(performance_results)
        
        # Create quick start script
        self.create_quick_start_script(recommended_setup)
        
        print("\n✅ SETUP COMPLETE!")
        print("=" * 20)
        print(f"🎯 Recommended: {recommended_setup}")
        print(f"🚀 Quick Start: start-{recommended_setup}.bat")
        
        # Save setup results
        setup_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recommended_setup": recommended_setup,
            "docker_available": docker_ok,
            "wsl2_available": wsl2_ok,
            "performance_results": performance_results
        }
        
        with open(self.project_root / "environment_setup_results.json", 'w') as f:
            json.dump(setup_results, f, indent=2)
        
        return setup_results

def main():
    setup = NoxPanelEnvironmentSetup()
    results = setup.run_setup()
    
    print(f"\n📊 Setup completed with {results['recommended_setup']} configuration")
    print("🔄 Run this script again anytime to re-validate your setup")

if __name__ == "__main__":
    main()
