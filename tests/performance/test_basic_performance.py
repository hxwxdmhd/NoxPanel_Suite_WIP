"""
Performance tests for NoxPanel
"""

import unittest
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestPerformance(unittest.TestCase):
    """Basic performance tests."""
    
    def test_web_response_time(self):
        """Test that web endpoints respond quickly."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            
            with app.test_client() as client:
                # Test response time for health endpoint
                start_time = time.time()
                response = client.get('/health')
                end_time = time.time()
                
                response_time = end_time - start_time
                
                self.assertEqual(response.status_code, 200)
                # Should respond in under 1 second
                self.assertLess(response_time, 1.0, 
                              f"Health endpoint took {response_time:.3f}s")
        except ImportError:
            self.skipTest("Web application not available")
    
    def test_import_time(self):
        """Test that core modules import quickly."""
        start_time = time.time()
        
        # Import core modules
        import main
        import install
        import validate_installation
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # Should import in under 2 seconds
        self.assertLess(import_time, 2.0,
                       f"Core modules took {import_time:.3f}s to import")


if __name__ == '__main__':
    unittest.main()