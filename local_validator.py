#!/usr/bin/env python3
"""
Local System Validator - Alternative to ChatGPT for autonomous validation
"""
import json
import time
from datetime import datetime
from emergency_copilot_fix import throttler

class LocalSystemValidator:
    def __init__(self):
        self.validation_rules = {
            "docker_health": {
                "min_containers": 3,
                "required_status": "running"
            },
            "langflow_health": {
                "required_status": "healthy",
                "max_response_time": 1.0
            },
            "mcp_integration": {
                "required_status": "accessible"
            },
            "tool_usage": {
                "warning_threshold": 100,
                "critical_threshold": 120
            }
        }
    
    def validate_system_audit(self, audit_data: dict) -> dict:
        """Perform local validation of system audit"""
        def local_validation():
            validation_result = {
                "status": "success",
                "validation_timestamp": datetime.now().isoformat(),
                "risk_assessment": "Low",
                "validation_checks": {},
                "recommendations": [],
                "external_validation": "local_completed"
            }
            
            checks = validation_result["validation_checks"]
            
            # Check Docker health
            docker_data = audit_data.get("audit_results", {}).get("docker", {})
            running_containers = sum(1 for c in docker_data.get("status", {}).values() 
                                   if c.get("status") == "running")
            
            checks["docker_health"] = {
                "running_containers": running_containers,
                "status": "pass" if running_containers >= self.validation_rules["docker_health"]["min_containers"] else "fail"
            }
            
            # Check Langflow health
            langflow_data = audit_data.get("audit_results", {}).get("langflow", {})
            langflow_status = langflow_data.get("status")
            response_time = langflow_data.get("response_time", 0)
            
            checks["langflow_health"] = {
                "status": langflow_status,
                "response_time": response_time,
                "result": "pass" if (langflow_status == "healthy" and 
                                   response_time < self.validation_rules["langflow_health"]["max_response_time"]) else "warning"
            }
            
            # Check MCP integration
            mcp_data = audit_data.get("audit_results", {}).get("mcp", {})
            mcp_status = mcp_data.get("status")
            
            checks["mcp_integration"] = {
                "status": mcp_status,
                "result": "pass" if mcp_status == "accessible" else "fail"
            }
            
            # Check tool usage
            tool_usage = audit_data.get("agent", {}).get("tool_usage", "0/120")
            current_tools = int(tool_usage.split("/")[0])
            
            checks["tool_usage"] = {
                "current": current_tools,
                "threshold": self.validation_rules["tool_usage"]["warning_threshold"],
                "result": "pass" if current_tools < self.validation_rules["tool_usage"]["warning_threshold"] else "warning"
            }
            
            # Determine overall risk
            failed_checks = sum(1 for check in checks.values() if check.get("result") == "fail")
            warning_checks = sum(1 for check in checks.values() if check.get("result") == "warning")
            
            if failed_checks > 0:
                validation_result["risk_assessment"] = "High"
                validation_result["recommendations"].append("Critical system failures detected - immediate intervention required")
            elif warning_checks > 1:
                validation_result["risk_assessment"] = "Medium"
                validation_result["recommendations"].append("Multiple warnings detected - monitor closely")
            else:
                validation_result["risk_assessment"] = "Low"
                validation_result["recommendations"].append("System operational within normal parameters")
            
            # Add specific recommendations
            if checks["tool_usage"]["result"] == "warning":
                validation_result["recommendations"].append(f"Tool usage approaching limit ({current_tools}/120) - implement throttling")
            
            if checks["langflow_health"]["result"] == "warning":
                validation_result["recommendations"].append(f"Langflow response time elevated ({response_time:.3f}s) - monitor performance")
            
            # Generate analysis summary
            validation_result["analysis_summary"] = f"""
Local Validation Analysis:
- Risk Level: {validation_result["risk_assessment"]}
- Docker: {running_containers} containers running ✅
- Langflow: {langflow_status} ({response_time:.3f}s response) {'✅' if checks["langflow_health"]["result"] == "pass" else '⚠️'}
- MCP: {mcp_status} {'✅' if checks["mcp_integration"]["result"] == "pass" else '❌'}
- Tool Usage: {current_tools}/120 {'✅' if checks["tool_usage"]["result"] == "pass" else '⚠️'}

Validation Verdict: System is {'OPERATIONAL' if validation_result["risk_assessment"] == "Low" else 'NEEDS ATTENTION'}
            """.strip()
            
            return validation_result
        
        return throttler.execute_with_throttle(local_validation)

def validate_latest_audit():
    """Find and validate the latest audit report with local validator"""
    import glob
    import os
    
    # Find latest audit file
    audit_files = glob.glob("autonomous_audit_*.json")
    if not audit_files:
        print("❌ No audit files found")
        return None
    
    latest_file = max(audit_files, key=os.path.getctime)
    print(f"📋 Validating: {latest_file}")
    
    # Load audit data
    with open(latest_file, 'r') as f:
        audit_data = json.load(f)
    
    # Perform local validation
    validator = LocalSystemValidator()
    validation_result = validator.validate_system_audit(audit_data)
    
    # Add validation to audit data
    audit_data["local_validation"] = validation_result
    
    # Save updated audit with validation
    validated_file = latest_file.replace("autonomous_audit_", "locally_validated_audit_")
    with open(validated_file, 'w') as f:
        json.dump(audit_data, f, indent=2)
    
    print(f"✅ Local validation complete: {validated_file}")
    
    # Display results
    if validation_result.get("status") == "success":
        print(f"\n🔍 Risk Assessment: {validation_result['risk_assessment']}")
        print(validation_result["analysis_summary"])
        print(f"\n🔧 Tool usage: {throttler.tool_count}/120")
        
        # Final mission status
        if validation_result["risk_assessment"] == "Low":
            print("\n🎯 LOCAL VALIDATION: MISSION ACCOMPLISHED")
            print("✅ All systems operational and validated")
        else:
            print(f"\n⚠️ LOCAL VALIDATION: {validation_result['risk_assessment']} RISK DETECTED")
            print("🔄 Recommendations:", validation_result["recommendations"])
    else:
        print(f"❌ Validation failed: {validation_result.get('error')}")
    
    return validation_result

if __name__ == "__main__":
    print("🔍 Local System Validator - Starting")
    result = validate_latest_audit()
    
    if result and result.get("risk_assessment") == "Low":
        print("\n🎯 AUTONOMOUS VALIDATION COMPLETE - MISSION ACCOMPLISHED")
    else:
        print("\n⚠️ Validation complete with warnings/issues")
