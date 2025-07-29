#!/usr/bin/env python3
"""
NoxGuard System Status Check
Provides comprehensive system status monitoring integrating Docker, VS Code Copilot tools,
and multi-agent coordination.
"""
import json
import os
import sys
import subprocess
import logging
import datetime
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_status.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemStatusCheck")

# Import local modules
try:
    from copilot_tools_monitor import CopilotToolsMonitor
except ImportError:
    logger.warning("Could not import CopilotToolsMonitor. Some features will be disabled.")
    CopilotToolsMonitor = None

class SystemStatusMonitor:
    """System status monitoring and reporting"""
    
    def __init__(self, output_file="system_status.json"):
        """Initialize the system status monitor"""
        self.output_file = output_file
        self.status_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system_info": {},
            "docker_status": {},
            "copilot_tools": {},
            "agent_coordination": {},
            "resources": {}
        }
    
    def check_system_info(self):
        """Get basic system information"""
        logger.info("Checking system information...")
        
        try:
            # Get OS information
            if os.name == 'nt':
                # Windows
                os_info = subprocess.run(
                    ["powershell", "-Command", 
                     "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture"],
                    capture_output=True, text=True
                )
                self.status_data["system_info"]["os"] = os_info.stdout.strip() if os_info.returncode == 0 else "Unknown Windows"
                
                # Memory information
                mem_info = subprocess.run(
                    ["powershell", "-Command", 
                     "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory"],
                    capture_output=True, text=True
                )
                self.status_data["system_info"]["memory"] = mem_info.stdout.strip() if mem_info.returncode == 0 else "Unknown"
            else:
                # Linux/macOS
                os_info = subprocess.run(["uname", "-a"], capture_output=True, text=True)
                self.status_data["system_info"]["os"] = os_info.stdout.strip() if os_info.returncode == 0 else "Unknown Unix-like"
                
                # Memory information on Linux
                if os.path.exists("/proc/meminfo"):
                    with open("/proc/meminfo", "r") as f:
                        meminfo = f.read()
                    self.status_data["system_info"]["memory"] = meminfo
            
            # Python version
            self.status_data["system_info"]["python_version"] = sys.version
            
            # Get current working directory
            self.status_data["system_info"]["working_directory"] = os.getcwd()
            
            # Check for virtual environment
            self.status_data["system_info"]["virtual_env"] = os.environ.get("VIRTUAL_ENV", "None")
            
            logger.info("System information collected")
        except Exception as e:
            logger.error(f"Error checking system info: {e}")
            self.status_data["system_info"]["error"] = str(e)
    
    def check_docker_status(self):
        """Check Docker status using our docker_fix_test module"""
        logger.info("Checking Docker status...")
        
        # Import threading and queue at the function level to avoid circular imports
        import threading
        import queue
        
        try:
            # Define the worker function to run in a separate thread with timeout
            def get_docker_status():
                result = {}
                
                try:
                    # Try to import docker module directly
                    import docker
                    client = docker.from_env()
                    
                    # Get Docker info with timeout
                    docker_info = client.info()
                    result["version"] = docker_info.get("ServerVersion", "Unknown")
                    result["containers"] = {
                        "total": docker_info.get("Containers", 0),
                        "running": docker_info.get("ContainersRunning", 0),
                        "stopped": docker_info.get("ContainersStopped", 0)
                    }
                    
                    # Get container details
                    containers = client.containers.list(all=True)
                    container_details = []
                    for container in containers:
                        container_details.append({
                            "id": container.id[:12],
                            "name": container.name,
                            "image": container.image.tags[0] if container.image.tags else "untagged",
                            "status": container.status
                        })
                    result["container_details"] = container_details
                    
                    # Check NoxSuite specific containers
                    noxsuite_containers = {
                        "noxsuite-langflow": False,
                        "noxsuite-postgres": False,
                        "noxsuite-redis": False
                    }
                    
                    for container in containers:
                        if container.name in noxsuite_containers:
                            noxsuite_containers[container.name] = container.status == "running"
                    
                    result["noxsuite_status"] = noxsuite_containers
                    result["all_running"] = all(noxsuite_containers.values())
                    
                    return ("success", result)
                except ImportError:
                    logger.warning("Docker module not available, attempting to run docker_fix_test.py")
                    
                    # Try running docker_fix_test.py
                    if os.path.exists("docker_fix_test.py"):
                        subprocess.run([sys.executable, "docker_fix_test.py"], check=False)
                        result["message"] = "Attempted to fix Docker integration"
                        return ("success", result)
                    else:
                        return ("error", "docker_fix_test.py not found")
                except Exception as docker_err:
                    logger.error(f"Docker error: {docker_err}")
                    return ("error", str(docker_err))
            
            # Create and start the thread
            result_queue = queue.Queue()
            
            def worker():
                try:
                    status, result = get_docker_status()
                    result_queue.put((status, result))
                except Exception as e:
                    result_queue.put(("error", str(e)))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
            # Wait with timeout
            try:
                status, result = result_queue.get(timeout=15)  # Allow 15 seconds for Docker operations
                
                if status == "error":
                    self.status_data["docker_status"]["error"] = result
                else:
                    self.status_data["docker_status"] = result
                    logger.info("Docker status checked successfully")
            except queue.Empty:
                logger.error("Timeout while checking Docker status")
                self.status_data["docker_status"]["error"] = "Operation timed out after 15 seconds"
                
        except Exception as e:
            logger.error(f"Error checking Docker status: {e}")
            self.status_data["docker_status"]["error"] = str(e)
    
    def check_copilot_tools(self):
        """Check VS Code Copilot tools usage status"""
        logger.info("Checking VS Code Copilot tools status...")
        
        try:
            if CopilotToolsMonitor:
                # Use a timeout mechanism to prevent hanging
                def get_monitor_stats():
                    monitor = CopilotToolsMonitor()
                    return monitor.get_detailed_statistics()
                
                # Create and start the thread
                import threading
                import queue
                result_queue = queue.Queue()
                
                def worker():
                    try:
                        stats = get_monitor_stats()
                        result_queue.put(("success", stats))
                    except Exception as e:
                        result_queue.put(("error", str(e)))
                
                thread = threading.Thread(target=worker)
                thread.daemon = True
                thread.start()
                
                # Wait with timeout
                try:
                    status, result = result_queue.get(timeout=10)
                    if status == "error":
                        raise Exception(result)
                    
                    stats = result
                    self.status_data["copilot_tools"] = {
                        "current_count": stats["current_count"],
                        "max_limit": stats["max_limit"],
                        "remaining": stats["remaining"],
                        "usage_percentage": stats["usage_percentage"],
                        "throttling_enabled": stats["throttling_enabled"],
                        "throttling_active": stats["throttling_active"]
                    }
                    
                    # Add warning if approaching limit
                    if stats["usage_percentage"] > 70:
                        self.status_data["copilot_tools"]["warning"] = "Approaching tool usage limit"
                    
                    logger.info(f"Copilot tools status: {stats['current_count']}/{stats['max_limit']} tools used")
                except queue.Empty:
                    logger.error("Timeout while getting Copilot tools status")
                    self.status_data["copilot_tools"]["error"] = "Operation timed out after 10 seconds"
            else:
                self.status_data["copilot_tools"]["error"] = "CopilotToolsMonitor not available"
        except Exception as e:
            logger.error(f"Error checking Copilot tools: {e}")
            self.status_data["copilot_tools"]["error"] = str(e)
    
    def check_agent_coordination(self):
        """Check agent coordination status"""
        logger.info("Checking agent coordination...")
        
        # Initialize the section if not already present
        if "agent_coordination" not in self.status_data:
            self.status_data["agent_coordination"] = {}
        
        try:
            # Check if coordination config exists
            config_file = "agent_collaboration_config.json"
            status_file = "agent_coordination_results.json"
            
            # Use timeout for file operations
            def process_coordination_files():
                result = {}
                
                # Check config file
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            config_content = f.read().strip()
                            # Make sure we have valid JSON
                            if config_content:
                                config = json.loads(config_content)
                                result["config"] = {
                                    "agents_configured": len(config.get("agents", {})),
                                    "config_timestamp": os.path.getmtime(config_file)
                                }
                            else:
                                result["config"] = "Empty file"
                    except json.JSONDecodeError as je:
                        result["config"] = f"Invalid JSON: {str(je)}"
                else:
                    result["config"] = "Missing"
                
                # Check results file
                if os.path.exists(status_file):
                    try:
                        with open(status_file, 'r') as f:
                            results_content = f.read().strip()
                            # Make sure we have valid JSON
                            if results_content:
                                results = json.loads(results_content)
                                
                                # Count tasks by status
                                tasks_by_status = {}
                                for task_id, task in results.items():
                                    status = task.get("status", "unknown")
                                    if status not in tasks_by_status:
                                        tasks_by_status[status] = 0
                                    tasks_by_status[status] += 1
                                
                                result["tasks"] = {
                                    "total": len(results),
                                    "by_status": tasks_by_status
                                }
                            else:
                                result["tasks"] = "Empty file"
                    except json.JSONDecodeError as je:
                        result["tasks"] = f"Invalid JSON: {str(je)}"
                else:
                    result["tasks"] = "No tasks found"
                
                return result
            
            # Create and start the thread with timeout
            import threading
            import queue
            result_queue = queue.Queue()
            
            def worker():
                try:
                    check_result = process_coordination_files()
                    result_queue.put(("success", check_result))
                except Exception as e:
                    result_queue.put(("error", str(e)))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
            # Wait with timeout
            try:
                status, thread_result = result_queue.get(timeout=5)
                if status == "error":
                    raise Exception(thread_result)
                
                self.status_data["agent_coordination"] = thread_result
                logger.info("Agent coordination status checked")
            except queue.Empty:
                logger.error("Timeout while checking agent coordination")
                self.status_data["agent_coordination"]["error"] = "Operation timed out after 5 seconds"
            
        except Exception as e:
            logger.error(f"Error checking agent coordination: {e}")
            self.status_data["agent_coordination"]["error"] = str(e)
            
    def check_resources(self):
        """Check system resource usage"""
        logger.info("Checking system resources...")
        
        # Import threading and queue at the function level
        import threading
        import queue
        
        try:
            def get_resource_info():
                result = {}
                
                try:
                    # Get CPU usage
                    if os.name == 'nt':
                        # Windows
                        cpu_cmd = subprocess.run(
                            ["powershell", "-Command", "Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object Average"],
                            capture_output=True, text=True, timeout=5
                        )
                        if cpu_cmd.returncode == 0:
                            try:
                                # Extract just the number from the output
                                cpu_output = cpu_cmd.stdout.strip()
                                cpu_usage = float([line for line in cpu_output.split('\n') if line.strip()][-1])
                                result["cpu_usage"] = cpu_usage
                            except:
                                result["cpu_usage"] = "Error parsing"
                    else:
                        # Linux
                        if os.path.exists("/proc/loadavg"):
                            with open("/proc/loadavg", "r") as f:
                                load = f.read().strip().split()
                                if len(load) >= 3:
                                    result["load_average"] = {
                                        "1min": float(load[0]),
                                        "5min": float(load[1]),
                                        "15min": float(load[2])
                                    }
                    
                    # Get disk space
                    if os.name == 'nt':
                        # Windows
                        disk_cmd = subprocess.run(
                            ["powershell", "-Command", "Get-PSDrive C | Select-Object Used, Free"],
                            capture_output=True, text=True, timeout=5
                        )
                        if disk_cmd.returncode == 0:
                            result["disk"] = disk_cmd.stdout.strip()
                    else:
                        # Linux/macOS
                        disk_cmd = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
                        if disk_cmd.returncode == 0:
                            result["disk"] = disk_cmd.stdout.strip()
                    
                    return ("success", result)
                except subprocess.TimeoutExpired:
                    return ("error", "Subprocess timed out")
                except Exception as e:
                    return ("error", str(e))
            
            # Create and start the thread
            result_queue = queue.Queue()
            
            def worker():
                try:
                    status, result = get_resource_info()
                    result_queue.put((status, result))
                except Exception as e:
                    result_queue.put(("error", str(e)))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            
            # Wait with timeout
            try:
                status, result = result_queue.get(timeout=10)
                
                if status == "error":
                    self.status_data["resources"]["error"] = result
                else:
                    self.status_data["resources"] = result
                    logger.info("Resource check completed")
            except queue.Empty:
                logger.error("Timeout while checking system resources")
                self.status_data["resources"]["error"] = "Operation timed out after 10 seconds"
                
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            self.status_data["resources"]["error"] = str(e)
    
    def run_all_checks(self):
        """Run all status checks"""
        logger.info("Running comprehensive system status check...")
        
        # Run each check with error handling to ensure we continue even if one check fails
        try:
            self.check_system_info()
            logger.info("System info check completed")
        except Exception as e:
            logger.error(f"System info check failed: {e}")
            self.status_data["system_info"]["error"] = f"Check failed: {str(e)}"
            
        try:
            self.check_docker_status()
            logger.info("Docker status check completed")
        except Exception as e:
            logger.error(f"Docker status check failed: {e}")
            self.status_data["docker_status"]["error"] = f"Check failed: {str(e)}"
            
        try:
            self.check_copilot_tools()
            logger.info("Copilot tools check completed")
        except Exception as e:
            logger.error(f"Copilot tools check failed: {e}")
            self.status_data["copilot_tools"]["error"] = f"Check failed: {str(e)}"
            
        try:
            self.check_agent_coordination()
            logger.info("Agent coordination check completed")
        except Exception as e:
            logger.error(f"Agent coordination check failed: {e}")
            self.status_data["agent_coordination"]["error"] = f"Check failed: {str(e)}"
            
        try:
            self.check_resources()
            logger.info("Resources check completed")
        except Exception as e:
            logger.error(f"Resources check failed: {e}")
            self.status_data["resources"]["error"] = f"Check failed: {str(e)}"
            
        # Add completion timestamp
        self.status_data["check_completed_at"] = datetime.datetime.now().isoformat()
        
        # Save results
        self.save_results()
        
        logger.info(f"Status check completed. Results saved to {self.output_file}")
        return self.status_data
    
    def save_results(self):
        """Save results to output file"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def print_summary(self):
        """Print a summary of the status check results"""
        try:
            # Use ASCII-only symbols to avoid encoding issues on Windows
            print("\n" + "=" * 50)
            print("NOXGUARD SYSTEM STATUS SUMMARY")
            print("=" * 50)
            
            # System information
            print("\nSYSTEM INFORMATION")
            if "system_info" in self.status_data:
                if "os" in self.status_data["system_info"]:
                    print(f"OS: {self.status_data['system_info']['os']}")
                if "python_version" in self.status_data["system_info"]:
                    print(f"Python: {self.status_data['system_info']['python_version'].split()[0]}")
                if "error" in self.status_data["system_info"]:
                    print(f"[!] Error: {self.status_data['system_info']['error']}")
            
            # Docker status
            print("\nDOCKER STATUS")
            if "docker_status" in self.status_data:
                if "error" in self.status_data["docker_status"]:
                    print(f"[!] Error: {self.status_data['docker_status']['error']}")
                elif "version" in self.status_data["docker_status"]:
                    print(f"Version: {self.status_data['docker_status']['version']}")
                    containers = self.status_data["docker_status"].get("containers", {})
                    print(f"Containers: {containers.get('running', 0)} running, {containers.get('stopped', 0)} stopped")
                    
                    # NoxSuite containers
                    if "noxsuite_status" in self.status_data["docker_status"]:
                        print("\nNoxSuite Containers:")
                        for container, running in self.status_data["docker_status"]["noxsuite_status"].items():
                            status = "[+] Running" if running else "[-] Stopped"
                            print(f"  - {container}: {status}")
            
            # Copilot tools
            print("\nVS CODE COPILOT TOOLS")
            if "copilot_tools" in self.status_data:
                if "error" in self.status_data["copilot_tools"]:
                    print(f"[!] Error: {self.status_data['copilot_tools']['error']}")
                elif "current_count" in self.status_data["copilot_tools"]:
                    count = self.status_data["copilot_tools"]["current_count"]
                    limit = self.status_data["copilot_tools"]["max_limit"]
                    percentage = self.status_data["copilot_tools"]["usage_percentage"]
                    print(f"Tools Usage: {count}/{limit} ({percentage:.1f}%)")
                    
                    # Show warning if applicable
                    if "warning" in self.status_data["copilot_tools"]:
                        print(f"[!] {self.status_data['copilot_tools']['warning']}")
                    
                    # Show throttling status
                    throttling = "Enabled" if self.status_data["copilot_tools"].get("throttling_enabled", False) else "Disabled"
                    active = self.status_data["copilot_tools"].get("throttling_active", False)
                    print(f"Throttling: {throttling}" + (" (Active)" if active else ""))
            
            # Agent coordination
            print("\nAGENT COORDINATION")
            if "agent_coordination" in self.status_data:
                if "error" in self.status_data["agent_coordination"]:
                    print(f"[!] Error: {self.status_data['agent_coordination']['error']}")
                else:
                    if "config" in self.status_data["agent_coordination"]:
                        if isinstance(self.status_data["agent_coordination"]["config"], dict):
                            print(f"Agents Configured: {self.status_data['agent_coordination']['config'].get('agents_configured', 0)}")
                        else:
                            print(f"Config Status: {self.status_data['agent_coordination']['config']}")
                    
                    if "tasks" in self.status_data["agent_coordination"]:
                        if isinstance(self.status_data["agent_coordination"]["tasks"], dict):
                            print(f"Total Tasks: {self.status_data['agent_coordination']['tasks'].get('total', 0)}")
                            if "by_status" in self.status_data["agent_coordination"]["tasks"]:
                                print("Tasks by Status:")
                                for status, count in self.status_data["agent_coordination"]["tasks"]["by_status"].items():
                                    print(f"  - {status}: {count}")
                        else:
                            print(f"Tasks Status: {self.status_data['agent_coordination']['tasks']}")
            
            # System resources
            print("\nSYSTEM RESOURCES")
            if "resources" in self.status_data:
                if "error" in self.status_data["resources"]:
                    print(f"[!] Error: {self.status_data['resources']['error']}")
                else:
                    if "cpu_usage" in self.status_data["resources"]:
                        print(f"CPU Usage: {self.status_data['resources']['cpu_usage']}%")
                    if "load_average" in self.status_data["resources"]:
                        load = self.status_data["resources"]["load_average"]
                        print(f"Load Average: {load['1min']} (1m), {load['5min']} (5m), {load['15min']} (15m)")
                    if "disk" in self.status_data["resources"]:
                        print(f"\nDisk Usage:\n{self.status_data['resources']['disk']}")
            
            print("\n" + "=" * 50)
        except Exception as e:
            # Fallback to minimal ASCII-only summary on error
            print("\n" + "=" * 50)
            print("NOXGUARD SYSTEM STATUS SUMMARY (MINIMAL FORMAT)")
            print("=" * 50)
            print(f"\nStatus check completed with possible errors: {str(e)}")
            print(f"Results saved to {self.output_file}")
            print("\n" + "=" * 50)


def main():
    """Main function"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NoxGuard System Status Check")
    parser.add_argument("--output", default="system_status.json", help="Output file path")
    parser.add_argument("--quiet", action="store_true", help="Don't print summary to console")
    parser.add_argument("--timeout", type=int, default=60, help="Global timeout in seconds")
    args = parser.parse_args()
    
    # Setup global timeout handler
    def timeout_handler(signum, frame):
        logger.error(f"Global timeout of {args.timeout} seconds reached. Exiting.")
        sys.exit(1)
    
    # Register timeout handler
    if os.name != 'nt':  # SIGALRM not available on Windows
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)
    
    # Start time for manual timeout on Windows
    start_time = time.time()
    
    try:
        # Run status check
        monitor = SystemStatusMonitor(output_file=args.output)
        monitor.run_all_checks()
        
        if not args.quiet:
            monitor.print_summary()
        
        # On Windows, we need to manually check the timeout
        if os.name == 'nt' and (time.time() - start_time) > args.timeout:
            logger.error(f"Global timeout of {args.timeout} seconds reached. Completed with possible partial results.")
    
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}")
        # Always save what we have, even on error
        if 'monitor' in locals():
            try:
                monitor.save_results()
                logger.info(f"Partial results saved to {args.output} despite error")
                
                if not args.quiet:
                    monitor.print_summary()
            except:
                logger.error("Could not save partial results")
        sys.exit(1)
    
    # Disable alarm if we finish normally (Unix only)
    if os.name != 'nt':
        signal.alarm(0)


if __name__ == "__main__":
    main()
