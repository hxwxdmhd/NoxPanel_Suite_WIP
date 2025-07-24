# 🛠️ Developer Guide

Welcome to Heimnetz development! This guide covers everything you need to contribute to the project.

## 🚀 Getting Started

### **Development Environment Setup**

1. **Clone the Repository**
   ```powershell
   git clone https://github.com/HobeLab-Projects/Heimnetz.git
   cd Heimnetz
   ```

2. **Create Virtual Environment**
   ```powershell
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Run Tests**
   ```powershell
   python -m pytest tests/ -v
   ```

### **Development Workflow**

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow ADHD-friendly design principles
   - Write clear, self-documenting code
   - Add tests for new functionality

3. **Test Your Changes**
   ```powershell
   python -m pytest tests/
   python main.py --test
   ```

4. **Submit Pull Request**
   - Use our PR template
   - Include ADHD impact assessment
   - Provide clear description and examples

## 🏗️ Architecture Overview

### **Project Structure**

```
Heimnetz/
├── 🏗️ main.py                     # Main entry point
├── 🌐 integrated_web_server.py    # Web dashboard server
├── 🤖 nox_assistant/              # AI Assistant module
│   ├── assistant.py               # Core assistant logic
│   ├── voice_interface.py         # Voice recognition & TTS
│   ├── llm_wrapper.py            # Local AI model interface
│   └── task_registry.yaml        # Command definitions
├── 🔗 api_bridge.py              # Frontend-backend connector
├── ⚙️ config/                    # Configuration files
├── 🧪 tests/                     # Test suite
├── 📚 docs/                      # Documentation
└── 🐳 docker/                    # Container configs
```

### **Core Components**

#### **Main Entry Point** (`main.py`)
- Unified launcher for all functionality
- Command-line interface with ADHD-friendly menus
- Handles application startup and coordination

#### **Web Server** (`integrated_web_server.py`)
- Flask-based web application
- ADHD-friendly web dashboard
- REST API endpoints for frontend

#### **AI Assistant** (`nox_assistant/`)
- **`assistant.py`**: Core AI logic and command processing
- **`voice_interface.py`**: Speech recognition and text-to-speech
- **`llm_wrapper.py`**: Interface to local AI models (Ollama)
- **`task_registry.yaml`**: Configuration for available commands

#### **API Bridge** (`api_bridge.py`)
- Connects frontend JavaScript to backend Python
- Handles real-time data updates
- WebSocket support for live updates

## 🧠 ADHD-Friendly Development

### **Design Principles**

1. **Visual Hierarchy**
   ```css
   /* Clear heading structure */
   h1 { font-size: 2.5em; color: #2c3e50; }
   h2 { font-size: 2em; color: #34495e; }
   h3 { font-size: 1.5em; color: #7f8c8d; }
   ```

2. **Reduced Cognitive Load**
   ```python
   # Good: Clear, single-purpose function
   def get_device_status(device_id):
       """Get the current status of a specific device."""
       return network_scanner.check_device(device_id)
   
   # Avoid: Complex functions doing multiple things
   ```

3. **Consistent Patterns**
   ```python
   # Use consistent naming and structure
   def scan_network():
       """Scan network for devices."""
       pass
   
   def scan_security():
       """Scan for security vulnerabilities."""
       pass
   ```

### **Code Style Guidelines**

#### **Python Code**
```python
# Use clear, descriptive names
def start_network_monitoring():
    """Start continuous network monitoring."""
    pass

# Add helpful comments for complex logic
def calculate_network_health():
    """Calculate overall network health score.
    
    Uses multiple metrics:
    - Device response times
    - Connection stability
    - Bandwidth utilization
    """
    pass

# Use type hints for clarity
def process_device_data(device: Dict[str, Any]) -> DeviceStatus:
    """Process raw device data into status object."""
    pass
```

#### **JavaScript/Frontend**
```javascript
// Use clear, descriptive function names
function updateDeviceStatus(deviceId, status) {
    // Update UI with new device status
}

// Group related functionality
const NetworkMonitor = {
    startScanning() {
        // Start network scanning
    },
    
    updateDisplay() {
        // Update dashboard display
    }
};
```

#### **CSS/Styling**
```css
/* Use ADHD-friendly color schemes */
:root {
    --success-color: #27ae60;  /* Clear green */
    --warning-color: #f39c12;  /* Clear orange */
    --error-color: #e74c3c;    /* Clear red */
    --info-color: #3498db;     /* Clear blue */
}

/* Ensure good contrast ratios */
.status-card {
    background: #ffffff;
    border: 2px solid var(--border-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

## 🤖 AI Integration

### **Adding New AI Models**

1. **Update LLM Wrapper**
   ```python
   # In nox_assistant/llm_wrapper.py
   SUPPORTED_MODELS = {
       'your-model': {
           'name': 'Your Model Name',
           'description': 'Model description',
           'endpoint': 'http://localhost:11434/api/generate',
           'context_length': 4096
       }
   }
   ```

2. **Add Model-Specific Prompts**
   ```python
   def get_model_prompt(model_name: str, task_type: str) -> str:
       """Get optimized prompt for specific model and task."""
       prompts = {
           'your-model': {
               'network_analysis': 'Analyze this network data...'
           }
       }
       return prompts.get(model_name, {}).get(task_type, '')
   ```

### **Creating New Assistant Tasks**

1. **Add to Task Registry**
   ```yaml
   # In nox_assistant/task_registry.yaml
   your_task:
     commands: ["task", "your-task", "do-something"]
     description: "Description of what this task does"
     module: "your_module"
     examples:
       - "Perform your task"
       - "Execute custom operation"
   ```

2. **Implement Task Module**
   ```python
   # Create nox_assistant/modules/your_module.py
   async def execute_task(command: str, context: dict) -> dict:
       """Execute your custom task."""
       result = {
           'success': True,
           'message': 'Task completed successfully',
           'data': {}
       }
       return result
   ```

## 🌐 Web Development

### **Frontend Architecture**

The web interface uses:
- **HTML5**: Semantic markup for accessibility
- **CSS3**: Modern styling with CSS custom properties
- **Vanilla JavaScript**: No heavy frameworks for better performance
- **Chart.js**: For data visualization
- **WebSockets**: For real-time updates

### **Adding New Dashboard Components**

1. **Create HTML Structure**
   ```html
   <!-- In templates/ -->
   <div class="dashboard-card" id="your-component">
       <h3 class="card-title">
           <i class="icon-your-icon"></i>
           Your Component
       </h3>
       <div class="card-content">
           <!-- Component content -->
       </div>
   </div>
   ```

2. **Add JavaScript Logic**
   ```javascript
   // In static/js/
   class YourComponent {
       constructor(containerId) {
           this.container = document.getElementById(containerId);
           this.init();
       }
       
       init() {
           // Initialize component
       }
       
       update(data) {
           // Update component with new data
       }
   }
   ```

3. **Style with CSS**
   ```css
   /* In static/css/ */
   .your-component {
       /* ADHD-friendly styling */
       background: var(--card-background);
       border-radius: 8px;
       padding: 1rem;
       margin-bottom: 1rem;
   }
   ```

### **API Endpoint Development**

1. **Create Flask Route**
   ```python
   # In integrated_web_server.py
   @app.route('/api/your-endpoint', methods=['GET', 'POST'])
   def your_endpoint():
       """Your API endpoint description."""
       try:
           # Process request
           result = process_your_request()
           return jsonify({
               'success': True,
               'data': result
           })
       except Exception as e:
           return jsonify({
               'success': False,
               'error': str(e)
           }), 500
   ```

2. **Add Frontend Integration**
   ```javascript
   // Call API from frontend
   async function callYourEndpoint() {
       try {
           const response = await fetch('/api/your-endpoint');
           const data = await response.json();
           
           if (data.success) {
               updateUI(data.data);
           } else {
               showError(data.error);
           }
       } catch (error) {
           showError('Network error: ' + error.message);
       }
   }
   ```

## 🧪 Testing

### **Running Tests**

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_assistant.py -v
python -m pytest tests/test_web.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### **Writing Tests**

#### **Unit Tests**
```python
# tests/test_your_feature.py
import pytest
from your_module import YourClass

class TestYourClass:
    def test_basic_functionality(self):
        """Test basic functionality works."""
        instance = YourClass()
        result = instance.your_method()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling works correctly."""
        instance = YourClass()
        with pytest.raises(ValueError):
            instance.your_method(invalid_input)
```

#### **Integration Tests**
```python
# tests/test_integration.py
def test_api_endpoint():
    """Test API endpoint integration."""
    client = app.test_client()
    response = client.get('/api/your-endpoint')
    
    assert response.status_code == 200
    assert response.json['success'] is True
```

#### **ADHD-Friendly Testing**
```python
def test_cognitive_load():
    """Test that interface doesn't overwhelm users."""
    page = get_dashboard_page()
    
    # Check that page has clear visual hierarchy
    assert len(page.find_all('h1')) == 1  # Single main heading
    assert len(page.find_all('h2')) <= 5  # Limited section headings
    
    # Check for ADHD-friendly features
    assert page.find(class_='status-indicators')  # Visual status cues
    assert page.find(class_='clear-navigation')   # Simple navigation
```

## 🔒 Security Considerations

### **Security Best Practices**

1. **Input Validation**
   ```python
   def validate_device_id(device_id: str) -> bool:
       """Validate device ID format."""
       if not device_id or len(device_id) > 50:
           return False
       return device_id.isalnum()
   ```

2. **Authentication**
   ```python
   from functools import wraps
   
   def require_auth(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           if not current_user.is_authenticated:
               abort(401)
           return f(*args, **kwargs)
       return decorated_function
   ```

3. **Data Sanitization**
   ```python
   import html
   
   def sanitize_user_input(user_input: str) -> str:
       """Sanitize user input for safe display."""
       return html.escape(user_input.strip())
   ```

## 🐳 Docker Development

### **Building Images**

```powershell
# Build development image
docker build -t heimnetz:dev .

# Build with specific tag
docker build -t heimnetz:v7.0.0 .
```

### **Development with Docker Compose**

```powershell
# Start development environment
docker-compose -f docker-compose.dev.yml up

# View logs
docker-compose -f docker-compose.dev.yml logs -f heimnetz

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

## 📝 Documentation

### **Writing Documentation**

1. **Follow ADHD-Friendly Principles**
   - Use clear headings and structure
   - Include visual examples
   - Break complex topics into smaller sections
   - Provide practical examples

2. **Documentation Standards**
   ```markdown
   # Clear Title
   
   Brief description of what this document covers.
   
   ## 🎯 Quick Start
   
   Essential information for getting started quickly.
   
   ## 📋 Detailed Information
   
   More comprehensive information organized logically.
   
   ## 💡 Examples
   
   Practical examples showing how to use features.
   
   ## 🆘 Troubleshooting
   
   Common issues and solutions.
   ```

### **Code Documentation**

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """Detailed function description.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Dictionary containing:
        - 'success': Boolean indicating success
        - 'data': The processed data
        - 'message': Human-readable status message
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['message'])
        "Processing completed successfully"
    """
    pass
```

## 🚀 Deployment

### **Preparing for Release**

1. **Update Version Numbers**
   ```python
   # In main.py or __init__.py
   __version__ = "7.1.0"
   ```

2. **Update Documentation**
   - Update README.md with new features
   - Update CHANGELOG.md with changes
   - Verify all links work

3. **Run Full Test Suite**
   ```powershell
   python -m pytest tests/ --cov=. --cov-report=html
   python -m pytest tests/integration/ -v
   ```

4. **Build and Test Docker Images**
   ```powershell
   docker build -t heimnetz:latest .
   docker run --rm heimnetz:latest python main.py --test
   ```

### **Creating Releases**

1. **Tag Release**
   ```bash
   git tag -a v7.1.0 -m "Release version 7.1.0"
   git push origin v7.1.0
   ```

2. **GitHub Release**
   - Use GitHub web interface or CLI
   - Include release notes from CHANGELOG.md
   - Attach built artifacts if needed

## 🤝 Contributing Guidelines

### **Before Contributing**

1. **Read Documentation**
   - Review this developer guide
   - Read CONTRIBUTING.md
   - Understand ADHD-friendly design principles

2. **Set Up Development Environment**
   - Follow setup instructions above
   - Run tests to verify everything works
   - Try the application to understand user experience

### **Making Contributions**

1. **Choose an Issue**
   - Look for "good first issue" labels
   - Check ADHD-specific issues
   - Ask questions if anything is unclear

2. **Development Process**
   - Create feature branch
   - Make small, focused commits
   - Write tests for new functionality
   - Update documentation as needed

3. **Pull Request Process**
   - Use PR template
   - Include ADHD impact assessment
   - Provide clear examples
   - Respond to feedback promptly

### **Types of Contributions**

- **🐛 Bug Fixes**: Fix existing functionality
- **✨ New Features**: Add new capabilities
- **🎨 UI/UX Improvements**: Enhance ADHD-friendliness
- **📚 Documentation**: Improve guides and examples
- **🧪 Testing**: Add test coverage
- **🔒 Security**: Improve security measures
- **♿ Accessibility**: Enhance accessibility features

## 🆘 Getting Help

### **Development Support**

- **Discord Community**: Join our developer channels
- **GitHub Discussions**: Ask technical questions
- **Code Review**: Request feedback on your changes
- **Pair Programming**: Find a development partner

### **Resources**

- **ADHD Design Resources**: Links to accessibility guidelines
- **Python Best Practices**: Coding standards and patterns
- **Flask Documentation**: Web development resources
- **AI/ML Resources**: Machine learning and AI development

---

**Thank you for contributing to Heimnetz! Together, we're building technology that's truly accessible for everyone.** 💙

**Next Steps:**
- 🎨 [ADHD Design Principles](accessibility.md)
- 🤖 [AI Integration Guide](ai-integration.md)
- 🔒 [Security Documentation](security.md)
