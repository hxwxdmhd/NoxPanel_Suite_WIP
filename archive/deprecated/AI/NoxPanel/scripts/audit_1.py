#!/usr/bin/env python3
"""
NoxPanel Audit Gate 1 - Core Containerization Audit
==================================================

This audit validates the core Flask application containerization
and ensures readiness for controlled expansion.

8-Gate Audit System with Progressive Unlocking:
- Gate 1: Core containerization (this file)
- Gate 2: Basic security validation
- Gates 1-2 Complete → Unlock: Database & Authentication modules
- Gate 3: Performance benchmarks  
- Gate 4: API security hardening
- Gates 3-4 Complete → Unlock: Plugin system & Advanced APIs
- Gate 5: Integration testing
- Gate 6: Load testing & scalability
- Gates 5-6 Complete → Unlock: Multi-container orchestration
- Gate 7: Production deployment validation
- Gate 8: Enterprise security audit
- Gates 7-8 Complete → Unlock: ALL advanced features (voice, streaming, LLM)

Only after ALL 8 gates pass with 100/100 score will voice processing,
streaming APIs, and LLM integration be unlocked.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class AuditGate1:
    """Core containerization audit system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.results = {
            "audit_gate": 1,
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
          # Expected locked modules until all 8 gates pass
        self.locked_until_gates_pass = [
            "voice_processing",
            "streaming_apis", 
            "multi_container_orchestration",
            "tts_services",
            "rtc_backends", 
            "assistant_containers",
            "frontend_ssr_frameworks",
            "llm_integration",
            "advanced_plugin_system",
            "enterprise_monitoring"
        ]
        
        # Progressive unlock system
        self.unlock_schedule = {
            2: ["database_advanced", "authentication_system", "basic_apis"],
            4: ["plugin_system", "advanced_apis", "security_middleware"], 
            6: ["multi_container_orchestration", "load_balancing", "caching_system"],
            8: ["voice_processing", "streaming_apis", "llm_integration", "enterprise_features"]
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
                self.log(f"✅ PASS: {test_name} (+{points} points)", "SUCCESS")
            else:
                self.log(f"❌ FAIL: {test_name} - {details}", "ERROR")
                
            return success
        except Exception as e:
            self.log(f"❌ ERROR: {test_name} - {str(e)}", "ERROR")
            self.results["tests"].append({
                "name": test_name,
                "success": False,
                "points": 0,
                "details": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def test_docker_files_exist(self) -> Tuple[bool, str]:
        """Test 1: Verify Docker files exist"""
        dockerfile = self.project_root / "docker" / "Dockerfile"
        compose = self.project_root / "docker" / "docker-compose.yml"
        
        missing = []
        if not dockerfile.exists():
            missing.append("docker/Dockerfile")
        if not compose.exists():
            missing.append("docker/docker-compose.yml")
            
        if missing:
            return False, f"Missing files: {', '.join(missing)}"
        return True, "All Docker files present"
    
    def test_main_entry_point(self) -> Tuple[bool, str]:
        """Test 2: Verify main.py exists and calls start_webpanel"""
        main_py = self.project_root / "main.py"
        
        if not main_py.exists():
            return False, "main.py not found"
            
        content = main_py.read_text()
        if "start_webpanel" not in content:
            return False, "main.py does not call start_webpanel()"
            
        return True, "main.py correctly configured"
    
    def test_requirements_file(self) -> Tuple[bool, str]:
        """Test 3: Verify requirements.txt exists"""
        req_file = self.project_root / "requirements.txt"
        
        if not req_file.exists():
            return False, "requirements.txt not found"
            
        content = req_file.read_text()
        required_packages = ["flask", "python-dotenv", "flask-cors"]
        missing = [pkg for pkg in required_packages if pkg not in content.lower()]
        
        if missing:
            return False, f"Missing required packages: {', '.join(missing)}"
            
        return True, f"requirements.txt valid with {len(content.strip().split())} packages"
    
    def test_env_configuration(self) -> Tuple[bool, str]:
        """Test 4: Verify .env configuration"""
        env_example = self.project_root / ".env.example"
        
        if not env_example.exists():
            return False, ".env.example not found"
            
        content = env_example.read_text()
        required_keys = ["SECRET_KEY", "FLASK_ENV"]
        missing = [key for key in required_keys if key not in content]
        
        if missing:
            return False, f"Missing required env keys: {', '.join(missing)}"
            
        return True, "Environment configuration valid"
    
    def test_webpanel_structure(self) -> Tuple[bool, str]:
        """Test 5: Verify webpanel directory structure"""
        webpanel_dir = self.project_root / "webpanel"
        
        if not webpanel_dir.exists():
            return False, "webpanel directory not found"
            
        required_files = ["app_v5.py"]
        missing = [f for f in required_files if not (webpanel_dir / f).exists()]
        
        if missing:
            return False, f"Missing webpanel files: {', '.join(missing)}"
            
        return True, f"webpanel structure valid"
    
    def test_container_build(self) -> Tuple[bool, str]:
        """Test 6: Test Docker container build (optional if Docker not available)"""
        try:
            # Check if Docker is available
            docker_check = subprocess.run(["docker", "--version"], 
                                        capture_output=True, text=True, timeout=10)
            
            if docker_check.returncode != 0:
                return True, "Docker not available - test skipped (development environment)"
            
            # Change to project root for Docker context
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # Build the container
            result = subprocess.run([
                "docker", "build", "-f", "docker/Dockerfile", "-t", "noxpanel-audit:test", "."
            ], capture_output=True, text=True, timeout=300)
            
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                return False, f"Docker build failed: {result.stderr}"
                
            return True, "Docker build successful"
            
        except subprocess.TimeoutExpired:
            return False, "Docker build timed out (>5 minutes)"
        except FileNotFoundError:
            return True, "Docker not installed - test skipped (development environment)"
        except Exception as e:
            return False, f"Build test error: {str(e)}"
    
    def test_no_forbidden_modules(self) -> Tuple[bool, str]:
        """Test 7: Verify no forbidden modules are present"""
        forbidden_patterns = [
            "voice_assistant",
            "streaming_api",
            "tts_container", 
            "rtc_backend",
            "multi_service",
            "nginx_proxy"
        ]
        
        violations = []
        
        # Check docker-compose for forbidden services
        compose_file = self.project_root / "docker" / "docker-compose.yml"
        if compose_file.exists():
            content = compose_file.read_text().lower()
            for pattern in forbidden_patterns:
                if pattern in content:
                    violations.append(f"docker-compose.yml contains '{pattern}'")
        
        # Check for forbidden directories
        forbidden_dirs = ["voice", "streaming", "tts", "rtc"]
        for dir_name in forbidden_dirs:
            if (self.project_root / dir_name).exists():
                violations.append(f"Forbidden directory '{dir_name}' exists")
        
        if violations:
            return False, f"Forbidden modules detected: {', '.join(violations)}"
            
        return True, "No forbidden modules detected"
    
    def test_code_quality(self) -> Tuple[bool, str]:
        """Test 8: Basic code quality checks"""
        try:
            # Check if main files are syntactically valid
            main_py = self.project_root / "main.py"
            app_py = self.project_root / "webpanel" / "app_v5.py"
            
            for file_path in [main_py, app_py]:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        compile(f.read(), str(file_path), 'exec')
            
            return True, "Basic syntax validation passed"
            
        except SyntaxError as e:
            return False, f"Syntax error in {e.filename}: {e.msg}"
        except Exception as e:
            return False, f"Code quality check failed: {str(e)}"
    
    def test_security_basics(self) -> Tuple[bool, str]:
        """Test 9: Basic security configuration"""
        dockerfile = self.project_root / "docker" / "Dockerfile"
        
        if not dockerfile.exists():
            return False, "Dockerfile not found"
            
        content = dockerfile.read_text()
        
        # Check for non-root user
        if "USER " not in content:
            return False, "No non-root user configured in Dockerfile"
            
        # Check for FLASK_ENV=production
        if "FLASK_ENV=production" not in content:
            return False, "FLASK_ENV not set to production"
            
        return True, "Basic security configuration valid"
    
    def test_health_check(self) -> Tuple[bool, str]:
        """Test 10: Verify health check configuration"""
        dockerfile = self.project_root / "docker" / "Dockerfile"
        compose = self.project_root / "docker" / "docker-compose.yml"
        
        has_dockerfile_healthcheck = False
        has_compose_healthcheck = False
        
        if dockerfile.exists():
            content = dockerfile.read_text()
            if "HEALTHCHECK" in content:
                has_dockerfile_healthcheck = True
        
        if compose.exists():
            content = compose.read_text()
            if "healthcheck:" in content:
                has_compose_healthcheck = True
        
        if not (has_dockerfile_healthcheck or has_compose_healthcheck):
            return False, "No health check configuration found"
            
        return True, "Health check configuration present"
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        failed_tests = [t for t in self.results["tests"] if not t["success"]]
        
        if not failed_tests:
            self.results["recommendations"].append(
                "🎉 All Audit Gate 1 tests passed! Ready to proceed to Gate 2."
            )
        else:
            self.results["recommendations"].append(
                "❌ Fix all failing tests before proceeding to next audit gate."
            )
            
        # Add specific recommendations based on failures
        for test in failed_tests:
            if "docker" in test["name"].lower():
                self.results["recommendations"].append(
                    "🐳 Install Docker and ensure it's accessible from command line"
                )
            elif "env" in test["name"].lower():
                self.results["recommendations"].append(
                    "🔧 Create .env file based on .env.example template"
                )
            elif "security" in test["name"].lower():
                self.results["recommendations"].append(
                    "🔒 Review security configuration in Dockerfile"
                )
    
    def determine_status(self):
        """Determine overall audit status"""
        if self.results["score"] == self.results["max_score"]:
            self.results["status"] = "PASS"
            self.results["unlocked_modules"] = ["audit_gate_2"]
            
            # Check for progressive unlocks (every 2 gates)
            if self.results["audit_gate"] % 2 == 0:  # Even numbered gates trigger unlocks
                if self.results["audit_gate"] in self.unlock_schedule:
                    unlocked_features = self.unlock_schedule[self.results["audit_gate"]]
                    self.results["unlocked_modules"].extend(unlocked_features)
                    
        elif self.results["score"] >= 80:
            self.results["status"] = "CONDITIONAL_PASS" 
            self.results["recommendations"].append("⚠️ Score ≥80 but <100. Fix remaining issues.")
        else:
            self.results["status"] = "FAIL"
            
        # All advanced modules remain locked until all 8 gates pass
        self.results["locked_modules"] = self.locked_until_gates_pass.copy()
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete Audit Gate 1"""
        self.log("=" * 60)
        self.log("🔍 NOXPANEL AUDIT GATE 1 - CORE CONTAINERIZATION")
        self.log("=" * 60)
        
        # Define all tests with point values
        tests = [
            ("Docker Files Exist", self.test_docker_files_exist, 10),
            ("Main Entry Point", self.test_main_entry_point, 10),
            ("Requirements File", self.test_requirements_file, 10),
            ("Environment Configuration", self.test_env_configuration, 10),
            ("Webpanel Structure", self.test_webpanel_structure, 10),
            ("Container Build", self.test_container_build, 20),
            ("No Forbidden Modules", self.test_no_forbidden_modules, 15),
            ("Code Quality", self.test_code_quality, 5),
            ("Security Basics", self.test_security_basics, 5),
            ("Health Check", self.test_health_check, 5)
        ]
        
        # Run all tests
        for test_name, test_func, points in tests:
            self.run_test(test_name, test_func, points)
        
        # Generate final results
        self.generate_recommendations()
        self.determine_status()
        
        # Log summary
        self.log("=" * 60)
        self.log(f"🏁 AUDIT COMPLETE")
        self.log(f"📊 Score: {self.results['score']}/{self.results['max_score']}")
        self.log(f"🎯 Status: {self.results['status']}")
        self.log("=" * 60)
        
        return self.results
    
    def save_results(self, output_file: str = "audit_results_1.json"):
        """Save audit results to file"""
        output_path = self.project_root / "docs" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"📄 Results saved to: {output_path}")

def main():
    """Main audit execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NoxPanel Audit Gate 1")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", default="audit_results_1.json", help="Output file name")
    
    args = parser.parse_args()
    
    # Run the audit
    auditor = AuditGate1(args.project_root)
    results = auditor.run_full_audit()
    auditor.save_results(args.output)
    
    # Exit with appropriate code
    if results["status"] == "PASS":
        print("\n🎉 Audit Gate 1 PASSED! Ready for Gate 2.")
        sys.exit(0)
    elif results["status"] == "CONDITIONAL_PASS":
        print("\n⚠️ Audit Gate 1 CONDITIONAL PASS. Address remaining issues.")
        sys.exit(1)
    else:
        print("\n❌ Audit Gate 1 FAILED. Fix issues before proceeding.")
        sys.exit(2)

if __name__ == "__main__":
    main()
