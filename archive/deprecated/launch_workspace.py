#!/usr/bin/env python3
"""
🚀 NoxPanel Multi-Workspace Launcher
====================================

Smart launcher for NoxPanel modular workspace system with performance optimization
and intelligent module detection.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

class NoxPanelWorkspaceLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.workspaces = {
            "core": {
                "file": "NoxPanel-Core.code-workspace",
                "description": "🏠 Core Application & Main Server",
                "components": ["src/", "main.py", "docker/", "scripts/"],
                "performance_profile": "lightweight"
            },
            "ai": {
                "file": "NoxPanel-AI.code-workspace", 
                "description": "🧠 AI, NoxPanel & Machine Learning",
                "components": ["AI/NoxPanel/", "aethercore/", "AI/models/"],
                "performance_profile": "heavy"
            },
            "plugins": {
                "file": "NoxPanel-Plugins.code-workspace",
                "description": "🔌 Plugin System & FRITZWATCHER",
                "components": ["plugins/", "tests/plugins/"],
                "performance_profile": "medium"
            },
            "devops": {
                "file": "NoxPanel-DevOps.code-workspace",
                "description": "🐳 Docker, Monitoring & Documentation", 
                "components": ["docker/", "monitoring/", "docs/", "archive/"],
                "performance_profile": "lightweight"
            }
        }
        
    def analyze_current_context(self) -> str:
        """Analyze current directory to suggest best workspace"""
        cwd = Path.cwd()
        relative_path = cwd.relative_to(self.project_root) if cwd.is_relative_to(self.project_root) else None
        
        if not relative_path:
            return "core"  # Default fallback
            
        path_str = str(relative_path).lower()
        
        # Smart context detection
        if any(component in path_str for component in ["ai", "noxpanel", "aethercore", "contextforge"]):
            return "ai"
        elif "plugin" in path_str:
            return "plugins" 
        elif any(component in path_str for component in ["docker", "monitoring", "docs", "archive"]):
            return "devops"
        else:
            return "core"
    
    def check_workspace_exists(self, workspace: str) -> bool:
        """Check if workspace file exists"""
        workspace_file = self.project_root / self.workspaces[workspace]["file"]
        return workspace_file.exists()
    
    def get_workspace_stats(self, workspace: str) -> dict:
        """Get performance statistics for workspace"""
        workspace_info = self.workspaces[workspace]
        
        # Count files in workspace components
        total_files = 0
        python_files = 0
        
        for component in workspace_info["components"]:
            component_path = self.project_root / component
            if component_path.exists():
                if component_path.is_file():
                    total_files += 1
                    if component_path.suffix == '.py':
                        python_files += 1
                else:
                    for file in component_path.rglob("*"):
                        if file.is_file() and not any(exclude in str(file) for exclude in 
                                                    ["__pycache__", ".git", "node_modules", ".venv"]):
                            total_files += 1
                            if file.suffix == '.py':
                                python_files += 1
        
        return {
            "total_files": total_files,
            "python_files": python_files,
            "performance_profile": workspace_info["performance_profile"],
            "estimated_memory_mb": self._estimate_memory_usage(total_files, workspace_info["performance_profile"])
        }
    
    def _estimate_memory_usage(self, file_count: int, profile: str) -> int:
        """Estimate VS Code memory usage for workspace"""
        base_memory = {
            "lightweight": 200,
            "medium": 400,
            "heavy": 800
        }
        
        file_memory = file_count * 0.5  # ~0.5MB per file indexed
        
        return int(base_memory.get(profile, 400) + file_memory)
    
    def launch_workspace(self, workspace: str, background: bool = False):
        """Launch specified workspace"""
        if workspace not in self.workspaces:
            print(f"❌ Unknown workspace: {workspace}")
            print(f"Available workspaces: {', '.join(self.workspaces.keys())}")
            return False
            
        if not self.check_workspace_exists(workspace):
            print(f"❌ Workspace file not found: {self.workspaces[workspace]['file']}")
            return False
        
        workspace_file = self.project_root / self.workspaces[workspace]["file"]
        workspace_info = self.workspaces[workspace]
        stats = self.get_workspace_stats(workspace)
        
        print(f"🚀 Launching {workspace_info['description']}")
        print(f"📁 Files: {stats['total_files']} total, {stats['python_files']} Python")
        print(f"💾 Estimated memory: {stats['estimated_memory_mb']}MB")
        print(f"⚡ Performance profile: {stats['performance_profile']}")
        print()
        
        # Launch VS Code with workspace
        try:
            cmd = ["code", str(workspace_file)]
            if background:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd)
            return True
        except FileNotFoundError:
            print("❌ VS Code not found in PATH. Please install VS Code or add it to PATH.")
            return False
        except Exception as e:
            print(f"❌ Error launching workspace: {e}")
            return False
    
    def show_interactive_menu(self):
        """Show interactive workspace selection menu"""
        print("🏠 NOXPANEL MULTI-WORKSPACE LAUNCHER")
        print("=" * 60)
        
        # Show current context suggestion
        suggested = self.analyze_current_context()
        print(f"💡 Suggested workspace based on current directory: {suggested}")
        print()
        
        print("Available workspaces:")
        print("-" * 40)
        
        for i, (key, info) in enumerate(self.workspaces.items(), 1):
            stats = self.get_workspace_stats(key)
            status = "✅" if self.check_workspace_exists(key) else "❌"
            
            print(f"{i}. {status} {info['description']}")
            print(f"   Files: {stats['total_files']} | Memory: {stats['estimated_memory_mb']}MB | Profile: {stats['performance_profile']}")
            print()
        
        print(f"{len(self.workspaces) + 1}. 🎯 Launch Suggested Workspace ({suggested})")
        print(f"{len(self.workspaces) + 2}. ❌ Exit")
        print()
        
        while True:
            try:
                choice = input("Enter your choice (1-{}): ".format(len(self.workspaces) + 2)).strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(self.workspaces):
                        workspace_key = list(self.workspaces.keys())[choice_num - 1]
                        return self.launch_workspace(workspace_key)
                    elif choice_num == len(self.workspaces) + 1:
                        return self.launch_workspace(suggested)
                    elif choice_num == len(self.workspaces) + 2:
                        print("👋 Goodbye!")
                        return True
                
                print("❌ Invalid choice. Please try again.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return True
    
    def show_workspace_status(self):
        """Show status of all workspaces"""
        print("📊 NOXPANEL WORKSPACE STATUS")
        print("=" * 60)
        
        total_files = 0
        total_memory = 0
        
        for key, info in self.workspaces.items():
            exists = self.check_workspace_exists(key)
            stats = self.get_workspace_stats(key) if exists else {"total_files": 0, "python_files": 0, "estimated_memory_mb": 0}
            
            status_icon = "✅" if exists else "❌"
            print(f"{status_icon} {key.upper()}: {info['description']}")
            print(f"   📁 Files: {stats['total_files']:,} total, {stats['python_files']:,} Python")
            print(f"   💾 Memory: {stats['estimated_memory_mb']}MB")
            print(f"   ⚡ Profile: {stats.get('performance_profile', 'unknown')}")
            print()
            
            if exists:
                total_files += stats['total_files']
                total_memory += stats['estimated_memory_mb']
        
        print(f"📈 TOTALS: {total_files:,} files, ~{total_memory}MB if all workspaces loaded")
        print(f"💡 Recommended: Use focused workspaces to reduce memory usage by 60-75%")

def main():
    parser = argparse.ArgumentParser(description="NoxPanel Multi-Workspace Launcher")
    parser.add_argument("workspace", nargs="?", choices=["core", "ai", "plugins", "devops", "menu", "status"],
                       help="Workspace to launch or 'menu' for interactive selection")
    parser.add_argument("--background", "-b", action="store_true", 
                       help="Launch workspace in background")
    parser.add_argument("--status", "-s", action="store_true",
                       help="Show workspace status")
    
    args = parser.parse_args()
    
    launcher = NoxPanelWorkspaceLauncher()
    
    if args.status or args.workspace == "status":
        launcher.show_workspace_status()
    elif args.workspace and args.workspace != "menu":
        launcher.launch_workspace(args.workspace, args.background)
    else:
        launcher.show_interactive_menu()

if __name__ == "__main__":
    main()
