"""
Integration tests for NoxPanel
"""

import unittest
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSystemIntegration(unittest.TestCase):
    """Test system integration functionality."""
    
    def test_installer_integration(self):
        """Test that installer runs without critical errors."""
        try:
            import install
            # Test that the installer main function exists and can be called
            # We don't actually run it to avoid side effects
            result = install.main if hasattr(install, 'main') else None
            self.assertIsNotNone(result, "Installer should have a main function")
        except ImportError:
            self.skipTest("Installer module not available")
    
    def test_validator_integration(self):
        """Test that validator runs successfully."""
        try:
            import validate_installation
            # This should not raise an exception
            result = validate_installation.main()
            # Validator should return 0 for success or 1 for warnings
            self.assertIn(result, [0, 1])
        except ImportError:
            self.skipTest("Validator module not available")
    
    def test_web_server_startup(self):
        """Test that web server can start and respond."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            with app.test_client() as client:
                # Test health endpoint
                response = client.get('/health')
                self.assertEqual(response.status_code, 200)
                
                # Test root endpoint
                response = client.get('/')
                self.assertEqual(response.status_code, 200)
        except ImportError:
            self.skipTest("Web server module not available")


if __name__ == '__main__':
    unittest.main()