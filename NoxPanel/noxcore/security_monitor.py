"""
Security Violation Detection Tool for NoxGuard---NoxPanel
Critical Audit Compliance Module for detecting and reporting security violations
"""

import logging
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import re

logger = logging.getLogger(__name__)

@dataclass
class SecurityViolation:
    """Data class for security violations"""
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # AUTH, DATA, NETWORK, SYSTEM, COMPLIANCE
    title: str
    description: str
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None

class SecurityViolationDetector:
    """Main security violation detection engine"""
    
    # Security thresholds and patterns
    FAILED_LOGIN_THRESHOLD = 5
    FAILED_LOGIN_WINDOW = 300  # 5 minutes
    SUSPICIOUS_IP_PATTERNS = [
        r'^10\.0\.0\.',  # Example: internal network scanning
        r'^192\.168\.',  # Local network unusual access
    ]
    SENSITIVE_DATA_PATTERNS = [
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    ]
    
    def __init__(self, db_service, config: Dict[str, Any] = None):
        self.db_service = db_service
        self.config = config or {}
        self.violations = []
        self.running = False
        self.monitor_thread = None
        
        # Initialize detection rules
        self._init_detection_rules()
        
    def _init_detection_rules(self):
        """Initialize security detection rules"""
        self.detection_rules = {
            'auth_failures': self._detect_auth_failures,
            'suspicious_ips': self._detect_suspicious_ips,
            'data_exfiltration': self._detect_data_exfiltration,
            'privilege_escalation': self._detect_privilege_escalation,
            'unusual_access_patterns': self._detect_unusual_access_patterns,
            'sensitive_data_exposure': self._detect_sensitive_data_exposure,
            'compliance_violations': self._detect_compliance_violations,
        }
        
    def start_monitoring(self):
        """Start continuous security monitoring"""
        if self.running:
            logger.warning("Security monitoring already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Security violation monitoring started")
        
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Security violation monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._run_detection_cycle()
                time.sleep(self.config.get('scan_interval', 60))  # Default 1 minute
            except Exception as e:
                logger.error(f"Error in security monitoring loop: {e}")
                time.sleep(10)  # Short delay before retry
                
    def _run_detection_cycle(self):
        """Run one cycle of violation detection"""
        logger.debug("Running security detection cycle")
        
        for rule_name, rule_func in self.detection_rules.items():
            try:
                violations = rule_func()
                for violation in violations:
                    self._record_violation(violation)
            except Exception as e:
                logger.error(f"Error in detection rule '{rule_name}': {e}")
                
    def _detect_auth_failures(self) -> List[SecurityViolation]:
        """Detect authentication failures and brute force attempts"""
        violations = []
        
        # Get recent audit logs for failed authentications
        try:
            recent_time = (datetime.now() - timedelta(seconds=self.FAILED_LOGIN_WINDOW)).strftime('%Y-%m-%d %H:%M:%S')
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ip_address, COUNT(*) as failures, user_id
                    FROM audit_logs 
                    WHERE action = 'auth_failed' 
                    AND timestamp > ? 
                    GROUP BY ip_address 
                    HAVING failures >= ?
                """, (recent_time, self.FAILED_LOGIN_THRESHOLD))
                
                for row in cursor.fetchall():
                    ip_address, failures, user_id = row
                    violation = SecurityViolation(
                        id=self._generate_violation_id(),
                        severity='HIGH',
                        category='AUTH',
                        title='Brute Force Attack Detected',
                        description=f'Multiple failed login attempts ({failures}) from IP {ip_address}',
                        timestamp=datetime.now(),
                        user_id=user_id,
                        ip_address=ip_address,
                        details={'failure_count': failures}
                    )
                    violations.append(violation)
                    
        except Exception as e:
            logger.error(f"Error detecting auth failures: {e}")
            
        return violations
        
    def _detect_suspicious_ips(self) -> List[SecurityViolation]:
        """Detect access from suspicious IP addresses"""
        violations = []
        
        try:
            recent_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT ip_address 
                    FROM audit_logs 
                    WHERE timestamp > ? AND ip_address IS NOT NULL
                """, (recent_time,))
                
                for (ip_address,) in cursor.fetchall():
                    for pattern in self.SUSPICIOUS_IP_PATTERNS:
                        if re.match(pattern, ip_address):
                            violation = SecurityViolation(
                                id=self._generate_violation_id(),
                                severity='MEDIUM',
                                category='NETWORK',
                                title='Suspicious IP Access',
                                description=f'Access from suspicious IP pattern: {ip_address}',
                                timestamp=datetime.now(),
                                ip_address=ip_address,
                                details={'pattern_matched': pattern}
                            )
                            violations.append(violation)
                            break
                            
        except Exception as e:
            logger.error(f"Error detecting suspicious IPs: {e}")
            
        return violations
        
    def _detect_data_exfiltration(self) -> List[SecurityViolation]:
        """Detect potential data exfiltration attempts"""
        violations = []
        
        try:
            # Check for large data exports or downloads
            recent_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, ip_address, COUNT(*) as export_count
                    FROM audit_logs 
                    WHERE action IN ('data_export', 'bulk_download', 'knowledge_export')
                    AND timestamp > ?
                    GROUP BY user_id, ip_address
                    HAVING export_count > 5
                """, (recent_time,))
                
                for row in cursor.fetchall():
                    user_id, ip_address, export_count = row
                    violation = SecurityViolation(
                        id=self._generate_violation_id(),
                        severity='HIGH',
                        category='DATA',
                        title='Potential Data Exfiltration',
                        description=f'Unusual number of data exports ({export_count}) by user {user_id}',
                        timestamp=datetime.now(),
                        user_id=user_id,
                        ip_address=ip_address,
                        details={'export_count': export_count}
                    )
                    violations.append(violation)
                    
        except Exception as e:
            logger.error(f"Error detecting data exfiltration: {e}")
            
        return violations
        
    def _detect_privilege_escalation(self) -> List[SecurityViolation]:
        """Detect privilege escalation attempts"""
        violations = []
        
        try:
            # Check for users trying to access admin functions
            recent_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.user_id, a.ip_address, u.role, COUNT(*) as attempts
                    FROM audit_logs a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.action IN ('admin_access_attempt', 'role_change_attempt')
                    AND a.timestamp > ?
                    AND u.role != 'admin'
                    GROUP BY a.user_id, a.ip_address
                    HAVING attempts > 3
                """, (recent_time,))
                
                for row in cursor.fetchall():
                    user_id, ip_address, role, attempts = row
                    violation = SecurityViolation(
                        id=self._generate_violation_id(),
                        severity='CRITICAL',
                        category='AUTH',
                        title='Privilege Escalation Attempt',
                        description=f'User {user_id} (role: {role}) attempting admin access {attempts} times',
                        timestamp=datetime.now(),
                        user_id=user_id,
                        ip_address=ip_address,
                        details={'attempts': attempts, 'user_role': role}
                    )
                    violations.append(violation)
                    
        except Exception as e:
            logger.error(f"Error detecting privilege escalation: {e}")
            
        return violations
        
    def _detect_unusual_access_patterns(self) -> List[SecurityViolation]:
        """Detect unusual access patterns"""
        violations = []
        
        try:
            # Check for access outside normal hours (configurable)
            normal_hours = self.config.get('normal_hours', {'start': 8, 'end': 18})
            current_hour = datetime.now().hour
            
            if not (normal_hours['start'] <= current_hour <= normal_hours['end']):
                recent_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
                with self.db_service.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_id, ip_address, COUNT(*) as access_count
                        FROM audit_logs 
                        WHERE timestamp > ?
                        GROUP BY user_id, ip_address
                        HAVING access_count > 10
                    """, (recent_time,))
                    
                    for row in cursor.fetchall():
                        user_id, ip_address, access_count = row
                        violation = SecurityViolation(
                            id=self._generate_violation_id(),
                            severity='MEDIUM',
                            category='SYSTEM',
                            title='Unusual Access Hours',
                            description=f'High activity ({access_count} actions) outside normal hours',
                            timestamp=datetime.now(),
                            user_id=user_id,
                            ip_address=ip_address,
                            details={'access_count': access_count, 'hour': current_hour}
                        )
                        violations.append(violation)
                        
        except Exception as e:
            logger.error(f"Error detecting unusual access patterns: {e}")
            
        return violations
        
    def _detect_sensitive_data_exposure(self) -> List[SecurityViolation]:
        """Detect potential sensitive data exposure"""
        violations = []
        
        try:
            # Check for sensitive data patterns in logged content
            recent_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, action, details, ip_address
                    FROM audit_logs 
                    WHERE timestamp > ? AND details IS NOT NULL
                """, (recent_time,))
                
                for row in cursor.fetchall():
                    user_id, action, details_json, ip_address = row
                    details_str = str(details_json) if details_json else ""
                    
                    for pattern in self.SENSITIVE_DATA_PATTERNS:
                        if re.search(pattern, details_str):
                            violation = SecurityViolation(
                                id=self._generate_violation_id(),
                                severity='HIGH',
                                category='DATA',
                                title='Sensitive Data Exposure',
                                description=f'Potential sensitive data detected in action: {action}',
                                timestamp=datetime.now(),
                                user_id=user_id,
                                ip_address=ip_address,
                                details={'action': action, 'pattern_type': 'sensitive_data'}
                            )
                            violations.append(violation)
                            break
                            
        except Exception as e:
            logger.error(f"Error detecting sensitive data exposure: {e}")
            
        return violations
        
    def _detect_compliance_violations(self) -> List[SecurityViolation]:
        """Detect compliance violations (GDPR, HIPAA, etc.)"""
        violations = []
        
        try:
            # Check for data retention policy violations
            retention_days = self.config.get('data_retention_days', 365)
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d %H:%M:%S')
            
            with self.db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check old user data
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at < ? AND active = 0
                """, (cutoff_date,))
                
                old_users = cursor.fetchone()[0]
                if old_users > 0:
                    violation = SecurityViolation(
                        id=self._generate_violation_id(),
                        severity='MEDIUM',
                        category='COMPLIANCE',
                        title='Data Retention Policy Violation',
                        description=f'{old_users} inactive users exceed retention policy',
                        timestamp=datetime.now(),
                        details={'old_users_count': old_users, 'retention_days': retention_days}
                    )
                    violations.append(violation)
                    
        except Exception as e:
            logger.error(f"Error detecting compliance violations: {e}")
            
        return violations
        
    def _record_violation(self, violation: SecurityViolation):
        """Record a security violation"""
        try:
            # Store in audit log
            self.db_service.audit.log_action(
                user_id=violation.user_id,
                action=f'security_violation_{violation.category.lower()}',
                resource_type='security',
                resource_id=violation.id,
                details=asdict(violation),
                ip_address=violation.ip_address
            )
            
            # Add to internal list
            self.violations.append(violation)
            
            # Log critical violations immediately
            if violation.severity == 'CRITICAL':
                logger.critical(f"CRITICAL SECURITY VIOLATION: {violation.title} - {violation.description}")
            elif violation.severity == 'HIGH':
                logger.error(f"HIGH SECURITY VIOLATION: {violation.title} - {violation.description}")
            else:
                logger.warning(f"{violation.severity} SECURITY VIOLATION: {violation.title}")
                
        except Exception as e:
            logger.error(f"Failed to record security violation: {e}")
            
    def _generate_violation_id(self) -> str:
        """Generate unique violation ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:16]
        
    def get_recent_violations(self, hours: int = 24) -> List[SecurityViolation]:
        """Get recent security violations"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [v for v in self.violations if v.timestamp >= cutoff]
        
    def get_violations_by_severity(self, severity: str) -> List[SecurityViolation]:
        """Get violations by severity level"""
        return [v for v in self.violations if v.severity == severity]
        
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        recent_violations = self.get_recent_violations(24)
        
        severity_counts = {}
        category_counts = {}
        
        for violation in recent_violations:
            severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
            category_counts[violation.category] = category_counts.get(violation.category, 0) + 1
            
        return {
            'report_generated': datetime.now().isoformat(),
            'total_violations_24h': len(recent_violations),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'critical_violations': [
                asdict(v) for v in recent_violations if v.severity == 'CRITICAL'
            ],
            'compliance_status': 'PASS' if (severity_counts.get('CRITICAL', 0) == 0 and severity_counts.get('HIGH', 0) == 0) else 'FAIL',
            'recommendations': self._generate_recommendations(recent_violations)
        }
        
    def _generate_recommendations(self, violations: List[SecurityViolation]) -> List[str]:
        """Generate security recommendations based on violations"""
        recommendations = []
        
        critical_count = len([v for v in violations if v.severity == 'CRITICAL'])
        auth_violations = len([v for v in violations if v.category == 'AUTH'])
        data_violations = len([v for v in violations if v.category == 'DATA'])
        
        if critical_count > 0:
            recommendations.append("URGENT: Address critical security violations immediately")
            
        if auth_violations > 5:
            recommendations.append("Consider implementing additional authentication measures (2FA, IP whitelisting)")
            
        if data_violations > 3:
            recommendations.append("Review data access policies and implement stricter data loss prevention")
            
        if not recommendations:
            recommendations.append("Security posture is acceptable, continue monitoring")
            
        return recommendations
        
    def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Mark a violation as resolved"""
        try:
            for violation in self.violations:
                if violation.id == violation_id:
                    violation.resolved = True
                    violation.resolution_notes = resolution_notes
                    
                    # Log resolution
                    self.db_service.audit.log_action(
                        user_id=None,
                        action='security_violation_resolved',
                        resource_id=violation_id,
                        details={'resolution_notes': resolution_notes}
                    )
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to resolve violation {violation_id}: {e}")
            return False

