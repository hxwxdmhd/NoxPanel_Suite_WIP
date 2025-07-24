#!/usr/bin/env python3
"""
Manual NoxPanel Environment Validation and Setup
"""

import json
import time
from pathlib import Path

def validate_environment():
    """Validate current NoxPanel environment state"""
    project_root = Path("k:/Project Heimnetz")
    
    print("🚀 NoxPanel Suite Environment Validation")
    print("=" * 50)
    
    validation_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment_checks": {},
        "recommendations": []
    }
    
    # Check core files
    core_files = [
        "main.py",
        "docker-compose.yml", 
        "docker-compose.dev.yml",
        "docker-compose.override.yml",
        ".devcontainer/devcontainer.json",
        ".vscode/settings.json",
        ".vscode/tasks.json",
        "plugins/fritzwatcher_plugin.py",
        "plugins/test_fritzwatcher_integration.py"
    ]
    
    print("📁 Checking core files...")
    for file_path in core_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        validation_results["environment_checks"][file_path] = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {file_path}: {'✅ EXISTS' if exists else '❌ MISSING'}")
    
    # Check plugin system status
    print("\n🔌 Plugin System Status...")
    plugins_dir = project_root / "plugins"
    if plugins_dir.exists():
        plugin_files = list(plugins_dir.glob("*.py"))
        print(f"  Plugin files found: {len(plugin_files)}")
        validation_results["environment_checks"]["plugin_count"] = len(plugin_files)
        
        # Check FRITZWATCHER specifically
        fritzwatcher_files = [
            "fritzwatcher_plugin.py",
            "fritzwatcher_resilience.py", 
            "fritzwatcher_ux.py",
            "test_fritzwatcher_integration.py",
            "test_fritzwatcher_comprehensive.py"
        ]
        
        fritzwatcher_complete = True
        for fw_file in fritzwatcher_files:
            fw_path = plugins_dir / fw_file
            exists = fw_path.exists()
            if not exists:
                fritzwatcher_complete = False
            print(f"  FRITZWATCHER {fw_file}: {'✅' if exists else '❌'}")
        
        validation_results["environment_checks"]["fritzwatcher_complete"] = fritzwatcher_complete
        
    # Environment recommendations
    print("\n💡 Environment Recommendations...")
    
    # Check if devcontainer is configured
    devcontainer_json = project_root / ".devcontainer" / "devcontainer.json"
    if devcontainer_json.exists():
        print("✅ Remote Container configuration available")
        validation_results["recommendations"].append("Use Remote Container for optimal development")
    else:
        print("⚠️ Remote Container not configured")
        validation_results["recommendations"].append("Configure Remote Container for better performance")
    
    # Check workspace configuration
    workspace_file = project_root / "noxpanel-modular-workspace.code-workspace"
    if workspace_file.exists():
        print("✅ Multi-root workspace configuration available")
        validation_results["recommendations"].append("Multi-root workspace ready as fallback")
    else:
        print("⚠️ Multi-root workspace not configured")
    
    # Performance assessment
    try:
        total_files = len(list(project_root.rglob("*.py")))
        print(f"📊 Python files in project: {total_files}")
        validation_results["environment_checks"]["python_files"] = total_files
        
        if total_files > 1000:
            validation_results["recommendations"].append("Large project - recommend Remote Container or multi-root workspace")
        elif total_files > 500:
            validation_results["recommendations"].append("Medium project - VS Code optimization recommended")
        else:
            validation_results["recommendations"].append("Small project - native development suitable")
            
    except Exception as e:
        print(f"⚠️ Could not count project files: {e}")
    
    # Save validation results
    results_file = project_root / "environment_validation_results.json"
    try:
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        print(f"\n📄 Validation results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    return validation_results

def main():
    results = validate_environment()
    
    print("\n🎯 NEXT STEPS RECOMMENDATION:")
    print("=" * 30)
    
    if results["environment_checks"].get("fritzwatcher_complete", False):
        print("✅ FRITZWATCHER Plugin System: READY")
        print("🚀 Recommended next action:")
        print("   1. Start main server: python main.py")
        print("   2. Access web interface: http://localhost:5000")
        print("   3. Test FRITZWATCHER: http://localhost:5000/fritzwatcher")
    else:
        print("⚠️ FRITZWATCHER Plugin System: INCOMPLETE")
        print("🔧 Recommended action: Check missing plugin files")
    
    if len(results["recommendations"]) > 0:
        print("\n💡 Environment optimizations:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    return results

if __name__ == "__main__":
    main()
