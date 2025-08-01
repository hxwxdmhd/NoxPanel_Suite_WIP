"""
Test suite for MariaDB Migration functionality
Tests database migration capabilities and compatibility
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import our modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from noxcore.database_service import DatabaseService
from noxcore.mariadb_migration import (
    DatabaseMigrator, DatabaseFactory, MARIADB_AVAILABLE,
    MariaDBDatabase, MariaDBConnectionPool
)

class TestDatabaseFactory(unittest.TestCase):
    """Test database factory functionality"""
    
    def test_create_sqlite_database(self):
        """Test creating SQLite database via factory"""
        config = {
            'type': 'sqlite',
            'path': ':memory:',
            'pool_size': 5
        }
        
        db = DatabaseFactory.create_database(config)
        self.assertIsNotNone(db)
        # Should be a NoxDatabase instance for SQLite
        self.assertTrue(hasattr(db, 'get_connection'))
    
    def test_create_mariadb_database_without_pymysql(self):
        """Test MariaDB creation fails without PyMySQL"""
        config = {
            'type': 'mariadb',
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }
        
        if not MARIADB_AVAILABLE:
            with self.assertRaises(ImportError):
                DatabaseFactory.create_database(config)
        else:
            # If PyMySQL is available, we expect a different error (connection failure)
            # since we're not actually connecting to a real MariaDB
            try:
                db = DatabaseFactory.create_database(config)
                # If creation succeeds, it should be a MariaDB instance
                self.assertIsInstance(db, MariaDBDatabase)
            except Exception as e:
                # Expected if no actual MariaDB server available
                self.assertIn('connect', str(e).lower())
    
    def test_unsupported_database_type(self):
        """Test error for unsupported database type"""
        config = {
            'type': 'postgresql',
            'host': 'localhost'
        }
        
        with self.assertRaises(ValueError):
            DatabaseFactory.create_database(config)

@unittest.skipUnless(MARIADB_AVAILABLE, "PyMySQL not available")
class TestMariaDBConnectionPool(unittest.TestCase):
    """Test MariaDB connection pool (mocked)"""
    
    def setUp(self):
        # Mock PyMySQL connection
        self.mock_connection = Mock()
        self.mock_connection.ping = Mock()
        self.mock_connection.close = Mock()
        
    @patch('noxcore.mariadb_migration.pymysql.connect')
    def test_connection_pool_creation(self, mock_connect):
        """Test connection pool creation"""
        mock_connect.return_value = self.mock_connection
        
        pool = MariaDBConnectionPool(
            host='localhost',
            port=3306,
            user='test',
            password='test',
            database='test',
            pool_size=3
        )
        
        self.assertEqual(pool.pool_size, 3)
        self.assertEqual(len(pool._pool), 3)
        self.assertEqual(mock_connect.call_count, 3)
    
    @patch('noxcore.mariadb_migration.pymysql.connect')
    def test_get_return_connection(self, mock_connect):
        """Test getting and returning connections"""
        mock_connect.return_value = self.mock_connection
        
        pool = MariaDBConnectionPool(
            host='localhost',
            port=3306,
            user='test',
            password='test',
            database='test',
            pool_size=2
        )
        
        # Get connection
        conn = pool.get_connection()
        self.assertIsNotNone(conn)
        self.mock_connection.ping.assert_called_once()
        
        # Return connection
        pool.return_connection(conn)
        self.assertEqual(len(pool._pool), 2)

class TestDatabaseMigrator(unittest.TestCase):
    """Test database migration functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sqlite_db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_service = DatabaseService(self.sqlite_db_path, auto_migrate=True)
        
        # MariaDB config (for testing purposes)
        self.mariadb_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test',
            'password': 'test',
            'database': 'noxpanel_test',
            'pool_size': 5
        }
        
        self.migrator = DatabaseMigrator(self.db_service.db, self.mariadb_config)
    
    def tearDown(self):
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_migrator_initialization(self):
        """Test migrator initialization"""
        self.assertIsNotNone(self.migrator.sqlite_db)
        self.assertEqual(self.migrator.mariadb_config, self.mariadb_config)
        self.assertIsNone(self.migrator.mariadb_db)
    
    def test_migrator_without_pymysql(self):
        """Test migrator behavior without PyMySQL"""
        if not MARIADB_AVAILABLE:
            with self.assertRaises(ImportError):
                self.migrator.connect_mariadb()
    
    @unittest.skipUnless(MARIADB_AVAILABLE, "PyMySQL not available")
    @patch('noxcore.mariadb_migration.MariaDBDatabase')
    def test_connect_mariadb(self, mock_mariadb_class):
        """Test MariaDB connection"""
        mock_db = Mock()
        mock_mariadb_class.return_value = mock_db
        
        result = self.migrator.connect_mariadb()
        
        self.assertEqual(result, mock_db)
        self.assertEqual(self.migrator.mariadb_db, mock_db)
        mock_mariadb_class.assert_called_once_with(**self.mariadb_config)
    
    @unittest.skipUnless(MARIADB_AVAILABLE, "PyMySQL not available")
    @patch('noxcore.mariadb_migration.MariaDBDatabase')
    def test_validate_mariadb_connection(self, mock_mariadb_class):
        """Test MariaDB connection validation"""
        # Setup mock
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'VERSION()': '10.5.8-MariaDB'}
        
        mock_mariadb_class.return_value = mock_db
        
        # Test validation
        result = self.migrator.validate_mariadb_connection()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_with("SELECT VERSION()")
    
    def test_create_migration_report(self):
        """Test migration report creation"""
        stats = {
            'start_time': datetime(2023, 1, 1, 10, 0, 0),
            'end_time': datetime(2023, 1, 1, 10, 5, 30),
            'duration': 330.0,
            'total_records': 1500,
            'tables_migrated': {
                'users': 100,
                'knowledge_items': 500,
                'audit_logs': 900
            },
            'errors': []
        }
        
        report = self.migrator.create_migration_report(stats)
        
        self.assertIn('Migration Report', report)
        self.assertIn('Duration: 330.00 seconds', report)
        self.assertIn('Total records migrated: 1500', report)
        self.assertIn('users: 100 records', report)
        self.assertIn('knowledge_items: 500 records', report)
        self.assertIn('successfully with no errors', report)
    
    def test_create_migration_report_with_errors(self):
        """Test migration report with errors"""
        stats = {
            'start_time': datetime(2023, 1, 1, 10, 0, 0),
            'end_time': datetime(2023, 1, 1, 10, 2, 0),
            'duration': 120.0,
            'total_records': 50,
            'tables_migrated': {
                'users': 50
            },
            'errors': ['Failed to migrate table sessions: Connection lost']
        }
        
        report = self.migrator.create_migration_report(stats)
        
        self.assertIn('Errors encountered:', report)
        self.assertIn('Failed to migrate table sessions', report)

