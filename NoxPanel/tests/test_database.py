"""
Comprehensive test suite for NoxGuard---NoxPanel database system
Tests all database components including schema, migrations, and operations
"""

import unittest
import tempfile
import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Import our database components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from noxcore.database import NoxDatabase, DatabaseConnectionPool
from noxcore.migrations import MigrationManager, InitialMigration
from noxcore.repositories import (
    UserRepository, KnowledgeRepository, TagRepository,
    ConversationRepository, SessionRepository, AuditRepository
)
from noxcore.database_service import DatabaseService
from noxcore.database_admin import DatabaseAdmin

class TestDatabaseConnectionPool(unittest.TestCase):
    """Test database connection pool functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.pool = DatabaseConnectionPool(self.db_path, pool_size=3)
    
    def tearDown(self):
        self.pool.close_all()
        shutil.rmtree(self.temp_dir)
    
    def test_pool_creation(self):
        """Test connection pool is created correctly"""
        self.assertEqual(self.pool.pool_size, 3)
        self.assertIsNotNone(self.pool._pool)
    
    def test_get_return_connection(self):
        """Test getting and returning connections"""
        conn = self.pool.get_connection()
        self.assertIsNotNone(conn)
        
        # Test connection is functional
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        
        # Return connection
        self.pool.return_connection(conn)

class TestNoxDatabase(unittest.TestCase):
    """Test core database functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = NoxDatabase(self.db_path)
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database is initialized with correct schema"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check that all expected tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {
                'users', 'devices', 'settings', 'audit_logs',
                'knowledge_items', 'tags', 'knowledge_item_tags', 'knowledge_relationships',
                'conversations', 'conversation_messages', 'ai_metrics', 'ai_feedback',
                'sessions', 'session_activities', 'api_tokens'
            }
            
            self.assertTrue(expected_tables.issubset(tables))
    
    def test_default_admin_user(self):
        """Test default admin user is created"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin_user = cursor.fetchone()
            
            self.assertIsNotNone(admin_user)
            self.assertEqual(admin_user['role'], 'admin')
    
    def test_settings_initialization(self):
        """Test settings are initialized correctly"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'db_schema_version'")
            version = cursor.fetchone()
            
            self.assertIsNotNone(version)
            self.assertEqual(version[0], '1')

class TestMigrationManager(unittest.TestCase):
    """Test migration system functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.migration_manager = MigrationManager(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_migration_table_creation(self):
        """Test migration tracking table is created"""
        with self.migration_manager.get_connection() as conn:
            self.migration_manager._ensure_migration_table(conn)
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_migrations'
            """)
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
    
    def test_migration_status(self):
        """Test migration status reporting"""
        status = self.migration_manager.status()
        
        self.assertIn('current_version', status)
        self.assertIn('target_version', status)
        self.assertIn('pending_count', status)
        self.assertIn('needs_migration', status)
    
    def test_auto_migrate(self):
        """Test automatic migration"""
        success = self.migration_manager.auto_migrate()
        self.assertTrue(success)
        
        # Check that migration was recorded
        status = self.migration_manager.status()
        self.assertFalse(status['needs_migration'])

