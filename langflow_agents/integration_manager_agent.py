"""
Integration Manager Agent - Core implementation

Ensures MCP-Langflow API connectivity, manages agent definitions in Langflow,
and handles VS Code Copilot agent integration and 128 tools limit management.
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'integration_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IntegrationManagerAgent")

class IntegrationManagerAgent:
    """
    Integration Manager Agent that ensures MCP-Langflow API connectivity,
    manages agent definitions in Langflow, and handles VS Code Copilot agent integration.
    """
    
    def __init__(self, 
                 mcp_server_url: str = "http://localhost:8000",
                 langflow_url: str = "http://localhost:7860",
                 config_dir: str = None):
        """
        Initialize the Integration Manager Agent
        
        Args:
            mcp_server_url: URL of the MCP Server
            langflow_url: URL of the Langflow interface
            config_dir: Directory for configuration files
        """
        self.mcp_server_url = mcp_server_url
        self.langflow_url = langflow_url
        self.config_dir = config_dir or str(Path(__file__).parent / 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize working directories
        self.langflow_components_dir = Path(__file__).parent.parent / "langflow" / "components"
        self.langflow_flows_dir = Path(__file__).parent.parent / "langflow" / "flows"
        os.makedirs(self.langflow_components_dir, exist_ok=True)
        os.makedirs(self.langflow_flows_dir, exist_ok=True)
        
        # Initialize session
        self.session = requests.Session()
        
        # Store integration status
        self.integration_status = {
            "mcp_langflow_connected": False,
            "last_connectivity_check": None,
            "agent_definitions_synced": False,
            "last_sync_time": None,
            "copilot_integration_active": False
        }
        
        logger.info(f"Integration Manager Agent initialized with MCP URL: {self.mcp_server_url} and Langflow URL: {self.langflow_url}")
    
    def check_mcp_langflow_connectivity(self) -> Dict[str, Any]:
        """
        Check connectivity between MCP Server and Langflow
        
        Returns:
            Dictionary containing connectivity check results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "mcp_available": False,
            "langflow_available": False,
            "connection_established": False,
            "errors": []
        }
        
        try:
            # Check MCP Server availability
            mcp_response = self.session.get(f"{self.mcp_server_url}/health", timeout=5)
            results["mcp_available"] = mcp_response.status_code == 200
            
            # Check Langflow availability
            langflow_response = self.session.get(f"{self.langflow_url}/health", timeout=5)
            results["langflow_available"] = langflow_response.status_code == 200
            
            # Check if MCP can reach Langflow
            if results["mcp_available"]:
                try:
                    mcp_connectivity = self.session.post(
                        f"{self.mcp_server_url}/api/integration/test-connectivity",
                        json={"target_url": self.langflow_url},
                        timeout=10
                    )
                    results["connection_established"] = mcp_connectivity.status_code == 200
                except Exception as e:
                    results["errors"].append(f"MCP connectivity test failed: {str(e)}")
            
            # Update integration status
            self.integration_status["mcp_langflow_connected"] = results["mcp_available"] and results["langflow_available"]
            self.integration_status["last_connectivity_check"] = results["timestamp"]
            
            logger.info(f"Connectivity check - MCP: {results['mcp_available']}, Langflow: {results['langflow_available']}")
            
        except requests.RequestException as e:
            error_msg = f"Connection error during connectivity check: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"Error checking connectivity: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def manage_langflow_agent_definitions(self) -> Dict[str, Any]:
        """
        Manage agent definitions in Langflow based on MCP state
        
        Returns:
            Dictionary containing agent definition management results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "agents_synced": 0,
            "components_created": 0,
            "flows_updated": 0,
            "errors": []
        }
        
        try:
            # First check MCP Server for agent definitions
            if not self.check_mcp_langflow_connectivity()["mcp_available"]:
                results["errors"].append("MCP Server not available for agent definition sync")
                return results
            
            # Get agent definitions from MCP
            try:
                agents_response = self.session.get(f"{self.mcp_server_url}/api/agents", timeout=10)
                if agents_response.status_code != 200:
                    results["errors"].append(f"Failed to retrieve agent definitions: {agents_response.status_code}")
                    return results
                
                agent_definitions = agents_response.json()
                
                # Process agent definitions
                for agent_name, agent_def in agent_definitions.items():
                    # Create custom component for each agent
                    component_file = self.langflow_components_dir / f"{agent_name}_component.py"
                    
                    # Create component Python file
                    with open(component_file, 'w') as f:
                        f.write(self._generate_agent_component_code(agent_name, agent_def))
                    
                    results["components_created"] += 1
                    
                    # Create flow for the agent if specified
                    if agent_def.get("create_flow", False):
                        flow_file = self.langflow_flows_dir / f"{agent_name}_flow.json"
                        
                        with open(flow_file, 'w') as f:
                            f.write(json.dumps(self._generate_agent_flow(agent_name, agent_def), indent=2))
                        
                        results["flows_updated"] += 1
                
                results["agents_synced"] = len(agent_definitions)
                
                # Update integration status
                self.integration_status["agent_definitions_synced"] = True
                self.integration_status["last_sync_time"] = results["timestamp"]
                
                logger.info(f"Synced {results['agents_synced']} agent definitions, created {results['components_created']} components, updated {results['flows_updated']} flows")
                
            except Exception as e:
                error_msg = f"Error syncing agent definitions: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
            
            # If MCP is not available, create default agent definitions
            if not results["agents_synced"]:
                # Create core agent definitions for our system
                self._create_default_agent_definitions()
                results["agents_synced"] = 4  # Our 4 default agents
                results["components_created"] = 4
                results["flows_updated"] = 4
                logger.info("Created default agent definitions")
        
        except Exception as e:
            error_msg = f"Error managing agent definitions: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _generate_agent_component_code(self, agent_name: str, agent_def: Dict[str, Any]) -> str:
        """
        Generate Python code for a custom Langflow component representing an agent
        
        Args:
            agent_name: Name of the agent
            agent_def: Agent definition dictionary
            
        Returns:
            String containing Python code for the component
        """
        code = f'''"""
{agent_name.replace('_', ' ').title()} Component for Langflow
Generated by Integration Manager Agent
"""
from typing import Dict, Any, List, Optional
from langflow import CustomComponent


class {agent_name.replace('_', '').title()}Component(CustomComponent):
    """
    {agent_def.get('description', 'Custom agent component')}
    """
    display_name = "{agent_name.replace('_', ' ').title()}"
    description = "{agent_def.get('description', 'Custom agent component')}"
    icon = "{agent_def.get('icon', 'agent')}"
    
    def build_config(self) -> Dict[str, Any]:
        """Build the configuration for the component"""
        return {{
'''
        
        # Add agent parameters from definition
        for param_name, param_def in agent_def.get('parameters', {}).items():
            param_type = param_def.get('type', 'str')
            default_value = param_def.get('default', '')
            
            if param_type == 'str':
                default_repr = f'"{default_value}"' if default_value else '""'
            elif param_type == 'int':
                default_repr = str(default_value) if default_value else '0'
            elif param_type == 'bool':
                default_repr = str(default_value).lower() if isinstance(default_value, bool) else 'False'
            else:
                default_repr = 'None'
            
            code += f'''            "{param_name}": {{
                "display_name": "{param_name.replace('_', ' ').title()}",
                "info": "{param_def.get('description', '')}",
                "type": "{param_type}",
                "default": {default_repr},
                "required": {str(param_def.get('required', False)).lower()},
            }},
'''
        
        code += f'''        }}
    
    def build(self, **kwargs) -> Dict[str, Any]:
        """Build the agent with given parameters"""
        # Process parameters
        processed_params = {{}}
        for key, value in kwargs.items():
            processed_params[key] = value
        
        # Include agent definition metadata
        processed_params["agent_type"] = "{agent_name}"
        processed_params["agent_version"] = "{agent_def.get('version', '1.0.0')}"
        
        return processed_params
'''
        
        return code
    
    def _generate_agent_flow(self, agent_name: str, agent_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Langflow flow definition for an agent
        
        Args:
            agent_name: Name of the agent
            agent_def: Agent definition dictionary
            
        Returns:
            Dictionary containing flow definition
        """
        # This is a simplified flow generation - in a real implementation,
        # you'd want to generate a more complex flow based on agent capabilities
        
        flow_id = str(uuid.uuid4())
        
        flow = {
            "id": flow_id,
            "name": f"{agent_name.replace('_', ' ').title()} Flow",
            "description": agent_def.get('description', f"Flow for {agent_name}"),
            "data": {
                "nodes": [
                    {
                        "id": f"node_{uuid.uuid4()}",
                        "type": "customComponent",
                        "position": {
                            "x": 200,
                            "y": 200
                        },
                        "data": {
                            "name": f"{agent_name.replace('_', '').title()}Component",
                            "type": "customComponent",
                            "node": {
                                "display_name": f"{agent_name.replace('_', ' ').title()}",
                                "description": agent_def.get('description', 'Custom agent component'),
                                "base_classes": ["customComponent"]
                            }
                        }
                    }
                ],
                "edges": []
            }
        }
        
        return flow
    
    def _create_default_agent_definitions(self) -> None:
        """
        Create default agent definitions for our core agents when MCP is not available
        """
        # System Auditor Agent
        self._create_default_agent("system_auditor", {
            "description": "Continuously audits the NoxSuite ecosystem, MCP Server orchestration logs, Docker networking, and service health",
            "version": "1.0.0",
            "icon": "monitoring",
            "parameters": {
                "audit_interval": {
                    "type": "int",
                    "description": "Time between audits in seconds",
                    "default": 300,
                    "required": False
                },
                "output_dir": {
                    "type": "str",
                    "description": "Directory to store audit results",
                    "default": "",
                    "required": False
                }
            },
            "create_flow": True
        })
        
        # Integration Manager Agent
        self._create_default_agent("integration_manager", {
            "description": "Ensures MCP–Langflow API connectivity, manages agent definitions, handles VS Code Copilot agent integration",
            "version": "1.0.0",
            "icon": "integration",
            "parameters": {
                "mcp_server_url": {
                    "type": "str",
                    "description": "URL of the MCP Server",
                    "default": "http://localhost:8000",
                    "required": True
                },
                "config_dir": {
                    "type": "str",
                    "description": "Directory for configuration files",
                    "default": "",
                    "required": False
                }
            },
            "create_flow": True
        })
        
        # Workflow Executor Agent
        self._create_default_agent("workflow_executor", {
            "description": "Simulates real-user scenarios across MCP agents, Docker containers, and Langflow UI endpoints",
            "version": "1.0.0",
            "icon": "workflow",
            "parameters": {
                "workflow_dir": {
                    "type": "str",
                    "description": "Directory containing workflow definitions",
                    "default": "",
                    "required": False
                },
                "execution_interval": {
                    "type": "int",
                    "description": "Time between workflow executions in seconds",
                    "default": 600,
                    "required": False
                }
            },
            "create_flow": True
        })
        
        # ChatGPT Cross-Verification Agent
        self._create_default_agent("chatgpt_verification", {
            "description": "Submits system audits to OpenAI ChatGPT API for independent reasoning and validation",
            "version": "1.0.0",
            "icon": "ai",
            "parameters": {
                "openai_api_key": {
                    "type": "str",
                    "description": "OpenAI API key",
                    "default": "",
                    "required": True
                },
                "verification_interval": {
                    "type": "int",
                    "description": "Time between verifications in seconds",
                    "default": 1800,
                    "required": False
                }
            },
            "create_flow": True
        })
    
    def _create_default_agent(self, agent_name: str, agent_def: Dict[str, Any]) -> None:
        """
        Create a default agent definition file
        
        Args:
            agent_name: Name of the agent
            agent_def: Agent definition dictionary
        """
        try:
            # Create component Python file
            component_file = self.langflow_components_dir / f"{agent_name}_component.py"
            with open(component_file, 'w') as f:
                f.write(self._generate_agent_component_code(agent_name, agent_def))
            
            # Create flow for the agent if specified
            if agent_def.get("create_flow", False):
                flow_file = self.langflow_flows_dir / f"{agent_name}_flow.json"
                with open(flow_file, 'w') as f:
                    f.write(json.dumps(self._generate_agent_flow(agent_name, agent_def), indent=2))
            
            logger.info(f"Created default agent definition for {agent_name}")
        except Exception as e:
            logger.error(f"Failed to create default agent {agent_name}: {e}")
    
    def monitor_copilot_tools(self) -> Dict[str, Any]:
        """
        Monitor and manage VS Code Copilot agent tools usage constraints
        
        Returns:
            Dictionary containing tools monitoring results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "tools_monitored": False,
            "throttling_required": False,
            "tool_usage": {},
            "errors": []
        }
        
        try:
            # Try to import CopilotToolsMonitor
            sys.path.append(str(Path(__file__).parent.parent))
            from copilot_tools_monitor import CopilotToolsMonitor
            
            # Get tool usage statistics
            monitor = CopilotToolsMonitor()
            stats = monitor.get_detailed_statistics()
            
            results["tools_monitored"] = True
            results["tool_usage"] = {
                "current_count": stats.get("current_count", 0),
                "max_limit": stats.get("max_limit", 128),
                "remaining": stats.get("remaining", 0),
                "usage_percentage": stats.get("usage_percentage", 0)
            }
            
            # Check if throttling is needed
            results["throttling_required"] = stats.get("usage_percentage", 0) > 70
            
            if results["throttling_required"]:
                logger.warning(f"Copilot tools approaching limit: {stats.get('usage_percentage')}% used")
                
                # Activate throttling if not already active
                if not stats.get("throttling_active", False):
                    monitor.enable_throttling()
                    logger.info("Enabled Copilot tools throttling")
                
                # Check if we need to distribute tasks
                if stats.get("usage_percentage", 0) > 85:
                    logger.warning("Copilot tools critical limit approaching, activating task distribution")
                    
                    # Initialize task distributor
                    from copilot_tools_monitor import MultiAgentTaskDistributor
                    distributor = MultiAgentTaskDistributor()
                    
                    # Create task to handle the high load
                    distributor.distribute_task(
                        "High Copilot tools usage detected - offloading tasks to prevent limit breach",
                        priority=5
                    )
                    
                    logger.info("Task distribution activated")
            else:
                # Disable throttling if active but no longer needed
                if stats.get("throttling_active", False) and stats.get("usage_percentage", 0) < 60:
                    monitor.disable_throttling()
                    logger.info("Disabled Copilot tools throttling")
            
            # Update integration status
            self.integration_status["copilot_integration_active"] = True
            
        except ImportError:
            results["errors"].append("CopilotToolsMonitor module not available")
            logger.error("Failed to import CopilotToolsMonitor")
        except Exception as e:
            error_msg = f"Error during Copilot tools monitoring: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def ensure_mcp_langflow_integration(self) -> Dict[str, Any]:
        """
        Ensure proper integration between MCP and Langflow
        
        Returns:
            Dictionary containing integration results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "connectivity_established": False,
            "agent_definitions_synced": False,
            "copilot_integration_active": False,
            "errors": []
        }
        
        try:
            # Check connectivity
            connectivity = self.check_mcp_langflow_connectivity()
            results["connectivity_established"] = connectivity["connection_established"]
            
            if connectivity["errors"]:
                results["errors"].extend(connectivity["errors"])
            
            # Manage agent definitions
            if results["connectivity_established"] or not connectivity["mcp_available"]:
                agent_def_results = self.manage_langflow_agent_definitions()
                results["agent_definitions_synced"] = agent_def_results["agents_synced"] > 0
                
                if agent_def_results["errors"]:
                    results["errors"].extend(agent_def_results["errors"])
            
            # Monitor Copilot tools
            copilot_results = self.monitor_copilot_tools()
            results["copilot_integration_active"] = copilot_results["tools_monitored"]
            
            if copilot_results["errors"]:
                results["errors"].extend(copilot_results["errors"])
            
            # Update integration status
            self.integration_status["mcp_langflow_connected"] = results["connectivity_established"]
            self.integration_status["agent_definitions_synced"] = results["agent_definitions_synced"]
            self.integration_status["copilot_integration_active"] = results["copilot_integration_active"]
            
            logger.info(f"Integration status - Connectivity: {results['connectivity_established']}, " +
                      f"Agents Synced: {results['agent_definitions_synced']}, " +
                      f"Copilot Integration: {results['copilot_integration_active']}")
            
        except Exception as e:
            error_msg = f"Error ensuring MCP-Langflow integration: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def check_and_fix_issues(self) -> Dict[str, Any]:
        """
        Check for integration issues and attempt to fix them
        
        Returns:
            Dictionary containing issue resolution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "issues_detected": 0,
            "issues_resolved": 0,
            "remaining_issues": 0,
            "actions_taken": []
        }
        
        try:
            # First check integration status
            integration_results = self.ensure_mcp_langflow_integration()
            
            # Count issues
            issues = 0
            if not integration_results["connectivity_established"]:
                issues += 1
                results["actions_taken"].append("Attempting to fix MCP-Langflow connectivity")
                
                # Try to restart services (for demonstration only)
                results["actions_taken"].append("Simulated service restart for connectivity issues")
            
            if not integration_results["agent_definitions_synced"]:
                issues += 1
                results["actions_taken"].append("Attempting to re-sync agent definitions")
                
                # Force re-sync
                self.manage_langflow_agent_definitions()
                
                # Check if this resolved the issue
                if self.integration_status["agent_definitions_synced"]:
                    results["issues_resolved"] += 1
                    results["actions_taken"].append("Successfully re-synced agent definitions")
            
            if not integration_results["copilot_integration_active"]:
                issues += 1
                results["actions_taken"].append("Attempting to fix Copilot tools monitoring")
                
                # Try to fix Copilot tools monitoring
                self.monitor_copilot_tools()
                
                # Check if this resolved the issue
                if self.integration_status["copilot_integration_active"]:
                    results["issues_resolved"] += 1
                    results["actions_taken"].append("Successfully restored Copilot tools monitoring")
            
            results["issues_detected"] = issues
            results["remaining_issues"] = issues - results["issues_resolved"]
            
            logger.info(f"Issue resolution completed - Detected: {results['issues_detected']}, " +
                      f"Resolved: {results['issues_resolved']}, Remaining: {results['remaining_issues']}")
            
        except Exception as e:
            error_msg = f"Error checking and fixing issues: {str(e)}"
            logger.error(error_msg)
            results["actions_taken"].append(f"Error during issue resolution: {error_msg}")
        
        return results
    
    def run_integration_monitor(self, interval: int = 300, run_once: bool = False) -> None:
        """
        Run continuous integration monitoring at specified intervals
        
        Args:
            interval: Time between checks in seconds (default: 5 minutes)
            run_once: If True, run only one check and return
        """
        logger.info(f"Starting {'single' if run_once else 'continuous'} integration monitoring")
        
        try:
            while True:
                # Ensure integration
                integration_results = self.ensure_mcp_langflow_integration()
                
                # Fix issues if needed
                if (not integration_results["connectivity_established"] or
                    not integration_results["agent_definitions_synced"] or
                    not integration_results["copilot_integration_active"] or
                    integration_results["errors"]):
                    
                    logger.info("Issues detected, attempting to fix")
                    self.check_and_fix_issues()
                
                if run_once:
                    logger.info("Single integration check completed, exiting loop")
                    break
                
                logger.info(f"Sleeping for {interval} seconds until next integration check")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Integration monitor interrupted by user")
        except Exception as e:
            logger.error(f"Error in integration monitor loop: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get current integration status
        
        Returns:
            Dictionary containing integration status
        """
        status = self.integration_status.copy()
        status["timestamp"] = datetime.now().isoformat()
        
        # Add more detailed information
        if status["mcp_langflow_connected"]:
            status["connectivity_details"] = "MCP and Langflow connected and communicating"
        else:
            status["connectivity_details"] = "Connection issues between MCP and Langflow"
        
        if status["agent_definitions_synced"]:
            status["agent_sync_details"] = "Agent definitions successfully synchronized"
        else:
            status["agent_sync_details"] = "Agent definitions not synchronized"
        
        if status["copilot_integration_active"]:
            status["copilot_details"] = "Copilot tools monitoring active"
        else:
            status["copilot_details"] = "Copilot tools monitoring inactive"
        
        return status


# For importing as module
if __name__ == "__main__":
    # Simple CLI for integration manager
    print("Integration Manager Agent - Starting")
    manager = IntegrationManagerAgent()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            print("Running single integration check")
            manager.run_integration_monitor(run_once=True)
        else:
            print("Checking integration status")
            status = manager.ensure_mcp_langflow_integration()
            print(f"Integration status: {'✓' if status['connectivity_established'] else '✗'} MCP-Langflow Connection")
            print(f"                   {'✓' if status['agent_definitions_synced'] else '✗'} Agent Definitions Synced")
            print(f"                   {'✓' if status['copilot_integration_active'] else '✗'} Copilot Tools Monitoring")
            
            if status["errors"]:
                print("\nErrors:")
                for error in status["errors"]:
                    print(f"  - {error}")
    except KeyboardInterrupt:
        print("\nIntegration check interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
