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

Open your browser:
```
http://localhost:5000
http://noxpanel.local:5000
```

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
│   └── runner.py
├── webpanel/
│   ├── app.py
│   ├── templates/
│   │   └── dashboard.html
│   ├── static/
│   │   └── style.css
│   └── frontend/ (optional React app)
├── data/
│   ├── logs/
│   ├── profiles/
│   └── chatgpt_exports/
└── themes/
    ├── dark/
    └── light/
```

---

## 🧠 Use Case Examples

- 🔍 Run diagnostic scripts (`ping_test.py`, `firewall_check.py`)
- 💾 Sync your backups (`backup_runner.py`)
- 🧠 Trigger LLM workflows locally (`ollama_chat.py`, `embedding_tool.py`)
- 🌐 Manage Proxmox, SMB, and LAN setups visually

---

## 🧱 Tech Stack

- **Python 3.x**
- **Flask**
- **dotenv**
- **Optional:** React + REST frontend (via create-react-app)

---

## 💡 Roadmap Highlights

- ✅ CLI installer and environment bootstrap
- ✅ Dynamic script discovery
- 🔜 Authentication / Login system
- 🔜 Plugin loader
- 🔜 Live terminal stream
- 🔜 Mobile-friendly dashboard
- 🔜 Smart script tags & categories
- 🔜 Notification system
\n\n![Version](https://img.shields.io/badge/version-4.1.0-blue.svg)
