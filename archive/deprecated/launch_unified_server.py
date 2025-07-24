#!/usr/bin/env python3
"""
Ultimate Suite v11.0 - Production Launch Script
==============================================
Simple standalone launcher for testing and deployment
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heimnetz_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main launcher function"""
    print("=" * 60)
    print("ULTIMATE SUITE v11.0 - UNIFIED SERVER LAUNCHER")
    print("=" * 60)
    print(f"Starting at: {datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    try:
        # Test imports
        print("Testing imports...")
        
        try:
            from unified_plugin_system import UnifiedPluginManager
            print("✓ UnifiedPluginManager import successful")
        except Exception as e:
            print(f"✗ UnifiedPluginManager import failed: {e}")
            return False
            
        try:
            from models_unified import DatabaseManager
            print("✓ DatabaseManager import successful")
        except Exception as e:
            print(f"✗ DatabaseManager import failed: {e}")
            # Continue without database for now
            
        try:
            from main_unified_server import UnifiedServer, ServerConfig
            print("✓ UnifiedServer import successful")
        except Exception as e:
            print(f"✗ UnifiedServer import failed: {e}")
            return False
        
        print()
        print("All critical imports successful!")
        print()
        
        # Initialize configuration
        print("Initializing configuration...")
        config = ServerConfig()
        config.database_url = "sqlite:///heimnetz.db"  # Use SQLite for testing
        config.redis_url = "redis://localhost:6379/0"
        config.debug = True
        config.ssl_enabled = False
        config.host = "127.0.0.1"
        config.port = 5000
        
        print(f"Server will run on: {config.host}:{config.port}")
        print(f"Database: {config.database_url}")
        print(f"Debug mode: {config.debug}")
        print()
        
        # Initialize plugin system
        print("Initializing plugin system...")
        try:
            plugin_dirs = ["plugins", "AI/plugins", "NoxPanel/plugins"]
            plugin_manager = UnifiedPluginManager(plugin_dirs)
            print("✓ Plugin system initialized")
        except Exception as e:
            print(f"✗ Plugin system initialization failed: {e}")
            plugin_manager = None
        
        print()
        
        # Create and start server
        print("Creating unified server...")
        server = UnifiedServer(config)
        
        if plugin_manager:
            server.plugin_manager = plugin_manager
        
        print("✓ Server created successfully")
        print()
        print("Starting server...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the server
        server.run()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server shutdown requested by user")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