class SecurityDashboard:
    """Security dashboard for monitoring and reporting"""
    
    def __init__(self, detector: SecurityViolationDetector):
        self.detector = detector
        
    def generate_html_report(self) -> str:
        """Generate HTML security dashboard"""
        compliance_report = self.detector.get_compliance_report()
        recent_violations = self.detector.get_recent_violations(24)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NoxPanel Security Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .status {{ padding: 20px; margin: 10px 0; border-radius: 5px; }}
                .status.pass {{ background: #d4edda; border: 1px solid #c3e6cb; }}
                .status.fail {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
                .violation {{ margin: 10px 0; padding: 15px; border-left: 4px solid #ccc; }}
                .critical {{ border-left-color: #dc3545; }}
                .high {{ border-left-color: #fd7e14; }}
                .medium {{ border-left-color: #ffc107; }}
                .low {{ border-left-color: #28a745; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>NoxPanel Security Dashboard</h1>
                <p>Critical Audit Compliance Monitoring</p>
            </div>
            
            <div class="status {'pass' if compliance_report['compliance_status'] == 'PASS' else 'fail'}">
                <h2>Compliance Status: {compliance_report['compliance_status']}</h2>
                <p>Last Updated: {compliance_report['report_generated']}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>{compliance_report['total_violations_24h']}</h3>
                    <p>Total Violations (24h)</p>
                </div>
                <div class="metric">
                    <h3>{compliance_report['severity_breakdown'].get('CRITICAL', 0)}</h3>
                    <p>Critical Violations</p>
                </div>
                <div class="metric">
                    <h3>{compliance_report['severity_breakdown'].get('HIGH', 0)}</h3>
                    <p>High Severity</p>
                </div>
                <div class="metric">
                    <h3>{len([v for v in recent_violations if not v.resolved])}</h3>
                    <p>Unresolved</p>
                </div>
            </div>
            
            <h2>Recent Violations</h2>
        """
        
        for violation in recent_violations[-10:]:  # Show last 10
            html += f"""
            <div class="violation {violation.severity.lower()}">
                <h4>{violation.title}</h4>
                <p><strong>Severity:</strong> {violation.severity} | <strong>Category:</strong> {violation.category}</p>
                <p>{violation.description}</p>
                <small>Time: {violation.timestamp} | ID: {violation.id}</small>
                {f'<p><em>Resolved: {violation.resolution_notes}</em></p>' if violation.resolved else ''}
            </div>
            """
        
        html += f"""
            <h2>Recommendations</h2>
            <ul>
        """
        
        for rec in compliance_report['recommendations']:
            html += f"<li>{rec}</li>"
            
        html += """
            </ul>
        </body>
        </html>
        """
        
        return html

# Export main classes
__all__ = ['SecurityViolation', 'SecurityViolationDetector', 'SecurityDashboard']