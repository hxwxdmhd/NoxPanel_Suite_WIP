#!/usr/bin/env python3
"""
NoxSuite Bootstrap Installer
Self-contained installer that bootstraps its own dependencies before launching the full installer
Uses only Python standard library modules to ensure maximum compatibility
"""

import os
import sys
import json
import subprocess
import platform
import tempfile
import urllib.request
import urllib.error
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback

# Force UTF-8 output on Windows
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

class BootstrapLogger:
    """Simple logger using only standard library"""
    
    def __init__(self):
        self.log_file = Path("noxsuite_bootstrap.log")
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Ensure log file exists and is writable"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Bootstrap Session Started: {self._get_timestamp()} ===\n")
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
            self.log_file = None
    
    def _get_timestamp(self):
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _log_to_file(self, level: str, message: str):
        """Log message to file if possible"""
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{self._get_timestamp()}] [{level}] {message}\n")
            except:
                pass  # Silent fail for logging
    
    def info(self, message: str):
        """Log info message"""
        print(f"ℹ️  {message}")
        self._log_to_file("INFO", message)
    
    def success(self, message: str):
        """Log success message"""
        print(f"✅ {message}")
        self._log_to_file("SUCCESS", message)
    
    def warning(self, message: str):
        """Log warning message"""
        print(f"⚠️  {message}")
        self._log_to_file("WARNING", message)
    
    def error(self, message: str):
        """Log error message"""
        print(f"❌ {message}")
        self._log_to_file("ERROR", message)
    
    def debug(self, message: str):
        """Log debug message"""
        self._log_to_file("DEBUG", message)

class DependencyInstaller:
    """Handles installation of required Python packages"""
    
    def __init__(self, logger: BootstrapLogger):
        self.logger = logger
        self.required_packages = [
            'requests>=2.25.0',
            'chardet>=4.0.0'
        ]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check which dependencies are available"""
        status = {}
        
        for package in self.required_packages:
            package_name = package.split('>=')[0].split('==')[0]
            try:
                __import__(package_name)
                status[package_name] = True
                self.logger.debug(f"Found package: {package_name}")
            except ImportError:
                status[package_name] = False
                self.logger.debug(f"Missing package: {package_name}")
        
        return status
    
    def install_package(self, package: str) -> bool:
        """Install a single package using various methods"""
        self.logger.info(f"Installing {package}...")
        
        try:
            # Try different installation methods in order of preference
            install_methods = [
                # Standard pip install
                [sys.executable, '-m', 'pip', 'install', package],
                ['pip3', 'install', package],
                ['pip', 'install', package],
                
                # User install (for managed environments)
                [sys.executable, '-m', 'pip', 'install', '--user', package],
                ['pip3', 'install', '--user', package],
                
                # Break system packages (last resort)
                [sys.executable, '-m', 'pip', 'install', '--break-system-packages', package],
                ['pip3', 'install', '--break-system-packages', package],
                
                # Try system package manager (Linux)
                ['apt-get', 'install', '-y', f'python3-{package.split(">=")[0]}'],
                ['yum', 'install', '-y', f'python3-{package.split(">=")[0]}'],
                ['dnf', 'install', '-y', f'python3-{package.split(">=")[0]}'],
                
                # Try package managers (macOS)
                ['brew', 'install', f'python3-{package.split(">=")[0]}'],
            ]
            
            for cmd in install_methods:
                try:
                    self.logger.debug(f"Trying: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    if result.returncode == 0:
                        self.logger.success(f"Successfully installed {package} using {cmd[0]}")
                        return True
                    else:
                        self.logger.debug(f"Command failed with return code {result.returncode}")
                        if result.stderr:
                            self.logger.debug(f"Error output: {result.stderr.strip()}")
                        
                        # Check for specific error patterns
                        if "externally-managed-environment" in result.stderr:
                            self.logger.debug("Detected externally managed environment, trying alternative methods...")
                            continue
                        
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    self.logger.debug(f"Command not available or timed out: {' '.join(cmd)}")
                    continue
                except Exception as e:
                    self.logger.debug(f"Exception with command {' '.join(cmd)}: {e}")
                    continue
            
            self.logger.error(f"Failed to install {package} with all available methods")
            return False
            
        except Exception as e:
            self.logger.error(f"Exception during installation of {package}: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        self.logger.info("Checking and installing dependencies...")
        
        status = self.check_dependencies()
        missing = [pkg for pkg, available in status.items() if not available]
        
        if not missing:
            self.logger.success("All dependencies are already available!")
            return True
        
        self.logger.info(f"Missing dependencies: {', '.join(missing)}")
        
        # Install missing packages
        success_count = 0
        for package in self.required_packages:
            package_name = package.split('>=')[0].split('==')[0]
            if package_name in missing:
                if self.install_package(package):
                    success_count += 1
        
        # Verify installations
        final_status = self.check_dependencies()
        still_missing = [pkg for pkg, available in final_status.items() if not available]
        
        if still_missing:
            self.logger.warning(f"Still missing: {', '.join(still_missing)}")
            self.logger.warning("The installer will attempt to run with reduced functionality")
            return False
        else:
            self.logger.success("All dependencies installed successfully!")
            return True

class SystemChecker:
    """Check system compatibility and requirements"""
    
    def __init__(self, logger: BootstrapLogger):
        self.logger = logger
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        version = sys.version_info
        required = (3, 8)
        
        self.logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
        
        if version >= required:
            self.logger.success(f"Python version {version.major}.{version.minor} is compatible")
            return True
        else:
            self.logger.error(f"Python {required[0]}.{required[1]}+ is required")
            return False
    
    def check_network_connectivity(self) -> bool:
        """Check if we can reach the internet"""
        test_urls = [
            'https://pypi.org',
            'https://github.com',
            'https://google.com'
        ]
        
        for url in test_urls:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    if response.getcode() == 200:
                        self.logger.success("Network connectivity confirmed")
                        return True
            except:
                continue
        
        self.logger.warning("Network connectivity check failed")
        self.logger.warning("Some features may not work without internet access")
        return False
    
    def check_permissions(self) -> bool:
        """Check if we have necessary permissions"""
        test_dir = Path.cwd() / "noxsuite_permission_test"
        
        try:
            test_dir.mkdir(exist_ok=True)
            test_file = test_dir / "test.txt"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            test_dir.rmdir()
            
            self.logger.success("File system permissions confirmed")
            return True
            
        except Exception as e:
            self.logger.error(f"Insufficient permissions: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'architecture': platform.architecture(),
            'python_version': sys.version,
            'python_executable': sys.executable,
            'working_directory': str(Path.cwd()),
            'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        }

class NoxSuiteBootstrap:
    """Main bootstrap class"""
    
    def __init__(self):
        self.logger = BootstrapLogger()
        self.system_checker = SystemChecker(self.logger)
        self.dependency_installer = DependencyInstaller(self.logger)
    
    def show_banner(self):
        """Show welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║              🧠 NoxSuite Bootstrap Installer v1.0                ║
