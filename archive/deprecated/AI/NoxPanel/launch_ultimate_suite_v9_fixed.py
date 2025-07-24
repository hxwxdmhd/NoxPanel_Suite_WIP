#!/usr/bin/env python3
"""
🚀 ULTIMATE SUITE v9.0 - FIXED LAUNCH SCRIPT
===========================================
Auto-generated launch script with Unicode and dependency fixes
"""

import sys
import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Fix Unicode issues on Windows
if sys.platform == "win32":
    # Set UTF-8 encoding for console output
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    # Set environment variable for Python to use UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def setup_logging():
    """Setup logging with Unicode support"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ultimate_suite_launch.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    except:
        # Fallback without emojis
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check and install missing dependencies"""
    logger = logging.getLogger(__name__)
    
    required_packages = [
        'flask', 'flask-cors', 'requests', 'psutil', 
        'websockets', 'numpy', 'pandas', 'matplotlib', 'plotly', 'networkx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"Missing packages detected: {missing_packages}")
        logger.info("Attempting to install missing packages...")
        
        try:
            import subprocess
            for package in missing_packages:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f"Successfully installed: {package}")
        except Exception as e:
            logger.error(f"Failed to install packages: {e}")
            return False
    
    return True

def create_default_config():
    """Create default configuration if missing"""
    config_path = Path('ultimate_config.json')
    if not config_path.exists():
        default_config = {
            "suite_version": "9.0",
            "debug_mode": True,
            "host": "127.0.0.1",
            "port": 5000,
            "ai_enabled": True,
            "plugin_system_enabled": True,
            "sysadmin_copilot_enabled": True,
            "plugin_directory": "plugins",
            "plugin_security_level": "medium",
            "created_by": "launch_script",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to create config: {e}")
            return False
    return True

def safe_import_webapp():
    """Safely import the webapp module"""
    logger = logging.getLogger(__name__)
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(current_dir))
        
        # Try to import the webapp
        import ultimate_webapp_v9
        logger.info("Module imported successfully")
        return ultimate_webapp_v9
    except Exception as e:
        logger.error(f"Failed to import module: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def main():
    """Main launch function"""
    print("=" * 60)
    print("ULTIMATE SUITE v9.0 - FIXED LAUNCHER")
    print("=" * 60)
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Ultimate Suite v9.0...")
    
    # Create default config
    if not create_default_config():
        print("Failed to create configuration")
        return 1
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("Dependency check failed")
        return 1
    
    # Import webapp
    print("Importing webapp module...")
    webapp_module = safe_import_webapp()
    if not webapp_module:
        print("Failed to import webapp module")
        return 1
    
    # Initialize and start
    try:
        print("Initializing Ultimate Suite v9.0...")
        suite = webapp_module.UltimateSuiteV9()
        
        print("Creating Flask application...")
        app = suite.create_app()
        
        print("Starting web server...")
        print("Access URL: http://127.0.0.1:5000")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the server
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,  # Disable debug to avoid Unicode issues
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\\nServer stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"Launch failed: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    sys.exit(exit_code)