class TestUserRepository(unittest.TestCase):
    """Test user repository functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = NoxDatabase(self.db_path)
        self.user_repo = UserRepository(self.db)
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_user(self):
        """Test user creation"""
        user_id = self.user_repo.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            role='user'
        )
        
        self.assertIsNotNone(user_id)
        self.assertIsInstance(user_id, int)
    
    def test_get_user(self):
        """Test user retrieval"""
        # Create user first
        user_id = self.user_repo.create_user('testuser', 'testpass', 'test@example.com')
        
        # Get by ID
        user = self.user_repo.get_user(user_id=user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')
        
        # Get by username
        user = self.user_repo.get_user(username='testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user['id'], user_id)
    
    def test_authenticate_user(self):
        """Test user authentication"""
        self.user_repo.create_user('testuser', 'testpass', 'test@example.com')
        
        # Valid credentials
        user = self.user_repo.authenticate_user('testuser', 'testpass')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')
        
        # Invalid credentials
        user = self.user_repo.authenticate_user('testuser', 'wrongpass')
        self.assertIsNone(user)

class TestKnowledgeRepository(unittest.TestCase):
    """Test knowledge repository functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = NoxDatabase(self.db_path)
        self.knowledge_repo = KnowledgeRepository(self.db)
        self.user_repo = UserRepository(self.db)
        
        # Create test user
        self.user_id = self.user_repo.create_user('testuser', 'testpass')
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_knowledge_item(self):
        """Test knowledge item creation"""
        item_id = self.knowledge_repo.create_knowledge_item(
            title='Test Article',
            content='This is test content',
            category='testing',
            author_id=self.user_id
        )
        
        self.assertIsNotNone(item_id)
        self.assertIsInstance(item_id, int)
    
    def test_get_knowledge_item(self):
        """Test knowledge item retrieval"""
        item_id = self.knowledge_repo.create_knowledge_item(
            'Test Article', 'Test content', 'testing', self.user_id
        )
        
        item = self.knowledge_repo.get_knowledge_item(item_id)
        self.assertIsNotNone(item)
        self.assertEqual(item['title'], 'Test Article')
        self.assertEqual(item['author_id'], self.user_id)
    
    def test_search_knowledge_items(self):
        """Test knowledge search functionality"""
        # Create test items
        self.knowledge_repo.create_knowledge_item(
            'Python Tutorial', 'Learn Python programming', 'tutorial', self.user_id
        )
        self.knowledge_repo.create_knowledge_item(
            'JavaScript Guide', 'Learn JavaScript', 'tutorial', self.user_id
        )
        
        # Search for Python
        results = self.knowledge_repo.search_knowledge_items('Python')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Tutorial')
        
        # Search by category
        results = self.knowledge_repo.search_knowledge_items('', category='tutorial')
        self.assertEqual(len(results), 2)

class TestConversationRepository(unittest.TestCase):
    """Test conversation repository functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = NoxDatabase(self.db_path)
        self.conversation_repo = ConversationRepository(self.db)
        self.user_repo = UserRepository(self.db)
        
        # Create test user
        self.user_id = self.user_repo.create_user('testuser', 'testpass')
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_conversation(self):
        """Test conversation creation"""
        conv_id = self.conversation_repo.create_conversation(
            user_id=self.user_id,
            title='Test Conversation',
            model_name='test-model'
        )
        
        self.assertIsNotNone(conv_id)
        self.assertIsInstance(conv_id, int)
    
    def test_add_message(self):
        """Test adding messages to conversation"""
        conv_id = self.conversation_repo.create_conversation(self.user_id)
        
        msg_id = self.conversation_repo.add_message(
            conversation_id=conv_id,
            role='user',
            content='Hello, AI!',
            token_count=10
        )
        
        self.assertIsNotNone(msg_id)
    
    def test_get_conversation_with_messages(self):
        """Test retrieving conversation with messages"""
        conv_id = self.conversation_repo.create_conversation(self.user_id, title='Test Chat')
        
        # Add messages
        self.conversation_repo.add_message(conv_id, 'user', 'Hello')
        self.conversation_repo.add_message(conv_id, 'assistant', 'Hi there!')
        
        conversation = self.conversation_repo.get_conversation(conv_id, include_messages=True)
        
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation['title'], 'Test Chat')
        self.assertIn('messages', conversation)
        self.assertEqual(len(conversation['messages']), 2)

class TestSessionRepository(unittest.TestCase):
    """Test session repository functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = NoxDatabase(self.db_path)
        self.session_repo = SessionRepository(self.db)
        self.user_repo = UserRepository(self.db)
        
        # Create test user
        self.user_id = self.user_repo.create_user('testuser', 'testpass')
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_session(self):
        """Test session creation"""
        session_id = self.session_repo.create_session(
            user_id=self.user_id,
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, str)
    
    def test_get_session(self):
        """Test session retrieval"""
        session_id = self.session_repo.create_session(self.user_id, '127.0.0.1')
        
        session = self.session_repo.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session['user_id'], self.user_id)
    
    def test_invalidate_session(self):
        """Test session invalidation"""
        session_id = self.session_repo.create_session(self.user_id)
        
        # Session should be active
        session = self.session_repo.get_session(session_id)
        self.assertIsNotNone(session)
        
        # Invalidate session
        success = self.session_repo.invalidate_session(session_id)
        self.assertTrue(success)
        
        # Session should no longer be retrievable
        session = self.session_repo.get_session(session_id)
        self.assertIsNone(session)

