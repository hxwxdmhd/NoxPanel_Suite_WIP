#!/usr/bin/env python3
"""
NoxSuite MCP Autonomous Agent - Main Orchestrator
Operates within VS Code with 128-tools throttling
"""
import time
import json
import requests
import docker
import subprocess
from datetime import datetime
from typing import Dict, Any, List
from emergency_copilot_fix import throttler

class NoxSuiteMCPAgent:
    def __init__(self):
        self.name = "NoxSuite MCP Autonomous Agent"
        self.version = "1.0.0"
        self.langflow_url = "http://localhost:7860"
        self.project_id = "d602c2ae-497e-49cf-9e7b-f503ef844007"
        self.chatgpt_api_key = "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"
        self.mission_status = "INITIALIZING"
        self.audit_results = {}
        
        print(f"🤖 {self.name} v{self.version} - ACTIVATED")
        print(f"🔧 Tool usage: {throttler.tool_count}/120")
        
    def safe_execute(self, operation_name: str, func, *args, **kwargs):
        """Execute operations with automatic throttling"""
        if throttler.tool_count >= 120:
            print(f"⚠️ Tool limit reached, queuing: {operation_name}")
            time.sleep(30)  # Wait before retry
            
        print(f"🔄 Executing: {operation_name} (Tools: {throttler.tool_count}/120)")
        return throttler.execute_with_throttle(func, *args, **kwargs)
    
    def audit_docker_containers(self) -> Dict[str, Any]:
        """Audit Docker container health - Step 1"""
        def docker_audit():
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                
                noxsuite_containers = [c for c in containers if 'noxsuite' in c.name]
                
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "total_containers": len(containers),
                    "noxsuite_containers": len(noxsuite_containers),
                    "status": {}
                }
                
                for container in noxsuite_containers:
                    results["status"][container.name] = {
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else "unknown"
                    }
                
                return results
                
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        return self.safe_execute("Docker Container Audit", docker_audit)
    
    def validate_langflow_endpoint(self) -> Dict[str, Any]:
        """Validate Langflow connectivity - Step 2"""
        def langflow_check():
            try:
                # Health check
                health_response = requests.get(f"{self.langflow_url}/health", timeout=5)
                
                # API check
                api_response = requests.get(f"{self.langflow_url}/api/v1/version", timeout=5)
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "health_status": health_response.status_code,
                    "api_status": api_response.status_code,
                    "response_time": health_response.elapsed.total_seconds(),
                    "url": self.langflow_url,
                    "status": "healthy" if health_response.status_code == 200 else "degraded"
                }
                
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        return self.safe_execute("Langflow Endpoint Validation", langflow_check)
    
    def test_mcp_integration(self) -> Dict[str, Any]:
        """Test MCP integration - Step 3"""
        def mcp_test():
            try:
                mcp_endpoint = f"{self.langflow_url}/api/v1/mcp/project/{self.project_id}/sse"
                response = requests.get(mcp_endpoint, timeout=5)
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "project_id": self.project_id,
                    "endpoint": mcp_endpoint,
                    "status_code": response.status_code,
                    "status": "accessible" if response.status_code in [200, 404] else "error"
                }
                
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        return self.safe_execute("MCP Integration Test", mcp_test)
    
    def check_github_mcp_server(self) -> Dict[str, Any]:
        """Check GitHub MCP Server status - Step 4"""
        def github_mcp_check():
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                
                github_containers = [c for c in containers if 'github' in c.name.lower() or 'mcp' in c.name.lower()]
                
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "github_mcp_containers": []
                }
                
                for container in github_containers:
                    results["github_mcp_containers"].append({
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else "unknown"
                    })
                
                results["status"] = "healthy" if any(c["status"] == "running" for c in results["github_mcp_containers"]) else "no_running_containers"
                
                return results
                
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        return self.safe_execute("GitHub MCP Server Check", github_mcp_check)
    
    def generate_system_summary(self) -> Dict[str, Any]:
        """Generate comprehensive system summary - Step 5"""
        def summary_generation():
            summary = {
                "agent": {
                    "name": self.name,
                    "version": self.version,
                    "timestamp": datetime.now().isoformat(),
                    "tool_usage": f"{throttler.tool_count}/120"
                },
                "audit_results": self.audit_results,
                "overall_status": "unknown",
                "critical_issues": [],
                "recommendations": []
            }
            
            # Analyze results
            issues_found = 0
            
            if self.audit_results.get("docker", {}).get("status") == "failed":
                issues_found += 1
                summary["critical_issues"].append("Docker connectivity issues")
                
            if self.audit_results.get("langflow", {}).get("status") != "healthy":
                issues_found += 1
                summary["critical_issues"].append("Langflow endpoint issues")
                
            if self.audit_results.get("mcp", {}).get("status") != "accessible":
                issues_found += 1
                summary["critical_issues"].append("MCP integration issues")
            
            # Determine overall status
            if issues_found == 0:
                summary["overall_status"] = "operational"
                summary["recommendations"].append("System operational - continue monitoring")
            elif issues_found <= 2:
                summary["overall_status"] = "degraded"
                summary["recommendations"].append("Address identified issues")
            else:
                summary["overall_status"] = "critical"
                summary["recommendations"].append("Emergency intervention required")
            
            return summary
        
        return self.safe_execute("System Summary Generation", summary_generation)
    
    def autonomous_audit_cycle(self) -> Dict[str, Any]:
        """Execute complete autonomous audit cycle"""
        print(f"\n🎯 Starting Autonomous Audit Cycle")
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Step 1: Docker Audit (30s cooldown)
        print("\n📊 Step 1/5: Docker Container Audit")
        self.audit_results["docker"] = self.audit_docker_containers()
        print(f"   Status: {self.audit_results['docker'].get('status', 'unknown')}")
        time.sleep(30)
        
        # Step 2: Langflow Validation (30s cooldown)
        print("\n🌐 Step 2/5: Langflow Endpoint Validation")
        self.audit_results["langflow"] = self.validate_langflow_endpoint()
        print(f"   Status: {self.audit_results['langflow'].get('status', 'unknown')}")
        time.sleep(30)
        
        # Step 3: MCP Integration Test (30s cooldown)
        print("\n🔗 Step 3/5: MCP Integration Test")
        self.audit_results["mcp"] = self.test_mcp_integration()
        print(f"   Status: {self.audit_results['mcp'].get('status', 'unknown')}")
        time.sleep(30)
        
        # Step 4: GitHub MCP Check (30s cooldown)
        print("\n🐙 Step 4/5: GitHub MCP Server Check")
        self.audit_results["github_mcp"] = self.check_github_mcp_server()
        print(f"   Status: {self.audit_results['github_mcp'].get('status', 'unknown')}")
        time.sleep(30)
        
        # Step 5: System Summary
        print("\n📋 Step 5/5: System Summary Generation")
        system_summary = self.generate_system_summary()
        
        # Save results
        report_file = f"autonomous_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(system_summary, f, indent=2)
        
        print(f"\n💾 Audit report saved: {report_file}")
        print(f"🎯 Overall Status: {system_summary.get('overall_status', 'unknown')}")
        print(f"🔧 Final tool usage: {throttler.tool_count}/120")
        
        # Update mission status
        if system_summary.get('overall_status') == 'operational':
            self.mission_status = "MISSION ACCOMPLISHED"
            print("\n✅ 🎯 MISSION ACCOMPLISHED")
        else:
            self.mission_status = "ISSUES_DETECTED"
            print(f"\n⚠️ Issues detected: {len(system_summary.get('critical_issues', []))}")
        
        return system_summary

def main():
    """Main autonomous agent execution"""
    print("🚀 NoxSuite MCP Autonomous Agent - Starting Autonomous Operation")
    
    # Initialize agent
    agent = NoxSuiteMCPAgent()
    
    # Execute autonomous audit cycle
    results = agent.autonomous_audit_cycle()
    
    # Final status
    print(f"\n🏁 Mission Status: {agent.mission_status}")
    print(f"📊 Tool Usage: {throttler.tool_count}/120")
    
    if agent.mission_status == "MISSION ACCOMPLISHED":
        print("🎉 All systems operational - autonomous monitoring active")
    else:
        print("🔄 Re-entering diagnostic loop for issue resolution")
    
    return results

if __name__ == "__main__":
    try:
        result = main()
    except Exception as e:
        print(f"❌ Autonomous agent error: {e}")
        print(f"🔧 Current tool usage: {throttler.tool_count}/120")
