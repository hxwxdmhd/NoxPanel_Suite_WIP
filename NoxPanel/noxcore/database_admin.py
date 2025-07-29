"""
Database Administration and Utility Tools for NoxGuard---NoxPanel
Provides command-line tools for database management
"""

import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .database_service import DatabaseService, get_database_service
from .migrations import MigrationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseAdmin:
    """Database administration utilities"""
    
    def __init__((self, db_path: str = None) -> None:
        self.db_service = get_database_service(db_path)
    
    def status(self) -> Dict[str, Any]:
        """Get comprehensive database status"""
        return self.db_service.get_status()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return self.db_service.get_health_metrics()
    
    def backup(self, backup_path: str = None) -> bool:
        """Create database backup"""
        return self.db_service.backup_database(backup_path)
    
    def restore(self, backup_path: str) -> bool:
        """Restore database from backup"""
        return self.db_service.restore_database(backup_path)
    
    def optimize(self) -> bool:
        """Optimize database"""
        return self.db_service.optimize_database()
    
    def cleanup(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data"""
        return self.db_service.cleanup_old_data(days)
    
    def create_user(self, username: str, password: str, email: str = None, 
                   role: str = 'user') -> Optional[int]:
        """Create a new user"""
        return self.db_service.users.create_user(username, password, email, role)
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        try:
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, role, created_at, last_login, active
                    FROM users ORDER BY created_at DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    def reset_user_password(self, username: str, new_password: str) -> bool:
        """Reset user password"""
        try:
            import hashlib
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET password_hash = ? WHERE username = ?
                """, (password_hash, username))
                
                if cursor.rowcount > 0:
                    logger.info(f"Password reset for user: {username}")
                    return True
                else:
                    logger.warning(f"User not found: {username}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            return False
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user"""
        try:
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET active = 0 WHERE username = ?
                """, (username,))
                
                if cursor.rowcount > 0:
                    logger.info(f"User deactivated: {username}")
                    return True
                else:
                    logger.warning(f"User not found: {username}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to deactivate user: {e}")
            return False
    
    def export_data(self, export_path: str, table: str = None) -> bool:
        """Export database data to JSON"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if table:
                    # Export specific table
                    cursor.execute(f"SELECT * FROM {table}")
                    data[table] = [dict(row) for row in cursor.fetchall()]
                else:
                    # Export all tables
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table_name in tables:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        data[table_name] = [dict(row) for row in cursor.fetchall()]
            
            # Add metadata
            data['_metadata'] = {
                'export_time': datetime.now().isoformat(),
                'database_path': str(self.db_service.db_path),
                'schema_version': self.db_service.migration_manager.get_current_version()
            }
            
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Data exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            return False
    
    def import_knowledge(self, import_path: str) -> int:
        """Import knowledge items from JSON file"""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            imported_count = 0
            
            if 'knowledge_items' in data:
                for item in data['knowledge_items']:
                    knowledge_id = self.db_service.knowledge.create_knowledge_item(
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        category=item.get('category', 'imported'),
                        author_id=item.get('author_id'),
                        content_type=item.get('content_type', 'text'),
                        source=item.get('source'),
                        source_url=item.get('source_url'),
                        metadata=item.get('metadata', {}),
                        search_keywords=item.get('search_keywords', '')
                    )
                    
                    if knowledge_id:
                        imported_count += 1
            
            logger.info(f"Imported {imported_count} knowledge items")
            return imported_count
            
        except Exception as e:
            logger.error(f"Knowledge import failed: {e}")
            return 0
    
    def generate_report(self, output_path: str = None) -> str:
        """Generate comprehensive database report"""
        try:
            status = self.status()
            health = self.health_check()
            users = self.list_users()
            
            report = {
                'report_generated': datetime.now().isoformat(),
                'database_status': status,
                'health_metrics': health,
                'user_summary': {
                    'total_users': len(users),
                    'active_users': len([u for u in users if u['active']]),
                    'admin_users': len([u for u in users if u['role'] == 'admin']),
                    'recent_logins': len([u for u in users if u['last_login'] and 
                                        datetime.fromisoformat(u['last_login']) > 
                                        datetime.now() - timedelta(days=7)])
                },
                'recommendations': self._generate_recommendations(status, health)
            }
            
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                logger.info(f"Report saved to: {output_path}")
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {e}"
    
    def _generate_recommendations(self, status: Dict[str, Any], 
                                health: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on database status"""
        recommendations = []
        
        # Check database size
        if status.get('database_size_mb', 0) > 500:
            recommendations.append("Database size is large (>500MB). Consider archiving old data.")
        
        # Check connection pool utilization
        pool_util = health.get('connection_pool', {}).get('utilization', 0)
        if pool_util > 80:
            recommendations.append("Connection pool utilization is high. Consider increasing pool size.")
        
        # Check recent activity
        if status.get('recent_activity_24h', 0) == 0:
            recommendations.append("No recent activity detected. Check if the system is being used.")
        
        # Check for pending migrations
        if status.get('migrations_pending', 0) > 0:
            recommendations.append("Pending database migrations detected. Apply migrations.")
        
        # Check integrity
        if health.get('health_status') != 'healthy':
            recommendations.append("Database integrity issues detected. Run optimization or restore from backup.")
        
        # Performance recommendations
        if status.get('table_counts', {}).get('audit_logs', 0) > 100000:
            recommendations.append("Large number of audit logs. Consider enabling automatic cleanup.")
        
        return recommendations if recommendations else ["Database is healthy and well-maintained."]

def main() -> bool:
    """Command-line interface for database administration"""
    parser = argparse.ArgumentParser(description='NoxGuard Database Administration Tool')
    parser.add_argument('--db-path', help='Database file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show database status')
    
    # Health command
    subparsers.add_parser('health', help='Check database health')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--path', help='Backup file path')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_path', help='Backup file to restore from')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Optimize database')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Retention days')
    
    # User management commands
    user_parser = subparsers.add_parser('user', help='User management')
    user_subparsers = user_parser.add_subparsers(dest='user_command')
    
    # Create user
    create_user_parser = user_subparsers.add_parser('create', help='Create user')
    create_user_parser.add_argument('username', help='Username')
    create_user_parser.add_argument('password', help='Password')
    create_user_parser.add_argument('--email', help='Email address')
    create_user_parser.add_argument('--role', default='user', help='User role')
    
    # List users
    user_subparsers.add_parser('list', help='List users')
    
    # Reset password
    reset_password_parser = user_subparsers.add_parser('reset-password', help='Reset user password')
    reset_password_parser.add_argument('username', help='Username')
    reset_password_parser.add_argument('password', help='New password')
    
    # Deactivate user
    deactivate_parser = user_subparsers.add_parser('deactivate', help='Deactivate user')
    deactivate_parser.add_argument('username', help='Username')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('path', help='Export file path')
    export_parser.add_argument('--table', help='Specific table to export')
    
    # Import command
    import_parser = subparsers.add_parser('import-knowledge', help='Import knowledge items')
    import_parser.add_argument('path', help='JSON file to import')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate database report')
    report_parser.add_argument('--output', help='Output file path')
    
    # Migration commands
    migration_parser = subparsers.add_parser('migrate', help='Database migrations')
    migration_subparsers = migration_parser.add_subparsers(dest='migration_command')
    
    migration_subparsers.add_parser('status', help='Migration status')
    
    migrate_up_parser = migration_subparsers.add_parser('up', help='Apply migrations')
    migrate_up_parser.add_argument('--version', type=int, help='Target version')
    
    migrate_down_parser = migration_subparsers.add_parser('down', help='Rollback migrations')
    migrate_down_parser.add_argument('version', type=int, help='Target version')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize admin
    admin = DatabaseAdmin(args.db_path)
    
    try:
        # Execute commands
        if args.command == 'status':
            status = admin.status()
            logger.info(json.dumps(status, indent=2, default=str))
        
        elif args.command == 'health':
            health = admin.health_check()
            logger.info(json.dumps(health, indent=2, default=str))
        
        elif args.command == 'backup':
            success = admin.backup(args.path)
            sys.exit(0 if success else 1)
        
        elif args.command == 'restore':
            success = admin.restore(args.backup_path)
            sys.exit(0 if success else 1)
        
        elif args.command == 'optimize':
            success = admin.optimize()
            sys.exit(0 if success else 1)
        
        elif args.command == 'cleanup':
            stats = admin.cleanup(args.days)
            logger.info(f"Cleanup completed: {stats}")
        
        elif args.command == 'user':
            if args.user_command == 'create':
                user_id = admin.create_user(args.username, args.password, args.email, args.role)
                if user_id:
                    logger.info(f"User created with ID: {user_id}")
                else:
                    logger.error("Failed to create user")
                    sys.exit(1)
            
            elif args.user_command == 'list':
                users = admin.list_users()
                for user in users:
                    logger.info(f"{user['id']:3d} | {user['username']:20s} | {user['role']:10s} | {user['active']}")
            
            elif args.user_command == 'reset-password':
                success = admin.reset_user_password(args.username, args.password)
                sys.exit(0 if success else 1)
            
            elif args.user_command == 'deactivate':
                success = admin.deactivate_user(args.username)
                sys.exit(0 if success else 1)
        
        elif args.command == 'export':
            success = admin.export_data(args.path, args.table)
            sys.exit(0 if success else 1)
        
        elif args.command == 'import-knowledge':
            count = admin.import_knowledge(args.path)
            logger.info(f"Imported {count} knowledge items")
        
        elif args.command == 'report':
            report = admin.generate_report(args.output)
            if not args.output:
                logger.info(report)
        
        elif args.command == 'migrate':
            migration_manager = MigrationManager(args.db_path or 'data/db/noxpanel.db')
            
            if args.migration_command == 'status':
                status = migration_manager.status()
                logger.info(f"Current version: {status['current_version']}")
                logger.info(f"Target version: {status['target_version']}")
                logger.info(f"Pending migrations: {status['pending_count']}")
            
            elif args.migration_command == 'up':
                success = migration_manager.migrate_up(args.version)
                sys.exit(0 if success else 1)
            
            elif args.migration_command == 'down':
                success = migration_manager.migrate_down(args.version)
                sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)
    finally:
        admin.db_service.close()

if __name__ == '__main__':
    main()