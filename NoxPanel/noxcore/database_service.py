"""
Database Service for NoxGuard---NoxPanel
High-level service that orchestrates database operations
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from .database import NoxDatabase
from .migrations import MigrationManager
from .repositories import (
    AuditRepository,
    ConversationRepository,
    KnowledgeRepository,
    SessionRepository,
    TagRepository,
    UserRepository,
)


# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details,
        "request_ip": request_ip,
        "severity": "security",
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")


def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event(
        "access_attempt", {"endpoint": endpoint, "user_id": user_id, "success": success}
    )


logger = logging.getLogger(__name__)


class DatabaseService:
    """Main database service for NoxGuard---NoxPanel"""

    def __init__(
        self, db_path: str = None, auto_migrate: bool = True, pool_size: int = 10
    ) -> None:
        """Initialize database service"""
        if db_path is None:
            db_path = os.getenv("NOX_DB_PATH", "data/db/noxpanel.db")

        self.db_path = db_path
        self.auto_migrate = auto_migrate

        # Initialize database
        self.db = NoxDatabase(db_path, pool_size)

        # Initialize migration manager
        self.migration_manager = MigrationManager(db_path)

        # Apply migrations if enabled
        if auto_migrate:
            self._apply_migrations()

        # Initialize repositories
        self.users = UserRepository(self.db)
        self.knowledge = KnowledgeRepository(self.db)
        self.tags = TagRepository(self.db)
        self.conversations = ConversationRepository(self.db)
        self.sessions = SessionRepository(self.db)
        self.audit = AuditRepository(self.db)

        logger.info("Database service initialized successfully")

    def _apply_migrations(self) -> bool:
        """Apply pending migrations"""
        try:
            status = self.migration_manager.status()
            if status["needs_migration"]:
                logger.info(f"Applying {status['pending_count']} pending migrations")
                success = self.migration_manager.auto_migrate()
                if success:
                    logger.info("Database migrations applied successfully")
                else:
                    logger.error("Failed to apply database migrations")
                    raise Exception("Migration failed")
            else:
                logger.info("Database schema is up to date")
        except Exception as e:
            logger.error(f"Migration error: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive database status"""
        try:
            migration_status = self.migration_manager.status()

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Get table counts
                table_counts = {}
                tables = [
                    "users",
                    "devices",
                    "knowledge_items",
                    "tags",
                    "conversations",
                    "conversation_messages",
                    "sessions",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]

                # Get database size
                cursor.execute(
                    "SELECT page_count * page_size as size "
                    "FROM pragma_page_count(), pragma_page_size()"
                )
                db_size = cursor.fetchone()[0]

                # Get recent activity
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM audit_logs
                    WHERE timestamp > datetime('now', '-24 hours')
                """
                )
                recent_activity = cursor.fetchone()[0]

                return {
                    "database_path": str(self.db_path),
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / 1024 / 1024, 2),
                    "schema_version": migration_status["current_version"],
                    "migrations_pending": migration_status["pending_count"],
                    "table_counts": table_counts,
                    "recent_activity_24h": recent_activity,
                    "connection_pool_size": self.db.pool.pool_size,
                    "last_updated": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
            return {"error": str(e)}

    def backup_database(self, backup_path: str = None) -> bool:
        """Create database backup"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"data/backups/noxpanel_backup_{timestamp}.db"

            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            with self.db.get_connection() as conn:
                # Use SQLite backup API
                conn.execute("PRAGMA wal_checkpoint").fetchone()

                # Copy database file
                import shutil

                shutil.copy2(self.db_path, backup_path)

                # Create backup metadata
                metadata = {
                    "backup_time": datetime.now().isoformat(),
                    "original_path": str(self.db_path),
                    "schema_version": self.migration_manager.get_current_version(),
                    "database_size": backup_file.stat().st_size,
                }

                metadata_path = backup_file.with_suffix(".json")
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)

                logger.info(f"Database backup created: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Close current connections
            self.db.close()

            # Backup current database
            current_backup = (
                f"{self.db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            import shutil

            shutil.copy2(self.db_path, current_backup)

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)

            # Reinitialize database
            self.db = NoxDatabase(self.db_path)

            # Verify restored database
            if self.migration_manager.validate_schema():
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                # Restore failed, rollback
                shutil.copy2(current_backup, self.db_path)
                self.db = NoxDatabase(self.db_path)
                logger.error("Database restore failed validation, rolled back")
                return False

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False

    def optimize_database(self) -> bool:
        """Optimize database performance"""
        try:
            with self.db.get_connection() as conn:
                # Run VACUUM to reclaim space and optimize
                conn.execute("VACUUM")

                # Analyze tables for query optimization
                conn.execute("ANALYZE")

                # Update table statistics
                conn.executescript(
                    """
                    PRAGMA optimize;
                    PRAGMA wal_checkpoint(TRUNCATE);
                """
                )

                logger.info("Database optimization completed")
                return True

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False

    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        try:
            cleanup_stats = {}
            cutoff_date = datetime.now() - timedelta(days=days)

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Clean up old audit logs
                cursor.execute(
                    """
                    DELETE FROM audit_logs
                    WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )
                cleanup_stats["audit_logs"] = cursor.rowcount

                # Clean up expired sessions
                cursor.execute(
                    """
                    DELETE FROM sessions
                    WHERE expires_at < ? OR last_activity < ?
                """,
                    (datetime.now().isoformat(), cutoff_date.isoformat()),
                )
                cleanup_stats["sessions"] = cursor.rowcount

                # Clean up old conversation messages
                # (keep conversations but remove old messages)
                cursor.execute(
                    """
                    DELETE FROM conversation_messages
                    WHERE timestamp < ? AND conversation_id IN (
                        SELECT id FROM conversations WHERE ended_at < ?
                    )
                """,
                    (cutoff_date.isoformat(), cutoff_date.isoformat()),
                )
                cleanup_stats["conversation_messages"] = cursor.rowcount

                # Clean up orphaned data
                cursor.execute(
                    """
                    DELETE FROM knowledge_item_tags
                    WHERE knowledge_item_id NOT IN (SELECT id FROM knowledge_items)
                """
                )
                cleanup_stats["orphaned_tags"] = cursor.rowcount

                logger.info(f"Data cleanup completed: {cleanup_stats}")
                return cleanup_stats

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {}

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get database health metrics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]

                # Get database stats
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()

                # Get cache statistics
                cursor.execute("PRAGMA cache_size")
                cache_size = cursor.fetchone()[0]

                # Check for locked tables
                cursor.execute("PRAGMA lock_status")
                lock_status = cursor.fetchall()

                # Get active connections (estimated)
                active_connections = len(self.db.pool._pool)

                return {
                    "integrity_check": integrity_result,
                    "database_info": [
                        dict(zip(["seq", "name", "file"], row)) for row in db_info
                    ],
                    "cache_size": cache_size,
                    "lock_status": lock_status,
                    "connection_pool": {
                        "active_connections": active_connections,
                        "pool_size": self.db.pool.pool_size,
                        "utilization": round(
                            (self.db.pool.pool_size - active_connections)
                            / self.db.pool.pool_size
                            * 100,
                            2,
                        ),
                    },
                    "health_status": "healthy"
                    if integrity_result == "ok"
                    else "warning",
                    "checked_at": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "health_status": "error",
                "error": str(e),
                "checked_at": datetime.now().isoformat(),
            }

    def close(self) -> bool:
        """Close database service"""
        try:
            self.db.close()
            logger.info("Database service closed")
        except Exception as e:
            logger.error(f"Error closing database service: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service(
    db_path: str | None = None, auto_migrate: bool = True
) -> DatabaseService:
    """Get or create global database service instance.

    If a database service has already been created but a different ``db_path`` is
    requested, a new instance will be initialized with the provided path.
    """

    global _db_service

    if _db_service is None or (db_path and str(_db_service.db_path) != db_path):
        _db_service = DatabaseService(db_path, auto_migrate)

    return _db_service


def close_database_service() -> bool:
    """Close global database service"""
    global _db_service

    if _db_service is not None:
        _db_service.close()
        _db_service = None


# Export main classes and functions
__all__ = ["DatabaseService", "get_database_service", "close_database_service"]
