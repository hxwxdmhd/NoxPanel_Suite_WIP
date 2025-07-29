#!/usr/bin/env python3
"""
NoxSuite Smart Installer Launcher
Simple launcher script that provides multiple installation modes
"""

import sys
import os
from pathlib import Path

# Add current directory to path to import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def show_help():
    """Show help message with available modes"""
    help_text = """
🧠 NoxSuite Smart Self-Healing Installer

USAGE:
    python install_noxsuite.py [mode] [options]

INSTALLATION MODES:
    guided     Interactive guided installation (default)
    fast       Quick installation with recommended defaults
    dry-run    Preview installation without making changes
    safe       Minimal installation for maximum stability
    recovery   Recover from previous failed installation

EXAMPLES:
    python install_noxsuite.py                 # Guided mode
    python install_noxsuite.py fast            # Fast mode
    python install_noxsuite.py dry-run         # Preview only
    python install_noxsuite.py recovery        # Recovery mode

OPTIONS:
    --help, -h     Show this help message
    --version      Show installer version
    --check-deps   Check dependencies only
    --update       Check for installer updates

FEATURES:
    ✅ Smart dependency detection and installation
    ✅ Cross-platform support (Windows, Linux, macOS)
    ✅ Self-healing error recovery
    ✅ UTF-8 encoding support with fallbacks
    ✅ Atomic operations with rollback capability
    ✅ Comprehensive logging and auditing
    ✅ AI-powered issue analysis and suggestions
    ✅ Multiple package manager support
    ✅ Docker health checks and optimization
    ✅ Real-time progress tracking with ETA
    ✅ Network connectivity validation
    ✅ System resource monitoring
    ✅ Configuration validation
    ✅ Backup and restore functionality

For more information, visit: https://github.com/noxsuite/noxsuite
    """
    print(help_text)

def check_dependencies():
    """Quick dependency check"""
    print("🔍 Checking dependencies...")
    
    dependencies = {
        "Python": sys.version_info >= (3, 8),
        "Git": os.system("git --version > /dev/null 2>&1") == 0,
        "Docker": os.system("docker --version > /dev/null 2>&1") == 0,
        "Node.js": os.system("node --version > /dev/null 2>&1") == 0
    }
    
    print("\n📋 Dependency Status:")
    all_good = True
    for dep, available in dependencies.items():
        status = "✅" if available else "❌"
        print(f"   {status} {dep}")
        if not available:
            all_good = False
    
    if all_good:
        print("\n🎉 All dependencies are available!")
    else:
        print("\n⚠️  Some dependencies are missing. The installer can help install them.")
    
    return all_good

def check_updates():
    """Check for installer updates"""
    print("🔄 Checking for updates...")
    
    try:
        from noxsuite_installer_utils import UpdateChecker
        from noxsuite_smart_installer_complete import SmartLogger
        
        logger = SmartLogger()
        checker = UpdateChecker(logger)
        updates = checker.check_for_updates()
        
        if updates.get("available", False):
            print("🆕 Updates available:")
            for component, info in updates["components"].items():
                if info.get("update_available", False):
                    current = info.get("current_version", "unknown")
                    latest = info.get("latest_version", "unknown")
                    print(f"   • {component}: {current} → {latest}")
        else:
            print("✅ You have the latest version!")
            
    except Exception as e:
        print(f"❌ Could not check for updates: {e}")

def try_bootstrap():
    """Try to run bootstrap installer if main installer fails"""
    print("\n🔄 Attempting to bootstrap dependencies...")
    try:
        bootstrap_file = Path("noxsuite_bootstrap_installer.py")
        if bootstrap_file.exists():
            import subprocess
            result = subprocess.run([
                sys.executable, 
                str(bootstrap_file)
            ] + sys.argv[1:], capture_output=False)
            sys.exit(result.returncode)
        else:
            print("❌ Bootstrap installer not found")
            return False
    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")
        return False

def main():
    """Main launcher function"""
    # Parse command line arguments
    args = sys.argv[1:]
    
    if not args or args[0] in ["--help", "-h", "help"]:
        show_help()
        return
    
    if args[0] == "--version":
        print("NoxSuite Smart Installer v1.0.0")
        return
    
    if args[0] == "--check-deps":
        check_dependencies()
        return
    
    if args[0] == "--update":
        check_updates()
        return
    
    # Import the main installer
    try:
        from noxsuite_smart_installer_complete import SmartNoxSuiteInstaller, InstallMode
    except ImportError as e:
        print(f"❌ Could not import installer modules: {e}")
        print("This usually means required dependencies are missing.")
        
        # Try to run bootstrap installer
        print("\n🔧 The installer will now attempt to install missing dependencies...")
        try_bootstrap()
        
        print("\nIf the problem persists, try manually installing dependencies:")
        print("  pip install requests chardet")
        print("  python install_noxsuite.py")
        sys.exit(1)
    
    # Determine installation mode
    mode_map = {
        "guided": InstallMode.GUIDED,
        "fast": InstallMode.FAST,
        "dry-run": InstallMode.DRY_RUN,
        "safe": InstallMode.SAFE,
        "recovery": InstallMode.RECOVERY
    }
    
    mode_arg = args[0].lower() if args else "guided"
    install_mode = mode_map.get(mode_arg, InstallMode.GUIDED)
    
    if mode_arg not in mode_map:
        print(f"❌ Unknown mode: {mode_arg}")
        print("Use --help to see available modes")
        sys.exit(1)
    
    # Welcome message
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                🧠 NoxSuite Smart Self-Healing Installer           ║
║                      Starting {install_mode.value.title()} Mode Installation                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run the installer
    try:
        installer = SmartNoxSuiteInstaller()
        success = installer.run_installation(install_mode)
        
        if success:
            print("\n🎉 Installation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Installation failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installer crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
