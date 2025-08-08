"""
NoxSuite FastAPI Backend - Main Application
AI-Powered Infrastructure Management API
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import os
import json

# Import routers
from .routers import (
    auth, system, noxpanel, noxguard, autoimport, 
    powerlog, langflow_hub, autocleaner, heimnetz_scanner,
    ai_models, websocket, health
)

# Import core modules
from .core.config import settings
from .core.database import init_db, get_db
from .core.ai_manager import AIManager
from .core.websocket_manager import WebSocketManager
from .core.plugin_manager import PluginManager
from .core.security import get_current_user
from .core.metrics import metrics_middleware
from .core.logging_config import setup_logging

# Import models and schemas
from .models.base import Base
from .schemas.system import SystemStatus, HealthCheck

# Setup logging
setup_logging()

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger(__name__)

# Global managers
ai_manager: Optional[AIManager] = None
ws_manager: Optional[WebSocketManager] = None
plugin_manager: Optional[PluginManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting NoxSuite FastAPI Backend...")
    
    global ai_manager, ws_manager, plugin_manager
    
    try:
        # Initialize database
        logger.info("📊 Initializing database...")
        await init_db()
        
        # Initialize AI Manager
        if settings.ENABLE_AI:
            logger.info("🤖 Initializing AI Manager...")
            ai_manager = AIManager()
            await ai_manager.initialize()
            app.state.ai_manager = ai_manager
        
        # Initialize WebSocket Manager
        logger.info("🌐 Initializing WebSocket Manager...")
        ws_manager = WebSocketManager()
        app.state.ws_manager = ws_manager
        
        # Initialize Plugin Manager
        logger.info("🧩 Initializing Plugin Manager...")
        plugin_manager = PluginManager()
        await plugin_manager.initialize()
        app.state.plugin_manager = plugin_manager
        
        # Start background tasks
        logger.info("⚙️ Starting background tasks...")
        asyncio.create_task(system_monitor_task())
        asyncio.create_task(ai_model_health_check())
        
        logger.info("✅ NoxSuite Backend initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize NoxSuite Backend: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("🛑 Shutting down NoxSuite Backend...")
        
        if ai_manager:
            await ai_manager.cleanup()
        if ws_manager:
            await ws_manager.cleanup()
        if plugin_manager:
            await plugin_manager.cleanup()
            
        logger.info("✅ NoxSuite Backend shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="NoxSuite API",
    description="""
    🧠 **NoxSuite + AI Dev Infrastructure API**
    
    Comprehensive AI-powered infrastructure management platform with:
    
    - **ADHD-Friendly Design**: Intuitive, accessible interfaces
    - **AI Integration**: Local LLM support with Ollama, Langflow
    - **Real-time Monitoring**: WebSocket-powered live updates
    - **Modular Architecture**: Extensible plugin system
    - **Cross-Platform**: Docker-native deployment
    
    ## Features
    
    ### 🛡️ Core Modules
    - **NoxPanel**: Dashboard and system overview
    - **NoxGuard**: Security monitoring and alerts
    - **AutoImport**: Device discovery and inventory
    - **PowerLog**: System health and performance
    
    ### 🤖 AI & Automation
    - **Langflow Hub**: Visual agent workflow builder
    - **AI Models**: Local LLM integration and management
    - **AutoCleaner**: Intelligent system optimization
    - **Smart Analytics**: Pattern recognition and insights
    
    ### 🔧 Infrastructure
    - **Plugin System**: Extensible architecture
    - **WebSocket**: Real-time communication
    - **Metrics**: Prometheus integration
    - **Security**: JWT authentication, RBAC
    """,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "NoxSuite Support",
        "url": "https://github.com/noxpanel/noxsuite",
        "email": "support@noxsuite.dev"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS middleware - Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend
        "http://localhost:3001",  # Grafana
        "http://localhost:3002",  # Mobile PWA
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts (security)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.noxsuite.local"]
)

# Custom metrics middleware
app.middleware("http")(metrics_middleware)

# Security middleware
security = HTTPBearer(auto_error=False)

# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

# Public routes (no authentication required)
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Protected routes (authentication required)
app.include_router(
    system.router, 
    prefix="/api/system", 
    tags=["System Management"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    noxpanel.router, 
    prefix="/api/noxpanel", 
    tags=["NoxPanel Dashboard"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    noxguard.router, 
    prefix="/api/noxguard", 
    tags=["NoxGuard Security"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    autoimport.router, 
    prefix="/api/autoimport", 
    tags=["AutoImport Discovery"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    powerlog.router, 
    prefix="/api/powerlog", 
    tags=["PowerLog Monitoring"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    langflow_hub.router, 
    prefix="/api/langflow", 
    tags=["Langflow AI Hub"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    autocleaner.router, 
    prefix="/api/autocleaner", 
    tags=["AutoCleaner Optimization"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    heimnetz_scanner.router, 
    prefix="/api/scanner", 
    tags=["Network Scanner"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    ai_models.router, 
    prefix="/api/ai", 
    tags=["AI Models"],
    dependencies=[Depends(get_current_user)]
)

# WebSocket routes
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML welcome page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NoxSuite API</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px; 
                margin: 40px auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                line-height: 1.6;
            }
            .container { 
                background: rgba(255,255,255,0.1); 
                padding: 40px; 
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3em; margin-bottom: 20px; text-align: center; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; }
            .links { text-align: center; margin-top: 30px; }
            .links a { 
                display: inline-block; 
                margin: 10px; 
                padding: 12px 24px; 
                background: rgba(255,255,255,0.2); 
                color: white; 
                text-decoration: none; 
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            .links a:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 NoxSuite API</h1>
            <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px;">
                AI-Powered Infrastructure Management Platform
            </p>
            
            <div class="features">
                <div class="feature">
                    <h3>🛡️ Security First</h3>
                    <p>Real-time monitoring, threat detection, and automated response systems.</p>
                </div>
                <div class="feature">
                    <h3>🤖 AI-Powered</h3>
                    <p>Local LLM integration with Ollama, intelligent automation, and smart analytics.</p>
                </div>
                <div class="feature">
                    <h3>🎯 ADHD-Friendly</h3>
                    <p>Intuitive interfaces, clear visual hierarchy, and cognitive load management.</p>
                </div>
                <div class="feature">
                    <h3>⚡ Real-time</h3>
                    <p>WebSocket-powered live updates, instant notifications, and responsive UI.</p>
                </div>
            </div>
            
            <div class="links">
                <a href="/api/docs">📚 API Documentation</a>
                <a href="/api/health">🏥 Health Check</a>
                <a href="http://localhost:3000">🌐 Web Interface</a>
                <a href="http://localhost:3001">📊 Grafana</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "🧠 NoxSuite API - AI-Powered Infrastructure Management",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
        "status": "operational",
        "features": {
            "ai_enabled": settings.ENABLE_AI,
            "voice_enabled": settings.ENABLE_VOICE,
            "websocket_enabled": True,
            "plugins_enabled": True
        },
        "endpoints": {
            "authentication": "/api/auth",
            "system": "/api/system",
            "dashboard": "/api/noxpanel",
            "security": "/api/noxguard",
            "ai_models": "/api/ai",
            "websocket": "/ws"
        }
    }

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def system_monitor_task():
    """Background task for system monitoring"""
    while True:
        try:
            # Collect system metrics
            if ws_manager:
                system_data = await collect_system_metrics()
                await ws_manager.broadcast_to_all({
                    "type": "system_update",
                    "data": system_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            await asyncio.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"System monitor task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

async def ai_model_health_check():
    """Background task for AI model health monitoring"""
    if not settings.ENABLE_AI or not ai_manager:
        return
        
    while True:
        try:
            # Check AI model status
            models_status = await ai_manager.health_check()
            
            if ws_manager:
                await ws_manager.broadcast_to_all({
                    "type": "ai_status_update",
                    "data": models_status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            await asyncio.sleep(120)  # Check every 2 minutes
            
        except Exception as e:
            logger.error(f"AI health check task error: {e}")
            await asyncio.sleep(300)  # Wait longer on error

async def collect_system_metrics() -> Dict[str, Any]:
    """Collect comprehensive system metrics"""
    try:
        import psutil
        import docker
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Docker metrics
        docker_client = docker.from_env()
        containers = docker_client.containers.list()
        
        container_stats = []
        for container in containers:
            if container.name.startswith('noxsuite-'):
                stats = container.stats(stream=False)
                container_stats.append({
                    "name": container.name,
                    "status": container.status,
                    "cpu_usage": _calculate_cpu_percent(stats),
                    "memory_usage": _calculate_memory_usage(stats)
                })
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "uptime": _get_system_uptime()
            },
            "containers": container_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {
            "error": "Failed to collect metrics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

def _calculate_cpu_percent(stats: Dict) -> float:
    """Calculate CPU percentage from Docker stats"""
    try:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        
        if system_delta > 0:
            return (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
        return 0.0
    except (KeyError, ZeroDivisionError):
        return 0.0

def _calculate_memory_usage(stats: Dict) -> Dict[str, int]:
    """Calculate memory usage from Docker stats"""
    try:
        usage = stats['memory_stats']['usage']
        limit = stats['memory_stats']['limit']
        return {
            "usage_mb": usage // 1024 // 1024,
            "limit_mb": limit // 1024 // 1024,
            "percent": (usage / limit) * 100
        }
    except KeyError:
        return {"usage_mb": 0, "limit_mb": 0, "percent": 0}

def _get_system_uptime() -> str:
    """Get system uptime"""
    try:
        import psutil
        return str(psutil.boot_time())
    except ImportError:
        return "0"

# Security: Input validation utilities
import re
import html
from typing import Any, Optional

def validate_input(value: Any, pattern: str = None, max_length: int = 1000) -> str:
    """Validate and sanitize input data."""
    if value is None:
        return ""
    
    # Convert to string and strip
    str_value = str(value).strip()
    
    # Check length
    if len(str_value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    # Apply pattern validation if provided
    if pattern and not re.match(pattern, str_value):
        raise ValueError("Input format validation failed")
    
    # HTML escape for XSS prevention
    return html.escape(str_value)

def validate_file_path(path: str) -> str:
    """Validate file path to prevent directory traversal."""
    if not path:
        raise ValueError("File path cannot be empty")
    
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    if '..' in normalized or normalized.startswith('/'):
        raise ValueError("Invalid file path detected")
    
    return normalized

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path)
        }
    )

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
        server_header=False,
        date_header=False
    )
