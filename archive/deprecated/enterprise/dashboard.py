#!/usr/bin/env python3
"""
Enterprise Dashboard - Audit 4 Advanced Features Integration
===========================================================

This system provides a comprehensive enterprise dashboard integrating:
- TTS/Voice Assistant capabilities
- WebRTC real-time communication
- Advanced analytics and monitoring
- System performance metrics
- Security monitoring
- User management
- Real-time notifications

The ultimate administrative and user interface for Heimnetz
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import hmac
import base64

# Web framework
try:
    from fastapi import FastAPI, WebSocket, Request, Response, Depends, HTTPException, status
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# WebSocket management
try:
    from fastapi import WebSocket, WebSocketDisconnect
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our systems
try:
    from voice.tts_system import VoiceAssistant, VoiceConfig, AudioConfig
    from webrtc.webrtc_system import WebRTCPeerManager, WebRTCConfig, SignalingServer
    from analytics.analytics_dashboard import AnalyticsEngine, MetricType, AlertLevel
except ImportError as e:
    print(f"Warning: Could not import some systems: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

class SystemStatus(Enum):
    """System status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"

class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class User:
    """User account"""
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Session:
    """User session"""
    id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

@dataclass
class Notification:
    """System notification"""
    id: str
    type: NotificationType
    title: str
    message: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    expires_at: Optional[datetime] = None

