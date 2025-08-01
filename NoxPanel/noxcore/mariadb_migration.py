"""
MariaDB Migration Module for NoxGuard---NoxPanel System
Provides database migration and compatibility between SQLite and MariaDB
"""

import logging
import os
import json
import time
import threading
from typing import Optional, Dict, List, Any, Union, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pymysql
    import pymysql.cursors
    MARIADB_AVAILABLE = True
except ImportError:
    pymysql = None
    MARIADB_AVAILABLE = False

import sqlite3
from .database import NoxDatabase, DatabaseConnectionPool

logger = logging.getLogger(__name__)

class MariaDBConnectionPool:
    """MariaDB connection pool for improved performance"""
    
    def __init__(self, host: str, port: int, user: str, password: str, 
                 database: str, pool_size: int = 10, timeout: float = 30.0):
        if not MARIADB_AVAILABLE:
            raise ImportError("PyMySQL is required for MariaDB support. Install with: pip install pymysql")
            
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool = []
        self._lock = threading.Lock()
        self._create_pool()
    
    def _create_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.append(conn)
    
    def _create_connection(self):
        """Create a new MariaDB connection"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=self.timeout
        )
    
    def get_connection(self):
        """Get connection from pool"""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                # Test connection is still alive
                try:
                    conn.ping(reconnect=True)
                    return conn
                except:
                    # Connection is dead, create new one
                    return self._create_connection()
            else:
                return self._create_connection()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        with self._lock:
            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
            else:
                conn.close()
    
    def close_all(self):
        """Close all connections in pool"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except:
                    pass
            self._pool.clear()

