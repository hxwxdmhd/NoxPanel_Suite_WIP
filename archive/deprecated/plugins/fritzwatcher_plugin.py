#!/usr/bin/env python3
"""
FRITZWATCHER Plugin - Advanced Fritz!Box Monitoring System
==========================================================

This plugin provides comprehensive monitoring and management of Fritz!Box
routers using the TR-064 SOAP API with secure credential management.

Features:
- Multi-router support with roaming device tracking
- Secure credential management via KeePassXC/KeePass
- Real-time device monitoring and control
- Guest Wi-Fi management
- Signal quality monitoring
- Device session tracking across routers

Codename: FRITZWATCHER
Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import json
import logging
import time
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Import resilience framework
from fritzwatcher_resilience import (
    get_resilience_manager, 
    configure_resilience, 
    RetryConfig, 
    FailoverConfig,
    with_retry,
    with_failover
)
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
import re

# Import plugin framework
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the plugin system
try:
    from unified_plugin_system_clean import ServicePlugin, PluginInfo
except ImportError:
    try:
        from NoxPanel.unified_plugin_system_clean import ServicePlugin, PluginInfo
    except ImportError:
        # Create minimal stub classes for testing
        class ServicePlugin:
            def __init__(self):
                pass
            def get_service_status(self) -> Dict[str, Any]:
                return {}
            def start_service(self) -> bool:
                return True
            def stop_service(self) -> bool:
                return True
        
        class PluginInfo:
            def __init__(self, name, version, description, author, category, dependencies):
                self.name = name
                self.version = version
                self.description = description
                self.author = author
                self.category = category
                self.dependencies = dependencies
try:
    from plugins.keepass_helper import KeePassHelper, FritzBoxCredentialManager, create_keepass_helper
except ImportError:
    # Create minimal stub classes for testing
    class KeePassHelper:
        def __init__(self, config):
            pass
        def get_credentials(self, ref):
            return None
    
    class FritzBoxCredentialManager:
        def __init__(self, helper):
            self.helper = helper
        def get_router_credentials(self, config):
            return None
    
    def create_keepass_helper(config):
        return KeePassHelper(config)

# Configure logging
logger = logging.getLogger(__name__)

class FritzBoxDevice:
    """Represents a connected device on Fritz!Box network"""
    
    def __init__(self, data: Dict[str, Any]):
        self.mac_address = data.get('mac_address', '')
        self.ip_address = data.get('ip_address', '')
        self.hostname = data.get('hostname', '')
        self.interface = data.get('interface', '')
        self.connection_type = data.get('connection_type', '')
        self.connected = data.get('connected', False)
        self.signal_strength = data.get('signal_strength', 0)
        self.last_seen = data.get('last_seen', datetime.now())
        self.router_name = data.get('router_name', '')
        self.device_info = data.get('device_info', {})
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary"""
        return {
            'mac_address': self.mac_address,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'interface': self.interface,
            'connection_type': self.connection_type,
            'connected': self.connected,
            'signal_strength': self.signal_strength,
            'last_seen': self.last_seen.isoformat(),
            'router_name': self.router_name,
            'device_info': self.device_info
        }


