"""
NoxPanel Plugin SDK
API bindings for plugin development
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PluginMetadata:
    """Plugin metadata structure"""
    name: str
    version: str
    author: str
    description: str
    category: str
    permissions: List[str]
    dependencies: List[str]

@dataclass
class PluginResponse:
    """Standard plugin response structure"""
    success: bool
    message: str
    data: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class PluginBase:
    """Base class for all NoxPanel plugins"""

    def __init__(self):
        self.metadata = None
        self.config = {}
        self.start_time = datetime.now()
        self.api_client = PluginAPIClient()

    def initialize(self) -> PluginResponse:
        """Initialize the plugin - must be implemented by subclasses"""
        raise NotImplementedError("initialize() must be implemented")

    def execute(self, action: str, parameters: Dict[str, Any] = None) -> PluginResponse:
        """Execute plugin action - must be implemented by subclasses"""
        raise NotImplementedError("execute() must be implemented")

    def cleanup(self) -> PluginResponse:
        """Cleanup plugin resources - must be implemented by subclasses"""
        raise NotImplementedError("cleanup() must be implemented")

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status - can be overridden by subclasses"""
        return {
            "name": self.metadata.name if self.metadata else "Unknown",
            "status": "running",
            "uptime": str(datetime.now() - self.start_time)
        }

class PluginAPIClient:
    """API client for plugin communication with NoxPanel"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "NoxPanel-Plugin-SDK/1.0.0"
        }

    def register_plugin(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """Register plugin with NoxPanel"""
        try:
            response = requests.post(
                f"{self.base_url}/api/plugins/register",
                json=metadata.__dict__,
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def send_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send event to NoxPanel"""
        try:
            event_data = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.base_url}/api/events",
                json=event_data,
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information from NoxPanel"""
        try:
            response = requests.get(
                f"{self.base_url}/api/system/info",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def store_data(self, key: str, value: Any) -> Dict[str, Any]:
        """Store data in NoxPanel"""
        try:
            response = requests.post(
                f"{self.base_url}/api/data/store",
                json={"key": key, "value": value},
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def retrieve_data(self, key: str) -> Dict[str, Any]:
        """Retrieve data from NoxPanel"""
        try:
            response = requests.get(
                f"{self.base_url}/api/data/retrieve/{key}",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
