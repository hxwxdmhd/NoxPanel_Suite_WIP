#!/usr/bin/env python3
"""
Resource Management & Quota System - Audit 5 Enterprise Scaling
================================================================

This system provides comprehensive resource management and quota enforcement:
- Real-time resource monitoring and tracking
- Flexible quota policies and limits
- Automated resource allocation and scaling
- Usage-based billing and cost tracking
- Performance monitoring and optimization
- Resource alerts and notifications
- Compliance reporting and auditing

Essential for enterprise multi-tenant resource control
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import sqlite3
from contextlib import contextmanager
from collections import defaultdict
import psutil
import platform

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from tenant_manager import TenantManager, Tenant, ResourceType, ResourceQuota
    from tenant_auth import TenantAuthManager, User
except ImportError:
    TenantManager = None
    Tenant = None
    ResourceType = None
    ResourceQuota = None
    TenantAuthManager = None
    User = None

# Optional imports with fallbacks
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Numeric, Float
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False

try:
    import boto3
    HAS_AWS = True
except ImportError:
    HAS_AWS = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceStatus(Enum):
    """Resource status enumeration"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"

class AlertType(Enum):
    """Alert type enumeration"""
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    PERFORMANCE_DEGRADED = "performance_degraded"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    BILLING_THRESHOLD = "billing_threshold"

