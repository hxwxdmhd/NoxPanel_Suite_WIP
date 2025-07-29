#!/usr/bin/env python3
"""
🚀 ULTIMATE SUITE v9.0 - INSTALLATION & LAUNCH SCRIPT
=====================================================

Comprehensive installation, dependency management, and launch script
for Ultimate Heimnetz/NoxPanel/NoxGuard Suite v9.0 with SysAdmin Copilot
and Plugin Framework.

Features:
- Automatic dependency installation
- Environment setup and validation
- Component initialization and testing
- Graceful error handling and recovery
- Comprehensive logging and monitoring
"""

import os
import sys
import json
import time
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import argparse
import shutil
import urllib.request
import zipfile
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ultimate_suite_v9_install.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class InstallationConfig:
    """Installation configuration"""
    python_version_min: str = "3.8"
    node_version_min: str = "14.0"
    
    # Required Python packages
    python_packages: List[str] = None
    
    # Optional packages for enhanced features
    optional_packages: List[str] = None
    
    # System packages (platform-specific)
    system_packages: Dict[str, List[str]] = None
    
    # Installation directories
    install_dir: str = "."
    plugin_dir: str = "plugins"
    data_dir: str = "data"
    logs_dir: str = "logs"
    
    def __post_init__(self):
        if self.python_packages is None:
            self.python_packages = [
                "flask>=2.3.0",
                "flask-cors>=4.0.0",
                "requests>=2.28.0",
                "psutil>=5.9.0",
                "asyncio",
                "dataclasses-json>=0.5.7",
                "pyyaml>=6.0",
                "click>=8.0.0"
            ]
            
        if self.optional_packages is None:
            self.optional_packages = [
                "python-nmap>=0.7.1",  # Enhanced network scanning
                "scapy>=2.5.0",        # Advanced network analysis
                "openai>=1.0.0",       # OpenAI integration
                "anthropic>=0.7.0",    # Anthropic Claude integration
                "speechrecognition>=3.10.0",  # Voice interface
                "pyttsx3>=2.90",       # Text-to-speech
                "opencv-python>=4.8.0", # Computer vision
                "matplotlib>=3.7.0",   # Data visualization
                "pandas>=2.0.0",       # Data analysis
                "numpy>=1.24.0",       # Numerical computing
                "scipy>=1.10.0",       # Scientific computing
                "cryptography>=41.0.0", # Enhanced security
                "paramiko>=3.2.0",     # SSH connections
                "docker>=6.1.0",       # Docker integration
                "kubernetes>=27.2.0"   # Kubernetes integration
            ]
            
        if self.system_packages is None:
            self.system_packages = {
                "ubuntu": ["nmap", "traceroute", "netstat", "ss", "iptables"],
                "debian": ["nmap", "traceroute", "net-tools", "iptables"],
                "centos": ["nmap", "traceroute", "net-tools", "iptables"],
                "rhel": ["nmap", "traceroute", "net-tools", "iptables"],
                "fedora": ["nmap", "traceroute", "net-tools", "iptables"],
                "arch": ["nmap", "traceroute", "net-tools", "iptables"],
                "windows": [],  # Windows packages handled differently
                "macos": ["nmap"]  # macOS packages via Homebrew
            }

