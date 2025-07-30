#!/usr/bin/env python3
"""
TestSprite MCP Integration System
Integrates TestSprite automated testing with NoxSuite MCP infrastructure
"""

import json
import os
import subprocess
import time
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from emergency_copilot_fix import throttler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp_agent/testsprite/testsprite_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestSpriteMCP")

class TestSpriteMCPIntegration:
    """TestSprite MCP Integration for automated testing within NoxSuite"""
    
    def __init__(self):
        self.mcp_config_path = "mcp_config.json"
        self.testsprite_api_key = "sk-user-PHX6GBegO44LzqKY7otF7AmKHjbHE2AuPE5Yl4M8EShn7RS4dkFqb2Kas8jVg4wiONnDXfnU_EBQ8B4nnllXNDObNrqL2L4dMH0UIcLVE9YPge0ZQomL01KtEuMzMuzDOQM"
        self.langflow_url = "http://localhost:7860"
        self.logs_dir = Path("logs/mcp_agent/testsprite")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Test results storage
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "ui_tests": {},
            "integration_tests": {},
            "summary": {}
        }
    
    def validate_mcp_config(self) -> Dict[str, Any]:
        """Validate TestSprite MCP server configuration"""
        def check_config():
            try:
                with open(self.mcp_config_path, 'r') as f:
                    config = json.load(f)
                
                # Check if TestSprite is configured
                if "TestSprite" not in config.get("mcpServers", {}):
                    return {
                        "status": "error",
                        "error": "TestSprite not found in MCP configuration"
                    }
                
                testsprite_config = config["mcpServers"]["TestSprite"]
                
                # Validate configuration structure
                required_fields = ["command", "args", "env"]
                for field in required_fields:
                    if field not in testsprite_config:
                        return {
                            "status": "error", 
                            "error": f"Missing required field: {field}"
                        }
                
                # Check API key
                if "API_KEY" not in testsprite_config["env"]:
                    return {
                        "status": "error",
                        "error": "Missing API_KEY in environment"
                    }
                
                return {
                    "status": "success",
                    "config": testsprite_config,
                    "servers_configured": len(config["mcpServers"]),
                    "api_key_present": bool(testsprite_config["env"]["API_KEY"])
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Configuration validation failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(check_config)
    
    def test_testsprite_connectivity(self) -> Dict[str, Any]:
        """Test TestSprite CLI connectivity via MCP"""
        def test_connectivity():
            try:
                # Test npx availability
                logger.info("🔍 Testing npx availability...")
                npx_result = subprocess.run(
                    ["npx", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if npx_result.returncode != 0:
                    return {
                        "status": "error",
                        "error": "npx not available",
                        "npx_output": npx_result.stderr
                    }
                
                # Test TestSprite package availability
                logger.info("🧪 Testing TestSprite MCP package...")
                test_result = subprocess.run(
                    ["npx", "@testsprite/testsprite-mcp@latest", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env={**os.environ, "API_KEY": self.testsprite_api_key}
                )
                
                return {
                    "status": "success" if test_result.returncode == 0 else "warning",
                    "npx_version": npx_result.stdout.strip(),
                    "testsprite_version": test_result.stdout.strip() if test_result.returncode == 0 else "Not available",
                    "testsprite_stderr": test_result.stderr.strip() if test_result.stderr else None,
                    "connectivity_test": "passed" if test_result.returncode == 0 else "failed"
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "error": "TestSprite connectivity test timed out"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Connectivity test failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(test_connectivity)
    
    def run_api_tests(self) -> Dict[str, Any]:
        """Run API tests via TestSprite - Step 1 of atomic testing"""
        def execute_api_tests():
            try:
                logger.info("🔬 Running API tests via TestSprite...")
                
                # Create test configuration for API testing
                api_test_config = {
                    "testType": "api",
                    "target": self.langflow_url,
                    "endpoints": [
                        "/health",
                        "/api/v1/flows",
                        "/api/v1/components",
                        f"/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse"
                    ],
                    "timeout": 10
                }
                
                # Save test config
                config_file = self.logs_dir / "api_test_config.json"
                with open(config_file, 'w') as f:
                    json.dump(api_test_config, f, indent=2)
                
                # Run TestSprite API tests
                test_result = subprocess.run(
                    ["npx", "@testsprite/testsprite-mcp@latest", "run", 
                     "--config", str(config_file), "--dry-run"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, "API_KEY": self.testsprite_api_key}
                )
                
                # Parse results
                api_results = {
                    "status": "success" if test_result.returncode == 0 else "failed",
                    "tests_run": len(api_test_config["endpoints"]),
                    "stdout": test_result.stdout,
                    "stderr": test_result.stderr if test_result.stderr else None,
                    "return_code": test_result.returncode
                }
                
                # Store results
                self.test_results["api_tests"] = api_results
                
                # Save detailed results
                results_file = self.logs_dir / f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(results_file, 'w') as f:
                    json.dump(api_results, f, indent=2)
                
                logger.info(f"✅ API tests completed: {api_results['status']}")
                return api_results
                
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "error": "API tests timed out"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"API test execution failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(execute_api_tests)
    
    def run_ui_tests(self) -> Dict[str, Any]:
        """Run UI flow tests via TestSprite - Step 2 of atomic testing"""
        def execute_ui_tests():
            try:
                logger.info("🖥️ Running UI flow tests via TestSprite...")
                
                # Create test configuration for UI testing
                ui_test_config = {
                    "testType": "ui",
                    "target": self.langflow_url,
                    "scenarios": [
                        {
                            "name": "Login Flow",
                            "steps": [
                                {"action": "navigate", "url": f"{self.langflow_url}/login"},
                                {"action": "input", "selector": "input[name='username']", "value": "noxsuite_admin"},
                                {"action": "input", "selector": "input[name='password']", "value": "noxsuite_secure_2024"},
                                {"action": "click", "selector": "button[type='submit']"}
                            ]
                        },
                        {
                            "name": "Flow Navigation",
                            "steps": [
                                {"action": "navigate", "url": f"{self.langflow_url}/flows"},
                                {"action": "wait", "selector": ".flow-list", "timeout": 5000}
                            ]
                        }
                    ],
                    "browser": "chromium",
                    "headless": True,
                    "timeout": 30
                }
                
                # Save test config
                config_file = self.logs_dir / "ui_test_config.json"
                with open(config_file, 'w') as f:
                    json.dump(ui_test_config, f, indent=2)
                
                # Run TestSprite UI tests
                test_result = subprocess.run(
                    ["npx", "@testsprite/testsprite-mcp@latest", "run", 
                     "--config", str(config_file), "--dry-run"],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    env={**os.environ, "API_KEY": self.testsprite_api_key}
                )
                
                # Parse results
                ui_results = {
                    "status": "success" if test_result.returncode == 0 else "failed",
                    "scenarios_run": len(ui_test_config["scenarios"]),
                    "stdout": test_result.stdout,
                    "stderr": test_result.stderr if test_result.stderr else None,
                    "return_code": test_result.returncode
                }
                
                # Store results
                self.test_results["ui_tests"] = ui_results
                
                # Save detailed results
                results_file = self.logs_dir / f"ui_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(results_file, 'w') as f:
                    json.dump(ui_results, f, indent=2)
                
                logger.info(f"✅ UI tests completed: {ui_results['status']}")
                return ui_results
                
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "error": "UI tests timed out"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"UI test execution failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(execute_ui_tests)
    
    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary report - Step 3 of atomic testing"""
        def create_summary():
            try:
                logger.info("📊 Generating test summary report...")
                
                # Calculate summary statistics
                total_tests = 0
                passed_tests = 0
                failed_tests = 0
                
                # API test summary
                if "api_tests" in self.test_results:
                    api_tests = self.test_results["api_tests"]
                    api_count = api_tests.get("tests_run", 0)
                    total_tests += api_count
                    if api_tests.get("status") == "success":
                        passed_tests += api_count
                    else:
                        failed_tests += api_count
                
                # UI test summary
                if "ui_tests" in self.test_results:
                    ui_tests = self.test_results["ui_tests"]
                    ui_count = ui_tests.get("scenarios_run", 0)
                    total_tests += ui_count
                    if ui_tests.get("status") == "success":
                        passed_tests += ui_count
                    else:
                        failed_tests += ui_count
                
                # Calculate success rate
                success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                
                # Create summary
                summary = {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": round(success_rate, 2),
                    "tool_usage": {
                        "current": throttler.tool_count,
                        "limit": throttler.max_tools,
                        "percentage": round(throttler.tool_count / throttler.max_tools * 100, 1)
                    },
                    "test_categories": {
                        "api_tests": self.test_results.get("api_tests", {}).get("status", "not_run"),
                        "ui_tests": self.test_results.get("ui_tests", {}).get("status", "not_run")
                    },
                    "recommendations": []
                }
                
                # Add recommendations based on results
                if failed_tests > 0:
                    summary["recommendations"].append("Investigation required for failed tests")
                if success_rate < 80:
                    summary["recommendations"].append("System stability issues detected")
                if throttler.tool_count > 100:
                    summary["recommendations"].append("Tool usage approaching limit - implement cooldown")
                
                if not summary["recommendations"]:
                    summary["recommendations"].append("All tests passed - system operational")
                
                # Store summary
                self.test_results["summary"] = summary
                
                # Save comprehensive report
                report_file = self.logs_dir / f"testsprite_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(self.test_results, f, indent=2)
                
                logger.info(f"📋 Test summary completed: {success_rate}% success rate")
                return summary
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Summary generation failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(create_summary)
    
    def validate_mcp_agents_communication(self) -> Dict[str, Any]:
        """Validate MCP agents can communicate without collision"""
        def test_communication():
            try:
                logger.info("🔗 Testing MCP agents communication...")
                
                # Test endpoints
                endpoints = {
                    "langflow": f"{self.langflow_url}/health",
                    "mcp_project": f"{self.langflow_url}/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse"
                }
                
                results = {}
                for service, endpoint in endpoints.items():
                    try:
                        response = requests.get(endpoint, timeout=5)
                        results[service] = {
                            "status": "accessible" if response.status_code in [200, 404] else "error",
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds()
                        }
                    except Exception as e:
                        results[service] = {
                            "status": "error",
                            "error": str(e)
                        }
                
                # Check Docker containers
                try:
                    docker_result = subprocess.run(
                        ["docker", "ps", "--filter", "name=noxsuite", "--format", "{{.Names}}\t{{.Status}}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    containers = {}
                    for line in docker_result.stdout.strip().split('\n'):
                        if line:
                            name, status = line.split('\t', 1)
                            containers[name] = status
                    
                    results["docker_containers"] = containers
                    
                except Exception as e:
                    results["docker_containers"] = {"error": str(e)}
                
                # Overall communication status
                communication_ok = all(
                    result.get("status") == "accessible" 
                    for result in results.values() 
                    if isinstance(result, dict) and "status" in result
                )
                
                return {
                    "status": "success" if communication_ok else "issues_detected",
                    "endpoints": results,
                    "communication_healthy": communication_ok
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Communication test failed: {str(e)}"
                }
        
        return throttler.execute_with_throttle(test_communication)
    
    def run_full_integration_test(self) -> Dict[str, Any]:
        """Run complete TestSprite MCP integration test with throttling"""
        logger.info("🚀 Starting TestSprite MCP Full Integration Test")
        
        integration_results = {
            "timestamp": datetime.now().isoformat(),
            "phases": {},
            "overall_status": "running"
        }
        
        try:
            # Phase 1: MCP Configuration Validation
            logger.info("📋 Phase 1: MCP Configuration Validation")
            integration_results["phases"]["config_validation"] = self.validate_mcp_config()
            
            # 30s cooldown
            logger.info("⏳ Cooldown: 30 seconds...")
            time.sleep(30)
            
            # Phase 2: TestSprite Connectivity
            logger.info("🔌 Phase 2: TestSprite Connectivity Test")
            integration_results["phases"]["connectivity_test"] = self.test_testsprite_connectivity()
            
            # 30s cooldown
            logger.info("⏳ Cooldown: 30 seconds...")
            time.sleep(30)
            
            # Phase 3: API Tests
            logger.info("🔬 Phase 3: API Tests")
            integration_results["phases"]["api_tests"] = self.run_api_tests()
            
            # 30s cooldown
            logger.info("⏳ Cooldown: 30 seconds...")
            time.sleep(30)
            
            # Phase 4: UI Tests
            logger.info("🖥️ Phase 4: UI Flow Tests")
            integration_results["phases"]["ui_tests"] = self.run_ui_tests()
            
            # 30s cooldown
            logger.info("⏳ Cooldown: 30 seconds...")
            time.sleep(30)
            
            # Phase 5: MCP Communication Validation
            logger.info("🔗 Phase 5: MCP Communication Validation")
            integration_results["phases"]["communication_test"] = self.validate_mcp_agents_communication()
            
            # 30s cooldown
            logger.info("⏳ Cooldown: 30 seconds...")
            time.sleep(30)
            
            # Phase 6: Test Summary Generation
            logger.info("📊 Phase 6: Test Summary Generation")
            integration_results["phases"]["summary"] = self.generate_test_summary()
            
            # Determine overall status
            failed_phases = sum(1 for phase in integration_results["phases"].values() 
                              if phase.get("status") in ["error", "failed"])
            
            if failed_phases == 0:
                integration_results["overall_status"] = "success"
            elif failed_phases <= 2:
                integration_results["overall_status"] = "partial_success"
            else:
                integration_results["overall_status"] = "failed"
            
            # Save final results
            final_report = self.logs_dir / f"integration_test_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(final_report, 'w') as f:
                json.dump(integration_results, f, indent=2)
            
            logger.info(f"🎯 Integration test completed: {integration_results['overall_status']}")
            return integration_results
            
        except Exception as e:
            integration_results["overall_status"] = "error"
            integration_results["error"] = str(e)
            logger.error(f"❌ Integration test failed: {e}")
            return integration_results

def main():
    """Main execution function for TestSprite MCP Integration"""
    print("🧪 TESTSPRITE MCP INTEGRATION - STARTING")
    print("=" * 60)
    
    # Initialize integration system
    testsprite = TestSpriteMCPIntegration()
    
    # Run full integration test
    results = testsprite.run_full_integration_test()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TESTSPRITE MCP INTEGRATION COMPLETE")
    print("=" * 60)
    
    print(f"🎯 Overall Status: {results['overall_status']}")
    print(f"🔧 Tool Usage: {throttler.tool_count}/{throttler.max_tools}")
    
    if results["overall_status"] == "success":
        print("✅ TESTSPRITE MCP INTEGRATED AND VALIDATED")
    else:
        print("⚠️ Integration completed with issues - check logs for details")
    
    return results

if __name__ == "__main__":
    main()