║              Self-Contained Dependency Manager                    ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        self.logger.info("NoxSuite Bootstrap Installer started")
    
    def run_system_checks(self) -> bool:
        """Run all system compatibility checks"""
        self.logger.info("Running system compatibility checks...")
        
        checks = [
            ("Python Version", self.system_checker.check_python_version),
            ("File Permissions", self.system_checker.check_permissions),
            ("Network Connectivity", self.system_checker.check_network_connectivity)
        ]
        
        results = []
        for check_name, check_func in checks:
            self.logger.info(f"Checking {check_name}...")
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error during {check_name} check: {e}")
                results.append(False)
        
        # Log system info
        system_info = self.system_checker.get_system_info()
        self.logger.debug(f"System info: {json.dumps(system_info, indent=2)}")
        
        critical_checks = results[:2]  # Python version and permissions are critical
        if not all(critical_checks):
            self.logger.error("Critical system checks failed")
            return False
        
        self.logger.success("System compatibility checks completed")
        return True
    
    def bootstrap_dependencies(self) -> bool:
        """Bootstrap all required dependencies"""
        self.logger.info("Bootstrapping dependencies...")
        return self.dependency_installer.install_dependencies()
    
    def launch_main_installer(self, args: List[str]) -> bool:
        """Launch the main NoxSuite installer"""
        self.logger.info("Launching main installer...")
        
        try:
            # Check if main installer exists
            main_installer = Path("noxsuite_smart_installer_complete.py")
            if not main_installer.exists():
                self.logger.error("Main installer file not found: noxsuite_smart_installer_complete.py")
                return False
            
            # Import and run the main installer
            sys.path.insert(0, str(Path.cwd()))
            
            try:
                from noxsuite_smart_installer_complete import SmartNoxSuiteInstaller, InstallMode
                from install_noxsuite import main as launcher_main
                
                # Pass control to the launcher with original arguments
                launcher_main()
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to launch main installer: {e}")
                self.logger.debug(f"Traceback: {traceback.format_exc()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during installer launch: {e}")
            return False
    
    def run(self, args: List[str]) -> bool:
        """Main bootstrap process"""
        try:
            self.show_banner()
            
            # Skip bootstrap for certain commands
            if args and args[0] in ['--help', '-h', '--version']:
                return self.launch_main_installer(args)
            
            # Run system checks
            if not self.run_system_checks():
                self.logger.error("System checks failed. Cannot continue.")
                return False
            
            # Bootstrap dependencies
            deps_ok = self.bootstrap_dependencies()
            if not deps_ok:
                self.logger.warning("Some dependencies could not be installed")
                self.logger.warning("Attempting to continue with reduced functionality...")
            
            # Launch main installer
            return self.launch_main_installer(args)
            
        except KeyboardInterrupt:
            self.logger.warning("Bootstrap cancelled by user")
            return False
        except Exception as e:
            self.logger.error(f"Bootstrap failed: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            return False

def main():
    """Entry point"""
    bootstrap = NoxSuiteBootstrap()
    success = bootstrap.run(sys.argv[1:])
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
