# 📖 User Guide

Welcome to Heimnetz! This guide will help you get started with your ADHD-friendly network management suite.

## 🎯 Quick Start

### **First Time Setup**

1. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Start the Web Dashboard**
   ```powershell
   python main.py --web
   ```

3. **Access Your Dashboard**
   Open your browser to: `http://localhost:5000`

### **Basic Navigation**

The Heimnetz interface is designed with ADHD-friendly principles:

- **Clear Visual Hierarchy**: Important information is prominently displayed
- **Color-Coded Status**: Green = Good, Yellow = Warning, Red = Issues
- **Reduced Cognitive Load**: Only essential information on each screen

## 🌐 Web Dashboard

### **Dashboard Overview**

The main dashboard shows:
- **Device Status**: Live network device monitoring
- **Network Health**: Overall network performance
- **AI Insights**: Intelligent recommendations
- **Quick Actions**: Common tasks at your fingertips

### **Device Management**

- **Auto-Discovery**: Heimnetz automatically finds devices on your network
- **Status Monitoring**: Real-time online/offline status
- **Device Details**: Click any device for detailed information
- **Custom Names**: Give your devices friendly names

### **Network Analysis**

- **Bandwidth Usage**: See which devices use the most data
- **Connection Quality**: Monitor signal strength and connection stability
- **Historical Data**: View network trends over time

## 🤖 AI Assistant

### **Using NoxAssistant**

The AI assistant helps with network management tasks:

#### **Text Commands**
```powershell
# System diagnostics
python main.py --assistant "Run full system diagnostic"

# Network scanning
python main.py --assistant "Scan network and show device status"

# Security checks
python main.py --assistant "Check for security vulnerabilities"
```

#### **Voice Commands** (Optional)
```powershell
# Enable voice interface
python main.py --voice

# Example voice commands:
"Hey Nox, what's my network status?"
"Run a security scan"
"Show me bandwidth usage"
```

### **AI Capabilities**

- **Intelligent Analysis**: Pattern recognition and anomaly detection
- **Security Monitoring**: Automated threat detection
- **Performance Optimization**: AI-driven recommendations
- **Natural Language**: Understand plain English commands

## 🔧 Common Tasks

### **Adding New Devices**

1. Connect device to your network
2. Open Heimnetz dashboard
3. Click "Scan for New Devices"
4. New devices appear automatically

### **Setting Up Monitoring**

1. Go to "Monitoring" section
2. Choose devices to monitor
3. Set monitoring intervals
4. Configure alerts (optional)

### **Running Diagnostics**

1. Click "Diagnostics" in main menu
2. Select diagnostic type:
   - Quick Health Check
   - Full Network Scan
   - Security Analysis
3. Review results and recommendations

### **Customizing Your Dashboard**

1. Click "Settings" gear icon
2. Choose your preferences:
   - Dark/Light theme
   - Update frequency
   - Display options
3. Click "Save Changes"

## 🎨 ADHD-Friendly Features

### **Visual Design**

- **High Contrast**: Clear text and visual elements
- **Consistent Colors**: Same colors mean the same things
- **Organized Layout**: Logical grouping of related information
- **Minimal Distractions**: Clean, focused interface

### **Cognitive Load Reduction**

- **Progressive Disclosure**: Advanced features hidden until needed
- **Clear Labels**: Everything clearly labeled and explained
- **Visual Cues**: Icons and colors provide instant understanding
- **Logical Flow**: Tasks follow natural mental models

### **Accessibility Features**

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Friendly**: Works with assistive technology
- **Adjustable Text Size**: Customize for your needs
- **Focus Indicators**: Clear visual focus for navigation

## 🔒 Security & Privacy

### **Data Protection**

- **Local Processing**: AI models run locally, no data sent to cloud
- **Encrypted Storage**: Sensitive data is encrypted
- **Secure Connections**: HTTPS for web interface
- **Privacy First**: Your network data stays on your network

### **Security Features**

- **Threat Detection**: Automatic scanning for security issues
- **Vulnerability Alerts**: Notifications about potential problems
- **Access Control**: Secure login and user management
- **Audit Logs**: Track all system access and changes

## 🆘 Troubleshooting

### **Common Issues**

#### **Dashboard Won't Load**
- Check if web server is running: `python main.py --status`
- Restart web server: `python main.py --web`
- Check firewall settings

#### **Devices Not Found**
- Ensure devices are on same network
- Run manual scan: Click "Scan for Devices"
- Check network permissions

#### **AI Assistant Not Responding**
- Verify Ollama is installed and running
- Check AI model availability: `python main.py --assistant "list models"`
- Restart AI service

#### **Voice Interface Issues**
- Check microphone permissions
- Verify speech recognition library installed
- Test with text commands first

### **Getting Help**

1. **Built-in Help**: Click "?" icon anywhere in the interface
2. **AI Assistant**: Ask "Help with [your issue]"
3. **Documentation**: Check the docs/ folder for detailed guides
4. **Community**: Join our Discord community for support

## 🚀 Advanced Features

### **Automation**

- **Scheduled Scans**: Automatic network monitoring
- **Smart Alerts**: AI-powered notification system
- **Custom Scripts**: Extend functionality with your own code
- **Integration**: Connect with other home automation systems

### **Performance Monitoring**

- **Real-time Metrics**: Live network performance data
- **Historical Analysis**: Track network health over time
- **Predictive Insights**: AI predictions for potential issues
- **Optimization Suggestions**: Automated recommendations

### **Customization**

- **Themes**: Multiple visual themes available
- **Layouts**: Customize dashboard layout
- **Widgets**: Add/remove dashboard components
- **Plugins**: Extend functionality with community plugins

## 📊 Understanding Your Data

### **Network Metrics**

- **Bandwidth**: How much data is being transferred
- **Latency**: How fast your network responds
- **Packet Loss**: Missing or delayed data
- **Connection Quality**: Overall network health score

### **Device Information**

- **IP Address**: Network location of device
- **MAC Address**: Unique device identifier
- **Manufacturer**: Who made the device
- **Last Seen**: When device was last active

### **Security Indicators**

- **Open Ports**: Network services running on devices
- **Security Score**: Overall device security rating
- **Vulnerabilities**: Known security issues
- **Recommendations**: How to improve security

## 💡 Tips for ADHD Users

### **Staying Organized**

- **Use Clear Names**: Give devices meaningful names
- **Set Reminders**: Use built-in alert system
- **Regular Reviews**: Weekly network health checks
- **Document Changes**: Keep notes about network modifications

### **Reducing Overwhelm**

- **Start Simple**: Begin with basic monitoring
- **One Task at a Time**: Focus on single objectives
- **Use AI Help**: Let the assistant guide you
- **Take Breaks**: Complex network tasks can wait

### **Building Habits**

- **Daily Checks**: Quick dashboard review each morning
- **Weekly Scans**: Regular security and health checks
- **Monthly Reviews**: Analyze network trends and usage
- **Quarterly Updates**: Keep software and configurations current

---

**Need more help? Check our other documentation:**
- 🛠️ [Developer Guide](developer-guide.md) - For technical users
- 🤖 [AI Integration Guide](ai-integration.md) - Advanced AI features
- 🔒 [Security Guide](security.md) - Detailed security information
- 🚀 [Deployment Guide](deployment.md) - Installation and setup

**Remember: Heimnetz is designed to make network management easier, not harder. If something feels overwhelming, use the AI assistant or reach out for help!** 💙
