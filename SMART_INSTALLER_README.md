# 🧠 NoxSuite Smart Self-Healing Installer

**Intelligent cross-platform setup with AI-powered error recovery and learning capabilities**

## 🌟 Features

### 🔧 Smart Installation Modes
- **Guided Mode**: Interactive installation with full configuration options
- **Fast Mode**: Quick setup with sensible defaults
- **Dry Run Mode**: Preview installation without making changes
- **Safe Mode**: Minimal installation for maximum stability  
- **Recovery Mode**: Intelligent recovery from previous failures

### 🛠️ Self-Healing Capabilities
- **Failure Analysis**: Learns from previous installation attempts
- **Smart Fallbacks**: Multiple installation methods per dependency
- **Atomic Operations**: Rollback capability for failed steps
- **Error Pattern Recognition**: AI-powered issue identification
- **Automatic Retry Logic**: Configurable retry strategies

### 🌐 Cross-Platform Support
- **Windows**: Chocolatey, WinGet, Scoop support
- **Linux**: APT, YUM, DNF, Pacman support  
- **macOS**: Homebrew, MacPorts support
- **UTF-8 Encoding**: Proper Unicode handling across platforms
- **Permission Detection**: Smart privilege requirement handling

### 📊 Advanced Monitoring
- **Real-time Progress**: ETA calculation with step timing
- **Resource Monitoring**: CPU, memory, disk usage tracking
- **Network Validation**: Connectivity and port availability checks
- **Docker Health Checks**: Comprehensive Docker validation
- **Configuration Validation**: YAML and JSON validation

### 📝 Comprehensive Logging
- **Structured Logging**: JSON logs for machine processing
- **UTF-8 Support**: Proper emoji and Unicode logging
- **Session Tracking**: Unique session IDs for troubleshooting
- **Audit Trail**: Complete installation history
- **Error Context**: Detailed error information with suggestions

## 🚀 Quick Start

### Basic Installation
```bash
# Interactive guided installation
python install_noxsuite.py

# Quick installation with defaults
python install_noxsuite.py fast

# Preview without changes
python install_noxsuite.py dry-run
```

### Recovery from Failures
```bash
# Recover from previous failed installation
python install_noxsuite.py recovery

# Safe mode for troubleshooting
python install_noxsuite.py safe
```

### Utility Commands
```bash
# Check dependencies
python install_noxsuite.py --check-deps

# Check for updates
python install_noxsuite.py --update

# Show help
python install_noxsuite.py --help
```

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8+ (backwards compatible to 3.6 with limitations)
- **Operating System**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.14+
- **Memory**: 4GB minimum, 8GB recommended for AI features
- **Disk Space**: 2GB minimum, 10GB+ for full installation with AI models
- **Network**: Internet connection for downloads and updates

### Optional Dependencies
The installer can automatically install these if missing:
- **Docker**: Container orchestration (required)
- **Git**: Version control (required)  
- **Node.js**: Frontend development (optional)
- **Package Managers**: Platform-specific package managers

## 🏗️ Architecture

### Core Components

#### 1. SmartLogger
- UTF-8 safe logging with encoding fallbacks
- Structured JSON logs for analysis
- Session tracking and error context
- Cross-platform console support

#### 2. InstallationAuditor  
- Analyzes previous installation logs
- Pattern recognition for common failures
- Generates recovery suggestions
- Maintains issue knowledge database

#### 3. PlatformDetector
- Comprehensive system capability detection
- Package manager discovery
- Encoding and permission testing
- Resource availability assessment

#### 4. SmartDependencyManager
- Multi-method dependency installation
- Version requirement checking
- Smart fallback strategies
- Retry logic with exponential backoff

#### 5. ConfigurationWizard
- ADHD-friendly interface design
- Preview and confirmation screens
- Smart defaults based on system capabilities
- Validation with warnings and recommendations

#### 6. AtomicOperation
- Rollback-capable operations
- Transaction-style execution
- Cleanup on failure
- State persistence

### Installation Flow

```
1. System Detection & Analysis
   ├── Platform capabilities
   ├── Previous failure analysis  
   ├── Resource availability
   └── Permission assessment

2. Configuration & Planning
   ├── Mode selection
   ├── Interactive configuration
   ├── Dependency analysis
   └── Installation preview

3. Pre-Installation Validation
   ├── System compatibility
   ├── Disk space check
   ├── Network connectivity
   └── Permission validation

4. Dependency Management
   ├── Missing dependency detection
   ├── Smart installation strategies
   ├── Version compatibility checks
   └── Verification and testing

5. Directory Setup
   ├── Atomic directory creation
   ├── Permission validation
   ├── Backup existing installations
   └── Structure validation

6. Component Installation
   ├── Core NoxSuite components
   ├── AI models and services
   ├── Frontend applications
   └── Configuration generation

7. Service Configuration
   ├── Docker Compose generation
   ├── Environment configuration
   ├── Network setup
   └── Security configuration

8. Validation & Testing
   ├── Installation verification
   ├── Service health checks
   ├── Configuration validation
   └── Integration testing

9. Finalization
   ├── Startup script generation
   ├── Documentation creation
   ├── Summary report
   └── Next steps guidance
```

## 🔧 Configuration Options

### Installation Modes

#### Guided Mode (Default)
```python
# Full interactive configuration
# - Custom installation directory
# - Module selection
# - Feature configuration
# - AI model selection
# - Advanced options
```

