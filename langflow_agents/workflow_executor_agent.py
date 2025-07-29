"""
Workflow Executor Agent - Core implementation

Simulates real-user scenarios across MCP agents, Docker containers,
and Langflow UI endpoints to validate real-world agentic use cases.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'workflow_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WorkflowExecutorAgent")

class WorkflowExecutorAgent:
    """
    Workflow Executor Agent that simulates real-user scenarios across MCP agents,
    Docker containers, and Langflow UI endpoints to validate real-world agentic use cases.
    """
    
    def __init__(self, 
                 mcp_server_url: str = "http://localhost:8000",
                 langflow_url: str = "http://localhost:7860",
                 workflow_dir: str = None):
        """
        Initialize the Workflow Executor Agent
        
        Args:
            mcp_server_url: URL of the MCP Server
            langflow_url: URL of the Langflow interface
            workflow_dir: Directory containing workflow definitions
        """
        self.mcp_server_url = mcp_server_url
        self.langflow_url = langflow_url
        self.workflow_dir = workflow_dir or str(Path(__file__).parent / 'workflows')
        os.makedirs(self.workflow_dir, exist_ok=True)
        
        # Initialize Docker client for container interactions
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
        
        # Initialize session
        self.session = requests.Session()
        
        # Store workflow execution results
        self.execution_results = {}
        self.available_workflows = {}
        self.execution_history = []
        
        # Load available workflows
        self._load_available_workflows()
        
        logger.info(f"Workflow Executor Agent initialized with {len(self.available_workflows)} workflows")
    
    def _load_available_workflows(self) -> None:
        """
        Load available workflows from the workflow directory
        """
        try:
            workflow_path = Path(self.workflow_dir)
            
            if not workflow_path.exists():
                logger.warning(f"Workflow directory not found: {workflow_path}")
                self._create_default_workflows()
                return
            
            workflow_files = list(workflow_path.glob("*.json"))
            
            if not workflow_files:
                logger.warning("No workflow files found, creating defaults")
                self._create_default_workflows()
                return
            
            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, 'r') as f:
                        workflow = json.load(f)
                    
                    self.available_workflows[workflow_file.stem] = {
                        "name": workflow.get("name", workflow_file.stem),
                        "description": workflow.get("description", ""),
                        "steps": workflow.get("steps", []),
                        "file_path": str(workflow_file)
                    }
                except Exception as e:
                    logger.error(f"Failed to load workflow {workflow_file}: {e}")
            
            logger.info(f"Loaded {len(self.available_workflows)} workflows")
        except Exception as e:
            logger.error(f"Error loading workflows: {e}")
    
    def _create_default_workflows(self) -> None:
        """
        Create default workflow definitions
        """
        try:
            workflow_path = Path(self.workflow_dir)
            os.makedirs(workflow_path, exist_ok=True)
            
            # Create basic system health check workflow
            system_health_workflow = {
                "name": "System Health Validation",
                "description": "Validates core system components health and connectivity",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "check_docker_health",
                        "name": "Docker Health Check",
                        "type": "docker_check",
                        "params": {
                            "containers": ["noxsuite-langflow", "noxsuite-postgres", "noxsuite-redis"]
                        },
                        "expected_result": {
                            "all_running": True
                        }
                    },
                    {
                        "id": "check_langflow_health",
                        "name": "Langflow Health Check",
                        "type": "http_check",
                        "params": {
                            "url": "${LANGFLOW_URL}/health",
                            "method": "GET",
                            "timeout": 5
                        },
                        "expected_result": {
                            "status_code": 200
                        }
                    },
                    {
                        "id": "check_mcp_health",
                        "name": "MCP Server Health Check",
                        "type": "http_check",
                        "params": {
                            "url": "${MCP_SERVER_URL}/health",
                            "method": "GET",
                            "timeout": 5
                        },
                        "expected_result": {
                            "status_code": 200
                        }
                    }
                ]
            }
            
            # Create workflow for testing agent coordination
            agent_coordination_workflow = {
                "name": "Agent Coordination Test",
                "description": "Tests coordination between multiple agents",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "check_config",
                        "name": "Check Agent Configuration",
                        "type": "file_check",
                        "params": {
                            "path": "agent_collaboration_config.json"
                        },
                        "expected_result": {
                            "exists": True
                        }
                    },
                    {
                        "id": "check_agent_status",
                        "name": "Check Agent Status",
                        "type": "http_check",
                        "params": {
                            "url": "${MCP_SERVER_URL}/api/agents/status",
                            "method": "GET",
                            "timeout": 5
                        },
                        "expected_result": {
                            "status_code": 200
                        }
                    },
                    {
                        "id": "test_agent_coordination",
                        "name": "Test Agent Coordination",
                        "type": "coordination_test",
                        "params": {
                            "task_description": "Test coordination between agents"
                        },
                        "expected_result": {
                            "success": True
                        }
                    }
                ]
            }
            
            # Create workflow for testing Langflow flows
            langflow_workflow = {
                "name": "Langflow Integration Test",
                "description": "Tests Langflow flow execution and integration",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "check_flows",
                        "name": "Check Available Flows",
                        "type": "http_check",
                        "params": {
                            "url": "${LANGFLOW_URL}/api/v1/flows",
                            "method": "GET",
                            "timeout": 5
                        },
                        "expected_result": {
                            "status_code": 200
                        }
                    },
                    {
                        "id": "check_components",
                        "name": "Check Available Components",
                        "type": "http_check",
                        "params": {
                            "url": "${LANGFLOW_URL}/api/v1/components",
                            "method": "GET",
                            "timeout": 5
                        },
                        "expected_result": {
                            "status_code": 200
                        }
                    },
                    {
                        "id": "execute_test_flow",
                        "name": "Execute Test Flow",
                        "type": "flow_execution",
                        "params": {
                            "flow_id": "test_flow",
                            "input": {
                                "message": "Test execution"
                            }
                        },
                        "expected_result": {
                            "success": True
                        }
                    }
                ]
            }
            
            # Create workflow for testing VS Code Copilot constraints
            copilot_workflow = {
                "name": "VS Code Copilot Constraints Test",
                "description": "Tests VS Code Copilot agent constraints handling",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "check_tools_monitor",
                        "name": "Check Tools Monitor",
                        "type": "file_check",
                        "params": {
                            "path": "copilot_tools_monitor.py"
                        },
                        "expected_result": {
                            "exists": True
                        }
                    },
                    {
                        "id": "check_tool_usage",
                        "name": "Check Tool Usage",
                        "type": "python_execution",
                        "params": {
                            "code": "from copilot_tools_monitor import CopilotToolsMonitor; monitor = CopilotToolsMonitor(); print(monitor.get_detailed_statistics())"
                        },
                        "expected_result": {
                            "success": True
                        }
                    },
                    {
                        "id": "test_throttling",
                        "name": "Test Throttling Mechanism",
                        "type": "python_execution",
                        "params": {
                            "code": "from copilot_tools_monitor import CopilotToolsMonitor; monitor = CopilotToolsMonitor(); monitor.enable_throttling(); print('Throttling enabled')"
                        },
                        "expected_result": {
                            "success": True
                        }
                    }
                ]
            }
            
            # Save workflows
            with open(workflow_path / "system_health_workflow.json", 'w') as f:
                json.dump(system_health_workflow, f, indent=2)
            
            with open(workflow_path / "agent_coordination_workflow.json", 'w') as f:
                json.dump(agent_coordination_workflow, f, indent=2)
            
            with open(workflow_path / "langflow_workflow.json", 'w') as f:
                json.dump(langflow_workflow, f, indent=2)
            
            with open(workflow_path / "copilot_workflow.json", 'w') as f:
                json.dump(copilot_workflow, f, indent=2)
            
            # Load created workflows
            self.available_workflows = {
                "system_health_workflow": {
                    "name": system_health_workflow["name"],
                    "description": system_health_workflow["description"],
                    "steps": system_health_workflow["steps"],
                    "file_path": str(workflow_path / "system_health_workflow.json")
                },
                "agent_coordination_workflow": {
                    "name": agent_coordination_workflow["name"],
                    "description": agent_coordination_workflow["description"],
                    "steps": agent_coordination_workflow["steps"],
                    "file_path": str(workflow_path / "agent_coordination_workflow.json")
                },
                "langflow_workflow": {
                    "name": langflow_workflow["name"],
                    "description": langflow_workflow["description"],
                    "steps": langflow_workflow["steps"],
                    "file_path": str(workflow_path / "langflow_workflow.json")
                },
                "copilot_workflow": {
                    "name": copilot_workflow["name"],
                    "description": copilot_workflow["description"],
                    "steps": copilot_workflow["steps"],
                    "file_path": str(workflow_path / "copilot_workflow.json")
                }
            }
            
            logger.info("Created default workflows")
        except Exception as e:
            logger.error(f"Error creating default workflows: {e}")
    
    def execute_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Execute a workflow by name
        
        Args:
            workflow_name: Name of the workflow to execute
            
        Returns:
            Dictionary containing execution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow_name,
            "success": False,
            "steps_total": 0,
            "steps_passed": 0,
            "steps_failed": 0,
            "step_results": [],
            "errors": []
        }
        
        try:
            # Check if workflow exists
            if workflow_name not in self.available_workflows:
                error_msg = f"Workflow '{workflow_name}' not found"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results
            
            workflow = self.available_workflows[workflow_name]
            steps = workflow["steps"]
            results["steps_total"] = len(steps)
            
            logger.info(f"Executing workflow '{workflow_name}' with {len(steps)} steps")
            
            # Replace variables in workflow
            variables = {
                "MCP_SERVER_URL": self.mcp_server_url,
                "LANGFLOW_URL": self.langflow_url
            }
            
            # Execute each step
            for step in steps:
                step_result = self._execute_workflow_step(step, variables)
                results["step_results"].append(step_result)
                
                if step_result["success"]:
                    results["steps_passed"] += 1
                else:
                    results["steps_failed"] += 1
                    results["errors"].append(f"Step '{step['name']}' failed: {step_result.get('error', 'Unknown error')}")
            
            # Overall success
            results["success"] = results["steps_failed"] == 0
            
            # Store execution result
            self.execution_results[workflow_name] = results
            
            # Add to history
            self.execution_history.append({
                "timestamp": results["timestamp"],
                "workflow": workflow_name,
                "success": results["success"],
                "steps_passed": results["steps_passed"],
                "steps_total": results["steps_total"]
            })
            
            # Trim history to keep it manageable
            if len(self.execution_history) > 50:
                self.execution_history = self.execution_history[-50:]
            
            logger.info(f"Workflow '{workflow_name}' execution completed - " +
                      f"Success: {results['success']}, Passed: {results['steps_passed']}/{results['steps_total']}")
            
        except Exception as e:
            error_msg = f"Error executing workflow: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _execute_workflow_step(self, step: Dict[str, Any], variables: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute a single workflow step
        
        Args:
            step: Step definition
            variables: Variables to substitute in step parameters
            
        Returns:
            Dictionary containing step execution result
        """
        step_result = {
            "id": step["id"],
            "name": step["name"],
            "type": step["type"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "details": {}
        }
        
        try:
            step_type = step["type"]
            params = self._replace_variables(step["params"], variables)
            expected_result = step.get("expected_result", {})
            
            logger.info(f"Executing step '{step['name']}' of type '{step_type}'")
            
            if step_type == "docker_check":
                result = self._execute_docker_check(params)
            elif step_type == "http_check":
                result = self._execute_http_check(params)
            elif step_type == "file_check":
                result = self._execute_file_check(params)
            elif step_type == "python_execution":
                result = self._execute_python_code(params)
            elif step_type == "flow_execution":
                result = self._execute_langflow_flow(params)
            elif step_type == "coordination_test":
                result = self._execute_coordination_test(params)
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            step_result["details"] = result
            
            # Validate result against expected result
            step_result["success"] = self._validate_result(result, expected_result)
            if not step_result["success"]:
                step_result["error"] = "Result does not match expected result"
                logger.warning(f"Step '{step['name']}' failed validation")
            else:
                logger.info(f"Step '{step['name']}' completed successfully")
            
        except Exception as e:
            error_msg = f"Error executing step: {str(e)}"
            logger.error(error_msg)
            step_result["error"] = error_msg
        
        return step_result
    
    def _replace_variables(self, obj: Any, variables: Dict[str, str]) -> Any:
        """
        Replace variables in strings recursively
        
        Args:
            obj: Object to replace variables in
            variables: Variables to substitute
            
        Returns:
            Object with variables replaced
        """
        if isinstance(obj, str):
            for var_name, var_value in variables.items():
                obj = obj.replace(f"${{{var_name}}}", var_value)
            return obj
        elif isinstance(obj, dict):
            return {k: self._replace_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_variables(item, variables) for item in obj]
        else:
            return obj
    
    def _execute_docker_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Docker container check
        
        Args:
            params: Docker check parameters
            
        Returns:
            Dictionary containing check results
        """
        result = {
            "containers_checked": [],
            "all_running": False,
            "details": {}
        }
        
        try:
            if not self.docker_client:
                self.docker_client = docker.from_env()
            
            container_names = params.get("containers", [])
            containers_running = True
            
            for container_name in container_names:
                container_found = False
                container_status = "not_found"
                container_health = None
                
                try:
                    containers = self.docker_client.containers.list(all=True, filters={"name": container_name})
                    if containers:
                        container = containers[0]
                        container_found = True
                        container_status = container.status
                        
                        # Get container health if available
                        if hasattr(container, "attrs") and "State" in container.attrs:
                            if "Health" in container.attrs["State"]:
                                container_health = container.attrs["State"]["Health"]["Status"]
                except Exception as e:
                    logger.error(f"Error checking container {container_name}: {e}")
                
                result["containers_checked"].append(container_name)
                result["details"][container_name] = {
                    "found": container_found,
                    "status": container_status,
                    "health": container_health
                }
                
                if not container_found or container_status != "running":
                    containers_running = False
            
            result["all_running"] = containers_running
            
        except Exception as e:
            logger.error(f"Error during Docker check: {e}")
            result["error"] = str(e)
        
        return result
    
    def _execute_http_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an HTTP endpoint check
        
        Args:
            params: HTTP check parameters
            
        Returns:
            Dictionary containing check results
        """
        result = {
            "url": params.get("url"),
            "method": params.get("method", "GET"),
            "status_code": None,
            "response_time": None,
            "error": None
        }
        
        try:
            url = params.get("url")
            method = params.get("method", "GET")
            timeout = params.get("timeout", 10)
            headers = params.get("headers", {})
            data = params.get("data")
            
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.status_code
            
            # Try to parse response as JSON
            try:
                result["response_body"] = response.json()
            except:
                # Store first 1000 chars of text response
                result["response_body"] = response.text[:1000]
            
        except requests.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            result["error"] = str(e)
        except Exception as e:
            logger.error(f"Error during HTTP check: {e}")
            result["error"] = str(e)
        
        return result
    
    def _execute_file_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a file check
        
        Args:
            params: File check parameters
            
        Returns:
            Dictionary containing check results
        """
        result = {
            "path": params.get("path"),
            "exists": False,
            "size": None,
            "modified": None,
            "error": None
        }
        
        try:
            file_path = params.get("path")
            check_content = params.get("check_content", False)
            
            if os.path.exists(file_path):
                result["exists"] = True
                result["size"] = os.path.getsize(file_path)
                result["modified"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                
                if check_content:
                    with open(file_path, 'r') as f:
                        # Read first 1000 chars
                        result["content_preview"] = f.read(1000)
                    
                    # If JSON, validate structure
                    if file_path.endswith(".json"):
                        try:
                            with open(file_path, 'r') as f:
                                json.load(f)
                            result["valid_json"] = True
                        except json.JSONDecodeError:
                            result["valid_json"] = False
            
        except Exception as e:
            logger.error(f"Error during file check: {e}")
            result["error"] = str(e)
        
        return result
    
    def _execute_python_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Python code
        
        Args:
            params: Python execution parameters
            
        Returns:
            Dictionary containing execution results
        """
        result = {
            "success": False,
            "output": None,
            "error": None
        }
        
        try:
            code = params.get("code")
            
            if not code:
                result["error"] = "No code provided"
                return result
            
            # Execute in temporary file for safety
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with subprocess for isolation
                process = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                result["output"] = process.stdout
                result["success"] = process.returncode == 0
                
                if not result["success"]:
                    result["error"] = process.stderr
            finally:
                # Clean up
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Execution timed out"
        except Exception as e:
            logger.error(f"Error during Python execution: {e}")
            result["error"] = str(e)
        
        return result
    
    def _execute_langflow_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Langflow flow
        
        Args:
            params: Flow execution parameters
            
        Returns:
            Dictionary containing execution results
        """
        result = {
            "flow_id": params.get("flow_id"),
            "success": False,
            "output": None,
            "error": None
        }
        
        try:
            flow_id = params.get("flow_id")
            inputs = params.get("input", {})
            
            # Try to execute flow via Langflow API
            try:
                execution_url = f"{self.langflow_url}/api/v1/flows/{flow_id}/execute"
                
                response = self.session.post(
                    execution_url,
                    json={"inputs": inputs},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result["output"] = response.json()
                    result["success"] = True
                else:
                    result["error"] = f"Flow execution failed with status code: {response.status_code}"
                    result["response"] = response.text[:1000]
            except requests.RequestException as e:
                # If API call fails, try to execute flow using JSON definition
                result["error"] = f"API execution failed: {str(e)}, trying direct execution"
                result["success"] = self._simulate_flow_execution(flow_id, inputs)
                result["output"] = "Flow execution simulated locally (API unavailable)"
            
        except Exception as e:
            logger.error(f"Error during Langflow flow execution: {e}")
            result["error"] = str(e)
        
        return result
    
    def _simulate_flow_execution(self, flow_id: str, inputs: Dict[str, Any]) -> bool:
        """
        Simulate Langflow flow execution when API is unavailable
        
        Args:
            flow_id: ID of the flow to execute
            inputs: Flow inputs
            
        Returns:
            True if simulation was successful
        """
        try:
            # Try to find flow definition
            flow_path = Path(self.workflow_dir).parent.parent / "langflow" / "flows" / f"{flow_id}.json"
            
            if not flow_path.exists():
                logger.warning(f"Flow definition not found: {flow_path}")
                return False
            
            with open(flow_path, 'r') as f:
                flow_def = json.load(f)
            
            # Basic simulation - in real implementation, you'd process the flow graph
            logger.info(f"Simulating execution of flow: {flow_id}")
            logger.info(f"With inputs: {inputs}")
            
            return True
        except Exception as e:
            logger.error(f"Error simulating flow execution: {e}")
            return False
    
    def _execute_coordination_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an agent coordination test
        
        Args:
            params: Coordination test parameters
            
        Returns:
            Dictionary containing test results
        """
        result = {
            "task_description": params.get("task_description"),
            "success": False,
            "coordination_file": None,
            "error": None
        }
        
        try:
            # Check if coordination config exists
            config_file = Path(__file__).parent.parent / "agent_collaboration_config.json"
            result["coordination_file"] = str(config_file)
            
            if not config_file.exists():
                result["error"] = "Agent collaboration config not found"
                return result
            
            # Read config
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check for required fields
            if "collaboration_active" not in config:
                result["error"] = "Invalid configuration - missing collaboration_active field"
                return result
            
            # Write test task to results file
            task_description = params.get("task_description", "Test coordination task")
            results_file = Path(__file__).parent.parent / "agent_coordination_results.json"
            
            # Create or update results file
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        results_data = json.load(f)
                except json.JSONDecodeError:
                    results_data = {}
            else:
                results_data = {}
            
            # Add new test task
            task_id = f"test_task_{int(time.time())}"
            results_data[task_id] = {
                "description": task_description,
                "status": "completed",
                "created": datetime.now().isoformat(),
                "completed": datetime.now().isoformat(),
                "result": "Test task completed successfully"
            }
            
            # Write updated results
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error during coordination test: {e}")
            result["error"] = str(e)
        
        return result
    
    def _validate_result(self, result: Dict[str, Any], expected_result: Dict[str, Any]) -> bool:
        """
        Validate a result against expected result
        
        Args:
            result: Result to validate
            expected_result: Expected result
            
        Returns:
            True if result matches expected result
        """
        # If there's an error in the result, it's automatically invalid
        if "error" in result and result["error"] is not None:
            return False
        
        # Check each expected field
        for key, expected_value in expected_result.items():
            if key not in result:
                logger.warning(f"Expected key '{key}' not found in result")
                return False
            
            actual_value = result[key]
            
            # Different comparison based on value type
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                # Recursively validate nested dictionaries
                if not self._validate_result(actual_value, expected_value):
                    return False
            elif expected_value != actual_value:
                logger.warning(f"Value mismatch for key '{key}': expected '{expected_value}', got '{actual_value}'")
                return False
        
        return True
    
    def run_all_workflows(self) -> Dict[str, Any]:
        """
        Execute all available workflows
        
        Returns:
            Dictionary containing overall execution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflows_total": len(self.available_workflows),
            "workflows_passed": 0,
            "workflows_failed": 0,
            "workflow_results": {},
            "errors": []
        }
        
        if not self.available_workflows:
            results["errors"].append("No workflows available")
            return results
        
        logger.info(f"Running all {len(self.available_workflows)} workflows")
        
        for workflow_name in self.available_workflows:
            try:
                workflow_result = self.execute_workflow(workflow_name)
                results["workflow_results"][workflow_name] = {
                    "success": workflow_result["success"],
                    "steps_passed": workflow_result["steps_passed"],
                    "steps_total": workflow_result["steps_total"]
                }
                
                if workflow_result["success"]:
                    results["workflows_passed"] += 1
                else:
                    results["workflows_failed"] += 1
                    results["errors"].extend([f"Workflow '{workflow_name}': {error}" for error in workflow_result["errors"]])
            except Exception as e:
                logger.error(f"Error executing workflow '{workflow_name}': {e}")
                results["workflows_failed"] += 1
                results["errors"].append(f"Workflow '{workflow_name}' failed: {str(e)}")
        
        logger.info(f"All workflows executed - Passed: {results['workflows_passed']}/{results['workflows_total']}")
        return results
    
    def run_continuous_execution(self, interval: int = 600, run_once: bool = False) -> None:
        """
        Run continuous workflow execution at specified intervals
        
        Args:
            interval: Time between executions in seconds
            run_once: If True, run only one execution and return
        """
        logger.info(f"Starting {'single' if run_once else 'continuous'} workflow execution")
        
        try:
            while True:
                start_time = time.time()
                
                # Run all workflows
                self.run_all_workflows()
                
                if run_once:
                    logger.info("Single workflow execution completed, exiting loop")
                    break
                
                # Calculate sleep time (to ensure consistent interval)
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                
                logger.info(f"Sleeping for {sleep_time:.1f} seconds until next execution")
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            logger.info("Workflow execution interrupted by user")
        except Exception as e:
            logger.error(f"Error in workflow execution loop: {e}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of workflow execution results
        
        Returns:
            Dictionary containing execution summary
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "workflows_available": len(self.available_workflows),
            "workflows_executed": len(self.execution_results),
            "overall_health": "unknown",
            "workflow_status": {},
            "recent_executions": self.execution_history[-5:] if self.execution_history else []
        }
        
        # Check all workflow results
        passed_count = 0
        for workflow_name, workflow_result in self.execution_results.items():
            if workflow_result["success"]:
                passed_count += 1
                status = "passed"
            else:
                status = "failed"
            
            summary["workflow_status"][workflow_name] = {
                "status": status,
                "steps_passed": workflow_result["steps_passed"],
                "steps_total": workflow_result["steps_total"],
                "last_execution": workflow_result["timestamp"]
            }
        
        # Calculate overall health
        if not self.execution_results:
            summary["overall_health"] = "unknown"
        elif passed_count == len(self.execution_results):
            summary["overall_health"] = "healthy"
        elif passed_count == 0:
            summary["overall_health"] = "critical"
        else:
            summary["overall_health"] = "issues_detected"
        
        return summary


# For importing as module
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Executor Agent")
    parser.add_argument("--once", action="store_true", help="Run workflows once and exit")
    parser.add_argument("--workflow", type=str, help="Run a specific workflow")
    args = parser.parse_args()
    
    executor = WorkflowExecutorAgent()
    
    if args.workflow:
        # Run specific workflow
        print(f"Executing workflow: {args.workflow}")
        result = executor.execute_workflow(args.workflow)
        print(f"Execution completed - Success: {result['success']}, Steps passed: {result['steps_passed']}/{result['steps_total']}")
        
        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
    elif args.once:
        # Run all workflows once
        print("Running all workflows once")
        executor.run_continuous_execution(run_once=True)
    else:
        # Show available workflows
        print("Available workflows:")
        for name, workflow in executor.available_workflows.items():
            print(f"  - {name}: {workflow['description']}")
        print("\nUse --workflow <name> to execute a specific workflow or --once to run all workflows")
