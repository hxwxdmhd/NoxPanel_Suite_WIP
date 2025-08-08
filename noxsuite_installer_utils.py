"""
NoxSuite Smart Installer - Utility Functions and Components
Additional components for the smart installer system
"""

import os
import sys
import json
import subprocess
import shutil
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta

class ProgressTracker:
    """Enhanced progress tracking with ETA calculation"""
    
    def __init__(self, total_steps: int, logger):
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logger
        self.start_time = datetime.now()
        self.step_times = []
        self.step_names = []
    
    def start_step(self, step_name: str):
        """Start tracking a new step"""
        self.current_step += 1
        self.step_names.append(step_name)
        step_start_time = datetime.now()
        
        # Calculate ETA
        if self.current_step > 1:
            avg_step_time = sum(self.step_times) / len(self.step_times)
            remaining_steps = self.total_steps - self.current_step + 1
            eta_seconds = remaining_steps * avg_step_time
            eta_str = self._format_duration(eta_seconds)
        else:
            eta_str = "calculating..."
        
        progress_pct = (self.current_step - 1) / self.total_steps * 100
        
        self.logger.info(f"[{self.current_step}/{self.total_steps}] {step_name} ({progress_pct:.1f}% - ETA: {eta_str})")
        return step_start_time
    
    def complete_step(self, step_start_time: datetime):
        """Complete the current step and record timing"""
        step_duration = (datetime.now() - step_start_time).total_seconds()
        self.step_times.append(step_duration)
        
        progress_pct = self.current_step / self.total_steps * 100
        self.logger.info(f"✅ Step completed ({progress_pct:.1f}% total)")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

