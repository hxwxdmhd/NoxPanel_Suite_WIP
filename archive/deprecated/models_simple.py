#!/usr/bin/env python3
"""
Ultimate Suite v11.0 - Simplified Models for Quick Deployment
============================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

# Use SQLite for initial deployment to avoid PostgreSQL dependency
try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if HAS_SQLALCHEMY:
    # Create declarative base
    Base = declarative_base()

    class SystemMetrics(Base):
        """System metrics table"""
        __tablename__ = 'system_metrics'
        
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime, default=datetime.utcnow)
        cpu_usage = Column(Float)
        memory_usage = Column(Float)
        disk_usage = Column(Float)
        network_usage = Column(Float)
        active_connections = Column(Integer)
        requests_per_second = Column(Float)
        error_rate = Column(Float)
        response_time_avg = Column(Float)
        
        def to_dict(self):
            return {
                'id': self.id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'cpu_usage': self.cpu_usage,
                'memory_usage': self.memory_usage,
                'disk_usage': self.disk_usage,
                'network_usage': self.network_usage,
                'active_connections': self.active_connections,
                'requests_per_second': self.requests_per_second,
                'error_rate': self.error_rate,
                'response_time_avg': self.response_time_avg
            }

    class UserSession(Base):
        """User session management"""
        __tablename__ = 'user_sessions'
        
        id = Column(Integer, primary_key=True)
        session_id = Column(String(255), unique=True, nullable=False)
        user_id = Column(String(255), nullable=False)
        ip_address = Column(String(45))
        user_agent = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)
        last_activity = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
        
        def to_dict(self):
            return {
                'id': self.id,
                'session_id': self.session_id,
                'user_id': self.user_id,
                'ip_address': self.ip_address,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'is_active': self.is_active
            }

    class SystemLog(Base):
        """System logging"""
        __tablename__ = 'system_logs'
        
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime, default=datetime.utcnow)
        level = Column(String(20))
        component = Column(String(100))
        message = Column(Text)
        extra_data = Column(Text)  # JSON string for additional data
        
        def to_dict(self):
            return {
                'id': self.id,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'level': self.level,
                'component': self.component,
                'message': self.message,
                'extra_data': json.loads(self.extra_data) if self.extra_data else None
            }

    class DatabaseManager:
        """Simplified database manager"""
        
        def __init__(self, database_url: str = "sqlite:///heimnetz.db"):
            self.database_url = database_url
            self.engine = create_engine(database_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            
        def create_tables(self):
            """Create all tables"""
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            
        def get_session(self):
            """Get database session"""
            return self.Session()
            
        def close(self):
            """Close database connection"""
            if self.session:
                self.session.close()
            if self.engine:
                self.engine.dispose()
                
        def log_system_metrics(self, metrics: Dict[str, Any]):
            """Log system metrics"""
            try:
                metric_record = SystemMetrics(
                    cpu_usage=metrics.get('cpu_usage'),
                    memory_usage=metrics.get('memory_usage'),
                    disk_usage=metrics.get('disk_usage'),
                    network_usage=metrics.get('network_usage'),
                    active_connections=metrics.get('active_connections'),
                    requests_per_second=metrics.get('requests_per_second'),
                    error_rate=metrics.get('error_rate'),
                    response_time_avg=metrics.get('response_time_avg')
                )
                self.session.add(metric_record)
                self.session.commit()
            except Exception as e:
                logger.error(f"Failed to log metrics: {e}")
                self.session.rollback()
                
        def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
            """Get recent system metrics"""
            try:
                metrics = self.session.query(SystemMetrics).order_by(
                    SystemMetrics.timestamp.desc()
                ).limit(limit).all()
                return [metric.to_dict() for metric in metrics]
            except Exception as e:
                logger.error(f"Failed to get metrics: {e}")
                return []

else:
    # Fallback without SQLAlchemy
    class DatabaseManager:
        """Fallback database manager without SQLAlchemy"""
        
        def __init__(self, database_url: str = ""):
            self.database_url = database_url
            self.metrics = []
            self.sessions = []
            self.logs = []
            logger.warning("SQLAlchemy not available, using in-memory storage")
            
        def create_tables(self):
            """No-op for fallback"""
            logger.info("Using in-memory storage (no database)")
            
        def get_session(self):
            """Return self for compatibility"""
            return self
            
        def close(self):
            """No-op for fallback"""
            pass
            
        def log_system_metrics(self, metrics: Dict[str, Any]):
            """Store metrics in memory"""
            metrics['timestamp'] = datetime.utcnow().isoformat()
            self.metrics.append(metrics)
            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
                
        def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
            """Get recent metrics from memory"""
            return self.metrics[-limit:]

# Export main classes
__all__ = ['DatabaseManager', 'SystemMetrics', 'UserSession', 'SystemLog']

if __name__ == '__main__':
    # Test database setup
    try:
        db_manager = DatabaseManager()
        db_manager.create_tables()
        print("✓ Simple database setup successful")
        
        # Test metrics logging
        test_metrics = {
            'cpu_usage': 25.5,
            'memory_usage': 45.2,
            'disk_usage': 60.0,
            'active_connections': 5
        }
        
        db_manager.log_system_metrics(test_metrics)
        recent_metrics = db_manager.get_recent_metrics(10)
        print(f"✓ Metrics logging successful: {len(recent_metrics)} records")
        
        db_manager.close()
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
