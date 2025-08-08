"""
Database Migration System for NoxGuard---NoxPanel
Handles schema versioning and automated migrations
"""

import sqlite3
import logging
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .utils.datetime_utils import utc_now


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

class Migration:
    """Base class for database migrations"""
    
    def __init__(self, version: int, description: str) -> None:
        self.version = version
        self.description = description
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Apply the migration"""
        raise NotImplementedError("Subclasses must implement up()")
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Rollback the migration"""
        raise NotImplementedError("Subclasses must implement down()")

class InitialMigration(Migration):
    """Initial database schema migration"""
    
    def __init__(self) -> None:
        super().__init__(1, "Initial database schema with enhanced tables")
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Create initial schema"""
        from .database import NoxDatabase
        # The schema is already created by NoxDatabase.init_database()
        # This migration just records that it was applied
        pass
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Drop all tables"""
        tables = [
            'session_activities', 'sessions', 'api_tokens',
            'conversation_messages', 'conversations', 'ai_metrics', 'ai_feedback',
            'knowledge_item_tags', 'knowledge_relationships', 'knowledge_items', 'tags',
            'audit_logs', 'settings', 'devices', 'users'
        ]
        
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table}")

class MigrationManager:
    """Manages database migrations and schema versioning"""
    
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.migrations: List[Migration] = []
        self._register_migrations()
    
    def _register_migrations(self) -> bool:
        """Register all available migrations"""
        self.migrations = [
            InitialMigration(),
            # Future migrations would be added here
        ]
        # Sort by version
        self.migrations.sort(key=lambda m: m.version)
    
    @contextmanager
    def get_connection(self) -> bool:
        """Get database connection for migrations"""
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()
    
    def _ensure_migration_table(self, conn: sqlite3.Connection) -> bool:
        """Create migration tracking table if it doesn't exist"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_by TEXT DEFAULT 'system',
                execution_time REAL,
                checksum TEXT
            )
        """)
    
    def get_current_version(self) -> int:
        """Get current database schema version"""
        try:
            with self.get_connection() as conn:
                self._ensure_migration_table(conn)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(version) FROM schema_migrations")
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.Error as e:
            logger.warning(f"Could not determine current schema version: {e}")
            return 0
    
    def get_target_version(self) -> int:
        """Get latest available migration version"""
        return max(m.version for m in self.migrations) if self.migrations else 0
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        current_version = self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations"""
        try:
            with self.get_connection() as conn:
                self._ensure_migration_table(conn)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT version, description, applied_at, applied_by, execution_time
                    FROM schema_migrations
                    ORDER BY version
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def migrate_up(self, target_version: Optional[int] = None) -> bool:
        """Apply pending migrations up to target version"""
        try:
            if target_version is None:
                target_version = self.get_target_version()
            
            current_version = self.get_current_version()
            
            if current_version >= target_version:
                logger.info(f"Database is already at version {current_version}")
                return True
            
            pending = [m for m in self.migrations 
                      if current_version < m.version <= target_version]
            
            if not pending:
                logger.info("No pending migrations to apply")
                return True
            
            logger.info(f"Applying {len(pending)} migrations...")
            
            with self.get_connection() as conn:
                self._ensure_migration_table(conn)
                
                for migration in pending:
                    start_time = utc_now()
                    logger.info(f"Applying migration {migration.version}: {migration.description}")
                    
                    try:
                        # Apply the migration
                        migration.up(conn)
                        
                        # Record successful application
                        execution_time = (utc_now() - start_time).total_seconds()
                        conn.execute("""
                            INSERT INTO schema_migrations 
                            (version, description, applied_at, execution_time)
                            VALUES (?, ?, ?, ?)
                        """, (
                            migration.version,
                            migration.description,
                            utc_now().isoformat(),
                            execution_time
                        ))
                        
                        logger.info(f"Migration {migration.version} applied successfully in {execution_time:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"Migration {migration.version} failed: {e}")
                        raise
            
            logger.info(f"Successfully migrated from version {current_version} to {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def migrate_down(self, target_version: int) -> bool:
        """Rollback migrations down to target version"""
        try:
            current_version = self.get_current_version()
            
            if current_version <= target_version:
                logger.info(f"Database is already at or below version {target_version}")
                return True
            
            # Get migrations to rollback (in reverse order)
            to_rollback = [m for m in reversed(self.migrations) 
                          if target_version < m.version <= current_version]
            
            if not to_rollback:
                logger.info("No migrations to rollback")
                return True
            
            logger.info(f"Rolling back {len(to_rollback)} migrations...")
            
            with self.get_connection() as conn:
                for migration in to_rollback:
                    start_time = utc_now()
                    logger.info(f"Rolling back migration {migration.version}: {migration.description}")
                    
                    try:
                        # Rollback the migration
                        migration.down(conn)
                        
                        # Remove from migration table
                        conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))
                        
                        execution_time = (utc_now() - start_time).total_seconds()
                        logger.info(f"Migration {migration.version} rolled back successfully in {execution_time:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"Rollback of migration {migration.version} failed: {e}")
                        raise
            
            logger.info(f"Successfully rolled back from version {current_version} to {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Migration rollback failed: {e}")
            return False
    
    def status(self) -> Dict[str, Any]:
        """Get migration status information"""
        current_version = self.get_current_version()
        target_version = self.get_target_version()
        pending = self.get_pending_migrations()
        applied = self.get_applied_migrations()
        
        return {
            'current_version': current_version,
            'target_version': target_version,
            'pending_count': len(pending),
            'applied_count': len(applied),
            'pending_migrations': [
                {'version': m.version, 'description': m.description} 
                for m in pending
            ],
            'applied_migrations': applied,
            'needs_migration': len(pending) > 0
        }
    
    def auto_migrate(self) -> bool:
        """Automatically apply all pending migrations"""
        status = self.status()
        
        if not status['needs_migration']:
            logger.info("Database schema is up to date")
            return True
        
        logger.info(f"Auto-migration: {status['pending_count']} pending migrations")
        return self.migrate_up()
    
    def validate_schema(self) -> bool:
        """Validate current database schema"""
        try:
            with self.get_connection() as conn:
                # Check if all expected tables exist
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = {row[0] for row in cursor.fetchall()}
                
                expected_tables = {
                    'users', 'devices', 'settings', 'audit_logs',
                    'knowledge_items', 'tags', 'knowledge_item_tags', 'knowledge_relationships',
                    'conversations', 'conversation_messages', 'ai_metrics', 'ai_feedback',
                    'sessions', 'session_activities', 'api_tokens', 'schema_migrations'
                }
                
                missing_tables = expected_tables - tables
                extra_tables = tables - expected_tables
                
                if missing_tables:
                    logger.error(f"Missing tables: {missing_tables}")
                    return False
                
                if extra_tables:
                    logger.warning(f"Extra tables found: {extra_tables}")
                
                logger.info("Database schema validation passed")
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False

# CLI interface for migrations
def main() -> bool:
    """Command-line interface for migrations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NoxGuard Database Migration Tool')
    parser.add_argument('--db-path', default='data/db/noxpanel.db', help='Database path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Apply migrations')
    migrate_parser.add_argument('--version', type=int, help='Target version (default: latest)')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('version', type=int, help='Target version')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate database schema')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = MigrationManager(args.db_path)
    
    if args.command == 'status':
        status = manager.status()
        logger.info(f"Current version: {status['current_version']}")
        logger.info(f"Target version: {status['target_version']}")
        logger.info(f"Pending migrations: {status['pending_count']}")
        logger.info(f"Applied migrations: {status['applied_count']}")
        
        if status['pending_migrations']:
            logger.info("Pending migrations:")
            for migration in status['pending_migrations']:
                logger.info(f"  {migration['version']}: {migration['description']}")
    
    elif args.command == 'migrate':
        success = manager.migrate_up(args.version)
        exit(0 if success else 1)
    
    elif args.command == 'rollback':
        success = manager.migrate_down(args.version)
        exit(0 if success else 1)
    
    elif args.command == 'validate':
        success = manager.validate_schema()
        exit(0 if success else 1)

if __name__ == '__main__':
    main()