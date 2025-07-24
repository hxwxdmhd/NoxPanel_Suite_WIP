# 🌌 NoxPanel — Your Local AI Command Center

**Empowering your local scripts with a visual dashboard.**
**Crafted for control. Designed for clarity. Fueled by Python.**

---

## 🔰 What is NoxPanel?

NoxPanel is a modular, locally hosted AI command center that unifies your Python scripts and tools under one stunning web dashboard.
It runs directly on your machine or server and offers:

- 🔧 Script execution via Flask API
- 🎛️ A minimalist dashboard for your tools
- 🔐 Local intranet access via custom IP/domain
- 💡 React frontend support (optional)
- 🧠 Smart structure for logs, exports, profiles, and themes
- ✨ Dark/light themes ready to roll

**Slogan Ideas** (pick one or use all):
- *"Where Python meets purpose."*
- *"Local tools. Unified."*
- *"Run your code. Rule your kingdom."*

---

## 🖼️ Logo Concept (ASCII Draft)

```
███╗   ██╗ ██████╗ ██╗  ██╗██████╗  █████╗ ███╗   ██╗███████╗██╗
████╗  ██║██╔═══██╗╚██╗██╔╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██║
██╔██╗ ██║██║   ██║ ╚███╔╝ ██████╔╝███████║██╔██╗ ██║█████╗  ██║
██║╚██╗██║██║   ██║ ██╔██╗ ██╔═══╝ ██╔══██║██║╚██╗██║██╔══╝  ██║
██║ ╚████║╚██████╔╝██╔╝ ██╗██║     ██║  ██║██║ ╚████║███████╗███████╗
╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
```

---

## 🌍 Local IP & Access Info

> Your system uses a custom internal subnet for trusted services.

| Service      | IP            | Domain Alias        | Port |
|--------------|---------------|---------------------|------|
| NoxPanel     | `10.1.0.88`   | `noxpanel.local`     | 5000 |
| Proxmox Node | `10.1.0.2`    | `proxmox.local`      | 8006 |
| NAS / SMB    | `10.1.0.50`   | `nas.local`          | 445  |
| Ollama Host  | `10.1.0.99`   | `ollama.local`       | 11434 |
| LLM Scripts  | `10.1.0.77`   | `llmtools.local`     | various |

**To use `.local` domains:**
Edit your system's `hosts` file:

- On Windows: `C:\Windows\System32\drivers\etc\hosts`
- On Linux/macOS: `/etc/hosts`

Add:
```
127.0.0.1 noxpanel.local
```

Or use your machine's LAN IP instead.

---

## 🧪 Getting Started

Clone and bootstrap the project:

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

**First Time Setup:**
1. Open your browser to `http://localhost:5000`
2. Navigate to `/admin/login`
3. Login with default credentials: `admin / admin123`
4. Create additional users and configure permissions
5. Start scheduling jobs and installing plugins

Access your dashboard:
```
http://localhost:5000
http://noxpanel.local:5000
```

**Available Endpoints:**
- `/` - Main dashboard
- `/admin/` - User management and system administration
- `/scheduler/` - Job scheduling and monitoring
- `/plugins/` - Plugin management
- `/ai-monitor/` - AI model monitoring
- `/models/` - AI model API
- `/chatbot/` - Interactive AI chat interface

---

## 🗃️ File Structure

```
NoxPanel/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── scripts/
│   └── example_script.py
├── noxcore/
│   ├── runner.py
│   ├── auth.py
│   ├── ai_monitor.py
│   └── model_detector.py
├── webpanel/
│   ├── app.py
│   ├── admin_blueprint.py
│   ├── job_scheduler.py
│   ├── plugin_loader.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── admin/
│   │   ├── scheduler/
│   │   ├── plugins/
│   │   └── dashboard.html
│   ├── static/
│   │   └── style.css
│   └── frontend/ (optional React app)
├── config/
│   └── system.json
├── data/
│   ├── db/
│   │   └── noxpanel.db
│   ├── logs/
│   ├── profiles/
│   └── chatgpt_exports/
├── themes/
│   ├── dark/
│   └── light/
└── plugins/
    └── sample-plugin/
```

