#!/usr/bin/env python3
"""
FRITZWATCHER Configuration Example
==================================

This file shows how to configure the FRITZWATCHER plugin system
with proper security practices and dynamic network discovery.

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import json
import os
import re
from pathlib import Path

# Example configuration with security best practices
FRITZWATCHER_CONFIG = {
    # Router Configuration
    "routers": [
        # Example 1: Auto-discovered router with KeePass credentials
        {
            "name": "Main Fritz!Box",
            "host": "http://fritz.box",  # Use hostname, not IP
            "username": "admin",
            "keepass_ref": "FritzBox_Main",  # Reference to KeePass entry
            "auto_discovered": False
        },
        # Example 2: Manually configured router
        {
            "name": "Guest Network",
            "host": "http://fritz.repeater",
            "username": "admin",
            "keepass_ref": "FritzBox_Guest",
            "auto_discovered": False
        }
        # Note: No passwords stored in plaintext!
    ],
    
    # Auto-discovery settings
    "auto_discover": True,  # Enable automatic router discovery
    "discovery_methods": [
        "hostname",  # Try common hostnames (fritz.box, etc.)
        "upnp",      # UPnP/SSDP discovery
        "network_scan"  # Network scanning as fallback
    ],
    
    # Credential Management
    "keepass": {
        "database_path": "~/Documents/passwords.kdbx",  # Path to KeePass database
        "use_cli": True,        # Use KeePass CLI if available
        "use_browser_integration": True,  # Use browser integration
        "master_password_env": "KEEPASS_MASTER_PASSWORD"  # Environment variable for master password
    },
    
    # Security Settings
    "prompt_for_credentials": True,  # Prompt user for missing credentials
    "store_credentials": False,      # Don't store credentials in memory longer than needed
    "use_secure_storage": True,      # Use OS secure storage if available
    
    # Network Settings
    "update_interval": 30,           # Update interval in seconds
    "connection_timeout": 10,        # Connection timeout in seconds
    "retry_attempts": 3,             # Number of retry attempts
    "enable_guest_wifi_control": True,  # Allow guest WiFi control
    
    # Monitoring Settings
    "track_roaming": True,           # Enable roaming tracking
    "signal_monitoring": True,       # Enable signal strength monitoring
    "device_history_days": 30,       # Keep device history for X days
    
    # Web Interface Settings
    "web_interface": {
        "enabled": True,
        "port": 5000,
        "bind_address": "127.0.0.1",  # Only local access by default
        "enable_remote_access": False,  # Disable remote access for security
        "authentication_required": True
    },
    
    # Logging Settings
    "logging": {
        "level": "INFO",
        "file": "fritzwatcher.log",
        "max_size": "10MB",
        "backup_count": 3
    }
}

# Example KeePass database structure
KEEPASS_STRUCTURE_EXAMPLE = {
    "entries": [
        {
            "title": "FritzBox_Main",
            "username": "admin",
            "password": "your_secure_password_here",
            "url": "http://fritz.box",
            "notes": "Main Fritz!Box router credentials"
        },
        {
            "title": "FritzBox_Guest",
            "username": "admin", 
            "password": "another_secure_password",
            "url": "http://fritz.repeater",
            "notes": "Guest network Fritz!Box credentials"
        }
    ]
}

# Environment variables for secure configuration
ENVIRONMENT_VARIABLES = {
    "KEEPASS_MASTER_PASSWORD": "your_keepass_master_password",
    "FRITZWATCHER_CONFIG_PATH": "/path/to/config.json",
    "FRITZWATCHER_LOG_LEVEL": "INFO"
}

def create_sample_config():
    """Create a sample configuration file"""
    config_path = Path("fritzwatcher_config.json")
    
    # Remove any sensitive data from sample
    safe_config = FRITZWATCHER_CONFIG.copy()
    safe_config["keepass"]["master_password_env"] = "KEEPASS_MASTER_PASSWORD"
    
    with open(config_path, 'w') as f:
        json.dump(safe_config, f, indent=2)
    
    print(f"✅ Sample configuration created: {config_path}")
    print("\n🔐 Security Notes:")
    print("1. Never store passwords in plaintext in configuration files")
    print("2. Use KeePass or similar password manager for credentials")
    print("3. Set environment variables for sensitive data")
    print("4. Enable auto-discovery to avoid hardcoded IP addresses")
    print("5. Use hostnames (fritz.box) instead of IP addresses when possible")
    
    return config_path

def validate_config(config_path: str) -> bool:
    """Validate configuration file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for security issues
        issues = []
        
        # Check for hardcoded passwords
        for router in config.get('routers', []):
            if router.get('password'):
                issues.append(f"Router '{router['name']}' has hardcoded password")
        
        # Check for hardcoded IP addresses
        for router in config.get('routers', []):
            host = router.get('host', '')
            if host and re.match(r'http://\d+\.\d+\.\d+\.\d+', host):
                issues.append(f"Router '{router['name']}' uses hardcoded IP address")
        
        # Check for KeePass configuration
        if not config.get('keepass', {}).get('database_path'):
            issues.append("No KeePass database path configured")
        
        if issues:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Configuration validation passed")
            return True
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def setup_secure_environment():
    """Setup secure environment for FRITZWATCHER"""
    print("🔧 Setting up secure FRITZWATCHER environment...")
    
    # Create config directory
    config_dir = Path.home() / ".fritzwatcher"
    config_dir.mkdir(exist_ok=True)
    
    # Create logs directory
    logs_dir = config_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create sample configuration
    config_path = create_sample_config()
    
    # Validate configuration
    validate_config(config_path)
    
    print("\n📋 Next Steps:")
    print("1. Set up KeePass database with router credentials")
    print("2. Configure environment variables for sensitive data")
    print("3. Review and customize the configuration file")
    print("4. Test the configuration with: python fritzwatcher_plugin.py")
    
    return config_path

if __name__ == "__main__":
    setup_secure_environment()
