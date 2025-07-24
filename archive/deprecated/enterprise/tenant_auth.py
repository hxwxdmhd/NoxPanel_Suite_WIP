#!/usr/bin/env python3
"""
Tenant Authentication & Authorization System - Audit 5 Enterprise Scaling
========================================================================

This system provides comprehensive tenant-aware authentication and authorization:
- Multi-tenant user management with complete isolation
- Role-based access control (RBAC) per tenant
- JWT token management with tenant context
- SSO integration capabilities
- API key management per tenant
- Permission-based resource access
- Audit logging for compliance

Essential for enterprise multi-tenant security
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import hmac
import base64
import secrets
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from tenant_manager import TenantManager, Tenant, TenantStatus
except ImportError:
    TenantManager = None
    Tenant = None
    TenantStatus = None

# Optional imports with fallbacks
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role types"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(Enum):
    """System permissions"""
    # Tenant management
    TENANT_CREATE = "tenant:create"
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"
    
    # Role management
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_ASSIGN = "role:assign"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    
    # Data access
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    
    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # Billing
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    BILLING_ADMIN = "billing:admin"

class AuthTokenType(Enum):
    """Authentication token types"""
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    API_KEY = "api_key"
    INVITATION = "invitation"
    RESET_PASSWORD = "reset_password"

@dataclass
class User:
    """User entity"""
    id: str
    tenant_id: str
    email: str
    name: str
    role: UserRole
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'settings': self.settings,
            'metadata': self.metadata
        }

@dataclass
class Role:
    """Role entity"""
    id: str
    tenant_id: str
    name: str
    description: str
    permissions: Set[Permission]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.value for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class AuthToken:
    """Authentication token"""
    id: str
    user_id: str
    tenant_id: str
    token_type: AuthTokenType
    token: str
    expires_at: datetime
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIKey:
    """API key for tenant"""
    id: str
    tenant_id: str
    user_id: str
    name: str
    key: str
    permissions: Set[Permission]
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class LoginAttempt:
    """Login attempt tracking"""
    id: str
    tenant_id: str
    email: str
    ip_address: str
    user_agent: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class TenantAuthManager:
    """
    Tenant-aware authentication and authorization manager
    """
    
    def __init__(self, tenant_manager: TenantManager = None, db_url: str = "sqlite:///auth.db"):
        self.tenant_manager = tenant_manager
        self.db_url = db_url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # JWT configuration
        self.jwt_secret = os.environ.get('JWT_SECRET', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=30)
        
        # Cache for users and roles
        self.users_cache = {}
        self.roles_cache = {}
        
        # Initialize database
        self._init_database()
        
        # Initialize Redis cache if available
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
                self.redis_client.ping()
                self.logger.info("Redis cache initialized for auth")
            except Exception as e:
                self.logger.warning(f"Redis not available for auth: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
        
        # Initialize default roles
        self._init_default_roles()
    
    def _init_database(self):
        """Initialize authentication database"""
        try:
            if HAS_SQLALCHEMY:
                self.engine = create_engine(self.db_url)
                self.Base = declarative_base()
                self._create_auth_tables()
                self.SessionLocal = sessionmaker(bind=self.engine)
            else:
                # Fallback to SQLite
                import sqlite3
                self.auth_conn = sqlite3.connect("auth.db", check_same_thread=False)
                self._create_auth_tables_sqlite()
            
            self.logger.info("Authentication database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize auth database: {e}")
    
    def _create_auth_tables(self):
        """Create authentication tables using SQLAlchemy"""
        try:
            # Users table
            self.users_table = Table(
                'users', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('email', String, nullable=False),
                Column('name', String, nullable=False),
                Column('role', String, nullable=False),
                Column('password_hash', String, nullable=False),
                Column('is_active', Boolean, default=True),
                Column('is_verified', Boolean, default=False),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False),
                Column('last_login', DateTime),
                Column('settings', Text),
                Column('metadata', Text)
            )
            
            # Roles table
            self.roles_table = Table(
                'roles', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('name', String, nullable=False),
                Column('description', String, nullable=False),
                Column('permissions', Text, nullable=False),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False)
            )
            
            # Auth tokens table
            self.auth_tokens_table = Table(
                'auth_tokens', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('user_id', String, nullable=False),
                Column('tenant_id', String, nullable=False),
                Column('token_type', String, nullable=False),
                Column('token', String, nullable=False),
                Column('expires_at', DateTime, nullable=False),
                Column('is_active', Boolean, default=True),
                Column('created_at', DateTime, nullable=False),
                Column('metadata', Text)
            )
            
            # API keys table
            self.api_keys_table = Table(
                'api_keys', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('user_id', String, nullable=False),
                Column('name', String, nullable=False),
                Column('key', String, nullable=False),
                Column('permissions', Text, nullable=False),
                Column('expires_at', DateTime),
                Column('is_active', Boolean, default=True),
                Column('created_at', DateTime, nullable=False),
                Column('last_used', DateTime),
                Column('usage_count', Integer, default=0)
            )
            
            # Login attempts table
            self.login_attempts_table = Table(
                'login_attempts', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('email', String, nullable=False),
                Column('ip_address', String, nullable=False),
                Column('user_agent', String, nullable=False),
                Column('success', Boolean, nullable=False),
                Column('timestamp', DateTime, nullable=False),
                Column('metadata', Text)
            )
            
            # Create all tables
            self.Base.metadata.create_all(self.engine)
            
        except Exception as e:
            self.logger.error(f"Error creating auth tables: {e}")
    
    def _create_auth_tables_sqlite(self):
        """Create authentication tables using SQLite"""
        try:
            cursor = self.auth_conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login TEXT,
                    settings TEXT,
                    metadata TEXT,
                    UNIQUE(tenant_id, email)
                )
            """)
            
            # Roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(tenant_id, name)
                )
            """)
            
            # Auth tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # API keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    key TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            # Login attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            self.auth_conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating SQLite auth tables: {e}")
    
    def _init_default_roles(self):
        """Initialize default roles for each tenant"""
        try:
            # Default role permissions
            default_roles = {
                UserRole.SUPER_ADMIN: {
                    'description': 'Super administrator with full system access',
                    'permissions': set(Permission)
                },
                UserRole.TENANT_ADMIN: {
                    'description': 'Tenant administrator with full tenant access',
                    'permissions': {
                        Permission.TENANT_READ, Permission.TENANT_UPDATE,
                        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
                        Permission.ROLE_CREATE, Permission.ROLE_READ, Permission.ROLE_UPDATE, Permission.ROLE_DELETE,
                        Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_DELETE,
                        Permission.API_READ, Permission.API_WRITE,
                        Permission.BILLING_READ, Permission.BILLING_WRITE
                    }
                },
                UserRole.ADMIN: {
                    'description': 'Administrator with user and data management access',
                    'permissions': {
                        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
                        Permission.ROLE_READ, Permission.ROLE_ASSIGN,
                        Permission.DATA_READ, Permission.DATA_WRITE,
                        Permission.API_READ, Permission.API_WRITE
                    }
                },
                UserRole.MANAGER: {
                    'description': 'Manager with limited user and data access',
                    'permissions': {
                        Permission.USER_READ, Permission.USER_UPDATE,
                        Permission.DATA_READ, Permission.DATA_WRITE,
                        Permission.API_READ
                    }
                },
                UserRole.USER: {
                    'description': 'Regular user with basic access',
                    'permissions': {
                        Permission.USER_READ, Permission.DATA_READ, Permission.API_READ
                    }
                },
                UserRole.VIEWER: {
                    'description': 'Viewer with read-only access',
                    'permissions': {
                        Permission.DATA_READ
                    }
                },
                UserRole.GUEST: {
                    'description': 'Guest with minimal access',
                    'permissions': set()
                }
            }
            
            self.default_roles = default_roles
            self.logger.info("Default roles initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing default roles: {e}")
    
    def create_user(self, tenant_id: str, email: str, name: str, password: str,
                   role: UserRole = UserRole.USER) -> Optional[User]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(tenant_id, email)
            if existing_user:
                self.logger.warning(f"User already exists: {email}")
                return None
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Create user object
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=email,
                name=name,
                role=role,
                password_hash=password_hash
            )
            
            # Store user in database
            self._store_user(user)
            
            # Cache user
            self.users_cache[f"{tenant_id}:{user_id}"] = user
            
            self.logger.info(f"Created user: {email} ({user_id})")
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return None
    
    def _store_user(self, user: User):
        """Store user in database"""
        try:
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.users_table.insert().values(
                            id=user.id,
                            tenant_id=user.tenant_id,
                            email=user.email,
                            name=user.name,
                            role=user.role.value,
                            password_hash=user.password_hash,
                            is_active=user.is_active,
                            is_verified=user.is_verified,
                            created_at=user.created_at,
                            updated_at=user.updated_at,
                            last_login=user.last_login,
                            settings=json.dumps(user.settings),
                            metadata=json.dumps(user.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute("""
                    INSERT INTO users (id, tenant_id, email, name, role, password_hash, is_active, is_verified, created_at, updated_at, last_login, settings, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.id, user.tenant_id, user.email, user.name,
                    user.role.value, user.password_hash, user.is_active,
                    user.is_verified, user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    json.dumps(user.settings), json.dumps(user.metadata)
                ))
                self.auth_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing user: {e}")
    
    def get_user(self, tenant_id: str, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Check cache first
            cache_key = f"{tenant_id}:{user_id}"
            if cache_key in self.users_cache:
                return self.users_cache[cache_key]
            
            # Query database
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    result = session.execute(
                        self.users_table.select().where(
                            (self.users_table.c.tenant_id == tenant_id) &
                            (self.users_table.c.id == user_id)
                        )
                    ).fetchone()
                    
                    if result:
                        user = User(
                            id=result.id,
                            tenant_id=result.tenant_id,
                            email=result.email,
                            name=result.name,
                            role=UserRole(result.role),
                            password_hash=result.password_hash,
                            is_active=result.is_active,
                            is_verified=result.is_verified,
                            created_at=result.created_at,
                            updated_at=result.updated_at,
                            last_login=result.last_login,
                            settings=json.loads(result.settings) if result.settings else {},
                            metadata=json.loads(result.metadata) if result.metadata else {}
                        )
                        
                        # Cache user
                        self.users_cache[cache_key] = user
                        return user
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE tenant_id = ? AND id = ?",
                    (tenant_id, user_id)
                )
                result = cursor.fetchone()
                
                if result:
                    user = User(
                        id=result[0],
                        tenant_id=result[1],
                        email=result[2],
                        name=result[3],
                        role=UserRole(result[4]),
                        password_hash=result[5],
                        is_active=bool(result[6]),
                        is_verified=bool(result[7]),
                        created_at=datetime.fromisoformat(result[8]),
                        updated_at=datetime.fromisoformat(result[9]),
                        last_login=datetime.fromisoformat(result[10]) if result[10] else None,
                        settings=json.loads(result[11]) if result[11] else {},
                        metadata=json.loads(result[12]) if result[12] else {}
                    )
                    
                    # Cache user
                    self.users_cache[cache_key] = user
                    return user
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    result = session.execute(
                        self.users_table.select().where(
                            (self.users_table.c.tenant_id == tenant_id) &
                            (self.users_table.c.email == email)
                        )
                    ).fetchone()
                    
                    if result:
                        return self.get_user(tenant_id, result.id)
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE tenant_id = ? AND email = ?",
                    (tenant_id, email)
                )
                result = cursor.fetchone()
                
                if result:
                    return self.get_user(tenant_id, result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            return None
    
    def authenticate_user(self, tenant_id: str, email: str, password: str,
                         ip_address: str = "", user_agent: str = "") -> Optional[User]:
        """Authenticate user with credentials"""
        try:
            # Get user
            user = self.get_user_by_email(tenant_id, email)
            
            # Record login attempt
            self.record_login_attempt(tenant_id, email, ip_address, user_agent, user is not None)
            
            if not user:
                return None
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Inactive user login attempt: {email}")
                return None
            
            # Check password
            if not check_password_hash(user.password_hash, password):
                self.logger.warning(f"Invalid password for user: {email}")
                return None
            
            # Update last login
            user.last_login = datetime.now()
            self.update_user(user)
            
            self.logger.info(f"User authenticated: {email}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error authenticating user: {e}")
            return None
    
    def record_login_attempt(self, tenant_id: str, email: str, ip_address: str,
                           user_agent: str, success: bool):
        """Record login attempt"""
        try:
            attempt = LoginAttempt(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.login_attempts_table.insert().values(
                            id=attempt.id,
                            tenant_id=attempt.tenant_id,
                            email=attempt.email,
                            ip_address=attempt.ip_address,
                            user_agent=attempt.user_agent,
                            success=attempt.success,
                            timestamp=attempt.timestamp,
                            metadata=json.dumps(attempt.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute("""
                    INSERT INTO login_attempts (id, tenant_id, email, ip_address, user_agent, success, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attempt.id, attempt.tenant_id, attempt.email,
                    attempt.ip_address, attempt.user_agent, attempt.success,
                    attempt.timestamp.isoformat(), json.dumps(attempt.metadata)
                ))
                self.auth_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error recording login attempt: {e}")
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        try:
            now = datetime.utcnow()
            
            # Generate access token
            access_payload = {
                'user_id': user.id,
                'tenant_id': user.tenant_id,
                'email': user.email,
                'role': user.role.value,
                'type': 'access',
                'iat': now,
                'exp': now + self.access_token_expire
            }
            
            access_token = jwt.encode(
                access_payload, 
                self.jwt_secret, 
                algorithm=self.jwt_algorithm
            )
            
            # Generate refresh token
            refresh_payload = {
                'user_id': user.id,
                'tenant_id': user.tenant_id,
                'type': 'refresh',
                'iat': now,
                'exp': now + self.refresh_token_expire
            }
            
            refresh_token = jwt.encode(
                refresh_payload,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            # Store tokens in database
            self._store_token(
                user.id, user.tenant_id, AuthTokenType.ACCESS_TOKEN,
                access_token, now + self.access_token_expire
            )
            
            self._store_token(
                user.id, user.tenant_id, AuthTokenType.REFRESH_TOKEN,
                refresh_token, now + self.refresh_token_expire
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': int(self.access_token_expire.total_seconds())
            }
            
        except Exception as e:
            self.logger.error(f"Error generating tokens: {e}")
            return {}
    
    def _store_token(self, user_id: str, tenant_id: str, token_type: AuthTokenType,
                    token: str, expires_at: datetime):
        """Store authentication token"""
        try:
            auth_token = AuthToken(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                token_type=token_type,
                token=token,
                expires_at=expires_at
            )
            
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.auth_tokens_table.insert().values(
                            id=auth_token.id,
                            user_id=auth_token.user_id,
                            tenant_id=auth_token.tenant_id,
                            token_type=auth_token.token_type.value,
                            token=auth_token.token,
                            expires_at=auth_token.expires_at,
                            is_active=auth_token.is_active,
                            created_at=auth_token.created_at,
                            metadata=json.dumps(auth_token.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute("""
                    INSERT INTO auth_tokens (id, user_id, tenant_id, token_type, token, expires_at, is_active, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    auth_token.id, auth_token.user_id, auth_token.tenant_id,
                    auth_token.token_type.value, auth_token.token,
                    auth_token.expires_at.isoformat(), auth_token.is_active,
                    auth_token.created_at.isoformat(), json.dumps(auth_token.metadata)
                ))
                self.auth_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing token: {e}")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check if token is in database and active
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    result = session.execute(
                        self.auth_tokens_table.select().where(
                            (self.auth_tokens_table.c.token == token) &
                            (self.auth_tokens_table.c.is_active == True)
                        )
                    ).fetchone()
                    
                    if not result:
                        return None
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute(
                    "SELECT * FROM auth_tokens WHERE token = ? AND is_active = 1",
                    (token,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid token")
            return None
        except Exception as e:
            self.logger.error(f"Error verifying token: {e}")
            return None
    
    def create_api_key(self, tenant_id: str, user_id: str, name: str,
                      permissions: Set[Permission] = None,
                      expires_at: datetime = None) -> Optional[APIKey]:
        """Create API key for tenant"""
        try:
            # Generate API key
            api_key = f"hk_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(40))}"
            
            # Default permissions
            if permissions is None:
                permissions = {Permission.API_READ}
            
            # Create API key object
            api_key_obj = APIKey(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                name=name,
                key=api_key,
                permissions=permissions,
                expires_at=expires_at
            )
            
            # Store in database
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.api_keys_table.insert().values(
                            id=api_key_obj.id,
                            tenant_id=api_key_obj.tenant_id,
                            user_id=api_key_obj.user_id,
                            name=api_key_obj.name,
                            key=api_key_obj.key,
                            permissions=json.dumps([p.value for p in api_key_obj.permissions]),
                            expires_at=api_key_obj.expires_at,
                            is_active=api_key_obj.is_active,
                            created_at=api_key_obj.created_at,
                            last_used=api_key_obj.last_used,
                            usage_count=api_key_obj.usage_count
                        )
                    )
                    session.commit()
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute("""
                    INSERT INTO api_keys (id, tenant_id, user_id, name, key, permissions, expires_at, is_active, created_at, last_used, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    api_key_obj.id, api_key_obj.tenant_id, api_key_obj.user_id,
                    api_key_obj.name, api_key_obj.key,
                    json.dumps([p.value for p in api_key_obj.permissions]),
                    api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                    api_key_obj.is_active, api_key_obj.created_at.isoformat(),
                    api_key_obj.last_used.isoformat() if api_key_obj.last_used else None,
                    api_key_obj.usage_count
                ))
                self.auth_conn.commit()
            
            self.logger.info(f"Created API key: {name} for tenant {tenant_id}")
            return api_key_obj
            
        except Exception as e:
            self.logger.error(f"Error creating API key: {e}")
            return None
    
    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key"""
        try:
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    result = session.execute(
                        self.api_keys_table.select().where(
                            (self.api_keys_table.c.key == api_key) &
                            (self.api_keys_table.c.is_active == True)
                        )
                    ).fetchone()
                    
                    if result:
                        # Check expiration
                        if result.expires_at and datetime.now() > result.expires_at:
                            return None
                        
                        # Update usage
                        session.execute(
                            self.api_keys_table.update().where(
                                self.api_keys_table.c.id == result.id
                            ).values(
                                last_used=datetime.now(),
                                usage_count=self.api_keys_table.c.usage_count + 1
                            )
                        )
                        session.commit()
                        
                        return APIKey(
                            id=result.id,
                            tenant_id=result.tenant_id,
                            user_id=result.user_id,
                            name=result.name,
                            key=result.key,
                            permissions=set(Permission(p) for p in json.loads(result.permissions)),
                            expires_at=result.expires_at,
                            is_active=result.is_active,
                            created_at=result.created_at,
                            last_used=result.last_used,
                            usage_count=result.usage_count
                        )
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute(
                    "SELECT * FROM api_keys WHERE key = ? AND is_active = 1",
                    (api_key,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Check expiration
                    if result[7] and datetime.now() > datetime.fromisoformat(result[7]):
                        return None
                    
                    # Update usage
                    cursor.execute("""
                        UPDATE api_keys 
                        SET last_used = ?, usage_count = usage_count + 1
                        WHERE id = ?
                    """, (datetime.now().isoformat(), result[0]))
                    self.auth_conn.commit()
                    
                    return APIKey(
                        id=result[0],
                        tenant_id=result[1],
                        user_id=result[2],
                        name=result[3],
                        key=result[4],
                        permissions=set(Permission(p) for p in json.loads(result[5])),
                        expires_at=datetime.fromisoformat(result[7]) if result[7] else None,
                        is_active=bool(result[8]),
                        created_at=datetime.fromisoformat(result[9]),
                        last_used=datetime.fromisoformat(result[10]) if result[10] else None,
                        usage_count=result[11]
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error verifying API key: {e}")
            return None
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        try:
            # Get user's role permissions
            role_perms = self.default_roles.get(user.role, {}).get('permissions', set())
            
            # Check if user has permission
            return permission in role_perms
            
        except Exception as e:
            self.logger.error(f"Error checking permission: {e}")
            return False
    
    def update_user(self, user: User) -> bool:
        """Update user information"""
        try:
            user.updated_at = datetime.now()
            
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.users_table.update().where(
                            self.users_table.c.id == user.id
                        ).values(
                            name=user.name,
                            role=user.role.value,
                            is_active=user.is_active,
                            is_verified=user.is_verified,
                            updated_at=user.updated_at,
                            last_login=user.last_login,
                            settings=json.dumps(user.settings),
                            metadata=json.dumps(user.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.auth_conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET name = ?, role = ?, is_active = ?, is_verified = ?, 
                        updated_at = ?, last_login = ?, settings = ?, metadata = ?
                    WHERE id = ?
                """, (
                    user.name, user.role.value, user.is_active, user.is_verified,
                    user.updated_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    json.dumps(user.settings), json.dumps(user.metadata),
                    user.id
                ))
                self.auth_conn.commit()
            
            # Update cache
            cache_key = f"{user.tenant_id}:{user.id}"
            self.users_cache[cache_key] = user
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            return False

def require_auth(tenant_auth: TenantAuthManager):
    """Decorator to require authentication"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get token from request headers
                auth_header = kwargs.get('auth_header', '')
                if not auth_header.startswith('Bearer '):
                    return {"error": "Authorization required"}, 401
                
                token = auth_header.split(' ')[1]
                payload = tenant_auth.verify_token(token)
                
                if not payload:
                    return {"error": "Invalid token"}, 401
                
                # Get user
                user = tenant_auth.get_user(payload['tenant_id'], payload['user_id'])
                if not user:
                    return {"error": "User not found"}, 404
                
                # Add user to kwargs
                kwargs['current_user'] = user
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Auth decorator error: {e}")
                return {"error": "Authentication error"}, 500
        
        return wrapper
    return decorator

def require_permission(tenant_auth: TenantAuthManager, permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                current_user = kwargs.get('current_user')
                if not current_user:
                    return {"error": "Authentication required"}, 401
                
                if not tenant_auth.check_permission(current_user, permission):
                    return {"error": "Insufficient permissions"}, 403
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Permission decorator error: {e}")
                return {"error": "Permission error"}, 500
        
        return wrapper
    return decorator

def main():
    """Main function for testing tenant auth system"""
    try:
        print("Tenant Authentication System - Test Mode")
        print("=" * 50)
        
        # Initialize tenant auth manager
        tenant_auth = TenantAuthManager()
        
        # Test tenant creation (mock tenant)
        tenant_id = "test-tenant-123"
        
        # Test user creation
        print("Testing user creation...")
        user = tenant_auth.create_user(
            tenant_id=tenant_id,
            email="admin@test.com",
            name="Test Admin",
            password="securepassword123",
            role=UserRole.TENANT_ADMIN
        )
        
        if user:
            print(f"Created user: {user.name} ({user.id})")
            
            # Test user authentication
            print("Testing user authentication...")
            auth_user = tenant_auth.authenticate_user(
                tenant_id=tenant_id,
                email="admin@test.com",
                password="securepassword123"
            )
            
            if auth_user:
                print(f"User authenticated: {auth_user.email}")
                
                # Test token generation
                print("Testing token generation...")
                tokens = tenant_auth.generate_tokens(auth_user)
                
                if tokens:
                    print(f"Generated tokens: {list(tokens.keys())}")
                    
                    # Test token verification
                    print("Testing token verification...")
                    payload = tenant_auth.verify_token(tokens['access_token'])
                    
                    if payload:
                        print(f"Token verified: {payload['email']}")
                        
                        # Test permission checking
                        print("Testing permission checking...")
                        can_read = tenant_auth.check_permission(auth_user, Permission.USER_READ)
                        can_delete = tenant_auth.check_permission(auth_user, Permission.TENANT_DELETE)
                        print(f"Can read users: {can_read}")
                        print(f"Can delete tenant: {can_delete}")
                        
                        # Test API key creation
                        print("Testing API key creation...")
                        api_key = tenant_auth.create_api_key(
                            tenant_id=tenant_id,
                            user_id=auth_user.id,
                            name="Test API Key",
                            permissions={Permission.API_READ, Permission.DATA_READ}
                        )
                        
                        if api_key:
                            print(f"Created API key: {api_key.name}")
                            
                            # Test API key verification
                            print("Testing API key verification...")
                            verified_key = tenant_auth.verify_api_key(api_key.key)
                            
                            if verified_key:
                                print(f"API key verified: {verified_key.name}")
                            else:
                                print("API key verification failed")
                        else:
                            print("API key creation failed")
                    else:
                        print("Token verification failed")
                else:
                    print("Token generation failed")
            else:
                print("User authentication failed")
        else:
            print("User creation failed")
        
        print("\nTenant authentication system test completed!")
        
    except Exception as e:
        print(f"Error in tenant auth system: {e}")
        logger.error(f"Tenant auth system error: {e}")

if __name__ == "__main__":
    main()
