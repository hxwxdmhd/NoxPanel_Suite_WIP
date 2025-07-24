#!/usr/bin/env python3
"""
NoxPanel 8-Gate Audit System Launcher
====================================

Comprehensive audit system controller that manages the 8-gate progression
with progressive unlocking every 2 gates.

Usage:
    python scripts/audit_launcher.py --gate 1        # Run specific gate
    python scripts/audit_launcher.py --check-status  # Check current status
    python scripts/audit_launcher.py --run-sequence  # Run available gates in sequence
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

class AuditSystemController:
    """Controls the 8-gate audit system with progressive unlocking"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.docs_dir = self.project_root / "docs"
        self.scripts_dir = self.project_root / "scripts"
        
        # 8-gate system configuration
        self.gate_config = {
            1: {
                "name": "Core Containerization",
                "script": "audit_1.py",
                "focus": "Flask application containerization and foundation security",
                "unlock_trigger": None
            },
            2: {
                "name": "Basic Security Validation", 
                "script": "audit_2.py",
                "focus": "Authentication, authorization, and basic security hardening",
                "unlock_trigger": "Gates 1-2 Complete → Database systems, Authentication APIs, Basic endpoints"
            },
            3: {
                "name": "Performance Benchmarks",
                "script": "audit_3.py", 
                "focus": "Performance optimization and basic scalability",
                "unlock_trigger": None
            },
            4: {
                "name": "API Security Hardening",
                "script": "audit_4.py",
                "focus": "API security, rate limiting, and input validation", 
                "unlock_trigger": "Gates 3-4 Complete → Plugin system, Advanced APIs, Security middleware"
            },
            5: {
                "name": "Integration Testing",
                "script": "audit_5.py",
                "focus": "Component integration and workflow validation",
                "unlock_trigger": None
            },
            6: {
                "name": "Load Testing & Scalability",
                "script": "audit_6.py", 
                "focus": "High-load scenarios and scaling validation",
                "unlock_trigger": "Gates 5-6 Complete → Multi-container orchestration, Load balancing, Caching"
            },
            7: {
                "name": "Production Deployment",
                "script": "audit_7.py",
                "focus": "Production-ready deployment and configuration",
                "unlock_trigger": None
            },
            8: {
                "name": "Enterprise Security Audit",
                "script": "audit_8.py",
                "focus": "Enterprise-grade security and compliance validation",
                "unlock_trigger": "Gates 7-8 Complete → Voice processing, Streaming APIs, LLM integration, Enterprise features"
            }
        }
        
        # Progressive unlock schedule
        self.unlock_schedule = {
            2: ["database_advanced", "authentication_system", "basic_apis"],
            4: ["plugin_system", "advanced_apis", "security_middleware"],
            6: ["multi_container_orchestration", "load_balancing", "caching_system"], 
            8: ["voice_processing", "streaming_apis", "llm_integration", "enterprise_features"]
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log controller messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def get_gate_status(self, gate_number: int) -> Dict:
        """Get status of a specific gate"""
        results_file = self.docs_dir / f"audit_results_{gate_number}.json"
        
        if not results_file.exists():
            return {
                "gate": gate_number,
                "status": "NOT_RUN",
                "score": 0,
                "max_score": 100,
                "timestamp": None
            }
        
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                return {
                    "gate": gate_number,
                    "status": data.get("status", "UNKNOWN"),
                    "score": data.get("score", 0),
                    "max_score": data.get("max_score", 100), 
                    "timestamp": data.get("timestamp"),
                    "unlocked_modules": data.get("unlocked_modules", [])
                }
        except Exception as e:
            self.log(f"Error reading gate {gate_number} results: {e}", "ERROR")
            return {
                "gate": gate_number,
                "status": "ERROR",
                "score": 0,
                "max_score": 100,
                "timestamp": None
            }
    
    def check_system_status(self) -> Dict:
        """Check overall system status and unlock progress"""
        self.log("🔍 Checking 8-Gate Audit System Status...")
        
        status = {
            "total_gates": 8,
            "gates_completed": 0,
            "gates_passed": 0,
            "current_unlocks": [],
            "pending_unlocks": [],
            "gate_statuses": {},
            "next_available_gate": None
        }
        
        # Check each gate
        for gate_num in range(1, 9):
            gate_status = self.get_gate_status(gate_num)
            status["gate_statuses"][gate_num] = gate_status
            
            if gate_status["status"] not in ["NOT_RUN", "ERROR"]:
                status["gates_completed"] += 1
                
            if gate_status["status"] == "PASS":
                status["gates_passed"] += 1
                
                # Check for unlocks
                if gate_num in self.unlock_schedule:
                    unlocked_features = self.unlock_schedule[gate_num]
                    
                    # Verify previous gate also passed for even-numbered gates
                    if gate_num % 2 == 0:  # Even gate - check if previous gate also passed
                        prev_gate_status = self.get_gate_status(gate_num - 1)
                        if prev_gate_status["status"] == "PASS":
                            status["current_unlocks"].extend(unlocked_features)
                        else:
                            status["pending_unlocks"].extend(unlocked_features)
            
            # Find next available gate
            if status["next_available_gate"] is None and gate_status["status"] in ["NOT_RUN", "FAIL"]:
                status["next_available_gate"] = gate_num
        
        return status
    
    def run_gate_audit(self, gate_number: int) -> bool:
        """Run audit for specific gate"""
        if gate_number < 1 or gate_number > 8:
            self.log(f"Invalid gate number: {gate_number}", "ERROR")
            return False
        
        gate_info = self.gate_config[gate_number]
        script_path = self.scripts_dir / gate_info["script"]
        
        if not script_path.exists():
            self.log(f"Audit script not found: {script_path}", "ERROR")
            return False
        
        self.log(f"🚀 Running Gate {gate_number}: {gate_info['name']}")
        self.log(f"📋 Focus: {gate_info['focus']}")
        
        try:
            # Run the audit script
            result = subprocess.run([
                sys.executable, str(script_path),
                "--project-root", str(self.project_root)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                self.log(f"✅ Gate {gate_number} PASSED!", "SUCCESS")
                
                # Check for unlock triggers
                if gate_info["unlock_trigger"]:
                    self.log(f"🎉 {gate_info['unlock_trigger']}", "SUCCESS")
                
                return True
            else:
                self.log(f"❌ Gate {gate_number} FAILED", "ERROR")
                if result.stderr:
                    self.log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error running gate {gate_number}: {e}", "ERROR")
            return False
    
    def run_available_sequence(self) -> None:
        """Run all available gates in sequence"""
        self.log("🔄 Running available audit sequence...")
        
        status = self.check_system_status()
        next_gate = status["next_available_gate"]
        
        if next_gate is None:
            self.log("🎉 All gates completed!", "SUCCESS")
            return
        
        # Run gates sequentially starting from next available
        for gate_num in range(next_gate, 9):
            gate_status = self.get_gate_status(gate_num)
            
            if gate_status["status"] == "PASS":
                self.log(f"⏭️  Gate {gate_num} already passed, skipping")
                continue
            
            success = self.run_gate_audit(gate_num)
            
            if not success:
                self.log(f"🛑 Sequence stopped at Gate {gate_num} due to failure", "ERROR")
                break
            
            # Check if we've completed an unlock pair
            if gate_num % 2 == 0 and gate_num in self.unlock_schedule:
                prev_gate_status = self.get_gate_status(gate_num - 1)
                if prev_gate_status["status"] == "PASS":
                    unlocked = self.unlock_schedule[gate_num]
                    self.log(f"🔓 UNLOCKED: {', '.join(unlocked)}", "SUCCESS")
    
    def display_system_status(self) -> None:
        """Display comprehensive system status"""
        status = self.check_system_status()
        
        print("\n" + "=" * 70)
        print("🏛️  NOXPANEL 8-GATE AUDIT SYSTEM STATUS")
        print("=" * 70)
        
        print(f"📊 Progress: {status['gates_passed']}/{status['total_gates']} gates passed")
        print(f"🎯 Completion: {(status['gates_passed']/8)*100:.1f}%")
        
        if status["next_available_gate"]:
            print(f"▶️  Next Gate: {status['next_available_gate']} - {self.gate_config[status['next_available_gate']]['name']}")
        else:
            print("🏆 All gates completed!")
        
        print("\n📋 Gate Status:")
        for gate_num in range(1, 9):
            gate_status = status["gate_statuses"][gate_num]
            gate_info = self.gate_config[gate_num]
            
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌", 
                "CONDITIONAL_PASS": "⚠️",
                "NOT_RUN": "⏸️",
                "ERROR": "💥"
            }.get(gate_status["status"], "❓")
            
            print(f"  {status_icon} Gate {gate_num}: {gate_info['name']} - {gate_status['status']} ({gate_status['score']}/100)")
        
        if status["current_unlocks"]:
            print(f"\n🔓 Currently Unlocked: {', '.join(status['current_unlocks'])}")
        
        if status["pending_unlocks"]:
            print(f"⏳ Pending Unlocks: {', '.join(status['pending_unlocks'])}")
        
        print("=" * 70)

def main():
    """Main launcher execution"""
    parser = argparse.ArgumentParser(description="NoxPanel 8-Gate Audit System Launcher")
    parser.add_argument("--gate", type=int, help="Run specific gate (1-8)")
    parser.add_argument("--check-status", action="store_true", help="Check current system status")
    parser.add_argument("--run-sequence", action="store_true", help="Run available gates in sequence")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    controller = AuditSystemController(args.project_root)
    
    if args.check_status:
        controller.display_system_status()
    elif args.gate:
        success = controller.run_gate_audit(args.gate)
        sys.exit(0 if success else 1)
    elif args.run_sequence:
        controller.run_available_sequence()
    else:
        controller.display_system_status()
        print("\nUsage examples:")
        print("  python scripts/audit_launcher.py --gate 1        # Run Gate 1")
        print("  python scripts/audit_launcher.py --check-status  # Check status")
        print("  python scripts/audit_launcher.py --run-sequence  # Run sequence")

if __name__ == "__main__":
    main()
