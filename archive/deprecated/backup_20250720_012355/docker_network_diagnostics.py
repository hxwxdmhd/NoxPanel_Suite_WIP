#!/usr/bin/env python3
"""
Docker Network Diagnostics and Redis Connection Manager
Part of Ultimate Suite v11.0 - Development Tools

This script provides comprehensive Docker networking diagnostics
and automated Redis connection management for local development.
"""

import os
import sys
import json
import time
import socket
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import redis
import docker
from docker.models.networks import Network
from docker.models.containers import Container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_network_diagnostics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NetworkDiagnostic:
    """Network diagnostic result"""
    test_name: str
    success: bool
    details: Dict
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass
class RedisConnectionResult:
    """Redis connection test result"""
    host: str
    port: int
    success: bool
    latency_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DockerNetworkDiagnostics:
    """Comprehensive Docker networking diagnostics"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.results: List[NetworkDiagnostic] = []
        
    def run_all_diagnostics(self) -> Dict:
        """Run all network diagnostics"""
        logger.info("Starting Docker network diagnostics...")
        
        # Basic Docker connectivity
        self._test_docker_connectivity()
        
        # Network inspection
        self._inspect_networks()
        
        # Container connectivity
        self._test_container_connectivity()
        
        # Host accessibility
        self._test_host_accessibility()
        
        # Port availability
        self._test_port_availability()
        
        # Generate report
        return self._generate_report()
    
    def _test_docker_connectivity(self):
        """Test basic Docker daemon connectivity"""
        try:
            version = self.client.version()
            self.results.append(NetworkDiagnostic(
                test_name="docker_connectivity",
                success=True,
                details={"version": version},
                timestamp=datetime.now()
            ))
            logger.info("✅ Docker connectivity successful")
        except Exception as e:
            self.results.append(NetworkDiagnostic(
                test_name="docker_connectivity",
                success=False,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
            logger.error(f"❌ Docker connectivity failed: {e}")
    
    def _inspect_networks(self):
        """Inspect Docker networks"""
        try:
            networks = self.client.networks.list()
            network_info = []
            
            for network in networks:
                network_info.append({
                    "name": network.name,
                    "driver": network.attrs.get("Driver"),
                    "scope": network.attrs.get("Scope"),
                    "ipam": network.attrs.get("IPAM", {}),
                    "containers": len(network.containers)
                })
            
            self.results.append(NetworkDiagnostic(
                test_name="network_inspection",
                success=True,
                details={"networks": network_info},
                timestamp=datetime.now()
            ))
            logger.info(f"✅ Found {len(networks)} Docker networks")
        except Exception as e:
            self.results.append(NetworkDiagnostic(
                test_name="network_inspection",
                success=False,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
            logger.error(f"❌ Network inspection failed: {e}")
    
    def _test_container_connectivity(self):
        """Test connectivity between containers"""
        try:
            containers = self.client.containers.list()
            container_info = []
            
            for container in containers:
                networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
                container_info.append({
                    "name": container.name,
                    "status": container.status,
                    "networks": list(networks.keys()),
                    "ip_addresses": [net.get("IPAddress") for net in networks.values()]
                })
            
            self.results.append(NetworkDiagnostic(
                test_name="container_connectivity",
                success=True,
                details={"containers": container_info},
                timestamp=datetime.now()
            ))
            logger.info(f"✅ Found {len(containers)} running containers")
        except Exception as e:
            self.results.append(NetworkDiagnostic(
                test_name="container_connectivity",
                success=False,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
            logger.error(f"❌ Container connectivity test failed: {e}")
    
    def _test_host_accessibility(self):
        """Test host accessibility from container perspective"""
        try:
            # Test common host addresses
            host_addresses = [
                "host.docker.internal",
                "172.17.0.1",  # Default Docker bridge gateway
                "192.168.65.1",  # Docker Desktop on Mac
                "10.0.75.1",   # Docker Desktop on Windows
                "localhost"
            ]
            
            accessible_hosts = []
            for host in host_addresses:
                try:
                    socket.gethostbyname(host)
                    accessible_hosts.append(host)
                except socket.gaierror:
                    pass
            
            self.results.append(NetworkDiagnostic(
                test_name="host_accessibility",
                success=len(accessible_hosts) > 0,
                details={"accessible_hosts": accessible_hosts},
                timestamp=datetime.now()
            ))
            logger.info(f"✅ Host accessibility: {accessible_hosts}")
        except Exception as e:
            self.results.append(NetworkDiagnostic(
                test_name="host_accessibility",
                success=False,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
            logger.error(f"❌ Host accessibility test failed: {e}")
    
    def _test_port_availability(self):
        """Test port availability on host"""
        try:
            ports_to_test = [5000, 5001, 5002, 6379, 6380, 3000, 8081, 9090]
            available_ports = []
            occupied_ports = []
            
            for port in ports_to_test:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    occupied_ports.append(port)
                else:
                    available_ports.append(port)
            
            self.results.append(NetworkDiagnostic(
                test_name="port_availability",
                success=True,
                details={
                    "available_ports": available_ports,
                    "occupied_ports": occupied_ports
                },
                timestamp=datetime.now()
            ))
            logger.info(f"✅ Port availability checked: {len(available_ports)} available, {len(occupied_ports)} occupied")
        except Exception as e:
            self.results.append(NetworkDiagnostic(
                test_name="port_availability",
                success=False,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
            logger.error(f"❌ Port availability test failed: {e}")
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive diagnostic report"""
        successful_tests = sum(1 for r in self.results if r.success)
        total_tests = len(self.results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "results": [asdict(r) for r in self.results]
        }
        
        return report

