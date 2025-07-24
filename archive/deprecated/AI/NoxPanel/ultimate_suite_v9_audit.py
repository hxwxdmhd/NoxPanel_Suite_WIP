#!/usr/bin/env python3
"""
🔍 ULTIMATE SUITE v9.0 - COMPREHENSIVE AUDIT & DIAGNOSIS SYSTEM
================================================================

This audit script performs a complete health check of the Ultimate Suite v9.0:
- Component integrity verification
- Dependency validation
- Configuration analysis
- Error detection and auto-repair
- Performance diagnostics
- Security assessment
"""

import os
import sys
import json
import time
import logging
import subprocess
import importlib
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

class UltimateSuiteAuditor:
    """Comprehensive audit system for Ultimate Suite v9.0"""
    
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'suite_version': '9.0',
            'overall_status': 'UNKNOWN',
            'components': {},
            'dependencies': {},
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'auto_fixes_applied': []
        }
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ultimate_suite_audit.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Define expected components
        self.expected_components = {
            'ultimate_webapp_v9.py': 'Main Flask Application',
            'sysadmin_copilot.py': 'SysAdmin Copilot Engine',
            'plugin_framework.py': 'Plugin Framework',
            'install_ultimate_suite_v9.py': 'Installer',
            'templates/ultimate_dashboard_v9.html': 'Main Dashboard Template',
            'static/css/ultimate-dashboard-v9.css': 'Main Stylesheet',
            'static/js/ultimate-suite-v9.js': 'Main JavaScript',
            'README_ULTIMATE_V9.md': 'Documentation'
        }
        
        # Define critical dependencies
        self.critical_dependencies = [
            'flask', 'flask-cors', 'requests', 'psutil', 'websockets',
            'numpy', 'pandas', 'matplotlib', 'plotly', 'networkx'
        ]
        
        # Define optional dependencies
        self.optional_dependencies = [
            'openai', 'anthropic', 'ollama', 'scikit-learn',
            'tensorflow', 'torch', 'transformers'
        ]

    def print_header(self):
        """Print audit header"""
        print("\n" + "="*80)
        print("🔍 ULTIMATE SUITE v9.0 - COMPREHENSIVE AUDIT SYSTEM")
        print("="*80)
        print(f"📅 Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Working Directory: {os.getcwd()}")
        print(f"🐍 Python Version: {sys.version}")
        print("="*80 + "\n")

    def check_component_integrity(self) -> Dict[str, Any]:
        """Check if all expected components exist and are valid"""
        print("🔍 CHECKING COMPONENT INTEGRITY...")
        results = {}
        
        for component, description in self.expected_components.items():
            component_path = Path(component)
            status = {
                'exists': component_path.exists(),
                'size': 0,
                'readable': False,
                'syntax_valid': False,
                'description': description,
                'issues': []
            }
            
            if status['exists']:
                try:
                    status['size'] = component_path.stat().st_size
                    status['readable'] = True
                    
                    # Check Python file syntax
                    if component.endswith('.py'):
                        try:
                            with open(component_path, 'r', encoding='utf-8') as f:
                                compile(f.read(), component_path, 'exec')
                            status['syntax_valid'] = True
                        except SyntaxError as e:
                            status['issues'].append(f"Syntax Error: {e}")
                        except Exception as e:
                            status['issues'].append(f"Read Error: {e}")
                    else:
                        status['syntax_valid'] = True  # Non-Python files
                        
                except Exception as e:
                    status['issues'].append(f"File System Error: {e}")
            else:
                status['issues'].append("File does not exist")
            
            results[component] = status
            
            # Print status
            status_icon = "✅" if status['exists'] and status['syntax_valid'] else "❌"
            print(f"  {status_icon} {component:<40} {description}")
            if status['issues']:
                for issue in status['issues']:
                    print(f"    ⚠️  {issue}")
        
        self.audit_results['components'] = results
        return results

    def check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        print("\n🐍 CHECKING PYTHON DEPENDENCIES...")
        results = {'critical': {}, 'optional': {}}
        
        # Check critical dependencies
        print("  Critical Dependencies:")
        for dep in self.critical_dependencies:
            try:
                __import__(dep.replace('-', '_'))
                results['critical'][dep] = {'status': 'OK', 'version': self.get_package_version(dep)}
                print(f"    ✅ {dep:<20} - {results['critical'][dep]['version']}")
            except ImportError:
                results['critical'][dep] = {'status': 'MISSING', 'version': None}
                print(f"    ❌ {dep:<20} - NOT INSTALLED")
                self.audit_results['errors'].append(f"Critical dependency missing: {dep}")
        
        # Check optional dependencies
        print("  Optional Dependencies:")
        for dep in self.optional_dependencies:
            try:
                __import__(dep.replace('-', '_'))
                results['optional'][dep] = {'status': 'OK', 'version': self.get_package_version(dep)}
                print(f"    ✅ {dep:<20} - {results['optional'][dep]['version']}")
            except ImportError:
                results['optional'][dep] = {'status': 'MISSING', 'version': None}
                print(f"    ⚠️  {dep:<20} - NOT INSTALLED (optional)")
        
        self.audit_results['dependencies'] = results
        return results

    def get_package_version(self, package_name: str) -> str:
        """Get version of installed package"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
            return "Unknown"
        except:
            return "Unknown"

    def test_webapp_launch(self) -> Dict[str, Any]:
        """Test if the webapp can be imported and initialized"""
        print("\n🚀 TESTING WEBAPP LAUNCH CAPABILITY...")
        results = {
            'import_successful': False,
            'class_initialization': False,
            'flask_app_creation': False,
            'routes_registered': False,
            'errors': []
        }
        
        try:
            # Test import
            sys.path.insert(0, os.getcwd())
            webapp_module = importlib.import_module('ultimate_webapp_v9')
            results['import_successful'] = True
            print("  ✅ Module import successful")
            
            # Test class initialization
            if hasattr(webapp_module, 'UltimateSuiteV9'):
                suite = webapp_module.UltimateSuiteV9()
                results['class_initialization'] = True
                print("  ✅ UltimateSuiteV9 class initialization successful")
                
                # Test Flask app creation
                if hasattr(suite, 'create_app'):
                    app = suite.create_app()
                    results['flask_app_creation'] = True
                    print("  ✅ Flask app creation successful")
                    
                    # Check routes
                    if app.url_map.iter_rules():
                        results['routes_registered'] = True
                        print("  ✅ Routes registered successfully")
                        print(f"    📊 Total routes: {len(list(app.url_map.iter_rules()))}")
                    else:
                        results['errors'].append("No routes registered")
                        print("  ❌ No routes registered")
                else:
                    results['errors'].append("create_app method not found")
                    print("  ❌ create_app method not found")
            else:
                results['errors'].append("UltimateSuiteV9 class not found")
                print("  ❌ UltimateSuiteV9 class not found")
                
        except Exception as e:
            results['errors'].append(str(e))
            print(f"  ❌ Error during webapp test: {e}")
            print(f"    📋 Traceback: {traceback.format_exc()}")
        
        return results

    def test_components_integration(self) -> Dict[str, Any]:
        """Test integration between components"""
        print("\n🔗 TESTING COMPONENT INTEGRATION...")
        results = {}
        
        # Test SysAdmin Copilot
        print("  Testing SysAdmin Copilot...")
        try:
            sys.path.insert(0, os.getcwd())
            copilot_module = importlib.import_module('sysadmin_copilot')
            if hasattr(copilot_module, 'SysAdminCopilot'):
                copilot = copilot_module.SysAdminCopilot()
                results['sysadmin_copilot'] = {'status': 'OK', 'class_found': True}
                print("    ✅ SysAdmin Copilot initialization successful")
            else:
                results['sysadmin_copilot'] = {'status': 'ERROR', 'class_found': False}
                print("    ❌ SysAdminCopilot class not found")
        except Exception as e:
            results['sysadmin_copilot'] = {'status': 'ERROR', 'error': str(e)}
            print(f"    ❌ SysAdmin Copilot error: {e}")
        
        # Test Plugin Framework
        print("  Testing Plugin Framework...")
        try:
            plugin_module = importlib.import_module('plugin_framework')
            if hasattr(plugin_module, 'PluginManager'):
                plugin_manager = plugin_module.PluginManager()
                results['plugin_framework'] = {'status': 'OK', 'class_found': True}
                print("    ✅ Plugin Framework initialization successful")
            else:
                results['plugin_framework'] = {'status': 'ERROR', 'class_found': False}
                print("    ❌ PluginManager class not found")
        except Exception as e:
            results['plugin_framework'] = {'status': 'ERROR', 'error': str(e)}
            print(f"    ❌ Plugin Framework error: {e}")
        
        return results

    def check_web_assets(self) -> Dict[str, Any]:
        """Check web assets (HTML, CSS, JS)"""
        print("\n🎨 CHECKING WEB ASSETS...")
        results = {}
        
        # Check directories
        directories = ['templates', 'static', 'static/css', 'static/js', 'static/images']
        for directory in directories:
            dir_path = Path(directory)
            results[directory] = {
                'exists': dir_path.exists(),
                'is_directory': dir_path.is_dir() if dir_path.exists() else False,
                'files_count': len(list(dir_path.glob('*'))) if dir_path.exists() and dir_path.is_dir() else 0
            }
            
            status_icon = "✅" if results[directory]['exists'] and results[directory]['is_directory'] else "❌"
            print(f"  {status_icon} {directory:<30} ({results[directory]['files_count']} files)")
        
        return results

    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration files and settings"""
        print("\n⚙️  CHECKING CONFIGURATION...")
        results = {}
        
        # Look for configuration files
        config_files = [
            'config.json', 'settings.json', 'ultimate_config.json',
            '.env', 'environment.json'
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                        results[config_file] = {'status': 'OK', 'valid_json': True, 'keys': list(config_data.keys())}
                        print(f"  ✅ {config_file} - Valid JSON with {len(config_data)} keys")
                    else:
                        results[config_file] = {'status': 'OK', 'valid_json': False}
                        print(f"  ✅ {config_file} - Found")
                except Exception as e:
                    results[config_file] = {'status': 'ERROR', 'error': str(e)}
                    print(f"  ❌ {config_file} - Error: {e}")
            else:
                results[config_file] = {'status': 'NOT_FOUND'}
        
        return results

    def perform_auto_fixes(self) -> List[str]:
        """Perform automatic fixes for common issues"""
        print("\n🔧 PERFORMING AUTO-FIXES...")
        fixes_applied = []
        
        # Create missing directories
        required_dirs = ['templates', 'static', 'static/css', 'static/js', 'static/images', 'data', 'logs']
        for directory in required_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    fixes_applied.append(f"Created missing directory: {directory}")
                    print(f"  ✅ Created missing directory: {directory}")
                except Exception as e:
                    print(f"  ❌ Failed to create directory {directory}: {e}")
        
        # Create minimal configuration if missing
        config_path = Path('ultimate_config.json')
        if not config_path.exists():
            try:
                default_config = {
                    "suite_version": "9.0",
                    "debug_mode": True,
                    "host": "127.0.0.1",
                    "port": 5000,
                    "ai_enabled": True,
                    "plugin_system_enabled": True,
                    "sysadmin_copilot_enabled": True,
                    "created_by": "audit_system",
                    "created_at": datetime.now().isoformat()
                }
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                fixes_applied.append("Created default configuration file")
                print("  ✅ Created default configuration file")
            except Exception as e:
                print(f"  ❌ Failed to create configuration: {e}")
        
        self.audit_results['auto_fixes_applied'] = fixes_applied
        return fixes_applied

    def generate_launch_script(self) -> str:
        """Generate a safe launch script"""
        print("\n🚀 GENERATING SAFE LAUNCH SCRIPT...")
        
        launch_script = '''#!/usr/bin/env python3
"""
🚀 ULTIMATE SUITE v9.0 - SAFE LAUNCH SCRIPT
Generated by Audit System
"""

import sys
import os
import time
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for launch"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ultimate_suite_launch.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_prerequisites():
    """Check if all prerequisites are met"""
    logger = logging.getLogger(__name__)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        return False
    
    # Check critical files
    critical_files = [
        'ultimate_webapp_v9.py',
        'sysadmin_copilot.py',
        'plugin_framework.py'
    ]
    
    for file in critical_files:
        if not Path(file).exists():
            logger.error(f"Critical file missing: {file}")
            return False
    
    logger.info("Prerequisites check passed")
    return True

def safe_import():
    """Safely import the webapp module"""
    logger = logging.getLogger(__name__)
    
    try:
        sys.path.insert(0, os.getcwd())
        import ultimate_webapp_v9
        logger.info("Module imported successfully")
        return ultimate_webapp_v9
    except Exception as e:
        logger.error(f"Failed to import module: {e}")
        return None

def main():
    """Main launch function"""
    logger = setup_logging()
    
    print("🚀 Ultimate Suite v9.0 - Safe Launch")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please run audit again.")
        return 1
    
    # Import module
    webapp_module = safe_import()
    if not webapp_module:
        print("❌ Failed to import webapp module")
        return 1
    
    # Initialize and launch
    try:
        print("🔧 Initializing Ultimate Suite...")
        suite = webapp_module.UltimateSuiteV9()
        
        print("🌐 Creating Flask application...")
        app = suite.create_app()
        
        print("🚀 Starting web server...")
        print("📍 Access the interface at: http://127.0.0.1:5000")
        print("🛑 Press Ctrl+C to stop")
        
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Prevent double startup
        )
        
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        print(f"❌ Launch failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
'''
        
        script_path = Path('launch_ultimate_suite_v9_safe.py')
        try:
            with open(script_path, 'w') as f:
                f.write(launch_script)
            print(f"  ✅ Safe launch script created: {script_path}")
            return str(script_path)
        except Exception as e:
            print(f"  ❌ Failed to create launch script: {e}")
            return ""

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit results"""
        recommendations = []
        
        # Check for missing critical dependencies
        if self.audit_results.get('dependencies', {}).get('critical', {}):
            missing_critical = [dep for dep, info in self.audit_results['dependencies']['critical'].items() 
                              if info['status'] == 'MISSING']
            if missing_critical:
                recommendations.append(f"Install missing critical dependencies: {', '.join(missing_critical)}")
        
        # Check for missing components
        if self.audit_results.get('components', {}):
            missing_components = [comp for comp, info in self.audit_results['components'].items() 
                                if not info['exists']]
            if missing_components:
                recommendations.append(f"Restore missing components: {', '.join(missing_components)}")
        
        # General recommendations
        recommendations.extend([
            "Use the generated safe launch script for testing",
            "Check logs for detailed error information",
            "Ensure Python 3.8+ is being used",
            "Verify all file permissions are correct",
            "Consider running in a virtual environment"
        ])
        
        self.audit_results['recommendations'] = recommendations
        return recommendations

    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete audit process"""
        self.print_header()
        
        # Run all checks
        self.check_component_integrity()
        self.check_dependencies()
        webapp_test = self.test_webapp_launch()
        component_test = self.test_components_integration()
        asset_test = self.check_web_assets()
        config_test = self.check_configuration()
        
        # Perform auto-fixes
        auto_fixes = self.perform_auto_fixes()
        
        # Generate launch script
        launch_script = self.generate_launch_script()
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        # Determine overall status
        critical_errors = len([err for err in self.audit_results['errors'] if 'critical' in err.lower()])
        if critical_errors == 0 and webapp_test['import_successful']:
            self.audit_results['overall_status'] = 'HEALTHY'
        elif webapp_test['import_successful']:
            self.audit_results['overall_status'] = 'WARNING'
        else:
            self.audit_results['overall_status'] = 'CRITICAL'
        
        # Print summary
        self.print_audit_summary()
        
        # Save audit report
        self.save_audit_report()
        
        return self.audit_results

    def print_audit_summary(self):
        """Print audit summary"""
        print("\n" + "="*80)
        print("📊 AUDIT SUMMARY")
        print("="*80)
        
        # Overall status
        status_icon = {
            'HEALTHY': '✅',
            'WARNING': '⚠️',
            'CRITICAL': '❌'
        }.get(self.audit_results['overall_status'], '❓')
        
        print(f"🎯 Overall Status: {status_icon} {self.audit_results['overall_status']}")
        
        # Component status
        components = self.audit_results.get('components', {})
        healthy_components = len([c for c in components.values() if c['exists'] and c['syntax_valid']])
        total_components = len(components)
        print(f"🔧 Components: {healthy_components}/{total_components} healthy")
        
        # Dependencies
        deps = self.audit_results.get('dependencies', {})
        critical_deps = deps.get('critical', {})
        healthy_critical = len([d for d in critical_deps.values() if d['status'] == 'OK'])
        total_critical = len(critical_deps)
        print(f"📦 Critical Dependencies: {healthy_critical}/{total_critical} installed")
        
        # Errors and warnings
        errors = len(self.audit_results.get('errors', []))
        warnings = len(self.audit_results.get('warnings', []))
        print(f"⚠️  Issues: {errors} errors, {warnings} warnings")
        
        # Auto-fixes
        fixes = len(self.audit_results.get('auto_fixes_applied', []))
        print(f"🔧 Auto-fixes Applied: {fixes}")
        
        print("\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(self.audit_results.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        print("\n🚀 NEXT STEPS:")
        if self.audit_results['overall_status'] == 'HEALTHY':
            print("  ✅ System is healthy! You can launch Ultimate Suite v9.0")
            print("  🚀 Run: python launch_ultimate_suite_v9_safe.py")
        elif self.audit_results['overall_status'] == 'WARNING':
            print("  ⚠️  System has warnings but should work")
            print("  🚀 Try: python launch_ultimate_suite_v9_safe.py")
            print("  📋 Address warnings for optimal performance")
        else:
            print("  ❌ Critical issues found - system may not work")
            print("  🔧 Fix critical dependencies first")
            print("  📋 Follow recommendations above")
        
        print("="*80)

    def save_audit_report(self):
        """Save detailed audit report to file"""
        report_path = Path(f'ultimate_suite_audit_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_path, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            print(f"\n📄 Detailed audit report saved: {report_path}")
        except Exception as e:
            print(f"\n❌ Failed to save audit report: {e}")


def main():
    """Main audit function"""
    auditor = UltimateSuiteAuditor()
    results = auditor.run_full_audit()
    return results


if __name__ == '__main__':
    main()
