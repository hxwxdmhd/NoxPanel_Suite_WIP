"""
Smoke tests for NoxPanel
Quick tests to verify basic functionality after deployment
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSmokeTests(unittest.TestCase):
    """Basic smoke tests for deployment validation."""
    
    def test_basic_imports(self):
        """Test that basic modules can be imported."""
        # Core imports should work
        import main
        import install
        import validate_installation
        
        # These should all have main functions
        self.assertTrue(hasattr(main, 'main'))
        self.assertTrue(hasattr(install, 'main'))
        self.assertTrue(hasattr(validate_installation, 'main'))
    
    def test_web_app_basic_functionality(self):
        """Test basic web app functionality."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            
            with app.test_client() as client:
                # Test that key endpoints exist and return 200
                endpoints = ['/', '/health']
                
                for endpoint in endpoints:
                    response = client.get(endpoint)
                    self.assertEqual(response.status_code, 200,
                                   f"Endpoint {endpoint} failed with status {response.status_code}")
        except ImportError:
            self.skipTest("Web application not available")
    
    def test_rlvr_compliance(self):
        """Test RLVR compliance validation."""
        import rlvr_guardian
        import check_rlvr_score
        
        # Run RLVR validation
        results = rlvr_guardian.validate_compliance()
        
        # Should have basic required fields
        self.assertIn('compliance_score', results)
        self.assertIn('status', results)
        
        # Score should be reasonable
        self.assertGreaterEqual(results['compliance_score'], 0)
        self.assertLessEqual(results['compliance_score'], 100)


if __name__ == '__main__':
    unittest.main()