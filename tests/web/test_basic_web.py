"""
Basic web interface tests for NoxPanel
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestWebInterface(unittest.TestCase):
    """Test web interface functionality."""
    
    def setUp(self):
        """Set up test client."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            self.app = app
            self.client = app.test_client()
            self.app.config['TESTING'] = True
        except ImportError:
            self.skipTest("Flask app not available")
    
    def test_app_exists(self):
        """Test that app is created."""
        self.assertIsNotNone(self.app)
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get('/')
        # Accept any non-500 response
        self.assertNotEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()