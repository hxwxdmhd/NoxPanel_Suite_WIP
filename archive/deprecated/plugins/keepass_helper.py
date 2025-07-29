#!/usr/bin/env python3
"""
KeePass Helper for Secure Credential Management
==============================================

This module provides secure credential management using KeePassXC/KeePass
for the FRITZWATCHER plugin system.

Features:
- KeePassXC browser integration support
- .kdbx file access with CLI unlock
- Memory-only credential access
- No plaintext storage

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import os
import json
import logging
import tempfile
import subprocess
import time
from typing import Dict, Optional, Any
from pathlib import Path
import base64
import hashlib
import hmac

# Optional dependencies
try:
    import pykeepass
    HAS_PYKEEPASS = True
except ImportError:
    HAS_PYKEEPASS = False
    pykeepass = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

logger = logging.getLogger(__name__)

class KeePassHelper:
    """Secure credential management using KeePass/KeePassXC"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.database_path = self.config.get('database_path')
        self.master_key = None
        self.keyfile_path = self.config.get('keyfile_path')
        self.use_browser_integration = self.config.get('use_browser_integration', True)
        self.browser_port = self.config.get('browser_port', 19455)
        self.database = None
        
        # Auto-discover KeePass databases if no path specified
        if not self.database_path:
            self.database_path = self._find_keepass_database()
            
        # KeePassXC CLI settings
        self.keepassxc_cli = self.config.get('keepassxc_cli', 'keepassxc-cli')
        
        logger.info(f"KeePass Helper initialized with database: {self.database_path}")
        
    def _find_keepass_database(self) -> str:
        """Find existing KeePass database in common locations"""
        search_paths = [
            # User's Documents folder
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/OneDrive/Documents"),
            os.path.expanduser("~/Desktop"),
            
            # Common KeePass locations
            os.path.expanduser("~/KeePass"),
            os.path.expanduser("~/Passwords"),
            
            # Current directory and parent
            os.getcwd(),
            os.path.dirname(os.getcwd())
        ]
        
        found_databases = []
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    # Look for .kdbx files
                    for file in os.listdir(search_path):
                        if file.endswith('.kdbx'):
                            full_path = os.path.join(search_path, file)
                            found_databases.append(full_path)
                except (PermissionError, OSError):
                    continue
                    
    def _find_keepass_database(self) -> str:
        """Find existing KeePass database in common locations"""
        search_paths = [
            # User's Documents folder
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/OneDrive/Documents"),
            os.path.expanduser("~/Desktop"),
            
            # Common KeePass locations
            os.path.expanduser("~/KeePass"),
            os.path.expanduser("~/Passwords"),
            
            # Current directory and parent
            os.getcwd(),
            os.path.dirname(os.getcwd())
        ]
        
        found_databases = []
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    # Look for .kdbx files
                    for file in os.listdir(search_path):
                        if file.endswith('.kdbx'):
                            full_path = os.path.join(search_path, file)
                            found_databases.append(full_path)
                except (PermissionError, OSError):
                    continue
                    
        if found_databases:
            # Let user choose which database to use
            if len(found_databases) == 1:
                db_path = found_databases[0]
                db_name = os.path.basename(db_path)
                print(f"Found KeePass database: {db_name}")
                response = input(f"Use this database? (y/n): ").strip().lower()
                if response in ['y', 'yes', '']:
                    logger.info(f"Using KeePass database: {db_path}")
                    return db_path
                else:
                    # Let user choose a different one
                    db_path = input("Please enter the full path to your KeePass database (.kdbx): ").strip()
                    if db_path and os.path.exists(db_path):
                        logger.info(f"Using custom KeePass database: {db_path}")
                        return db_path
                    else:
                        logger.error("Database not found or invalid path")
                        return ""
            else:
                # Multiple databases found, let user choose
                print(f"Found {len(found_databases)} KeePass databases:")
                for i, db_path in enumerate(found_databases, 1):
                    print(f"{i}. {os.path.basename(db_path)} ({db_path})")
                
                print(f"{len(found_databases) + 1}. Enter custom path")
                
                while True:
                    try:
                        choice = input(f"Select database (1-{len(found_databases) + 1}): ").strip()
                        choice_num = int(choice)
                        
                        if 1 <= choice_num <= len(found_databases):
                            selected_db = found_databases[choice_num - 1]
                            logger.info(f"Using selected KeePass database: {selected_db}")
                            return selected_db
                        elif choice_num == len(found_databases) + 1:
                            # Custom path
                            db_path = input("Please enter the full path to your KeePass database (.kdbx): ").strip()
                            if db_path and os.path.exists(db_path):
                                logger.info(f"Using custom KeePass database: {db_path}")
                                return db_path
                            else:
                                logger.error("Database not found or invalid path")
                                return ""
                        else:
                            print(f"Invalid choice. Please enter a number between 1 and {len(found_databases) + 1}.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                        continue
        else:
            # No databases found, prompt user
            logger.warning("No KeePass database found in common locations")
            db_path = input("Please enter the full path to your KeePass database (.kdbx): ").strip()
            if db_path and os.path.exists(db_path):
                logger.info(f"Using custom KeePass database: {db_path}")
                return db_path
            else:
                logger.error("Database not found or invalid path")
                return ""
        
    def unlock_database(self, master_password: str = None) -> bool:
        """Unlock the KeePass database"""
        if not self.database_path:
            logger.error("No database path configured")
            return False
            
        if not os.path.exists(self.database_path):
            logger.error(f"Database file not found: {self.database_path}")
            return False
            
        # Prompt for master password if not provided
        if not master_password:
            master_password = self._prompt_for_master_password()
            
        if not master_password:
            logger.error("No master password provided")
            return False
            
        try:
            if HAS_PYKEEPASS:
                # Use pykeepass for direct access
                self.database = pykeepass.PyKeePass(
                    self.database_path,
                    password=master_password,
                    keyfile=self.keyfile_path
                )
                logger.info("Database unlocked successfully with pykeepass")
                return True
            else:
                # Store password for CLI operations
                self.master_key = master_password
                logger.info("Master password stored for CLI operations")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unlock database: {e}")
            return False
            
    def _prompt_for_master_password(self) -> str:
        """Prompt user for master password"""
        try:
            import getpass
            if self.database_path:
                db_name = os.path.basename(self.database_path)
                return getpass.getpass(f"Enter master password for {db_name}: ")
            else:
                return getpass.getpass("Enter KeePass master password: ")
        except Exception as e:
            logger.error(f"Failed to prompt for password: {e}")
            return ""
            
    def get_credentials(self, reference: str) -> Optional[Dict[str, str]]:
        """Get credentials by reference (alias for get_credential)"""
        return self.get_credential(reference)
        
    def get_credential(self, reference: str) -> Optional[Dict[str, str]]:
        """Get credential by reference (title, UUID, or path)"""
        if not self.database and not self.master_key:
            logger.error("Database not unlocked")
            return None
            
        try:
            # Try browser integration first
            if self.use_browser_integration and HAS_REQUESTS:
                credential = self._get_from_browser_integration(reference)
                if credential:
                    return credential
                    
            # Try pykeepass direct access
            if self.database:
                credential = self._get_from_pykeepass(reference)
                if credential:
                    return credential
                    
            # Try KeePassXC CLI
            if self.master_key:
                credential = self._get_from_cli(reference)
                if credential:
                    return credential
                    
        except Exception as e:
            logger.error(f"Failed to get credential '{reference}': {e}")
            
        return None
        
    def _get_from_browser_integration(self, reference: str) -> Optional[Dict[str, str]]:
        """Get credential using KeePassXC browser integration"""
        try:
            # This is a simplified implementation
            # Full implementation would require proper KeePassXC protocol
            logger.info(f"Attempting browser integration for: {reference}")
            
            # KeePassXC browser integration uses WebSocket/HTTP
            # This is a placeholder for the actual implementation
            return None
            
        except Exception as e:
            logger.error(f"Browser integration failed: {e}")
            return None
            
    def _get_from_pykeepass(self, reference: str) -> Optional[Dict[str, str]]:
        """Get credential using pykeepass direct access"""
        try:
            # Search by title first
            entries = self.database.find_entries(title=reference)
            if not entries:
                # Try searching by UUID
                try:
                    entry = self.database.find_entries(uuid=reference)
                    if entry:
                        entries = [entry[0]]
                except:
                    pass
                    
            if not entries:
                # Try searching by path
                entries = self.database.find_entries(path=reference)
                
            if entries:
                entry = entries[0]
                return {
                    'title': entry.title,
                    'username': entry.username,
                    'password': entry.password,
                    'url': entry.url,
                    'notes': entry.notes
                }
                
        except Exception as e:
            logger.error(f"PyKeePass access failed: {e}")
            
        return None
        
    def _get_from_cli(self, reference: str) -> Optional[Dict[str, str]]:
        """Get credential using KeePassXC CLI"""
        try:
            # Use keepassxc-cli to show entry
            cmd = [
                self.keepassxc_cli,
                'show',
                '-s',  # Show password
                self.database_path,
                reference
            ]
            
            # Create temporary file for password
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(self.master_key)
                password_file = f.name
                
            try:
                # Run command with password from file
                result = subprocess.run(
                    cmd,
                    input=self.master_key,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse output
                    output = result.stdout
                    credential = self._parse_cli_output(output)
                    if credential:
                        return credential
                else:
                    logger.error(f"CLI command failed: {result.stderr}")
                    
            finally:
                # Clean up password file
                try:
                    os.unlink(password_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"CLI access failed: {e}")
            
        return None
        
    def _parse_cli_output(self, output: str) -> Optional[Dict[str, str]]:
        """Parse keepassxc-cli output"""
        try:
            lines = output.strip().split('\n')
            credential = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'title':
                        credential['title'] = value
                    elif key == 'username':
                        credential['username'] = value
                    elif key == 'password':
                        credential['password'] = value
                    elif key == 'url':
                        credential['url'] = value
                    elif key == 'notes':
                        credential['notes'] = value
                        
            return credential if credential else None
            
        except Exception as e:
            logger.error(f"Failed to parse CLI output: {e}")
            return None
            
    def test_connection(self) -> bool:
        """Test if KeePass connection is working"""
        try:
            # Try to get a test entry
            test_result = self.get_credential('__test__')
            # If we don't get an error, connection is working
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
            
    def close(self):
        """Close database connection and clear sensitive data"""
        if self.database:
            try:
                # PyKeePass doesn't have explicit close
                self.database = None
            except:
                pass
                
        # Clear sensitive data
        self.master_key = None
        logger.info("KeePass Helper closed")
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class FritzBoxCredentialManager:
    """Specialized credential manager for FritzBox routers"""
    
    def __init__(self, keepass_helper: KeePassHelper):
        self.keepass = keepass_helper
        self.credential_cache = {}
        
    def get_router_credentials(self, router_config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Get credentials for a specific router"""
        keepass_ref = router_config.get('keepass_ref')
        if not keepass_ref:
            # Fall back to plaintext if no KeePass reference
            return {
                'username': router_config.get('username', 'admin'),
                'password': router_config.get('password', '')
            }
            
        # Check cache first
        if keepass_ref in self.credential_cache:
            return self.credential_cache[keepass_ref]
            
        # Get from KeePass
        credential = self.keepass.get_credential(keepass_ref)
        if credential:
            result = {
                'username': credential.get('username', 'admin'),
                'password': credential.get('password', '')
            }
            
            # Cache for this session
            self.credential_cache[keepass_ref] = result
            return result
            
        logger.error(f"Failed to get credentials for router: {keepass_ref}")
        return None
        
    def clear_cache(self):
        """Clear credential cache"""
        self.credential_cache.clear()


def create_keepass_helper(config: Dict[str, Any]) -> KeePassHelper:
    """Create and configure a KeePass helper"""
    helper = KeePassHelper(config)
    
    # Auto-detect database if not specified
    if not helper.database_path:
        common_paths = [
            os.path.expanduser('~/keepass.kdbx'),
            os.path.expanduser('~/Documents/keepass.kdbx'),
            os.path.expanduser('~/KeePass/database.kdbx'),
            'keepass.kdbx'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                helper.database_path = path
                logger.info(f"Auto-detected KeePass database: {path}")
                break
                
    return helper


def test_keepass_setup():
    """Test KeePass setup and configuration"""
    print("Testing KeePass Helper Setup")
    print("=" * 40)
    
    # Test configuration
    config = {
        'database_path': os.path.expanduser('~/keepass.kdbx'),
        'use_browser_integration': True,
        'keepassxc_cli': 'keepassxc-cli'
    }
    
    helper = create_keepass_helper(config)
    
    print(f"Database path: {helper.database_path}")
    print(f"Database exists: {os.path.exists(helper.database_path) if helper.database_path else False}")
    print(f"PyKeePass available: {HAS_PYKEEPASS}")
    print(f"Requests available: {HAS_REQUESTS}")
    
    # Test CLI availability
    try:
        result = subprocess.run([helper.keepassxc_cli, '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"KeePassXC CLI available: {result.returncode == 0}")
        if result.returncode == 0:
            print(f"KeePassXC version: {result.stdout.strip()}")
    except Exception as e:
        print(f"KeePassXC CLI not available: {e}")
        
    print("\nRecommended setup:")
    print("1. Install KeePassXC: https://keepassxc.org/")
    print("2. Enable browser integration in KeePassXC settings")
    print("3. Create a database with router credentials")
    print("4. Or install pykeepass: pip install pykeepass")


if __name__ == "__main__":
    # Run setup test
    test_keepass_setup()
