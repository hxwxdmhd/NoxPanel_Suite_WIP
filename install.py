#!/usr/bin/env python3
"""
NoxSuite Unified Installer Entry Point
Simple entry point for all installation modes and operations
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main entry point for NoxSuite installation"""
    
    # Show banner
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                🧠 NoxSuite Unified Installer                      ║
║                    AI-Powered Network Management Suite           ║
╠═══════════════════════════════════════════════════════════════════╣
║  🔧 Smart Error Recovery    🌐 Cross-Platform Support           ║
║  📊 Installation Analytics  🛡️  Self-Healing Operations          ║
║  🚀 Multiple Install Modes  🤖 AI-Powered Troubleshooting       ║
║  📱 ADHD-Friendly Interface 🔄 Atomic Operations                ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Get the installer path
    installer_path = Path(__file__).parent / "noxsuite_smart_installer_complete.py"
    
    if not installer_path.exists():
        print("❌ Smart installer not found!")
        print(f"Expected: {installer_path}")
        return 1
    
    # Pass all arguments to the smart installer
    try:
        result = subprocess.run([sys.executable, str(installer_path)] + sys.argv[1:], 
                              check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Failed to launch installer: {e}")
        return 1

def show_help():
    """Show available installation modes"""
    help_text = """
🛠️  INSTALLATION MODES:
    guided     Interactive guided installation (default)
    fast       Quick installation with recommended defaults  
    dry-run    Preview installation without making changes
    safe       Minimal installation for maximum stability
    recovery   Recover from previous failed installation
    audit-heal Audit and automatically heal system issues

📝 EXAMPLES:
    python install.py                    # Guided installation
    python install.py fast               # Fast installation
    python install.py dry-run            # Preview mode
    python install.py safe               # Safe minimal install
    
🔗 DOCKER DEPLOYMENT:
    docker-compose up -d                 # Production deployment
    docker-compose -f docker-compose.dev.yml up  # Development

📚 DOCUMENTATION:
    README.md                           # Project overview
    SMART_INSTALLER_README.md           # Installer details
    docs/                              # Comprehensive documentation
    """
    print(help_text)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)
    
    sys.exit(main())