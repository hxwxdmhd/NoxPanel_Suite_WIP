#!/usr/bin/env python3
"""
Example Plugin - Advanced Security Scanner
==========================================

This is a demonstration security plugin with enhanced features.
"""

import hashlib
import time
from typing import Dict, Any, List
from unified_plugin_system_clean import SecurityPlugin, PluginInfo

class SecurityScannerPlugin(SecurityPlugin):
    """Advanced security scanner plugin"""
    
    def __init__(self):
        super().__init__()
        self.scan_active = False
        self.security_level = "HIGH"
        self.scan_results = {
            'threats_detected': 0,
            'files_scanned': 0,
            'last_scan': None,
            'vulnerabilities': []
        }
        self.dependencies = []
    
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name="SecurityScannerPlugin",
            version="2.1.0",
            description="Advanced security scanner with threat detection",
            author="Enhanced Plugin System",
            category="security",
            dependencies=[],
            permissions=["security.scan", "filesystem.read", "system.monitor"]
        )
    
    def validate_security(self, context: Dict[str, Any]) -> bool:
        """Validate security context"""
        try:
            # Simulate security validation
            file_path = context.get('file_path', '')
            content = context.get('content', '')
            
            # Check for suspicious patterns
            dangerous_patterns = [
                'eval(', 'exec(', '__import__',
                'subprocess', 'os.system'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    self.scan_results['threats_detected'] += 1
                    self.scan_results['vulnerabilities'].append({
                        'type': 'dangerous_pattern',
                        'pattern': pattern,
                        'file': file_path,
                        'timestamp': time.time()
                    })
                    return False
            
            self.scan_results['files_scanned'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Security validation failed: {e}")
            return False
    
    def get_security_level(self) -> str:
        """Get security level provided"""
        return self.security_level
    
    def perform_security_scan(self, target_path: str) -> Dict[str, Any]:
        """Perform comprehensive security scan"""
        self.scan_active = True
        self.scan_results['last_scan'] = time.time()
        
        try:
            # Simulate security scan
            scan_result = {
                'scan_id': hashlib.md5(f"{target_path}{time.time()}".encode()).hexdigest(),
                'target': target_path,
                'start_time': time.time(),
                'status': 'completed',
                'threats_found': len(self.scan_results['vulnerabilities']),
                'files_scanned': self.scan_results['files_scanned'],
                'security_score': max(0, 100 - (len(self.scan_results['vulnerabilities']) * 10))
            }
            
            self.logger.info(f"Security scan completed for {target_path}")
            return scan_result
            
        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'target': target_path
            }
        finally:
            self.scan_active = False
    
    def get_scan_results(self) -> Dict[str, Any]:
        """Get latest scan results"""
        return self.scan_results.copy()
    
    def get_health(self) -> Dict[str, Any]:
        """Get plugin health status"""
        health = super().get_health()
        
        # Add security-specific health metrics
        health['metrics'].update({
            'scan_active': self.scan_active,
            'security_level': self.security_level,
            'scan_results': self.scan_results,
            'service_type': 'security_scanner'
        })
        
        return health

# Make plugin discoverable
__plugin_class__ = SecurityScannerPlugin
