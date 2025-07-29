"""
Security tests for NoxPanel
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSecurity(unittest.TestCase):
    """Basic security tests."""
    
    def test_no_hardcoded_secrets_in_main_files(self):
        """Test that main files don't contain obvious secrets."""
        main_files = [
            'main.py',
            'install.py', 
            'validate_installation.py',
            'rlvr_guardian.py',
            'check_rlvr_score.py'
        ]
        
        dangerous_patterns = [
            'password',
            'secret',
            'api_key',
            'token'
        ]
        
        for filename in main_files:
            file_path = Path(__file__).parent.parent.parent / filename
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8').lower()
                
                for pattern in dangerous_patterns:
                    # Allow references in comments and variable names, but not values
                    if f'= "{pattern}"' in content or f"= '{pattern}'" in content:
                        self.fail(f"Potential hardcoded {pattern} in {filename}")
    
    def test_web_security_headers(self):
        """Test basic security in web responses."""
        try:
            from AI.NoxPanel.test_server_optimized import app
            
            with app.test_client() as client:
                response = client.get('/health')
                self.assertEqual(response.status_code, 200)
                
                # Check response doesn't leak sensitive info
                response_text = response.get_data(as_text=True).lower()
                
                # Should not contain obvious sensitive patterns
                sensitive_patterns = ['password', 'secret', 'private_key']
                for pattern in sensitive_patterns:
                    self.assertNotIn(pattern, response_text,
                                   f"Response contains sensitive pattern: {pattern}")
        except ImportError:
            self.skipTest("Web application not available")


if __name__ == '__main__':
    unittest.main()