class UltimateSuiteInstaller:
    """Ultimate Suite v9.0 installer and launcher"""
    
    def __init__(self, config: InstallationConfig):
        self.config = config
        self.platform = platform.system().lower()
        self.install_path = Path(config.install_dir).resolve()
        
        # Track installation status
        self.installation_status = {
            "python_packages": False,
            "optional_packages": False,
            "system_packages": False,
            "directories": False,
            "configuration": False,
            "components": False
        }
        
        self.installed_packages = []
        self.failed_packages = []
        
    def run_installation(self) -> bool:
        """Run complete installation process"""
        try:
            logger.info("🚀 Starting Ultimate Suite v9.0 installation...")
            self.print_banner()
            
            # Pre-installation checks
            if not self.check_prerequisites():
                return False
                
            # Create directories
            if not self.create_directories():
                return False
                
            # Install Python packages
            if not self.install_python_packages():
                return False
                
            # Install optional packages (non-critical)
            self.install_optional_packages()
            
            # Install system packages
            self.install_system_packages()
            
            # Setup configuration
            if not self.setup_configuration():
                return False
                
            # Validate installation
            if not self.validate_installation():
                return False
                
            logger.info("✅ Ultimate Suite v9.0 installation completed successfully!")
            self.print_installation_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            return False
            
    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        min_version = tuple(map(int, self.config.python_version_min.split('.')))
        
        if python_version[:2] < min_version:
            logger.error(f"Python {self.config.python_version_min}+ required, found {python_version.major}.{python_version.minor}")
            return False
            
        logger.info(f"✅ Python {python_version.major}.{python_version.minor} found")
        
        # Check pip
        try:
            import pip
            logger.info("✅ pip found")
        except ImportError:
            logger.error("❌ pip not found - please install pip")
            return False
            
        # Check internet connectivity
        if not self.check_internet():
            logger.warning("⚠️ Limited internet connectivity - some features may not work")
            
        # Check available disk space
        if not self.check_disk_space():
            logger.warning("⚠️ Low disk space - installation may fail")
            
        return True
        
    def check_internet(self) -> bool:
        """Check internet connectivity"""
        try:
            urllib.request.urlopen('https://pypi.org', timeout=5)
            return True
        except:
            return False
            
    def check_disk_space(self, required_mb: int = 500) -> bool:
        """Check available disk space"""
        try:
            if self.platform == "windows":
                import shutil
                free_bytes = shutil.disk_usage(self.install_path.root)[2]
            else:
                statvfs = os.statvfs(self.install_path)
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                
            free_mb = free_bytes / (1024 * 1024)
            return free_mb >= required_mb
        except:
            return True  # Assume sufficient space if check fails
            
    def create_directories(self) -> bool:
        """Create required directories"""
        logger.info("📁 Creating directories...")
        
        directories = [
            self.install_path,
            self.install_path / self.config.plugin_dir,
            self.install_path / self.config.data_dir,
            self.install_path / self.config.logs_dir,
            self.install_path / "templates",
            self.install_path / "static" / "css",
            self.install_path / "static" / "js",
            self.install_path / "config"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created: {directory}")
            except Exception as e:
                logger.error(f"❌ Failed to create {directory}: {e}")
                return False
                
        self.installation_status["directories"] = True
        return True
        
    def install_python_packages(self) -> bool:
        """Install required Python packages"""
        logger.info("📦 Installing Python packages...")
        
        for package in self.config.python_packages:
            if self.install_package(package, required=True):
                self.installed_packages.append(package)
            else:
                self.failed_packages.append(package)
                logger.error(f"❌ Failed to install required package: {package}")
                return False
                
        self.installation_status["python_packages"] = True
        return True
        
    def install_optional_packages(self):
        """Install optional packages (non-critical)"""
        logger.info("🔧 Installing optional packages...")
        
        for package in self.config.optional_packages:
            if self.install_package(package, required=False):
                self.installed_packages.append(package)
                logger.info(f"✅ Optional package installed: {package}")
            else:
                self.failed_packages.append(package)
                logger.warning(f"⚠️ Optional package failed: {package}")
                
        self.installation_status["optional_packages"] = True
        
    def install_package(self, package: str, required: bool = True) -> bool:
        """Install a single Python package"""
        try:
            logger.info(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--upgrade"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True
            else:
                if required:
                    logger.error(f"Package installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Package installation timed out: {package}")
            return False
        except Exception as e:
            logger.error(f"Package installation error: {e}")
            return False
            
    def install_system_packages(self):
        """Install system packages"""
        logger.info("🔧 Installing system packages...")
        
        # Detect Linux distribution
        distro = self.detect_linux_distro()
        packages = self.config.system_packages.get(distro, [])
        
        if not packages:
            logger.info("No system packages to install for this platform")
            return
            
        if self.platform == "linux":
            self.install_linux_packages(distro, packages)
        elif self.platform == "darwin":  # macOS
            self.install_macos_packages(packages)
        elif self.platform == "windows":
            self.install_windows_packages(packages)
            
        self.installation_status["system_packages"] = True
        
    def detect_linux_distro(self) -> str:
        """Detect Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if line.startswith('ID='):
                    distro_id = line.split('=')[1].strip().strip('"')
                    return distro_id.lower()
                    
        except FileNotFoundError:
            pass
            
        # Fallback detection
        if shutil.which('apt'):
            return 'ubuntu'
        elif shutil.which('yum'):
            return 'centos'
        elif shutil.which('dnf'):
            return 'fedora'
        elif shutil.which('pacman'):
            return 'arch'
            
        return 'unknown'
        
    def install_linux_packages(self, distro: str, packages: List[str]):
        """Install Linux packages"""
        package_managers = {
            'ubuntu': 'apt',
            'debian': 'apt',
            'centos': 'yum',
            'rhel': 'yum',
            'fedora': 'dnf',
            'arch': 'pacman'
        }
        
        pm = package_managers.get(distro)
        if not pm:
            logger.warning(f"Unknown package manager for {distro}")
            return
            
        for package in packages:
            try:
                if pm == 'apt':
                    cmd = ['sudo', 'apt', 'install', '-y', package]
                elif pm in ['yum', 'dnf']:
                    cmd = ['sudo', pm, 'install', '-y', package]
                elif pm == 'pacman':
                    cmd = ['sudo', 'pacman', '-S', '--noconfirm', package]
                else:
                    continue
                    
                logger.info(f"Installing {package} with {pm}...")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Installed {package}")
                else:
                    logger.warning(f"⚠️ Failed to install {package}")
                    
            except Exception as e:
                logger.warning(f"⚠️ System package installation error: {e}")
                
    def install_macos_packages(self, packages: List[str]):
        """Install macOS packages using Homebrew"""
        if not shutil.which('brew'):
            logger.warning("Homebrew not found - skipping system packages")
            return
            
        for package in packages:
            try:
                logger.info(f"Installing {package} with Homebrew...")
                result = subprocess.run(['brew', 'install', package], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Installed {package}")
                else:
                    logger.warning(f"⚠️ Failed to install {package}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Homebrew installation error: {e}")
                
    def install_windows_packages(self, packages: List[str]):
        """Install Windows packages"""
        # For Windows, we might use chocolatey or direct downloads
        logger.info("Windows system packages would be installed here")
        # Implementation would depend on available package manager
        
    def setup_configuration(self) -> bool:
        """Setup configuration files"""
        logger.info("⚙️ Setting up configuration...")
        
        try:
            # Create main configuration
            config_data = {
                "app_name": "Ultimate Heimnetz/NoxPanel/NoxGuard Suite v9.0",
                "version": "9.0.0",
                "debug": False,
                "host": "127.0.0.1",
                "port": 5000,
                "secret_key": "nox_ultimate_secret_v9_sysadmin_plugins",
                
                # SysAdmin Copilot settings
                "sysadmin_copilot_enabled": True,
                "auto_maintenance_enabled": True,
                "health_monitoring_interval": 300,
                "task_confirmation_required": True,
                
                # Plugin framework settings
                "plugin_system_enabled": True,
                "plugin_directory": self.config.plugin_dir,
                "plugin_security_level": "strict",
                "plugin_auto_updates": False,
                
                # AI models configuration
                "ai_models": [
                    {
                        "provider": "ollama",
                        "model_name": "llama3.2",
                        "endpoint": "http://localhost:11434",
                        "enabled": True
                    },
                    {
                        "provider": "ollama", 
                        "model_name": "codellama",
                        "endpoint": "http://localhost:11434",
                        "enabled": True
                    }
                ],
                
                # Network configuration
                "network_config": {
                    "scan_range": "192.168.1.0/24",
                    "scan_timeout": 30,
                    "service_detection": True,
                    "vulnerability_scan": True,
                    "topology_mapping": True
                },
                
                # Enhanced features
                "real_time_monitoring": True,
                "voice_commands": False,
                "mobile_interface": True,
                "enterprise_features": False
            }
            
            config_path = self.install_path / "config" / "ultimate_suite_v9.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"✅ Configuration saved to {config_path}")
            
            self.installation_status["configuration"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration setup failed: {e}")
            return False
            
    def validate_installation(self) -> bool:
        """Validate installation"""
        logger.info("🔍 Validating installation...")
        
        # Check critical imports
        critical_modules = [
            'flask', 'flask_cors', 'requests', 'psutil', 'json', 'logging'
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} import successful")
            except ImportError as e:
                logger.error(f"❌ {module} import failed: {e}")
                return False
                
        # Check file structure
        required_files = [
            "ultimate_webapp_v9.py",
            "plugin_framework.py", 
            "sysadmin_copilot.py",
            "templates/ultimate_dashboard_v9.html",
            "static/css/ultimate-dashboard-v9.css",
            "static/js/ultimate-suite-v9.js"
        ]
        
        for file_path in required_files:
            full_path = self.install_path / file_path
            if full_path.exists():
                logger.info(f"✅ {file_path} found")
            else:
                logger.warning(f"⚠️ {file_path} not found")
                
        self.installation_status["components"] = True
        return True
        
    def print_banner(self):
        """Print installation banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🚀 ULTIMATE SUITE v9.0 INSTALLER 🚀                    ║
║                                                                  ║
║    SysAdmin Copilot • Plugin Framework • AI Integration         ║
║    Network Analysis • Real-time Monitoring • Security           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def print_installation_summary(self):
        """Print installation summary"""
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    INSTALLATION SUMMARY                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ Python Packages: {len(self.installed_packages)} installed                          ║
║  ⚠️  Failed Packages: {len(self.failed_packages)} failed                            ║
║                                                                  ║
║  📁 Installation Path: {str(self.install_path):<30} ║
║                                                                  ║
║  🚀 Ready to launch Ultimate Suite v9.0!                       ║
║                                                                  ║
║  Launch command:                                                 ║
║  python ultimate_webapp_v9.py                                   ║
║                                                                  ║
║  Web interface will be available at:                            ║
║  http://127.0.0.1:5000                                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """
        print(summary)
        
        if self.failed_packages:
            print("\n⚠️ Failed Packages (optional features may be limited):")
            for package in self.failed_packages:
                print(f"   • {package}")
                
    def launch_suite(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Launch Ultimate Suite v9.0"""
        logger.info("🚀 Launching Ultimate Suite v9.0...")
        
        try:
            # Change to installation directory
            os.chdir(self.install_path)
            
            # Import and run the suite
            sys.path.insert(0, str(self.install_path))
            
            from ultimate_webapp_v9 import UltimateSuiteV9
            
            # Create configuration path
            config_path = self.install_path / "config" / "ultimate_suite_v9.json"
            
            # Initialize and run the suite
            suite = UltimateSuiteV9(str(config_path))
            suite.run(host=host, port=port, debug=debug)
            
        except ImportError as e:
            logger.error(f"❌ Failed to import Ultimate Suite: {e}")
            logger.info("Please ensure all components are properly installed")
        except Exception as e:
            logger.error(f"❌ Failed to launch Ultimate Suite: {e}")

def main():
    """Main installation function"""
    parser = argparse.ArgumentParser(description="Ultimate Suite v9.0 Installer")
    parser.add_argument("--install-dir", default=".", help="Installation directory")
    parser.add_argument("--launch", action="store_true", help="Launch after installation")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional packages")
    
    args = parser.parse_args()
    
    # Create configuration
    config = InstallationConfig(install_dir=args.install_dir)
    
    if args.skip_optional:
        config.optional_packages = []
        
    # Create installer
    installer = UltimateSuiteInstaller(config)
    
    # Run installation
    if installer.run_installation():
        if args.launch:
            installer.launch_suite(host=args.host, port=args.port, debug=args.debug)
        else:
            print("\n🎉 Installation complete! To launch:")
            print(f"   cd {installer.install_path}")
            print("   python ultimate_webapp_v9.py")
    else:
        print("\n❌ Installation failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
