#!/usr/bin/env python3
"""
NoxSuite Docker Management Component for Langflow
Custom component for managing Docker containers within Langflow workflows
"""
from typing import Optional, Dict, Any, List
from langflow.custom import CustomComponent
from langflow.field_typing import Text, DropDown, Data
import docker
import json
from datetime import datetime

class NoxSuiteDockerManager(CustomComponent):
    display_name = "NoxSuite Docker Manager"
    description = "Manage NoxSuite Docker containers with health monitoring and auto-recovery"
    icon = "🐳"
    
    inputs = [
        DropDown(
            name="action",
            display_name="Action",
            options=["status", "restart", "logs", "health_check", "auto_heal"],
            value="status",
            info="Choose the Docker management action to perform"
        ),
        Text(
            name="container_filter",
            display_name="Container Filter",
            value="noxsuite",
            info="Filter containers by name pattern (default: noxsuite)"
        ),
        Text(
            name="log_lines",
            display_name="Log Lines",
            value="50",
            info="Number of log lines to retrieve (for logs action)"
        )
    ]
    
    outputs = [
        Data(name="result", display_name="Docker Management Result"),
        Text(name="status", display_name="Operation Status"),
        Text(name="message", display_name="Status Message")
    ]
    
    def build(
        self,
        action: str,
        container_filter: str = "noxsuite",
        log_lines: str = "50"
    ) -> Dict[str, Any]:
        """Execute Docker management operations"""
        try:
            client = docker.from_env()
            result = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "container_filter": container_filter,
                "containers": []
            }
            
            # Get filtered containers
            containers = client.containers.list(all=True)
            filtered_containers = [c for c in containers if container_filter in c.name]
            
            if action == "status":
                for container in filtered_containers:
                    result["containers"].append({
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "ports": container.ports,
                        "created": container.attrs.get("Created", "unknown")
                    })
                
                status = "success"
                message = f"Retrieved status for {len(filtered_containers)} containers"
                
            elif action == "restart":
                restarted = []
                for container in filtered_containers:
                    if container.status == "running":
                        container.restart()
                        restarted.append(container.name)
                
                result["restarted_containers"] = restarted
                status = "success"
                message = f"Restarted {len(restarted)} containers"
                
            elif action == "logs":
                log_data = {}
                for container in filtered_containers:
                    try:
                        logs = container.logs(tail=int(log_lines)).decode('utf-8')
                        log_data[container.name] = logs.split('\n')[-int(log_lines):]
                    except Exception as e:
                        log_data[container.name] = [f"Error retrieving logs: {str(e)}"]
                
                result["logs"] = log_data
                status = "success"
                message = f"Retrieved logs for {len(filtered_containers)} containers"
                
            elif action == "health_check":
                health_status = {}
                for container in filtered_containers:
                    try:
                        # Check if container is running
                        if container.status == "running":
                            # Try to get health status from inspect
                            inspect_data = container.attrs
                            health = inspect_data.get("State", {}).get("Health", {})
                            if health:
                                health_status[container.name] = health.get("Status", "unknown")
                            else:
                                health_status[container.name] = "no_healthcheck"
                        else:
                            health_status[container.name] = container.status
                    except Exception as e:
                        health_status[container.name] = f"error: {str(e)}"
                
                result["health_status"] = health_status
                status = "success"
                message = f"Health check completed for {len(filtered_containers)} containers"
                
            elif action == "auto_heal":
                healed = []
                for container in filtered_containers:
                    if container.status in ["exited", "dead", "created"]:
                        try:
                            container.start()
                            healed.append(container.name)
                        except Exception as e:
                            result.setdefault("errors", []).append(f"{container.name}: {str(e)}")
                
                result["healed_containers"] = healed
                status = "success" if healed else "no_action_needed"
                message = f"Auto-healed {len(healed)} containers" if healed else "No containers needed healing"
            
            else:
                status = "error"
                message = f"Unknown action: {action}"
                result["error"] = message
            
            return {
                "result": result,
                "status": status,
                "message": message
            }
            
        except docker.errors.DockerException as e:
            error_msg = f"Docker error: {str(e)}"
            return {
                "result": {"error": error_msg, "timestamp": datetime.now().isoformat()},
                "status": "error",
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            return {
                "result": {"error": error_msg, "timestamp": datetime.now().isoformat()},
                "status": "error", 
                "message": error_msg
            }