class MariaDBDatabase:
    """MariaDB database implementation compatible with NoxDatabase interface"""
    
    def __init__(self, host: str, port: int, user: str, password: str, 
                 database: str, pool_size: int = 10):
        self.pool = MariaDBConnectionPool(host, port, user, password, database, pool_size)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.pool.database}")
            cursor.execute(f"USE {self.pool.database}")
            
            # Create tables with MariaDB-specific syntax
            self._create_tables(cursor)
    
    def _create_tables(self, cursor):
        """Create all necessary tables"""
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'user', 'viewer') DEFAULT 'user',
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_active (active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Knowledge items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content LONGTEXT NOT NULL,
                category VARCHAR(100),
                tags JSON,
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_title (title),
                INDEX idx_category (category),
                INDEX idx_created_by (created_by),
                FULLTEXT idx_content (title, content)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                color VARCHAR(7) DEFAULT '#007bff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500),
                user_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT NOT NULL,
                role ENUM('user', 'assistant', 'system') NOT NULL,
                content LONGTEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                INDEX idx_conversation_id (conversation_id),
                INDEX idx_role (role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(255) PRIMARY KEY,
                user_id INT,
                data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_expires_at (expires_at),
                INDEX idx_active (active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action VARCHAR(255) NOT NULL,
                resource_type VARCHAR(100),
                resource_id VARCHAR(255),
                details JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_action (action),
                INDEX idx_timestamp (timestamp),
                INDEX idx_resource (resource_type, resource_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key_name VARCHAR(255) PRIMARY KEY,
                value JSON NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Migration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_migration_name (migration_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic return to pool"""
        conn = self.pool.get_connection()
        try:
            yield conn
        finally:
            self.pool.return_connection(conn)
    
    def close(self):
        """Close all connections"""
        self.pool.close_all()

class DatabaseMigrator:
    """Handles migration between SQLite and MariaDB"""
    
    def __init__(self, sqlite_db: NoxDatabase, mariadb_config: Dict[str, Any]):
        self.sqlite_db = sqlite_db
        self.mariadb_config = mariadb_config
        self.mariadb_db = None
        
    def connect_mariadb(self) -> MariaDBDatabase:
        """Connect to MariaDB"""
        if not MARIADB_AVAILABLE:
            raise ImportError("PyMySQL is required for MariaDB migration. Install with: pip install pymysql")
        
        self.mariadb_db = MariaDBDatabase(**self.mariadb_config)
        return self.mariadb_db
    
    def validate_mariadb_connection(self) -> bool:
        """Validate MariaDB connection and configuration"""
        try:
            if not self.mariadb_db:
                self.connect_mariadb()
            
            with self.mariadb_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                logger.info(f"Connected to MariaDB version: {version}")
                return True
        except Exception as e:
            logger.error(f"MariaDB connection validation failed: {e}")
            return False
    
    def migrate_data(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Migrate data from SQLite to MariaDB"""
        if not self.validate_mariadb_connection():
            raise ConnectionError("Cannot connect to MariaDB")
        
        migration_stats = {
            'start_time': datetime.now(),
            'tables_migrated': {},
            'total_records': 0,
            'errors': []
        }
        
        tables = ['users', 'knowledge_items', 'tags', 'conversations', 'messages', 
                 'sessions', 'audit_logs', 'settings']
        
        for table in tables:
            try:
                count = self._migrate_table(table, batch_size)
                migration_stats['tables_migrated'][table] = count
                migration_stats['total_records'] += count
                logger.info(f"Migrated {count} records from {table}")
            except Exception as e:
                error_msg = f"Failed to migrate table {table}: {e}"
                logger.error(error_msg)
                migration_stats['errors'].append(error_msg)
        
        migration_stats['end_time'] = datetime.now()
        migration_stats['duration'] = (migration_stats['end_time'] - migration_stats['start_time']).total_seconds()
        
        return migration_stats
    
    def _migrate_table(self, table_name: str, batch_size: int) -> int:
        """Migrate a single table"""
        total_count = 0
        
        # Get data from SQLite
        with self.sqlite_db.get_connection() as sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = sqlite_cursor.fetchone()[0]
            
            if total_records == 0:
                return 0
            
            # Get column info
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # Process in batches
            offset = 0
            while offset < total_records:
                sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    break
                
                # Insert into MariaDB
                self._insert_batch_mariadb(table_name, columns, rows)
                
                total_count += len(rows)
                offset += batch_size
                
                # Progress logging
                if offset % (batch_size * 10) == 0:
                    logger.info(f"Migrated {offset}/{total_records} records from {table_name}")
        
        return total_count
    
    def _insert_batch_mariadb(self, table_name: str, columns: List[str], rows: List[tuple]):
        """Insert a batch of rows into MariaDB"""
        if not rows:
            return
        
        # Prepare SQL
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Handle special cases for data conversion
        converted_rows = []
        for row in rows:
            converted_row = list(row)
            for i, value in enumerate(converted_row):
                if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                    # Try to parse JSON
                    try:
                        json.loads(value)  # Validate JSON
                    except:
                        converted_row[i] = value  # Keep as string if not valid JSON
            converted_rows.append(tuple(converted_row))
        
        with self.mariadb_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, converted_rows)
    
    def create_migration_report(self, stats: Dict[str, Any]) -> str:
        """Create a detailed migration report"""
        report = f"""
MariaDB Migration Report
========================
Migration completed: {stats['end_time']}
Duration: {stats['duration']:.2f} seconds
Total records migrated: {stats['total_records']}

Table Migration Summary:
"""
        for table, count in stats['tables_migrated'].items():
            report += f"  {table}: {count} records\n"
        
        if stats['errors']:
            report += f"\nErrors encountered:\n"
            for error in stats['errors']:
                report += f"  - {error}\n"
        else:
            report += f"\nMigration completed successfully with no errors!\n"
        
        report += f"\nValidation recommended: Run data integrity checks\n"
        
        return report
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate the migration by comparing record counts"""
        validation_results = {
            'validated_at': datetime.now(),
            'table_comparisons': {},
            'total_sqlite_records': 0,
            'total_mariadb_records': 0,
            'validation_passed': True
        }
        
        tables = ['users', 'knowledge_items', 'tags', 'conversations', 'messages', 
                 'sessions', 'audit_logs', 'settings']
        
        for table in tables:
            try:
                # Count SQLite records
                with self.sqlite_db.get_connection() as sqlite_conn:
                    sqlite_cursor = sqlite_conn.cursor()
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Count MariaDB records
                with self.mariadb_db.get_connection() as mariadb_conn:
                    mariadb_cursor = mariadb_conn.cursor()
                    mariadb_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    mariadb_result = mariadb_cursor.fetchone()
                    mariadb_count = mariadb_result['COUNT(*)']
                
                validation_results['table_comparisons'][table] = {
                    'sqlite_count': sqlite_count,
                    'mariadb_count': mariadb_count,
                    'match': sqlite_count == mariadb_count
                }
                
                validation_results['total_sqlite_records'] += sqlite_count
                validation_results['total_mariadb_records'] += mariadb_count
                
                if sqlite_count != mariadb_count:
                    validation_results['validation_passed'] = False
                    logger.warning(f"Count mismatch in {table}: SQLite={sqlite_count}, MariaDB={mariadb_count}")
                
            except Exception as e:
                logger.error(f"Validation error for table {table}: {e}")
                validation_results['validation_passed'] = False
                validation_results['table_comparisons'][table] = {
                    'error': str(e)
                }
        
        return validation_results

class DatabaseFactory:
    """Factory for creating database instances based on configuration"""
    
    @staticmethod
    def create_database(config: Dict[str, Any]):
        """Create database instance based on configuration"""
        db_type = config.get('type', 'sqlite').lower()
        
        if db_type == 'sqlite':
            from .database import NoxDatabase
            db_path = config.get('path', 'data/noxpanel.db')
            pool_size = config.get('pool_size', 10)
            return NoxDatabase(db_path, pool_size)
        
        elif db_type == 'mariadb' or db_type == 'mysql':
            if not MARIADB_AVAILABLE:
                raise ImportError("PyMySQL is required for MariaDB support. Install with: pip install pymysql")
            
            return MariaDBDatabase(
                host=config['host'],
                port=config.get('port', 3306),
                user=config['user'],
                password=config['password'],
                database=config['database'],
                pool_size=config.get('pool_size', 10)
            )
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

# Export main classes
__all__ = ['MariaDBDatabase', 'DatabaseMigrator', 'DatabaseFactory', 'MARIADB_AVAILABLE']