class ResourceCategory(Enum):
    """Resource category enumeration"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    APPLICATION = "application"
    CUSTOM = "custom"

class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class ResourceMetric:
    """Resource metric data"""
    id: str
    tenant_id: str
    resource_type: ResourceType
    category: ResourceCategory
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QuotaPolicy:
    """Quota policy definition"""
    id: str
    tenant_id: str
    resource_type: ResourceType
    hard_limit: int
    soft_limit: int
    warning_threshold: float  # Percentage
    critical_threshold: float  # Percentage
    auto_scale: bool = False
    auto_scale_factor: float = 1.5
    billing_enabled: bool = True
    cost_per_unit: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ResourceAllocation:
    """Resource allocation record"""
    id: str
    tenant_id: str
    user_id: str
    resource_type: ResourceType
    amount: int
    allocated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceAlert:
    """Resource alert"""
    id: str
    tenant_id: str
    alert_type: AlertType
    resource_type: ResourceType
    current_usage: int
    limit: int
    threshold: float
    message: str
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class BillingRecord:
    """Billing record for resource usage"""
    id: str
    tenant_id: str
    resource_type: ResourceType
    usage_amount: int
    unit_cost: float
    total_cost: float
    billing_period_start: datetime
    billing_period_end: datetime
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class ResourceMonitor:
    """
    Real-time resource monitoring system
    """
    
    def __init__(self, db_url: str = "sqlite:///resources.db"):
        self.db_url = db_url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.monitoring_active = False
        self.monitor_thread = None
        self.metrics_cache = {}
        
        # Initialize database
        self._init_database()
        
        # Initialize Redis cache if available
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=2)
                self.redis_client.ping()
                self.logger.info("Redis cache initialized for resource monitoring")
            except Exception as e:
                self.logger.warning(f"Redis not available for resource monitoring: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
        
        # Initialize Docker client if available
        if HAS_DOCKER:
            try:
                self.docker_client = docker.from_env()
                self.logger.info("Docker client initialized")
            except Exception as e:
                self.logger.warning(f"Docker not available: {e}")
                self.docker_client = None
        else:
            self.docker_client = None
    
    def _init_database(self):
        """Initialize resource monitoring database"""
        try:
            if HAS_SQLALCHEMY:
                self.engine = create_engine(self.db_url)
                self.Base = declarative_base()
                self._create_resource_tables()
                self.SessionLocal = sessionmaker(bind=self.engine)
            else:
                # Fallback to SQLite
                self.resource_conn = sqlite3.connect("resources.db", check_same_thread=False)
                self._create_resource_tables_sqlite()
            
            self.logger.info("Resource monitoring database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize resource database: {e}")
    
    def _create_resource_tables(self):
        """Create resource monitoring tables using SQLAlchemy"""
        try:
            # Resource metrics table
            self.metrics_table = Table(
                'resource_metrics', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('category', String, nullable=False),
                Column('metric_type', String, nullable=False),
                Column('value', Float, nullable=False),
                Column('unit', String, nullable=False),
                Column('timestamp', DateTime, nullable=False),
                Column('metadata', Text)
            )
            
            # Quota policies table
            self.quota_policies_table = Table(
                'quota_policies', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('hard_limit', Integer, nullable=False),
                Column('soft_limit', Integer, nullable=False),
                Column('warning_threshold', Float, nullable=False),
                Column('critical_threshold', Float, nullable=False),
                Column('auto_scale', Boolean, default=False),
                Column('auto_scale_factor', Float, default=1.5),
                Column('billing_enabled', Boolean, default=True),
                Column('cost_per_unit', Float, default=0.0),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False)
            )
            
            # Resource allocations table
            self.allocations_table = Table(
                'resource_allocations', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('user_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('amount', Integer, nullable=False),
                Column('allocated_at', DateTime, nullable=False),
                Column('expires_at', DateTime),
                Column('metadata', Text)
            )
            
            # Resource alerts table
            self.alerts_table = Table(
                'resource_alerts', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('alert_type', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('current_usage', Integer, nullable=False),
                Column('limit', Integer, nullable=False),
                Column('threshold', Float, nullable=False),
                Column('message', Text, nullable=False),
                Column('resolved', Boolean, default=False),
                Column('created_at', DateTime, nullable=False),
                Column('resolved_at', DateTime)
            )
            
            # Billing records table
            self.billing_records_table = Table(
                'billing_records', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('tenant_id', String, nullable=False),
                Column('resource_type', String, nullable=False),
                Column('usage_amount', Integer, nullable=False),
                Column('unit_cost', Float, nullable=False),
                Column('total_cost', Float, nullable=False),
                Column('billing_period_start', DateTime, nullable=False),
                Column('billing_period_end', DateTime, nullable=False),
                Column('created_at', DateTime, nullable=False),
                Column('metadata', Text)
            )
            
            # System metrics table
            self.system_metrics_table = Table(
                'system_metrics', self.Base.metadata,
                Column('id', String, primary_key=True),
                Column('cpu_usage', Float, nullable=False),
                Column('memory_usage', Float, nullable=False),
                Column('disk_usage', Float, nullable=False),
                Column('network_io', Text, nullable=False),
                Column('active_connections', Integer, nullable=False),
                Column('response_time', Float, nullable=False),
                Column('timestamp', DateTime, nullable=False)
            )
            
            # Create all tables
            self.Base.metadata.create_all(self.engine)
            
        except Exception as e:
            self.logger.error(f"Error creating resource tables: {e}")
    
    def _create_resource_tables_sqlite(self):
        """Create resource monitoring tables using SQLite"""
        try:
            cursor = self.resource_conn.cursor()
            
            # Resource metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Quota policies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quota_policies (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    hard_limit INTEGER NOT NULL,
                    soft_limit INTEGER NOT NULL,
                    warning_threshold REAL NOT NULL,
                    critical_threshold REAL NOT NULL,
                    auto_scale BOOLEAN DEFAULT 0,
                    auto_scale_factor REAL DEFAULT 1.5,
                    billing_enabled BOOLEAN DEFAULT 1,
                    cost_per_unit REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Resource allocations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_allocations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    allocated_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Resource alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_alerts (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    current_usage INTEGER NOT NULL,
                    limit INTEGER NOT NULL,
                    threshold REAL NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            
            # Billing records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS billing_records (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    usage_amount INTEGER NOT NULL,
                    unit_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    billing_period_start TEXT NOT NULL,
                    billing_period_end TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # System metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id TEXT PRIMARY KEY,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    network_io TEXT NOT NULL,
                    active_connections INTEGER NOT NULL,
                    response_time REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            self.resource_conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating SQLite resource tables: {e}")
    
    def start_monitoring(self, interval: int = 60):
        """Start resource monitoring"""
        try:
            if self.monitoring_active:
                self.logger.warning("Resource monitoring already active")
                return
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(interval,),
                daemon=True
            )
            self.monitor_thread.start()
            
            self.logger.info(f"Resource monitoring started with {interval}s interval")
            
        except Exception as e:
            self.logger.error(f"Error starting resource monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        try:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            self.logger.info("Resource monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping resource monitoring: {e}")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self._store_system_metrics(system_metrics)
                
                # Collect container metrics if Docker is available
                if self.docker_client:
                    container_metrics = self._collect_container_metrics()
                    for metric in container_metrics:
                        self._store_metric(metric)
                
                # Sleep for interval
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Active connections
            connections = len(psutil.net_connections())
            
            # Response time (mock value)
            response_time = 0.1  # Would be measured from actual requests
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, {}, 0, 0)
    
    def _collect_container_metrics(self) -> List[ResourceMetric]:
        """Collect Docker container metrics"""
        try:
            metrics = []
            
            for container in self.docker_client.containers.list():
                # Get container stats
                stats = container.stats(stream=False)
                
                # Extract tenant ID from container labels
                tenant_id = container.labels.get('tenant_id', 'unknown')
                
                # CPU usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * 100.0
                
                metrics.append(ResourceMetric(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    resource_type=ResourceType.CPU,
                    category=ResourceCategory.COMPUTE,
                    metric_type=MetricType.GAUGE,
                    value=cpu_usage,
                    unit='percent',
                    timestamp=datetime.now(),
                    metadata={'container_id': container.id, 'container_name': container.name}
                ))
                
                # Memory usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percent = (memory_usage / memory_limit) * 100.0
                
                metrics.append(ResourceMetric(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    resource_type=ResourceType.MEMORY,
                    category=ResourceCategory.COMPUTE,
                    metric_type=MetricType.GAUGE,
                    value=memory_percent,
                    unit='percent',
                    timestamp=datetime.now(),
                    metadata={'container_id': container.id, 'container_name': container.name}
                ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting container metrics: {e}")
            return []
    
    def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            metrics_id = str(uuid.uuid4())
            
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.system_metrics_table.insert().values(
                            id=metrics_id,
                            cpu_usage=metrics.cpu_usage,
                            memory_usage=metrics.memory_usage,
                            disk_usage=metrics.disk_usage,
                            network_io=json.dumps(metrics.network_io),
                            active_connections=metrics.active_connections,
                            response_time=metrics.response_time,
                            timestamp=metrics.timestamp
                        )
                    )
                    session.commit()
            else:
                cursor = self.resource_conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics (id, cpu_usage, memory_usage, disk_usage, network_io, active_connections, response_time, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics_id, metrics.cpu_usage, metrics.memory_usage,
                    metrics.disk_usage, json.dumps(metrics.network_io),
                    metrics.active_connections, metrics.response_time,
                    metrics.timestamp.isoformat()
                ))
                self.resource_conn.commit()
            
            # Cache in Redis
            if self.redis_client:
                self.redis_client.setex(
                    f"system:metrics:latest",
                    300,  # 5 minutes
                    json.dumps({
                        'cpu_usage': metrics.cpu_usage,
                        'memory_usage': metrics.memory_usage,
                        'disk_usage': metrics.disk_usage,
                        'network_io': metrics.network_io,
                        'active_connections': metrics.active_connections,
                        'response_time': metrics.response_time,
                        'timestamp': metrics.timestamp.isoformat()
                    })
                )
                
        except Exception as e:
            self.logger.error(f"Error storing system metrics: {e}")
    
    def _store_metric(self, metric: ResourceMetric):
        """Store resource metric in database"""
        try:
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    session.execute(
                        self.metrics_table.insert().values(
                            id=metric.id,
                            tenant_id=metric.tenant_id,
                            resource_type=metric.resource_type.value,
                            category=metric.category.value,
                            metric_type=metric.metric_type.value,
                            value=metric.value,
                            unit=metric.unit,
                            timestamp=metric.timestamp,
                            metadata=json.dumps(metric.metadata)
                        )
                    )
                    session.commit()
            else:
                cursor = self.resource_conn.cursor()
                cursor.execute("""
                    INSERT INTO resource_metrics (id, tenant_id, resource_type, category, metric_type, value, unit, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.id, metric.tenant_id, metric.resource_type.value,
                    metric.category.value, metric.metric_type.value,
                    metric.value, metric.unit, metric.timestamp.isoformat(),
                    json.dumps(metric.metadata)
                ))
                self.resource_conn.commit()
            
            # Cache in Redis
            if self.redis_client:
                cache_key = f"metric:{metric.tenant_id}:{metric.resource_type.value}:latest"
                self.redis_client.setex(
                    cache_key,
                    300,  # 5 minutes
                    json.dumps({
                        'value': metric.value,
                        'unit': metric.unit,
                        'timestamp': metric.timestamp.isoformat()
                    })
                )
                
        except Exception as e:
            self.logger.error(f"Error storing metric: {e}")
    
    def get_tenant_metrics(self, tenant_id: str, resource_type: ResourceType,
                          start_time: datetime, end_time: datetime) -> List[ResourceMetric]:
        """Get metrics for tenant and resource type"""
        try:
            metrics = []
            
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    results = session.execute(
                        self.metrics_table.select().where(
                            (self.metrics_table.c.tenant_id == tenant_id) &
                            (self.metrics_table.c.resource_type == resource_type.value) &
                            (self.metrics_table.c.timestamp >= start_time) &
                            (self.metrics_table.c.timestamp <= end_time)
                        ).order_by(self.metrics_table.c.timestamp.asc())
                    ).fetchall()
                    
                    for result in results:
                        metric = ResourceMetric(
                            id=result.id,
                            tenant_id=result.tenant_id,
                            resource_type=ResourceType(result.resource_type),
                            category=ResourceCategory(result.category),
                            metric_type=MetricType(result.metric_type),
                            value=result.value,
                            unit=result.unit,
                            timestamp=result.timestamp,
                            metadata=json.loads(result.metadata) if result.metadata else {}
                        )
                        metrics.append(metric)
            else:
                cursor = self.resource_conn.cursor()
                cursor.execute("""
                    SELECT * FROM resource_metrics 
                    WHERE tenant_id = ? AND resource_type = ? 
                    AND timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                """, (tenant_id, resource_type.value, start_time.isoformat(), end_time.isoformat()))
                results = cursor.fetchall()
                
                for result in results:
                    metric = ResourceMetric(
                        id=result[0],
                        tenant_id=result[1],
                        resource_type=ResourceType(result[2]),
                        category=ResourceCategory(result[3]),
                        metric_type=MetricType(result[4]),
                        value=result[5],
                        unit=result[6],
                        timestamp=datetime.fromisoformat(result[7]),
                        metadata=json.loads(result[8]) if result[8] else {}
                    )
                    metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting tenant metrics: {e}")
            return []
    
    def get_latest_system_metrics(self) -> Optional[SystemMetrics]:
        """Get latest system metrics"""
        try:
            # Try Redis cache first
            if self.redis_client:
                cached_metrics = self.redis_client.get("system:metrics:latest")
                if cached_metrics:
                    data = json.loads(cached_metrics)
                    return SystemMetrics(
                        cpu_usage=data['cpu_usage'],
                        memory_usage=data['memory_usage'],
                        disk_usage=data['disk_usage'],
                        network_io=data['network_io'],
                        active_connections=data['active_connections'],
                        response_time=data['response_time'],
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )
            
            # Query database
            if HAS_SQLALCHEMY:
                with self.SessionLocal() as session:
                    result = session.execute(
                        self.system_metrics_table.select().order_by(
                            self.system_metrics_table.c.timestamp.desc()
                        ).limit(1)
                    ).fetchone()
                    
                    if result:
                        return SystemMetrics(
                            cpu_usage=result.cpu_usage,
                            memory_usage=result.memory_usage,
                            disk_usage=result.disk_usage,
                            network_io=json.loads(result.network_io),
                            active_connections=result.active_connections,
                            response_time=result.response_time,
                            timestamp=result.timestamp
                        )
            else:
                cursor = self.resource_conn.cursor()
                cursor.execute("""
                    SELECT * FROM system_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                
                if result:
                    return SystemMetrics(
                        cpu_usage=result[1],
                        memory_usage=result[2],
                        disk_usage=result[3],
                        network_io=json.loads(result[4]),
                        active_connections=result[5],
                        response_time=result[6],
                        timestamp=datetime.fromisoformat(result[7])
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest system metrics: {e}")
            return None

class QuotaManager:
    """
    Quota management and enforcement system
    """
    
    def __init__(self, resource_monitor: ResourceMonitor, tenant_manager: TenantManager = None):
        self.resource_monitor = resource_monitor
        self.tenant_manager = tenant_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.quota_policies = {}
        self.alerts_cache = {}
        
        # Load existing quota policies
        self._load_quota_policies()
    
    def _load_quota_policies(self):
        """Load quota policies from database"""
        try:
            if HAS_SQLALCHEMY:
                with self.resource_monitor.SessionLocal() as session:
                    results = session.execute(
                        self.resource_monitor.quota_policies_table.select()
                    ).fetchall()
                    
                    for result in results:
                        policy = QuotaPolicy(
                            id=result.id,
                            tenant_id=result.tenant_id,
                            resource_type=ResourceType(result.resource_type),
                            hard_limit=result.hard_limit,
                            soft_limit=result.soft_limit,
                            warning_threshold=result.warning_threshold,
                            critical_threshold=result.critical_threshold,
                            auto_scale=result.auto_scale,
                            auto_scale_factor=result.auto_scale_factor,
                            billing_enabled=result.billing_enabled,
                            cost_per_unit=result.cost_per_unit,
                            created_at=result.created_at,
                            updated_at=result.updated_at
                        )
                        self.quota_policies[f"{result.tenant_id}:{result.resource_type}"] = policy
            else:
                cursor = self.resource_monitor.resource_conn.cursor()
                cursor.execute("SELECT * FROM quota_policies")
                results = cursor.fetchall()
                
                for result in results:
                    policy = QuotaPolicy(
                        id=result[0],
                        tenant_id=result[1],
                        resource_type=ResourceType(result[2]),
                        hard_limit=result[3],
                        soft_limit=result[4],
                        warning_threshold=result[5],
                        critical_threshold=result[6],
                        auto_scale=bool(result[7]),
                        auto_scale_factor=result[8],
                        billing_enabled=bool(result[9]),
                        cost_per_unit=result[10],
                        created_at=datetime.fromisoformat(result[11]),
                        updated_at=datetime.fromisoformat(result[12])
                    )
                    self.quota_policies[f"{result[1]}:{result[2]}"] = policy
                    
        except Exception as e:
            self.logger.error(f"Error loading quota policies: {e}")
    
    def create_quota_policy(self, tenant_id: str, resource_type: ResourceType,
                          hard_limit: int, soft_limit: int,
                          warning_threshold: float = 80.0,
                          critical_threshold: float = 95.0,
                          auto_scale: bool = False,
                          cost_per_unit: float = 0.0) -> Optional[QuotaPolicy]:
        """Create a new quota policy"""
        try:
            policy = QuotaPolicy(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                resource_type=resource_type,
                hard_limit=hard_limit,
                soft_limit=soft_limit,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                auto_scale=auto_scale,
                cost_per_unit=cost_per_unit
            )
            
            # Store in database
            if HAS_SQLALCHEMY:
                with self.resource_monitor.SessionLocal() as session:
                    session.execute(
                        self.resource_monitor.quota_policies_table.insert().values(
                            id=policy.id,
                            tenant_id=policy.tenant_id,
                            resource_type=policy.resource_type.value,
                            hard_limit=policy.hard_limit,
                            soft_limit=policy.soft_limit,
                            warning_threshold=policy.warning_threshold,
                            critical_threshold=policy.critical_threshold,
                            auto_scale=policy.auto_scale,
                            auto_scale_factor=policy.auto_scale_factor,
                            billing_enabled=policy.billing_enabled,
                            cost_per_unit=policy.cost_per_unit,
                            created_at=policy.created_at,
                            updated_at=policy.updated_at
                        )
                    )
                    session.commit()
            else:
                cursor = self.resource_monitor.resource_conn.cursor()
                cursor.execute("""
                    INSERT INTO quota_policies (id, tenant_id, resource_type, hard_limit, soft_limit, warning_threshold, critical_threshold, auto_scale, auto_scale_factor, billing_enabled, cost_per_unit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy.id, policy.tenant_id, policy.resource_type.value,
                    policy.hard_limit, policy.soft_limit, policy.warning_threshold,
                    policy.critical_threshold, policy.auto_scale, policy.auto_scale_factor,
                    policy.billing_enabled, policy.cost_per_unit,
                    policy.created_at.isoformat(), policy.updated_at.isoformat()
                ))
                self.resource_monitor.resource_conn.commit()
            
            # Cache policy
            self.quota_policies[f"{tenant_id}:{resource_type.value}"] = policy
            
            self.logger.info(f"Created quota policy for {tenant_id}:{resource_type.value}")
            return policy
            
        except Exception as e:
            self.logger.error(f"Error creating quota policy: {e}")
            return None
    
    def check_quota_status(self, tenant_id: str, resource_type: ResourceType,
                          current_usage: int) -> Tuple[ResourceStatus, Optional[ResourceAlert]]:
        """Check quota status for tenant and resource"""
        try:
            policy_key = f"{tenant_id}:{resource_type.value}"
            policy = self.quota_policies.get(policy_key)
            
            if not policy:
                return ResourceStatus.NORMAL, None
            
            # Calculate usage percentage
            usage_percent = (current_usage / policy.hard_limit) * 100
            
            # Determine status
            if usage_percent >= 100:
                status = ResourceStatus.EXCEEDED
                alert_type = AlertType.QUOTA_EXCEEDED
            elif usage_percent >= policy.critical_threshold:
                status = ResourceStatus.CRITICAL
                alert_type = AlertType.QUOTA_EXCEEDED
            elif usage_percent >= policy.warning_threshold:
                status = ResourceStatus.WARNING
                alert_type = AlertType.QUOTA_WARNING
            else:
                status = ResourceStatus.NORMAL
                alert_type = None
            
            # Create alert if needed
            alert = None
            if alert_type:
                alert = ResourceAlert(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    alert_type=alert_type,
                    resource_type=resource_type,
                    current_usage=current_usage,
                    limit=policy.hard_limit,
                    threshold=usage_percent,
                    message=f"Resource {resource_type.value} usage at {usage_percent:.1f}% ({current_usage}/{policy.hard_limit})"
                )
                
                # Store alert
                self._store_alert(alert)
                
                # Auto-scale if enabled
                if policy.auto_scale and status == ResourceStatus.CRITICAL:
                    self._auto_scale_resource(tenant_id, resource_type, policy)
            
            return status, alert
            
        except Exception as e:
            self.logger.error(f"Error checking quota status: {e}")
            return ResourceStatus.NORMAL, None
    
    def _store_alert(self, alert: ResourceAlert):
        """Store resource alert in database"""
        try:
            if HAS_SQLALCHEMY:
                with self.resource_monitor.SessionLocal() as session:
                    session.execute(
                        self.resource_monitor.alerts_table.insert().values(
                            id=alert.id,
                            tenant_id=alert.tenant_id,
                            alert_type=alert.alert_type.value,
                            resource_type=alert.resource_type.value,
                            current_usage=alert.current_usage,
                            limit=alert.limit,
                            threshold=alert.threshold,
                            message=alert.message,
                            resolved=alert.resolved,
                            created_at=alert.created_at,
                            resolved_at=alert.resolved_at
                        )
                    )
                    session.commit()
            else:
                cursor = self.resource_monitor.resource_conn.cursor()
                cursor.execute("""
                    INSERT INTO resource_alerts (id, tenant_id, alert_type, resource_type, current_usage, limit, threshold, message, resolved, created_at, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id, alert.tenant_id, alert.alert_type.value,
                    alert.resource_type.value, alert.current_usage, alert.limit,
                    alert.threshold, alert.message, alert.resolved,
                    alert.created_at.isoformat(),
                    alert.resolved_at.isoformat() if alert.resolved_at else None
                ))
                self.resource_monitor.resource_conn.commit()
            
            # Cache alert
            self.alerts_cache[alert.id] = alert
            
        except Exception as e:
            self.logger.error(f"Error storing alert: {e}")
    
    def _auto_scale_resource(self, tenant_id: str, resource_type: ResourceType, policy: QuotaPolicy):
        """Auto-scale resource based on policy"""
        try:
            new_limit = int(policy.hard_limit * policy.auto_scale_factor)
            
            # Update policy
            policy.hard_limit = new_limit
            policy.soft_limit = int(new_limit * 0.8)  # 80% of new limit
            policy.updated_at = datetime.now()
            
            # Update database
            if HAS_SQLALCHEMY:
                with self.resource_monitor.SessionLocal() as session:
                    session.execute(
                        self.resource_monitor.quota_policies_table.update().where(
                            self.resource_monitor.quota_policies_table.c.id == policy.id
                        ).values(
                            hard_limit=policy.hard_limit,
                            soft_limit=policy.soft_limit,
                            updated_at=policy.updated_at
                        )
                    )
                    session.commit()
            else:
                cursor = self.resource_monitor.resource_conn.cursor()
                cursor.execute("""
                    UPDATE quota_policies 
                    SET hard_limit = ?, soft_limit = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    policy.hard_limit, policy.soft_limit,
                    policy.updated_at.isoformat(), policy.id
                ))
                self.resource_monitor.resource_conn.commit()
            
            # Update cache
            policy_key = f"{tenant_id}:{resource_type.value}"
            self.quota_policies[policy_key] = policy
            
            self.logger.info(f"Auto-scaled {resource_type.value} for {tenant_id} to {new_limit}")
            
        except Exception as e:
            self.logger.error(f"Error auto-scaling resource: {e}")
    
    def get_tenant_alerts(self, tenant_id: str, resolved: bool = False) -> List[ResourceAlert]:
        """Get alerts for tenant"""
        try:
            alerts = []
            
            if HAS_SQLALCHEMY:
                with self.resource_monitor.SessionLocal() as session:
                    results = session.execute(
                        self.resource_monitor.alerts_table.select().where(
                            (self.resource_monitor.alerts_table.c.tenant_id == tenant_id) &
                            (self.resource_monitor.alerts_table.c.resolved == resolved)
                        ).order_by(self.resource_monitor.alerts_table.c.created_at.desc())
                    ).fetchall()
                    
                    for result in results:
                        alert = ResourceAlert(
                            id=result.id,
                            tenant_id=result.tenant_id,
                            alert_type=AlertType(result.alert_type),
                            resource_type=ResourceType(result.resource_type),
                            current_usage=result.current_usage,
                            limit=result.limit,
                            threshold=result.threshold,
                            message=result.message,
                            resolved=result.resolved,
                            created_at=result.created_at,
                            resolved_at=result.resolved_at
                        )
                        alerts.append(alert)
            else:
                cursor = self.resource_monitor.resource_conn.cursor()
                cursor.execute("""
                    SELECT * FROM resource_alerts 
                    WHERE tenant_id = ? AND resolved = ?
                    ORDER BY created_at DESC
                """, (tenant_id, resolved))
                results = cursor.fetchall()
                
                for result in results:
                    alert = ResourceAlert(
                        id=result[0],
                        tenant_id=result[1],
                        alert_type=AlertType(result[2]),
                        resource_type=ResourceType(result[3]),
                        current_usage=result[4],
                        limit=result[5],
                        threshold=result[6],
                        message=result[7],
                        resolved=bool(result[8]),
                        created_at=datetime.fromisoformat(result[9]),
                        resolved_at=datetime.fromisoformat(result[10]) if result[10] else None
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error getting tenant alerts: {e}")
            return []

def main():
    """Main function for testing resource management system"""
    try:
        print("Resource Management & Quota System - Test Mode")
        print("=" * 50)
        
        # Initialize resource monitor
        resource_monitor = ResourceMonitor()
        
        # Initialize quota manager
        quota_manager = QuotaManager(resource_monitor)
        
        # Start monitoring
        print("Starting resource monitoring...")
        resource_monitor.start_monitoring(interval=30)
        
        # Wait for some metrics to be collected
        time.sleep(5)
        
        # Get latest system metrics
        print("Getting latest system metrics...")
        system_metrics = resource_monitor.get_latest_system_metrics()
        
        if system_metrics:
            print(f"CPU Usage: {system_metrics.cpu_usage:.1f}%")
            print(f"Memory Usage: {system_metrics.memory_usage:.1f}%")
            print(f"Disk Usage: {system_metrics.disk_usage:.1f}%")
            print(f"Active Connections: {system_metrics.active_connections}")
            print(f"Response Time: {system_metrics.response_time:.3f}s")
        
        # Test quota policy creation
        print("\nTesting quota policy creation...")
        tenant_id = "test-tenant-123"
        
        policy = quota_manager.create_quota_policy(
            tenant_id=tenant_id,
            resource_type=ResourceType.CPU,
            hard_limit=1000,
            soft_limit=800,
            warning_threshold=80.0,
            critical_threshold=95.0,
            auto_scale=True,
            cost_per_unit=0.01
        )
        
        if policy:
            print(f"Created quota policy: {policy.resource_type.value}")
            print(f"Hard Limit: {policy.hard_limit}")
            print(f"Soft Limit: {policy.soft_limit}")
            print(f"Auto Scale: {policy.auto_scale}")
            
            # Test quota status checking
            print("\nTesting quota status checking...")
            status, alert = quota_manager.check_quota_status(
                tenant_id=tenant_id,
                resource_type=ResourceType.CPU,
                current_usage=850  # 85% of limit
            )
            
            print(f"Quota Status: {status.value}")
            if alert:
                print(f"Alert: {alert.message}")
            
            # Test critical usage
            print("\nTesting critical usage...")
            status, alert = quota_manager.check_quota_status(
                tenant_id=tenant_id,
                resource_type=ResourceType.CPU,
                current_usage=970  # 97% of limit
            )
            
            print(f"Critical Status: {status.value}")
            if alert:
                print(f"Critical Alert: {alert.message}")
                
                # Check if auto-scaling occurred
                updated_policy = quota_manager.quota_policies.get(f"{tenant_id}:{ResourceType.CPU.value}")
                if updated_policy and updated_policy.hard_limit > 1000:
                    print(f"Auto-scaling occurred! New limit: {updated_policy.hard_limit}")
            
            # Get tenant alerts
            print("\nGetting tenant alerts...")
            alerts = quota_manager.get_tenant_alerts(tenant_id, resolved=False)
            print(f"Active alerts: {len(alerts)}")
            
            for alert in alerts:
                print(f"- {alert.alert_type.value}: {alert.message}")
        
        # Stop monitoring
        print("\nStopping resource monitoring...")
        resource_monitor.stop_monitoring()
        
        print("\nResource management system test completed!")
        
    except Exception as e:
        print(f"Error in resource management system: {e}")
        logger.error(f"Resource management system error: {e}")

if __name__ == "__main__":
    main()
