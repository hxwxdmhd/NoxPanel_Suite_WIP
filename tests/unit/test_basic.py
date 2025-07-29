"""
Basic unit tests for NoxPanel
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestNoxPanelCore(unittest.TestCase):
    """Test core NoxPanel functionality."""
    
    def test_imports(self):
        """Test that core modules can be imported."""
        # Test main entry point
        try:
            import main
            self.assertTrue(hasattr(main, 'main'))
        except ImportError:
            self.fail("Cannot import main module")
    
    def test_installer_import(self):
        """Test that installer can be imported."""
        try:
            import install
            self.assertTrue(hasattr(install, 'main'))
        except ImportError:
            self.fail("Cannot import install module")
    
    def test_validator_import(self):
        """Test that validator can be imported."""
        try:
            import validate_installation
            self.assertTrue(hasattr(validate_installation, 'main'))
        except ImportError:
            self.fail("Cannot import validate_installation module")

    def test_rlvr_guardian_import(self):
        """Test that RLVR guardian can be imported."""
        try:
            import rlvr_guardian
            self.assertTrue(hasattr(rlvr_guardian, 'main'))
        except ImportError:
            self.fail("Cannot import rlvr_guardian module")


class TestWebApplication(unittest.TestCase):
    """Test web application functionality."""
    
    def test_flask_app_import(self):
        """Test that Flask app can be imported."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            self.assertIsNotNone(app)
        except ImportError:
            self.fail("Cannot import Flask app")


if __name__ == '__main__':
    unittest.main()