---

## 🎯 Current Status - Phase 1 Complete ✅

**NoxPanel v2.0.0-dev** has successfully completed **Phase 1: Critical Integration** with 100% of objectives achieved:

### ✅ **Completed Features**
- **🗄️ Database Integration**: SQLite database with auto-initialization and full Flask integration
- **🌐 Web Interface**: Modern, responsive dashboard with ADHD-friendly design principles
- **📡 Network Scanning**: Automated device discovery with web interface integration
- **🔐 Authentication**: JWT-based security system with development bypass
- **📊 Real-time Updates**: Live device status display with automatic refresh
- **⚙️ Environment Config**: Production-ready configuration management
- **🧪 Testing Framework**: Comprehensive bootstrap validation and integration testing
- **📚 Documentation**: Complete with audit compliance and ADHD accommodations

### 🚀 **Ready for Phase 2: Enhanced Integration**

Phase 2 will add:
- **Real-time WebSocket updates** for live status without page refresh
- **Complete user management system** with registration and role-based access
- **Background task processing** for non-blocking operations
- **Plugin architecture foundation** for extensible functionality
- **Enhanced monitoring** with real-time system metrics

---

## ✨ Current Features

### 🔐 **Admin Panel & User Management**
- Role-based access control (Admin, Moderator, User, Viewer)
- User registration and authentication
- Module-level permission assignment
- Session management with security tracking
- Default admin login: `admin / admin123`

### ⏰ **Job Scheduler**
- APScheduler integration with interval and cron scheduling
- Real-time job monitoring and execution history
- Script timeout handling and error capture
- Background task execution with proper logging
- Job statistics and success/failure tracking

### 🔌 **Plugin System**
- Dynamic plugin discovery and loading
- Plugin lifecycle management (enable/disable)
- Metadata-driven plugin configuration
- Hot-reload capabilities without restart

### 🤖 **AI Model Monitoring**
- Auto-detection of Ollama, LM Studio, LocalAI, Oobabooga
- Health checking with response time monitoring
- Self-healing capabilities with automatic restart attempts
- Real-time status updates and alerting

### 🎨 **Modern Interface**
- Responsive Bootstrap 5 design
- Dark/light theme switching with persistence
- Mobile-friendly navigation and layouts
- Font Awesome icon integration
- Real-time updates and notifications

---

## 🧱 Tech Stack

- **Python 3.x**
- **Flask** with Blueprint architecture
- **SQLite** for user management and job scheduling
- **APScheduler** for automated task execution
- **Bootstrap 5** responsive UI framework
- **Font Awesome** icons
- **dotenv** for environment configuration
- **Optional:** React + REST frontend (via create-react-app)

---

## 💡 Roadmap Highlights

- ✅ CLI installer and environment bootstrap
- ✅ Dynamic script discovery
- ✅ Authentication / Login system
- ✅ Plugin loader
- ✅ Job Scheduler with APScheduler
- ✅ Admin Panel with user management
- ✅ AI Model monitoring and auto-healing
- ✅ Mobile-friendly responsive dashboard
- ✅ Dark/light theme system
- 🔜 Live terminal stream
- 🔜 Smart script tags & categories
- 🔜 Assistant modes (ChatGPT-like interactions)
- 🔜 Pi Node management
- 🔜 Certificate & Reverse Proxy UI
- 🔜 VM Manager integration
- 🔜 Notification system

---

## 🧪 Testing

### Bootstrap Validation
```bash
# Run comprehensive system validation
python scripts/bootstrap.py

# Check project status
python scripts/bootstrap.py --quiet
```

### Integration Testing
```bash
# Test database integration
python test_integration.py

# Validate API endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/devices

# Test network scanning
curl -X POST http://localhost:5000/api/devices/scan
```
