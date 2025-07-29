#!/usr/bin/env python3
"""
NoxSuite Multi-Agent Coordinator for Langflow
Coordinates multiple agents with intelligent task distribution and 128-tools awareness
"""
from typing import Optional, Dict, Any, List
from langflow.custom import CustomComponent
from langflow.field_typing import Text, DropDown, Data, Bool, Number
import json
import time
from datetime import datetime
from emergency_copilot_fix import throttler

class NoxSuiteMultiAgentCoordinator(CustomComponent):
    display_name = "NoxSuite Multi-Agent Coordinator"
    description = "Coordinate multiple agents with intelligent task distribution and tool usage management"
    icon = "🤝"
    
    inputs = [
        DropDown(
            name="coordination_mode",
            display_name="Coordination Mode",
            options=["sequential", "parallel", "priority_based", "load_balanced", "emergency"],
            value="priority_based",
            info="Choose how agents should be coordinated"
        ),
        Text(
            name="agent_tasks",
            display_name="Agent Tasks (JSON)",
            value='{"docker": "health_check", "mcp": "check_connection", "monitor": "alerts"}',
            info="JSON object defining tasks for each agent"
        ),
        Number(
            name="max_concurrent_agents",
            display_name="Max Concurrent Agents",
            value=3,
            info="Maximum number of agents to run concurrently"
        ),
        Bool(
            name="tool_usage_aware",
            display_name="Tool Usage Aware",
            value=True,
            info="Consider VS Code Copilot tool usage limits in coordination"
        ),
        Number(
            name="task_timeout",
            display_name="Task Timeout (seconds)",
            value=30,
            info="Maximum time to wait for each agent task"
        )
    ]
    
    outputs = [
        Data(name="coordination_result", display_name="Coordination Result"),
        Text(name="execution_status", display_name="Execution Status"),
        Text(name="tool_usage_report", display_name="Tool Usage Report")
    ]
    
    def build(
        self,
        coordination_mode: str,
        agent_tasks: str,
        max_concurrent_agents: int = 3,
        tool_usage_aware: bool = True,
        task_timeout: int = 30
    ) -> Dict[str, Any]:
        """Execute multi-agent coordination"""
        try:
            # Parse agent tasks
            tasks = json.loads(agent_tasks)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "coordination_mode": coordination_mode,
                "agent_tasks": tasks,
                "max_concurrent": max_concurrent_agents,
                "tool_usage_aware": tool_usage_aware,
                "initial_tool_count": throttler.tool_count if tool_usage_aware else "not_tracked",
                "execution_log": []
            }
            
            if coordination_mode == "sequential":
                return self._sequential_coordination(tasks, result, tool_usage_aware, task_timeout)
                
            elif coordination_mode == "parallel":
                return self._parallel_coordination(tasks, result, max_concurrent_agents, tool_usage_aware, task_timeout)
                
            elif coordination_mode == "priority_based":
                return self._priority_based_coordination(tasks, result, tool_usage_aware, task_timeout)
                
            elif coordination_mode == "load_balanced":
                return self._load_balanced_coordination(tasks, result, max_concurrent_agents, tool_usage_aware, task_timeout)
                
            elif coordination_mode == "emergency":
                return self._emergency_coordination(tasks, result, tool_usage_aware, task_timeout)
                
            else:
                return {
                    "coordination_result": {"error": f"Unknown coordination mode: {coordination_mode}"},
                    "execution_status": "error",
                    "tool_usage_report": "Coordination failed"
                }
                
        except json.JSONDecodeError as e:
            return {
                "coordination_result": {"error": f"Invalid agent tasks JSON: {str(e)}"},
                "execution_status": "error",
                "tool_usage_report": "JSON parsing failed"
            }
        except Exception as e:
            error_msg = f"Multi-agent coordination error: {str(e)}"
            return {
                "coordination_result": {"error": error_msg, "timestamp": datetime.now().isoformat()},
                "execution_status": "error",
                "tool_usage_report": error_msg
            }
    
    def _check_tool_usage_limit(self, tool_usage_aware: bool) -> Dict[str, Any]:
        """Check if we can proceed with tool usage"""
        if not tool_usage_aware:
            return {"can_proceed": True, "reason": "tool_usage_not_tracked"}
        
        current_usage = throttler.tool_count
        remaining = 120 - current_usage
        
        if remaining < 10:
            return {
                "can_proceed": False,
                "reason": f"tool_limit_approaching",
                "current_usage": current_usage,
                "remaining": remaining
            }
        
        return {
            "can_proceed": True,
            "current_usage": current_usage,
            "remaining": remaining
        }
    
    def _execute_agent_task(self, agent_name: str, task: str, tool_usage_aware: bool) -> Dict[str, Any]:
        """Execute a single agent task with tool usage tracking"""
        start_time = datetime.now()
        
        if tool_usage_aware:
            pre_tool_count = throttler.tool_count
        
        try:
            # Simulate agent task execution
            if agent_name == "docker":
                result = self._simulate_docker_task(task)
            elif agent_name == "mcp":
                result = self._simulate_mcp_task(task)
            elif agent_name == "monitor":
                result = self._simulate_monitor_task(task)
            else:
                result = self._simulate_generic_task(agent_name, task)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            task_result = {
                "agent": agent_name,
                "task": task,
                "status": "completed",
                "execution_time": execution_time,
                "result": result
            }
            
            if tool_usage_aware:
                post_tool_count = throttler.tool_count
                task_result["tools_used"] = post_tool_count - pre_tool_count
            
            return task_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "agent": agent_name,
                "task": task,
                "status": "failed",
                "execution_time": execution_time,
                "error": str(e),
                "tools_used": 0 if not tool_usage_aware else throttler.tool_count - pre_tool_count
            }
    
    def _simulate_docker_task(self, task: str) -> Dict[str, Any]:
        """Simulate Docker agent task execution"""
        if tool_usage_aware:
            def docker_simulation():
                time.sleep(0.1)  # Simulate work
                return {
                    "task_type": "docker_operation",
                    "operation": task,
                    "containers_checked": 4,
                    "status": "healthy"
                }
            return throttler.execute_with_throttle(docker_simulation)
        else:
            time.sleep(0.1)
            return {
                "task_type": "docker_operation",
                "operation": task,
                "containers_checked": 4,
                "status": "healthy"
            }
    
    def _simulate_mcp_task(self, task: str) -> Dict[str, Any]:
        """Simulate MCP agent task execution"""
        if tool_usage_aware:
            def mcp_simulation():
                time.sleep(0.1)  # Simulate work
                return {
                    "task_type": "mcp_operation",
                    "operation": task,
                    "connection_status": "connected",
                    "response_time": 0.05
                }
            return throttler.execute_with_throttle(mcp_simulation)
        else:
            time.sleep(0.1)
            return {
                "task_type": "mcp_operation",
                "operation": task,
                "connection_status": "connected",
                "response_time": 0.05
            }
    
    def _simulate_monitor_task(self, task: str) -> Dict[str, Any]:
        """Simulate System Monitor agent task execution"""
        if tool_usage_aware:
            def monitor_simulation():
                time.sleep(0.1)  # Simulate work
                return {
                    "task_type": "monitoring_operation",
                    "operation": task,
                    "alerts_found": 0,
                    "system_status": "healthy"
                }
            return throttler.execute_with_throttle(monitor_simulation)
        else:
            time.sleep(0.1)
            return {
                "task_type": "monitoring_operation",
                "operation": task,
                "alerts_found": 0,
                "system_status": "healthy"
            }
    
    def _simulate_generic_task(self, agent_name: str, task: str) -> Dict[str, Any]:
        """Simulate generic agent task execution"""
        if tool_usage_aware:
            def generic_simulation():
                time.sleep(0.1)  # Simulate work
                return {
                    "task_type": "generic_operation",
                    "agent": agent_name,
                    "operation": task,
                    "status": "completed"
                }
            return throttler.execute_with_throttle(generic_simulation)
        else:
            time.sleep(0.1)
            return {
                "task_type": "generic_operation",
                "agent": agent_name,
                "operation": task,
                "status": "completed"
            }
    
    def _sequential_coordination(self, tasks: Dict, result: Dict, tool_usage_aware: bool, task_timeout: int) -> Dict[str, Any]:
        """Execute agent tasks sequentially"""
        for agent_name, task in tasks.items():
            # Check tool usage before each task
            usage_check = self._check_tool_usage_limit(tool_usage_aware)
            if not usage_check["can_proceed"]:
                result["execution_log"].append({
                    "agent": agent_name,
                    "task": task,
                    "status": "skipped",
                    "reason": usage_check["reason"]
                })
                continue
            
            # Execute task
            task_result = self._execute_agent_task(agent_name, task, tool_usage_aware)
            result["execution_log"].append(task_result)
            
            # Add delay between tasks
            time.sleep(1)
        
        completed_tasks = len([log for log in result["execution_log"] if log["status"] == "completed"])
        total_tasks = len(tasks)
        
        return {
            "coordination_result": result,
            "execution_status": f"sequential_completed_{completed_tasks}/{total_tasks}",
            "tool_usage_report": f"Final tool count: {throttler.tool_count}/120" if tool_usage_aware else "Tool usage not tracked"
        }
    
    def _priority_based_coordination(self, tasks: Dict, result: Dict, tool_usage_aware: bool, task_timeout: int) -> Dict[str, Any]:
        """Execute agent tasks based on priority"""
        # Define agent priorities
        priorities = {
            "monitor": 1,  # Highest priority
            "docker": 2,
            "mcp": 3,
            "system": 4
        }
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks.items(), key=lambda x: priorities.get(x[0], 5))
        
        for agent_name, task in sorted_tasks:
            usage_check = self._check_tool_usage_limit(tool_usage_aware)
            if not usage_check["can_proceed"]:
                result["execution_log"].append({
                    "agent": agent_name,
                    "task": task,
                    "status": "skipped",
                    "reason": usage_check["reason"],
                    "priority": priorities.get(agent_name, 5)
                })
                continue
            
            task_result = self._execute_agent_task(agent_name, task, tool_usage_aware)
            task_result["priority"] = priorities.get(agent_name, 5)
            result["execution_log"].append(task_result)
            
            time.sleep(0.5)  # Shorter delay for priority mode
        
        completed_tasks = len([log for log in result["execution_log"] if log["status"] == "completed"])
        
        return {
            "coordination_result": result,
            "execution_status": f"priority_completed_{completed_tasks}/{len(tasks)}",
            "tool_usage_report": f"Final tool count: {throttler.tool_count}/120" if tool_usage_aware else "Tool usage not tracked"
        }
    
    def _parallel_coordination(self, tasks: Dict, result: Dict, max_concurrent: int, tool_usage_aware: bool, task_timeout: int) -> Dict[str, Any]:
        """Simulate parallel execution (simplified)"""
        # For this simulation, we'll execute tasks in small batches
        task_items = list(tasks.items())
        batch_size = min(max_concurrent, len(task_items))
        
        for i in range(0, len(task_items), batch_size):
            batch = task_items[i:i + batch_size]
            
            # Check tool usage before batch
            usage_check = self._check_tool_usage_limit(tool_usage_aware)
            if not usage_check["can_proceed"]:
                for agent_name, task in batch:
                    result["execution_log"].append({
                        "agent": agent_name,
                        "task": task,
                        "status": "skipped",
                        "reason": usage_check["reason"]
                    })
                continue
            
            # Execute batch (simulated parallel execution)
            batch_start = datetime.now()
            for agent_name, task in batch:
                task_result = self._execute_agent_task(agent_name, task, tool_usage_aware)
                task_result["batch"] = i // batch_size + 1
                result["execution_log"].append(task_result)
            
            batch_time = (datetime.now() - batch_start).total_seconds()
            result["execution_log"].append({
                "batch_summary": f"Batch {i // batch_size + 1} completed in {batch_time:.2f}s"
            })
            
            time.sleep(0.5)  # Delay between batches
        
        completed_tasks = len([log for log in result["execution_log"] if log.get("status") == "completed"])
        
        return {
            "coordination_result": result,
            "execution_status": f"parallel_completed_{completed_tasks}/{len(tasks)}",
            "tool_usage_report": f"Final tool count: {throttler.tool_count}/120" if tool_usage_aware else "Tool usage not tracked"
        }
    
    def _load_balanced_coordination(self, tasks: Dict, result: Dict, max_concurrent: int, tool_usage_aware: bool, task_timeout: int) -> Dict[str, Any]:
        """Execute tasks with load balancing consideration"""
        # Estimate task weights
        task_weights = {
            "health_check": 1,
            "check_connection": 1,
            "alerts": 1,
            "full_system": 3,
            "restart": 2
        }
        
        # Sort by estimated load
        sorted_tasks = sorted(
            tasks.items(),
            key=lambda x: task_weights.get(x[1], 1)
        )
        
        current_load = 0
        max_load = max_concurrent * 2  # Arbitrary load limit
        
        for agent_name, task in sorted_tasks:
            task_weight = task_weights.get(task, 1)
            
            if current_load + task_weight > max_load:
                result["execution_log"].append({
                    "agent": agent_name,
                    "task": task,
                    "status": "deferred",
                    "reason": "load_limit_reached",
                    "weight": task_weight
                })
                continue
            
            usage_check = self._check_tool_usage_limit(tool_usage_aware)
            if not usage_check["can_proceed"]:
                result["execution_log"].append({
                    "agent": agent_name,
                    "task": task,
                    "status": "skipped",
                    "reason": usage_check["reason"],
                    "weight": task_weight
                })
                continue
            
            task_result = self._execute_agent_task(agent_name, task, tool_usage_aware)
            task_result["weight"] = task_weight
            result["execution_log"].append(task_result)
            
            current_load += task_weight
            time.sleep(0.2)
        
        completed_tasks = len([log for log in result["execution_log"] if log.get("status") == "completed"])
        
        return {
            "coordination_result": result,
            "execution_status": f"load_balanced_completed_{completed_tasks}/{len(tasks)}",
            "tool_usage_report": f"Final tool count: {throttler.tool_count}/120, Load used: {current_load}/{max_load}" if tool_usage_aware else "Tool usage not tracked"
        }
    
    def _emergency_coordination(self, tasks: Dict, result: Dict, tool_usage_aware: bool, task_timeout: int) -> Dict[str, Any]:
        """Execute critical tasks in emergency mode"""
        # Emergency priorities (only execute critical tasks)
        emergency_tasks = {
            "monitor": "alerts",
            "docker": "health_check"
        }
        
        # Filter to only emergency-critical tasks
        critical_tasks = {k: v for k, v in tasks.items() if k in emergency_tasks}
        
        for agent_name, task in critical_tasks.items():
            # In emergency mode, proceed even with high tool usage
            task_result = self._execute_agent_task(agent_name, task, tool_usage_aware)
            task_result["emergency_mode"] = True
            result["execution_log"].append(task_result)
            
            time.sleep(0.1)  # Minimal delay in emergency
        
        completed_tasks = len([log for log in result["execution_log"] if log.get("status") == "completed"])
        skipped_tasks = len(tasks) - len(critical_tasks)
        
        return {
            "coordination_result": result,
            "execution_status": f"emergency_completed_{completed_tasks}/{len(critical_tasks)}_critical_tasks_{skipped_tasks}_skipped",
            "tool_usage_report": f"Emergency mode - Final tool count: {throttler.tool_count}/120" if tool_usage_aware else "Emergency mode - Tool usage not tracked"
        }