class WebSocketManager:
    """
    WebSocket connection manager for real-time updates
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Connect a WebSocket"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        
        self.logger.info(f"WebSocket connected: {user_id} ({connection_id})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove user mapping
        user_id = None
        for uid, cid in self.user_connections.items():
            if cid == connection_id:
                user_id = uid
                break
        
        if user_id:
            del self.user_connections[user_id]
        
        self.logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending message to {user_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)

class SecurityManager:
    """
    Security and authentication manager
    """
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_user = User(
            id="admin",
            username="admin",
            email="admin@heimnetz.local",
            role=UserRole.ADMIN
        )
        self.users[admin_user.id] = admin_user
        
        self.logger.info("Created default admin user")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        # Simple authentication - in production, use proper password hashing
        if username == "admin" and password == "admin":
            return self.users.get("admin")
        
        return None
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create user session"""
        session_id = str(uuid.uuid4())
        
        session = Session(
            id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        
        # Update user last login
        if user_id in self.users:
            self.users[user_id].last_login = datetime.now()
        
        self.logger.info(f"Created session for user {user_id}: {session_id}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session is active
        if not session.is_active:
            return None
        
        # Check session timeout (24 hours)
        if datetime.now() - session.last_activity > timedelta(hours=24):
            session.is_active = False
            return None
        
        # Update last activity
        session.last_activity = datetime.now()
        
        # Return user
        return self.users.get(session.user_id)
    
    def create_token(self, user_id: str) -> str:
        """Create JWT-like token"""
        payload = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        token_data = base64.b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token_data}.{signature}"
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate token and return user"""
        try:
            token_data, signature = token.split('.')
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                return None
            
            # Decode payload
            payload = json.loads(base64.b64decode(token_data).decode())
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.now() > expires_at:
                return None
            
            # Return user
            return self.users.get(payload["user_id"])
            
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return None

class NotificationManager:
    """
    Notification management system
    """
    
    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_notification(self, type: NotificationType, title: str, message: str,
                          user_id: Optional[str] = None, expires_in: Optional[int] = None) -> str:
        """Create a notification"""
        notification_id = str(uuid.uuid4())
        
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        notification = Notification(
            id=notification_id,
            type=type,
            title=title,
            message=message,
            user_id=user_id,
            expires_at=expires_at
        )
        
        self.notifications[notification_id] = notification
        
        self.logger.info(f"Created notification: {title} ({notification_id})")
        return notification_id
    
    def get_user_notifications(self, user_id: str) -> List[Notification]:
        """Get notifications for user"""
        notifications = []
        
        for notification in self.notifications.values():
            # Include global notifications and user-specific ones
            if notification.user_id is None or notification.user_id == user_id:
                # Check if not expired
                if notification.expires_at is None or datetime.now() < notification.expires_at:
                    notifications.append(notification)
        
        # Sort by creation time (newest first)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        return notifications
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        if notification_id in self.notifications:
            self.notifications[notification_id].is_read = True
            return True
        return False

class EnterpriseDashboard:
    """
    Main enterprise dashboard application
    """
    
    def __init__(self):
        self.app = None
        self.websocket_manager = WebSocketManager()
        self.security_manager = SecurityManager()
        self.notification_manager = NotificationManager()
        
        # Initialize subsystems
        self.voice_assistant = None
        self.webrtc_manager = None
        self.analytics_engine = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize systems
        self._initialize_systems()
        
        # Create FastAPI app
        if HAS_FASTAPI:
            self._create_app()
    
    def _initialize_systems(self):
        """Initialize all subsystems"""
        try:
            # Initialize voice assistant
            try:
                self.voice_assistant = VoiceAssistant()
                self.logger.info("Voice assistant initialized")
            except Exception as e:
                self.logger.warning(f"Voice assistant initialization failed: {e}")
            
            # Initialize WebRTC manager
            try:
                self.webrtc_manager = WebRTCPeerManager(WebRTCConfig())
                self.logger.info("WebRTC manager initialized")
            except Exception as e:
                self.logger.warning(f"WebRTC manager initialization failed: {e}")
            
            # Initialize analytics engine
            try:
                self.analytics_engine = AnalyticsEngine()
                self.logger.info("Analytics engine initialized")
            except Exception as e:
                self.logger.warning(f"Analytics engine initialization failed: {e}")
                
        except Exception as e:
            self.logger.error(f"System initialization error: {e}")
    
    def _create_app(self):
        """Create FastAPI application"""
        try:
            self.app = FastAPI(
                title="Heimnetz Enterprise Dashboard",
                description="Advanced enterprise dashboard with voice, WebRTC, and analytics",
                version="1.0.0"
            )
            
            # Add middleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
            
            self.app.add_middleware(GZipMiddleware, minimum_size=1000)
            
            # Mount static files
            self.app.mount("/static", StaticFiles(directory="static"), name="static")
            
            # Templates
            self.templates = Jinja2Templates(directory="templates")
            
            # Add routes
            self._add_routes()
            
            self.logger.info("FastAPI application created")
            
        except Exception as e:
            self.logger.error(f"Error creating FastAPI app: {e}")
    
    def _add_routes(self):
        """Add API routes"""
        
        # Authentication dependency
        security = HTTPBearer()
        
        def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
            user = self.security_manager.validate_token(credentials.credentials)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            return user
        
        # Main dashboard
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
        
        # Authentication
        @self.app.post("/api/auth/login")
        async def login(request: Request):
            data = await request.json()
            username = data.get("username")
            password = data.get("password")
            
            user = self.security_manager.authenticate_user(username, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create session
            client_ip = request.client.host
            user_agent = request.headers.get("user-agent", "")
            session_id = self.security_manager.create_session(user.id, client_ip, user_agent)
            
            # Create token
            token = self.security_manager.create_token(user.id)
            
            return {
                "access_token": token,
                "session_id": session_id,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value
                }
            }
        
        # System status
        @self.app.get("/api/system/status")
        async def system_status(user: User = Depends(get_current_user)):
            status = {
                "overall": "healthy",
                "components": {
                    "voice_assistant": self.voice_assistant is not None,
                    "webrtc": self.webrtc_manager is not None,
                    "analytics": self.analytics_engine is not None
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Get system metrics if analytics available
            if self.analytics_engine:
                try:
                    report = self.analytics_engine.get_summary_report()
                    status["metrics"] = report.get("system_status", {})
                except Exception as e:
                    self.logger.error(f"Error getting system metrics: {e}")
            
            return status
        
        # Analytics API
        @self.app.get("/api/analytics/metrics")
        async def get_metrics(metric_name: str, time_range: str = "24h", 
                            user: User = Depends(get_current_user)):
            if not self.analytics_engine:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Analytics engine not available"
                )
            
            try:
                from analytics.analytics_dashboard import TimeRange
                
                time_range_enum = TimeRange(time_range)
                metrics = self.analytics_engine.metrics_collector.get_metrics(
                    metric_name, time_range_enum
                )
                
                return {
                    "metrics": [
                        {
                            "timestamp": m["timestamp"].isoformat(),
                            "value": m["value"]
                        } for m in metrics
                    ]
                }
                
            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error retrieving metrics"
                )
        
        # Voice assistant API
        @self.app.post("/api/voice/speak")
        async def speak_text(request: Request, user: User = Depends(get_current_user)):
            if not self.voice_assistant:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Voice assistant not available"
                )
            
            data = await request.json()
            text = data.get("text")
            
            if not text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text is required"
                )
            
            try:
                success = self.voice_assistant.speak(text)
                return {"success": success}
            except Exception as e:
                self.logger.error(f"Error speaking text: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error speaking text"
                )
        
        # WebRTC API
        @self.app.post("/api/webrtc/create-connection")
        async def create_webrtc_connection(request: Request, user: User = Depends(get_current_user)):
            if not self.webrtc_manager:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="WebRTC manager not available"
                )
            
            data = await request.json()
            room_id = data.get("room_id", "default")
            
            try:
                connection_id = await self.webrtc_manager.create_peer_connection(
                    user.id, room_id
                )
                
                if connection_id:
                    return {"connection_id": connection_id}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create WebRTC connection"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error creating WebRTC connection: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error creating WebRTC connection"
                )
        
        # Notifications API
        @self.app.get("/api/notifications")
        async def get_notifications(user: User = Depends(get_current_user)):
            notifications = self.notification_manager.get_user_notifications(user.id)
            
            return {
                "notifications": [
                    {
                        "id": n.id,
                        "type": n.type.value,
                        "title": n.title,
                        "message": n.message,
                        "created_at": n.created_at.isoformat(),
                        "is_read": n.is_read
                    } for n in notifications
                ]
            }
        
        @self.app.post("/api/notifications/{notification_id}/read")
        async def mark_notification_read(notification_id: str, user: User = Depends(get_current_user)):
            success = self.notification_manager.mark_as_read(notification_id)
            return {"success": success}
        
        # WebSocket endpoint
        @self.app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            connection_id = await self.websocket_manager.connect(websocket, user_id)
            
            try:
                # Send welcome message
                await websocket.send_text(json.dumps({
                    "type": "welcome",
                    "message": "Connected to Heimnetz Enterprise Dashboard",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Listen for messages
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
            except WebSocketDisconnect:
                await self.websocket_manager.disconnect(connection_id)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await self.websocket_manager.disconnect(connection_id)
    
    def start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start system monitoring
            import threading
            threading.Thread(target=self._system_monitoring_loop, daemon=True).start()
            
            # Start notification broadcasting
            threading.Thread(target=self._notification_broadcast_loop, daemon=True).start()
            
            self.logger.info("Background tasks started")
            
        except Exception as e:
            self.logger.error(f"Error starting background tasks: {e}")
    
    def _system_monitoring_loop(self):
        """System monitoring loop"""
        while True:
            try:
                time.sleep(30)  # Monitor every 30 seconds
                
                # Check system health
                self._check_system_health()
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
    
    def _check_system_health(self):
        """Check system health and create alerts"""
        try:
            if self.analytics_engine:
                # Get system metrics
                real_time_metrics = self.analytics_engine.metrics_collector.get_real_time_metrics()
                
                # Check for critical conditions
                for key, metric in real_time_metrics.items():
                    if "system_cpu_usage" in key and metric["current_value"] > 90:
                        self.notification_manager.create_notification(
                            NotificationType.CRITICAL,
                            "High CPU Usage",
                            f"CPU usage is at {metric['current_value']:.1f}%",
                            expires_in=300  # 5 minutes
                        )
                    
                    if "system_memory_usage" in key and metric["current_value"] > 90:
                        self.notification_manager.create_notification(
                            NotificationType.CRITICAL,
                            "High Memory Usage",
                            f"Memory usage is at {metric['current_value']:.1f}%",
                            expires_in=300  # 5 minutes
                        )
                
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
    
    def _notification_broadcast_loop(self):
        """Broadcast notifications to connected users"""
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds
                
                # Get recent notifications
                current_time = datetime.now()
                recent_notifications = []
                
                for notification in self.notification_manager.notifications.values():
                    # Check if notification is recent (last 10 seconds)
                    if current_time - notification.created_at < timedelta(seconds=10):
                        recent_notifications.append(notification)
                
                # Broadcast recent notifications
                for notification in recent_notifications:
                    message = {
                        "type": "notification",
                        "notification": {
                            "id": notification.id,
                            "type": notification.type.value,
                            "title": notification.title,
                            "message": notification.message,
                            "created_at": notification.created_at.isoformat()
                        }
                    }
                    
                    if notification.user_id:
                        # Send to specific user
                        asyncio.run(self.websocket_manager.send_personal_message(
                            notification.user_id, message
                        ))
                    else:
                        # Broadcast to all users
                        asyncio.run(self.websocket_manager.broadcast(message))
                
            except Exception as e:
                self.logger.error(f"Error in notification broadcast loop: {e}")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server"""
        try:
            if not HAS_FASTAPI:
                raise ImportError("FastAPI not installed")
            
            # Start background tasks
            self.start_background_tasks()
            
            # Create welcome notification
            self.notification_manager.create_notification(
                NotificationType.SUCCESS,
                "System Started",
                "Heimnetz Enterprise Dashboard is now running",
                expires_in=3600  # 1 hour
            )
            
            self.logger.info(f"Starting server on {host}:{port}")
            
            # Run the server
            uvicorn.run(self.app, host=host, port=port, log_level="info")
            
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")

def main():
    """Main function"""
    try:
        print("Heimnetz Enterprise Dashboard - Starting...")
        print("=" * 50)
        
        if not HAS_FASTAPI:
            print("Error: FastAPI not installed")
            print("Install with: pip install fastapi uvicorn")
            return
        
        # Create and run dashboard
        dashboard = EnterpriseDashboard()
        dashboard.run()
        
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Dashboard error: {e}")

if __name__ == "__main__":
    main()
