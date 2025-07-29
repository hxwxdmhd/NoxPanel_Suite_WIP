# NoxSuite Installation Guide

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/hxwxdmhd/NoxPanel_Suite_WIP.git
cd NoxPanel_Suite_WIP
```

### 2. Install Dependencies
```bash
# Option 1: Minimal dependencies (recommended for testing)
pip install -r requirements-minimal.txt

# Option 2: Full dependencies (complete feature set)
pip install -r requirements.txt
```

### 3. Run Installation
```bash
# Interactive guided installation
python install.py

# Quick installation with defaults
python install.py fast

# Preview without making changes
python install.py dry-run

# Minimal safe installation
python install.py safe
```

### 4. Start Web Interface
```bash
# Start the NoxPanel web interface
python start_noxpanel.py
```

Visit http://localhost:5000 to access the web interface.

## Installation Modes

### Guided Mode (Default)
Interactive installation with prompts for configuration options.
```bash
python install.py guided
```

### Fast Mode
Quick installation using recommended defaults.
```bash
python install.py fast
```

### Dry Run Mode
Preview what would be installed without making changes.
```bash
python install.py dry-run
```

### Safe Mode
Minimal installation for maximum stability.
```bash
python install.py safe
```

### Recovery Mode
Recover from a failed installation.
```bash
python install.py recovery
```

### Audit & Heal Mode
Automatically detect and fix system issues.
```bash
python install.py audit-heal
```

## Validation

Run the validation script to ensure everything is working correctly:
```bash
python validate_installation.py
```

This will check:
- ✅ Python syntax validation
- ✅ Core module imports
- ✅ Security assessment
- ✅ Installer functionality
- ✅ Web application functionality

## Available Services

After installation, you'll have access to:

- **Web Interface**: http://localhost:5000
  - Dashboard and system overview
  - Knowledge management system
  - User authentication
  
- **API Endpoints**:
  - `GET /` - Main dashboard
  - `GET /knowledge` - Knowledge base
  - `GET /api/knowledge/stats` - Knowledge statistics
  - `GET /api/knowledge/search` - Search functionality
  - `GET /login` - Authentication

## Troubleshooting

### Common Issues

**1. Module Import Errors**
```bash
# Ensure you're in the project directory
cd NoxPanel_Suite_WIP

# Check Python path
python -c "import sys; print(sys.path)"
```

**2. Permission Errors**
```bash
# Make sure you have write permissions
ls -la

# If needed, adjust permissions
chmod +x install.py start_noxpanel.py
```

**3. Port Already in Use**
If port 5000 is busy, edit `start_noxpanel.py` and change the port:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

**4. Validation Failures**
Run the validation script to identify issues:
```bash
python validate_installation.py
```

### Getting Help

1. Check the validation output for specific error messages
2. Review the installer logs: `noxsuite_installer.log`
3. Check the web server logs in the console output

## Architecture

The NoxSuite is organized as follows:

```
NoxPanel_Suite_WIP/
├── install.py                    # Main installer entry point
├── start_noxpanel.py            # Web server launcher
├── validate_installation.py     # Validation script
├── requirements-minimal.txt     # Core dependencies
├── NoxPanel/                    # Core application
│   ├── noxcore/                # Core modules
│   │   ├── database.py         # Database layer
│   │   ├── repositories.py     # Data access layer
│   │   └── utils/              # Utility modules
│   └── tests/                  # Test suite
├── AI/NoxPanel/                # AI-enhanced components
│   └── test_server_optimized.py # Flask web application
└── archive/                    # Archived/deprecated code
```

## Security Features

- **Secure Password Hashing**: PBKDF2 with 100,000 iterations
- **No Hardcoded Secrets**: All passwords generated securely
- **Input Validation**: Comprehensive security checks
- **Secure Session Management**: Flask secure sessions

## Development

To contribute or develop:

1. Run the validation suite: `python validate_installation.py`
2. Start the dev server: `python start_noxpanel.py`
3. Make changes and revalidate
4. Test the installer: `python install.py dry-run`

## Production Deployment

For production deployment, consider:

1. Use a proper WSGI server (gunicorn, uWSGI)
2. Set up reverse proxy (nginx)
3. Configure SSL/TLS certificates
4. Use environment variables for configuration
5. Set up proper logging and monitoring

Example production startup:
```bash
# Install production dependencies
pip install gunicorn

# Start with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 AI.NoxPanel.test_server_optimized:app
```