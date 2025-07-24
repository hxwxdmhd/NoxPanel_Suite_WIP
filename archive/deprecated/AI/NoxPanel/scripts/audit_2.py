#!/usr/bin/env python3
"""
NoxPanel Audit Gate 2 - Basic Security Validation
===============================================

This audit validates authentication, authorization, and basic security hardening.
Upon completion with Gates 1-2, unlocks: Database systems, Authentication APIs, Basic endpoints.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class AuditGate2:
    """Basic security validation audit system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.results = {
            "audit_gate": 2,
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "tests": [],
            "score": 0,
            "max_score": 100,
            "status": "PENDING",
            "unlocked_modules": [],
            "locked_modules": [],
            "recommendations": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log audit messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_test(self, test_name: str, test_func, points: int) -> bool:
        """Run a single test and record results"""
        self.log(f"Running: {test_name}")
        
        try:
            success, details = test_func()
            self.results["tests"].append({
                "name": test_name,
                "success": success,
                "points": points if success else 0,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
            
            if success:
                self.results["score"] += points
                self.log(f"PASS: {test_name} (+{points} points)", "SUCCESS")
            else:
                self.log(f"FAIL: {test_name} - {details}", "ERROR")
                
            return success
        except Exception as e:
            self.log(f"ERROR: {test_name} - {str(e)}", "ERROR")
            self.results["tests"].append({
                "name": test_name,
                "success": False,
                "points": 0,
                "details": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def test_authentication_system(self) -> Tuple[bool, str]:
        """Test 1: Verify authentication system exists"""
        auth_file = self.project_root / "noxcore" / "auth.py"
        
        if not auth_file.exists():
            return False, "Authentication module not found"
            
        content = auth_file.read_text()
        required_functions = ["auth_required", "create_user", "verify_user"]
        missing = [func for func in required_functions if func not in content]
        
        if missing:
            return False, f"Missing auth functions: {', '.join(missing)}"
            
        return True, "Authentication system validated"
    
    def test_session_security(self) -> Tuple[bool, str]:
        """Test 2: Verify session security configuration"""
        app_file = self.project_root / "webpanel" / "app_v5.py"
        
        if not app_file.exists():
            return False, "Main application file not found"
            
        try:
            with open(app_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return False, f"Error reading app file: {str(e)}"
        
        security_configs = [
            "SESSION_COOKIE_SECURE",
            "SESSION_COOKIE_HTTPONLY", 
            "SESSION_COOKIE_SAMESITE"
        ]
        
        missing = [config for config in security_configs if config not in content]
        
        if missing:
            return False, f"Missing session security: {', '.join(missing)}"
            
        return True, "Session security properly configured"
    
    def test_security_headers(self) -> Tuple[bool, str]:
        """Test 3: Verify security headers implementation"""
        security_file = self.project_root / "noxcore" / "security_headers.py"
        
        if not security_file.exists():
            return False, "Security headers module not found"
            
        try:
            with open(security_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return False, f"Error reading security headers file: {str(e)}"
        
        if "X-Frame-Options" not in content or "X-Content-Type-Options" not in content:
            return False, "Essential security headers not implemented"
            
        return True, "Security headers properly implemented"
    
    def test_input_validation(self) -> Tuple[bool, str]:
        """Test 4: Verify input validation exists"""
        # Check for validation in route handlers
        webpanel_dir = self.project_root / "webpanel"
        validation_found = False
        
        try:
            for py_file in webpanel_dir.glob("*.py"):
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "request.json" in content or "request.form" in content:
                        if "validate" in content.lower() or "sanitize" in content.lower():
                            validation_found = True
                            break
        except Exception as e:
            return False, f"Error checking validation patterns: {str(e)}"
        
        if not validation_found:
            return False, "No input validation patterns found"
            
        return True, "Input validation patterns detected"
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete Audit Gate 2"""
        self.log("=" * 60)
        self.log("NOXPANEL AUDIT GATE 2 - BASIC SECURITY VALIDATION")
        self.log("=" * 60)
        
        # Define all tests with point values
        tests = [
            ("Authentication System", self.test_authentication_system, 40),
            ("Session Security", self.test_session_security, 35),
            ("Security Headers", self.test_security_headers, 15),
            ("Input Validation", self.test_input_validation, 10)
        ]
        
        # Run all tests
        for test_name, test_func, points in tests:
            self.run_test(test_name, test_func, points)
        
        # Determine status
        if self.results["score"] == 100:
            self.results["status"] = "PASS"
            # Check if Gates 1-2 are complete for unlock
            self.results["unlocked_modules"] = ["database_advanced", "authentication_system", "basic_apis"]
        elif self.results["score"] >= 80:
            self.results["status"] = "CONDITIONAL_PASS"
        else:
            self.results["status"] = "FAIL"
        
        self.log("=" * 60)
        self.log(f"AUDIT GATE 2 COMPLETE")
        self.log(f"Score: {self.results['score']}/{self.results['max_score']}")
        self.log(f"Status: {self.results['status']}")
        self.log("=" * 60)
        
        return self.results

def main():
    """Main audit execution"""
    auditor = AuditGate2()
    results = auditor.run_full_audit()
    
    # Save results
    output_path = Path("docs/audit_results_2.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to: {output_path}")
    
    # Exit with appropriate code
    if results["status"] == "PASS":
        print("\nAudit Gate 2 PASSED!")
        sys.exit(0)
    else:
        print(f"\nAudit Gate 2 {results['status']}. Address issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
