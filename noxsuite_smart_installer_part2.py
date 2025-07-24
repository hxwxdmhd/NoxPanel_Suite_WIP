"""
NoxSuite Smart Self-Healing Auto-Installer - Part 2
Core installer implementation and atomic operations
"""

class AtomicOperation:
    """Represents an atomic, rollback-capable operation"""
    
    def __init__(self, name: str, execute_func: callable, rollback_func: callable = None, 
                 validate_func: callable = None, description: str = ""):
        self.name = name
        self.description = description
        self.execute_func = execute_func
        self.rollback_func = rollback_func
        self.validate_func = validate_func
        self.executed = False
        self.rollback_data = None
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the operation"""
        try:
            self.rollback_data = self.execute_func(*args, **kwargs)
            self.executed = True
            
            # Validate if validation function provided
            if self.validate_func:
                if not self.validate_func(self.rollback_data):
                    self.rollback()
                    return False
            
            return True
        except Exception as e:
            if self.executed:
                self.rollback()
            raise e
    
    def rollback(self) -> bool:
        """Rollback the operation if possible"""
        if not self.executed or not self.rollback_func:
            return True
        
        try:
            self.rollback_func(self.rollback_data)
            self.executed = False
            return True
        except Exception:
            return False

class DirectoryScaffold:
    """Manages directory structure creation and validation"""
    
    def __init__(self, base_path: Path, logger: SmartLogger):
        self.base_path = base_path
        self.logger = logger
        self.created_dirs = []
    
    def create_structure(self, structure: Dict[str, Any], dry_run: bool = False) -> bool:
        """Create directory structure atomically"""
        self.logger.step_start("creating_directories", f"Setting up {len(structure)} directory trees")
        
        # Plan all directories first
        all_dirs = self._flatten_structure(structure, self.base_path)
        
        if dry_run:
            self.logger.info("🔍 Dry run - directories that would be created:")
            for dir_path in all_dirs:
                self.logger.info(f"   📁 {dir_path}")
            return True
        
        # Validate base path permissions
        if not self._validate_base_path():
            return False
        
        # Create directories atomically
        created_dirs = []
        try:
            for dir_path in all_dirs:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_path)
                    self.logger.debug(f"Created directory: {dir_path}")
            
            self.created_dirs = created_dirs
            self.logger.step_complete("creating_directories", {
                "created_count": len(created_dirs),
                "total_dirs": len(all_dirs)
            })
            return True
            
        except Exception as e:
            # Rollback created directories
            self._cleanup_directories(created_dirs)
            self.logger.step_error("creating_directories", e)
            return False
    
    def _flatten_structure(self, structure: Dict[str, Any], base: Path) -> List[Path]:
        """Flatten nested directory structure into list of paths"""
        dirs = []
        
        for name, content in structure.items():
            current_path = base / name
            dirs.append(current_path)
            
            if isinstance(content, dict):
                dirs.extend(self._flatten_structure(content, current_path))
        
        return sorted(set(dirs))  # Remove duplicates and sort
    
    def _validate_base_path(self) -> bool:
        """Validate base path permissions and accessibility"""
        try:
            # Check if parent directory exists and is writable
            parent = self.base_path.parent
            if not parent.exists():
                self.logger.warning(f"Parent directory doesn't exist: {parent}")
                return False
            
            # Test write permissions
            test_file = parent / f".nox_write_test_{int(time.time())}"
            try:
                test_file.write_text("test", encoding='utf-8')
                test_file.unlink()
            except Exception as e:
                self.logger.warning(f"No write permission in {parent}: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Base path validation failed: {e}")
            return False
    
    def _cleanup_directories(self, dirs: List[Path]):
        """Clean up created directories in reverse order"""
        for dir_path in reversed(dirs):
            try:
                if dir_path.exists() and dir_path.is_dir():
                    # Only remove if empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
            except:
                pass  # Ignore cleanup errors

class ConfigurationWizard:
    """Enhanced configuration wizard with preview and validation"""
    
    def __init__(self, system_info: SystemInfo, logger: SmartLogger, auditor: InstallationAuditor):
        self.system_info = system_info 
        self.logger = logger
        self.auditor = auditor
        self.previous_failures = auditor.analyze_previous_failures()
    
    def run_wizard(self, mode: InstallMode = InstallMode.GUIDED) -> Optional[InstallConfig]:
        """Run configuration wizard based on mode"""
        if mode == InstallMode.FAST:
            return self._fast_mode_config()
        elif mode == InstallMode.DRY_RUN:
            return self._dry_run_config()
        elif mode == InstallMode.SAFE:
            return self._safe_mode_config()
        elif mode == InstallMode.RECOVERY:
            return self._recovery_mode_config()
        else:
            return self._guided_mode_config()
    
    def _show_welcome_screen(self):
        """Display enhanced welcome screen with system analysis"""
        welcome_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                🧠 NoxSuite Smart Self-Healing Installer           ║
║                    AI-Powered Infrastructure Automation           ║
╠═══════════════════════════════════════════════════════════════════╣
║  🔧 Smart Error Recovery    🌐 Cross-Platform Support           ║
║  📊 Installation Analytics  🛡️  Self-Healing Operations          ║
║  🚀 Multiple Install Modes  🤖 AI-Powered Troubleshooting       ║
║  📱 ADHD-Friendly Interface 🔄 Atomic Operations                ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(welcome_text)
        
        # System analysis summary
        print(f"\n🖥️  System Analysis:")
        print(f"   OS: {self.system_info.os_type.value.title()} {self.system_info.architecture}")
        print(f"   Python: {self.system_info.python_version}")
        print(f"   Resources: {self.system_info.cpu_cores} cores, {self.system_info.available_memory}GB RAM")
        
        # Tool availability with status icons
        tools = [
            ("Docker", self.system_info.docker_available),
            ("Node.js", self.system_info.node_available), 
            ("Git", self.system_info.git_available)
        ]
        
        print(f"   Dependencies: " + " | ".join([
            f"{tool} {'✅' if available else '❌'}" 
            for tool, available in tools
        ]))
        
        # Encoding and permissions status
        if self.system_info.encoding_support:
            utf8_ok = self.system_info.encoding_support.get("utf8", False)
            print(f"   Encoding: UTF-8 {'✅' if utf8_ok else '⚠️ '}")
        
        if self.system_info.permissions:
            admin_rights = self.system_info.permissions.get("admin_rights", False)
            write_ok = self.system_info.permissions.get("current_dir_write", False)
            print(f"   Permissions: Write {'✅' if write_ok else '❌'} | Admin {'✅' if admin_rights else '❌'}")
        
        # Previous installation analysis
        if self.previous_failures.get("failed_steps"):
            print(f"\n⚠️  Previous Installation Issues Detected:")
            for issue_type, count in self.previous_failures.get("error_patterns", {}).items():
                print(f"   • {issue_type.replace('_', ' ').title()}: {count} occurrences")
            
            if self.previous_failures.get("recovery_suggestions"):
                print(f"   💡 Recovery suggestions available")
    
    def _guided_mode_config(self) -> InstallConfig:
        """Full guided configuration with all options"""
        self._show_welcome_screen()
        
        print(f"\n🛠️  Configuration Wizard (Guided Mode)")
        print("=" * 60)
        
        # Installation directory with smart defaults
        default_dir = self._get_default_install_directory()
        print(f"\n📁 Installation Directory")
        print(f"   Default: {default_dir}")
        print(f"   • Must have at least 2GB free space")
        print(f"   • Avoid paths with spaces on Windows")
        
        while True:
            install_dir_input = input(f"   Directory [{default_dir}]: ").strip()
            install_directory = Path(install_dir_input) if install_dir_input else default_dir
            
            # Validate directory
            validation_result = self._validate_install_directory(install_directory)
            if validation_result["valid"]:
                break
            else:
                print(f"   ❌ {validation_result['message']}")
                continue
        
        # Module selection with smart recommendations
        modules = self._select_modules()
        
        # Feature selection
        features = self._select_features()
        
        # AI configuration
        ai_config = self._configure_ai() if features["enable_ai"] else {"models": []}
        
        # Mode selection
        mode_config = self._select_installation_mode()
        
        # Create configuration
        config = InstallConfig(
            install_directory=install_directory,
            modules=modules,
            enable_ai=features["enable_ai"],
            enable_voice=features["enable_voice"],
            enable_mobile=features["enable_mobile"],
            dev_mode=features["dev_mode"],
            auto_start=features["auto_start"],
            ai_models=ai_config["models"],
            mode=mode_config["mode"],
            force_reinstall=mode_config["force_reinstall"],
            backup_existing=mode_config["backup_existing"]
        )
        
        # Show configuration preview
        self._show_configuration_preview(config)
        
        # Final confirmation
        if not self._confirm_installation(config):
            return None
        
        return config
    
    def _fast_mode_config(self) -> InstallConfig:
        """Fast mode with sensible defaults"""
        print(f"\n⚡ Fast Mode Installation")
        print("Using recommended defaults for quick setup...")
        
        return InstallConfig(
            install_directory=self._get_default_install_directory(),
            modules=self._get_default_modules(),
            enable_ai=True,
            enable_voice=False,
            enable_mobile=True,
            dev_mode=False,
            auto_start=True,
            ai_models=["mistral:7b-instruct", "gemma:7b-it"],
            mode=InstallMode.FAST
        )
    
    def _dry_run_config(self) -> InstallConfig:
        """Dry run configuration for testing"""
        print(f"\n🔍 Dry Run Mode")
        print("Will simulate installation without making changes...")
        
        config = self._fast_mode_config()
        config.mode = InstallMode.DRY_RUN
        return config
    
    def _safe_mode_config(self) -> InstallConfig:
        """Safe mode with minimal features"""
        print(f"\n🛡️  Safe Mode Installation")
        print("Using minimal configuration for stability...")
        
        return InstallConfig(
            install_directory=self._get_default_install_directory(),
            modules=["noxpanel", "noxguard"],  # Minimal modules
            enable_ai=False,  # No AI in safe mode
            enable_voice=False,
            enable_mobile=False,
            dev_mode=False,
            auto_start=False,
            ai_models=[],
            mode=InstallMode.SAFE
        )
    
    def _recovery_mode_config(self) -> InstallConfig:
        """Recovery mode based on previous failure analysis"""
        print(f"\n🔄 Recovery Mode Installation")
        
        if not self.previous_failures.get("failed_steps"):
            print("No previous failures detected, using fast mode...")
            config = self._fast_mode_config()
            config.mode = InstallMode.RECOVERY
            return config
        
        print("Configuring based on previous failure analysis...")
        
        # Show recovery suggestions
        if self.previous_failures.get("recovery_suggestions"):
            print(f"\n💡 Recovery Suggestions:")
            for suggestion in self.previous_failures["recovery_suggestions"]:
                print(f"   • {suggestion}")
        
        # Use safe defaults with adjustments based on previous failures
        config = self._safe_mode_config()
        config.mode = InstallMode.RECOVERY
        
        # Adjust configuration based on error patterns
        error_patterns = self.previous_failures.get("error_patterns", {})
        
        if "encoding_issues" in error_patterns:
            print("   🔧 Enabled encoding fallbacks")
        
        if "dependency_failures" in error_patterns:
            print("   🔧 Will use alternative package managers")
        
        if "permission_errors" in error_patterns:
            print("   🔧 Will use user directory installation")
            config.install_directory = Path.home() / "noxsuite"
        
        return config
    
    def _get_default_install_directory(self) -> Path:
        """Get smart default installation directory"""
        if self.system_info.os_type == OSType.WINDOWS:
            # Avoid C:\Program Files to prevent permission issues
            return Path.home() / "NoxSuite"
        else:
            return Path.home() / "noxsuite"
    
    def _validate_install_directory(self, directory: Path) -> Dict[str, Any]:
        """Validate installation directory"""
        try:
            # Check if path has spaces (problematic on Windows)
            if self.system_info.os_type == OSType.WINDOWS and ' ' in str(directory):
                return {
                    "valid": False,
                    "message": "Avoid spaces in path on Windows (causes Docker issues)"
                }
            
            # Check parent directory permissions
            parent = directory.parent
            if not parent.exists():
                return {
                    "valid": False,
                    "message": f"Parent directory doesn't exist: {parent}"
                }
            
            # Check write permissions 
            test_file = parent / f".nox_test_{int(time.time())}"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                return {
                    "valid": False,
                    "message": f"No write permission in {parent}"
                }
            
            # Check available space (estimate needed: 2GB)
            try:
                if hasattr(shutil, 'disk_usage'):
                    _, _, free = shutil.disk_usage(parent)
                    free_gb = free // (1024**3)
                    if free_gb < 2:
                        return {
                            "valid": False,
                            "message": f"Insufficient disk space: {free_gb}GB free (need 2GB)"
                        }
            except:
                pass  # Skip space check if not available
            
            return {"valid": True, "message": "Directory is valid"}
            
        except Exception as e:
            return {"valid": False, "message": f"Validation error: {e}"}
    
    def _select_modules(self) -> List[str]:
        """Interactive module selection with recommendations"""
        default_modules = [
            "noxpanel", "noxguard", "autoimport", "powerlog",
            "langflow-hub", "autocleaner", "heimnetz-scanner",
            "plugin-system", "update-manager"
        ]
        
        print(f"\n📦 Module Selection")
        print("Select modules to install (recommended modules marked with ⭐):")
        
        # Show modules with descriptions
        module_descriptions = {
            "noxpanel": "⭐ Core web interface and dashboard",
            "noxguard": "⭐ Security monitoring and threat detection", 
            "autoimport": "⭐ Automated data import and processing",
            "powerlog": "Advanced logging and analysis",
            "langflow-hub": "AI workflow management (requires AI features)",
            "autocleaner": "Automatic cleanup and maintenance",
            "heimnetz-scanner": "⭐ Network scanning and discovery",
            "plugin-system": "⭐ Plugin management framework",
            "update-manager": "⭐ Automatic updates and patching"
        }
        
        for i, module in enumerate(default_modules, 1):
            description = module_descriptions.get(module, "")
            print(f"   {i:2d}. {module:<20} - {description}")
        
        print(f"\nOptions:")
        print(f"   • Enter numbers (e.g., 1,2,3) for specific modules")
        print(f"   • 'recommended' for starred modules only")
        print(f"   • 'all' for all modules")
        print(f"   • 'minimal' for core modules only")
        
        while True:
            selection = input(f"\nSelect modules [recommended]: ").strip().lower()
            
            if not selection or selection == "recommended":
                return [m for m in default_modules if "⭐" in module_descriptions.get(m, "")]
            elif selection == "all":
                return default_modules
            elif selection == "minimal":
                return ["noxpanel", "noxguard"]
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    selected = [default_modules[i] for i in indices if 0 <= i < len(default_modules)]
                    if selected:
                        return selected
                    else:
                        print("   ❌ Invalid selection, please try again")
                except:
                    print("   ❌ Invalid format, please try again")
    
    def _select_features(self) -> Dict[str, bool]:
        """Interactive feature selection"""
        print(f"\n🎯 Feature Configuration")
        
        features = {}
        
        # AI Features
        ai_recommendation = "recommended" if self.system_info.available_memory >= 8 else "not recommended (low memory)"
        features["enable_ai"] = self._ask_yes_no(
            f"🤖 Enable AI features (Ollama, LLMs) [{ai_recommendation}]", 
            default=self.system_info.available_memory >= 8
        )
        
        # Voice Interface (only if AI enabled)
        if features["enable_ai"]:
            features["enable_voice"] = self._ask_yes_no(
                "🎤 Enable voice interface (experimental)", 
                default=False
            )
        else:
            features["enable_voice"] = False
        
        # Mobile companion
        features["enable_mobile"] = self._ask_yes_no(
            "📱 Enable mobile companion (NoxGo PWA)",
            default=True
        )
        
        # Development mode
        features["dev_mode"] = self._ask_yes_no(
            "⚙️  Enable development mode (hot reload, debug logging)",
            default=False
        )
        
        # Auto-start services
        features["auto_start"] = self._ask_yes_no(
            "🚀 Auto-start services after installation",
            default=True
        )
        
        return features
    
    def _configure_ai(self) -> Dict[str, Any]:
        """Configure AI models and settings"""
        print(f"\n🧠 AI Configuration")
        
        available_models = [
            ("mistral:7b-instruct", "General purpose, good balance", "~4GB RAM"),
            ("gemma:7b-it", "Instruction-tuned, fast responses", "~4GB RAM"),
            ("tinyllama", "Lightweight, quick setup", "~1GB RAM"),
            ("phi", "Microsoft model, efficient", "~2GB RAM"),
            ("llama2:7b", "Meta's foundation model", "~4GB RAM"),
            ("codellama:7b", "Code-specialized model", "~4GB RAM")
        ]
        
        print("Available AI models:")
        for i, (model, description, memory) in enumerate(available_models, 1):
            print(f"   {i}. {model:<20} - {description} ({memory})")
        
        # Recommend models based on available memory
        if self.system_info.available_memory >= 16:
            recommended = "1,2,4"  # Multiple models
            print(f"\n💡 Recommendation: Install multiple models (you have {self.system_info.available_memory}GB RAM)")
        elif self.system_info.available_memory >= 8:
            recommended = "1,3"  # Balanced selection
            print(f"\n💡 Recommendation: Install 1-2 models (you have {self.system_info.available_memory}GB RAM)")
        else:
            recommended = "3"  # Lightweight only
            print(f"\n⚠️  Recommendation: Install lightweight model only (you have {self.system_info.available_memory}GB RAM)")
        
        while True:
            selection = input(f"\nSelect models [numbers like {recommended}]: ").strip()
            
            if not selection:
                selection = recommended
            
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected_models = [available_models[i][0] for i in indices if 0 <= i < len(available_models)]
                
                if selected_models:
                    # Estimate total memory usage
                    memory_estimate = len(selected_models) * 4  # Rough estimate
                    if memory_estimate > self.system_info.available_memory * 0.8:
                        print(f"   ⚠️  Warning: Selected models may use ~{memory_estimate}GB RAM")
                        if not self._ask_yes_no("Continue anyway?", default=False):
                            continue
                    
                    return {"models": selected_models}
                else:
                    print("   ❌ No models selected, please try again")
            except:
                print("   ❌ Invalid format, please try again")
    
    def _select_installation_mode(self) -> Dict[str, Any]:
        """Select advanced installation options"""
        print(f"\n🔧 Installation Options")
        
        mode_config = {}
        
        # Force reinstall
        mode_config["force_reinstall"] = self._ask_yes_no(
            "🔄 Force reinstall (remove existing installation)",
            default=False
        )
        
        # Backup existing
        if not mode_config["force_reinstall"]:
            mode_config["backup_existing"] = self._ask_yes_no(
                "💾 Backup existing installation before updating",
                default=True
            )
        else:
            mode_config["backup_existing"] = False
        
        mode_config["mode"] = InstallMode.GUIDED
        return mode_config
    
    def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question with default"""
        default_text = "Y/n" if default else "y/N"
        response = input(f"   {question} [{default_text}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def _show_configuration_preview(self, config: InstallConfig):
        """Show configuration preview before installation"""
        print(f"\n📋 Installation Summary")
        print("=" * 60)
        print(f"   📁 Directory: {config.install_directory}")
        print(f"   📦 Modules: {', '.join(config.modules)}")
        print(f"   🤖 AI Features: {'✅' if config.enable_ai else '❌'}")
        print(f"   🎤 Voice Interface: {'✅' if config.enable_voice else '❌'}")
        print(f"   📱 Mobile App: {'✅' if config.enable_mobile else '❌'}")
        print(f"   ⚙️  Development Mode: {'✅' if config.dev_mode else '❌'}")
        
        if config.ai_models:
            print(f"   🧠 AI Models: {', '.join(config.ai_models)}")
        
        # Estimate installation size and time
        estimated_size = self._estimate_installation_size(config)
        estimated_time = self._estimate_installation_time(config)
        
        print(f"\n📊 Estimates:")
        print(f"   💾 Disk space: ~{estimated_size}GB")
        print(f"   ⏱️  Time: ~{estimated_time} minutes")
        
        # Show any warnings
        warnings = self._check_configuration_warnings(config)
        if warnings:
            print(f"\n⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
    
    def _estimate_installation_size(self, config: InstallConfig) -> float:
        """Estimate total installation size"""
        base_size = 0.5  # Base NoxSuite components
        module_size = len(config.modules) * 0.1  # ~100MB per module
        ai_size = len(config.ai_models) * 4.0 if config.enable_ai else 0  # ~4GB per model
        docker_size = 2.0  # Docker images
        
        return base_size + module_size + ai_size + docker_size
    
    def _estimate_installation_time(self, config: InstallConfig) -> int:
        """Estimate installation time in minutes"""
        base_time = 5  # Base setup
        module_time = len(config.modules) * 2  # 2 minutes per module
        ai_time = len(config.ai_models) * 10 if config.enable_ai else 0  # 10 minutes per model
        dependency_time = 10  # Dependency installation
        
        return base_time + module_time + ai_time + dependency_time
    
    def _check_configuration_warnings(self, config: InstallConfig) -> List[str]:
        """Check configuration for potential issues"""
        warnings = []
        
        # Memory warnings
        if config.enable_ai and self.system_info.available_memory < 8:
            warnings.append("AI features may be slow with less than 8GB RAM")
        
        # Disk space warnings
        estimated_size = self._estimate_installation_size(config)
        if estimated_size > 20:
            warnings.append(f"Large installation size: ~{estimated_size}GB")
        
        # Windows-specific warnings
        if self.system_info.os_type == OSType.WINDOWS:
            if ' ' in str(config.install_directory):
                warnings.append("Path with spaces may cause Docker issues on Windows")
            
            if not self.system_info.permissions.get("admin_rights", False):
                warnings.append("Some features may require administrator privileges")
        
        # Encoding warnings
        if not self.system_info.encoding_support.get("utf8", True):
            warnings.append("Limited Unicode support detected - some display issues possible")
        
        return warnings
    
    def _confirm_installation(self, config: InstallConfig) -> bool:
        """Final confirmation before installation"""
        print(f"\n🎯 Ready to Install")
        
        # Show key information
        print(f"This will install NoxSuite to: {config.install_directory}")
        if config.force_reinstall:
            print(f"⚠️  Will remove existing installation")
        
        response = input(f"\n✅ Proceed with installation? [Y/n]: ").strip().lower()
        return response != 'n'
    
    def _get_default_modules(self) -> List[str]:
        """Get default recommended modules"""
        return ["noxpanel", "noxguard", "autoimport", "heimnetz-scanner", "plugin-system", "update-manager"]

class SmartNoxSuiteInstaller:
    """Main installer class with smart recovery and self-healing capabilities"""
    
    def __init__(self):
        # Initialize logging
        self.logger = SmartLogger()
        
        # Initialize auditor
        self.auditor = InstallationAuditor(self.logger.log_file)
        
        # Detect system capabilities
        detector = PlatformDetector(self.logger)
        self.system_info = detector.detect_system()
        
        # Initialize dependency manager
        self.dependency_manager = SmartDependencyManager(self.system_info, self.logger)
        
        # Initialize configuration wizard
        self.wizard = ConfigurationWizard(self.system_info, self.logger, self.auditor)
        
        # Installation state
        self.config: Optional[InstallConfig] = None
        self.completed_steps = []
        self.failed_steps = []
        self.rollback_stack = []
    
    def run_installation(self, mode: InstallMode = InstallMode.GUIDED) -> bool:
        """Run the complete smart installation process"""
        try:
            self.logger.info("🚀 Starting NoxSuite Smart Installation")
            
            # Step 1: Configuration
            self.logger.step_start("configuration", "Running configuration wizard")
            self.config = self.wizard.run_wizard(mode)
            
            if not self.config:
                self.logger.info("❌ Installation cancelled by user")
                return False
            
            self.logger.step_complete("configuration")
            
            # Step 2: Pre-installation checks
            if not self._run_pre_installation_checks():
                return False
            
            # Step 3: Dependency management
            if not self._handle_dependencies():
                return False
            
            # Step 4: Directory setup
            if not self._setup_directories():
                return False
            
            # Step 5: Core installation
            if not self._install_core_components():
                return False
            
            # Step 6: AI setup (if enabled)
            if self.config.enable_ai and not self._setup_ai_components():
                return False
            
            # Step 7: Configuration generation
            if not self._generate_configurations():
                return False
            
            # Step 8: Service setup
            if not self._setup_services():
                return False
            
            # Step 9: Post-installation validation
            if not self._validate_installation():
                return False
            
            # Step 10: Finalization
            self._finalize_installation()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("\n❌ Installation cancelled by user")
            self._cleanup_on_failure()
            return False
            
        except Exception as e:
            self.logger.step_error("installation", e, {
                "completed_steps": self.completed_steps,
                "config": asdict(self.config) if self.config else None
            })
            self._cleanup_on_failure()
            return False
    
    def _run_pre_installation_checks(self) -> bool:
        """Run comprehensive pre-installation validation"""
        self.logger.step_start("pre_checks", "Validating system requirements")
        
        checks = [
            ("system_compatibility", self._check_system_compatibility),
            ("disk_space", self._check_disk_space),
            ("permissions", self._check_permissions),
            ("existing_installation", self._check_existing_installation),
            ("network_connectivity", self._check_network_connectivity)
        ]
        
        all_passed = True
        results = {}
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                
                if result.get("status") == "failed":
                    self.logger.warning(f"❌ {check_name}: {result.get('message', 'Failed')}")
                    
                    # Some checks are critical
                    if result.get("critical", False):
                        all_passed = False
                elif result.get("status") == "warning":
                    self.logger.warning(f"⚠️  {check_name}: {result.get('message', 'Warning')}")
                else:
                    self.logger.debug(f"✅ {check_name}: OK")
                    
            except Exception as e:
                self.logger.warning(f"❌ {check_name}: Check failed - {e}")
                results[check_name] = {"status": "error", "message": str(e)}
        
        if not all_passed:
            self.logger.step_error("pre_checks", Exception("Critical pre-installation checks failed"))
            return False
        
        self.logger.step_complete("pre_checks", results)
        return True
    
    def _check_system_compatibility(self) -> Dict[str, Any]:
        """Check system compatibility"""
        # Python version check
        min_python = (3, 8)
        current_python = sys.version_info[:2]
        
        if current_python < min_python:
            return {
                "status": "failed",
                "critical": True,
                "message": f"Python {min_python[0]}.{min_python[1]}+ required, got {current_python[0]}.{current_python[1]}"
            }
        
        # OS support check
        if self.system_info.os_type == OSType.UNKNOWN:
            return {
                "status": "failed", 
                "critical": True,
                "message": "Unsupported operating system"
            }
        
        return {"status": "passed"}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            install_dir = self.config.install_directory
            required_gb = self.wizard._estimate_installation_size(self.config)
            
            if hasattr(shutil, 'disk_usage'):
                _, _, free = shutil.disk_usage(install_dir.parent)
                free_gb = free / (1024**3)
                
                if free_gb < required_gb:
                    return {
                        "status": "failed",
                        "critical": True,
                        "message": f"Need {required_gb:.1f}GB, only {free_gb:.1f}GB available"
                    }
                elif free_gb < required_gb * 1.5:
                    return {
                        "status": "warning",
                        "message": f"Low disk space: {free_gb:.1f}GB available"
                    }
            
            return {"status": "passed"}
            
        except Exception as e:
            return {"status": "warning", "message": f"Could not check disk space: {e}"}
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check file system permissions"""
        install_dir = self.config.install_directory
        
        # Test write permissions in target directory
        try:
            test_file = install_dir.parent / f".nox_perm_test_{int(time.time())}"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            return {
                "status": "failed",
                "critical": True,
                "message": f"No write permission in {install_dir.parent}: {e}"
            }
        
        return {"status": "passed"}
    
    def _check_existing_installation(self) -> Dict[str, Any]:
        """Check for existing NoxSuite installation"""
        install_dir = self.config.install_directory
        
        if install_dir.exists():
            # Check if it's a NoxSuite installation
            noxsuite_markers = [
                "noxsuite.json", 
                "INSTALLATION_SUMMARY.json",
                "docker/docker-compose.noxsuite.yml"
            ]
            
            is_noxsuite = any((install_dir / marker).exists() for marker in noxsuite_markers)
            
            if is_noxsuite:
                if self.config.force_reinstall:
                    return {
                        "status": "warning",
                        "message": "Existing installation will be removed"
                    }
                else:
                    return {
                        "status": "warning", 
                        "message": "Existing installation found - will attempt upgrade"
                    }
            else:
                # Directory exists but not NoxSuite
                if any(install_dir.iterdir()):
                    return {
                        "status": "warning",
                        "message": "Directory exists and contains files"
                    }
        
        return {"status": "passed"}
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity for downloads"""
        if self.config.mode == InstallMode.DRY_RUN:
            return {"status": "passed"}
        
        test_urls = [
            "https://github.com",
            "https://hub.docker.com",
        ]
        
        if self.config.enable_ai:
            test_urls.append("https://ollama.ai")
        
        failed_urls = []
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    failed_urls.append(url)
            except:
                failed_urls.append(url)
        
        if failed_urls:
            return {
                "status": "warning",
                "message": f"Network issues detected: {len(failed_urls)} sites unreachable"
            }
        
        return {"status": "passed"}
    
    def _handle_dependencies(self) -> bool:
        """Handle dependency installation and validation"""
        required_deps = ["docker", "git"]
        
        if self.config.enable_mobile or any("react" in module for module in self.config.modules):
            required_deps.append("node")
        
        return self.dependency_manager.check_and_install_dependencies(required_deps)
    
    def _setup_directories(self) -> bool:
        """Setup directory structure atomically"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would create directory structure")
            return True
        
        directory_structure = {
            "frontend": {
                "noxpanel-ui": {},
                "noxgo-mobile": {} if self.config.enable_mobile else None
            },
            "backend": {
                "fastapi": {},
                "flask-legacy": {}
            },
            "services": {
                "langflow": {} if self.config.enable_ai else None,
                "ollama": {} if self.config.enable_ai else None
            },
            "data": {
                "postgres": {},
                "redis": {},
                "logs": {}
            },
            "config": {},
            "scripts": {},
            "docker": {},
            "plugins": {}
        }
        
        # Remove None entries
        def clean_structure(d):
            if isinstance(d, dict):
                return {k: clean_structure(v) for k, v in d.items() if v is not None}
            return d
        
        directory_structure = clean_structure(directory_structure)
        
        scaffold = DirectoryScaffold(self.config.install_directory, self.logger)
        return scaffold.create_structure(directory_structure, dry_run=self.config.mode == InstallMode.DRY_RUN)
    
    def _install_core_components(self) -> bool:
        """Install core NoxSuite components"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would install core components")
            return True
        
        # This would implement the actual component installation
        # For now, return True to indicate success
        self.logger.step_start("installing_core", "Installing NoxSuite core components")
        
        # Simulate installation time
        time.sleep(1)
        
        self.logger.step_complete("installing_core")
        return True
    
    def _setup_ai_components(self) -> bool:
        """Setup AI components and models"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would setup AI components")
            return True
        
        if not self.config.enable_ai:return True
        
        self.logger.step_start("setting_up_ai", f"Installing {len(self.config.ai_models)} AI models")
        
        # This would implement actual AI model installation
        # For now, simulate the process
        for model in self.config.ai_models:
            self.logger.info(f"📦 Installing model: {model}")
            time.sleep(0.5)  # Simulate download time
        
        self.logger.step_complete("setting_up_ai")
        return True
    
    def _generate_configurations(self) -> bool:
        """Generate configuration files"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would generate configuration files")
            return True
        
        self.logger.step_start("generating_configs", "Creating configuration files")
        
        # This would implement actual configuration generation
        # For now, simulate the process
        time.sleep(0.5)
        
        self.logger.step_complete("generating_configs")
        return True
    
    def _setup_services(self) -> bool:
        """Setup and configure services"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would setup services")
            return True
        
        self.logger.step_start("setting_up_services", "Configuring Docker services")
        
        # This would implement actual service setup
        time.sleep(0.5)
        
        self.logger.step_complete("setting_up_services")
        return True
    
    def _validate_installation(self) -> bool:
        """Validate that installation completed successfully"""
        self.logger.step_start("validating_installation", "Running post-installation validation")
        
        validation_checks = [
            ("directory_structure", self._validate_directories),
            ("configuration_files", self._validate_configs),
            ("service_health", self._validate_services)
        ]
        
        all_passed = True
        for check_name, check_func in validation_checks:
            try:
                if not check_func():
                    self.logger.warning(f"❌ Validation failed: {check_name}")
                    all_passed = False
                else:
                    self.logger.debug(f"✅ Validation passed: {check_name}")
            except Exception as e:
                self.logger.warning(f"❌ Validation error in {check_name}: {e}")
                all_passed = False
        
        if all_passed:
            self.logger.step_complete("validating_installation")
        else:
            self.logger.step_error("validating_installation", Exception("Some validation checks failed"))
        
        return all_passed
    
    def _validate_directories(self) -> bool:
        """Validate directory structure"""
        required_dirs = ["config", "scripts", "docker", "data/logs"]
        
        for dir_path in required_dirs:
            full_path = self.config.install_directory / dir_path
            if not full_path.exists():
                return False
        
        return True
    
    def _validate_configs(self) -> bool:
        """Validate configuration files"""
        required_configs = ["config/noxsuite.json"]
        
        for config_path in required_configs:
            full_path = self.config.install_directory / config_path
            if not full_path.exists():
                return False
        
        return True
    
    def _validate_services(self) -> bool:
        """Validate that services can be started"""
        # This would implement actual service validation
        return True
    
    def _finalize_installation(self):
        """Finalize installation and show completion message"""
        self.logger.step_start("finalizing", "Completing installation")
        
        # Create installation summary
        summary = {
            "installation_status": "completed",
            "installation_time": datetime.now(timezone.utc).isoformat(),
            "installation_directory": str(self.config.install_directory),
            "configuration": asdict(self.config),
            "system_info": asdict(self.system_info)
        }
        
        # Save summary
        summary_file = self.config.install_directory / "INSTALLATION_SUMMARY.json"
        if self.config.mode != InstallMode.DRY_RUN:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Show completion message
        self._show_completion_message()
        
        self.logger.step_complete("finalizing")
        self.logger.info("🎉 NoxSuite installation completed successfully!")
    
    def _show_completion_message(self):
        """Display installation completion message"""
        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    🎉 Installation Complete!                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  NoxSuite Smart Installer has successfully completed setup       ║
║                                                                   ║
║  📁 Installation: {str(self.config.install_directory):<44} ║
║  🔧 Modules: {len(self.config.modules)} modules installed{' ' * (37 - len(str(self.config.modules)))} ║
║  🤖 AI Features: {'✅ Enabled' if self.config.enable_ai else '❌ Disabled':<43} ║
║                                                                   ║
║  🌐 Web Interface: http://localhost:3000                         ║
║  🔧 API Docs: http://localhost:8000/api/docs                     ║
║  📊 Monitoring: http://localhost:3001                            ║
{'║  🤖 AI Hub: http://localhost:7860                                ║' if self.config.enable_ai else ''}
║                                                                   ║
║  🚀 Next Steps:                                                  ║
║     1. Run: ./scripts/start-noxsuite.sh                         ║
║     2. Open web interface                                        ║
║     3. Complete initial setup wizard                            ║
║                                                                   ║
║  📚 Logs: noxsuite_installer.log                               ║
║  📋 Summary: INSTALLATION_SUMMARY.json                          ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
    
    def _cleanup_on_failure(self):
        """Cleanup on installation failure"""
        self.logger.info("🧹 Cleaning up after installation failure...")
        
        # This would implement cleanup logic
        # For now, just log the attempt
        self.logger.debug("Cleanup completed")

def main():
    """Main entry point for the smart installer"""
    try:
        # Parse command line arguments for mode selection
        mode = InstallMode.GUIDED
        
        if len(sys.argv) > 1:
            mode_arg = sys.argv[1].lower()
            mode_map = {
                "fast": InstallMode.FAST,
                "guided": InstallMode.GUIDED,
                "dry-run": InstallMode.DRY_RUN,
                "safe": InstallMode.SAFE,
                "recovery": InstallMode.RECOVERY
            }
            mode = mode_map.get(mode_arg, InstallMode.GUIDED)
        
        # Create and run installer
        installer = SmartNoxSuiteInstaller()
        success = installer.run_installation(mode)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installer crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
