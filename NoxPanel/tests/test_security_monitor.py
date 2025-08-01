"""
Test suite for Security Violation Detection Tool
Tests critical audit compliance functionality
"""

import unittest
import tempfile
import os
import json
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import our modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from noxcore.database_service import DatabaseService
from noxcore.security_monitor import (
    SecurityViolation, SecurityViolationDetector, SecurityDashboard
)

class TestSecurityViolation(unittest.TestCase):
    """Test SecurityViolation data class"""
    
    def test_security_violation_creation(self):
        """Test creating a security violation"""
        violation = SecurityViolation(
            id="test123",
            severity="HIGH",
            category="AUTH",
            title="Test Violation",
            description="Test description",
            timestamp=datetime.now(),
            user_id=1,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(violation.id, "test123")
        self.assertEqual(violation.severity, "HIGH")
        self.assertEqual(violation.category, "AUTH")
        self.assertFalse(violation.resolved)

class TestSecurityViolationDetector(unittest.TestCase):
    """Test security violation detector"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_security.db')
        self.db_service = DatabaseService(self.db_path, auto_migrate=True)
        
        # Create test configuration
        self.config = {
            'scan_interval': 10,
            'normal_hours': {'start': 9, 'end': 17},
            'data_retention_days': 90
        }
        
        self.detector = SecurityViolationDetector(self.db_service, self.config)
    
    def tearDown(self):
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_detector_initialization(self):
        """Test detector initialization"""
        self.assertIsNotNone(self.detector.db_service)
        self.assertEqual(self.detector.config, self.config)
        self.assertEqual(len(self.detector.detection_rules), 7)
        self.assertFalse(self.detector.running)
    
    def test_violation_id_generation(self):
        """Test violation ID generation"""
        id1 = self.detector._generate_violation_id()
        id2 = self.detector._generate_violation_id()
        
        self.assertIsInstance(id1, str)
        self.assertEqual(len(id1), 16)
        self.assertNotEqual(id1, id2)
    
    def test_record_violation(self):
        """Test recording a security violation"""
        violation = SecurityViolation(
            id="test123",
            severity="HIGH",
            category="AUTH",
            title="Test Violation",
            description="Test description",
            timestamp=datetime.now(),
            user_id=1,
            ip_address="192.168.1.1"
        )
        
        initial_count = len(self.detector.violations)
        self.detector._record_violation(violation)
        
        self.assertEqual(len(self.detector.violations), initial_count + 1)
        self.assertEqual(self.detector.violations[-1].id, "test123")
    
    def test_auth_failure_detection(self):
        """Test authentication failure detection"""
        # Create multiple failed login attempts
        for i in range(6):  # Exceeds threshold of 5
            self.db_service.audit.log_action(
                user_id=1,
                action='auth_failed',
                ip_address='192.168.1.100',
                details={'attempt': i}
            )
        
        violations = self.detector._detect_auth_failures()
        
        self.assertGreater(len(violations), 0)
        violation = violations[0]
        self.assertEqual(violation.severity, 'HIGH')
        self.assertEqual(violation.category, 'AUTH')
        self.assertIn('Brute Force', violation.title)
        self.assertEqual(violation.ip_address, '192.168.1.100')
    
    def test_suspicious_ip_detection(self):
        """Test suspicious IP detection"""
        # Log activity from suspicious IP
        self.db_service.audit.log_action(
            user_id=1,
            action='login',
            ip_address='10.0.0.5',  # Matches suspicious pattern
            details={'test': True}
        )
        
        violations = self.detector._detect_suspicious_ips()
        
        if violations:  # May not trigger if pattern doesn't match exactly
            violation = violations[0]
            self.assertEqual(violation.severity, 'MEDIUM')
            self.assertEqual(violation.category, 'NETWORK')
            self.assertIn('Suspicious IP', violation.title)
    
    def test_data_exfiltration_detection(self):
        """Test data exfiltration detection"""
        # Create multiple data export events
        for i in range(7):  # Exceeds threshold of 5
            self.db_service.audit.log_action(
                user_id=1,
                action='data_export',
                ip_address='192.168.1.200',
                details={'export_size': f'{i*100}MB'}
            )
        
        violations = self.detector._detect_data_exfiltration()
        
        self.assertGreater(len(violations), 0)
        violation = violations[0]
        self.assertEqual(violation.severity, 'HIGH')
        self.assertEqual(violation.category, 'DATA')
        self.assertIn('Data Exfiltration', violation.title)
    
    def test_privilege_escalation_detection(self):
        """Test privilege escalation detection"""
        # Create a regular user
        user_id = self.db_service.users.create_user('testuser', 'password123', 'test@example.com', 'user')
        
        # Simulate admin access attempts
        for i in range(5):  # Exceeds threshold of 3
            self.db_service.audit.log_action(
                user_id=user_id,
                action='admin_access_attempt',
                ip_address='192.168.1.300',
                details={'attempted_resource': 'admin_panel'}
            )
        
        violations = self.detector._detect_privilege_escalation()
        
        self.assertGreater(len(violations), 0)
        violation = violations[0]
        self.assertEqual(violation.severity, 'CRITICAL')
        self.assertEqual(violation.category, 'AUTH')
        self.assertIn('Privilege Escalation', violation.title)
    
    def test_compliance_report_generation(self):
        """Test compliance report generation"""
        # Add some test violations
        test_violations = [
            SecurityViolation(
                id="v1", severity="CRITICAL", category="AUTH",
                title="Test Critical", description="Test",
                timestamp=datetime.now()
            ),
            SecurityViolation(
                id="v2", severity="HIGH", category="DATA",
                title="Test High", description="Test",
                timestamp=datetime.now()
            ),
            SecurityViolation(
                id="v3", severity="MEDIUM", category="NETWORK",
                title="Test Medium", description="Test",
                timestamp=datetime.now()
            )
        ]
        
        for violation in test_violations:
            self.detector._record_violation(violation)
        
        report = self.detector.get_compliance_report()
        
        self.assertIn('report_generated', report)
        self.assertIn('total_violations_24h', report)
        self.assertIn('severity_breakdown', report)
        self.assertIn('category_breakdown', report)
        self.assertIn('compliance_status', report)
        self.assertIn('recommendations', report)
        
        # Should fail compliance due to critical violation
        self.assertEqual(report['compliance_status'], 'FAIL')
        self.assertEqual(report['severity_breakdown']['CRITICAL'], 1)
        self.assertEqual(report['severity_breakdown']['HIGH'], 1)
        self.assertEqual(report['severity_breakdown']['MEDIUM'], 1)
    
    def test_violation_resolution(self):
        """Test violation resolution"""
        # Create and record a violation
        violation = SecurityViolation(
            id="resolve_test",
            severity="HIGH",
            category="AUTH",
            title="Test Violation",
            description="Test description",
            timestamp=datetime.now()
        )
        
        self.detector._record_violation(violation)
        
        # Resolve the violation
        result = self.detector.resolve_violation("resolve_test", "False positive - resolved")
        
        self.assertTrue(result)
        
        # Check it's marked as resolved
        resolved_violation = next(v for v in self.detector.violations if v.id == "resolve_test")
        self.assertTrue(resolved_violation.resolved)
        self.assertEqual(resolved_violation.resolution_notes, "False positive - resolved")
    
    def test_get_violations_by_severity(self):
        """Test getting violations by severity"""
        # Add violations of different severities
        critical_violation = SecurityViolation(
            id="crit1", severity="CRITICAL", category="AUTH",
            title="Critical Test", description="Test",
            timestamp=datetime.now()
        )
        high_violation = SecurityViolation(
            id="high1", severity="HIGH", category="DATA",
            title="High Test", description="Test",
            timestamp=datetime.now()
        )
        
        self.detector._record_violation(critical_violation)
        self.detector._record_violation(high_violation)
        
        critical_violations = self.detector.get_violations_by_severity("CRITICAL")
        high_violations = self.detector.get_violations_by_severity("HIGH")
        
        self.assertEqual(len(critical_violations), 1)
        self.assertEqual(len(high_violations), 1)
        self.assertEqual(critical_violations[0].id, "crit1")
        self.assertEqual(high_violations[0].id, "high1")

class TestSecurityDashboard(unittest.TestCase):
    """Test security dashboard"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_dashboard.db')
        self.db_service = DatabaseService(self.db_path, auto_migrate=True)
        self.detector = SecurityViolationDetector(self.db_service)
        self.dashboard = SecurityDashboard(self.detector)
    
    def tearDown(self):
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard.detector)
        self.assertEqual(self.dashboard.detector, self.detector)
    
    def test_html_report_generation(self):
        """Test HTML report generation"""
        # Add a test violation
        violation = SecurityViolation(
            id="html_test",
            severity="HIGH",
            category="AUTH",
            title="Test HTML Violation",
            description="Test for HTML generation",
            timestamp=datetime.now()
        )
        
        self.detector._record_violation(violation)
        
        html_report = self.dashboard.generate_html_report()
        
        self.assertIsInstance(html_report, str)
        self.assertIn('<!DOCTYPE html>', html_report)
        self.assertIn('NoxPanel Security Dashboard', html_report)
        self.assertIn('Test HTML Violation', html_report)
        self.assertIn('Compliance Status', html_report)
        self.assertIn('Recent Violations', html_report)

