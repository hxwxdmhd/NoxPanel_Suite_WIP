#!/usr/bin/env python3
"""
Plugin Registry Database System - Audit 3 Compliant
==================================================

This system provides a centralized database for plugin management:
- Plugin metadata storage
- Version tracking
- Security audit results
- Performance metrics
- Dependency management
- Plugin lifecycle tracking

SQLite-based for local plugin registry management
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginStatus(Enum):
    """Plugin lifecycle status"""
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    DEPRECATED = "DEPRECATED"

class PluginCategory(Enum):
    """Plugin categories"""
    SERVICE = "SERVICE"
    MIDDLEWARE = "MIDDLEWARE"
    SECURITY = "SECURITY"
    FEATURE = "FEATURE"
    UTILITY = "UTILITY"
    MONITORING = "MONITORING"
    ANALYTICS = "ANALYTICS"

@dataclass
class PluginMetadata:
    """Plugin metadata structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    email: str = ""
    website: str = ""
    category: PluginCategory = PluginCategory.UTILITY
    status: PluginStatus = PluginStatus.DISCOVERED
    file_path: str = ""
    entry_point: str = ""
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    python_version: str = "3.8+"
    
    # Configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # Security
    permissions: List[str] = field(default_factory=list)
    security_level: str = "LOW"
    security_validated: bool = False
    
    # Performance
    memory_usage: int = 0  # bytes
    cpu_usage: float = 0.0  # percentage
    startup_time: float = 0.0  # seconds
    
    # Metadata
    file_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    # Statistics
    execution_count: int = 0
    error_count: int = 0
    avg_execution_time: float = 0.0
    
    # Validation
    enabled: bool = True
    auto_start: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['category'] = self.category.value
        data['status'] = self.status.value
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary"""
        # Convert string enums back to enum objects
        if 'category' in data:
            data['category'] = PluginCategory(data['category'])
        if 'status' in data:
            data['status'] = PluginStatus(data['status'])
        
        # Convert ISO strings back to datetime objects
        for date_field in ['created_at', 'updated_at', 'last_accessed']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        return cls(**data)

class PluginRegistryDatabase:
    """
    Centralized plugin registry database
    """
    
    def __init__(self, db_path: str = "plugin_registry.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.init_database()
    
    def init_database(self):
        """Initialize the plugin registry database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Plugins table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugins (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        version TEXT NOT NULL,
                        description TEXT,
                        author TEXT,
                        email TEXT,
                        website TEXT,
                        category TEXT NOT NULL,
                        status TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        entry_point TEXT,
                        dependencies TEXT,  -- JSON array
                        python_version TEXT,
                        config_schema TEXT,  -- JSON object
                        default_config TEXT,  -- JSON object
                        permissions TEXT,  -- JSON array
                        security_level TEXT,
                        security_validated BOOLEAN DEFAULT FALSE,
                        memory_usage INTEGER DEFAULT 0,
                        cpu_usage REAL DEFAULT 0.0,
                        startup_time REAL DEFAULT 0.0,
                        file_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        avg_execution_time REAL DEFAULT 0.0,
                        enabled BOOLEAN DEFAULT TRUE,
                        auto_start BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Plugin versions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        version TEXT NOT NULL,
                        changelog TEXT,
                        release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_current BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Plugin dependencies table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_dependencies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        dependency_name TEXT NOT NULL,
                        version_constraint TEXT,
                        required BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Plugin configurations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_configurations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        config_type TEXT,
                        is_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Plugin execution logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_execution_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        execution_id TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_ms INTEGER,
                        success BOOLEAN,
                        error_message TEXT,
                        memory_peak INTEGER,
                        cpu_usage REAL,
                        input_data TEXT,
                        output_data TEXT,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Plugin security audits table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_security_audits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        security_level TEXT NOT NULL,
                        compliance_score REAL,
                        violations_count INTEGER DEFAULT 0,
                        passed_checks TEXT,  -- JSON array
                        failed_checks TEXT,  -- JSON array
                        audit_details TEXT,  -- JSON object
                        auditor_version TEXT,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Plugin metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plugin_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plugin_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_type TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugin_logs_plugin_id ON plugin_execution_logs(plugin_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugin_metrics_plugin_id ON plugin_metrics(plugin_id)')
                
                conn.commit()
                self.logger.info("Plugin registry database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin registry database: {e}")
            raise
    
    def register_plugin(self, metadata: PluginMetadata) -> bool:
        """
        Register a new plugin in the database
        
        Args:
            metadata: Plugin metadata
            
        Returns:
            bool: True if registration successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if plugin already exists
                cursor.execute('SELECT id FROM plugins WHERE name = ?', (metadata.name,))
                if cursor.fetchone():
                    self.logger.warning(f"Plugin {metadata.name} already registered")
                    return self.update_plugin(metadata)
                
                # Insert plugin
                cursor.execute('''
                    INSERT INTO plugins (
                        id, name, version, description, author, email, website,
                        category, status, file_path, entry_point, dependencies,
                        python_version, config_schema, default_config, permissions,
                        security_level, security_validated, memory_usage, cpu_usage,
                        startup_time, file_hash, enabled, auto_start
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata.id, metadata.name, metadata.version, metadata.description,
                    metadata.author, metadata.email, metadata.website,
                    metadata.category.value, metadata.status.value, metadata.file_path,
                    metadata.entry_point, json.dumps(metadata.dependencies),
                    metadata.python_version, json.dumps(metadata.config_schema),
                    json.dumps(metadata.default_config), json.dumps(metadata.permissions),
                    metadata.security_level, metadata.security_validated,
                    metadata.memory_usage, metadata.cpu_usage, metadata.startup_time,
                    metadata.file_hash, metadata.enabled, metadata.auto_start
                ))
                
                # Insert version record
                cursor.execute('''
                    INSERT INTO plugin_versions (plugin_id, version, is_current)
                    VALUES (?, ?, TRUE)
                ''', (metadata.id, metadata.version))
                
                # Insert dependencies
                for dep in metadata.dependencies:
                    cursor.execute('''
                        INSERT INTO plugin_dependencies (plugin_id, dependency_name, required)
                        VALUES (?, ?, TRUE)
                    ''', (metadata.id, dep))
                
                conn.commit()
                self.logger.info(f"Plugin {metadata.name} registered successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to register plugin {metadata.name}: {e}")
            return False
    
    def update_plugin(self, metadata: PluginMetadata) -> bool:
        """
        Update existing plugin metadata
        
        Args:
            metadata: Updated plugin metadata
            
        Returns:
            bool: True if update successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update plugin
                cursor.execute('''
                    UPDATE plugins SET
                        version = ?, description = ?, author = ?, email = ?, website = ?,
                        category = ?, status = ?, file_path = ?, entry_point = ?,
                        dependencies = ?, python_version = ?, config_schema = ?,
                        default_config = ?, permissions = ?, security_level = ?,
                        security_validated = ?, memory_usage = ?, cpu_usage = ?,
                        startup_time = ?, file_hash = ?, updated_at = CURRENT_TIMESTAMP,
                        enabled = ?, auto_start = ?
                    WHERE name = ?
                ''', (
                    metadata.version, metadata.description, metadata.author,
                    metadata.email, metadata.website, metadata.category.value,
                    metadata.status.value, metadata.file_path, metadata.entry_point,
                    json.dumps(metadata.dependencies), metadata.python_version,
                    json.dumps(metadata.config_schema), json.dumps(metadata.default_config),
                    json.dumps(metadata.permissions), metadata.security_level,
                    metadata.security_validated, metadata.memory_usage,
                    metadata.cpu_usage, metadata.startup_time, metadata.file_hash,
                    metadata.enabled, metadata.auto_start, metadata.name
                ))
                
                conn.commit()
                self.logger.info(f"Plugin {metadata.name} updated successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update plugin {metadata.name}: {e}")
            return False
    
    def get_plugin(self, name: str) -> Optional[PluginMetadata]:
        """
        Get plugin metadata by name
        
        Args:
            name: Plugin name
            
        Returns:
            Optional[PluginMetadata]: Plugin metadata or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM plugins WHERE name = ?', (name,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_metadata(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get plugin {name}: {e}")
            return None
    
    def get_all_plugins(self) -> List[PluginMetadata]:
        """
        Get all plugin metadata
        
        Returns:
            List[PluginMetadata]: List of all plugin metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM plugins ORDER BY name')
                rows = cursor.fetchall()
                
                return [self._row_to_metadata(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get all plugins: {e}")
            return []
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[PluginMetadata]:
        """
        Get plugins by category
        
        Args:
            category: Plugin category
            
        Returns:
            List[PluginMetadata]: List of plugins in category
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM plugins WHERE category = ? ORDER BY name',
                             (category.value,))
                rows = cursor.fetchall()
                
                return [self._row_to_metadata(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get plugins by category {category.value}: {e}")
            return []
    
    def get_plugins_by_status(self, status: PluginStatus) -> List[PluginMetadata]:
        """
        Get plugins by status
        
        Args:
            status: Plugin status
            
        Returns:
            List[PluginMetadata]: List of plugins with status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM plugins WHERE status = ? ORDER BY name',
                             (status.value,))
                rows = cursor.fetchall()
                
                return [self._row_to_metadata(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get plugins by status {status.value}: {e}")
            return []
    
    def update_plugin_status(self, name: str, status: PluginStatus) -> bool:
        """
        Update plugin status
        
        Args:
            name: Plugin name
            status: New status
            
        Returns:
            bool: True if update successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE plugins SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (status.value, name))
                
                conn.commit()
                self.logger.info(f"Plugin {name} status updated to {status.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update plugin {name} status: {e}")
            return False
    
    def log_plugin_execution(self, plugin_name: str, execution_id: str, 
                           duration_ms: int, success: bool, error_message: str = None,
                           memory_peak: int = 0, cpu_usage: float = 0.0) -> bool:
        """
        Log plugin execution
        
        Args:
            plugin_name: Plugin name
            execution_id: Unique execution ID
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
            error_message: Error message if failed
            memory_peak: Peak memory usage
            cpu_usage: CPU usage during execution
            
        Returns:
            bool: True if logging successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get plugin ID
                cursor.execute('SELECT id FROM plugins WHERE name = ?', (plugin_name,))
                plugin_row = cursor.fetchone()
                if not plugin_row:
                    return False
                
                plugin_id = plugin_row[0]
                
                # Insert execution log
                cursor.execute('''
                    INSERT INTO plugin_execution_logs (
                        plugin_id, execution_id, end_time, duration_ms, success,
                        error_message, memory_peak, cpu_usage
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
                ''', (plugin_id, execution_id, duration_ms, success, error_message,
                     memory_peak, cpu_usage))
                
                # Update plugin statistics
                cursor.execute('''
                    UPDATE plugins SET
                        execution_count = execution_count + 1,
                        error_count = error_count + CASE WHEN ? THEN 0 ELSE 1 END,
                        avg_execution_time = (avg_execution_time * execution_count + ?) / (execution_count + 1),
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (success, duration_ms, plugin_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to log execution for plugin {plugin_name}: {e}")
            return False
    
    def get_plugin_statistics(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin execution statistics
        
        Args:
            name: Plugin name
            
        Returns:
            Optional[Dict[str, Any]]: Plugin statistics or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT execution_count, error_count, avg_execution_time,
                           memory_usage, cpu_usage, last_accessed
                    FROM plugins WHERE name = ?
                ''', (name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'execution_count': row[0],
                        'error_count': row[1],
                        'avg_execution_time': row[2],
                        'memory_usage': row[3],
                        'cpu_usage': row[4],
                        'last_accessed': row[5],
                        'success_rate': (row[0] - row[1]) / row[0] if row[0] > 0 else 0
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics for plugin {name}: {e}")
            return None
    
    def _row_to_metadata(self, row: Tuple) -> PluginMetadata:
        """Convert database row to PluginMetadata object"""
        return PluginMetadata(
            id=row[0],
            name=row[1],
            version=row[2],
            description=row[3] or "",
            author=row[4] or "",
            email=row[5] or "",
            website=row[6] or "",
            category=PluginCategory(row[7]),
            status=PluginStatus(row[8]),
            file_path=row[9],
            entry_point=row[10] or "",
            dependencies=json.loads(row[11]) if row[11] else [],
            python_version=row[12] or "3.8+",
            config_schema=json.loads(row[13]) if row[13] else {},
            default_config=json.loads(row[14]) if row[14] else {},
            permissions=json.loads(row[15]) if row[15] else [],
            security_level=row[16] or "LOW",
            security_validated=bool(row[17]),
            memory_usage=row[18] or 0,
            cpu_usage=row[19] or 0.0,
            startup_time=row[20] or 0.0,
            file_hash=row[21] or "",
            created_at=datetime.fromisoformat(row[22]) if row[22] else datetime.now(),
            updated_at=datetime.fromisoformat(row[23]) if row[23] else datetime.now(),
            last_accessed=datetime.fromisoformat(row[24]) if row[24] else datetime.now(),
            execution_count=row[25] or 0,
            error_count=row[26] or 0,
            avg_execution_time=row[27] or 0.0,
            enabled=bool(row[28]),
            auto_start=bool(row[29])
        )
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Clean up old execution logs
        
        Args:
            days: Number of days to keep logs
            
        Returns:
            int: Number of logs deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM plugin_execution_logs
                    WHERE start_time < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old execution logs")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    def export_plugin_data(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Export all plugin data
        
        Args:
            name: Plugin name
            
        Returns:
            Optional[Dict[str, Any]]: Complete plugin data or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get plugin metadata
                metadata = self.get_plugin(name)
                if not metadata:
                    return None
                
                # Get execution logs
                cursor.execute('''
                    SELECT * FROM plugin_execution_logs
                    WHERE plugin_id = (SELECT id FROM plugins WHERE name = ?)
                    ORDER BY start_time DESC LIMIT 100
                ''', (name,))
                
                execution_logs = cursor.fetchall()
                
                # Get metrics
                cursor.execute('''
                    SELECT * FROM plugin_metrics
                    WHERE plugin_id = (SELECT id FROM plugins WHERE name = ?)
                    ORDER BY timestamp DESC LIMIT 100
                ''', (name,))
                
                metrics = cursor.fetchall()
                
                return {
                    'metadata': metadata.to_dict(),
                    'execution_logs': execution_logs,
                    'metrics': metrics,
                    'statistics': self.get_plugin_statistics(name)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to export plugin data for {name}: {e}")
            return None

def main():
    """Main function for testing the plugin registry"""
    registry = PluginRegistryDatabase()
    
    # Create sample plugin metadata
    sample_plugin = PluginMetadata(
        name="test_plugin",
        version="1.0.0",
        description="Test plugin for registry",
        author="Test Author",
        email="test@example.com",
        category=PluginCategory.UTILITY,
        status=PluginStatus.REGISTERED,
        file_path="/path/to/test_plugin.py",
        dependencies=["json", "time"],
        permissions=["read_config"],
        security_level="LOW",
        security_validated=True,
        file_hash="abc123"
    )
    
    # Register plugin
    if registry.register_plugin(sample_plugin):
        print("Plugin registered successfully!")
        
        # Get plugin
        retrieved = registry.get_plugin("test_plugin")
        print(f"Retrieved plugin: {retrieved.name}")
        
        # Update status
        registry.update_plugin_status("test_plugin", PluginStatus.ACTIVE)
        
        # Log execution
        registry.log_plugin_execution("test_plugin", "exec_123", 500, True)
        
        # Get statistics
        stats = registry.get_plugin_statistics("test_plugin")
        print(f"Plugin statistics: {stats}")
        
        # Export data
        data = registry.export_plugin_data("test_plugin")
        print(f"Exported data keys: {list(data.keys())}")

if __name__ == "__main__":
    main()
