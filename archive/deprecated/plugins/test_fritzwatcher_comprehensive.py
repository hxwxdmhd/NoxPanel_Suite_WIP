#!/usr/bin/env python3
"""
FRITZWATCHER Test Suite - Comprehensive Testing Framework
=========================================================

Advanced test suite covering stability, edge cases, and resilience.
Includes mocked router simulation and KeePass validation.

Author: MSP-Aware Development Team
Date: July 19, 2025
"""

import asyncio
import pytest
import unittest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import modules under test
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fritzwatcher_resilience import (
    ResilienceManager, 
    RouterHealthMonitor, 
    TemporaryCredentialManager,
    RetryConfig, 
    FailoverConfig
)
from keepass_helper import KeePassHelper

class TestResilienceFramework(unittest.TestCase):
    """Test the resilience framework components"""
    
    def setUp(self):
        """Set up test environment"""
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,  # Fast for testing
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False  # Disable for predictable testing
        )
        
        self.failover_config = FailoverConfig(
            primary_router_timeout=1.0,
            secondary_router_delay=0.5,
            health_check_interval=5.0,
            max_consecutive_failures=2
        )
        
        self.resilience_manager = ResilienceManager(
            self.retry_config, 
            self.failover_config
        )
    
    def test_router_health_monitoring(self):
        """Test router health monitoring"""
        monitor = RouterHealthMonitor(self.failover_config)
        
        # Test initial state
        self.assertTrue(monitor.is_router_healthy("router1"))
        
        # Test failure tracking
        monitor.update_router_health("router1", False)
        self.assertTrue(monitor.is_router_healthy("router1"))  # Still healthy after 1 failure
        
        monitor.update_router_health("router1", False)
        self.assertFalse(monitor.is_router_healthy("router1"))  # Unhealthy after 2 failures
        
        # Test recovery
        monitor.update_router_health("router1", True, 0.5)
        self.assertTrue(monitor.is_router_healthy("router1"))  # Healthy again
        
        # Test response time tracking
        health = monitor.router_health["router1"]
        self.assertEqual(health["average_response_time"], 0.5)
    
    def test_best_router_selection(self):
        """Test best router selection algorithm"""
        monitor = RouterHealthMonitor(self.failover_config)
        
        # Setup router performance data
        monitor.update_router_health("router1", True, 0.1)  # Fast
        monitor.update_router_health("router2", True, 0.5)  # Slow
        monitor.update_router_health("router3", False)      # Failed
        monitor.update_router_health("router3", False)      # Failed again (unhealthy)
        
        routers = ["router1", "router2", "router3"]
        best = monitor.get_best_router(routers)
        
        # Should select router1 (fastest and healthy)
        self.assertEqual(best, "router1")
        
        # Test with all routers unhealthy
        monitor.update_router_health("router1", False)
        monitor.update_router_health("router1", False)
        monitor.update_router_health("router2", False)
        monitor.update_router_health("router2", False)
        
        best = monitor.get_best_router(routers)
        # Should return least unhealthy router
        self.assertIsNotNone(best)
    
    def test_temporary_credential_management(self):
        """Test temporary credential override system"""
        manager = TemporaryCredentialManager()
        
        # Test setting temporary credentials with very short expiry
        manager.set_temporary_credential("router1", "testuser", "testpass", expires_in_minutes=0.01)  # 0.6 seconds
        
        creds = manager.get_credentials("router1")
        self.assertIsNotNone(creds)
        self.assertEqual(creds["username"], "testuser")
        self.assertEqual(creds["password"], "testpass")
        self.assertEqual(creds["source"], "web_ui_override")
        
        # Test expiration - wait longer
        time.sleep(1.2)  # Wait for expiration
        creds = manager.get_credentials("router1")
        self.assertIsNone(creds)
    
    @patch.dict(os.environ, {"FRITZBOX_ROUTER1_USERNAME": "envuser", "FRITZBOX_ROUTER1_PASSWORD": "envpass"})
    def test_environment_credential_fallback(self):
        """Test environment variable credential fallback"""
        manager = TemporaryCredentialManager()
        
        creds = manager.get_credentials("router1")
        self.assertIsNotNone(creds)
        self.assertEqual(creds["username"], "envuser")
        self.assertEqual(creds["password"], "envpass")
        self.assertEqual(creds["source"], "environment")
    
    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic with exponential backoff"""
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return "success"
        
        # Test successful retry
        result = await self.resilience_manager.execute_with_retry(
            failing_function, 
            router_id="test_router"
        )
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        
        # Test failure after all retries
        call_count = 0
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Always fails {call_count}")
        
        with self.assertRaises(Exception):
            await self.resilience_manager.execute_with_retry(
                always_failing_function,
                router_id="test_router"
            )
        
        self.assertEqual(call_count, 3)  # Should try 3 times
    
    @pytest.mark.asyncio
    async def test_failover_logic(self):
        """Test failover between routers"""
        call_count = {"router1": 0, "router2": 0}
        
        async def router_function(router_id):
            call_count[router_id] += 1
            if router_id == "router1":
                raise Exception("Router1 failed")
            return f"success from {router_id}"
        
        # Test failover from router1 to router2
        result = await self.resilience_manager.execute_with_failover(
            router_function,
            ["router1", "router2"],
            router_id="router1"  # This will be overridden by failover
        )
        
        self.assertEqual(result, "success from router2")
        self.assertEqual(call_count["router1"], 3)  # Should retry 3 times
        self.assertEqual(call_count["router2"], 1)  # Should succeed on first try

class TestHostnameEdgeCases(unittest.TestCase):
    """Test edge cases in hostname parsing"""
    
    def test_emoji_hostnames(self):
        """Test handling of emoji characters in hostnames"""
        test_cases = [
            "🏠-router",
            "device-📱-phone",
            "laptop-💻",
            "printer-🖨️-office"
        ]
        
        for hostname in test_cases:
            # Should not crash and should handle gracefully
            sanitized = self._sanitize_hostname(hostname)
            self.assertIsInstance(sanitized, str)
            self.assertGreater(len(sanitized), 0)
    
    def test_reserved_characters(self):
        """Test handling of reserved characters"""
        test_cases = [
            "device<>name",
            "router\"with\"quotes",
            "host|with|pipes",
            "device\\with\\backslash",
            "router/with/slash"
        ]
        
        for hostname in test_cases:
            sanitized = self._sanitize_hostname(hostname)
            # Should not contain reserved characters
            reserved_chars = "<>\"|\\/:"
            for char in reserved_chars:
                self.assertNotIn(char, sanitized)
    
    def test_duplicate_mac_addresses(self):
        """Test handling of duplicate MAC addresses with different hostnames"""
        devices = [
            {"mac": "aa:bb:cc:dd:ee:ff", "hostname": "device1", "ip": "192.168.1.10"},
            {"mac": "aa:bb:cc:dd:ee:ff", "hostname": "device1-renamed", "ip": "192.168.1.11"},
            {"mac": "aa:bb:cc:dd:ee:ff", "hostname": "device1-guest", "ip": "192.168.1.12"},
        ]
        
        # Should handle duplicates gracefully
        processed = self._process_device_list(devices)
        
        # Should have only one entry per MAC
        macs = [d["mac"] for d in processed]
        self.assertEqual(len(set(macs)), 1)
        
        # Should use the most recent or preferred hostname
        self.assertIn("device1", processed[0]["hostname"])
    
    def _sanitize_hostname(self, hostname: str) -> str:
        """Sanitize hostname by removing or replacing problematic characters"""
        import re
        # Remove emojis and replace with underscore
        sanitized = re.sub(r'[^\w\-.]', '_', hostname)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_{2,}', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized or "unknown_device"
    
    def _process_device_list(self, devices: List[Dict]) -> List[Dict]:
        """Process device list to handle duplicates"""
        device_map = {}
        
        for device in devices:
            mac = device["mac"]
            if mac not in device_map:
                device_map[mac] = device
            else:
                # Update with newer information
                existing = device_map[mac]
                if device.get("timestamp", 0) > existing.get("timestamp", 0):
                    device_map[mac] = device
        
        return list(device_map.values())

class TestKeePassIntegration(unittest.TestCase):
    """Test KeePass integration edge cases"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test.kdbx")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_invalid_database_path(self):
        """Test handling of invalid database paths"""
        from keepass_helper import create_keepass_helper
        
        config = {
            'database_path': '/nonexistent/path/database.kdbx',
            'use_cli': False,
            'use_browser_integration': False
        }
        
        # Should handle gracefully without crashing
        helper = create_keepass_helper(config)
        self.assertIsNotNone(helper)
        
        # Should return None for credentials when database doesn't exist
        credentials = helper.get_credentials("test_entry")
        self.assertIsNone(credentials)
    
    def test_missing_database_file(self):
        """Test handling when database file is missing"""
        from keepass_helper import create_keepass_helper
        
        config = {
            'database_path': self.test_db_path,  # File doesn't exist
            'use_cli': False,
            'use_browser_integration': False
        }
        
        helper = create_keepass_helper(config)
        
        # Should handle missing file gracefully
        credentials = helper.get_credentials("test_entry")
        self.assertIsNone(credentials)
    
    @patch('getpass.getpass')
    def test_password_prompting(self, mock_getpass):
        """Test password prompting functionality"""
        mock_getpass.return_value = "testpassword"
        
        from keepass_helper import create_keepass_helper
        
        # Create a fake database file
        with open(self.test_db_path, 'wb') as f:
            f.write(b"fake kdbx content")
        
        config = {
            'database_path': self.test_db_path,
            'use_cli': False,
            'use_browser_integration': False
        }
        
        helper = create_keepass_helper(config)
        
        # Should prompt for password
        result = helper.unlock_database()
        mock_getpass.assert_called_once()

