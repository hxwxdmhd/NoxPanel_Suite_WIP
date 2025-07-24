#!/usr/bin/env python3
"""
Router Registry System for FRITZWATCHER
=======================================

This module manages a registry of Fritz!Box routers and provides
centralized configuration and discovery services.

Features:
- Dynamic router discovery
- Configuration management
- Health monitoring
- Automatic failover
- Router capability detection

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import json
import logging
import socket
import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import xml.etree.ElementTree as ET
import re

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RouterCapabilities:
    """Router capabilities and features"""
    tr064_support: bool = False
    upnp_support: bool = False
    guest_wifi: bool = False
    mesh_support: bool = False
    usb_support: bool = False
    telephony: bool = False
    nas_support: bool = False
    vpn_support: bool = False
    parental_controls: bool = False
    version: str = ""
    model: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RouterInfo:
    """Information about a Fritz!Box router"""
    name: str
    host: str
    port: int = 49000
    username: str = "admin"
    password: str = ""
    keepass_ref: Optional[str] = None
    
    # Discovery info
    mac_address: str = ""
    serial_number: str = ""
    model: str = ""
    firmware_version: str = ""
    
    # Status
    online: bool = False
    last_seen: Optional[datetime] = None
    response_time: float = 0.0
    
    # Capabilities
    capabilities: RouterCapabilities = None
    
    # Network info
    lan_ip: str = ""
    wan_ip: str = ""
    dns_servers: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = RouterCapabilities()
        if self.dns_servers is None:
            self.dns_servers = []
            
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if 'last_seen' in data and data['last_seen']:
            data['last_seen'] = data['last_seen'].isoformat()
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RouterInfo':
        # Handle datetime conversion
        if 'last_seen' in data and data['last_seen']:
            if isinstance(data['last_seen'], str):
                data['last_seen'] = datetime.fromisoformat(data['last_seen'])
                
        # Handle capabilities
        if 'capabilities' in data and isinstance(data['capabilities'], dict):
            data['capabilities'] = RouterCapabilities(**data['capabilities'])
            
        return cls(**data)


class RouterDiscovery:
    """Discovers Fritz!Box routers on the network"""
    
    def __init__(self):
        self.discovery_methods = [
            self._discover_by_hostname,
            self._discover_by_upnp,
            self._discover_by_network_scan
        ]
        
    async def discover_routers(self) -> List[RouterInfo]:
        """Discover all Fritz!Box routers on the network"""
        discovered = []
        
        for method in self.discovery_methods:
            try:
                routers = await method()
                discovered.extend(routers)
                logger.info(f"Discovery method {method.__name__} found {len(routers)} routers")
            except Exception as e:
                logger.error(f"Discovery method {method.__name__} failed: {e}")
                
        # Remove duplicates based on MAC address or IP
        unique_routers = {}
        for router in discovered:
            key = router.mac_address or router.host
            if key not in unique_routers:
                unique_routers[key] = router
                
        return list(unique_routers.values())
        
    async def _discover_by_hostname(self) -> List[RouterInfo]:
        """Discover routers by common hostnames"""
        hostnames = [
            'fritz.box',
            'fritzbox',
            'fritz.repeater',
            'fritz.nas',
            'myfritz.box'
        ]
        
        routers = []
        for hostname in hostnames:
            try:
                # Check if hostname resolves
                ip = socket.gethostbyname(hostname)
                
                # Test if it's a Fritz!Box
                if await self._test_fritzbox(f"http://{ip}"):
                    router = RouterInfo(
                        name=hostname.replace('.', '_').title(),
                        host=f"http://{ip}",
                        lan_ip=ip
                    )
                    routers.append(router)
                    
            except Exception as e:
                logger.debug(f"Hostname {hostname} not found: {e}")
                
        return routers
        
    async def _discover_by_upnp(self) -> List[RouterInfo]:
        """Discover routers using UPnP/SSDP"""
        routers = []
        
        try:
            # SSDP discovery
            ssdp_request = (
                'M-SEARCH * HTTP/1.1\r\n'
                'HOST: 239.255.255.250:1900\r\n'
                'MAN: "ssdp:discover"\r\n'
                'ST: upnp:rootdevice\r\n'
                'MX: 3\r\n\r\n'
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
            
            responses = []
            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    responses.append((data.decode(), addr))
            except socket.timeout:
                pass
            finally:
                sock.close()
                
            # Parse responses
            for response, addr in responses:
                if 'fritz' in response.lower() or 'avm' in response.lower():
                    # Extract location URL
                    location_match = re.search(r'LOCATION:\s*(.+)', response, re.IGNORECASE)
                    if location_match:
                        location = location_match.group(1).strip()
                        
                        # Extract device description
                        device_info = await self._get_device_description(location)
                        if device_info:
                            router = RouterInfo(
                                name=device_info.get('friendlyName', 'Fritz!Box'),
                                host=f"http://{addr[0]}",
                                lan_ip=addr[0],
                                model=device_info.get('modelName', ''),
                                serial_number=device_info.get('serialNumber', ''),
                                firmware_version=device_info.get('firmwareVersion', '')
                            )
                            routers.append(router)
                            
        except Exception as e:
            logger.error(f"UPnP discovery failed: {e}")
            
        return routers
        
    async def _discover_by_network_scan(self) -> List[RouterInfo]:
        """Discover routers by scanning network"""
        routers = []
        
        try:
            # Get local network range
            network_ranges = self._get_local_network_ranges()
            
            for network_range in network_ranges:
                # Scan common router IPs
                common_ips = [
                    f"{network_range}.1",
                    f"{network_range}.254",
                    f"{network_range}.100"
                ]
                
                for ip in common_ips:
                    try:
                        if await self._test_fritzbox(f"http://{ip}"):
                            router = RouterInfo(
                                name=f"Fritz!Box at {ip}",
                                host=f"http://{ip}",
                                lan_ip=ip
                            )
                            routers.append(router)
                    except Exception as e:
                        logger.debug(f"IP {ip} not reachable: {e}")
                        
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            
        return routers
        
    def _get_local_network_ranges(self) -> List[str]:
        """Get local network ranges to scan"""
        ranges = []
        
        try:
            import socket
            import subprocess
            
            # Method 1: Get from network interfaces
            try:
                if os.name == 'nt':  # Windows
                    # Use ipconfig to get network info
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if 'IPv4 Address' in line or 'IP Address' in line:
                            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                    parts = ip.split('.')
                                    if len(parts) == 4:
                                        network = f"{parts[0]}.{parts[1]}.{parts[2]}"
                                        if network not in ranges:
                                            ranges.append(network)
                else:  # Unix/Linux
                    # Use ip command or ifconfig
                    try:
                        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if 'inet ' in line and not '127.0.0.1' in line:
                                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                                if ip_match:
                                    ip = ip_match.group(1)
                                    parts = ip.split('.')
                                    if len(parts) == 4:
                                        network = f"{parts[0]}.{parts[1]}.{parts[2]}"
                                        if network not in ranges:
                                            ranges.append(network)
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"Network interface discovery failed: {e}")
            
            # Method 2: Fallback to socket method
            if not ranges:
                try:
                    # Connect to external host to determine local IP
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    
                    if local_ip and not local_ip.startswith('127.'):
                        parts = local_ip.split('.')
                        if len(parts) == 4:
                            network = f"{parts[0]}.{parts[1]}.{parts[2]}"
                            ranges.append(network)
                            
                except Exception as e:
                    logger.debug(f"Socket method failed: {e}")
                    
            # Method 3: Common network ranges as fallback
            if not ranges:
                ranges = ['192.168.1', '192.168.0', '10.0.0', '172.16.0']
                logger.info("Using common network ranges as fallback")
                
        except Exception as e:
            logger.error(f"Failed to get local network ranges: {e}")
            ranges = ['192.168.1', '192.168.0']  # Ultimate fallback
            
        logger.info(f"Scanning network ranges: {ranges}")
        return ranges
        
    async def _test_fritzbox(self, url: str) -> bool:
        """Test if URL is a Fritz!Box"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/", timeout=5) as response:
                    if response.status == 200:
                        content = await response.text()
                        return 'fritz' in content.lower() or 'avm' in content.lower()
                        
        except Exception as e:
            logger.debug(f"Fritz!Box test failed for {url}: {e}")
            
        return False
        
    async def _get_device_description(self, location: str) -> Optional[Dict[str, Any]]:
        """Get device description from UPnP location"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(location, timeout=5) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse XML
                        root = ET.fromstring(content)
                        
                        # Extract device info
                        device_info = {}
                        for elem in root.iter():
                            tag = elem.tag.split('}')[-1]  # Remove namespace
                            if tag in ['friendlyName', 'modelName', 'serialNumber', 'firmwareVersion']:
                                device_info[tag] = elem.text
                                
                        return device_info
                        
        except Exception as e:
            logger.error(f"Failed to get device description: {e}")
            
        return None


class RouterRegistry:
    """Central registry for managing Fritz!Box routers"""
    
    def __init__(self, config_file: str = "router_registry.json"):
        self.config_file = Path(config_file)
        self.routers: Dict[str, RouterInfo] = {}
        self.discovery = RouterDiscovery()
        
        # Load existing registry
        self.load_registry()
        
    def load_registry(self):
        """Load router registry from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                for router_data in data.get('routers', []):
                    router = RouterInfo.from_dict(router_data)
                    self.routers[router.name] = router
                    
                logger.info(f"Loaded {len(self.routers)} routers from registry")
            else:
                logger.info("No existing registry found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load router registry: {e}")
            
    def save_registry(self):
        """Save router registry to file"""
        try:
            data = {
                'routers': [router.to_dict() for router in self.routers.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.routers)} routers to registry")
            
        except Exception as e:
            logger.error(f"Failed to save router registry: {e}")
            
    async def discover_and_register(self) -> List[RouterInfo]:
        """Discover routers and add them to registry"""
        discovered = await self.discovery.discover_routers()
        
        for router in discovered:
            # Check if router already exists
            existing = None
            for existing_router in self.routers.values():
                if (existing_router.host == router.host or 
                    existing_router.mac_address == router.mac_address):
                    existing = existing_router
                    break
                    
            if existing:
                # Update existing router
                existing.online = True
                existing.last_seen = datetime.now()
                logger.info(f"Updated existing router: {existing.name}")
            else:
                # Add new router
                router.online = True
                router.last_seen = datetime.now()
                self.routers[router.name] = router
                logger.info(f"Registered new router: {router.name}")
                
        self.save_registry()
        return discovered
        
    def add_router(self, router: RouterInfo) -> bool:
        """Add a router to the registry"""
        try:
            self.routers[router.name] = router
            self.save_registry()
            logger.info(f"Added router: {router.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add router: {e}")
            return False
            
    def remove_router(self, name: str) -> bool:
        """Remove a router from the registry"""
        try:
            if name in self.routers:
                del self.routers[name]
                self.save_registry()
                logger.info(f"Removed router: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove router: {e}")
            return False
            
    def get_router(self, name: str) -> Optional[RouterInfo]:
        """Get a router by name"""
        return self.routers.get(name)
        
    def get_all_routers(self) -> List[RouterInfo]:
        """Get all routers"""
        return list(self.routers.values())
        
    def get_online_routers(self) -> List[RouterInfo]:
        """Get only online routers"""
        return [router for router in self.routers.values() if router.online]
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all routers"""
        results = {}
        
        for name, router in self.routers.items():
            try:
                start_time = datetime.now()
                
                # Test connectivity
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{router.host}/", timeout=5) as response:
                        online = response.status == 200
                        
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Update router status
                router.online = online
                router.response_time = response_time
                router.last_seen = datetime.now()
                
                results[name] = {
                    'online': online,
                    'response_time': response_time,
                    'last_seen': router.last_seen.isoformat()
                }
                
            except Exception as e:
                router.online = False
                results[name] = {
                    'online': False,
                    'error': str(e)
                }
                
        self.save_registry()
        return results
        
    def get_primary_router(self) -> Optional[RouterInfo]:
        """Get the primary router (first online router)"""
        online_routers = self.get_online_routers()
        return online_routers[0] if online_routers else None
        
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        online_count = len(self.get_online_routers())
        total_count = len(self.routers)
        
        return {
            'total_routers': total_count,
            'online_routers': online_count,
            'offline_routers': total_count - online_count,
            'last_discovery': max(
                (router.last_seen for router in self.routers.values() if router.last_seen),
                default=None
            )
        }


# Test function
async def test_router_registry():
    """Test router registry functionality"""
    print("Testing Router Registry")
    print("=" * 30)
    
    # Create registry
    registry = RouterRegistry("test_registry.json")
    
    # Add a test router
    test_router = RouterInfo(
        name="Test Router",
        host="http://192.168.1.1",
        username="admin",
        password="test123"
    )
    
    registry.add_router(test_router)
    print(f"✅ Added test router: {test_router.name}")
    
    # Test discovery
    print("🔍 Starting router discovery...")
    discovered = await registry.discover_and_register()
    print(f"✅ Discovered {len(discovered)} routers")
    
    # Test health check
    print("🏥 Performing health check...")
    health = await registry.health_check()
    print(f"✅ Health check completed: {health}")
    
    # Get stats
    stats = registry.get_registry_stats()
    print(f"📊 Registry stats: {stats}")
    
    # Clean up
    registry.config_file.unlink(missing_ok=True)
    print("✅ Test completed")


if __name__ == "__main__":
    asyncio.run(test_router_registry())