class FritzBoxRouter:
    """Represents a Fritz!Box router with API access"""
    
    def __init__(self, config: Dict[str, Any], credential_manager: FritzBoxCredentialManager):
        self.name = config.get('name', 'Fritz!Box')
        self.host = config.get('host', 'http://fritz.box')
        self.port = config.get('port', 49000)
        self.username = config.get('username', 'admin')
        self.password = config.get('password', '')
        self.keepass_ref = config.get('keepass_ref')
        self.credential_manager = credential_manager
        
        # API endpoints
        self.base_url = f"{self.host}:{self.port}"
        self.tr64_desc_url = f"{self.base_url}/tr64desc.xml"
        
        # Session management
        self.session_id = None
        self.session_expires = None
        self.services = {}
        
        # Device tracking
        self.devices = {}
        self.last_update = None
        
        logger.info(f"Fritz!Box router initialized: {self.name} at {self.host}")
        
    async def authenticate(self) -> bool:
        """Authenticate with Fritz!Box using TR-064 protocol"""
        try:
            # Get credentials
            if self.keepass_ref:
                credentials = self.credential_manager.get_router_credentials({
                    'keepass_ref': self.keepass_ref,
                    'username': self.username,
                    'password': self.password
                })
                if credentials:
                    self.username = credentials['username']
                    self.password = credentials['password']
                else:
                    logger.error(f"Failed to get credentials for {self.name}")
                    return False
                    
            # Test connection with device info request
            device_info = await self.get_device_info()
            if device_info:
                logger.info(f"Authentication successful for {self.name}")
                return True
            else:
                logger.error(f"Authentication failed for {self.name}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error for {self.name}: {e}")
            return False
            
    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get basic device information"""
        try:
            # TR-064 SOAP request for device info
            soap_action = 'urn:dslforum-org:service:DeviceInfo:1#GetInfo'
            soap_body = """
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" 
                       s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
                <s:Body>
                    <u:GetInfo xmlns:u="urn:dslforum-org:service:DeviceInfo:1"/>
                </s:Body>
            </s:Envelope>
            """
            
            result = await self._make_soap_request(
                '/upnp/control/deviceinfo',
                soap_action,
                soap_body
            )
            
            if result:
                return {
                    'model': result.get('ModelName', ''),
                    'serial': result.get('SerialNumber', ''),
                    'firmware': result.get('SoftwareVersion', ''),
                    'uptime': result.get('UpTime', 0),
                    'hardware_version': result.get('HardwareVersion', '')
                }
                
        except Exception as e:
            logger.error(f"Failed to get device info for {self.name}: {e}")
            
        return None
        
    async def get_connected_devices(self) -> List[FritzBoxDevice]:
        """Get list of connected devices"""
        try:
            devices = []
            
            # Get hosts list
            hosts_data = await self._get_hosts_list()
            if hosts_data:
                for host_data in hosts_data:
                    device = FritzBoxDevice({
                        'mac_address': host_data.get('MACAddress', ''),
                        'ip_address': host_data.get('IPAddress', ''),
                        'hostname': host_data.get('HostName', ''),
                        'interface': host_data.get('InterfaceType', ''),
                        'connected': host_data.get('Active', False),
                        'last_seen': datetime.now(),
                        'router_name': self.name,
                        'device_info': host_data
                    })
                    devices.append(device)
                    
            # Get WiFi devices for signal strength
            wifi_devices = await self._get_wifi_devices()
            if wifi_devices:
                for device in devices:
                    if device.mac_address in wifi_devices:
                        device.signal_strength = wifi_devices[device.mac_address].get('signal', 0)
                        device.connection_type = 'WiFi'
                        
            self.devices = {d.mac_address: d for d in devices}
            self.last_update = datetime.now()
            
            logger.info(f"Found {len(devices)} devices on {self.name}")
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get connected devices for {self.name}: {e}")
            return []
            
    async def _get_hosts_list(self) -> List[Dict[str, Any]]:
        """Get hosts list from Fritz!Box"""
        try:
            soap_action = 'urn:dslforum-org:service:Hosts:1#GetHostNumberOfEntries'
            soap_body = """
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
                <s:Body>
                    <u:GetHostNumberOfEntries xmlns:u="urn:dslforum-org:service:Hosts:1"/>
                </s:Body>
            </s:Envelope>
            """
            
            result = await self._make_soap_request(
                '/upnp/control/hosts',
                soap_action,
                soap_body
            )
            
            if result and 'HostNumberOfEntries' in result:
                num_entries = int(result['HostNumberOfEntries'])
                hosts = []
                
                # Get each host entry
                for i in range(num_entries):
                    host_data = await self._get_host_entry(i)
                    if host_data:
                        hosts.append(host_data)
                        
                return hosts
                
        except Exception as e:
            logger.error(f"Failed to get hosts list: {e}")
            
        return []
        
    async def _get_host_entry(self, index: int) -> Optional[Dict[str, Any]]:
        """Get specific host entry by index"""
        try:
            soap_action = 'urn:dslforum-org:service:Hosts:1#GetGenericHostEntry'
            soap_body = f"""
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
                <s:Body>
                    <u:GetGenericHostEntry xmlns:u="urn:dslforum-org:service:Hosts:1">
                        <NewIndex>{index}</NewIndex>
                    </u:GetGenericHostEntry>
                </s:Body>
            </s:Envelope>
            """
            
            result = await self._make_soap_request(
                '/upnp/control/hosts',
                soap_action,
                soap_body
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get host entry {index}: {e}")
            return None
            
    async def _get_wifi_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get WiFi devices with signal strength"""
        try:
            wifi_devices = {}
            
            # Get WiFi configuration for signal strength
            # This is a simplified implementation
            # Full implementation would query WLAN configuration services
            
            return wifi_devices
            
        except Exception as e:
            logger.error(f"Failed to get WiFi devices: {e}")
            return {}
            
    async def get_guest_wifi_status(self) -> Dict[str, Any]:
        """Get guest WiFi status"""
        try:
            soap_action = 'urn:dslforum-org:service:WLANConfiguration:1#GetInfo'
            soap_body = """
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
                <s:Body>
                    <u:GetInfo xmlns:u="urn:dslforum-org:service:WLANConfiguration:1"/>
                </s:Body>
            </s:Envelope>
            """
            
            result = await self._make_soap_request(
                '/upnp/control/wlanconfig1',  # Guest WiFi is usually wlanconfig1
                soap_action,
                soap_body
            )
            
            if result:
                return {
                    'enabled': result.get('Enable', False),
                    'ssid': result.get('SSID', ''),
                    'channel': result.get('Channel', 0),
                    'status': result.get('Status', '')
                }
                
        except Exception as e:
            logger.error(f"Failed to get guest WiFi status: {e}")
            
        return {}
        
    async def toggle_guest_wifi(self, enabled: bool) -> bool:
        """Toggle guest WiFi on/off"""
        try:
            soap_action = 'urn:dslforum-org:service:WLANConfiguration:1#SetEnable'
            soap_body = f"""
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
                <s:Body>
                    <u:SetEnable xmlns:u="urn:dslforum-org:service:WLANConfiguration:1">
                        <NewEnable>{1 if enabled else 0}</NewEnable>
                    </u:SetEnable>
                </s:Body>
            </s:Envelope>
            """
            
            result = await self._make_soap_request(
                '/upnp/control/wlanconfig1',
                soap_action,
                soap_body
            )
            
            if result is not None:
                logger.info(f"Guest WiFi {'enabled' if enabled else 'disabled'} on {self.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to toggle guest WiFi: {e}")
            
        return False
        
    async def _make_soap_request(self, endpoint: str, soap_action: str, soap_body: str) -> Optional[Dict[str, Any]]:
        """Make SOAP request to Fritz!Box"""
        try:
            url = urljoin(self.base_url, endpoint)
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': soap_action
            }
            
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data=soap_body, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_soap_response(content)
                    else:
                        logger.error(f"SOAP request failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"SOAP request error: {e}")
            
        return None
        
    def _parse_soap_response(self, content: str) -> Dict[str, Any]:
        """Parse SOAP response XML"""
        try:
            root = ET.fromstring(content)
            
            # Find the response body
            namespaces = {
                's': 'http://schemas.xmlsoap.org/soap/envelope/',
                'u': 'urn:dslforum-org:service:DeviceInfo:1'
            }
            
            body = root.find('.//s:Body', namespaces)
            if body is not None:
                result = {}
                for elem in body.iter():
                    if elem.text and elem.tag.split('}')[-1] not in ['Body', 'Envelope']:
                        key = elem.tag.split('}')[-1]
                        result[key] = elem.text
                        
                return result
                
        except Exception as e:
            logger.error(f"Failed to parse SOAP response: {e}")
            
        return {}


class RoamingTracker:
    """Tracks device roaming between multiple routers"""
    
    def __init__(self):
        self.device_history = {}
        self.roaming_events = []
        
    def update_device_locations(self, devices_by_router: Dict[str, List[FritzBoxDevice]]):
        """Update device locations and detect roaming"""
        current_time = datetime.now()
        
        for router_name, devices in devices_by_router.items():
            for device in devices:
                mac = device.mac_address
                
                # Check if device has moved
                if mac in self.device_history:
                    last_router = self.device_history[mac].get('router')
                    if last_router != router_name:
                        # Device has roamed
                        self.roaming_events.append({
                            'mac_address': mac,
                            'hostname': device.hostname,
                            'from_router': last_router,
                            'to_router': router_name,
                            'timestamp': current_time,
                            'event_type': 'roaming'
                        })
                        
                        logger.info(f"Device {device.hostname} ({mac}) roamed from {last_router} to {router_name}")
                        
                # Update device history
                self.device_history[mac] = {
                    'router': router_name,
                    'last_seen': current_time,
                    'hostname': device.hostname,
                    'ip_address': device.ip_address
                }
                
    def get_roaming_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get roaming events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [event for event in self.roaming_events if event['timestamp'] > cutoff_time]
        
    def get_device_current_router(self, mac_address: str) -> Optional[str]:
        """Get current router for a device"""
        return self.device_history.get(mac_address, {}).get('router')


class FritzWatcherPlugin(ServicePlugin):
    """Main FRITZWATCHER plugin class"""
    
    def __init__(self):
        super().__init__()
        self.routers = {}
        self.credential_manager = None
        self.keepass_helper = None
        self.roaming_tracker = RoamingTracker()
        self.monitoring_task = None
        self.update_interval = 30  # seconds
        
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name="FRITZWATCHER",
            version="1.0.0",
            description="Advanced Fritz!Box monitoring and management system",
            author="MSP-Aware Development Team",
            category="networking",
            dependencies=["aiohttp", "xml.etree.ElementTree"]
        )
        
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the plugin"""
        try:
            self.config = config or {}
            
            # Initialize KeePass helper
            keepass_config = self.config.get('keepass', {})
            self.keepass_helper = create_keepass_helper(keepass_config)
            
            # Initialize credential manager
            self.credential_manager = FritzBoxCredentialManager(self.keepass_helper)
            
            # Initialize routers
            router_configs = self.config.get('routers', [])
            
            # Auto-discover routers if none configured
            if not router_configs and self.config.get('auto_discover', True):
                print("🔍 Auto-discovering Fritz!Box routers...")
                # Use router registry for discovery
                from router_registry import RouterRegistry
                registry = RouterRegistry()
                
                # Store registry for later async discovery
                self.registry = registry
                
                # For now, add default router that will be discovered later
                router_configs.append({
                    'name': 'Fritz!Box',
                    'host': 'http://fritz.box',
                    'username': 'admin',
                    'password': '',
                    'auto_discovered': True,
                    'to_be_discovered': True
                })
                print(f"✅ Router discovery scheduled")
            
            # If still no routers, use default fritz.box
            if not router_configs:
                router_configs = [{
                    'name': 'Fritz!Box',
                    'host': 'http://fritz.box',
                    'username': 'admin',
                    'password': '',  # Will be prompted
                    'auto_discovered': False
                }]
                
            # Initialize routers with credential prompting
            for router_config in router_configs:
                # Prompt for credentials if needed
                if self.config.get('prompt_for_credentials', False) and not router_config.get('password'):
                    router_config = self._prompt_for_credentials(router_config)
                
                router = FritzBoxRouter(router_config, self.credential_manager)
                self.routers[router.name] = router
                
            self.update_interval = self.config.get('update_interval', 30)
            
            logger.info(f"FRITZWATCHER initialized with {len(self.routers)} routers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FRITZWATCHER: {e}")
            return False
            
    def _prompt_for_credentials(self, router_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt user for router credentials"""
        try:
            import getpass
            
            print(f"\n🔐 Credentials needed for {router_config['name']} ({router_config['host']})")
            
            # Prompt for username (with default)
            username = input(f"Username (default: {router_config.get('username', 'admin')}): ").strip()
            if not username:
                username = router_config.get('username', 'admin')
            
            # Prompt for password
            password = getpass.getpass(f"Password for {username}@{router_config['host']}: ")
            
            # Update config
            router_config['username'] = username
            router_config['password'] = password
            
            return router_config
            
        except Exception as e:
            logger.error(f"Failed to prompt for credentials: {e}")
            return router_config
            
    def start(self) -> bool:
        """Start the plugin"""
        try:
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("FRITZWATCHER started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FRITZWATCHER: {e}")
            return False
            
    def stop(self) -> bool:
        """Stop the plugin"""
        try:
            if self.monitoring_task:
                self.monitoring_task.cancel()
                
            logger.info("FRITZWATCHER stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop FRITZWATCHER: {e}")
            return False
            
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        # Perform router discovery if needed
        if hasattr(self, 'registry'):
            try:
                discovered = await self.registry.discover_and_register()
                if discovered:
                    print(f"✅ Discovered {len(discovered)} routers during monitoring")
                    
                    # Update router configs with discovered routers
                    for router in discovered:
                        if router.name not in self.routers:
                            router_config = {
                                'name': router.name,
                                'host': router.host,
                                'username': 'admin',
                                'password': '',
                                'auto_discovered': True
                            }
                            
                            # Prompt for credentials if needed
                            if self.config.get('prompt_for_credentials', False):
                                router_config = self._prompt_for_credentials(router_config)
                            
                            new_router = FritzBoxRouter(router_config, self.credential_manager)
                            self.routers[new_router.name] = new_router
                            
            except Exception as e:
                logger.error(f"Router discovery during monitoring failed: {e}")
        
        # Main monitoring loop
        while True:
            try:
                await self._update_all_routers()
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Wait before retry
                
    async def _update_all_routers(self):
        """Update information from all routers"""
        devices_by_router = {}
        
        for router_name, router in self.routers.items():
            try:
                # Authenticate if needed
                if not router.session_id:
                    await router.authenticate()
                    
                # Get connected devices
                devices = await router.get_connected_devices()
                devices_by_router[router_name] = devices
                
            except Exception as e:
                logger.error(f"Failed to update router {router_name}: {e}")
                
        # Update roaming tracker
        self.roaming_tracker.update_device_locations(devices_by_router)
        
    # API Methods for web interface
    async def get_router_status(self) -> Dict[str, Any]:
        """Get status of all routers"""
        status = {}
        
        for router_name, router in self.routers.items():
            try:
                device_info = await router.get_device_info()
                status[router_name] = {
                    'online': device_info is not None,
                    'device_info': device_info,
                    'last_update': router.last_update.isoformat() if router.last_update else None,
                    'device_count': len(router.devices)
                }
            except Exception as e:
                status[router_name] = {
                    'online': False,
                    'error': str(e),
                    'device_count': 0
                }
                
        return status
        
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from all routers"""
        all_devices = []
        
        for router in self.routers.values():
            for device in router.devices.values():
                all_devices.append(device.to_dict())
                
        return all_devices
        
    async def get_guest_wifi_status(self, router_name: str = None) -> Dict[str, Any]:
        """Get guest WiFi status"""
        if router_name and router_name in self.routers:
            router = self.routers[router_name]
            return await router.get_guest_wifi_status()
        else:
            # Get from all routers
            status = {}
            for name, router in self.routers.items():
                status[name] = await router.get_guest_wifi_status()
            return status
            
    async def toggle_guest_wifi(self, enabled: bool, router_name: str = None) -> bool:
        """Toggle guest WiFi"""
        if router_name and router_name in self.routers:
            router = self.routers[router_name]
            return await router.toggle_guest_wifi(enabled)
        else:
            # Toggle on all routers
            success = True
            for router in self.routers.values():
                result = await router.toggle_guest_wifi(enabled)
                success = success and result
            return success
            
    async def get_roaming_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get roaming events"""
        events = self.roaming_tracker.get_roaming_events(hours)
        return [
            {
                'mac_address': event['mac_address'],
                'hostname': event['hostname'],
                'from_router': event['from_router'],
                'to_router': event['to_router'],
                'timestamp': event['timestamp'].isoformat(),
                'event_type': event['event_type']
            }
            for event in events
        ]
        
    async def sync_now(self) -> Dict[str, Any]:
        """Force immediate sync of all routers"""
        await self._update_all_routers()
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'routers_updated': len(self.routers)
        }
        
    # Implementation of abstract methods from ServicePlugin
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'name': 'FRITZWATCHER',
            'status': 'running' if self.monitoring_task and not self.monitoring_task.done() else 'stopped',
            'routers': len(self.routers),
            'active_sessions': len(self.roaming_tracker.active_sessions) if hasattr(self.roaming_tracker, 'active_sessions') else 0,
            'last_update': datetime.now().isoformat()
        }
        
    def start_service(self) -> bool:
        """Start service"""
        return self.start()
        
    def stop_service(self) -> bool:
        """Stop service"""
        return self.stop()