#### Fast Mode
```python
# Sensible defaults for quick setup
install_directory = Path.home() / "noxsuite"
modules = ["noxpanel", "noxguard", "autoimport", "heimnetz-scanner", "plugin-system", "update-manager"]
enable_ai = True
ai_models = ["mistral:7b-instruct", "gemma:7b-it"]
```

#### Safe Mode
```python
# Minimal configuration for stability
modules = ["noxpanel", "noxguard"]  # Core only
enable_ai = False  # No AI features
enable_voice = False
enable_mobile = False
```

### Feature Configuration

#### AI Features
- **Local LLM Support**: Ollama integration with multiple models
- **Voice Interface**: Speech recognition and text-to-speech
- **Workflow Automation**: Langflow integration
- **Smart Assistance**: AI-powered troubleshooting

#### Development Features
- **Hot Reload**: Automatic code reloading
- **Debug Mode**: Enhanced logging and debugging
- **Development Tools**: Additional developer utilities
- **Test Environments**: Isolated testing setup

#### Mobile Features
- **PWA Support**: Progressive Web App functionality
- **Mobile Companion**: NoxGo mobile application
- **QR Code Integration**: Easy mobile access
- **Push Notifications**: Real-time mobile alerts

## 🔍 Troubleshooting

### Common Issues

#### UTF-8/Encoding Issues
```
Problem: Emojis or Unicode characters display incorrectly
Solution: Installer automatically detects and applies encoding fallbacks
```

#### Dependency Installation Failures
```
Problem: Package manager installation fails
Solution: Multiple fallback methods per dependency
- Windows: Chocolatey → WinGet → Scoop → Manual
- Linux: APT → YUM → DNF → Manual  
- macOS: Homebrew → MacPorts → Manual
```

#### Permission Errors
```
Problem: Access denied during installation
Solution: Smart permission detection and elevation
- User directory fallback
- Docker Desktop mode
- Containerized installation
```

#### Network Connectivity Issues
```
Problem: Downloads fail due to network issues
Solution: Multiple retry strategies
- Exponential backoff
- Alternative mirrors  
- Offline mode support
```

### Recovery Mode

When previous installations fail, recovery mode:

1. **Analyzes failure logs** for error patterns
2. **Identifies root causes** using pattern matching
3. **Suggests recovery strategies** based on known issues
4. **Applies smart defaults** to avoid previous failures
5. **Resumes from last successful step** when possible

### Log Analysis

The installer creates detailed logs at:
- `noxsuite_installer.log` - Main installation log
- `INSTALLATION_SUMMARY.json` - Installation summary
- `noxsuite_issues.json` - Known issues database

Log entries include:
- **Structured JSON data** for machine processing
- **Error context and stack traces** for debugging
- **Resource usage statistics** for performance analysis
- **Session tracking** for correlation

## 🔄 Updates and Maintenance

### Automatic Updates
```bash
# Check for installer updates
python install_noxsuite.py --update

# Update installer automatically
python -c "from noxsuite_installer_utils import UpdateChecker; UpdateChecker().auto_update()"
```

### Manual Updates
1. Download latest installer from GitHub releases
2. Replace existing installer files
3. Run update validation: `python install_noxsuite.py --check-deps`

### Maintenance Tasks
- **Log Rotation**: Automatic cleanup of old logs
- **Backup Management**: Automatic backup cleanup after 7 days
- **Resource Monitoring**: Background system monitoring
- **Health Checks**: Periodic installation validation

## 📚 Advanced Usage

### Custom Configuration
```python
# Create custom installation configuration
from noxsuite_smart_installer_complete import InstallConfig, InstallMode
from pathlib import Path

config = InstallConfig(
    install_directory=Path("/opt/noxsuite"),
    modules=["noxpanel", "noxguard", "custom-module"],
    enable_ai=True,
    ai_models=["llama2:7b", "codellama:7b"],
    mode=InstallMode.GUIDED,
    dev_mode=True
)
```

### Programmatic Installation
```python
# Use installer as a library
from noxsuite_smart_installer_complete import SmartNoxSuiteInstaller, InstallMode

installer = SmartNoxSuiteInstaller()
success = installer.run_installation(InstallMode.FAST)
```

### Custom Dependency Handlers
```python
# Add custom dependency installation methods
dependency_manager = installer.dependency_manager
dependency_manager.add_custom_handler("custom-tool", custom_install_function)
```

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run tests: `python -m pytest tests/`
4. Format code: `python -m black noxsuite_smart_installer*.py`

### Adding New Features
1. **Smart Dependency Handlers**: Add new package managers or installation methods
2. **Platform Support**: Extend support for new operating systems
3. **Recovery Strategies**: Add new failure pattern recognition
4. **Validation Rules**: Enhance configuration validation
5. **Monitoring Metrics**: Add new system monitoring capabilities

### Testing
```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests  
python -m pytest tests/integration/

# Run end-to-end tests
python -m pytest tests/e2e/

# Test specific platform
python -m pytest tests/ -k "windows" 
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Project Repository**: https://github.com/noxsuite/noxsuite
- **Documentation**: https://docs.noxsuite.com
- **Issue Tracker**: https://github.com/noxsuite/noxsuite/issues
- **Community Discord**: https://discord.gg/noxsuite
- **Release Notes**: https://github.com/noxsuite/noxsuite/releases

## 🏆 Acknowledgments

- **ADHD-Friendly Design**: Inspired by accessibility and cognitive load research
- **Self-Healing Concepts**: Based on autonomous system design principles  
- **Cross-Platform Support**: Built on Python's excellent cross-platform capabilities
- **Smart Recovery**: Influenced by AI/ML failure analysis techniques

---

**Made with ❤️ for the ADHD community and system administrators everywhere**
