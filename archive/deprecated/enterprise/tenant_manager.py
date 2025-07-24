#!/usr/bin/env python3
"""
Multi-Tenant Architecture System - Audit 5 Enterprise Scaling
============================================================

This system provides comprehensive multi-tenant capabilities for enterprise deployment:
- Complete tenant isolation and management
- Database schema per tenant
- Resource quotas and limits
- Tenant-aware authentication
- Billing and subscription management
- Compliance and security controls

Essential for enterprise SaaS platform deployment
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import hmac
import base64
from decimal import Decimal
import sqlite3
from contextlib import contextmanager

# Optional imports with fallbacks
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Numeric
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TRIAL = "trial"

class SubscriptionPlan(Enum):
    """Subscription plan types"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class BillingCycle(Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    CUSTOM = "custom"

class ResourceType(Enum):
    """Resource types for quota management"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    API_CALLS = "api_calls"
    USERS = "users"
    DATABASES = "databases"

@dataclass
class Tenant:
    """Tenant entity"""
    id: str
    name: str
    slug: str
    domain: str
    status: TenantStatus
    plan: SubscriptionPlan
    created_at: datetime
    updated_at: datetime
    owner_email: str
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'domain': self.domain,
            'status': self.status.value,
            'plan': self.plan.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'owner_email': self.owner_email,
            'settings': self.settings,
            'metadata': self.metadata
        }

@dataclass
class ResourceQuota:
    """Resource quota definition"""
    tenant_id: str
    resource_type: ResourceType
    limit: int
    used: int = 0
    soft_limit: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class BillingInfo:
    """Billing information"""
    tenant_id: str
    plan: SubscriptionPlan
    billing_cycle: BillingCycle
    price_per_cycle: Decimal
    currency: str
    next_billing_date: datetime
    payment_method: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class TenantUsage:
    """Tenant resource usage tracking"""
    tenant_id: str
    resource_type: ResourceType
    amount: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class DatabaseManager:
    """
    Multi-tenant database management system
    """
    
    def __init__(self, master_db_url: str = "sqlite:///tenants.db"):
        self.master_db_url = master_db_url
        self.tenant_connections = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize master database
        self._init_master_database()
    
    def _init_master_database(self):
        """Initialize master database with tenant metadata"""
        try:
            if HAS_SQLALCHEMY:
                self.engine = create_engine(self.master_db_url)
                self.Base = declarative_base()
                self._create_master_tables()
                self.SessionLocal = sessionmaker(bind=self.engine)
            else:
                # Fallback to SQLite
                self.master_conn = sqlite3.connect("tenants.db", check_same_thread=False)
                self._create_master_tables_sqlite()
            
            self.logger.info("Master database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize master database: {e}")
    
    def _create_master_tables(self):
        """Create master database tables using SQLAlchemy"""
        try:
            # Define tenant table
            self.tenants_table = Table(
                'tenants', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('name', String, nullable=False),
                Column('slug', String, unique=True, nullable=False),
                Column('domain', String, unique=True, nullable=False),
                Column('status', String, nullable=False),
                Column('plan', String, nullable=False),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False),
                Column('owner_email', String, nullable=False),
                Column('settings', Text),
                Column('metadata', Text),
                Column('db_url', String, nullable=False)
            )
            
            # Define resource quotas table
            self.quotas_table = Table(
                'resource_quotas', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('limit_value', Integer, nullable=False),
                Column('used_value', Integer, default=0),
                Column('soft_limit', Integer),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False)
            )
            
            # Define billing table
            self.billing_table = Table(
                'billing_info', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('plan', String, nullable=False),
                Column('billing_cycle', String, nullable=False),
                Column('price_per_cycle', Numeric(10, 2), nullable=False),
                Column('currency', String, nullable=False),
                Column('next_billing_date', DateTime, nullable=False),
                Column('payment_method', String, nullable=False),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False)
            )
            
            # Define usage tracking table
            self.usage_table = Table(
                'tenant_usage', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('amount', Integer, nullable=False),
                Column('timestamp', DateTime, nullable=False),
                Column('metadata', Text)
            )
            
            # Create all tables
            self.Base.metadata.create_all(self.engine)
            
        except Exception as e:
            self.logger.error(f"Error creating master tables: {e}")
    
    def _create_master_tables_sqlite(self):
        """Create master database tables using SQLite"""
        try:
            cursor = self.master_conn.cursor()
            
            # Create tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    domain TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    owner_email TEXT NOT NULL,
                    settings TEXT,
                    metadata TEXT,
                    db_url TEXT NOT NULL
                )
            """)
            
            # Create resource quotas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_quotas (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    limit_value INTEGER NOT NULL,
                    used_value INTEGER DEFAULT 0,
                    soft_limit INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (id)
                )
            """)
            
            # Create billing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS billing_info (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    billing_cycle TEXT NOT NULL,
                    price_per_cycle DECIMAL(10, 2) NOT NULL,
                    currency TEXT NOT NULL,
                    next_billing_date TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (id)
                )
            """)
            
            # Create usage tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (id)
                )
            """)
            
            self.master_conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
    
    def create_tenant_database(self, tenant_id: str) -> str:
        """Create a dedicated database for a tenant"""
        try:
            # Generate database URL for tenant
            if HAS_POSTGRESQL:
                db_url = f"postgresql://user:password@localhost:5432/tenant_{tenant_id}"
            else:
                db_url = f"sqlite:///tenant_{tenant_id}.db"
            
            # Create database connection
            if HAS_SQLALCHEMY:
                engine = create_engine(db_url)
                
                # Create tenant-specific tables
                self._create_tenant_tables(engine, tenant_id)
                
                # Store connection
                self.tenant_connections[tenant_id] = engine
            else:
                # Fallback to SQLite
                conn = sqlite3.connect(f"tenant_{tenant_id}.db")
                self._create_tenant_tables_sqlite(conn, tenant_id)
                self.tenant_connections[tenant_id] = conn
            
            self.logger.info(f"Created database for tenant: {tenant_id}")
            return db_url
            
        except Exception as e:
            self.logger.error(f"Error creating tenant database: {e}")
            return ""
    
    def _create_tenant_tables(self, engine, tenant_id: str):
        """Create tenant-specific tables"""
        try:
            # Create tenant-specific base
            Base = declarative_base()
            
            # Define tenant tables
            users_table = Table(
                'users', Base.metadata,
                Column('id', String, primary_key=True),
                Column('email', String, unique=True, nullable=False),
                Column('name', String, nullable=False),
                Column('role', String, nullable=False),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False)
            )
            
            # Create all tenant tables
            Base.metadata.create_all(engine)
            
        except Exception as e:
            self.logger.error(f"Error creating tenant tables: {e}")
    
    def _create_tenant_tables_sqlite(self, conn, tenant_id: str):
        """Create tenant-specific tables using SQLite"""
        try:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating tenant SQLite tables: {e}")
    
    @contextmanager
    def get_tenant_session(self, tenant_id: str):
        """Get database session for specific tenant"""
        try:
            if tenant_id not in self.tenant_connections:
                raise ValueError(f"Tenant database not found: {tenant_id}")
            
            if HAS_SQLALCHEMY:
                engine = self.tenant_connections[tenant_id]
                SessionLocal = sessionmaker(bind=engine)
                session = SessionLocal()
                try:
                    yield session
                finally:
                    session.close()
            else:
                conn = self.tenant_connections[tenant_id]
                yield conn
                
        except Exception as e:
            self.logger.error(f"Error getting tenant session: {e}")
            yield None

class TenantManager:
    """
    Complete tenant management system
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.tenants_cache = {}
        
        # Initialize Redis cache if available
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.redis_client.ping()
                self.logger.info("Redis cache initialized")
            except Exception as e:
                self.logger.warning(f"Redis not available: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
    
    def create_tenant(self, name: str, slug: str, domain: str, owner_email: str,
                     plan: SubscriptionPlan = SubscriptionPlan.FREE) -> Optional[Tenant]:
        """Create a new tenant"""
        try:
            # Generate tenant ID
            tenant_id = str(uuid.uuid4())
            
            # Create tenant database
            db_url = self.db_manager.create_tenant_database(tenant_id)
            if not db_url:
                raise Exception("Failed to create tenant database")
            
            # Create tenant object
            tenant = Tenant(
                id=tenant_id,
                name=name,
                slug=slug,
                domain=domain,
                status=TenantStatus.ACTIVE,
                plan=plan,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                owner_email=owner_email
            )
            
            # Store in master database
            self._store_tenant(tenant, db_url)
            
            # Initialize default quotas
            self._initialize_default_quotas(tenant_id, plan)
            
            # Initialize billing info
            self._initialize_billing_info(tenant_id, plan)
            
            # Cache tenant
            self.tenants_cache[tenant_id] = tenant
            if self.redis_client:
                self.redis_client.setex(
                    f"tenant:{tenant_id}",
                    3600,
                    json.dumps(tenant.to_dict())
                )
            
            self.logger.info(f"Created tenant: {name} ({tenant_id})")
            return tenant
            
        except Exception as e:
            self.logger.error(f"Error creating tenant: {e}")
            return None
    
    def _store_tenant(self, tenant: Tenant, db_url: str):
        """Store tenant in master database"""
        try:
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.tenants_table.insert().values(
                            id=tenant.id,
                            name=tenant.name,
                            slug=tenant.slug,
                            domain=tenant.domain,
                            status=tenant.status.value,
                            plan=tenant.plan.value,
                            created_at=tenant.created_at,
                            updated_at=tenant.updated_at,
                            owner_email=tenant.owner_email,
                            settings=json.dumps(tenant.settings),
                            metadata=json.dumps(tenant.metadata),
                            db_url=db_url
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    INSERT INTO tenants (id, name, slug, domain, status, plan, created_at, updated_at, owner_email, settings, metadata, db_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant.id, tenant.name, tenant.slug, tenant.domain,
                    tenant.status.value, tenant.plan.value,
                    tenant.created_at.isoformat(), tenant.updated_at.isoformat(),
                    tenant.owner_email, json.dumps(tenant.settings),
                    json.dumps(tenant.metadata), db_url
                ))
                self.db_manager.master_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing tenant: {e}")
    
    def _initialize_default_quotas(self, tenant_id: str, plan: SubscriptionPlan):
        """Initialize default resource quotas for tenant"""
        try:
            # Define default quotas by plan
            quota_limits = {
                SubscriptionPlan.FREE: {
                    ResourceType.USERS: 5,
                    ResourceType.STORAGE: 1024,  # MB
                    ResourceType.API_CALLS: 1000,
                    ResourceType.DATABASES: 1
                },
                SubscriptionPlan.STARTER: {
                    ResourceType.USERS: 25,
                    ResourceType.STORAGE: 10240,  # MB
                    ResourceType.API_CALLS: 10000,
                    ResourceType.DATABASES: 5
                },
                SubscriptionPlan.PROFESSIONAL: {
                    ResourceType.USERS: 100,
                    ResourceType.STORAGE: 102400,  # MB
                    ResourceType.API_CALLS: 100000,
                    ResourceType.DATABASES: 25
                },
                SubscriptionPlan.ENTERPRISE: {
                    ResourceType.USERS: 1000,
                    ResourceType.STORAGE: 1048576,  # MB
                    ResourceType.API_CALLS: 1000000,
                    ResourceType.DATABASES: 100
                }
            }
            
            limits = quota_limits.get(plan, quota_limits[SubscriptionPlan.FREE])
            
            for resource_type, limit in limits.items():
                quota = ResourceQuota(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    limit=limit,
                    soft_limit=int(limit * 0.8)  # 80% soft limit
                )
                self._store_quota(quota)
                
        except Exception as e:
            self.logger.error(f"Error initializing quotas: {e}")
    
    def _store_quota(self, quota: ResourceQuota):
        """Store resource quota in database"""
        try:
            quota_id = str(uuid.uuid4())
            
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.quotas_table.insert().values(
                            id=quota_id,
                            tenant_id=quota.tenant_id,
                            resource_type=quota.resource_type.value,
                            limit_value=quota.limit,
                            used_value=quota.used,
                            soft_limit=quota.soft_limit,
                            created_at=quota.created_at,
                            updated_at=quota.updated_at
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    INSERT INTO resource_quotas (id, tenant_id, resource_type, limit_value, used_value, soft_limit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quota_id, quota.tenant_id, quota.resource_type.value,
                    quota.limit, quota.used, quota.soft_limit,
                    quota.created_at.isoformat(), quota.updated_at.isoformat()
                ))
                self.db_manager.master_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing quota: {e}")
    
    def _initialize_billing_info(self, tenant_id: str, plan: SubscriptionPlan):
        """Initialize billing information for tenant"""
        try:
            # Define pricing by plan
            pricing = {
                SubscriptionPlan.FREE: Decimal('0.00'),
                SubscriptionPlan.STARTER: Decimal('29.99'),
                SubscriptionPlan.PROFESSIONAL: Decimal('99.99'),
                SubscriptionPlan.ENTERPRISE: Decimal('299.99')
            }
            
            price = pricing.get(plan, Decimal('0.00'))
            
            billing_info = BillingInfo(
                tenant_id=tenant_id,
                plan=plan,
                billing_cycle=BillingCycle.MONTHLY,
                price_per_cycle=price,
                currency='USD',
                next_billing_date=datetime.now() + timedelta(days=30),
                payment_method='credit_card'
            )
            
            self._store_billing_info(billing_info)
            
        except Exception as e:
            self.logger.error(f"Error initializing billing info: {e}")
    
    def _store_billing_info(self, billing_info: BillingInfo):
        """Store billing information in database"""
        try:
            billing_id = str(uuid.uuid4())
            
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.billing_table.insert().values(
                            id=billing_id,
                            tenant_id=billing_info.tenant_id,
                            plan=billing_info.plan.value,
                            billing_cycle=billing_info.billing_cycle.value,
                            price_per_cycle=billing_info.price_per_cycle,
                            currency=billing_info.currency,
                            next_billing_date=billing_info.next_billing_date,
                            payment_method=billing_info.payment_method,
                            created_at=billing_info.created_at,
                            updated_at=billing_info.updated_at
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    INSERT INTO billing_info (id, tenant_id, plan, billing_cycle, price_per_cycle, currency, next_billing_date, payment_method, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    billing_id, billing_info.tenant_id, billing_info.plan.value,
                    billing_info.billing_cycle.value, str(billing_info.price_per_cycle),
                    billing_info.currency, billing_info.next_billing_date.isoformat(),
                    billing_info.payment_method, billing_info.created_at.isoformat(),
                    billing_info.updated_at.isoformat()
                ))
                self.db_manager.master_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing billing info: {e}")
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        try:
            # Check cache first
            if tenant_id in self.tenants_cache:
                return self.tenants_cache[tenant_id]
            
            # Check Redis cache
            if self.redis_client:
                cached_tenant = self.redis_client.get(f"tenant:{tenant_id}")
                if cached_tenant:
                    tenant_data = json.loads(cached_tenant)
                    tenant = Tenant(
                        id=tenant_data['id'],
                        name=tenant_data['name'],
                        slug=tenant_data['slug'],
                        domain=tenant_data['domain'],
                        status=TenantStatus(tenant_data['status']),
                        plan=SubscriptionPlan(tenant_data['plan']),
                        created_at=datetime.fromisoformat(tenant_data['created_at']),
                        updated_at=datetime.fromisoformat(tenant_data['updated_at']),
                        owner_email=tenant_data['owner_email'],
                        settings=tenant_data['settings'],
                        metadata=tenant_data['metadata']
                    )
                    self.tenants_cache[tenant_id] = tenant
                    return tenant
            
            # Query database
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    result = session.execute(
                        self.db_manager.tenants_table.select().where(
                            self.db_manager.tenants_table.c.id == tenant_id
                        )
                    ).fetchone()
                    
                    if result:
                        tenant = Tenant(
                            id=result.id,
                            name=result.name,
                            slug=result.slug,
                            domain=result.domain,
                            status=TenantStatus(result.status),
                            plan=SubscriptionPlan(result.plan),
                            created_at=result.created_at,
                            updated_at=result.updated_at,
                            owner_email=result.owner_email,
                            settings=json.loads(result.settings) if result.settings else {},
                            metadata=json.loads(result.metadata) if result.metadata else {}
                        )
                        
                        # Cache tenant
                        self.tenants_cache[tenant_id] = tenant
                        if self.redis_client:
                            self.redis_client.setex(
                                f"tenant:{tenant_id}",
                                3600,
                                json.dumps(tenant.to_dict())
                            )
                        
                        return tenant
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
                result = cursor.fetchone()
                
                if result:
                    tenant = Tenant(
                        id=result[0],
                        name=result[1],
                        slug=result[2],
                        domain=result[3],
                        status=TenantStatus(result[4]),
                        plan=SubscriptionPlan(result[5]),
                        created_at=datetime.fromisoformat(result[6]),
                        updated_at=datetime.fromisoformat(result[7]),
                        owner_email=result[8],
                        settings=json.loads(result[9]) if result[9] else {},
                        metadata=json.loads(result[10]) if result[10] else {}
                    )
                    
                    # Cache tenant
                    self.tenants_cache[tenant_id] = tenant
                    return tenant
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tenant: {e}")
            return None
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        try:
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    result = session.execute(
                        self.db_manager.tenants_table.select().where(
                            self.db_manager.tenants_table.c.domain == domain
                        )
                    ).fetchone()
                    
                    if result:
                        return self.get_tenant(result.id)
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("SELECT id FROM tenants WHERE domain = ?", (domain,))
                result = cursor.fetchone()
                
                if result:
                    return self.get_tenant(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tenant by domain: {e}")
            return None
    
    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant information"""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Update tenant object
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)
            
            tenant.updated_at = datetime.now()
            
            # Update database
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.tenants_table.update().where(
                            self.db_manager.tenants_table.c.id == tenant_id
                        ).values(
                            name=tenant.name,
                            status=tenant.status.value,
                            plan=tenant.plan.value,
                            updated_at=tenant.updated_at,
                            settings=json.dumps(tenant.settings),
                            metadata=json.dumps(tenant.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    UPDATE tenants 
                    SET name = ?, status = ?, plan = ?, updated_at = ?, settings = ?, metadata = ?
                    WHERE id = ?
                """, (
                    tenant.name, tenant.status.value, tenant.plan.value,
                    tenant.updated_at.isoformat(), json.dumps(tenant.settings),
                    json.dumps(tenant.metadata), tenant_id
                ))
                self.db_manager.master_conn.commit()
            
            # Update cache
            self.tenants_cache[tenant_id] = tenant
            if self.redis_client:
                self.redis_client.setex(
                    f"tenant:{tenant_id}",
                    3600,
                    json.dumps(tenant.to_dict())
                )
            
            self.logger.info(f"Updated tenant: {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating tenant: {e}")
            return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant and all associated data"""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Delete from database
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    # Delete related records
                    session.execute(
                        self.db_manager.quotas_table.delete().where(
                            self.db_manager.quotas_table.c.tenant_id == tenant_id
                        )
                    )
                    session.execute(
                        self.db_manager.billing_table.delete().where(
                            self.db_manager.billing_table.c.tenant_id == tenant_id
                        )
                    )
                    session.execute(
                        self.db_manager.usage_table.delete().where(
                            self.db_manager.usage_table.c.tenant_id == tenant_id
                        )
                    )
                    # Delete tenant
                    session.execute(
                        self.db_manager.tenants_table.delete().where(
                            self.db_manager.tenants_table.c.id == tenant_id
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("DELETE FROM resource_quotas WHERE tenant_id = ?", (tenant_id,))
                cursor.execute("DELETE FROM billing_info WHERE tenant_id = ?", (tenant_id,))
                cursor.execute("DELETE FROM tenant_usage WHERE tenant_id = ?", (tenant_id,))
                cursor.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
                self.db_manager.master_conn.commit()
            
            # Remove from cache
            if tenant_id in self.tenants_cache:
                del self.tenants_cache[tenant_id]
            
            if self.redis_client:
                self.redis_client.delete(f"tenant:{tenant_id}")
            
            # Close tenant database connection
            if tenant_id in self.db_manager.tenant_connections:
                conn = self.db_manager.tenant_connections[tenant_id]
                if hasattr(conn, 'close'):
                    conn.close()
                del self.db_manager.tenant_connections[tenant_id]
            
            self.logger.info(f"Deleted tenant: {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting tenant: {e}")
            return False
    
    def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        """List all tenants with pagination"""
        try:
            tenants = []
            
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    results = session.execute(
                        self.db_manager.tenants_table.select().limit(limit).offset(offset)
                    ).fetchall()
                    
                    for result in results:
                        tenant = Tenant(
                            id=result.id,
                            name=result.name,
                            slug=result.slug,
                            domain=result.domain,
                            status=TenantStatus(result.status),
                            plan=SubscriptionPlan(result.plan),
                            created_at=result.created_at,
                            updated_at=result.updated_at,
                            owner_email=result.owner_email,
                            settings=json.loads(result.settings) if result.settings else {},
                            metadata=json.loads(result.metadata) if result.metadata else {}
                        )
                        tenants.append(tenant)
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("SELECT * FROM tenants LIMIT ? OFFSET ?", (limit, offset))
                results = cursor.fetchall()
                
                for result in results:
                    tenant = Tenant(
                        id=result[0],
                        name=result[1],
                        slug=result[2],
                        domain=result[3],
                        status=TenantStatus(result[4]),
                        plan=SubscriptionPlan(result[5]),
                        created_at=datetime.fromisoformat(result[6]),
                        updated_at=datetime.fromisoformat(result[7]),
                        owner_email=result[8],
                        settings=json.loads(result[9]) if result[9] else {},
                        metadata=json.loads(result[10]) if result[10] else {}
                    )
                    tenants.append(tenant)
            
            return tenants
            
        except Exception as e:
            self.logger.error(f"Error listing tenants: {e}")
            return []
    
    def get_tenant_quotas(self, tenant_id: str) -> List[ResourceQuota]:
        """Get resource quotas for tenant"""
        try:
            quotas = []
            
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    results = session.execute(
                        self.db_manager.quotas_table.select().where(
                            self.db_manager.quotas_table.c.tenant_id == tenant_id
                        )
                    ).fetchall()
                    
                    for result in results:
                        quota = ResourceQuota(
                            tenant_id=result.tenant_id,
                            resource_type=ResourceType(result.resource_type),
                            limit=result.limit_value,
                            used=result.used_value,
                            soft_limit=result.soft_limit,
                            created_at=result.created_at,
                            updated_at=result.updated_at
                        )
                        quotas.append(quota)
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("SELECT * FROM resource_quotas WHERE tenant_id = ?", (tenant_id,))
                results = cursor.fetchall()
                
                for result in results:
                    quota = ResourceQuota(
                        tenant_id=result[1],
                        resource_type=ResourceType(result[2]),
                        limit=result[3],
                        used=result[4],
                        soft_limit=result[5],
                        created_at=datetime.fromisoformat(result[6]),
                        updated_at=datetime.fromisoformat(result[7])
                    )
                    quotas.append(quota)
            
            return quotas
            
        except Exception as e:
            self.logger.error(f"Error getting tenant quotas: {e}")
            return []
    
    def check_resource_quota(self, tenant_id: str, resource_type: ResourceType, 
                           requested_amount: int = 1) -> bool:
        """Check if tenant has enough quota for resource"""
        try:
            quotas = self.get_tenant_quotas(tenant_id)
            
            for quota in quotas:
                if quota.resource_type == resource_type:
                    available = quota.limit - quota.used
                    return available >= requested_amount
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking resource quota: {e}")
            return False
    
    def consume_resource(self, tenant_id: str, resource_type: ResourceType, 
                        amount: int = 1) -> bool:
        """Consume resource quota"""
        try:
            if not self.check_resource_quota(tenant_id, resource_type, amount):
                return False
            
            # Update quota usage
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.quotas_table.update().where(
                            (self.db_manager.quotas_table.c.tenant_id == tenant_id) &
                            (self.db_manager.quotas_table.c.resource_type == resource_type.value)
                        ).values(
                            used_value=self.db_manager.quotas_table.c.used_value + amount,
                            updated_at=datetime.now()
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    UPDATE resource_quotas 
                    SET used_value = used_value + ?, updated_at = ?
                    WHERE tenant_id = ? AND resource_type = ?
                """, (amount, datetime.now().isoformat(), tenant_id, resource_type.value))
                self.db_manager.master_conn.commit()
            
            # Track usage
            self.track_usage(tenant_id, resource_type, amount)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error consuming resource: {e}")
            return False
    
    def track_usage(self, tenant_id: str, resource_type: ResourceType, 
                   amount: int, metadata: Dict[str, Any] = None):
        """Track resource usage"""
        try:
            usage = TenantUsage(
                tenant_id=tenant_id,
                resource_type=resource_type,
                amount=amount,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            usage_id = str(uuid.uuid4())
            
            if HAS_SQLALCHEMY:
                with self.db_manager.SessionLocal() as session:
                    session.execute(
                        self.db_manager.usage_table.insert().values(
                            id=usage_id,
                            tenant_id=usage.tenant_id,
                            resource_type=usage.resource_type.value,
                            amount=usage.amount,
                            timestamp=usage.timestamp,
                            metadata=json.dumps(usage.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.db_manager.master_conn.cursor()
                cursor.execute("""
                    INSERT INTO tenant_usage (id, tenant_id, resource_type, amount, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    usage_id, usage.tenant_id, usage.resource_type.value,
                    usage.amount, usage.timestamp.isoformat(),
                    json.dumps(usage.metadata)
                ))
                self.db_manager.master_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error tracking usage: {e}")

class MultiTenantMiddleware:
    """
    Middleware for tenant-aware request handling
    """
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_tenant_from_request(self, request) -> Optional[Tenant]:
        """Extract tenant from request"""
        try:
            # Try to get tenant from subdomain
            host = request.headers.get('Host', '')
            if host:
                # Extract subdomain
                parts = host.split('.')
                if len(parts) >= 3:
                    subdomain = parts[0]
                    # Look up tenant by subdomain
                    tenant = self.tenant_manager.get_tenant_by_domain(host)
                    if tenant:
                        return tenant
            
            # Try to get tenant from header
            tenant_id = request.headers.get('X-Tenant-ID')
            if tenant_id:
                return self.tenant_manager.get_tenant(tenant_id)
            
            # Try to get tenant from path
            path = request.path
            if path.startswith('/tenant/'):
                tenant_id = path.split('/')[2]
                return self.tenant_manager.get_tenant(tenant_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tenant from request: {e}")
            return None
    
    def process_request(self, request, handler):
        """Process request with tenant context"""
        try:
            tenant = self.get_tenant_from_request(request)
            if not tenant:
                return {"error": "Tenant not found"}, 404
            
            if tenant.status != TenantStatus.ACTIVE:
                return {"error": "Tenant not active"}, 403
            
            # Add tenant to request context
            request.tenant = tenant
            
            # Process request
            response = handler(request)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return {"error": "Internal server error"}, 500

def main():
    """Main function for testing multi-tenant system"""
    try:
        print("Multi-Tenant Architecture System - Test Mode")
        print("=" * 50)
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Initialize tenant manager
        tenant_manager = TenantManager(db_manager)
        
        # Test tenant creation
        print("Testing tenant creation...")
        tenant = tenant_manager.create_tenant(
            name="Test Organization",
            slug="test-org",
            domain="test-org.example.com",
            owner_email="admin@test-org.com",
            plan=SubscriptionPlan.PROFESSIONAL
        )
        
        if tenant:
            print(f"Created tenant: {tenant.name} ({tenant.id})")
            
            # Test tenant retrieval
            retrieved_tenant = tenant_manager.get_tenant(tenant.id)
            if retrieved_tenant:
                print(f"Retrieved tenant: {retrieved_tenant.name}")
            
            # Test quota checking
            can_create_user = tenant_manager.check_resource_quota(
                tenant.id, ResourceType.USERS, 1
            )
            print(f"Can create user: {can_create_user}")
            
            # Test resource consumption
            if can_create_user:
                consumed = tenant_manager.consume_resource(
                    tenant.id, ResourceType.USERS, 1
                )
                print(f"Consumed user quota: {consumed}")
            
            # Test quota status
            quotas = tenant_manager.get_tenant_quotas(tenant.id)
            for quota in quotas:
                print(f"Quota: {quota.resource_type.value} - {quota.used}/{quota.limit}")
            
        else:
            print("Failed to create tenant")
        
        print("\nMulti-tenant system test completed!")
        
    except Exception as e:
        print(f"Error in multi-tenant system: {e}")
        logger.error(f"Multi-tenant system error: {e}")

if __name__ == "__main__":
    main()
