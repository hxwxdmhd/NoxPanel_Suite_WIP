#!/usr/bin/env python3
"""
Ultimate Suite v11.0 - Unified Models Implementation
====================================================

This is the SINGLE, UNIFIED models implementation that consolidates:
- Database models from all server implementations
- User management models
- System metrics models
- Audit logging models
- Plugin registry models

ARCHITECTURAL PRINCIPLE: ONE MODELS FILE FOR ALL DATA
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets

# Logging
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

class AuditAction(Enum):
    """Audit action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    SYSTEM = "system"
    PLUGIN = "plugin"

class AuditResult(Enum):
    """Audit result types"""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class User:
    """User model"""
    id: int = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = None
    last_login: datetime = None
    login_attempts: int = 0
    locked_until: datetime = None
    two_factor_enabled: bool = False
    two_factor_secret: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def set_password(self, password: str) -> None:
        """Set password with hashing"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_attempts': self.login_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'two_factor_enabled': self.two_factor_enabled,
            'preferences': self.preferences,
            'metadata': self.metadata
        }

@dataclass
class SystemMetrics:
    """System metrics model"""
    id: int = None
    timestamp: datetime = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_in: float = 0.0
    network_out: float = 0.0
    active_connections: int = 0
    requests_per_minute: int = 0
    response_time_avg: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: int = 0
    system_load: float = 0.0
    temperature: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_in': self.network_in,
            'network_out': self.network_out,
            'active_connections': self.active_connections,
            'requests_per_minute': self.requests_per_minute,
            'response_time_avg': self.response_time_avg,
            'error_rate': self.error_rate,
            'uptime_seconds': self.uptime_seconds,
            'system_load': self.system_load,
            'temperature': self.temperature,
            'metadata': self.metadata
        }

@dataclass
class AuditLog:
    """Audit log model"""
    id: int = None
    timestamp: datetime = None
    user_id: int = None
    session_id: str = ""
    action: AuditAction = AuditAction.ACCESS
    result: AuditResult = AuditResult.SUCCESS
    resource: str = ""
    ip_address: str = ""
    user_agent: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'action': self.action.value,
            'result': self.result.value,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'risk_score': self.risk_score,
            'metadata': self.metadata
        }

@dataclass
class Plugin:
    """Plugin model"""
    id: int = None
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    category: str = "general"
    enabled: bool = False
    auto_start: bool = False
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    status: str = "inactive"
    last_error: str = ""
    install_date: datetime = None
    update_date: datetime = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.install_date is None:
            self.install_date = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'category': self.category,
            'enabled': self.enabled,
            'auto_start': self.auto_start,
            'dependencies': self.dependencies,
            'permissions': self.permissions,
            'config': self.config,
            'status': self.status,
            'last_error': self.last_error,
            'install_date': self.install_date.isoformat() if self.install_date else None,
            'update_date': self.update_date.isoformat() if self.update_date else None,
            'metadata': self.metadata
        }

@dataclass
class Session:
    """Session model"""
    id: str = ""
    user_id: int = None
    created_at: datetime = None
    last_activity: datetime = None
    expires_at: datetime = None
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = secrets.token_hex(32)
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'data': self.data
        }

class UnifiedDatabase:
    """Unified database manager for all models"""
    
    def __init__(self, db_path: str = "unified_heimnetz.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database with all tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        is_active BOOLEAN DEFAULT 1,
                        is_verified BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP,
                        two_factor_enabled BOOLEAN DEFAULT 0,
                        two_factor_secret TEXT,
                        preferences TEXT DEFAULT '{}',
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # System metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cpu_usage REAL DEFAULT 0.0,
                        memory_usage REAL DEFAULT 0.0,
                        disk_usage REAL DEFAULT 0.0,
                        network_in REAL DEFAULT 0.0,
                        network_out REAL DEFAULT 0.0,
                        active_connections INTEGER DEFAULT 0,
                        requests_per_minute INTEGER DEFAULT 0,
                        response_time_avg REAL DEFAULT 0.0,
                        error_rate REAL DEFAULT 0.0,
                        uptime_seconds INTEGER DEFAULT 0,
                        system_load REAL DEFAULT 0.0,
                        temperature REAL DEFAULT 0.0,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Audit log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER,
                        session_id TEXT,
                        action TEXT NOT NULL,
                        result TEXT NOT NULL,
                        resource TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        details TEXT DEFAULT '{}',
                        risk_score INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Plugins table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        version TEXT DEFAULT '1.0.0',
                        description TEXT,
                        author TEXT,
                        category TEXT DEFAULT 'general',
                        enabled BOOLEAN DEFAULT 0,
                        auto_start BOOLEAN DEFAULT 0,
                        dependencies TEXT DEFAULT '[]',
                        permissions TEXT DEFAULT '[]',
                        config TEXT DEFAULT '{}',
                        status TEXT DEFAULT 'inactive',
                        last_error TEXT,
                        install_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        update_date TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        data TEXT DEFAULT '{}'
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugins_enabled ON plugins(enabled)')
                
                # Create default admin user if not exists
                cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
                if cursor.fetchone()[0] == 0:
                    admin_user = User(
                        username='admin',
                        email='admin@heimnetz.local',
                        role=UserRole.ADMIN,
                        is_active=True,
                        is_verified=True
                    )
                    admin_user.set_password('admin123')
                    self.create_user(admin_user)
                
                conn.commit()
                logger.info("Unified database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def create_user(self, user: User) -> Optional[User]:
        """Create a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role, is_active, is_verified,
                                     created_at, two_factor_enabled, two_factor_secret, preferences, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.username, user.email, user.password_hash, user.role.value,
                    user.is_active, user.is_verified, user.created_at,
                    user.two_factor_enabled, user.two_factor_secret,
                    json.dumps(user.preferences), json.dumps(user.metadata)
                ))
                user.id = cursor.lastrowid
                conn.commit()
                return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_user(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_user(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def log_system_metrics(self, metrics: SystemMetrics) -> bool:
        """Log system metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, disk_usage,
                                              network_in, network_out, active_connections,
                                              requests_per_minute, response_time_avg, error_rate,
                                              uptime_seconds, system_load, temperature, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp, metrics.cpu_usage, metrics.memory_usage, metrics.disk_usage,
                    metrics.network_in, metrics.network_out, metrics.active_connections,
                    metrics.requests_per_minute, metrics.response_time_avg, metrics.error_rate,
                    metrics.uptime_seconds, metrics.system_load, metrics.temperature,
                    json.dumps(metrics.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging system metrics: {e}")
            return False
    
    def log_audit_event(self, audit_log: AuditLog) -> bool:
        """Log audit event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log (timestamp, user_id, session_id, action, result,
                                         resource, ip_address, user_agent, details, risk_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_log.timestamp, audit_log.user_id, audit_log.session_id,
                    audit_log.action.value, audit_log.result.value, audit_log.resource,
                    audit_log.ip_address, audit_log.user_agent, json.dumps(audit_log.details),
                    audit_log.risk_score, json.dumps(audit_log.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return False
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            role=UserRole(row[4]),
            is_active=bool(row[5]),
            is_verified=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            last_login=datetime.fromisoformat(row[8]) if row[8] else None,
            login_attempts=row[9] or 0,
            locked_until=datetime.fromisoformat(row[10]) if row[10] else None,
            two_factor_enabled=bool(row[11]),
            two_factor_secret=row[12] or "",
            preferences=json.loads(row[13]) if row[13] else {},
            metadata=json.loads(row[14]) if row[14] else {}
        )

# Global database instance
db = None

def init_db(db_path: str = "unified_heimnetz.db") -> UnifiedDatabase:
    """Initialize the global database instance"""
    global db
    if db is None:
        db = UnifiedDatabase(db_path)
    return db

def get_db() -> UnifiedDatabase:
    """Get the global database instance"""
    global db
    if db is None:
        db = init_db()
    return db

# Compatibility aliases for legacy code
DatabaseManager = UnifiedDatabase
User = User
SystemMetrics = SystemMetrics
AuditLog = AuditLog