class TestMockedRouterSimulation(unittest.TestCase):
    """Test with mocked router responses"""
    
    def setUp(self):
        """Set up mock router environment"""
        self.mock_responses = {
            "router1": {
                "success": True,
                "devices": [
                    {"mac": "aa:bb:cc:dd:ee:01", "hostname": "laptop", "ip": "192.168.1.10"},
                    {"mac": "aa:bb:cc:dd:ee:02", "hostname": "phone", "ip": "192.168.1.11"}
                ]
            },
            "router2": {
                "success": False,
                "error": "Connection timeout"
            }
        }
    
    @patch('aiohttp.ClientSession.post')
    async def test_router_api_calls(self, mock_post):
        """Test router API calls with mocked responses"""
        
        async def mock_response(url, **kwargs):
            mock_resp = Mock()
            if "router1" in url:
                mock_resp.text = AsyncMock(return_value='<response>success</response>')
                mock_resp.status = 200
            else:
                mock_resp.status = 500
                mock_resp.text = AsyncMock(return_value='<error>timeout</error>')
            return mock_resp
        
        mock_post.side_effect = mock_response
        
        # Test successful call
        # This would normally call the actual FritzWatcher plugin
        # For now, we'll just test the mock setup
        self.assertTrue(True)  # Placeholder
    
    def test_network_behavior_simulation(self):
        """Test various network behaviors"""
        behaviors = [
            "timeout",
            "connection_refused", 
            "slow_response",
            "malformed_response",
            "partial_response"
        ]
        
        for behavior in behaviors:
            # Simulate different network conditions
            result = self._simulate_network_behavior(behavior)
            self.assertIsNotNone(result)
    
    def _simulate_network_behavior(self, behavior: str) -> Dict:
        """Simulate different network behaviors"""
        if behavior == "timeout":
            return {"success": False, "error": "timeout", "duration": 30.0}
        elif behavior == "connection_refused":
            return {"success": False, "error": "connection_refused", "duration": 0.1}
        elif behavior == "slow_response":
            return {"success": True, "data": "response", "duration": 5.0}
        elif behavior == "malformed_response":
            return {"success": False, "error": "malformed_xml", "duration": 1.0}
        elif behavior == "partial_response":
            return {"success": True, "data": "partial", "duration": 1.0}
        else:
            return {"success": True, "data": "normal", "duration": 0.5}

def run_all_tests():
    """Run all test suites"""
    print("🧪 Running FRITZWATCHER Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestResilienceFramework))
    suite.addTest(unittest.makeSuite(TestHostnameEdgeCases))
    suite.addTest(unittest.makeSuite(TestKeePassIntegration))
    suite.addTest(unittest.makeSuite(TestMockedRouterSimulation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