class TestDatabaseService(unittest.TestCase):
    """Test database service integration"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_service = DatabaseService(self.db_path, auto_migrate=True)
    
    def tearDown(self):
        self.db_service.close()
        shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test service is initialized correctly"""
        self.assertIsNotNone(self.db_service.db)
        self.assertIsNotNone(self.db_service.users)
        self.assertIsNotNone(self.db_service.knowledge)
        self.assertIsNotNone(self.db_service.conversations)
        self.assertIsNotNone(self.db_service.sessions)
    
    def test_get_status(self):
        """Test service status reporting"""
        status = self.db_service.get_status()
        
        self.assertIn('database_path', status)
        self.assertIn('database_size_bytes', status)
        self.assertIn('schema_version', status)
        self.assertIn('table_counts', status)
    
    def test_backup_restore(self):
        """Test database backup and restore"""
        # Create some test data
        user_id = self.db_service.users.create_user('testuser', 'testpass')
        self.assertIsNotNone(user_id)
        
        # Create backup
        backup_path = os.path.join(self.temp_dir, 'backup.db')
        success = self.db_service.backup_database(backup_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(backup_path))
        
        # Modify data
        self.db_service.users.create_user('testuser2', 'testpass2')
        
        # Restore from backup
        success = self.db_service.restore_database(backup_path)
        self.assertTrue(success)
        
        # Check that second user is gone
        user2 = self.db_service.users.get_user(username='testuser2')
        self.assertIsNone(user2)
    
    def test_cleanup_old_data(self):
        """Test old data cleanup"""
        # Create some old audit logs by directly inserting with past dates
        with self.db_service.db.get_connection() as conn:
            old_date = (datetime.now() - timedelta(days=40)).isoformat()
            conn.execute("""
                INSERT INTO audit_logs (user_id, action, timestamp)
                VALUES (1, 'test_action', ?)
            """, (old_date,))
        
        # Run cleanup
        stats = self.db_service.cleanup_old_data(days=30)
        
        self.assertIn('audit_logs', stats)
        self.assertGreaterEqual(stats['audit_logs'], 1)

class TestDatabaseAdmin(unittest.TestCase):
    """Test database administration utilities"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        # Initialize database service first
        self.db_service = DatabaseService(self.db_path, auto_migrate=True)
        self.admin = DatabaseAdmin(self.db_path)
    
    def tearDown(self):
        try:
            self.admin.db_service.close()
        except:
            pass
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_create_list_users(self):
        """Test user management via admin"""
        # Create user
        user_id = self.admin.create_user('testuser', 'testpass', 'test@example.com', 'user')
        self.assertIsNotNone(user_id)
        
        # List users
        users = self.admin.list_users()
        self.assertGreaterEqual(len(users), 2)  # admin + testuser
        
        user_names = [u['username'] for u in users]
        self.assertIn('testuser', user_names)
        self.assertIn('admin', user_names)
    
    def test_export_import_data(self):
        """Test data export and import"""
        # Create some test data
        user_id = self.admin.create_user('testuser', 'testpass')
        
        # Export data
        export_path = os.path.join(self.temp_dir, 'export.json')
        success = self.admin.export_data(export_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Check export content
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn('users', data)
        self.assertIn('_metadata', data)
    
    def test_generate_report(self):
        """Test report generation"""
        report_json = self.admin.generate_report()
        report = json.loads(report_json)
        
        self.assertIn('report_generated', report)
        self.assertIn('database_status', report)
        self.assertIn('health_metrics', report)
        self.assertIn('user_summary', report)
        self.assertIn('recommendations', report)

def run_tests():
    """Run all database tests"""
    # Create test suite
    test_classes = [
        TestDatabaseConnectionPool,
        TestNoxDatabase,
        TestMigrationManager,
        TestUserRepository,
        TestKnowledgeRepository,
        TestConversationRepository,
        TestSessionRepository,
        TestDatabaseService,
        TestDatabaseAdmin
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)