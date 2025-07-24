#!/usr/bin/env python3
"""
FRITZWATCHER Setup Script
=========================

Interactive setup script for FRITZWATCHER plugin system.
Helps users configure the system securely without hardcoded credentials.

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import json
import os
import sys
import getpass
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional

def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} (default: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} ({default_str}): ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def discover_network_info() -> Dict[str, Any]:
    """Discover network information"""
    print("\n🔍 Discovering network information...")
    
    network_info = {
        'local_ip': None,
        'network_range': None,
        'gateway_ip': None
    }
    
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        network_info['local_ip'] = local_ip
        
        # Calculate network range
        parts = local_ip.split('.')
        if len(parts) == 4:
            network_info['network_range'] = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            network_info['gateway_ip'] = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
        
        print(f"   ✅ Local IP: {local_ip}")
        print(f"   ✅ Network range: {network_info['network_range']}")
        print(f"   ✅ Likely gateway: {network_info['gateway_ip']}")
        
    except Exception as e:
        print(f"   ⚠️  Network discovery failed: {e}")
        
    return network_info

def setup_keepass_config() -> Dict[str, Any]:
    """Setup KeePass configuration"""
    print("\n🔐 KeePass Configuration")
    
    use_keepass = get_yes_no("Do you want to use KeePass for credential management?", True)
    
    if not use_keepass:
        return {
            'enabled': False,
            'database_path': '',
            'use_cli': False,
            'use_browser_integration': False
        }
    
    # KeePass database path
    default_path = str(Path.home() / "Documents" / "passwords.kdbx")
    db_path = get_user_input("KeePass database path", default_path)
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"⚠️  KeePass database not found at: {db_path}")
        create_db = get_yes_no("Would you like to create a new KeePass database?", False)
        if create_db:
            print("Please create the KeePass database manually and run this setup again.")
            return None
    
    # KeePass access methods
    use_cli = get_yes_no("Enable KeePass CLI integration?", True)
    use_browser = get_yes_no("Enable browser integration?", True)
    
    return {
        'enabled': True,
        'database_path': db_path,
        'use_cli': use_cli,
        'use_browser_integration': use_browser
    }

def setup_routers(network_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Setup router configuration"""
    print("\n📡 Router Configuration")
    
    routers = []
    
    # Auto-discovery option
    auto_discover = get_yes_no("Enable automatic router discovery?", True)
    
    if auto_discover:
        print("   ✅ Auto-discovery enabled - routers will be found automatically")
        return routers
    
    # Manual router configuration
    print("\nManual router configuration:")
    
    while True:
        router = {}
        
        # Router name
        router['name'] = get_user_input("Router name", "Fritz!Box")
        
        # Router host
        default_host = "http://fritz.box"
        if network_info.get('gateway_ip'):
            default_host = f"http://{network_info['gateway_ip']}"
        
        router['host'] = get_user_input("Router URL/IP", default_host)
        
        # Username
        router['username'] = get_user_input("Username", "admin")
        
        # KeePass reference
        router['keepass_ref'] = get_user_input(f"KeePass entry name (optional)", f"FritzBox_{router['name'].replace(' ', '_')}")
        
        routers.append(router)
        
        # Add another router?
        if not get_yes_no("Add another router?", False):
            break
    
    return routers

def setup_monitoring() -> Dict[str, Any]:
    """Setup monitoring configuration"""
    print("\n📊 Monitoring Configuration")
    
    config = {}
    
    # Update interval
    try:
        interval_str = get_user_input("Update interval (seconds)", "30")
        config['update_interval'] = int(interval_str)
    except ValueError:
        print("   ⚠️  Invalid input, using default value of 30 seconds")
        config['update_interval'] = 30
    
    # Roaming tracking
    config['track_roaming'] = get_yes_no("Enable roaming tracking?", True)
    
    # Signal monitoring
    config['signal_monitoring'] = get_yes_no("Enable signal strength monitoring?", True)
    
    # Device history
    try:
        history_str = get_user_input("Device history retention (days)", "30")
        config['device_history_days'] = int(history_str)
    except ValueError:
        print("   ⚠️  Invalid input, using default value of 30 days")
        config['device_history_days'] = 30
    
    # Guest WiFi control
    config['enable_guest_wifi_control'] = get_yes_no("Enable guest WiFi control?", True)
    
    return config