# Plugin registration
def create_plugin():
    """Create plugin instance"""
    return FritzWatcherPlugin()


# Test function
async def test_fritzwatcher():
    """Test FRITZWATCHER plugin"""
    print("Testing FRITZWATCHER Plugin")
    print("=" * 40)
    
    # Test configuration with dynamic discovery
    config = {
        'routers': [],  # Empty - will be auto-discovered
        'keepass': {
            'database_path': os.path.expanduser('~/keepass.kdbx'),
            'use_browser_integration': True,
            'use_cli': True
        },
        'update_interval': 30,
        'auto_discover': True,
        'prompt_for_credentials': True
    }
    
    plugin = FritzWatcherPlugin()
    
    if plugin.initialize(config):
        print("✅ Plugin initialized successfully")
        
        if plugin.start():
            print("✅ Plugin started successfully")
            
            # Test API methods
            try:
                status = await plugin.get_router_status()
                print(f"Router status: {status}")
                
                devices = await plugin.get_all_devices()
                print(f"Found {len(devices)} devices")
                
                guest_wifi = await plugin.get_guest_wifi_status()
                print(f"Guest WiFi status: {guest_wifi}")
                
            except Exception as e:
                print(f"API test failed: {e}")
                
            plugin.stop()
            print("✅ Plugin stopped successfully")
        else:
            print("❌ Plugin start failed")
    else:
        print("❌ Plugin initialization failed")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_fritzwatcher())
