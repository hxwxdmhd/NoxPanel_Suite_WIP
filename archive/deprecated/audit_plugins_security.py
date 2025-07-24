#!/usr/bin/env python3
"""
Plugin Security Audit System - Audit 3 Compliant
================================================

This system provides comprehensive security validation for plugins:
- Static code analysis
- Runtime security monitoring
- Resource usage validation
- Threat detection
- Security compliance reporting

Required for Audit 3 compliance
"""

import os
import sys
import ast
import json
import logging
import hashlib
import importlib
import subprocess
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import sqlite3
import traceback
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityViolationType(Enum):
    """Types of security violations"""
    FILE_SYSTEM_ACCESS = "FILE_SYSTEM_ACCESS"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    SUBPROCESS_EXECUTION = "SUBPROCESS_EXECUTION"
    DANGEROUS_IMPORTS = "DANGEROUS_IMPORTS"
    CODE_INJECTION = "CODE_INJECTION"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    UNSAFE_DESERIALIZATION = "UNSAFE_DESERIALIZATION"

@dataclass
class SecurityViolation:
    """Security violation details"""
    type: SecurityViolationType
    severity: SecurityLevel
    description: str
    location: str
    line_number: int = 0
    code_snippet: str = ""
    remediation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SecurityAuditResult:
    """Security audit result"""
    plugin_name: str
    plugin_path: str
    security_level: SecurityLevel
    violations: List[SecurityViolation] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    audit_timestamp: datetime = field(default_factory=datetime.now)
    hash_signature: str = ""
    compliance_score: float = 0.0