class RedisConnectionManager:
    """Redis connection manager with Docker networking support"""
    
    def __init__(self):
        self.test_results: List[RedisConnectionResult] = []
    
    def test_redis_connections(self) -> List[RedisConnectionResult]:
        """Test Redis connections with various configurations"""
        logger.info("Testing Redis connections...")
        
        # Test configurations
        test_configs = [
            ("localhost", 6379),
            ("127.0.0.1", 6379),
            ("host.docker.internal", 6379),
            ("172.17.0.1", 6379),
            ("localhost", 6380),
            ("127.0.0.1", 6380),
        ]
        
        for host, port in test_configs:
            result = self._test_redis_connection(host, port)
            self.test_results.append(result)
            
            if result.success:
                logger.info(f"✅ Redis connection successful: {host}:{port} ({result.latency_ms:.2f}ms)")
            else:
                logger.warning(f"❌ Redis connection failed: {host}:{port} - {result.error_message}")
        
        return self.test_results
    
    def _test_redis_connection(self, host: str, port: int, password: str = None) -> RedisConnectionResult:
        """Test individual Redis connection"""
        start_time = time.time()
        
        try:
            # Create Redis client
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True
            )
            
            # Test connection
            client.ping()
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            return RedisConnectionResult(
                host=host,
                port=port,
                success=True,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            return RedisConnectionResult(
                host=host,
                port=port,
                success=False,
                latency_ms=0,
                error_message=str(e)
            )
    
    def get_best_redis_config(self) -> Optional[Tuple[str, int]]:
        """Get the best Redis configuration"""
        successful_connections = [r for r in self.test_results if r.success]
        
        if not successful_connections:
            return None
        
        # Sort by latency
        best_connection = min(successful_connections, key=lambda x: x.latency_ms)
        return (best_connection.host, best_connection.port)

class DockerNetworkFixer:
    """Automated Docker network issue resolver"""
    
    def __init__(self):
        self.client = docker.from_env()
    
    def fix_redis_connectivity(self) -> Dict:
        """Fix Redis connectivity issues"""
        logger.info("Attempting to fix Redis connectivity issues...")
        
        fixes_applied = []
        
        # 1. Check if Redis container is running
        redis_fix = self._ensure_redis_container()
        if redis_fix:
            fixes_applied.append(redis_fix)
        
        # 2. Create or update network
        network_fix = self._ensure_development_network()
        if network_fix:
            fixes_applied.append(network_fix)
        
        # 3. Start Redis service if needed
        service_fix = self._start_redis_service()
        if service_fix:
            fixes_applied.append(service_fix)
        
        return {
            "fixes_applied": fixes_applied,
            "timestamp": datetime.now().isoformat()
        }
    
    def _ensure_redis_container(self) -> Optional[str]:
        """Ensure Redis container is available"""
        try:
            container = self.client.containers.get("heimnetz-redis-dev")
            if container.status != "running":
                container.start()
                return "Started existing Redis container"
        except docker.errors.NotFound:
            # Container doesn't exist, will be created by docker-compose
            return "Redis container needs to be created"
        except Exception as e:
            logger.error(f"Error with Redis container: {e}")
            return None
    
    def _ensure_development_network(self) -> Optional[str]:
        """Ensure development network exists"""
        try:
            network = self.client.networks.get("heimnetz-dev-network")
            return None  # Network already exists
        except docker.errors.NotFound:
            # Create network
            network = self.client.networks.create(
                "heimnetz-dev-network",
                driver="bridge",
                ipam=docker.types.IPAMConfig(
                    pool_configs=[
                        docker.types.IPAMPool(
                            subnet="172.28.0.0/16",
                            gateway="172.28.0.1"
                        )
                    ]
                )
            )
            return "Created development network"
        except Exception as e:
            logger.error(f"Error with development network: {e}")
            return None
    
    def _start_redis_service(self) -> Optional[str]:
        """Start Redis service using docker-compose"""
        try:
            # Use docker-compose to start Redis
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.dev-networking.yml", "up", "-d", "redis-dev"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                return "Started Redis service via docker-compose"
            else:
                logger.error(f"Failed to start Redis service: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting Redis service: {e}")
            return None

def main():
    """Main function"""
    print("🔧 Docker Network Diagnostics and Redis Connection Manager")
    print("=" * 60)
    
    # Run diagnostics
    diagnostics = DockerNetworkDiagnostics()
    diagnostic_report = diagnostics.run_all_diagnostics()
    
    # Test Redis connections
    redis_manager = RedisConnectionManager()
    redis_results = redis_manager.test_redis_connections()
    
    # Get best Redis config
    best_config = redis_manager.get_best_redis_config()
    
    # Print summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("-" * 30)
    print(f"Network Tests: {diagnostic_report['summary']['success_rate']}")
    print(f"Redis Tests: {len([r for r in redis_results if r.success])}/{len(redis_results)} successful")
    
    if best_config:
        print(f"Best Redis Config: {best_config[0]}:{best_config[1]}")
    else:
        print("❌ No working Redis configuration found")
        
        # Try to fix issues
        print("\n🔧 Attempting to fix Redis connectivity...")
        fixer = DockerNetworkFixer()
        fix_results = fixer.fix_redis_connectivity()
        
        print(f"Fixes applied: {len(fix_results['fixes_applied'])}")
        for fix in fix_results['fixes_applied']:
            print(f"  - {fix}")
    
    # Save detailed report
    report_path = "docker_network_diagnostic_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            "diagnostic_report": diagnostic_report,
            "redis_results": [asdict(r) for r in redis_results],
            "best_config": best_config
        }, f, indent=2, default=str)
    
    print(f"\n📁 Detailed report saved to: {report_path}")
    
    return best_config is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
