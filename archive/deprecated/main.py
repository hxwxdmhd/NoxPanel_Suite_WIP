#!/usr/bin/env python3
"""
🚀 Heimnetz Project - Unified Main Entry Point
============================================

ADHD-Friendly project launcher with clear options and visual feedback.
This replaces the chaos of 50+ scattered entry points with a single, clean interface.

Usage:
    python main.py                    # Interactive menu
    python main.py --web             # Start web dashboard
    python main.py --ai              # Start AI assistant
    python main.py --scan            # Network scanner
    python main.py --admin           # Admin panel
    python main.py --bootstrap       # Project bootstrapper
    python main.py --test            # Run test suite
"""

import sys
import os
import argparse
from pathlib import Path
import subprocess
import platform

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Visual feedback for ADHD-friendly experience
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """Display ADHD-friendly project banner"""
    banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔════════════════════════════════════════════════════════════════╗
║                    🏠 HEIMNETZ PROJECT 🏠                      ║
║               Network Management & AI Dashboard                ║
║                     Unified Entry Point                       ║
╚════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
"""
    print(banner)

def print_status(message, status_type="info"):
    """Print status message with visual indicators"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "loading": "⏳"
    }
    
    colors = {
        "info": Colors.OKBLUE,
        "success": Colors.OKGREEN,
        "warning": Colors.WARNING,
        "error": Colors.FAIL,
        "loading": Colors.OKCYAN
    }
    
    icon = icons.get(status_type, "ℹ️")
    color = colors.get(status_type, Colors.OKBLUE)
    
    print(f"{color}{icon} {message}{Colors.ENDC}")

def check_dependencies():
    """Check if required dependencies are available"""
    print_status("Checking dependencies...", "loading")
    
    required_modules = ["flask", "requests", "flask_cors"]
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print_status(f"✓ {module} found", "success")
        except ImportError:
            missing_modules.append(module)
            print_status(f"✗ {module} missing", "warning")
    
    if missing_modules:
        print_status(f"Missing modules: {', '.join(missing_modules)}", "warning")
        print_status("Run: pip install flask requests flask-cors", "info")
        return False
    
    return True

def show_interactive_menu():
    """Display interactive menu for ADHD-friendly navigation"""
    options = [
        ("🌐", "Web Dashboard", "Start the main web interface", "web"),
        ("🤖", "AI Assistant", "Launch text-based AI assistant", "ai"),
        ("🎤", "Voice Assistant", "Launch voice-enabled AI assistant", "voice"),
        ("🔍", "Network Scanner", "Scan and discover network devices", "scan"),
        ("⚙️", "Admin Panel", "Administrative control panel", "admin"),
        ("🚀", "Project Bootstrap", "Create new project or reset environment", "bootstrap"),
        ("🧪", "Test Suite", "Run comprehensive tests", "test"),
        ("📊", "System Status", "Check system health and logs", "status"),
        ("🛠️", "Development Tools", "Developer utilities and debugging", "dev"),
        ("📖", "Documentation", "Open project documentation", "docs"),
        ("❌", "Exit", "Close the application", "exit")
    ]
    
    print(f"\n{Colors.BOLD}Choose an option:{Colors.ENDC}")
    print("=" * 70)
    
    for i, (icon, name, description, _) in enumerate(options, 1):
        print(f"{Colors.OKCYAN}{i:2d}.{Colors.ENDC} {icon} {Colors.BOLD}{name:<16}{Colors.ENDC} - {description}")
    
    print("=" * 70)
    
    while True:
        try:
            choice = input(f"\n{Colors.OKBLUE}Enter your choice (1-{len(options)}): {Colors.ENDC}").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return options[choice_num - 1][3]
            
            print_status("Invalid choice. Please enter a number between 1 and {}.".format(len(options)), "error")
        except KeyboardInterrupt:
            print_status("\nExiting...", "info")
            return "exit"

def start_web_dashboard():
    """Start the integrated Heimnetz web dashboard"""
    print_status("Starting Heimnetz Web Dashboard...", "loading")
    
    try:
        # Use the integrated web server
        integrated_server = PROJECT_ROOT / "integrated_web_server.py"
        if integrated_server.exists():
            print_status("Starting integrated Heimnetz dashboard...", "success")
            print_status("🌐 Dashboard: http://localhost:5000", "info")
            print_status("🔗 Heimnetz: http://localhost:5000/heimnetz", "info")
            subprocess.run([sys.executable, str(integrated_server)])
        else:
            # Fallback to original web panel
            from NoxPanel.webpanel.app import start_webpanel
            print_status("Web dashboard starting on http://localhost:5000", "success")
            start_webpanel()
    except ImportError as e:
        print_status(f"Failed to import web panel: {e}", "error")
        print_status("Trying alternative web server...", "loading")
        
        # Fallback to simple HTTP server for static files
        web_root = PROJECT_ROOT / "htdocs"
        if web_root.exists():
            os.chdir(web_root)
            print_status("Starting simple HTTP server on http://localhost:8000", "info")
            subprocess.run([sys.executable, "-m", "http.server", "8000"])
        else:
            print_status("No web files found. Please check installation.", "error")

