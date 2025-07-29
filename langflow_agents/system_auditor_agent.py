"""
System Auditor Agent - Core implementation

Continuously audits the NoxSuite ecosystem, MCP Server orchestration logs,
Docker networking, and service health.
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import docker
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'system_auditor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemAuditorAgent")

class SystemAuditorAgent:
    """
    MCP-driven System Auditor Agent that continuously monitors the NoxSuite ecosystem,
    MCP Server orchestration logs, Docker networking, and service health.
    """
    
    def __init__(self, 
                 output_dir: str = None,
                 mcp_server_url: str = "http://localhost:8000",
                 langflow_url: str = "http://localhost:7860",
                 audit_interval: int = 300):
        """
        Initialize the System Auditor Agent
        
        Args:
            output_dir: Directory to store audit results
            mcp_server_url: URL of the MCP Server
            langflow_url: URL of the Langflow interface
            audit_interval: Time between audits in seconds (default: 5 minutes)
        """
        self.output_dir = output_dir or str(Path(__file__).parent / 'audit_results')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.mcp_server_url = mcp_server_url
        self.langflow_url = langflow_url
        self.audit_interval = audit_interval
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
        
        # Initialize results storage
        self.last_audit_result = {}
        self.audit_history = []
        self.regression_metrics = {}
        
        logger.info(f"System Auditor Agent initialized with output directory: {self.output_dir}")
    
    def audit_docker_ecosystem(self) -> Dict[str, Any]:
        """
        Audit the Docker ecosystem including containers, networks, and volumes
        
        Returns:
            Dictionary containing Docker audit results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "containers": {},
            "networks": {},
            "volumes": {},
            "errors": []
        }
        
        try:
            if not self.docker_client:
                self.docker_client = docker.from_env()
            
            # Audit containers
            containers = self.docker_client.containers.list(all=True)
            results["containers"]["total"] = len(containers)
            results["containers"]["running"] = sum(1 for c in containers if c.status == "running")
            results["containers"]["stopped"] = sum(1 for c in containers if c.status == "exited")
            
            # Check for NoxSuite specific containers
            nox_containers = {
                "noxsuite-langflow": {"found": False, "status": None, "health": None},
                "noxsuite-postgres": {"found": False, "status": None, "health": None},
                "noxsuite-redis": {"found": False, "status": None, "health": None},
                "contextforge-mcp": {"found": False, "status": None, "health": None}
            }
            
            for container in containers:
                if container.name in nox_containers:
                    nox_containers[container.name]["found"] = True
                    nox_containers[container.name]["status"] = container.status
                    
                    # Get container health if available
                    if hasattr(container, "attrs") and "State" in container.attrs:
                        if "Health" in container.attrs["State"]:
                            nox_containers[container.name]["health"] = container.attrs["State"]["Health"]["Status"]
            
            results["containers"]["nox_services"] = nox_containers
            
            # Audit networks
            networks = self.docker_client.networks.list()
            results["networks"]["total"] = len(networks)
            results["networks"]["details"] = []
            
            for network in networks:
                network_info = {
                    "id": network.id[:12],
                    "name": network.name,
                    "driver": network.attrs.get("Driver", "unknown"),
                    "containers": len(network.attrs.get("Containers", {}))
                }
                results["networks"]["details"].append(network_info)
            
            # Check for NoxSuite network
            nox_network_exists = any(n.name == "noxsuite-network" for n in networks)
            results["networks"]["nox_network_exists"] = nox_network_exists
            
            # Audit volumes
            volumes = self.docker_client.volumes.list()
            results["volumes"]["total"] = len(volumes)
            results["volumes"]["names"] = [v.name for v in volumes]
            
        except Exception as e:
            error_msg = f"Error during Docker ecosystem audit: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def audit_mcp_server(self) -> Dict[str, Any]:
        """
        Audit the MCP Server health, orchestration logs, and agent definitions
        
        Returns:
            Dictionary containing MCP Server audit results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "health": False,
            "orchestration": {},
            "agent_definitions": {},
            "errors": []
        }
        
        try:
            # Check MCP Server health
            health_response = requests.get(f"{self.mcp_server_url}/health", timeout=5)
            results["health"] = health_response.status_code == 200
            
            if results["health"]:
                # Get orchestration logs
                logs_response = requests.get(f"{self.mcp_server_url}/api/orchestration/logs", timeout=10)
                if logs_response.status_code == 200:
                    results["orchestration"]["logs"] = logs_response.json()
                else:
                    results["errors"].append(f"Failed to retrieve orchestration logs: {logs_response.status_code}")
                
                # Get agent definitions
                agents_response = requests.get(f"{self.mcp_server_url}/api/agents", timeout=10)
                if agents_response.status_code == 200:
                    results["agent_definitions"]["agents"] = agents_response.json()
                else:
                    results["errors"].append(f"Failed to retrieve agent definitions: {agents_response.status_code}")
        except requests.RequestException as e:
            error_msg = f"MCP Server connection error: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"Error during MCP Server audit: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def audit_langflow(self) -> Dict[str, Any]:
        """
        Audit Langflow health, available flows, and component status
        
        Returns:
            Dictionary containing Langflow audit results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "health": False,
            "flows": {},
            "components": {},
            "errors": []
        }
        
        try:
            # Check Langflow health
            health_response = requests.get(f"{self.langflow_url}/health", timeout=5)
            results["health"] = health_response.status_code == 200
            
            if results["health"]:
                # Get flows (if API available)
                try:
                    flows_response = requests.get(f"{self.langflow_url}/api/v1/flows", timeout=10)
                    if flows_response.status_code == 200:
                        flows_data = flows_response.json()
                        results["flows"]["count"] = len(flows_data)
                        results["flows"]["names"] = [flow.get("name") for flow in flows_data]
                    else:
                        results["errors"].append(f"Failed to retrieve flows: {flows_response.status_code}")
                except:
                    # Fallback to checking local files
                    flows_dir = Path(__file__).parent.parent / "langflow" / "flows"
                    if flows_dir.exists():
                        flow_files = list(flows_dir.glob("*.json"))
                        results["flows"]["count"] = len(flow_files)
                        results["flows"]["names"] = [f.stem for f in flow_files]
                    else:
                        results["flows"]["count"] = 0
                        results["flows"]["names"] = []
                
                # Check components
                try:
                    components_response = requests.get(f"{self.langflow_url}/api/v1/components", timeout=10)
                    if components_response.status_code == 200:
                        components_data = components_response.json()
                        results["components"]["count"] = sum(len(components_data.get(category, [])) for category in components_data)
                        results["components"]["categories"] = list(components_data.keys())
                    else:
                        results["errors"].append(f"Failed to retrieve components: {components_response.status_code}")
                except Exception as e:
                    results["errors"].append(f"Failed to process components: {str(e)}")
        except requests.RequestException as e:
            error_msg = f"Langflow connection error: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"Error during Langflow audit: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def audit_copilot_tools(self) -> Dict[str, Any]:
        """
        Audit VS Code Copilot tools usage and constraints
        
        Returns:
            Dictionary containing Copilot tools audit results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "tool_usage": {},
            "constraints": {},
            "errors": []
        }
        
        try:
            # Try to import CopilotToolsMonitor
            sys.path.append(str(Path(__file__).parent.parent))
            from copilot_tools_monitor import CopilotToolsMonitor
            
            # Get tool usage statistics
            monitor = CopilotToolsMonitor()
            stats = monitor.get_detailed_statistics()
            
            results["tool_usage"] = {
                "current_count": stats.get("current_count", 0),
                "max_limit": stats.get("max_limit", 128),
                "remaining": stats.get("remaining", 0),
                "usage_percentage": stats.get("usage_percentage", 0)
            }
            
            results["constraints"] = {
                "throttling_enabled": stats.get("throttling_enabled", False),
                "throttling_active": stats.get("throttling_active", False),
                "approaching_limit": results["tool_usage"]["usage_percentage"] > 70
            }
            
            # Check tool usage trends
            if hasattr(monitor, "get_usage_trends"):
                results["tool_usage"]["trends"] = monitor.get_usage_trends()
        except ImportError:
            results["errors"].append("CopilotToolsMonitor module not available")
        except Exception as e:
            error_msg = f"Error during Copilot tools audit: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def detect_regressions(self, current_audit: Dict[str, Any], previous_audit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current audit with previous audit to detect regressions
        
        Args:
            current_audit: Current audit results
            previous_audit: Previous audit results
            
        Returns:
            Dictionary containing detected regressions
        """
        regressions = {
            "timestamp": datetime.now().isoformat(),
            "detected": False,
            "issues": []
        }
        
        try:
            # Check Docker container health regressions
            if ("docker" in current_audit and "docker" in previous_audit and
                "containers" in current_audit["docker"] and "containers" in previous_audit["docker"]):
                
                prev_running = previous_audit["docker"]["containers"].get("running", 0)
                curr_running = current_audit["docker"]["containers"].get("running", 0)
                
                if curr_running < prev_running:
                    regressions["detected"] = True
                    regressions["issues"].append({
                        "component": "docker",
                        "issue": "container_count_decreased",
                        "previous": prev_running,
                        "current": curr_running
                    })
                
                # Check NoxSuite container health
                if ("nox_services" in current_audit["docker"]["containers"] and 
                    "nox_services" in previous_audit["docker"]["containers"]):
                    
                    for container_name, curr_info in current_audit["docker"]["containers"]["nox_services"].items():
                        prev_info = previous_audit["docker"]["containers"]["nox_services"].get(container_name, {})
                        
                        # Check if container was running but is now stopped
                        if (prev_info.get("found", False) and prev_info.get("status") == "running" and 
                            (not curr_info.get("found", False) or curr_info.get("status") != "running")):
                            
                            regressions["detected"] = True
                            regressions["issues"].append({
                                "component": "docker",
                                "issue": "container_stopped",
                                "container": container_name,
                                "previous_status": prev_info.get("status"),
                                "current_status": curr_info.get("status")
                            })
                        
                        # Check if container health degraded
                        if (curr_info.get("health") != prev_info.get("health") and 
                            prev_info.get("health") == "healthy" and curr_info.get("health") != "healthy"):
                            
                            regressions["detected"] = True
                            regressions["issues"].append({
                                "component": "docker",
                                "issue": "health_degraded",
                                "container": container_name,
                                "previous_health": prev_info.get("health"),
                                "current_health": curr_info.get("health")
                            })
            
            # Check MCP server health regressions
            if ("mcp" in current_audit and "mcp" in previous_audit):
                if previous_audit["mcp"].get("health", False) and not current_audit["mcp"].get("health", False):
                    regressions["detected"] = True
                    regressions["issues"].append({
                        "component": "mcp_server",
                        "issue": "health_degraded",
                        "previous": "healthy",
                        "current": "unhealthy"
                    })
            
            # Check Langflow health regressions
            if ("langflow" in current_audit and "langflow" in previous_audit):
                if previous_audit["langflow"].get("health", False) and not current_audit["langflow"].get("health", False):
                    regressions["detected"] = True
                    regressions["issues"].append({
                        "component": "langflow",
                        "issue": "health_degraded",
                        "previous": "healthy",
                        "current": "unhealthy"
                    })
                
                # Check for missing flows
                prev_flows = set(previous_audit["langflow"].get("flows", {}).get("names", []))
                curr_flows = set(current_audit["langflow"].get("flows", {}).get("names", []))
                
                missing_flows = prev_flows - curr_flows
                if missing_flows:
                    regressions["detected"] = True
                    regressions["issues"].append({
                        "component": "langflow",
                        "issue": "missing_flows",
                        "flows": list(missing_flows)
                    })
            
            # Check Copilot tools usage regressions
            if ("copilot" in current_audit and "copilot" in previous_audit):
                prev_usage = previous_audit["copilot"].get("tool_usage", {}).get("usage_percentage", 0)
                curr_usage = current_audit["copilot"].get("tool_usage", {}).get("usage_percentage", 0)
                
                if curr_usage > 90 and curr_usage > prev_usage:
                    regressions["detected"] = True
                    regressions["issues"].append({
                        "component": "copilot",
                        "issue": "approaching_tool_limit",
                        "previous_percentage": prev_usage,
                        "current_percentage": curr_usage
                    })
        except Exception as e:
            logger.error(f"Error during regression detection: {e}")
            regressions["errors"] = [str(e)]
        
        return regressions
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Run a comprehensive system audit
        
        Returns:
            Dictionary containing all audit results
        """
        logger.info("Starting comprehensive system audit")
        
        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "docker": {},
            "mcp": {},
            "langflow": {},
            "copilot": {},
            "regressions": {
                "detected": False,
                "issues": []
            }
        }
        
        # Run Docker ecosystem audit
        try:
            audit_results["docker"] = self.audit_docker_ecosystem()
            logger.info("Docker ecosystem audit completed")
        except Exception as e:
            logger.error(f"Docker ecosystem audit failed: {e}")
            audit_results["docker"] = {"error": str(e)}
        
        # Run MCP Server audit
        try:
            audit_results["mcp"] = self.audit_mcp_server()
            logger.info("MCP Server audit completed")
        except Exception as e:
            logger.error(f"MCP Server audit failed: {e}")
            audit_results["mcp"] = {"error": str(e)}
        
        # Run Langflow audit
        try:
            audit_results["langflow"] = self.audit_langflow()
            logger.info("Langflow audit completed")
        except Exception as e:
            logger.error(f"Langflow audit failed: {e}")
            audit_results["langflow"] = {"error": str(e)}
        
        # Run Copilot tools audit
        try:
            audit_results["copilot"] = self.audit_copilot_tools()
            logger.info("Copilot tools audit completed")
        except Exception as e:
            logger.error(f"Copilot tools audit failed: {e}")
            audit_results["copilot"] = {"error": str(e)}
        
        # Check for regressions if we have previous audit results
        if self.last_audit_result:
            audit_results["regressions"] = self.detect_regressions(audit_results, self.last_audit_result)
            logger.info(f"Regression analysis completed - issues detected: {audit_results['regressions']['detected']}")
        
        # Save audit results
        self.save_audit_results(audit_results)
        
        # Update last audit result and history
        self.last_audit_result = audit_results
        self.audit_history.append({
            "timestamp": audit_results["timestamp"],
            "summary": {
                "docker_health": "healthy" if not audit_results["docker"].get("errors") else "issues_detected",
                "mcp_health": audit_results["mcp"].get("health", False),
                "langflow_health": audit_results["langflow"].get("health", False),
                "regressions": audit_results["regressions"]["detected"]
            }
        })
        
        # Trim history to keep it manageable
        if len(self.audit_history) > 50:
            self.audit_history = self.audit_history[-50:]
        
        logger.info("Comprehensive system audit completed")
        return audit_results
    
    def save_audit_results(self, audit_results: Dict[str, Any]) -> None:
        """
        Save audit results to output directory
        
        Args:
            audit_results: Audit results to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"audit_{timestamp}.json")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(audit_results, f, indent=2)
            logger.info(f"Audit results saved to {output_file}")
            
            # Also save latest audit result for quick access
            latest_file = os.path.join(self.output_dir, "latest_audit.json")
            with open(latest_file, 'w') as f:
                json.dump(audit_results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit results: {e}")
    
    def continuous_audit_loop(self, run_once: bool = False) -> None:
        """
        Run continuous audit loop at specified intervals
        
        Args:
            run_once: If True, run only one audit and return
        """
        logger.info(f"Starting {'single' if run_once else 'continuous'} audit process")
        
        try:
            while True:
                self.run_full_audit()
                
                if run_once:
                    logger.info("Single audit completed, exiting loop")
                    break
                
                logger.info(f"Sleeping for {self.audit_interval} seconds until next audit")
                time.sleep(self.audit_interval)
        except KeyboardInterrupt:
            logger.info("Audit process interrupted by user")
        except Exception as e:
            logger.error(f"Error in continuous audit loop: {e}")
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the latest audit results
        
        Returns:
            Dictionary containing audit summary
        """
        if not self.last_audit_result:
            return {"error": "No audit results available"}
        
        summary = {
            "timestamp": self.last_audit_result.get("timestamp", "unknown"),
            "system_health": {
                "docker": "healthy" if not self.last_audit_result.get("docker", {}).get("errors") else "issues_detected",
                "mcp": self.last_audit_result.get("mcp", {}).get("health", False),
                "langflow": self.last_audit_result.get("langflow", {}).get("health", False),
                "copilot_tools": not self.last_audit_result.get("copilot", {}).get("constraints", {}).get("approaching_limit", False)
            },
            "containers": {
                "total": self.last_audit_result.get("docker", {}).get("containers", {}).get("total", 0),
                "running": self.last_audit_result.get("docker", {}).get("containers", {}).get("running", 0)
            },
            "regressions_detected": self.last_audit_result.get("regressions", {}).get("detected", False),
            "history_entries": len(self.audit_history)
        }
        
        # Overall health assessment
        health_values = list(summary["system_health"].values())
        if all(health_values):
            summary["overall_health"] = "healthy"
        elif not any(health_values):
            summary["overall_health"] = "critical"
        else:
            summary["overall_health"] = "issues_detected"
        
        return summary


# For importing as module
if __name__ == "__main__":
    import sys
    
    # Simple CLI for running the auditor
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        auditor = SystemAuditorAgent()
        auditor.continuous_audit_loop(run_once=True)
    else:
        print("System Auditor Agent - Running single audit")
        auditor = SystemAuditorAgent()
        results = auditor.run_full_audit()
        print(f"Audit completed with {len(results.get('docker', {}).get('errors', [])) + len(results.get('mcp', {}).get('errors', [])) + len(results.get('langflow', {}).get('errors', [])) + len(results.get('copilot', {}).get('errors', []))} errors")
        print(f"Results saved to {auditor.output_dir}/latest_audit.json")
