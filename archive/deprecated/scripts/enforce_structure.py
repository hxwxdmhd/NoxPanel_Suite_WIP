#!/usr/bin/env python3
"""
U.A.C.M.S. - Architectural Structure Enforcer
==============================================

This script validates the project structure against the merge proposal plan
and prevents architectural violations from occurring.

Author: U.A.C.M.S. System
Version: 1.0
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ArchitecturalEnforcer:
    """Enforces architectural boundaries and prevents violations"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.project_state_file = self.project_root / "project_state.json"
        self.merge_plan_file = self.project_root / "docs" / "merge_plan.md"
        
        # Load project state
        self.project_state = self.load_project_state()
        
        # Define architectural rules
        self.architectural_rules = {
            "max_servers": 1,
            "max_plugin_systems": 1,
            "max_database_models": 1,
            "required_unified_files": [
                "main_unified_server_clean.py",
                "models_unified_clean.py", 
                "unified_plugin_system_clean.py"
            ],
            "forbidden_patterns": [
                "server_*.py",
                "main_*.py",
                "*_server.py",
                "launch_*.py"
            ],
            "allowed_exceptions": [
                "main_unified_server_clean.py",
                "test_*.py",
                "scripts/*.py"
            ]
        }
    
    def load_project_state(self) -> Dict:
        """Load current project state from JSON file"""
        try:
            if self.project_state_file.exists():
                with open(self.project_state_file, 'r') as f:
                    return json.load(f)
            else:
                return {"architectural_compliance": {"violations": 0}}
        except Exception as e:
            print(f"⚠️  Warning: Could not load project state: {e}")
            return {"architectural_compliance": {"violations": 0}}
    
    def validate_unified_files(self) -> Tuple[bool, List[str]]:
        """Validate that the 3 unified files exist and are the only server implementations"""
        violations = []
        
        # Check required unified files exist
        for required_file in self.architectural_rules["required_unified_files"]:
            file_path = self.project_root / required_file
            if not file_path.exists():
                violations.append(f"❌ Required unified file missing: {required_file}")
        
        # Check for competing implementations
        competing_servers = self.find_competing_implementations()
        if competing_servers:
            violations.append(f"❌ Found {len(competing_servers)} competing server implementations:")
            for server in competing_servers:
                violations.append(f"   - {server}")
        
        return len(violations) == 0, violations
    
    def find_competing_implementations(self) -> List[str]:
        """Find files that might be competing server implementations"""
        competing_files = []
        
        # Search for potential server files
        for pattern in self.architectural_rules["forbidden_patterns"]:
            for file_path in self.project_root.glob(pattern):
                # Skip if it's an allowed exception
                if not self.is_allowed_exception(file_path):
                    competing_files.append(str(file_path.relative_to(self.project_root)))
        
        return competing_files
    
    def is_allowed_exception(self, file_path: Path) -> bool:
        """Check if a file is an allowed exception to the architectural rules"""
        file_str = str(file_path.relative_to(self.project_root))
        
        # Check against allowed exceptions
        for exception in self.architectural_rules["allowed_exceptions"]:
            if file_path.match(exception) or file_str == exception:
                return True
        
        return False
    
    def validate_directory_structure(self) -> Tuple[bool, List[str]]:
        """Validate the overall directory structure"""
        violations = []
        
        # Check for required directories
        required_dirs = ["scripts", "docs", "config"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                violations.append(f"❌ Required directory missing: {dir_name}")
        
        # Check for project state file
        if not self.project_state_file.exists():
            violations.append("❌ project_state.json missing")
        
        return len(violations) == 0, violations
    
    def validate_merge_plan_compliance(self) -> Tuple[bool, List[str]]:
        """Validate compliance with the merge proposal plan"""
        violations = []
        
        # Check current audit phase
        current_phase = self.project_state.get("current_phase", "unknown")
        if current_phase == "unknown":
            violations.append("❌ Current audit phase not defined in project_state.json")
        
        # Check compliance score
        compliance_score = self.project_state.get("architectural_compliance", {}).get("compliance", 0)
        if compliance_score < 100:
            violations.append(f"❌ Architectural compliance below 100%: {compliance_score}%")
        
        return len(violations) == 0, violations
    
    def generate_compliance_report(self) -> Dict:
        """Generate a comprehensive compliance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "overall_compliance": True,
            "violations": [],
            "checks_performed": []
        }
        
        # Validate unified files
        unified_valid, unified_violations = self.validate_unified_files()
        report["checks_performed"].append("unified_files_validation")
        if not unified_valid:
            report["overall_compliance"] = False
            report["violations"].extend(unified_violations)
        
        # Validate directory structure
        structure_valid, structure_violations = self.validate_directory_structure()
        report["checks_performed"].append("directory_structure_validation")
        if not structure_valid:
            report["overall_compliance"] = False
            report["violations"].extend(structure_violations)
        
        # Validate merge plan compliance
        merge_valid, merge_violations = self.validate_merge_plan_compliance()
        report["checks_performed"].append("merge_plan_compliance")
        if not merge_valid:
            report["overall_compliance"] = False
            report["violations"].extend(merge_violations)
        
        return report
    
    def update_project_state(self, violations_count: int):
        """Update project state with validation results"""
        if self.project_state_file.exists():
            try:
                with open(self.project_state_file, 'r') as f:
                    state = json.load(f)
                
                # Update architectural compliance
                state["architectural_compliance"]["violations"] = violations_count
                state["architectural_compliance"]["last_validation"] = datetime.now().isoformat()
                
                with open(self.project_state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not update project state: {e}")
    
    def enforce_structure(self, auto_fix: bool = False) -> bool:
        """Main enforcement method"""
        print("🛡️  U.A.C.M.S. Architectural Structure Enforcer")
        print("=" * 50)
        
        # Generate compliance report
        report = self.generate_compliance_report()
        
        # Display results
        if report["overall_compliance"]:
            print("✅ ARCHITECTURAL COMPLIANCE: PASSED")
            print(f"   - Unified files: Present and validated")
            print(f"   - Directory structure: Compliant")
            print(f"   - Merge plan: Compliant")
            print(f"   - Violations: 0")
        else:
            print("❌ ARCHITECTURAL COMPLIANCE: FAILED")
            print(f"   - Violations found: {len(report['violations'])}")
            print("\n🚨 VIOLATIONS DETECTED:")
            for violation in report["violations"]:
                print(f"   {violation}")
        
        # Update project state
        self.update_project_state(len(report["violations"]))
        
        # Save detailed report
        report_file = self.project_root / "compliance_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Detailed report saved to: {report_file}")
        
        return report["overall_compliance"]

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="U.A.C.M.S. Architectural Structure Enforcer")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically fix violations")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    # Create enforcer
    enforcer = ArchitecturalEnforcer(args.project_root)
    
    # Run enforcement
    compliance = enforcer.enforce_structure(args.auto_fix)
    
    # Exit with appropriate code
    if compliance:
        if not args.quiet:
            print("\n🎯 ARCHITECTURAL ENFORCEMENT: SUCCESS")
        sys.exit(0)
    else:
        if not args.quiet:
            print("\n💥 ARCHITECTURAL ENFORCEMENT: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