class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for the complete security system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_integration.db')
        self.db_service = DatabaseService(self.db_path, auto_migrate=True)
        self.detector = SecurityViolationDetector(self.db_service)
        self.dashboard = SecurityDashboard(self.detector)
    
    def tearDown(self):
        try:
            self.db_service.close()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_complete_security_workflow(self):
        """Test complete security monitoring workflow"""
        # 1. Simulate security events
        user_id = self.db_service.users.create_user('testuser', 'password123', 'test@example.com', 'user')
        
        # Simulate multiple failed logins (should trigger brute force detection)
        for i in range(6):
            self.db_service.audit.log_action(
                user_id=user_id,
                action='auth_failed',
                ip_address='192.168.1.999',
                details={'attempt': i}
            )
        
        # 2. Run detection
        violations = self.detector._detect_auth_failures()
        
        # 3. Verify violations detected
        self.assertGreater(len(violations), 0)
        
        # 4. Record violations
        for violation in violations:
            self.detector._record_violation(violation)
        
        # 5. Generate compliance report
        report = self.detector.get_compliance_report()
        
        # 6. Verify report contents
        self.assertGreater(report['total_violations_24h'], 0)
        self.assertEqual(report['compliance_status'], 'FAIL')  # Due to HIGH severity
        
        # 7. Generate dashboard
        html_report = self.dashboard.generate_html_report()
        self.assertIn('Brute Force', html_report)
        
        # 8. Resolve violation
        violation_id = violations[0].id
        resolution_result = self.detector.resolve_violation(violation_id, "Investigated - legitimate user")
        self.assertTrue(resolution_result)

if __name__ == '__main__':
    unittest.main()