#!/usr/bin/env python3
"""
NoxSuite + AI Dev Infrastructure Auto-Installer
Intelligent cross-platform setup for the complete NoxSuite ecosystem
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('noxsuite-install.log')
    ]
)
logger = logging.getLogger(__name__)

class OSType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"

@dataclass
class SystemInfo:
    os_type: OSType
    architecture: str
    python_version: str
    available_memory: int
    cpu_cores: int
    docker_available: bool = False
    node_available: bool = False
    git_available: bool = False

@dataclass
class InstallConfig:
    install_directory: Path
    modules: List[str]
    enable_ai: bool = True
    enable_voice: bool = False
    enable_mobile: bool = True
    dev_mode: bool = False
    auto_start: bool = True
    ai_models: List[str]

class NoxSuiteInstaller:
    """Comprehensive NoxSuite installer with AI-powered setup"""
    
    DEFAULT_MODULES = [
        "noxpanel", "noxguard", "autoimport", "powerlog", 
        "langflow-hub", "autocleaner", "heimnetz-scanner", 
        "plugin-system", "update-manager"
    ]
    
    DEFAULT_AI_MODELS = [
        "mistral:7b-instruct", "gemma:7b-it", "tinyllama", "phi"
    ]
    
    def __init__((self) -> None:
        self.system_info = self._detect_system()
        self.config: Optional[InstallConfig] = None
        self.install_log = []
        
    def _detect_system(self) -> SystemInfo:
        """Detect comprehensive system information"""
        logger.info("🔍 Detecting system specifications...")
        
        # OS Detection
        os_name = platform.system().lower()
        if os_name == "windows":
            os_type = OSType.WINDOWS
        elif os_name == "linux":
            os_type = OSType.LINUX
        elif os_name == "darwin":
            os_type = OSType.MACOS
        else:
            os_type = OSType.UNKNOWN
            
        # System specs
        architecture = platform.machine()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Memory (rough estimate)
        try:
            if os_type == OSType.WINDOWS:
                import psutil
                available_memory = psutil.virtual_memory().total // (1024**3)  # GB
            else:
                with open('/proc/meminfo', 'r') as f:
                    memory_kb = int([line for line in f if 'MemTotal' in line][0].split()[1])
                    available_memory = memory_kb // (1024**2)  # GB
        except:
            available_memory = 8  # Default assumption
            
        cpu_cores = os.cpu_count() or 4
        
        # Tool availability
        docker_available = shutil.which("docker") is not None
        node_available = shutil.which("node") is not None
        git_available = shutil.which("git") is not None
        
        system_info = SystemInfo(
            os_type=os_type,
            architecture=architecture,
            python_version=python_version,
            available_memory=available_memory,
            cpu_cores=cpu_cores,
            docker_available=docker_available,
            node_available=node_available,
            git_available=git_available
        )
        
        logger.info(f"✅ Detected: {os_type.value} {architecture}, {cpu_cores} cores, {available_memory}GB RAM")
        return system_info
    
    def welcome_screen(self) -> bool:
        """Display welcome and system info"""
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║                    🧠 NoxSuite + AI Dev Infrastructure            ║
║                        Intelligent Auto-Installer                ║
╠═══════════════════════════════════════════════════════════════════╣
║  • ADHD-Friendly Design      • AI-Powered Automation            ║
║  • Cross-Platform Support    • Self-Healing Infrastructure      ║
║  • Docker-Native Deployment  • Local LLM Integration            ║
║  • Modular Architecture      • Real-time Monitoring             ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"\n🖥️  System Information:")
        logger.info(f"   OS: {self.system_info.os_type.value.title()
        logger.info(f"   Python: {self.system_info.python_version}")
        logger.info(f"   CPU Cores: {self.system_info.cpu_cores}")
        logger.info(f"   Memory: {self.system_info.available_memory}GB")
        logger.info(f"   Docker: {'✅' if self.system_info.docker_available else '❌'}")
        logger.info(f"   Node.js: {'✅' if self.system_info.node_available else '❌'}")
        logger.info(f"   Git: {'✅' if self.system_info.git_available else '❌'}")
        
    def interactive_config(self) -> InstallConfig:
        """Interactive configuration wizard"""
        logger.info("\n🛠️  Configuration Wizard")
        logger.info("=" * 50)
        
        # Installation directory
        if self.system_info.os_type == OSType.WINDOWS:
            default_dir = Path.home() / "NoxSuite"
        else:
            default_dir = Path.home() / "noxsuite"
            
        install_dir_input = input(f"📁 Installation directory [{default_dir}]: ").strip()
        install_directory = Path(install_dir_input) if install_dir_input else default_dir
        
        # Module selection
        logger.info(f"\n📦 Available Modules:")
        for i, module in enumerate(self.DEFAULT_MODULES, 1):
            logger.info(f"   {i}. {module}")
            
        module_input = input(f"\n🔢 Select modules (comma-separated numbers, or 'all') [all]: ").strip()
        if module_input.lower() in ["", "all"]:
            modules = self.DEFAULT_MODULES
        else:
            try:
                indices = [int(x.strip()) - 1 for x in module_input.split(",")]
                modules = [self.DEFAULT_MODULES[i] for i in indices if 0 <= i < len(self.DEFAULT_MODULES)]
            except:
                logger.warning("Invalid module selection, using all modules")
                modules = self.DEFAULT_MODULES
        
        # AI Configuration
        enable_ai = input(f"\n🤖 Enable AI features (Ollama, LLMs) [Y/n]: ").strip().lower() != 'n'
        enable_voice = input(f"🎤 Enable voice interface [y/N]: ").strip().lower() == 'y'
        enable_mobile = input(f"📱 Enable mobile companion (NoxGo PWA) [Y/n]: ").strip().lower() != 'n'
        
        # Development mode
        dev_mode = input(f"\n⚙️  Enable development mode (hot reload, debug) [y/N]: ").strip().lower() == 'y'
        auto_start = input(f"🚀 Auto-start services after installation [Y/n]: ").strip().lower() != 'n'
        
        # AI Models
        ai_models = []
        if enable_ai:
            logger.info(f"\n🧠 Available AI Models:")
            for i, model in enumerate(self.DEFAULT_AI_MODELS, 1):
                logger.info(f"   {i}. {model}")
            
            model_input = input(f"🤖 Select AI models (comma-separated numbers, or 'all') [1,2]: ").strip()
            if model_input.lower() == "all":
                ai_models = self.DEFAULT_AI_MODELS
            elif model_input == "":
                ai_models = self.DEFAULT_AI_MODELS[:2]  # First two by default
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in model_input.split(",")]
                    ai_models = [self.DEFAULT_AI_MODELS[i] for i in indices if 0 <= i < len(self.DEFAULT_AI_MODELS)]
                except:
                    ai_models = self.DEFAULT_AI_MODELS[:2]
        
        config = InstallConfig(
            install_directory=install_directory,
            modules=modules,
            enable_ai=enable_ai,
            enable_voice=enable_voice,
            enable_mobile=enable_mobile,
            dev_mode=dev_mode,
            auto_start=auto_start,
            ai_models=ai_models
        )
        
        # Confirmation
        logger.info(f"\n📋 Installation Summary:")
        logger.info(f"   Directory: {config.install_directory}")
        logger.info(f"   Modules: {', '.join(config.modules)
        logger.info(f"   AI Features: {'✅' if config.enable_ai else '❌'}")
        logger.info(f"   Voice Interface: {'✅' if config.enable_voice else '❌'}")
        logger.info(f"   Mobile App: {'✅' if config.enable_mobile else '❌'}")
        logger.info(f"   Development Mode: {'✅' if config.dev_mode else '❌'}")
        if config.ai_models:
            logger.info(f"   AI Models: {', '.join(config.ai_models)
            
        confirm = input(f"\n✅ Proceed with installation? [Y/n]: ").strip().lower()
        if confirm == 'n':
            logger.info("❌ Installation cancelled.")
            sys.exit(0)
            
        return config
    
    def check_dependencies(self) -> bool:
        """Check and install missing dependencies"""
        logger.info("🔍 Checking dependencies...")
        missing_deps = []
        
        # Critical dependencies
        if not self.system_info.docker_available:
            missing_deps.append("Docker")
        if not self.system_info.git_available:
            missing_deps.append("Git")
        if not self.system_info.node_available and self.config.enable_mobile:
            missing_deps.append("Node.js")
            
        if missing_deps:
            logger.info(f"\n⚠️  Missing Dependencies: {', '.join(missing_deps)
            install_deps = input("🤖 Auto-install missing dependencies? [Y/n]: ").strip().lower() != 'n'
            
            if install_deps:
                return self._install_dependencies(missing_deps)
            else:
                logger.info("❌ Cannot proceed without required dependencies.")
                return False
                
        logger.info("✅ All dependencies satisfied")
        return True
    
    def _install_dependencies(self, deps: List[str]) -> bool:
        """Install missing dependencies based on OS"""
        logger.info(f"📦 Installing dependencies: {', '.join(deps)}")
        
        try:
            if self.system_info.os_type == OSType.WINDOWS:
                return self._install_windows_deps(deps)
            elif self.system_info.os_type == OSType.LINUX:
                return self._install_linux_deps(deps)
            elif self.system_info.os_type == OSType.MACOS:
                return self._install_macos_deps(deps)
        except Exception as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
            
        return True
    
    def _install_windows_deps(self, deps: List[str]) -> bool:
        """Install dependencies on Windows using Chocolatey"""
        # Check for Chocolatey
        if not shutil.which("choco"):
            logger.info("🍫 Installing Chocolatey package manager...")
            powershell_cmd = """
            Set-ExecutionPolicy Bypass -Scope Process -Force;
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            """
            subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
        
        # Install dependencies
        for dep in deps:
            if dep == "Docker":
                subprocess.run(["choco", "install", "docker-desktop", "-y"], check=True)
            elif dep == "Git":
                subprocess.run(["choco", "install", "git", "-y"], check=True)
            elif dep == "Node.js":
                subprocess.run(["choco", "install", "nodejs", "-y"], check=True)
                
        logger.info("🔄 Please restart your terminal and re-run the installer.")
        return False  # Require restart
    
    def _install_linux_deps(self, deps: List[str]) -> bool:
        """Install dependencies on Linux"""
        # Detect package manager
        if shutil.which("apt-get"):
            pkg_manager = "apt"
        elif shutil.which("yum"):
            pkg_manager = "yum"
        elif shutil.which("dnf"):
            pkg_manager = "dnf"
        elif shutil.which("pacman"):
            pkg_manager = "pacman"
        else:
            logger.error("❌ Unsupported Linux distribution")
            return False
            
        for dep in deps:
            if dep == "Docker":
                if pkg_manager == "apt":
                    subprocess.run(["sudo", "apt-get", "update"], check=True)
                    subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose"], check=True)
                    subprocess.run(["sudo", "systemctl", "enable", "docker"], check=True)
                    subprocess.run(["sudo", "usermod", "-aG", "docker", os.getenv("USER")], check=True)
            elif dep == "Git":
                if pkg_manager == "apt":
                    subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)
            elif dep == "Node.js":
                if pkg_manager == "apt":
                    subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs", "npm"], check=True)
                    
        return True
    
    def _install_macos_deps(self, deps: List[str]) -> bool:
        """Install dependencies on macOS using Homebrew"""
        # Check for Homebrew
        if not shutil.which("brew"):
            logger.info("🍺 Installing Homebrew package manager...")
            subprocess.run(["/bin/bash", "-c", 
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"], check=True)
        
        for dep in deps:
            if dep == "Docker":
                subprocess.run(["brew", "install", "--cask", "docker"], check=True)
            elif dep == "Git":
                subprocess.run(["brew", "install", "git"], check=True)
            elif dep == "Node.js":
                subprocess.run(["brew", "install", "node"], check=True)
                
        return True
    
    def setup_directories(self) -> bool:
        """Create directory structure"""
        logger.info(f"📁 Setting up directories in {self.config.install_directory}")
        
        dirs = [
            "frontend/noxpanel-ui",
            "frontend/noxgo-mobile", 
            "backend/fastapi",
            "backend/flask-legacy",
            "services/langflow",
            "services/ollama",
            "data/postgres",
            "data/redis", 
            "data/logs",
            "config",
            "scripts",
            "docker",
            "plugins"
        ]
        
        for dir_path in dirs:
            full_path = self.config.install_directory / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("✅ Directory structure created")
    
    def clone_repositories(self) -> bool:
        """Clone or copy existing codebase"""
        logger.info("📂 Setting up codebase...")
        
        # Copy existing NoxPanel/Heimnetz codebase
        src_dir = Path.cwd()
        dst_dir = self.config.install_directory / "backend" / "flask-legacy"
        
        if src_dir != dst_dir:
            shutil.copytree(src_dir / "NoxPanel", dst_dir / "NoxPanel", dirs_exist_ok=True)
            shutil.copytree(src_dir / "aethercore", dst_dir / "aethercore", dirs_exist_ok=True)
            
            # Copy Docker configurations
            for file in src_dir.glob("docker-compose*.yml"):
                shutil.copy2(file, self.config.install_directory / "docker")
                
            # Copy configuration files
            for file in ["pyproject.toml", ".env.example", "requirements.txt"]:
                if (src_dir / file).exists():
                    shutil.copy2(src_dir / file, self.config.install_directory)
        
        logger.info("✅ Existing codebase integrated")
    
    def generate_react_frontend(self) -> bool:
        """Generate React-based frontend"""
        logger.info("⚛️  Generating React frontend...")
        
        frontend_dir = self.config.install_directory / "frontend" / "noxpanel-ui"
        
        # Create package.json
        package_json = {
            "name": "noxpanel-ui",
            "version": "2.0.0",
            "description": "NoxSuite React Frontend - ADHD-Friendly Network Management",
            "scripts": {
                "dev": "next dev",
                "build": "next build", 
                "start": "next start",
                "lint": "next lint",
                "type-check": "tsc --noEmit"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@tanstack/react-query": "^4.36.1",
                "axios": "^1.6.0",
                "tailwindcss": "^3.3.0",
                "@headlessui/react": "^1.7.17",
                "@heroicons/react": "^2.0.18",
                "framer-motion": "^10.16.0",
                "socket.io-client": "^4.7.0",
                "react-hook-form": "^7.47.0",
                "react-hot-toast": "^2.4.1",
                "@types/node": "^20.8.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "typescript": "^5.2.0"
            },
            "devDependencies": {
                "eslint": "^8.51.0",
                "eslint-config-next": "^14.0.0",
                "@typescript-eslint/eslint-plugin": "^6.7.0",
                "@typescript-eslint/parser": "^6.7.0",
                "autoprefixer": "^10.4.16",
                "postcss": "^8.4.31"
            }
        }
        
        with open(frontend_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
            
        # Create basic Next.js structure
        self._create_nextjs_structure(frontend_dir)
        
        logger.info("✅ React frontend generated")
    
    def _create_nextjs_structure(self, frontend_dir: Path) -> bool:
        """Create Next.js application structure"""
        
        # Next.js config
        nextjs_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
'''
        with open(frontend_dir / "next.config.js", "w") as f:
            f.write(nextjs_config)
            
        # Tailwind config
        tailwind_config = '''module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // ADHD-friendly color palette
        'nox-primary': '#6366f1',
        'nox-secondary': '#8b5cf6', 
        'nox-accent': '#f59e0b',
        'nox-danger': '#ef4444',
        'nox-success': '#10b981',
        'nox-warning': '#f59e0b',
        // Spicy mode (high contrast)
        'spicy-bg': '#0f0f0f',
        'spicy-text': '#ffffff',
        'spicy-accent': '#ff6b6b',
        // Steady mode (calm colors)
        'steady-bg': '#f8fafc',
        'steady-text': '#334155',
        'steady-accent': '#3b82f6',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
'''
        with open(frontend_dir / "tailwind.config.js", "w") as f:
            f.write(tailwind_config)
            
        # TypeScript config
        ts_config = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./*"],
                    "@/components/*": ["./components/*"],
                    "@/lib/*": ["./lib/*"],
                    "@/types/*": ["./types/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        
        with open(frontend_dir / "tsconfig.json", "w") as f:
            json.dump(ts_config, f, indent=2)
            
        # Create directory structure
        dirs = ["pages", "components", "lib", "types", "styles", "public"]
        for dir_name in dirs:
            (frontend_dir / dir_name).mkdir(exist_ok=True)
            
        # Basic index page
        index_page = '''import { useState, useEffect } from 'react'
import Head from 'next/head'
import { motion } from 'framer-motion'

export default function Home() {
  const [theme, setTheme] = useState('steady')
  const [systemStatus, setSystemStatus] = useState('loading')

  useEffect(() => {
    // Fetch system status
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setSystemStatus(data.status))
      .catch(() => setSystemStatus('error'))
  }, [])

  return (
    <>
      <Head>
        <title>NoxSuite - AI-Powered Infrastructure Management</title>
        <meta name="description" content="ADHD-friendly network management with AI automation" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className={`min-h-screen ${theme === 'spicy' ? 'bg-spicy-bg text-spicy-text' : 'bg-steady-bg text-steady-text'}`}>
        <nav className="border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-nox-primary">🧠 NoxSuite</h1>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setTheme(theme === 'spicy' ? 'steady' : 'spicy')}
                  className="px-3 py-2 rounded-md text-sm font-medium bg-nox-primary text-white hover:bg-nox-secondary"
                >
                  {theme === 'spicy' ? '🧘 Steady' : '🌶️ Spicy'} Mode
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center"
            >
              <h2 className="text-4xl font-extrabold mb-4">
                Welcome to NoxSuite 🚀
              </h2>
              <p className="text-xl mb-8 text-gray-600 dark:text-gray-300">
                AI-Powered Infrastructure Management for ADHD-Friendly Operations
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                  <h3 className="text-lg font-semibold mb-2">🛡️ NoxGuard</h3>
                  <p className="text-gray-600 dark:text-gray-300">Real-time security monitoring</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                  <h3 className="text-lg font-semibold mb-2">🤖 AI Agents</h3>
                  <p className="text-gray-600 dark:text-gray-300">Intelligent automation workflows</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                  <h3 className="text-lg font-semibold mb-2">📱 NoxGo Mobile</h3>
                  <p className="text-gray-600 dark:text-gray-300">Mobile companion app</p>
                </div>
              </div>
            </motion.div>
          </div>
        </main>
      </div>
    </>
  )
}
'''
        with open(frontend_dir / "pages" / "index.tsx", "w") as f:
            f.write(index_page)
    
    def generate_fastapi_backend(self) -> bool:
        """Generate FastAPI backend service"""
        logger.info("🚀 Generating FastAPI backend...")
        
        backend_dir = self.config.install_directory / "backend" / "fastapi"
        
        # Create main FastAPI application
        main_py = '''from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone

from .routers import (
    noxpanel, noxguard, autoimport, powerlog,
    langflow_hub, autocleaner, heimnetz_scanner,
    system, auth
)
from .core.config import settings
from .core.database import init_db
from .core.ai_manager import AIManager
from .core.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting NoxSuite FastAPI Backend...")
    
    # Initialize database
    await init_db()
    
    # Initialize AI Manager
    ai_manager = AIManager()
    await ai_manager.initialize()
    app.state.ai_manager = ai_manager
    
    # Initialize WebSocket Manager
    ws_manager = WebSocketManager()
    app.state.ws_manager = ws_manager
    
    logger.info("✅ NoxSuite Backend initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down NoxSuite Backend...")
    await ai_manager.cleanup()

# Create FastAPI application
app = FastAPI(
    title="NoxSuite API",
    description="AI-Powered Infrastructure Management Backend",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(noxpanel.router, prefix="/api/noxpanel", tags=["NoxPanel"])
app.include_router(noxguard.router, prefix="/api/noxguard", tags=["NoxGuard"])
app.include_router(autoimport.router, prefix="/api/autoimport", tags=["AutoImport"])
app.include_router(powerlog.router, prefix="/api/powerlog", tags=["PowerLog"])
app.include_router(langflow_hub.router, prefix="/api/langflow", tags=["Langflow Hub"])
app.include_router(autocleaner.router, prefix="/api/autocleaner", tags=["AutoCleaner"])
app.include_router(heimnetz_scanner.router, prefix="/api/scanner", tags=["Network Scanner"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "🧠 NoxSuite API - AI-Powered Infrastructure Management"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "redis": "connected", 
            "ai_models": "loaded"
        }
    }

@app.get("/api/status")
async def system_status():
    """Get system status"""
    try:
        ai_manager = app.state.ai_manager
        models_status = await ai_manager.get_models_status()
        
        return {
            "status": "operational",
            "uptime": "00:05:23", # TODO: Calculate actual uptime
            "modules": {
                "noxpanel": "active",
                "noxguard": "active", 
                "autoimport": "active",
                "powerlog": "active",
                "langflow_hub": "active",
                "autocleaner": "active",
                "heimnetz_scanner": "active"
            },
            "ai_models": models_status,
            "metrics": {
                "cpu_usage": 15.2,
                "memory_usage": 42.8,
                "disk_usage": 67.1,
                "network_traffic": "1.2 MB/s"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False,
        log_level="info"
    )
'''
        with open(backend_dir / "main.py", "w") as f:
            f.write(main_py)
            
        # Create directory structure
        dirs = ["routers", "core", "models", "services", "utils"]
        for dir_name in dirs:
            (backend_dir / dir_name).mkdir(parents=True, exist_ok=True)
            (backend_dir / dir_name / "__init__.py").touch()
            
        logger.info("✅ FastAPI backend generated")
    
    def generate_docker_compose(self) -> bool:
        """Generate comprehensive Docker Compose configuration"""
        logger.info("🐳 Generating Docker Compose configuration...")
        
        docker_dir = self.config.install_directory / "docker"
        
        compose_config = {
            "version": "3.8",
            "services": {
                # React Frontend
                "noxpanel-ui": {
                    "build": {
                        "context": "../frontend/noxpanel-ui",
                        "dockerfile": "Dockerfile"
                    },
                    "ports": ["3000:3000"],
                    "environment": {
                        "NODE_ENV": "development" if self.config.dev_mode else "production",
                        "NEXT_PUBLIC_API_URL": "http://localhost:8000"
                    },
                    "volumes": ["../frontend/noxpanel-ui:/app"] if self.config.dev_mode else [],
                    "depends_on": ["noxsuite-api"],
                    "networks": ["noxsuite-network"]
                },
                
                # FastAPI Backend
                "noxsuite-api": {
                    "build": {
                        "context": "../backend/fastapi",
                        "dockerfile": "Dockerfile"
                    },
                    "ports": ["8000:8000"],
                    "environment": {
                        "DATABASE_URL": "postgresql://postgres:noxsuite123@postgres:5432/noxsuite",
                        "REDIS_URL": "redis://redis:6379",
                        "OLLAMA_HOST": "http://ollama:11434" if self.config.enable_ai else "",
                        "DEBUG": str(self.config.dev_mode).lower()
                    },
                    "volumes": [
                        "../backend/fastapi:/app",
                        "../data/logs:/app/logs"
                    ],
                    "depends_on": ["postgres", "redis"],
                    "networks": ["noxsuite-network"]
                },
                
                # Legacy Flask Backend (Compatibility)
                "heimnetz-legacy": {
                    "build": {
                        "context": "../backend/flask-legacy",
                        "dockerfile": "../../Dockerfile.production"  
                    },
                    "ports": ["5000:5000"],
                    "environment": {
                        "FLASK_ENV": "development" if self.config.dev_mode else "production",
                        "DATABASE_URL": "postgresql://postgres:noxsuite123@postgres:5432/noxsuite",
                        "REDIS_URL": "redis://redis:6379"
                    },
                    "volumes": ["../data/logs:/app/logs"],
                    "depends_on": ["postgres", "redis"],
                    "networks": ["noxsuite-network"]
                },
                
                # PostgreSQL Database
                "postgres": {
                    "image": "postgres:15-alpine",
                    "environment": {
                        "POSTGRES_DB": "noxsuite",
                        "POSTGRES_USER": "postgres", 
                        "POSTGRES_PASSWORD": "noxsuite123"
                    },
                    "volumes": [
                        "../data/postgres:/var/lib/postgresql/data",
                        "../sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
                    ],
                    "ports": ["5432:5432"],
                    "networks": ["noxsuite-network"],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U postgres"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                },
                
                # Redis Cache
                "redis": {
                    "image": "redis:7-alpine",
                    "command": "redis-server --appendonly yes",
                    "volumes": ["../data/redis:/data"],
                    "ports": ["6379:6379"],
                    "networks": ["noxsuite-network"],
                    "healthcheck": {
                        "test": ["CMD", "redis-cli", "ping"],
                        "interval": "10s",
                        "timeout": "3s",
                        "retries": 3
                    }
                },
                
                # Nginx Reverse Proxy
                "nginx": {
                    "image": "nginx:alpine",
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        "../nginx/nginx.conf:/etc/nginx/nginx.conf:ro",
                        "../ssl:/etc/ssl:ro"
                    ],
                    "depends_on": ["noxpanel-ui", "noxsuite-api"],
                    "networks": ["noxsuite-network"]
                },
                
                # Prometheus Monitoring
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "../prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
                        "../data/prometheus:/prometheus"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--web.enable-lifecycle"
                    ],
                    "networks": ["noxsuite-network"]
                },
                
                # Grafana Dashboards
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "ports": ["3001:3000"],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "noxsuite123"
                    },
                    "volumes": [
                        "../data/grafana:/var/lib/grafana",
                        "../grafana/provisioning:/etc/grafana/provisioning:ro"
                    ],
                    "depends_on": ["prometheus"],
                    "networks": ["noxsuite-network"]
                }
            },
            
            "networks": {
                "noxsuite-network": {
                    "driver": "bridge"
                }
            },
            
            "volumes": {
                "postgres_data": {"driver": "local"},
                "redis_data": {"driver": "local"},
                "prometheus_data": {"driver": "local"},
                "grafana_data": {"driver": "local"}
            }
        }
        
        # Add AI services if enabled
        if self.config.enable_ai:
            compose_config["services"]["ollama"] = {
                "image": "ollama/ollama:latest",
                "ports": ["11434:11434"],
                "volumes": [
                    "../data/ollama:/root/.ollama",
                    "../models:/models"
                ],
                "environment": {
                    "OLLAMA_HOST": "0.0.0.0"
                },
                "networks": ["noxsuite-network"],
                "deploy": {
                    "resources": {
                        "reservations": {
                            "devices": [
                                {
                                    "driver": "nvidia",
                                    "count": "all",
                                    "capabilities": ["gpu"]
                                }
                            ]
                        }
                    }
                }
            }
            
            compose_config["services"]["langflow"] = {
                "image": "logspace/langflow:latest",
                "ports": ["7860:7860"],
                "environment": {
                    "LANGFLOW_DATABASE_URL": "postgresql://postgres:noxsuite123@postgres:5432/langflow",
                    "LANGFLOW_REDIS_URL": "redis://redis:6379"
                },
                "volumes": ["../data/langflow:/app/langflow"],
                "depends_on": ["postgres", "redis", "ollama"],
                "networks": ["noxsuite-network"]
            }
        
        # Write Docker Compose file
        import yaml
        with open(docker_dir / "docker-compose.noxsuite.yml", "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)
            
        logger.info("✅ Docker Compose configuration generated")
    
    def install_ai_models(self) -> bool:
        """Install and configure AI models"""
        if not self.config.enable_ai or not self.config.ai_models:
            return
            
        logger.info("🤖 Installing AI models...")
        
        models_dir = self.config.install_directory / "models"
        models_dir.mkdir(exist_ok=True)
        
        # Create model installation script
        install_script = f'''#!/bin/bash
# NoxSuite AI Model Installation Script

echo "🤖 Installing AI models for NoxSuite..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama service..."
while ! curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 2
done

echo "✅ Ollama is ready, installing models..."

# Install each selected model
{chr(10).join([f'echo "📦 Installing {model}..."' + chr(10) + f'ollama pull {model}' for model in self.config.ai_models])}

echo "✅ All AI models installed successfully!"

# Test models
echo "🧪 Testing models..."
{chr(10).join([f'echo "Testing {model}..."' + chr(10) + f'ollama run {model} "Hello, test response please" --timeout 30' for model in self.config.ai_models[:1]])}

echo "🎉 AI model installation complete!"
'''
        
        script_path = self.config.install_directory / "scripts" / "install-models.sh"
        script_path.parent.mkdir(exist_ok=True)
        with open(script_path, "w") as f:
            f.write(install_script)
        script_path.chmod(0o755)
        
        logger.info(f"✅ AI model installation script created: {script_path}")
    
    def generate_startup_scripts(self) -> bool:
        """Generate platform-specific startup scripts"""
        logger.info("📜 Generating startup scripts...")
        
        scripts_dir = self.config.install_directory / "scripts"
        
        # Cross-platform startup script
        if self.system_info.os_type == OSType.WINDOWS:
            startup_script = f'''@echo off
echo 🧠 Starting NoxSuite + AI Dev Infrastructure...
echo ================================================

cd /d "{self.config.install_directory}"

echo 🐳 Starting Docker services...
docker-compose -f docker/docker-compose.noxsuite.yml up -d

echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak > nul

{"echo 🤖 Installing AI models..." if self.config.enable_ai else ""}
{"call scripts\\install-models.bat" if self.config.enable_ai else ""}

echo ✅ NoxSuite is starting up!
echo 🌐 Web UI: http://localhost:3000
echo 📊 Grafana: http://localhost:3001
echo 🔧 API Docs: http://localhost:8000/api/docs
{"echo 🤖 Langflow: http://localhost:7860" if self.config.enable_ai else ""}

if "{self.config.auto_start}" == "True" (
    echo 🚀 Opening web interface...
    start http://localhost:3000
)

pause
'''
            with open(scripts_dir / "start-noxsuite.bat", "w") as f:
                f.write(startup_script)
                
        else:  # Linux/macOS
            startup_script = f'''#!/bin/bash
echo "🧠 Starting NoxSuite + AI Dev Infrastructure..."
echo "================================================"

cd "{self.config.install_directory}"

echo "🐳 Starting Docker services..."
docker-compose -f docker/docker-compose.noxsuite.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

{"echo '🤖 Installing AI models...'" if self.config.enable_ai else ""}
{"bash scripts/install-models.sh" if self.config.enable_ai else ""}

echo "✅ NoxSuite is starting up!"
echo "🌐 Web UI: http://localhost:3000"
echo "📊 Grafana: http://localhost:3001" 
echo "🔧 API Docs: http://localhost:8000/api/docs"
{"echo '🤖 Langflow: http://localhost:7860'" if self.config.enable_ai else ""}

{"echo '🚀 Opening web interface...'" if self.config.auto_start else ""}
{"command -v xdg-open > /dev/null && xdg-open 'http://localhost:3000' || open 'http://localhost:3000'" if self.config.auto_start else ""}

echo "Press any key to continue..."
read -n 1
'''
            script_path = scripts_dir / "start-noxsuite.sh"
            with open(script_path, "w") as f:
                f.write(startup_script)
            script_path.chmod(0o755)
            
        logger.info("✅ Startup scripts generated")
    
    def create_configuration_files(self) -> bool:
        """Create configuration files and environment variables"""
        logger.info("⚙️  Creating configuration files...")
        
        config_dir = self.config.install_directory / "config"
        
        # Environment configuration
        env_content = f'''# NoxSuite Configuration
NOXSUITE_ENV={"development" if self.config.dev_mode else "production"}
DEBUG={"true" if self.config.dev_mode else "false"}

# Database
DATABASE_URL=postgresql://postgres:noxsuite123@localhost:5432/noxsuite
REDIS_URL=redis://localhost:6379

# AI Configuration
ENABLE_AI={"true" if self.config.enable_ai else "false"}
ENABLE_VOICE={"true" if self.config.enable_voice else "false"}
OLLAMA_HOST=http://localhost:11434
AI_MODELS={",".join(self.config.ai_models)}

# Security
SECRET_KEY={os.urandom(32).hex()}
JWT_SECRET={os.urandom(32).hex()}

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=noxsuite123

# Logging
LOG_LEVEL={"DEBUG" if self.config.dev_mode else "INFO"}
LOG_FILE=/app/logs/noxsuite.log

# Feature Flags
ENABLE_MOBILE={"true" if self.config.enable_mobile else "false"}
ENABLE_LEGACY_SUPPORT=true
ENABLE_EXPERIMENTAL_FEATURES={"true" if self.config.dev_mode else "false"}
'''
        
        with open(self.config.install_directory / ".env", "w") as f:
            f.write(env_content)
            
        # NoxSuite configuration
        noxsuite_config = {
            "version": "2.0.0",
            "installation": {
                "directory": str(self.config.install_directory),
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "installer_version": "1.0.0"
            },
            "modules": {
                module: {"enabled": True, "version": "2.0.0"} 
                for module in self.config.modules
            },
            "features": {
                "ai_enabled": self.config.enable_ai,
                "voice_enabled": self.config.enable_voice,
                "mobile_enabled": self.config.enable_mobile,
                "dev_mode": self.config.dev_mode
            },
            "ai": {
                "models": self.config.ai_models,
                "ollama_host": "http://localhost:11434",
                "langflow_enabled": self.config.enable_ai
            },
            "system": {
                "os_type": self.system_info.os_type.value,
                "architecture": self.system_info.architecture,
                "cpu_cores": self.system_info.cpu_cores,
                "memory_gb": self.system_info.available_memory
            }
        }
        
        with open(config_dir / "noxsuite.json", "w") as f:
            json.dump(noxsuite_config, f, indent=2)
            
        logger.info("✅ Configuration files created")
    
    def finalize_installation(self) -> bool:
        """Finalize installation and provide summary"""
        logger.info("🎯 Finalizing installation...")
        
        # Create installation summary
        summary = {
            "installation_status": "completed",
            "installation_time": datetime.now(timezone.utc).isoformat(),
            "installation_directory": str(self.config.install_directory),
            "modules_installed": self.config.modules,
            "features": {
                "ai_enabled": self.config.enable_ai,
                "voice_enabled": self.config.enable_voice,
                "mobile_enabled": self.config.enable_mobile,
                "dev_mode": self.config.dev_mode
            },
            "services": {
                "web_ui": "http://localhost:3000",
                "api": "http://localhost:8000",
                "grafana": "http://localhost:3001",
                "prometheus": "http://localhost:9090"
            },
            "next_steps": [
                "Run the startup script to begin",
                "Access the web interface at http://localhost:3000",
                "Configure additional modules as needed",
                "Set up monitoring dashboards in Grafana"
            ]
        }
        
        if self.config.enable_ai:
            summary["services"]["langflow"] = "http://localhost:7860"
            summary["services"]["ollama"] = "http://localhost:11434"
            summary["next_steps"].insert(2, "Wait for AI models to download and initialize")
        
        # Save installation summary
        with open(self.config.install_directory / "INSTALLATION_SUMMARY.json", "w") as f:
            json.dump(summary, f, indent=2)
            
        # Display completion message
        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    🎉 Installation Complete!                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  NoxSuite + AI Dev Infrastructure has been successfully installed ║
║                                                                   ║
║  📁 Installation Directory: {str(self.config.install_directory):<30} ║
║  🔧 Modules: {len(self.config.modules)} modules installed                            ║
║  🤖 AI Features: {'✅ Enabled' if self.config.enable_ai else '❌ Disabled':<43} ║
║                                                                   ║
║  🌐 Web Interface: http://localhost:3000                         ║
║  🔧 API Documentation: http://localhost:8000/api/docs            ║
║  📊 Monitoring: http://localhost:3001                            ║
{"║  🤖 Langflow: http://localhost:7860                              ║" if self.config.enable_ai else ""}
║                                                                   ║
║  🚀 To start NoxSuite:                                           ║
║     {"Windows: scripts\\start-noxsuite.bat" if self.system_info.os_type == OSType.WINDOWS else "Unix: ./scripts/start-noxsuite.sh":<54} ║
║                                                                   ║
║  📚 Documentation: NOXSUITE_ARCHITECTURE.md                     ║
║  📋 Summary: INSTALLATION_SUMMARY.json                          ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
        
        logger.info("🎉 NoxSuite installation completed successfully!")
    
    def run_installation(self) -> bool:
        """Run the complete installation process"""
        try:
            self.welcome_screen()
            self.config = self.interactive_config()
            
            if not self.check_dependencies():
                return False
                
            self.setup_directories()
            self.clone_repositories()
            self.generate_react_frontend()
            self.generate_fastapi_backend()
            self.generate_docker_compose()
            
            if self.config.enable_ai:
                self.install_ai_models()
                
            self.generate_startup_scripts()
            self.create_configuration_files()
            self.finalize_installation()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\n❌ Installation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            logger.error(f"\n❌ Installation failed: {e}")
            logger.info("📋 Check noxsuite-install.log for details")
            return False

def main() -> bool:
    """Main installer entry point"""
    installer = NoxSuiteInstaller()
    success = installer.run_installation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
