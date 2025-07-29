#!/usr/bin/env python3
"""
VS Code Copilot Tools Usage Monitor and Throttling System
Prevents exceeding the 128 tools usage limit in VS Code Copilot through
automated monitoring, throttling, and task splitting.
"""
import json
import time
import logging
import os
import sys
import re
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue
import random
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('copilot_tools_usage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CopilotToolsMonitor")

class MultiAgentTaskDistributor:
    """
    Handles distributing tasks across multiple agents when approaching the VS Code Copilot tools limit
    """
    
    def __init__(self, coordinator_file="agent_collaboration_config.json"):
        """Initialize the task distributor with coordinator config"""
        self.coordinator_file = coordinator_file
        self.agents = {}
        self.load_config()
    
    def load_config(self):
        """Load agent collaboration configuration"""
        try:
            if os.path.exists(self.coordinator_file):
                with open(self.coordinator_file, 'r') as f:
                    config = json.load(f)
                    self.agents = config.get("agents", {})
                    logger.info(f"Loaded {len(self.agents)} available agents for task distribution")
            else:
                logger.warning(f"Agent collaboration config not found at {self.coordinator_file}")
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
    
    def distribute_task(self, task_description: str, priority: int = 1) -> Dict[str, Any]:
        """
        Split a complex task among available agents to avoid exceeding tool limits
        
        Args:
            task_description: Description of the task to distribute
            priority: Task priority (1-5, 5 being highest)
            
        Returns:
            Dict with task distribution information
        """
        if not self.agents:
            logger.warning("No agents available for task distribution")
            return {"success": False, "error": "No agents configured"}
        
        # Create a task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Simple round-robin distribution for now
        available_agents = list(self.agents.keys())
        agent_count = len(available_agents)
        
        if agent_count == 0:
            return {"success": False, "error": "No agents available"}
        
        # For demonstration - in real use, this would be more sophisticated
        selected_agent = random.choice(available_agents)
        
        task_assignment = {
            "task_id": task_id,
            "description": task_description,
            "assigned_agent": selected_agent,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # In a full implementation, we'd send this to the agent
        logger.info(f"Task {task_id} assigned to {selected_agent}")
        
        # Save to coordination file
        self._save_task_assignment(task_assignment)
        
        return {
            "success": True, 
            "task_id": task_id,
            "agent": selected_agent
        }
    
    def _save_task_assignment(self, task: Dict[str, Any]):
        """Save task assignment to coordination status file"""
        status_file = "agent_coordination_results.json"
        try:
            current_tasks = {}
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    current_tasks = json.load(f)
            
            # Add the new task
            current_tasks[task["task_id"]] = task
            
            # Save updated tasks
            with open(status_file, 'w') as f:
                json.dump(current_tasks, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save task assignment: {e}")


class CopilotToolsMonitor:
    """Monitor and manage VS Code Copilot tools usage to prevent exceeding 128 tools limit"""
    
    # Maximum number of tools allowed in VS Code Copilot
    MAX_TOOLS_LIMIT = 128
    
    # Warning thresholds
    WARNING_THRESHOLD = 100  # 78% of limit
    CRITICAL_THRESHOLD = 115  # 90% of limit
    
    # Tool cooldown periods in seconds
    TOOL_COOLDOWN_PERIODS = {
        "default": 60,
        "high_impact": 120,  # Tools that consume more resources
        "file_search": 30,
        "semantic_search": 90,
        "grep_search": 45
    }
    
    def __init__(self, context_file="copilot_context.json", throttle_enabled=True):
        """Initialize the monitor with context file path and throttling control"""
        self.context_file = context_file
        self.throttle_enabled = throttle_enabled
        self.tools_used = []
        self.tool_usage_timestamps = {}  # Track when each tool was used
        self.current_count = 0
        self.session_start = datetime.now()
        self.lock = threading.Lock()
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.last_cleanup = datetime.now()
        self.task_distributor = MultiAgentTaskDistributor()
        self.load_context()
        logger.info(f"Copilot Tools Monitor initialized. Max limit: {self.MAX_TOOLS_LIMIT}")
        
        # Start background worker thread
        self._start_worker()
    
    def load_context(self):
        """Load existing context if available"""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r') as f:
                    data = json.load(f)
                    self.tools_used = data.get("tools_used", [])
                    self.tool_usage_timestamps = data.get("tool_usage_timestamps", {})
                    self.current_count = len(self.tools_used)
                    logger.info(f"Loaded existing context. Current tools count: {self.current_count}")
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")
            self.reset_context()
    
    def save_context(self):
        """Save current context"""
        try:
            with self.lock:
                with open(self.context_file, 'w') as f:
                    json.dump({
                        "tools_used": self.tools_used,
                        "tool_usage_timestamps": self.tool_usage_timestamps,
                        "count": self.current_count,
                        "last_updated": datetime.now().isoformat(),
                        "session_start": self.session_start.isoformat(),
                        "throttling_enabled": self.throttle_enabled
                    }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
    
    def reset_context(self):
        """Reset tools usage context"""
        with self.lock:
            self.tools_used = []
            self.current_count = 0
            self.tool_usage_timestamps = {}
            self.save_context()
            logger.info("Tools usage context has been reset")
    
    def _start_worker(self):
        """Start background worker thread for processing tasks"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.debug("Background worker thread started")
    
    def _worker_loop(self):
        """Background worker loop to process queued tasks"""
        max_consecutive_errors = 3
        error_count = 0
        max_idle_time = 300  # 5 minutes max idle time
        last_activity = time.time()
        
        while True:
            try:
                # Get task from queue with timeout
                try:
                    task = self.task_queue.get(timeout=5)
                    # Reset error count on successful task retrieval
                    error_count = 0
                    last_activity = time.time()
                    
                    # Process task
                    if task["type"] == "register_tool":
                        self._register_tool(task["tool_name"], task["category"])
                    elif task["type"] == "cleanup":
                        self._cleanup_expired_tools()
                    elif task["type"] == "exit":
                        logger.debug("Received exit signal, terminating worker thread")
                        break
                    
                    # Mark task as done
                    self.task_queue.task_done()
                    
                except queue.Empty:
                    # Check idle timeout
                    if time.time() - last_activity > max_idle_time:
                        logger.info(f"Worker thread idle for {max_idle_time} seconds, terminating")
                        break
                        
                    # Perform periodic maintenance
                    try:
                        self._perform_maintenance()
                        # Reset error count on successful maintenance
                        error_count = 0
                    except Exception as maint_err:
                        logger.error(f"Error in maintenance task: {maint_err}")
                        error_count += 1
                    
                    continue
                
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
                error_count += 1
                
                if error_count >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({error_count}), terminating worker thread")
                    break
                    
                time.sleep(1)  # Prevent tight loop on error
                
        logger.info("Worker thread terminated")
    
    def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        now = datetime.now()
        # Run cleanup every hour
        if (now - self.last_cleanup).total_seconds() > 3600:
            logger.debug("Running periodic maintenance")
            self._cleanup_expired_tools()
            self.last_cleanup = now
    
    def _cleanup_expired_tools(self):
        """Clean up expired tool usage records"""
        with self.lock:
            now = datetime.now()
            expired_tools = []
            
            # Find tools that haven't been used in 24 hours
            for tool_name, timestamp_str in list(self.tool_usage_timestamps.items()):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if (now - timestamp).total_seconds() > 86400:  # 24 hours
                        expired_tools.append(tool_name)
                except (ValueError, TypeError):
                    # Handle invalid timestamp format
                    expired_tools.append(tool_name)
            
            # Remove expired tools
            for tool in expired_tools:
                if tool in self.tools_used:
                    self.tools_used.remove(tool)
                if tool in self.tool_usage_timestamps:
                    del self.tool_usage_timestamps[tool]
            
            # Update count and save
            self.current_count = len(self.tools_used)
            if expired_tools:
                logger.info(f"Cleaned up {len(expired_tools)} expired tool records")
                self.save_context()
    
    def register_tool(self, tool_name: str, category: str = "default"):
        """
        Register a tool usage (async via queue)
        
        Args:
            tool_name: Name of the tool being used
            category: Tool category for throttling purposes
        """
        self.task_queue.put({
            "type": "register_tool",
            "tool_name": tool_name,
            "category": category
        })
    
    def _register_tool(self, tool_name: str, category: str = "default"):
        """
        Internal method to register a tool usage
        
        Args:
            tool_name: Name of the tool being used
            category: Tool category for throttling purposes
        """
        with self.lock:
            now = datetime.now()
            timestamp = now.isoformat()
            
            # Add tool if not already tracked
            if tool_name not in self.tools_used:
                self.tools_used.append(tool_name)
                self.current_count = len(self.tools_used)
                logger.debug(f"Registered new tool: {tool_name} (Total: {self.current_count})")
            
            # Update timestamp regardless
            self.tool_usage_timestamps[tool_name] = timestamp
            
            # Check thresholds and save
            self._check_thresholds()
            self.save_context()
    
    def get_remaining_capacity(self) -> int:
        """Get remaining capacity before hitting the tools limit"""
        with self.lock:
            return max(0, self.MAX_TOOLS_LIMIT - self.current_count)
    
    def _check_thresholds(self):
        """Check usage thresholds and take appropriate actions"""
        # Handle critical threshold
        if self.current_count >= self.CRITICAL_THRESHOLD:
            logger.warning(f"CRITICAL: Tool usage at {self.current_count}/{self.MAX_TOOLS_LIMIT}")
            if self.throttle_enabled:
                self._initiate_task_splitting()
        
        # Handle warning threshold
        elif self.current_count >= self.WARNING_THRESHOLD:
            logger.warning(f"WARNING: Tool usage approaching limit: {self.current_count}/{self.MAX_TOOLS_LIMIT}")
            if self.throttle_enabled:
                self._apply_throttling()
    
    def _apply_throttling(self):
        """Apply throttling to reduce tool usage rate"""
        logger.info("Applying throttling to reduce tool usage rate")
        # In a real implementation, this would slow down tool usage
        # For now, just log the action
    
    def _initiate_task_splitting(self):
        """Initiate task splitting to avoid exceeding the limit"""
        logger.warning("Initiating task splitting to avoid exceeding tool limit")
        # In a real implementation, this would split the current task
        # across multiple agents
        
        # Example task distribution
        self.task_distributor.distribute_task(
            "Continue processing with reduced tool usage",
            priority=4
        )
    
    def terminate_worker(self):
        """Safely terminate the worker thread"""
        if self.worker_thread and self.worker_thread.is_alive():
            try:
                # Send exit signal
                self.task_queue.put({"type": "exit"})
                
                # Wait for thread to finish, but with timeout
                self.worker_thread.join(timeout=5)
                
                if self.worker_thread.is_alive():
                    logger.warning("Worker thread did not terminate gracefully within timeout")
                else:
                    logger.debug("Worker thread terminated successfully")
            except Exception as e:
                logger.error(f"Error terminating worker thread: {e}")
    
    def get_detailed_statistics(self):
        """Get detailed usage statistics"""
        with self.lock:
            now = datetime.now()
            session_duration = (now - self.session_start).total_seconds()
            
            # Calculate usage rate
            if session_duration > 0:
                usage_rate = self.current_count / session_duration
            else:
                usage_rate = 0
            
            # Calculate estimated time to limit
            remaining = self.get_remaining_capacity()
            if usage_rate > 0:
                time_to_limit = remaining / usage_rate
            else:
                time_to_limit = float('inf')
            
            return {
                "current_count": self.current_count,
                "max_limit": self.MAX_TOOLS_LIMIT,
                "remaining": remaining,
                "usage_percentage": (self.current_count / self.MAX_TOOLS_LIMIT) * 100,
                "session_duration_seconds": session_duration,
                "usage_rate_per_second": usage_rate,
                "estimated_seconds_to_limit": time_to_limit,
                "throttling_enabled": self.throttle_enabled,
                "throttling_active": self.throttle_enabled and self.current_count >= self.WARNING_THRESHOLD,
                "worker_active": self.worker_thread is not None and self.worker_thread.is_alive()
            }


def monitor_command_line():
    """Command line interface for the monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VS Code Copilot Tools Usage Monitor")
    parser.add_argument("--reset", action="store_true", help="Reset the tools usage counter")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--register", help="Register a tool usage")
    parser.add_argument("--category", default="default", help="Tool category")
    parser.add_argument("--disable-throttle", action="store_true", help="Disable throttling")
    parser.add_argument("--context-file", default="copilot_context.json", help="Context file path")
    args = parser.parse_args()
    
    # Initialize the monitor
    monitor = CopilotToolsMonitor(
        context_file=args.context_file,
        throttle_enabled=not args.disable_throttle
    )
    
    if args.reset:
        monitor.reset_context()
        print("Tools usage context reset")
        return
    
    if args.register:
        monitor.register_tool(args.register, args.category)
        print(f"Registered tool usage: {args.register} (category: {args.category})")
        # Sleep briefly to allow background thread to process
        time.sleep(0.5)
    
    if args.status or not (args.reset or args.register):
        stats = monitor.get_detailed_statistics()
        print("\nVS Code Copilot Tools Usage Monitor")
        print("=" * 40)
        print(f"Current usage: {stats['current_count']} / {stats['max_limit']} tools")
        print(f"Remaining capacity: {stats['remaining']} tools")
        print(f"Usage percentage: {stats['usage_percentage']:.1f}%")
        print(f"Session duration: {stats['session_duration_seconds']:.1f} seconds")
        print(f"Usage rate: {stats['usage_rate_per_second']:.4f} tools/second")
        
        # Show estimated time to limit
        if stats['estimated_seconds_to_limit'] == float('inf'):
            time_to_limit = "Never (no usage rate)"
        else:
            seconds = stats['estimated_seconds_to_limit']
            if seconds < 60:
                time_to_limit = f"{seconds:.1f} seconds"
            elif seconds < 3600:
                time_to_limit = f"{seconds / 60:.1f} minutes"
            else:
                time_to_limit = f"{seconds / 3600:.1f} hours"
        
        print(f"Estimated time to limit: {time_to_limit}")
        print(f"Throttling: {'Enabled' if stats['throttling_enabled'] else 'Disabled'}")
        print(f"Throttling active: {'Yes' if stats['throttling_active'] else 'No'}")


if __name__ == "__main__":
    monitor_command_line()
    
    def register_tool_usage(self, tool_name, params=None):
        """Register a tool usage, with optional throttling"""
        with self.lock:
            timestamp = datetime.now().isoformat()
            tool_entry = {
                "tool": tool_name,
                "timestamp": timestamp,
                "params": params
            }
            self.tools_used.append(tool_entry)
            self.current_count = len(self.tools_used)
            
            # Check thresholds
            if self.current_count >= self.WARNING_THRESHOLD:
                if self.current_count >= self.CRITICAL_THRESHOLD:
                    logger.critical(f"CRITICAL: Tools usage at {self.current_count}/{self.MAX_TOOLS_LIMIT} - immediate action required!")
                else:
                    logger.warning(f"WARNING: Tools usage at {self.current_count}/{self.MAX_TOOLS_LIMIT}")
            
            # Apply throttling if enabled and approaching limit
            if self.throttle_enabled and self.current_count >= self.WARNING_THRESHOLD:
                delay = self._calculate_throttle_delay()
                if delay > 0:
                    logger.info(f"Throttling tool usage - applying {delay}ms delay")
                    time.sleep(delay / 1000.0)  # Convert ms to seconds
            
            self.save_context()
            return self.current_count
    
    def _calculate_throttle_delay(self):
        """Calculate appropriate throttle delay based on current usage"""
        if self.current_count >= self.CRITICAL_THRESHOLD:
            # Exponential backoff for critical levels
            return 200 + (self.current_count - self.CRITICAL_THRESHOLD) * 50
        elif self.current_count >= self.WARNING_THRESHOLD:
            # Linear increase for warning levels
            return 50 + (self.current_count - self.WARNING_THRESHOLD) * 10
        return 0
    
    def get_remaining_capacity(self):
        """Get remaining tools capacity"""
        with self.lock:
            remaining = self.MAX_TOOLS_LIMIT - self.current_count
            return max(0, remaining)
    
    def get_usage_stats(self):
        """Get detailed usage statistics"""
        with self.lock:
            now = datetime.now()
            session_duration = (now - self.session_start).total_seconds()
            
            # Calculate usage rate
            if session_duration > 0:
                usage_rate = self.current_count / session_duration
            else:
                usage_rate = 0
            
            # Calculate estimated time to limit
            remaining = self.get_remaining_capacity()
            if usage_rate > 0:
                time_to_limit = remaining / usage_rate
            else:
                time_to_limit = float('inf')
            
            return {
                "current_count": self.current_count,
                "max_limit": self.MAX_TOOLS_LIMIT,
                "remaining": remaining,
                "usage_percentage": (self.current_count / self.MAX_TOOLS_LIMIT) * 100,
                "session_duration_seconds": session_duration,
                "usage_rate_per_second": usage_rate,
                "estimated_seconds_to_limit": time_to_limit,
                "throttling_enabled": self.throttle_enabled,
                "throttling_active": self.throttle_enabled and self.current_count >= self.WARNING_THRESHOLD,
            }
    
    def start_background_worker(self):
        """Start background worker for processing tasks"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._worker_loop)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            logger.info("Background worker started")
    
    def _worker_loop(self):
        """Background worker loop for processing queued tasks"""
        while True:
            try:
                task = self.task_queue.get(timeout=1.0)
                if task is None:  # Sentinel for shutdown
                    break
                
                tool_name, params = task
                # Process task with automatic throttling
                self.register_tool_usage(tool_name, params)
                self.task_queue.task_done()
            except queue.Empty:
                continue  # No tasks available
            except Exception as e:
                logger.error(f"Error processing task: {e}")
    
    def enqueue_tool_usage(self, tool_name, params=None):
        """Queue a tool usage for background processing"""
        self.task_queue.put((tool_name, params))
        return {
            "queued": True, 
            "queue_size": self.task_queue.qsize(),
            "current_count": self.current_count
        }
    
    def batch_process_tools(self, tools_list):
        """Process multiple tools as a batch with optimized throttling"""
        if not tools_list:
            return {"processed": 0}
        
        with self.lock:
            # Pre-calculate how many we can safely process
            remaining = self.get_remaining_capacity()
            can_process = min(len(tools_list), remaining)
            
            if can_process < len(tools_list):
                logger.warning(f"Cannot process all tools - limit would be exceeded. Processing {can_process}/{len(tools_list)}")
            
            # Process the safe number of tools
            batch_timestamp = datetime.now().isoformat()
            for i in range(can_process):
                tool_name, params = tools_list[i]
                tool_entry = {
                    "tool": tool_name,
                    "timestamp": batch_timestamp,
                    "params": params,
                    "batch_id": datetime.now().strftime("%Y%m%d%H%M%S")
                }
                self.tools_used.append(tool_entry)
            
            self.current_count = len(self.tools_used)
            self.save_context()
            
            # Apply single throttle delay at the end if needed
            if self.throttle_enabled and self.current_count >= self.WARNING_THRESHOLD:
                delay = self._calculate_throttle_delay()
                if delay > 0:
                    logger.info(f"Batch throttling - applying {delay}ms delay for {can_process} tools")
                    time.sleep(delay / 1000.0)
            
            return {
                "processed": can_process,
                "remaining": self.get_remaining_capacity(),
                "batch_throttled": delay > 0 if 'delay' in locals() else False
            }
    
    def shutdown(self):
        """Shutdown the monitor cleanly"""
        # Signal worker thread to exit
        if self.worker_thread and self.worker_thread.is_alive():
            self.task_queue.put(None)
            self.worker_thread.join(timeout=2.0)
        
        # Final context save
        self.save_context()
        logger.info(f"Monitor shutdown. Final tools count: {self.current_count}")

def main():
    """Demo function to test the monitor"""
    monitor = CopilotToolsMonitor()
    
    print("🔍 VS Code Copilot Tools Usage Monitor")
    print("=" * 50)
    
    # Register some sample tool usages
    for i in range(30):
        tool_name = f"sample_tool_{i % 10}"
        monitor.register_tool_usage(tool_name, {"arg": f"value_{i}"})
    
    # Display stats
    stats = monitor.get_usage_stats()
    print(f"📊 Current usage: {stats['current_count']}/{stats['max_limit']} tools")
    print(f"📈 Usage rate: {stats['usage_rate_per_second']:.2f} tools/sec")
    print(f"⏳ Time to limit: {stats['estimated_seconds_to_limit']:.1f} seconds")
    
    # Test batch processing
    batch_tools = [
        ("batch_tool_a", {"arg": "batch_1"}),
        ("batch_tool_b", {"arg": "batch_2"}),
        ("batch_tool_c", {"arg": "batch_3"}),
    ]
    result = monitor.batch_process_tools(batch_tools)
    print(f"🔄 Batch processed: {result['processed']} tools")
    
    # Clean shutdown
    monitor.shutdown()

if __name__ == "__main__":
    main()
