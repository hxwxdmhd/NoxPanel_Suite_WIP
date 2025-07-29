#!/usr/bin/env python3
"""
NoxSuite MCP Emergency System - Handles both CVE and 128 Tools Limit
Specifically designed for your Langflow MCP configuration
"""
import json
import time
import subprocess
import requests
import logging
from typing import Dict, Any, List
from datetime import datetime
from emergency_copilot_fix import throttler

class MCPEmergencySystem:
    def __init__(self, mcp_config_path: str = None):
        self.mcp_config = {}
        self.langflow_url = "http://localhost:7860"
        self.project_id = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MCPEmergency")
        
        # Load MCP configuration if provided
        if mcp_config_path:
            self.load_mcp_config(mcp_config_path)
    
    def load_mcp_config(self, config_path: str):
        """Load MCP configuration from file"""
        try:
            with open(config_path, 'r') as f:
                self.mcp_config = json.load(f)
            
            # Extract project ID from URL if present
            for server_name, config in self.mcp_config.get("mcpServers", {}).items():
                if "args" in config:
                    for arg in config["args"]:
                        if "project/" in arg and "/sse" in arg:
                            # Extract project ID from URL
                            parts = arg.split("project/")[1].split("/")
                            self.project_id = parts[0]
                            self.logger.info(f"🆔 Found project ID: {self.project_id}")
                            
        except Exception as e:
            self.logger.error(f"❌ Failed to load MCP config: {e}")
    
    def check_langflow_health(self) -> Dict[str, Any]:
        """Check Langflow health with throttling"""
        def health_check():
            try:
                response = requests.get(f"{self.langflow_url}/health", timeout=5)
                return {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        return throttler.execute_with_throttle(health_check)
    
    def check_mcp_endpoint(self) -> Dict[str, Any]:
        """Check MCP endpoint connectivity"""
        def mcp_check():
            if not self.project_id:
                return {"status": "error", "error": "No project ID found in MCP config"}
            
            try:
                # Test the MCP API endpoint
                mcp_url = f"{self.langflow_url}/api/v1/mcp/project/{self.project_id}/sse"
                response = requests.get(mcp_url, timeout=5)
                
                return {
                    "status": "accessible" if response.status_code in [200, 404] else "error",
                    "status_code": response.status_code,
                    "endpoint": mcp_url
                }
            except Exception as e:
                return {
                    "status": "error", 
                    "error": str(e),
                    "endpoint": f"{self.langflow_url}/api/v1/mcp/project/{self.project_id}/sse"
                }
        
        return throttler.execute_with_throttle(mcp_check)
    
    def emergency_container_update(self) -> bool:
        """Update Langflow container to patch CVE vulnerabilities"""
        def update_container():
            try:
                self.logger.info("🔒 Starting emergency container update...")
                
                # Check current container
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=noxsuite-langflow", "--format", "{{.Names}}"],
                    capture_output=True, text=True
                )
                
                if "noxsuite-langflow" in result.stdout:
                    # Stop container
                    self.logger.info("🛑 Stopping vulnerable container...")
                    subprocess.run(["docker", "stop", "noxsuite-langflow"], check=True)
                    
                    # Remove old container
                    subprocess.run(["docker", "rm", "noxsuite-langflow"], check=True)
                
                # Pull latest secure image
                self.logger.info("⬇️ Pulling latest secure image...")
                subprocess.run(["docker", "pull", "langflowai/langflow:latest"], check=True)
                
                # Restart with docker-compose
                self.logger.info("🔄 Starting updated container...")
                subprocess.run(["docker-compose", "-f", "docker-compose.langflow.yml", "up", "-d"], check=True)
                
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Container update failed: {e}")
                return False
        
        return throttler.execute_with_throttle(update_container)
    
    def validate_mcp_connection(self) -> Dict[str, Any]:
        """Comprehensive MCP connection validation"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "langflow_health": {},
            "mcp_endpoint": {},
            "overall_status": "unknown"
        }
        
        # Check Langflow health
        self.logger.info("🏥 Checking Langflow health...")
        results["langflow_health"] = self.check_langflow_health()
        
        # Wait to respect tool limits
        time.sleep(2)
        
        # Check MCP endpoint
        self.logger.info("🔗 Checking MCP endpoint...")
        results["mcp_endpoint"] = self.check_mcp_endpoint()
        
        # Determine overall status
        if (results["langflow_health"].get("status") == "healthy" and 
            results["mcp_endpoint"].get("status") == "accessible"):
            results["overall_status"] = "operational"
        elif (results["langflow_health"].get("status") == "healthy"):
            results["overall_status"] = "langflow_ok_mcp_issues"
        else:
            results["overall_status"] = "critical_issues"
        
        return results
    
    def emergency_diagnostic_report(self) -> Dict[str, Any]:
        """Generate emergency diagnostic report"""
        def generate_report():
            report = {
                "emergency_assessment": {
                    "timestamp": datetime.now().isoformat(),
                    "copilot_tools_used": throttler.tool_count,
                    "copilot_tools_remaining": throttler.max_tools - throttler.tool_count,
                    "next_reset_in": throttler.reset_interval - (time.time() - throttler.last_reset)
                },
                "mcp_config": self.mcp_config,
                "system_validation": {},
                "recommended_actions": []
            }
            
            # Add system validation
            validation = self.validate_mcp_connection()
            report["system_validation"] = validation
            
            # Add recommendations based on status
            if validation["overall_status"] == "critical_issues":
                report["recommended_actions"].extend([
                    "Execute emergency container update immediately",
                    "Check Docker daemon status",
                    "Verify network connectivity"
                ])
            elif validation["overall_status"] == "langflow_ok_mcp_issues":
                report["recommended_actions"].extend([
                    "Check MCP project configuration",
                    "Verify project ID in Langflow",
                    "Test MCP endpoint manually"
                ])
            else:
                report["recommended_actions"].append("System operational - monitor for stability")
            
            return report
        
        return throttler.execute_with_throttle(generate_report)

def main():
    """Main emergency execution function"""
    print("🚨 NoxSuite MCP Emergency System - ACTIVATED")
    print("🛡️ Addressing CVE vulnerabilities and 128 tools limit")
    
    # Initialize with your MCP config
    mcp_config = {
        "mcpServers": {
            "lf-starter_project": {
                "command": "cmd",
                "args": [
                    "/c",
                    "uvx",
                    "mcp-proxy",
                    "http://localhost:7860/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse"
                ]
            }
        }
    }
    
    # Create emergency system
    emergency_system = MCPEmergencySystem()
    emergency_system.mcp_config = mcp_config
    emergency_system.project_id = "d602c2ae-497e-49cf-9e7b-f503ef844007"
    
    print(f"🆔 Project ID: {emergency_system.project_id}")
    print(f"🔧 Tool count: {throttler.tool_count}/{throttler.max_tools}")
    
    # Step 1: Emergency container update
    print("\n🔒 Step 1: Emergency security update...")
    container_updated = emergency_system.emergency_container_update()
    
    if container_updated:
        print("✅ Container security update completed")
        # Wait for container to start
        print("⏳ Waiting for Langflow to restart...")
        time.sleep(30)
    else:
        print("⚠️ Container update failed - proceeding with validation")
    
    # Step 2: System validation
    print("\n🔍 Step 2: System validation...")
    validation_results = emergency_system.validate_mcp_connection()
    
    print(f"📊 Langflow Status: {validation_results['langflow_health'].get('status', 'unknown')}")
    print(f"🔗 MCP Endpoint: {validation_results['mcp_endpoint'].get('status', 'unknown')}")
    print(f"🎯 Overall Status: {validation_results['overall_status']}")
    
    # Step 3: Generate diagnostic report
    print("\n📋 Step 3: Generating diagnostic report...")
    diagnostic_report = emergency_system.emergency_diagnostic_report()
    
    # Save report
    report_file = f"emergency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(diagnostic_report, f, indent=2)
    
    print(f"💾 Report saved: {report_file}")
    
    # Final status
    print("\n🎯 EMERGENCY PROTOCOL COMPLETE")
    print("📈 Current tool usage:", f"{throttler.tool_count}/{throttler.max_tools}")
    
    if validation_results['overall_status'] == 'operational':
        print("✅ MISSION ACCOMPLISHED - System operational")
    else:
        print("⚠️ Issues detected - check diagnostic report for details")
    
    return diagnostic_report

if __name__ == "__main__":
    try:
        result = main()
    except Exception as e:
        print(f"❌ Emergency system failed: {e}")
        print("📞 Manual intervention required")