class FileBackupManager:
    """Manages file and directory backups during installation"""
    
    def __init__(self, backup_root: Path, logger):
        self.backup_root = backup_root
        self.logger = logger
        self.backups = []
        
        # Ensure backup directory exists
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    def backup_path(self, path: Path, backup_name: str = None) -> Optional[Path]:
        """Create backup of file or directory"""
        if not path.exists():
            return None
        
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.name}_{timestamp}"
        
        backup_path = self.backup_root / backup_name
        
        try:
            if path.is_file():
                shutil.copy2(path, backup_path)
            else:
                shutil.copytree(path, backup_path, dirs_exist_ok=True)
            
            self.backups.append({
                'original': str(path),
                'backup': str(backup_path),
                'timestamp': datetime.now().isoformat(),
                'size': self._get_size(backup_path)
            })
            
            self.logger.debug(f"Backed up {path} to {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.warning(f"Failed to backup {path}: {e}")
            return None
    
    def restore_backup(self, original_path: str) -> bool:
        """Restore a specific backup"""
        for backup_info in self.backups:
            if backup_info['original'] == original_path:
                try:
                    backup_path = Path(backup_info['backup'])
                    original = Path(original_path)
                    
                    if backup_path.is_file():
                        shutil.copy2(backup_path, original)
                    else:
                        if original.exists():
                            shutil.rmtree(original)
                        shutil.copytree(backup_path, original)
                    
                    self.logger.info(f"Restored {original_path} from backup")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Failed to restore {original_path}: {e}")
                    return False
        
        self.logger.warning(f"No backup found for {original_path}")
        return False
    
    def cleanup_backups(self, max_age_days: int = 7):
        """Clean up old backups"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        for backup_info in self.backups[:]:
            backup_time = datetime.fromisoformat(backup_info['timestamp'])
            if backup_time < cutoff_time:
                try:
                    backup_path = Path(backup_info['backup'])
                    if backup_path.exists():
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)
                    
                    self.backups.remove(backup_info)
                    self.logger.debug(f"Cleaned up old backup: {backup_path}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup backup {backup_path}: {e}")
    
    def _get_size(self, path: Path) -> int:
        """Get size of file or directory in bytes"""
        if path.is_file():
            return path.stat().st_size
        else:
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    try:
                        total += filepath.stat().st_size
                    except:
                        pass
            return total

class DockerManager:
    """Enhanced Docker management with health checks and image optimization"""
    
    def __init__(self, logger):
        self.logger = logger
        self.docker_available = shutil.which("docker") is not None
    
    def check_docker_health(self) -> Dict[str, Any]:
        """Comprehensive Docker health check"""
        if not self.docker_available:
            return {"status": "unavailable", "message": "Docker not found"}
        
        health = {"status": "healthy", "issues": []}
        
        # Check Docker daemon
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                health["status"] = "unhealthy"
                health["issues"].append("Docker daemon not running")
                return health
            
        except subprocess.TimeoutExpired:
            health["status"] = "unhealthy"
            health["issues"].append("Docker daemon not responsive")
            return health
        except Exception as e:
            health["status"] = "unhealthy"
            health["issues"].append(f"Docker check failed: {e}")
            return health
        
        # Check Docker Compose
        compose_available = (
            shutil.which("docker-compose") is not None or
            self._check_docker_compose_plugin()
        )
        
        if not compose_available:
            health["issues"].append("Docker Compose not available")
        
        # Check available space
        try:
            result = subprocess.run(
                ["docker", "system", "df"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                # Parse output for space information
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Images' in line and 'MB' in line or 'GB' in line:
                        # Extract space info if needed
                        pass
        except:
            pass
        
        return health
    
    def _check_docker_compose_plugin(self) -> bool:
        """Check if Docker Compose is available as a plugin"""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def pull_images_with_progress(self, images: List[str]) -> bool:
        """Pull Docker images with progress tracking"""
        self.logger.info(f"📦 Pulling {len(images)} Docker images...")
        
        for i, image in enumerate(images, 1):
            self.logger.info(f"[{i}/{len(images)}] Pulling {image}...")
            
            try:
                # Use docker pull with progress
                process = subprocess.Popen(
                    ["docker", "pull", image],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                last_progress = ""
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    
                    if output:
                        # Extract progress information
                        line = output.strip()
                        if "Downloading" in line or "Extracting" in line:
                            if line != last_progress:
                                self.logger.debug(f"  {line}")
                                last_progress = line
                
                if process.returncode != 0:
                    self.logger.error(f"Failed to pull {image}")
                    return False
                else:
                    self.logger.info(f"✅ Pulled {image}")
                    
            except Exception as e:
                self.logger.error(f"Error pulling {image}: {e}")
                return False
        
        return True
    
    def optimize_images(self) -> bool:
        """Clean up unused Docker images and containers"""
        self.logger.info("🧹 Optimizing Docker images...")
        
        try:
            # Remove dangling images
            subprocess.run(
                ["docker", "image", "prune", "-f"],
                capture_output=True,
                timeout=60
            )
            
            # Remove unused containers
            subprocess.run(
                ["docker", "container", "prune", "-f"],
                capture_output=True,
                timeout=60
            )
            
            self.logger.info("✅ Docker optimization completed")
            return True
            
        except Exception as e:
            self.logger.warning(f"Docker optimization failed: {e}")
            return False

class NetworkValidator:
    """Network connectivity and service validation"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def check_connectivity(self, urls: List[str], timeout: int = 10) -> Dict[str, Any]:
        """Check connectivity to required services"""
        results = {"reachable": [], "unreachable": [], "total_checked": len(urls)}
        
        for url in urls:
            try:
                import requests
                response = requests.get(url, timeout=timeout, allow_redirects=True)
                if response.status_code < 400:
                    results["reachable"].append(url)
                    self.logger.debug(f"✅ {url} - OK ({response.status_code})")
                else:
                    results["unreachable"].append(url)
                    self.logger.debug(f"❌ {url} - HTTP {response.status_code}")
                    
            except Exception as e:
                results["unreachable"].append(url)
                self.logger.debug(f"❌ {url} - {type(e).__name__}: {e}")
        
        success_rate = len(results["reachable"]) / len(urls) * 100
        results["success_rate"] = success_rate
        
        return results
    
    def check_ports(self, host: str, ports: List[int]) -> Dict[str, Any]:
        """Check if specific ports are available/in use"""
        import socket
        
        results = {"available": [], "in_use": [], "total_checked": len(ports)}
        
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    
                    if result == 0:
                        results["in_use"].append(port)
                        self.logger.debug(f"Port {port}: In use")
                    else:
                        results["available"].append(port)
                        self.logger.debug(f"Port {port}: Available")
                        
            except Exception as e:
                self.logger.debug(f"Port {port}: Check failed - {e}")
                results["available"].append(port)  # Assume available if check fails
        
        return results

class SystemResourceMonitor:
    """Monitor system resources during installation"""
    
    def __init__(self, logger):
        self.logger = logger
        self.monitoring = False
        self.resource_history = []
    
    def start_monitoring(self, interval: int = 30):
        """Start resource monitoring in background"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    resources = self.get_current_resources()
                    self.resource_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'resources': resources
                    })
                    
                    # Keep only last 100 entries
                    if len(self.resource_history) > 100:
                        self.resource_history.pop(0)
                    
                    # Check for resource issues
                    self._check_resource_alerts(resources)
                    
                except Exception as e:
                    self.logger.debug(f"Resource monitoring error: {e}")
                
                time.sleep(interval)
        
        import threading
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.debug("Started resource monitoring")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
        
        self.logger.debug("Stopped resource monitoring")
    
    def get_current_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        resources = {}
        
        try:
            # Try to use psutil if available
            import psutil
            
            resources['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            memory = psutil.virtual_memory()
            resources['memory_percent'] = memory.percent
            resources['memory_available_gb'] = memory.available / (1024**3)
            
            disk = psutil.disk_usage('/')
            resources['disk_percent'] = disk.percent
            resources['disk_free_gb'] = disk.free / (1024**3)
            
            resources['load_average'] = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
            
        except ImportError:
            # Fallback methods without psutil
            resources = self._get_resources_without_psutil()
        except Exception as e:
            self.logger.debug(f"Resource check error: {e}")
            resources = {'error': str(e)}
        
        return resources
    
    def _get_resources_without_psutil(self) -> Dict[str, Any]:
        """Get system resources without psutil"""
        resources = {}
        
        try:
            # Memory from /proc/meminfo (Linux)
            if Path('/proc/meminfo').exists():
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                for line in meminfo.split('\n'):
                    if 'MemTotal:' in line:
                        total_kb = int(line.split()[1])
                        resources['memory_total_gb'] = total_kb / (1024**2)
                    elif 'MemAvailable:' in line:
                        available_kb = int(line.split()[1])
                        resources['memory_available_gb'] = available_kb / (1024**2)
            
            # Load average (Linux/macOS)
            try:
                load_avg = os.getloadavg()[0]
                resources['load_average'] = load_avg
            except:
                pass
            
            # Disk space
            try:
                import shutil
                _, _, free = shutil.disk_usage('/')
                resources['disk_free_gb'] = free / (1024**3)
            except:
                pass
                
        except Exception as e:
            resources['fallback_error'] = str(e)
        
        return resources
    
    def _check_resource_alerts(self, resources: Dict[str, Any]):
        """Check for resource usage alerts"""
        # CPU alert
        cpu_percent = resources.get('cpu_percent', 0)
        if cpu_percent > 90:
            self.logger.warning(f"⚠️  High CPU usage: {cpu_percent:.1f}%")
        
        # Memory alert
        memory_percent = resources.get('memory_percent', 0)
        if memory_percent > 85:
            self.logger.warning(f"⚠️  High memory usage: {memory_percent:.1f}%")
        
        # Disk alert
        disk_percent = resources.get('disk_percent', 0)
        if disk_percent > 90:
            self.logger.warning(f"⚠️  Low disk space: {100-disk_percent:.1f}% free")
        
        # Load average alert (Unix-like systems)
        load_avg = resources.get('load_average')
        if load_avg and load_avg > os.cpu_count() * 2:
            self.logger.warning(f"⚠️  High system load: {load_avg:.2f}")

class ConfigurationValidator:
    """Validate generated configuration files"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def validate_docker_compose(self, compose_file: Path) -> Dict[str, Any]:
        """Validate Docker Compose configuration"""
        validation = {"valid": False, "errors": [], "warnings": []}
        
        try:
            # Load and parse YAML
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
            
            # Basic structure validation
            if not isinstance(compose_data, dict):
                validation["errors"].append("Invalid YAML structure")
                return validation
            
            if "services" not in compose_data:
                validation["errors"].append("No services defined")
                return validation
            
            services = compose_data["services"]
            if not isinstance(services, dict) or len(services) == 0:
                validation["errors"].append("No valid services found")
                return validation
            
            # Validate individual services
            for service_name, service_config in services.items():
                service_validation = self._validate_service_config(service_name, service_config)
                validation["errors"].extend(service_validation["errors"])
                validation["warnings"].extend(service_validation["warnings"])
            
            # Check for common issues
            self._check_compose_common_issues(compose_data, validation)
            
            validation["valid"] = len(validation["errors"]) == 0
            
        except yaml.YAMLError as e:
            validation["errors"].append(f"YAML syntax error: {e}")
        except FileNotFoundError:
            validation["errors"].append(f"File not found: {compose_file}")
        except Exception as e:
            validation["errors"].append(f"Validation error: {e}")
        
        return validation
    
    def _validate_service_config(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual service configuration"""
        validation = {"errors": [], "warnings": []}
        
        # Check required fields
        if "image" not in config and "build" not in config:
            validation["errors"].append(f"Service '{name}': No image or build specified")
        
        # Check port mappings
        if "ports" in config:
            for port_mapping in config["ports"]:
                if not self._validate_port_mapping(port_mapping):
                    validation["warnings"].append(f"Service '{name}': Invalid port mapping {port_mapping}")
        
        # Check volumes
        if "volumes" in config:
            for volume in config["volumes"]:
                if not self._validate_volume_mapping(volume):
                    validation["warnings"].append(f"Service '{name}': Invalid volume mapping {volume}")
        
        # Check environment variables
        if "environment" in config:
            env_config = config["environment"]
            if isinstance(env_config, dict):
                for key, value in env_config.items():
                    if not key or not isinstance(key, str):
                        validation["warnings"].append(f"Service '{name}': Invalid environment variable key")
        
        return validation
    
    def _validate_port_mapping(self, port_mapping: str) -> bool:
        """Validate port mapping format"""
        try:
            if ":" in str(port_mapping):
                host_port, container_port = str(port_mapping).split(":", 1)
                return (host_port.isdigit() and container_port.isdigit() and 
                       1 <= int(host_port) <= 65535 and 1 <= int(container_port) <= 65535)
            else:
                port = int(port_mapping)
                return 1 <= port <= 65535
        except:
            return False
    
    def _validate_volume_mapping(self, volume: str) -> bool:
        """Validate volume mapping format"""
        try:
            if isinstance(volume, str):
                if ":" in volume:
                    parts = volume.split(":")
                    return len(parts) >= 2
                else:
                    # Named volume or container path only
                    return len(volume) > 0
            return False
        except:
            return False
    
    def _check_compose_common_issues(self, compose_data: Dict[str, Any], validation: Dict[str, Any]):
        """Check for common Docker Compose issues"""
        services = compose_data.get("services", {})
        
        # Check for port conflicts
        used_ports = []
        for service_name, service_config in services.items():
            if "ports" in service_config:
                for port_mapping in service_config["ports"]:
                    if ":" in str(port_mapping):
                        host_port = str(port_mapping).split(":")[0]
                        if host_port in used_ports:
                            validation["errors"].append(f"Port conflict: {host_port} used by multiple services")
                        used_ports.append(host_port)
        
        # Check for network configuration
        if "networks" not in compose_data:
            validation["warnings"].append("No custom networks defined - services will use default network")
        
        # Check for volume definitions
        services_with_volumes = [name for name, config in services.items() if "volumes" in config]
        if services_with_volumes and "volumes" not in compose_data:
            validation["warnings"].append("Services use volumes but no volumes section defined")
    
    def validate_json_config(self, config_file: Path, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate JSON configuration file"""
        validation = {"valid": False, "errors": [], "warnings": []}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Basic JSON validation passed if we get here
            validation["valid"] = True
            
            # Schema validation if provided
            if schema:
                schema_validation = self._validate_against_schema(config_data, schema)
                validation["errors"].extend(schema_validation["errors"])
                validation["warnings"].extend(schema_validation["warnings"])
                validation["valid"] = len(validation["errors"]) == 0
            
        except json.JSONDecodeError as e:
            validation["errors"].append(f"JSON syntax error: {e}")
        except FileNotFoundError:
            validation["errors"].append(f"File not found: {config_file}")
        except Exception as e:
            validation["errors"].append(f"Validation error: {e}")
        
        return validation
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Simple schema validation (basic implementation)"""
        validation = {"errors": [], "warnings": []}
        
        # This is a simplified schema validator
        # In a full implementation, you'd use jsonschema library
        
        try:
            if "type" in schema:
                expected_type = schema["type"]
                if expected_type == "object" and not isinstance(data, dict):
                    validation["errors"].append("Expected object")
                elif expected_type == "array" and not isinstance(data, list):
                    validation["errors"].append("Expected array")
                elif expected_type == "string" and not isinstance(data, str):
                    validation["errors"].append("Expected string")
                elif expected_type == "number" and not isinstance(data, (int, float)):
                    validation["errors"].append("Expected number")
                elif expected_type == "boolean" and not isinstance(data, bool):
                    validation["errors"].append("Expected boolean")
            
            if "required" in schema and isinstance(data, dict):
                for required_field in schema["required"]:
                    if required_field not in data:
                        validation["errors"].append(f"Missing required field: {required_field}")
            
        except Exception as e:
            validation["errors"].append(f"Schema validation error: {e}")
        
        return validation

class UpdateChecker:
    """Check for installer and component updates"""
    
    def __init__(self, logger, current_version: str = "1.0.0"):
        self.logger = logger
        self.current_version = current_version
        self.update_sources = {
            "installer": "https://api.github.com/repos/noxsuite/installer/releases/latest",
            "noxsuite": "https://api.github.com/repos/noxsuite/noxsuite/releases/latest"
        }
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates"""
        updates = {"available": False, "components": {}}
        
        for component, url in self.update_sources.items():
            try:
                update_info = self._check_component_update(component, url)
                updates["components"][component] = update_info
                
                if update_info.get("update_available", False):
                    updates["available"] = True
                    
            except Exception as e:
                self.logger.debug(f"Update check failed for {component}: {e}")
                updates["components"][component] = {"error": str(e)}
        
        return updates
    
    def _check_component_update(self, component: str, url: str) -> Dict[str, Any]:
        """Check for updates for a specific component"""
        try:
            import requests
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name", "").lstrip("v")
                
                if latest_version and latest_version != self.current_version:
                    return {
                        "update_available": True,
                        "current_version": self.current_version,
                        "latest_version": latest_version,
                        "release_url": release_data.get("html_url"),
                        "release_notes": release_data.get("body", "")[:500] + "..." if len(release_data.get("body", "")) > 500 else release_data.get("body", "")
                    }
                else:
                    return {
                        "update_available": False,
                        "current_version": self.current_version,
                        "latest_version": latest_version or self.current_version
                    }
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def download_update(self, component: str, download_url: str, target_path: Path) -> bool:
        """Download component update"""
        try:
            import requests
            
            self.logger.info(f"📥 Downloading {component} update...")
            
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            progress = downloaded / total_size * 100
                            if progress % 10 < 1:  # Show every 10%
                                self.logger.info(f"  Progress: {progress:.1f}%")
            
            self.logger.info(f"✅ Downloaded {component} update to {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {component} update: {e}")
            return False