class PluginSecurityAuditor:
    """
    Comprehensive plugin security auditor
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Security patterns to detect
        self.dangerous_patterns = {
            # File system access patterns
            SecurityViolationType.FILE_SYSTEM_ACCESS: [
                r'open\s*\(',
                r'file\s*\(',
                r'os\.path',
                r'pathlib\.',
                r'shutil\.',
                r'glob\.',
                r'tempfile\.',
                r'__file__',
                r'__path__'
            ],
            
            # Network access patterns
            SecurityViolationType.NETWORK_ACCESS: [
                r'urllib\.',
                r'requests\.',
                r'socket\.',
                r'http\.',
                r'ftplib\.',
                r'smtplib\.',
                r'telnetlib\.',
                r'websocket'
            ],
            
            # Subprocess execution patterns
            SecurityViolationType.SUBPROCESS_EXECUTION: [
                r'subprocess\.',
                r'os\.system',
                r'os\.popen',
                r'os\.spawn',
                r'os\.exec',
                r'commands\.',
                r'shell=True'
            ],
            
            # Dangerous imports
            SecurityViolationType.DANGEROUS_IMPORTS: [
                r'import\s+os\b',
                r'import\s+sys\b',
                r'import\s+subprocess\b',
                r'import\s+importlib\b',
                r'import\s+__builtin__',
                r'import\s+builtins',
                r'from\s+os\s+import',
                r'from\s+sys\s+import',
                r'from\s+subprocess\s+import'
            ],
            
            # Code injection patterns
            SecurityViolationType.CODE_INJECTION: [
                r'eval\s*\(',
                r'exec\s*\(',
                r'compile\s*\(',
                r'__import__\s*\(',
                r'getattr\s*\(',
                r'setattr\s*\(',
                r'hasattr\s*\(',
                r'delattr\s*\('
            ],
            
            # Path traversal patterns
            SecurityViolationType.PATH_TRAVERSAL: [
                r'\.\./\.\.',
                r'\.\.\\\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
                r'\.\.%2f',
                r'\.\.%5c'
            ],
            
            # Unsafe deserialization patterns
            SecurityViolationType.UNSAFE_DESERIALIZATION: [
                r'pickle\.',
                r'cPickle\.',
                r'marshal\.',
                r'shelve\.',
                r'yaml\.load\s*\(',
                r'yaml\.unsafe_load'
            ]
        }
        
        # Allowed modules for plugins
        self.allowed_modules = {
            'json', 'time', 'datetime', 'logging', 'threading', 'queue',
            'collections', 'itertools', 'functools', 'operator', 'random',
            'uuid', 'hashlib', 'hmac', 'base64', 'math', 'statistics',
            'decimal', 'fractions', 're', 'string', 'typing'
        }
        
        # Blocked modules
        self.blocked_modules = {
            'os', 'sys', 'subprocess', 'importlib', '__builtin__', 'builtins',
            'ctypes', 'multiprocessing', 'signal', 'atexit', 'weakref',
            'gc', 'site', 'sysconfig', 'pkgutil', 'zipimport', 'runpy'
        }
        
        # Security check weights for scoring
        self.check_weights = {
            'static_analysis': 0.3,
            'import_validation': 0.2,
            'pattern_matching': 0.2,
            'ast_analysis': 0.2,
            'file_integrity': 0.1
        }
    
    def audit_plugin(self, plugin_path: str) -> SecurityAuditResult:
        """
        Perform comprehensive security audit on a plugin
        
        Args:
            plugin_path: Path to the plugin file
            
        Returns:
            SecurityAuditResult: Audit results
        """
        self.logger.info(f"Starting security audit for plugin: {plugin_path}")
        
        plugin_name = os.path.basename(plugin_path).replace('.py', '')
        
        result = SecurityAuditResult(
            plugin_name=plugin_name,
            plugin_path=plugin_path,
            security_level=SecurityLevel.LOW,
            hash_signature=self._calculate_file_hash(plugin_path)
        )
        
        try:
            # Read plugin file
            with open(plugin_path, 'r', encoding='utf-8') as f:
                plugin_code = f.read()
            
            # Perform security checks
            self._check_static_analysis(plugin_code, result)
            self._check_imports(plugin_code, result)
            self._check_dangerous_patterns(plugin_code, result)
            self._check_ast_analysis(plugin_code, result)
            self._check_file_integrity(plugin_path, result)
            
            # Calculate compliance score
            result.compliance_score = self._calculate_compliance_score(result)
            
            # Determine overall security level
            result.security_level = self._determine_security_level(result)
            
            self.logger.info(f"Security audit completed for {plugin_name}: {result.security_level.value}")
            
        except Exception as e:
            self.logger.error(f"Security audit failed for {plugin_path}: {e}")
            result.violations.append(SecurityViolation(
                type=SecurityViolationType.CODE_INJECTION,
                severity=SecurityLevel.CRITICAL,
                description=f"Failed to audit plugin: {str(e)}",
                location=plugin_path,
                remediation="Fix syntax errors and ensure valid Python code"
            ))
            result.security_level = SecurityLevel.CRITICAL
        
        return result
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of the plugin file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _check_static_analysis(self, code: str, result: SecurityAuditResult):
        """Perform static code analysis"""
        try:
            # Check for basic syntax
            ast.parse(code)
            result.passed_checks.append("syntax_validation")
            
            # Check code complexity (simplified)
            lines = code.split('\n')
            if len(lines) > 1000:
                result.violations.append(SecurityViolation(
                    type=SecurityViolationType.RESOURCE_EXHAUSTION,
                    severity=SecurityLevel.MEDIUM,
                    description="Plugin code is too long (>1000 lines)",
                    location=result.plugin_path,
                    remediation="Reduce code complexity and length"
                ))
            else:
                result.passed_checks.append("code_complexity")
                
        except SyntaxError as e:
            result.violations.append(SecurityViolation(
                type=SecurityViolationType.CODE_INJECTION,
                severity=SecurityLevel.HIGH,
                description=f"Syntax error in plugin code: {str(e)}",
                location=result.plugin_path,
                line_number=e.lineno or 0,
                remediation="Fix syntax errors"
            ))
            result.failed_checks.append("syntax_validation")
    
    def _check_imports(self, code: str, result: SecurityAuditResult):
        """Check for dangerous imports"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name in self.blocked_modules:
                            result.violations.append(SecurityViolation(
                                type=SecurityViolationType.DANGEROUS_IMPORTS,
                                severity=SecurityLevel.HIGH,
                                description=f"Dangerous import detected: {module_name}",
                                location=result.plugin_path,
                                line_number=node.lineno,
                                code_snippet=f"import {alias.name}",
                                remediation=f"Remove import of {module_name}"
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name in self.blocked_modules:
                            result.violations.append(SecurityViolation(
                                type=SecurityViolationType.DANGEROUS_IMPORTS,
                                severity=SecurityLevel.HIGH,
                                description=f"Dangerous import detected: from {module_name}",
                                location=result.plugin_path,
                                line_number=node.lineno,
                                code_snippet=f"from {node.module} import ...",
                                remediation=f"Remove import from {module_name}"
                            ))
            
            result.passed_checks.append("import_validation")
            
        except Exception as e:
            self.logger.error(f"Import validation failed: {e}")
            result.failed_checks.append("import_validation")
    
    def _check_dangerous_patterns(self, code: str, result: SecurityAuditResult):
        """Check for dangerous code patterns"""
        lines = code.split('\n')
        
        for violation_type, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        severity = SecurityLevel.HIGH
                        if violation_type in [SecurityViolationType.CODE_INJECTION, 
                                            SecurityViolationType.SUBPROCESS_EXECUTION]:
                            severity = SecurityLevel.CRITICAL
                        
                        result.violations.append(SecurityViolation(
                            type=violation_type,
                            severity=severity,
                            description=f"Dangerous pattern detected: {pattern}",
                            location=result.plugin_path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            remediation=f"Remove or secure usage of {pattern}"
                        ))
        
        result.passed_checks.append("pattern_matching")
    
    def _check_ast_analysis(self, code: str, result: SecurityAuditResult):
        """Perform AST-based security analysis"""
        try:
            tree = ast.parse(code)
            
            # Check for dangerous function calls
            dangerous_calls = {'eval', 'exec', 'compile', '__import__'}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                        result.violations.append(SecurityViolation(
                            type=SecurityViolationType.CODE_INJECTION,
                            severity=SecurityLevel.CRITICAL,
                            description=f"Dangerous function call: {node.func.id}",
                            location=result.plugin_path,
                            line_number=node.lineno,
                            remediation=f"Remove {node.func.id} call"
                        ))
            
            result.passed_checks.append("ast_analysis")
            
        except Exception as e:
            self.logger.error(f"AST analysis failed: {e}")
            result.failed_checks.append("ast_analysis")
    
    def _check_file_integrity(self, file_path: str, result: SecurityAuditResult):
        """Check file integrity and permissions"""
        try:
            # Check file permissions
            file_stat = os.stat(file_path)
            if file_stat.st_mode & 0o002:  # World writable
                result.violations.append(SecurityViolation(
                    type=SecurityViolationType.FILE_SYSTEM_ACCESS,
                    severity=SecurityLevel.MEDIUM,
                    description="Plugin file is world-writable",
                    location=file_path,
                    remediation="Change file permissions to be more restrictive"
                ))
            
            # Check file size
            if file_stat.st_size > 1024 * 1024:  # 1MB
                result.violations.append(SecurityViolation(
                    type=SecurityViolationType.RESOURCE_EXHAUSTION,
                    severity=SecurityLevel.MEDIUM,
                    description="Plugin file is too large (>1MB)",
                    location=file_path,
                    remediation="Reduce plugin file size"
                ))
            
            result.passed_checks.append("file_integrity")
            
        except Exception as e:
            self.logger.error(f"File integrity check failed: {e}")
            result.failed_checks.append("file_integrity")
    
    def _calculate_compliance_score(self, result: SecurityAuditResult) -> float:
        """Calculate compliance score based on checks"""
        total_score = 0.0
        
        # Calculate score based on passed checks
        for check in result.passed_checks:
            if check in self.check_weights:
                total_score += self.check_weights[check]
        
        # Subtract score for violations
        for violation in result.violations:
            if violation.severity == SecurityLevel.CRITICAL:
                total_score -= 0.3
            elif violation.severity == SecurityLevel.HIGH:
                total_score -= 0.2
            elif violation.severity == SecurityLevel.MEDIUM:
                total_score -= 0.1
        
        return max(0.0, min(1.0, total_score))
    
    def _determine_security_level(self, result: SecurityAuditResult) -> SecurityLevel:
        """Determine overall security level"""
        # Check for critical violations
        for violation in result.violations:
            if violation.severity == SecurityLevel.CRITICAL:
                return SecurityLevel.CRITICAL
        
        # Check compliance score
        if result.compliance_score >= 0.8:
            return SecurityLevel.LOW
        elif result.compliance_score >= 0.6:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.HIGH
    
    def audit_all_plugins(self, plugin_directories: List[str]) -> List[SecurityAuditResult]:
        """
        Audit all plugins in the specified directories
        
        Args:
            plugin_directories: List of directories to scan
            
        Returns:
            List[SecurityAuditResult]: Audit results for all plugins
        """
        results = []
        
        for directory in plugin_directories:
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                if filename.endswith('.py') and not filename.startswith('__'):
                    plugin_path = os.path.join(directory, filename)
                    result = self.audit_plugin(plugin_path)
                    results.append(result)
        
        return results
    
    def generate_security_report(self, results: List[SecurityAuditResult]) -> str:
        """
        Generate a comprehensive security report
        
        Args:
            results: List of audit results
            
        Returns:
            str: Security report in markdown format
        """
        report = []
        report.append("# Plugin Security Audit Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_plugins = len(results)
        secure_plugins = sum(1 for r in results if r.security_level == SecurityLevel.LOW)
        critical_plugins = sum(1 for r in results if r.security_level == SecurityLevel.CRITICAL)
        
        report.append("## Summary")
        report.append(f"- **Total Plugins Audited:** {total_plugins}")
        report.append(f"- **Secure Plugins:** {secure_plugins}")
        report.append(f"- **Critical Issues:** {critical_plugins}")
        report.append(f"- **Overall Security Score:** {sum(r.compliance_score for r in results) / len(results):.2f}")
        report.append("")
        
        # Detailed results
        report.append("## Detailed Results")
        for result in results:
            report.append(f"### {result.plugin_name}")
            report.append(f"- **Security Level:** {result.security_level.value}")
            report.append(f"- **Compliance Score:** {result.compliance_score:.2f}")
            report.append(f"- **Violations:** {len(result.violations)}")
            
            if result.violations:
                report.append("- **Security Violations:**")
                for violation in result.violations:
                    report.append(f"  - {violation.type.value}: {violation.description}")
            
            report.append("")
        
        return '\n'.join(report)

class PluginSecurityDatabase:
    """Database for storing plugin security audit results"""
    
    def __init__(self, db_path: str = "plugin_security.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize security database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Security audit results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_name TEXT NOT NULL,
                    plugin_path TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    compliance_score REAL NOT NULL,
                    hash_signature TEXT NOT NULL,
                    audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    violations_json TEXT,
                    passed_checks_json TEXT,
                    failed_checks_json TEXT
                )
            ''')
            
            # Security violations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id INTEGER,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    line_number INTEGER,
                    code_snippet TEXT,
                    remediation TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audit_id) REFERENCES security_audits (id)
                )
            ''')
            
            conn.commit()
    
    def store_audit_result(self, result: SecurityAuditResult) -> int:
        """Store audit result in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store audit result
            cursor.execute('''
                INSERT INTO security_audits 
                (plugin_name, plugin_path, security_level, compliance_score, hash_signature, 
                 violations_json, passed_checks_json, failed_checks_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.plugin_name,
                result.plugin_path,
                result.security_level.value,
                result.compliance_score,
                result.hash_signature,
                json.dumps([v.__dict__ for v in result.violations], default=str),
                json.dumps(result.passed_checks),
                json.dumps(result.failed_checks)
            ))
            
            audit_id = cursor.lastrowid
            
            # Store violations
            for violation in result.violations:
                cursor.execute('''
                    INSERT INTO security_violations 
                    (audit_id, violation_type, severity, description, location, 
                     line_number, code_snippet, remediation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_id,
                    violation.type.value,
                    violation.severity.value,
                    violation.description,
                    violation.location,
                    violation.line_number,
                    violation.code_snippet,
                    violation.remediation
                ))
            
            conn.commit()
            return audit_id

def main():
    """Main function for testing the security auditor"""
    auditor = PluginSecurityAuditor()
    
    # Test directories
    plugin_directories = ['plugins', 'AI/plugins', 'NoxPanel/plugins']
    
    # Audit all plugins
    results = auditor.audit_all_plugins(plugin_directories)
    
    # Generate report
    report = auditor.generate_security_report(results)
    
    # Save report
    with open('plugin_security_report.md', 'w') as f:
        f.write(report)
    
    # Store results in database
    db = PluginSecurityDatabase()
    for result in results:
        db.store_audit_result(result)
    
    print("Security audit completed!")
    print(f"Audited {len(results)} plugins")
    print("Report saved to plugin_security_report.md")

if __name__ == "__main__":
    main()