def start_ai_assistant():
    """Start AI-powered network analysis"""
    print_status("Starting AI Assistant...", "loading")
    
    try:
        # Import NoxAssistant
        from nox_assistant.assistant import NoxAssistant
        
        assistant = NoxAssistant()
        print_status("🤖 NoxAssistant initialized successfully", "success")
        
        # Start interactive session
        print_status("Starting interactive AI session...", "info")
        print_status("Type 'help' for commands, 'exit' to quit", "info")
        
        while True:
            try:
                user_input = input(f"\n{Colors.OKCYAN}💬 You: {Colors.ENDC}").strip()
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print_status("👋 Goodbye!", "success")
                    break
                
                if user_input:
                    response = assistant.process_command(user_input)
                    print(response)
                    
            except KeyboardInterrupt:
                print_status("\n👋 Session ended", "success")
                break
                
    except ImportError as e:
        print_status(f"AI Assistant not available: {e}", "error")
        print_status("Install requirements: pip install pyyaml", "info")
    except Exception as e:
        print_status(f"AI Assistant error: {e}", "error")

def start_voice_assistant():
    """Start voice-enabled AI assistant"""
    print_status("Starting Voice Assistant...", "loading")
    
    try:
        from nox_assistant.assistant import NoxAssistant
        from nox_assistant.voice_interface import VoiceInterface
        
        assistant = NoxAssistant()
        
        # Check if voice is available
        try:
            voice = VoiceInterface()
            print_status("🎤 Voice interface initialized", "success")
            
            # Start interactive voice session
            def process_voice_command(command):
                return assistant.process_command(command, use_voice=False)
            
            voice.interactive_session(process_voice_command)
            
        except ImportError:
            print_status("Voice capabilities not available", "warning")
            print_status("Install: pip install SpeechRecognition pyttsx3", "info")
            print_status("Falling back to text mode...", "info")
            start_ai_assistant()
            
    except Exception as e:
        print_status(f"Voice assistant error: {e}", "error")

def start_network_scanner():
    """Start network scanning functionality"""
    print_status("Starting Network Scanner...", "loading")
    
    try:
        # Look for network scanner scripts
        scanner_paths = [
            PROJECT_ROOT / "AI" / "NoxPanel" / "dev_scanner.py",
            PROJECT_ROOT / "scripts" / "network_scanner.py"
        ]
        
        for scanner_path in scanner_paths:
            if scanner_path.exists():
                print_status(f"Running network scanner: {scanner_path.name}", "success")
                subprocess.run([sys.executable, str(scanner_path)])
                return
        
        print_status("Network scanner not found. Creating basic scanner...", "warning")
        # Could implement a basic network scanner here
        
    except Exception as e:
        print_status(f"Failed to start network scanner: {e}", "error")

def start_admin_panel():
    """Start administrative control panel"""
    print_status("Starting Admin Panel...", "loading")
    
    try:
        # Look for admin panel implementations
        admin_paths = [
            PROJECT_ROOT / "AI" / "NoxPanel" / "enhanced_admin_panel.py",
            PROJECT_ROOT / "NoxPanel" / "webpanel" / "app.py"
        ]
        
        for admin_path in admin_paths:
            if admin_path.exists():
                print_status(f"Launching admin panel: {admin_path.name}", "success")
                subprocess.run([sys.executable, str(admin_path)])
                return
        
        print_status("Admin panel not found. Using web dashboard instead.", "warning")
        start_web_dashboard()
        
    except Exception as e:
        print_status(f"Failed to start admin panel: {e}", "error")

def start_project_bootstrap():
    """Start project bootstrapper"""
    print_status("Starting Project Bootstrapper...", "loading")
    
    try:
        bootstrap_script = PROJECT_ROOT / "init_noxpanel.py"
        if bootstrap_script.exists():
            print_status("Launching NoxPanel bootstrapper...", "success")
            subprocess.run([sys.executable, str(bootstrap_script)])
        else:
            print_status("Bootstrapper not found. Please check installation.", "error")
    except Exception as e:
        print_status(f"Failed to start bootstrapper: {e}", "error")

def run_test_suite():
    """Run comprehensive test suite"""
    print_status("Running Test Suite...", "loading")
    
    try:
        test_paths = [
            PROJECT_ROOT / "tests",
            PROJECT_ROOT / "AI" / "test"
        ]
        
        for test_path in test_paths:
            if test_path.exists():
                print_status(f"Running tests in: {test_path}", "info")
                subprocess.run([sys.executable, "-m", "pytest", str(test_path), "-v"])
                return
        
        print_status("No test directories found.", "warning")
        
    except Exception as e:
        print_status(f"Failed to run tests: {e}", "error")

def show_system_status():
    """Display system status and health check"""
    print_status("System Status Check", "loading")
    
    print(f"\n{Colors.BOLD}System Information:{Colors.ENDC}")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Project Root: {PROJECT_ROOT}")
    
    print(f"\n{Colors.BOLD}Project Structure:{Colors.ENDC}")
    key_paths = [
        "NoxPanel/webpanel/app.py",
        "init_noxpanel.py",
        "htdocs/index.html",
        "AI/NoxPanel/"
    ]
    
    for path in key_paths:
        full_path = PROJECT_ROOT / path
        status = "✅ Found" if full_path.exists() else "❌ Missing"
        print(f"  {status} - {path}")
    
    # Check dependencies
    print(f"\n{Colors.BOLD}Dependencies:{Colors.ENDC}")
    check_dependencies()

