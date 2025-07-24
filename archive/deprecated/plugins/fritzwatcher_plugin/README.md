# 🔍 FRITZWATCHER Plugin

**Advanced Fritz!Box Monitoring and Management System**

## 🎯 Overview

FRITZWATCHER is a comprehensive plugin for monitoring and managing Fritz!Box routers with advanced features including:

- **Multi-router support** with automatic discovery
- **Roaming device tracking** across network segments
- **Secure credential management** via KeePass integration
- **Real-time monitoring** with resilience and failover
- **Interactive UX customization** with ADHD-friendly themes
- **Comprehensive API** for integration and automation

## 🚀 Features

### Core Functionality
- **TR-064 SOAP API Integration**: Full access to Fritz!Box functionality
- **Multi-Router Support**: Monitor multiple routers simultaneously
- **Device Tracking**: Track device connections and roaming patterns
- **Guest WiFi Management**: Control guest network access
- **Signal Quality Monitoring**: Monitor connection quality and strength

### Security & Credentials
- **KeePass Integration**: Secure credential storage and retrieval
- **Interactive Database Selection**: Choose your preferred KeePass database
- **Multiple Access Methods**: CLI, browser integration, and direct access
- **Encrypted Storage**: All sensitive data encrypted at rest
- **Audit Logging**: Complete audit trail for security compliance

### Resilience & Reliability
- **Automatic Retry Logic**: Configurable retry with exponential backoff
- **Failover Support**: Automatic failover between routers
- **Health Monitoring**: Continuous router health assessment
- **Graceful Degradation**: Continues operation with partial failures

### User Experience
- **Device Auto-Detection**: Automatic device type identification using OUI database
- **Custom Device Labels**: Personalize device names and icons
- **ADHD-Friendly Themes**: "Spicy" (high contrast) and "Steady" (minimal) themes
- **Interactive Web Interface**: Real-time dashboard with customizable views

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- KeePass or KeePassXC (for credential management)
- Network access to Fritz!Box routers
- NoxPanel Plugin System

### Required Dependencies
```bash
pip install aiohttp>=3.8.0 pykeepass>=4.0.0
```

### Optional Dependencies
```bash
pip install pytest>=7.0.0 docker  # For testing
```

## ⚙️ Configuration

### Basic Configuration
```json
{
  "routers": [
    {
      "hostname": "fritz.box",
      "port": 49000,
      "nickname": "Main Router",
      "priority": 1
    }
  ],
  "credentials": {
    "prompt_for_selection": true,
    "use_cli": false,
    "use_browser_integration": false
  },
  "monitoring": {
    "poll_interval": 30,
    "roaming_detection": true,
    "signal_monitoring": true
  }
}
```

### Advanced Configuration
```json
{
  "resilience": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "failover_enabled": true,
    "health_check_interval": 60
  },
  "ui_customization": {
    "theme": "spicy",
    "device_auto_detection": true,
    "show_device_icons": true,
    "custom_device_names": true
  },
  "security": {
    "validate_certificates": true,
    "encrypted_storage": true,
    "audit_logging": true
  }
}
```

## 🔧 Usage

### Web Interface
Access the FRITZWATCHER dashboard at:
```
http://localhost:5000/fritzwatcher
```

### API Endpoints
- `GET /api/fritzwatcher/routers` - List all routers
- `GET /api/fritzwatcher/devices` - Get all devices
- `GET /api/fritzwatcher/roaming` - Roaming events
- `POST /api/fritzwatcher/sync` - Trigger sync
- `GET /api/fritzwatcher/health` - Health check

### Device Customization
1. Access the web interface
2. Navigate to "Devices" tab
3. Click on any device to customize
4. Set custom name, icon, and color
5. Save changes

### Theme Selection
Choose from three themes:
- **Default**: Standard interface
- **Spicy**: High contrast, animated elements
- **Steady**: Minimal, low contrast

## 🧪 Testing

### Run Basic Tests
```bash
python test_fritzwatcher_integration.py
```

### Run Comprehensive Tests
```bash
python test_fritzwatcher_comprehensive.py
```

### Interactive KeePass Test
```bash
python test_keepass_selection.py
```

## 🛡️ Security

### Credential Management
- Credentials stored in KeePass database
- No hardcoded passwords or IP addresses
- Interactive database selection
- Secure password prompting

### Network Security
- SSL/TLS support for router connections
- Certificate validation
- Encrypted local storage
- Audit logging enabled

### Access Control
- Role-based access control
- Session management
- API key authentication
- Rate limiting

## 🔄 Resilience Features

### Retry Logic
- Configurable retry attempts
- Exponential backoff with jitter
- Router health monitoring
- Graceful failure handling

### Failover Support
- Automatic router failover
- Health-based router selection
- Load balancing
- Recovery detection

### Monitoring
- Real-time health checks
- Performance metrics
- Alert notifications
- Historical data retention

## 🎨 Customization

### Device Types
Automatically detects device types using OUI database:
- 📱 Smartphones (Apple, Samsung, etc.)
- 💻 Laptops and computers
- 📺 Smart TVs
- 🖨️ Printers
- 🎮 Gaming consoles
- 🏠 Smart home devices

### Custom Labels
- Personalized device names
- Custom icons and colors
- Priority settings
- Notes and descriptions

### Themes
- **Spicy Theme**: High contrast, animations, large fonts
- **Steady Theme**: Muted colors, minimal motion
- **Default Theme**: Standard interface

## 📊 Monitoring & Metrics

### Device Metrics
- Connection status
- Signal strength
- Data usage
- Connection duration
- Roaming events

### Router Metrics
- Health status
- Response time
- Active connections
- Guest network status
- Firmware version

### System Metrics
- Plugin performance
- Error rates
- Resource usage
- API response times

## 🔍 Troubleshooting

### Common Issues

**Can't connect to Fritz!Box**
- Check network connectivity
- Verify TR-064 is enabled
- Confirm credentials are correct
- Check firewall settings

**KeePass integration not working**
- Ensure KeePass database exists
- Check database password
- Verify pykeepass installation
- Try different access methods

**Device detection issues**
- Update OUI database
- Check device MAC addresses
- Verify network scanning
- Review device filters

### Debug Mode
Enable debug logging:
```json
{
  "logging": {
    "level": "DEBUG",
    "file_path": "fritzwatcher_debug.log"
  }
}
```

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies
3. Set up test environment
4. Run test suite
5. Create feature branch

### Testing
- Unit tests for all components
- Integration tests with mocked routers
- Security validation tests
- Performance benchmarks

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings
- Include error handling

## 📋 Changelog

### Version 1.0.0
- Initial release with comprehensive Fritz!Box integration
- Multi-router support and roaming detection
- Secure credential management via KeePass
- Interactive database selection
- Resilience framework with retry logic and failover
- UX customization with device auto-detection
- ADHD-friendly theme system
- Comprehensive test coverage

## 📞 Support

For support and documentation:
- **Documentation**: https://docs.heimnetz.local/plugins/fritzwatcher
- **Support**: https://support.heimnetz.local/plugins/fritzwatcher
- **Issues**: Create an issue in the plugin repository

## 📄 License

This plugin is part of the NoxPanel system and follows the project's licensing terms.

---

**FRITZWATCHER** - *Advanced Fritz!Box Monitoring Made Simple*
