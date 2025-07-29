#!/usr/bin/env python3
"""
Tests for example_plugin plugin
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import ExamplePlugin

class TestExamplePlugin(unittest.TestCase):
    """Test cases for example_plugin plugin"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.plugin = ExamplePlugin()
    
    def test_initialization(self):
        """Test plugin initialization"""
        self.assertIsNotNone(self.plugin)
        self.assertIsInstance(self.plugin.config, dict)
    
    def test_execute(self):
        """Test plugin execution"""
        result = self.plugin.execute({"test": "data"})
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
    
    def test_health_status(self):
        """Test health status"""
        health = self.plugin.get_health_status()
        self.assertIsInstance(health, dict)
        self.assertIn("status", health)
        self.assertEqual(health["status"], "healthy")
    
    def test_validate_config(self):
        """Test configuration validation"""
        config = {"enabled": True}
        self.assertTrue(self.plugin.validate_config(config))

if __name__ == "__main__":
    unittest.main()