def setup_web_interface() -> Dict[str, Any]:
    """Setup web interface configuration"""
    print("\n🌐 Web Interface Configuration")
    
    config = {}
    
    # Enable web interface
    config['enabled'] = get_yes_no("Enable web interface?", True)
    
    if not config['enabled']:
        return config
    
    # Port
    try:
        port_str = get_user_input("Web interface port", "5000")
        config['port'] = int(port_str)
    except ValueError:
        print("   ⚠️  Invalid port, using default value of 5000")
        config['port'] = 5000
    
    # Bind address
    config['bind_address'] = get_user_input("Bind address (127.0.0.1 for local only)", "127.0.0.1")
    
    # Remote access
    config['enable_remote_access'] = get_yes_no("Enable remote access?", False)
    
    # Authentication
    config['authentication_required'] = get_yes_no("Require authentication?", True)
    
    return config

def save_configuration(config: Dict[str, Any], config_path: Path) -> bool:
    """Save configuration to file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved to: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def validate_configuration(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return warnings"""
    warnings = []
    
    # Check for security issues
    for router in config.get('routers', []):
        if router.get('password'):
            warnings.append(f"Router '{router['name']}' has hardcoded password - consider using KeePass")
    
    # Check KeePass setup
    keepass_config = config.get('keepass', {})
    if not keepass_config.get('enabled', False):
        warnings.append("KeePass not enabled - credentials may be stored insecurely")
    
    # Check web interface security
    web_config = config.get('web_interface', {})
    if web_config.get('enabled', False):
        if web_config.get('enable_remote_access', False) and not web_config.get('authentication_required', True):
            warnings.append("Remote access enabled without authentication - security risk")
    
    return warnings

def main():
    """Main setup function"""
    print("🚀 FRITZWATCHER Setup Script")
    print("=" * 40)
    print("This script will help you configure FRITZWATCHER securely.")
    print("No passwords will be stored in plaintext.\n")
    
    # Create config directory
    config_dir = Path.home() / ".fritzwatcher"
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "config.json"
    
    # Check if config already exists
    if config_path.exists():
        overwrite = get_yes_no(f"Configuration file already exists at {config_path}. Overwrite?", False)
        if not overwrite:
            print("Setup cancelled.")
            return
    
    # Discover network information
    network_info = discover_network_info()
    
    # Setup components
    keepass_config = setup_keepass_config()
    if keepass_config is None:
        print("Setup cancelled.")
        return
    
    routers = setup_routers(network_info)
    monitoring = setup_monitoring()
    web_interface = setup_web_interface()
    
    # Build final configuration
    config = {
        'routers': routers,
        'auto_discover': len(routers) == 0,
        'keepass': keepass_config,
        'prompt_for_credentials': True,
        'update_interval': monitoring['update_interval'],
        'track_roaming': monitoring['track_roaming'],
        'signal_monitoring': monitoring['signal_monitoring'],
        'device_history_days': monitoring['device_history_days'],
        'enable_guest_wifi_control': monitoring['enable_guest_wifi_control'],
        'web_interface': web_interface,
        'logging': {
            'level': 'INFO',
            'file': str(config_dir / 'fritzwatcher.log')
        }
    }
    
    # Validate configuration
    warnings = validate_configuration(config)
    if warnings:
        print("\n⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        
        if not get_yes_no("Continue with these warnings?", True):
            print("Setup cancelled.")
            return
    
    # Save configuration
    if save_configuration(config, config_path):
        print("\n🎉 FRITZWATCHER setup completed successfully!")
        print("\nNext steps:")
        print("1. If using KeePass, add router credentials to your database")
        print("2. Test the configuration with: python fritzwatcher_plugin.py")
        print("3. Start the web interface with: python main_unified_server_clean.py")
        print(f"4. Configuration can be edited at: {config_path}")
        
        # Show web interface URL
        if web_interface.get('enabled', False):
            bind_addr = web_interface.get('bind_address', '127.0.0.1')
            port = web_interface.get('port', 5000)
            print(f"5. Web interface will be available at: http://{bind_addr}:{port}/fritzwatcher")
    
    else:
        print("❌ Setup failed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