def open_documentation():
    """Open project documentation"""
    print_status("Opening Documentation...", "loading")
    
    doc_paths = [
        PROJECT_ROOT / "docs" / "README.md",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "NOXPANEL_COMPLETE_GUIDE.md"
    ]
    
    for doc_path in doc_paths:
        if doc_path.exists():
            print_status(f"Opening: {doc_path.name}", "success")
            if platform.system() == "Windows":
                os.startfile(doc_path)
            else:
                subprocess.run(["open" if platform.system() == "Darwin" else "xdg-open", str(doc_path)])
            return
    
    print_status("Documentation not found.", "warning")


def start_integrated_web():
    """Start integrated web interface (Frontend + Backend)"""
    print_status("Starting Integrated Heimnetz Dashboard...", "loading")
    
    try:
        # Check if we can import the AI backend
        backend_path = Path(__file__).parent / "AI" / "NoxPanel"
        if (backend_path / "webpanel" / "app_v5.py").exists():
            sys.path.insert(0, str(backend_path))
            from webpanel.app_v5 import create_app
            
            # Create Flask app with AI features
            app = create_app()
            
            # Add route to serve Heimnetz frontend
            frontend_path = Path("c:/xampp/htdocs/heimnetzV2/Heimnetz/htdocs")
            if frontend_path.exists():
                from flask import send_from_directory
                
                @app.route('/heimnetz')
                @app.route('/heimnetz/')
                def serve_heimnetz():
                    return send_from_directory(str(frontend_path), 'index.html')
                
                @app.route('/heimnetz/<path:filename>')
                def serve_heimnetz_assets(filename):
                    return send_from_directory(str(frontend_path), filename)
            
            print_status("Integrated dashboard starting on http://localhost:5000", "success")
            print_status("Heimnetz frontend available at http://localhost:5000/heimnetz", "info")
            app.run(host="0.0.0.0", port=5000, debug=False)
            
        else:
            print_status("AI backend not found, using basic integration", "warning")
            start_web_dashboard()
            
    except Exception as e:
        print_status(f"Integration failed: {e}", "error")
        print_status("Falling back to basic web server", "info")
        start_web_dashboard()

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Heimnetz Project - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                 # Interactive menu
  python main.py --web          # Start web dashboard  
  python main.py --ai           # Start AI assistant
  python main.py --scan         # Network scanner
        """
    )
    
    parser.add_argument("--web", action="store_true", help="Start web dashboard")
    parser.add_argument("--ai", action="store_true", help="Start AI assistant (text mode)")
    parser.add_argument("--voice", action="store_true", help="Start voice-enabled AI assistant")
    parser.add_argument("--assistant", type=str, help="Send single command to AI assistant")
    parser.add_argument("--scan", action="store_true", help="Network scanner")
    parser.add_argument("--admin", action="store_true", help="Admin panel")
    parser.add_argument("--bootstrap", action="store_true", help="Project bootstrapper")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--status", action="store_true", help="System status")
    parser.add_argument("--docs", action="store_true", help="Open documentation")
    parser.add_argument("--no-banner", action="store_true", help="Skip banner display")
    
    args = parser.parse_args()
    
    # Show banner unless suppressed
    if not args.no_banner:
        print_banner()
    
    # Handle command line arguments
    if args.web:
        start_web_dashboard()
    elif args.ai:
        start_ai_assistant()
    elif args.voice:
        start_voice_assistant()
    elif args.assistant:
        # Single command mode
        try:
            from nox_assistant.assistant import NoxAssistant
            assistant = NoxAssistant()
            response = assistant.process_command(args.assistant)
            print(response)
        except Exception as e:
            print_status(f"Assistant error: {e}", "error")
    elif args.scan:
        start_network_scanner()
    elif args.admin:
        start_admin_panel()
    elif args.bootstrap:
        start_project_bootstrap()
    elif args.test:
        run_test_suite()
    elif args.status:
        show_system_status()
    elif args.docs:
        open_documentation()
    else:
        # Interactive menu
        while True:
            choice = show_interactive_menu()
            
            if choice == "exit":
                print_status("Goodbye! 👋", "info")
                break
            elif choice == "web":
                start_integrated_web()
            elif choice == "ai":
                start_ai_assistant()
            elif choice == "voice":
                start_voice_assistant()
            elif choice == "scan":
                start_network_scanner()
            elif choice == "admin":
                start_admin_panel()
            elif choice == "bootstrap":
                start_project_bootstrap()
            elif choice == "test":
                run_test_suite()
            elif choice == "status":
                show_system_status()
            elif choice == "dev":
                print_status("Development tools coming soon...", "info")
            elif choice == "docs":
                open_documentation()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("\nOperation cancelled by user.", "info")
        sys.exit(0)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "error")
        sys.exit(1)
