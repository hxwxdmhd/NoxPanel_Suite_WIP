#!/usr/bin/env python3
"""
NoxPanel Development Server Startup Script
Quick way to start the NoxPanel web interface for testing and development
"""

import sys
import os
from pathlib import Path

def main():
    """Start the NoxPanel development server"""
    
    # Set up path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Import the Flask app
        from AI.NoxPanel.test_server_optimized import app
        
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║                🧠 NoxPanel Development Server                     ║
║                    Starting Web Interface...                     ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
        
        print("🌐 Starting NoxPanel web interface on http://localhost:5000")
        print("📊 Available endpoints:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                print(f"   http://localhost:5000{rule.rule}")
        
        print("\n🔥 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the development server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Failed to import NoxPanel app: {e}")
        print("💡 Make sure Flask is installed: pip install flask")
        return 1
    except KeyboardInterrupt:
        print("\n👋 NoxPanel server stopped")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())