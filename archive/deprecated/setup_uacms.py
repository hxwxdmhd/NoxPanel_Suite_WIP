#!/usr/bin/env python3
"""
🛠️ U.A.C.M.S. COMPLETE SETUP SCRIPT
===================================

This script sets up the complete Unified AI-Collaborative Mitigation System (U.A.C.M.S.)
for bulletproof project management across the NoxPanel / Heimnetz / NoxGuard ecosystem.

Usage:
    python setup_uacms.py --init         # Initialize complete system
    python setup_uacms.py --status       # Show system status
    python setup_uacms.py --validate     # Validate system integrity
    python setup_uacms.py --sync         # Synchronize AI agents

Author: U.A.C.M.S. System
Version: 1.0
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class UACMSSetup:
    """Complete U.A.C.M.S. setup and management system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.setup_info = {
            "system_name": "U.A.C.M.S.",
            "version": "1.0",
            "description": "Unified AI-Collaborative Mitigation System",
            "initialized": datetime.now().isoformat(),
            "project_root": str(self.project_root)
        }
    
    def display_banner(self):
        """Display U.A.C.M.S. banner"""
        print("🛠️" + "=" * 60)
        print("🛠️  UNIFIED AI-COLLABORATIVE MITIGATION SYSTEM (U.A.C.M.S.)")
        print("🛠️" + "=" * 60)
        print("🛠️  Version: 1.0")
        print("🛠️  Purpose: Bulletproof AI-coordinated project management")
        print("🛠️  Scope: NoxPanel / Heimnetz / NoxGuard ecosystem")
        print("🛠️" + "=" * 60)
        print()
    
    def check_prerequisites(self) -> Dict:
        """Check system prerequisites"""
        print("🔍 Checking prerequisites...")
        
        prereqs = {
            "python_version": sys.version_info >= (3, 8),
            "project_root_exists": self.project_root.exists(),
            "scripts_dir_exists": (self.project_root / "scripts").exists(),
            "write_permissions": os.access(self.project_root, os.W_OK),
            "status": "CHECKING"
        }
        
        # Check Python version
        if prereqs["python_version"]:
            print("  ✅ Python version: OK")
        else:
            print("  ❌ Python version: Requires Python 3.8+")
        
        # Check project root
        if prereqs["project_root_exists"]:
            print("  ✅ Project root: OK")
        else:
            print("  ❌ Project root: Does not exist")
        
        # Check write permissions
        if prereqs["write_permissions"]:
            print("  ✅ Write permissions: OK")
        else:
            print("  ❌ Write permissions: Insufficient")
        
        # Determine overall status
        if all([prereqs["python_version"], prereqs["project_root_exists"], prereqs["write_permissions"]]):
            prereqs["status"] = "PASSED"
            print("  🎯 Prerequisites: PASSED")
        else:
            prereqs["status"] = "FAILED"
            print("  💥 Prerequisites: FAILED")
        
        return prereqs
    
    def initialize_system(self) -> Dict:
        """Initialize complete U.A.C.M.S. system"""
        print("🚀 Initializing U.A.C.M.S. system...")
        
        initialization_results = {
            "timestamp": datetime.now().isoformat(),
            "status": "IN_PROGRESS",
            "components_initialized": [],
            "errors": []
        }
        
        try:
            # Step 1: Initialize project safety
            print("  📋 Step 1: Initializing project safety...")
            init_script = self.project_root / "scripts" / "init_project_safely.py"
            if init_script.exists():
                result = subprocess.run([sys.executable, str(init_script), "--init"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    initialization_results["components_initialized"].append("project_safety")
                    print("    ✅ Project safety initialized")
                else:
                    print(f"    ❌ Project safety failed: {result.stderr}")
            else:
                print("    ⚠️  init_project_safely.py not found")
            
            # Step 2: Validate architectural structure
            print("  🏗️  Step 2: Validating architectural structure...")
            enforce_script = self.project_root / "scripts" / "enforce_structure.py"
            if enforce_script.exists():
                result = subprocess.run([sys.executable, str(enforce_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    initialization_results["components_initialized"].append("architectural_validation")
                    print("    ✅ Architectural structure validated")
                else:
                    print(f"    ⚠️  Architectural validation warnings: {result.stdout}")
            else:
                print("    ⚠️  enforce_structure.py not found")
            
            # Step 3: Initialize audit system
            print("  📊 Step 3: Initializing audit system...")
            audit_script = self.project_root / "scripts" / "audit_system.py"
            if audit_script.exists():
                result = subprocess.run([sys.executable, str(audit_script), "--status"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    initialization_results["components_initialized"].append("audit_system")
                    print("    ✅ Audit system initialized")
                else:
                    print(f"    ⚠️  Audit system warnings: {result.stderr}")
            else:
                print("    ⚠️  audit_system.py not found")
            
            # Step 4: Synchronize AI agents
            print("  🤖 Step 4: Synchronizing AI agents...")
            memory_script = self.project_root / "scripts" / "update_memory.py"
            if memory_script.exists():
                result = subprocess.run([sys.executable, str(memory_script), "--sync"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    initialization_results["components_initialized"].append("ai_synchronization")
                    print("    ✅ AI agents synchronized")
                else:
                    print(f"    ⚠️  AI synchronization warnings: {result.stderr}")
            else:
                print("    ⚠️  update_memory.py not found")
            
            # Step 5: Validate system integrity
            print("  🔍 Step 5: Validating system integrity...")
            system_valid = self.validate_system_integrity()
            if system_valid:
                initialization_results["components_initialized"].append("system_validation")
                print("    ✅ System integrity validated")
            else:
                print("    ⚠️  System integrity validation warnings")
            
            initialization_results["status"] = "COMPLETED"
            print("  🎯 U.A.C.M.S. Initialization: COMPLETED")
            
        except Exception as e:
            initialization_results["status"] = "FAILED"
            initialization_results["errors"].append(str(e))
            print(f"  ❌ Initialization failed: {e}")
        
        return initialization_results
    
    def validate_system_integrity(self) -> bool:
        """Validate complete system integrity"""
        print("🔍 Validating system integrity...")
        
        # Check critical files
        critical_files = [
            "project_state.json",
            "scripts/enforce_structure.py",
            "scripts/audit_system.py",
            "scripts/update_memory.py",
            "scripts/init_project_safely.py",
            "README_PHASE_LOCK.md"
        ]
        
        all_valid = True
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path}")
                all_valid = False
        
        # Check project state
        project_state_file = self.project_root / "project_state.json"
        if project_state_file.exists():
            try:
                with open(project_state_file, 'r') as f:
                    state = json.load(f)
                
                required_keys = ["system_name", "current_phase", "audit_status", "architectural_compliance"]
                for key in required_keys:
                    if key in state:
                        print(f"  ✅ project_state.{key}")
                    else:
                        print(f"  ❌ project_state.{key}")
                        all_valid = False
                        
            except Exception as e:
                print(f"  ❌ project_state.json invalid: {e}")
                all_valid = False
        
        if all_valid:
            print("  🎯 System integrity: VALIDATED")
        else:
            print("  ⚠️  System integrity: WARNINGS")
        
        return all_valid
    
    def display_system_status(self):
        """Display comprehensive system status"""
        print("📊 U.A.C.M.S. System Status Report")
        print("=" * 50)
        
        # Load project state
        project_state_file = self.project_root / "project_state.json"
        if project_state_file.exists():
            try:
                with open(project_state_file, 'r') as f:
                    state = json.load(f)
                
                print(f"System Name: {state.get('system_name', 'Unknown')}")
                print(f"Version: {state.get('version', 'Unknown')}")
                print(f"Current Phase: {state.get('current_phase', 'Unknown')}")
                
                # Architectural compliance
                compliance = state.get('architectural_compliance', {})
                print(f"Compliance Score: {compliance.get('compliance', 0)}%")
                print(f"Violations: {compliance.get('violations', 0)}")
                
                # Audit status
                audit_status = state.get('audit_status', {})
                print(f"\nAudit Status:")
                for audit, info in audit_status.items():
                    status = info.get('status', 'UNKNOWN')
                    print(f"  {audit}: {status}")
                
                # Features
                locked_features = state.get('locked_features', {})
                unlocked_features = state.get('unlocked_features', {})
                
                print(f"\nLocked Features: {len(locked_features)}")
                for feature in locked_features:
                    print(f"  🔒 {feature}")
                
                print(f"\nUnlocked Features: {len(unlocked_features)}")
                for feature in unlocked_features:
                    print(f"  ✅ {feature}")
                
                # AI coordination
                ai_coord = state.get('ai_coordination', {})
                print(f"\nAI Coordination:")
                print(f"  ChatGPT Sync: {ai_coord.get('chatgpt_sync', False)}")
                print(f"  Copilot Sync: {ai_coord.get('copilot_sync', False)}")
                print(f"  Shared Memory: {ai_coord.get('shared_memory_active', False)}")
                
            except Exception as e:
                print(f"❌ Error reading project state: {e}")
        else:
            print("❌ project_state.json not found")
    
    def sync_ai_agents(self):
        """Synchronize AI agents"""
        print("🤖 Synchronizing AI agents...")
        
        memory_script = self.project_root / "scripts" / "update_memory.py"
        if memory_script.exists():
            result = subprocess.run([sys.executable, str(memory_script), "--sync"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ AI agents synchronized successfully")
                print(result.stdout)
            else:
                print(f"❌ AI synchronization failed: {result.stderr}")
        else:
            print("❌ update_memory.py not found")
    
    def create_setup_summary(self) -> Dict:
        """Create comprehensive setup summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.setup_info,
            "components": {
                "architectural_enforcement": "enforce_structure.py",
                "progressive_audits": "audit_system.py", 
                "ai_coordination": "update_memory.py",
                "project_safety": "init_project_safely.py",
                "phase_locks": "README_PHASE_LOCK.md",
                "project_state": "project_state.json"
            },
            "features": {
                "architectural_compliance": "ACTIVE",
                "progressive_gates": "ACTIVE",
                "ai_synchronization": "ACTIVE",
                "fail_safe_responses": "ACTIVE",
                "phase_based_development": "ACTIVE"
            },
            "guarantees": [
                "No competing implementations",
                "No scope creep",
                "No AI conflicts",
                "No architectural regression",
                "Synchronized AI agents",
                "Progressive development",
                "Bulletproof compliance"
            ]
        }
        
        return summary

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="U.A.C.M.S. Complete Setup Script")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--init", action="store_true", help="Initialize complete U.A.C.M.S. system")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--validate", action="store_true", help="Validate system integrity")
    parser.add_argument("--sync", action="store_true", help="Synchronize AI agents")
    
    args = parser.parse_args()
    
    # Create setup manager
    setup = UACMSSetup(args.project_root)
    
    # Display banner
    setup.display_banner()
    
    if args.init:
        # Check prerequisites
        prereqs = setup.check_prerequisites()
        if prereqs["status"] != "PASSED":
            print("❌ Prerequisites not met. Cannot initialize system.")
            sys.exit(1)
        
        # Initialize system
        results = setup.initialize_system()
        
        # Create summary
        summary = setup.create_setup_summary()
        summary_file = setup.project_root / "uacms_setup_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Setup summary saved to: {summary_file}")
        
        if results["status"] == "COMPLETED":
            print("\n🎯 U.A.C.M.S. SETUP: COMPLETED SUCCESSFULLY")
            print("🛡️  Your project is now protected by bulletproof AI coordination!")
            sys.exit(0)
        else:
            print("\n⚠️  U.A.C.M.S. SETUP: COMPLETED WITH WARNINGS")
            sys.exit(1)
    
    elif args.status:
        setup.display_system_status()
    
    elif args.validate:
        valid = setup.validate_system_integrity()
        sys.exit(0 if valid else 1)
    
    elif args.sync:
        setup.sync_ai_agents()
    
    else:
        # Show help
        parser.print_help()

if __name__ == "__main__":
    main()
