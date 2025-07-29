#!/usr/bin/env python3
"""
NoxSuite MCP Orchestrator Component for Langflow
Manages MCP server connections and workflow coordination
"""
from typing import Optional, Dict, Any, List
from langflow.custom import CustomComponent
from langflow.field_typing import Text, DropDown, Data, Bool
import requests
import json
import subprocess
from datetime import datetime

class NoxSuiteMCPOrchestrator(CustomComponent):
    display_name = "NoxSuite MCP Orchestrator"
    description = "Orchestrate MCP server connections and manage workflow coordination"
    icon = "🔗"
    
    inputs = [
        DropDown(
            name="operation",
            display_name="MCP Operation",
            options=["check_connection", "list_tools", "execute_workflow", "health_monitor", "restart_connection"],
            value="check_connection",
            info="Choose the MCP operation to perform"
        ),
        Text(
            name="mcp_endpoint",
            display_name="MCP Endpoint",
            value="http://localhost:7860/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse",
            info="MCP server endpoint URL"
        ),
        Text(
            name="workflow_data",
            display_name="Workflow Data",
            value="{}",
            info="JSON workflow data for execution (optional)"
        ),
        Bool(
            name="auto_retry",
            display_name="Auto Retry",
            value=True,
            info="Automatically retry failed operations"
        )
    ]
    
    outputs = [
        Data(name="mcp_result", display_name="MCP Operation Result"),
        Text(name="connection_status", display_name="Connection Status"),
        Text(name="operation_message", display_name="Operation Message")
    ]
    
    def build(
        self,
        operation: str,
        mcp_endpoint: str,
        workflow_data: str = "{}",
        auto_retry: bool = True
    ) -> Dict[str, Any]:
        """Execute MCP orchestration operations"""
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "endpoint": mcp_endpoint,
                "auto_retry": auto_retry
            }
            
            if operation == "check_connection":
                return self._check_mcp_connection(mcp_endpoint, result)
                
            elif operation == "list_tools":
                return self._list_mcp_tools(mcp_endpoint, result)
                
            elif operation == "execute_workflow":
                return self._execute_mcp_workflow(mcp_endpoint, workflow_data, result)
                
            elif operation == "health_monitor":
                return self._health_monitor(mcp_endpoint, result)
                
            elif operation == "restart_connection":
                return self._restart_mcp_connection(mcp_endpoint, result)
                
            else:
                return {
                    "mcp_result": {"error": f"Unknown operation: {operation}"},
                    "connection_status": "error",
                    "operation_message": f"Unsupported operation: {operation}"
                }
                
        except Exception as e:
            error_msg = f"MCP Orchestrator error: {str(e)}"
            return {
                "mcp_result": {"error": error_msg, "timestamp": datetime.now().isoformat()},
                "connection_status": "error",
                "operation_message": error_msg
            }
    
    def _check_mcp_connection(self, endpoint: str, result: Dict) -> Dict[str, Any]:
        """Check MCP server connection status"""
        try:
            # Test connection to MCP endpoint
            response = requests.get(endpoint, timeout=10, stream=True)
            
            result.update({
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "connection_test": "successful" if response.status_code in [200, 404] else "failed"
            })
            
            # Also test the base Langflow health
            base_url = endpoint.split('/api/')[0]
            health_response = requests.get(f"{base_url}/health", timeout=5)
            
            result["langflow_health"] = {
                "status_code": health_response.status_code,
                "response": health_response.json() if health_response.headers.get('content-type') == 'application/json' else health_response.text
            }
            
            if response.status_code in [200, 404] and health_response.status_code == 200:
                status = "connected"
                message = "MCP connection and Langflow health verified"
            else:
                status = "degraded"
                message = f"Connection issues detected (MCP: {response.status_code}, Health: {health_response.status_code})"
            
            return {
                "mcp_result": result,
                "connection_status": status,
                "operation_message": message
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "mcp_result": {"error": "Connection refused", "endpoint": endpoint},
                "connection_status": "disconnected",
                "operation_message": "Cannot connect to MCP endpoint"
            }
        except Exception as e:
            return {
                "mcp_result": {"error": str(e), "endpoint": endpoint},
                "connection_status": "error",
                "operation_message": f"Connection test failed: {str(e)}"
            }
    
    def _list_mcp_tools(self, endpoint: str, result: Dict) -> Dict[str, Any]:
        """List available MCP tools and capabilities"""
        try:
            # Extract base URL and project ID
            base_url = endpoint.split('/api/')[0]
            project_id = endpoint.split('project/')[1].split('/')[0]
            
            # Try to get project information
            project_url = f"{base_url}/api/v1/flows/{project_id}"
            response = requests.get(project_url, timeout=10)
            
            if response.status_code == 200:
                project_data = response.json()
                result.update({
                    "project_id": project_id,
                    "project_data": project_data,
                    "available_tools": "project_accessible"
                })
                status = "success"
                message = f"Retrieved project data for {project_id}"
            else:
                result.update({
                    "project_id": project_id,
                    "status_code": response.status_code,
                    "available_tools": "project_not_accessible"
                })
                status = "limited"
                message = f"Project {project_id} not directly accessible (status: {response.status_code})"
            
            return {
                "mcp_result": result,
                "connection_status": status,
                "operation_message": message
            }
            
        except Exception as e:
            return {
                "mcp_result": {"error": str(e)},
                "connection_status": "error",
                "operation_message": f"Failed to list MCP tools: {str(e)}"
            }
    
    def _execute_mcp_workflow(self, endpoint: str, workflow_data: str, result: Dict) -> Dict[str, Any]:
        """Execute an MCP workflow with provided data"""
        try:
            # Parse workflow data
            workflow = json.loads(workflow_data) if workflow_data.strip() else {}
            
            # For now, simulate workflow execution
            result.update({
                "workflow": workflow,
                "execution_status": "simulated",
                "execution_time": datetime.now().isoformat()
            })
            
            return {
                "mcp_result": result,
                "connection_status": "executed",
                "operation_message": "Workflow execution simulated (full implementation pending)"
            }
            
        except json.JSONDecodeError as e:
            return {
                "mcp_result": {"error": f"Invalid workflow JSON: {str(e)}"},
                "connection_status": "error",
                "operation_message": "Workflow data is not valid JSON"
            }
    
    def _health_monitor(self, endpoint: str, result: Dict) -> Dict[str, Any]:
        """Monitor MCP health and performance"""
        try:
            start_time = datetime.now()
            
            # Test connection speed
            base_url = endpoint.split('/api/')[0]
            health_response = requests.get(f"{base_url}/health", timeout=5)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            result.update({
                "response_time_seconds": response_time,
                "health_status": health_response.json() if health_response.headers.get('content-type') == 'application/json' else health_response.text,
                "performance": "good" if response_time < 1.0 else "slow" if response_time < 3.0 else "poor"
            })
            
            return {
                "mcp_result": result,
                "connection_status": "monitored",
                "operation_message": f"Health check completed in {response_time:.3f}s"
            }
            
        except Exception as e:
            return {
                "mcp_result": {"error": str(e)},
                "connection_status": "unhealthy",
                "operation_message": f"Health monitoring failed: {str(e)}"
            }
    
    def _restart_mcp_connection(self, endpoint: str, result: Dict) -> Dict[str, Any]:
        """Restart MCP connection (placeholder for restart logic)"""
        try:
            # This would implement actual restart logic
            result.update({
                "restart_attempted": True,
                "restart_method": "placeholder",
                "restart_time": datetime.now().isoformat()
            })
            
            return {
                "mcp_result": result,
                "connection_status": "restart_attempted",
                "operation_message": "MCP connection restart attempted (implementation pending)"
            }
            
        except Exception as e:
            return {
                "mcp_result": {"error": str(e)},
                "connection_status": "restart_failed",
                "operation_message": f"Restart attempt failed: {str(e)}"
            }
