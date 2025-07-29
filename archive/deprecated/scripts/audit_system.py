#!/usr/bin/env python3
"""
U.A.C.M.S. - Progressive Audit System
=====================================

This script implements the Progressive Audit Gate System (PAGS) to ensure
phased development and prevent feature creep.

Author: U.A.C.M.S. System
Version: 1.0
"""

import os
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ProgressiveAuditSystem:
    """Implements progressive audit gates for phased development"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.project_state_file = self.project_root / "project_state.json"
        
        # Load project state
        self.project_state = self.load_project_state()
        
        # Define audit phases
        self.audit_phases = {
            "audit_1": {
                "name": "Architectural Consolidation",
                "requirements": [
                    "3_unified_files_created",
                    "server_operational",
                    "database_initialized",
                    "no_competing_implementations",
                    "basic_functionality_verified"
                ],
                "unlocks": [
                    "dockerfile_creation",
                    "docker_compose_setup",
                    "basic_plugin_system"
                ],
                "script": "audit_1.py"
            },
            "audit_2": {
                "name": "Plugin Architecture & API Gateway",
                "requirements": [
                    "plugin_architecture_validated",
                    "api_endpoints_documented",
                    "security_basic_validation",
                    "performance_benchmarks_basic"
                ],
                "unlocks": [
                    "advanced_plugin_system",
                    "api_gateway_features",
                    "middleware_development"
                ],
                "script": "audit_2.py"
            },
            "audit_3": {
                "name": "CI/CD & Production Configuration",
                "requirements": [
                    "test_coverage_80_percent",
                    "ci_cd_pipeline_setup",
                    "production_configuration",
                    "security_audit_passed"
                ],
                "unlocks": [
                    "production_deployment",
                    "monitoring_system",
                    "logging_aggregation"
                ],
                "script": "audit_3.py"
            },
            "audit_4": {
                "name": "Production Deployment & Advanced Features",
                "requirements": [
                    "production_deployment_verified",
                    "monitoring_system_active",
                    "load_testing_passed",
                    "security_hardening_complete"
                ],
                "unlocks": [
                    "tts_voice_features",
                    "advanced_rtc_features",
                    "real_time_communication"
                ],
                "script": "audit_4.py"
            },
            "audit_5": {
                "name": "Enterprise & LLM Integration",
                "requirements": [
                    "enterprise_features_validated",
                    "scaling_architecture_proven",
                    "advanced_monitoring_active",
                    "analytics_system_operational"
                ],
                "unlocks": [
                    "llm_integration",
                    "advanced_analytics",
                    "enterprise_dashboard",
                    "ai_assistant_memory"
                ],
                "script": "audit_5.py"
            }
        }
    
    def load_project_state(self) -> Dict:
        """Load current project state from JSON file"""
        try:
            if self.project_state_file.exists():
                with open(self.project_state_file, 'r') as f:
                    return json.load(f)
            else:
                return self.create_default_state()
        except Exception as e:
            print(f"⚠️  Warning: Could not load project state: {e}")
            return self.create_default_state()
    
    def create_default_state(self) -> Dict:
        """Create default project state"""
        return {
            "current_phase": "audit_1_preparation",
            "audit_status": {},
            "architectural_compliance": {"violations": 0},
            "allowed_operations": [],
            "blocked_operations": ["all_advanced_features"]
        }
    
    def get_current_phase(self) -> str:
        """Get the current audit phase"""
        return self.project_state.get("current_phase", "audit_1_preparation")
    
    def get_audit_status(self, phase: str) -> Dict:
        """Get audit status for a specific phase"""
        return self.project_state.get("audit_status", {}).get(phase, {"status": "NOT_STARTED"})
    
    def can_proceed_to_phase(self, target_phase: str) -> Tuple[bool, List[str]]:
        """Check if project can proceed to target phase"""
        violations = []
        
        # Get phase requirements
        if target_phase not in self.audit_phases:
            violations.append(f"❌ Unknown audit phase: {target_phase}")
            return False, violations
        
        phase_config = self.audit_phases[target_phase]
        
        # Check if previous phases are completed
        phase_order = list(self.audit_phases.keys())
        current_index = phase_order.index(target_phase)
        
        for i in range(current_index):
            previous_phase = phase_order[i]
            status = self.get_audit_status(previous_phase)
            if status.get("status") != "PASSED":
                violations.append(f"❌ Previous phase {previous_phase} not completed")
        
        return len(violations) == 0, violations
    
    def run_audit_phase(self, phase: str) -> Dict:
        """Run audit for a specific phase"""
        print(f"🔍 Running audit for phase: {phase}")
        
        if phase not in self.audit_phases:
            return {
                "status": "ERROR",
                "message": f"Unknown audit phase: {phase}",
                "violations": [f"Phase {phase} not defined"]
            }
        
        phase_config = self.audit_phases[phase]
        
        # Check if can proceed to this phase
        can_proceed, violations = self.can_proceed_to_phase(phase)
        if not can_proceed:
            return {
                "status": "BLOCKED",
                "message": f"Cannot proceed to {phase}",
                "violations": violations
            }
        
        # Run specific audit script
        audit_script = self.project_root / "scripts" / phase_config["script"]
        if audit_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(audit_script)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    return {
                        "status": "PASSED",
                        "message": f"Audit {phase} completed successfully",
                        "output": result.stdout,
                        "violations": []
                    }
                else:
                    return {
                        "status": "FAILED",
                        "message": f"Audit {phase} failed",
                        "output": result.stderr,
                        "violations": [f"Audit script returned non-zero exit code: {result.returncode}"]
                    }
            except Exception as e:
                return {
                    "status": "ERROR",
                    "message": f"Error running audit script: {e}",
                    "violations": [str(e)]
                }
        else:
            # Run basic validation if no specific script exists
            return self.run_basic_validation(phase)
    
    def run_basic_validation(self, phase: str) -> Dict:
        """Run basic validation for a phase"""
        phase_config = self.audit_phases[phase]
        violations = []
        
        # Check requirements based on phase
        if phase == "audit_1":
            # Check for unified files
            required_files = [
                "main_unified_server_clean.py",
                "models_unified_clean.py",
                "unified_plugin_system_clean.py"
            ]
            
            for file_name in required_files:
                file_path = self.project_root / file_name
                if not file_path.exists():
                    violations.append(f"❌ Required file missing: {file_name}")
            
            # Check for competing implementations
            competing_files = self.find_competing_implementations()
            if competing_files:
                violations.append(f"❌ Found competing implementations: {', '.join(competing_files)}")
        
        # Determine status
        if len(violations) == 0:
            return {
                "status": "PASSED",
                "message": f"Basic validation for {phase} passed",
                "violations": []
            }
        else:
            return {
                "status": "FAILED",
                "message": f"Basic validation for {phase} failed",
                "violations": violations
            }
    
    def find_competing_implementations(self) -> List[str]:
        """Find competing server implementations"""
        competing_files = []
        
        # Search patterns for server files
        patterns = ["*server*.py", "main_*.py", "launch_*.py"]
        allowed_files = [
            "main_unified_server_clean.py",
            "test_server_startup.py"
        ]
        
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.name not in allowed_files:
                    competing_files.append(file_path.name)
        
        return competing_files
    
    def update_audit_status(self, phase: str, result: Dict):
        """Update audit status in project state"""
        if not self.project_state_file.exists():
            return
        
        try:
            with open(self.project_state_file, 'r') as f:
                state = json.load(f)
            
            # Update audit status
            if "audit_status" not in state:
                state["audit_status"] = {}
            
            state["audit_status"][phase] = {
                "status": result["status"],
                "message": result["message"],
                "timestamp": datetime.now().isoformat(),
                "violations": result.get("violations", [])
            }
            
            # Update current phase if audit passed
            if result["status"] == "PASSED":
                # Find next phase
                phase_order = list(self.audit_phases.keys())
                current_index = phase_order.index(phase)
                if current_index < len(phase_order) - 1:
                    next_phase = phase_order[current_index + 1]
                    state["current_phase"] = f"{next_phase}_preparation"
                else:
                    state["current_phase"] = "all_audits_completed"
                
                # Update unlocked features
                unlocked_features = self.audit_phases[phase]["unlocks"]
                if "unlocked_features" not in state:
                    state["unlocked_features"] = {}
                
                for feature in unlocked_features:
                    state["unlocked_features"][feature] = "AVAILABLE"
            
            with open(self.project_state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Warning: Could not update audit status: {e}")
    
    def get_audit_status_report(self) -> Dict:
        """Generate comprehensive audit status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_phase": self.get_current_phase(),
            "audit_phases": {},
            "overall_status": "IN_PROGRESS"
        }
        
        all_passed = True
        for phase_name, phase_config in self.audit_phases.items():
            status = self.get_audit_status(phase_name)
            
            report["audit_phases"][phase_name] = {
                "name": phase_config["name"],
                "status": status.get("status", "NOT_STARTED"),
                "requirements": phase_config["requirements"],
                "unlocks": phase_config["unlocks"],
                "violations": status.get("violations", [])
            }
            
            if status.get("status") != "PASSED":
                all_passed = False
        
        if all_passed:
            report["overall_status"] = "ALL_AUDITS_COMPLETED"
        
        return report
    
    def display_audit_status(self):
        """Display current audit status"""
        print("📋 U.A.C.M.S. Progressive Audit Status")
        print("=" * 50)
        
        report = self.get_audit_status_report()
        
        print(f"Current Phase: {report['current_phase']}")
        print(f"Overall Status: {report['overall_status']}")
        print()
        
        for phase_name, phase_info in report["audit_phases"].items():
            status = phase_info["status"]
            if status == "PASSED":
                status_icon = "✅"
            elif status == "FAILED":
                status_icon = "❌"
            elif status == "IN_PROGRESS":
                status_icon = "🔄"
            else:
                status_icon = "⏳"
            
            print(f"{status_icon} {phase_name}: {phase_info['name']}")
            print(f"   Status: {status}")
            
            if phase_info["violations"]:
                print(f"   Violations: {len(phase_info['violations'])}")
                for violation in phase_info["violations"]:
                    print(f"     - {violation}")
            
            print(f"   Unlocks: {', '.join(phase_info['unlocks'])}")
            print()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="U.A.C.M.S. Progressive Audit System")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--run-audit", help="Run audit for specific phase")
    parser.add_argument("--status", action="store_true", help="Show audit status")
    parser.add_argument("--phase", help="Target phase for operations")
    
    args = parser.parse_args()
    
    # Create audit system
    audit_system = ProgressiveAuditSystem(args.project_root)
    
    if args.status:
        audit_system.display_audit_status()
    elif args.run_audit:
        result = audit_system.run_audit_phase(args.run_audit)
        audit_system.update_audit_status(args.run_audit, result)
        
        print(f"Audit Result: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result.get("violations"):
            print("Violations:")
            for violation in result["violations"]:
                print(f"  - {violation}")
        
        sys.exit(0 if result["status"] == "PASSED" else 1)
    else:
        audit_system.display_audit_status()

if __name__ == "__main__":
    main()