class TestMigrationIntegration(unittest.TestCase):
    """Integration tests for migration functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sqlite_db_path = os.path.join(self.temp_dir, 'test_migration.db')
        self.db_service = DatabaseService(self.sqlite_db_path, auto_migrate=True)
        
        # Create some test data
        self._create_test_data()
        
        self.mariadb_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test',
            'password': 'test',
            'database': 'noxpanel_test'
        }
    
    def tearDown(self):
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """Create test data in SQLite database"""
        # Create test users
        user1_id = self.db_service.users.create_user('testuser1', 'password123', 'user1@test.com', 'user')
        user2_id = self.db_service.users.create_user('testuser2', 'password456', 'user2@test.com', 'admin')
        
        # Create test knowledge items
        self.db_service.knowledge.create_knowledge_item(
            'Test Knowledge 1',
            'This is test content for knowledge item 1',
            'testing',
            user1_id
        )
        
        self.db_service.knowledge.create_knowledge_item(
            'Test Knowledge 2', 
            'This is test content for knowledge item 2',
            'testing',
            user2_id
        )
        
        # Create test audit logs
        for i in range(5):
            self.db_service.audit.log_action(
                user_id=user1_id,
                action=f'test_action_{i}',
                resource_type='test',
                resource_id=str(i),
                details={'test': True, 'iteration': i}
            )
    
    def test_sqlite_data_creation(self):
        """Test that test data was created in SQLite"""
        with self.db_service.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check users
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            self.assertGreaterEqual(user_count, 2)  # At least 2 test users + admin
            
            # Check knowledge items
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            knowledge_count = cursor.fetchone()[0]
            self.assertEqual(knowledge_count, 2)
            
            # Check audit logs
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            audit_count = cursor.fetchone()[0]
            self.assertGreaterEqual(audit_count, 5)
    
    @unittest.skipUnless(MARIADB_AVAILABLE, "PyMySQL not available")
    @patch('noxcore.mariadb_migration.MariaDBDatabase')
    def test_migration_data_preparation(self, mock_mariadb_class):
        """Test migration data preparation without actual MariaDB"""
        # Setup mock MariaDB
        mock_db = Mock()
        mock_mariadb_class.return_value = mock_db
        
        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock validation
        mock_cursor.fetchone.return_value = {'VERSION()': '10.5.8-MariaDB'}
        
        migrator = DatabaseMigrator(self.db_service.db, self.mariadb_config)
        
        # Test connection validation
        result = migrator.validate_mariadb_connection()
        self.assertTrue(result)
        
        # Verify mock was called
        mock_cursor.execute.assert_called_with("SELECT VERSION()")

class TestMigrationCLI(unittest.TestCase):
    """Test migration CLI functionality"""
    
    def test_migration_configuration_parsing(self):
        """Test parsing migration configuration"""
        config = {
            'source': {
                'type': 'sqlite',
                'path': '/path/to/source.db'
            },
            'target': {
                'type': 'mariadb',
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': 'password',
                'database': 'noxpanel'
            },
            'migration': {
                'batch_size': 1000,
                'validate': True
            }
        }
        
        # Test configuration structure
        self.assertIn('source', config)
        self.assertIn('target', config)
        self.assertIn('migration', config)
        
        # Test source config
        self.assertEqual(config['source']['type'], 'sqlite')
        self.assertIn('path', config['source'])
        
        # Test target config
        self.assertEqual(config['target']['type'], 'mariadb')
        self.assertIn('host', config['target'])
        self.assertIn('database', config['target'])
        
        # Test migration config
        self.assertEqual(config['migration']['batch_size'], 1000)
        self.assertTrue(config['migration']['validate'])

if __name__ == '__main__':
    unittest.main()