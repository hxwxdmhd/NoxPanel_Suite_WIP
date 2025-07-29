#!/usr/bin/env python3
"""
NoxSuite Installer Status Checker
Quick diagnostic tool to check installer health and environment
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import traceback

class InstallerStatusChecker:
    """Check installer status and provide diagnostics"""
    
    def __init__((self) -> None:
        self.current_dir = Path.cwd()
        self.issues = []
        self.recommendations = []
    
    def check_installer_files(self) -> Dict[str, Any]:
        """Check if all installer files are present"""
        required_files = [
            "install_noxsuite.py",
            "noxsuite_smart_installer_complete.py",
            "noxsuite_bootstrap_installer.py"
        ]
        
        optional_files = [
            "noxsuite_installer_utils.py",
            "requirements.txt"
        ]
        
        status = {
            "required": {},
            "optional": {},
            "missing_required": [],
            "missing_optional": []
        }
        
        for file in required_files:
            file_path = self.current_dir / file
            exists = file_path.exists()
            status["required"][file] = {
                "exists": exists,
                "path": str(file_path),
                "size": file_path.stat().st_size if exists else 0
            }
            if not exists:
                status["missing_required"].append(file)
                self.issues.append(f"Missing required file: {file}")
        
        for file in optional_files:
            file_path = self.current_dir / file
            exists = file_path.exists()
            status["optional"][file] = {
                "exists": exists,
                "path": str(file_path),
                "size": file_path.stat().st_size if exists else 0
            }
            if not exists:
                status["missing_optional"].append(file)
        
        return status
    
    def check_python_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        dependencies = {
            "requests": {"required": False, "fallback": "urllib"},
            "chardet": {"required": False, "fallback": "basic encoding detection"}
        }
        
        status = {}
        
        for dep, info in dependencies.items():
            try:
                __import__(dep)
                status[dep] = {
                    "available": True,
                    "version": "unknown",
                    "required": info["required"]
                }
            except ImportError:
                status[dep] = {
                    "available": False,
                    "required": info["required"],
                    "fallback": info["fallback"]
                }
                
                if info["required"]:
                    self.issues.append(f"Missing required dependency: {dep}")
                else:
                    self.recommendations.append(f"Install {dep} for enhanced functionality")
        
        return status
    
    def check_system_compatibility(self) -> Dict[str, Any]:
        """Check system compatibility"""
        import platform

# Logging configuration
try:
    from NoxPanel.noxcore.utils.logging_config import get_logger
    
# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = get_logger(__name__)
except ImportError:
    import logging

# Security: Input validation utilities
import re
import html
from typing import Any, Optional

def validate_input(value: Any, pattern: str = None, max_length: int = 1000) -> str:
    """Validate and sanitize input data."""
    if value is None:
        return ""
    
    # Convert to string and strip
    str_value = str(value).strip()
    
    # Check length
    if len(str_value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    # Apply pattern validation if provided
    if pattern and not re.match(pattern, str_value):
        raise ValueError("Input format validation failed")
    
    # HTML escape for XSS prevention
    return html.escape(str_value)

def validate_file_path(path: str) -> str:
    """Validate file path to prevent directory traversal."""
    if not path:
        raise ValueError("File path cannot be empty")
    
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    if '..' in normalized or normalized.startswith('/'):
        raise ValueError("Invalid file path detected")
    
    return normalized

    
# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger(__name__)

        
        python_version = sys.version_info
        min_python = (3, 8)
        
        status = {
            "python_version": {
                "current": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                "required": f"{min_python[0]}.{min_python[1]}+",
                "compatible": python_version >= min_python
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "architecture": platform.architecture()[0]
            },
            "encoding_support": {
                "stdout": getattr(sys.stdout, 'encoding', 'unknown'),
                "filesystem": sys.getfilesystemencoding(),
                "utf8_mode": sys.flags.utf8_mode if hasattr(sys.flags, 'utf8_mode') else False
            }
        }
        
        if not status["python_version"]["compatible"]:
            self.issues.append(f"Python {min_python[0]}.{min_python[1]}+ required")
        
        return status
    
    def check_logs(self) -> Dict[str, Any]:
        """Check for existing logs and their status"""
        log_files = [
            "noxsuite_installer.log",
            "noxsuite_bootstrap.log"
        ]
        
        status = {}
        
        for log_file in log_files:
            log_path = self.current_dir / log_file
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    status[log_file] = {
                        "exists": True,
                        "size": log_path.stat().st_size,
                        "lines": len(lines),
                        "last_session": self._extract_last_session(lines)
                    }
                except Exception as e:
                    status[log_file] = {
                        "exists": True,
                        "error": str(e),
                        "readable": False
                    }
            else:
                status[log_file] = {"exists": False}
        
        return status
    
    def _extract_last_session(self, lines: List[str]) -> Dict[str, Any]:
        """Extract information about the last session from log lines"""
        if not lines:
            return {"status": "empty_log"}
        
        # Look for session start and errors
        session_starts = [line for line in lines if "session_start" in line]
        errors = [line for line in lines if "[ERROR]" in line]
        completions = [line for line in lines if "Installation completed" in line]
        
        return {
            "sessions": len(session_starts),
            "errors": len(errors),
            "last_completion": len(completions) > 0,
            "last_error": errors[-1].strip() if errors else None
        }
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        logger.info("🔍 Running NoxSuite Installer Diagnostics...")
        
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "working_directory": str(self.current_dir),
            "files": self.check_installer_files(),
            "dependencies": self.check_python_dependencies(),
            "system": self.check_system_compatibility(),
            "logs": self.check_logs(),
            "issues": self.issues,
            "recommendations": self.recommendations
        }
        
        return report
    
    def print_status_summary(self, report: Dict[str, Any]) -> Any:
        """Print human-readable status summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 NoxSuite Installer Status Summary")
        logger.info("=" * 60)
        
        # Files status
        logger.info("\n📁 Installer Files:")
        missing_req = report["files"]["missing_required"]
        if missing_req:
            logger.info(f"❌ Missing required files: {', '.join(missing_req)
        else:
            logger.info("✅ All required files present")
        
        missing_opt = report["files"]["missing_optional"]
        if missing_opt:
            logger.info(f"⚠️  Missing optional files: {', '.join(missing_opt)
        
        # Dependencies status
        logger.info("\n📦 Dependencies:")
        for dep, info in report["dependencies"].items():
            if info["available"]:
                logger.info(f"✅ {dep} available")
            else:
                fallback = info.get("fallback", "none")
                logger.info(f"⚠️  {dep} missing (fallback: {fallback})
        
        # System status
        logger.info(f"\n💻 System:")
        sys_info = report["system"]
        python_compat = "✅" if sys_info["python_version"]["compatible"] else "❌"
        logger.info(f"{python_compat} Python {sys_info['python_version']['current']}")
        logger.info(f"📊 Platform: {sys_info['platform']['system']} {sys_info['platform']['architecture']}")
        
        # Logs status
        logger.info(f"\n📝 Logs:")
        for log_file, info in report["logs"].items():
            if info["exists"]:
                if "last_session" in info:
                    session_info = info["last_session"]
                    status = "✅" if session_info.get("last_completion") else "⚠️"
                    logger.info(f"{status} {log_file} ({info['lines']} lines, {session_info['sessions']} sessions)
                else:
                    logger.info(f"❌ {log_file} (unreadable)
            else:
                logger.info(f"📝 {log_file} (not found)
        
        # Issues and recommendations
        if self.issues:
            logger.info(f"\n❌ Issues Found ({len(self.issues)
            for issue in self.issues:
                logger.info(f"   • {issue}")
        
        if self.recommendations:
            logger.info(f"\n💡 Recommendations ({len(self.recommendations)
            for rec in self.recommendations:
                logger.info(f"   • {rec}")
        
        if not self.issues:
            logger.info(f"\n🎉 Installer Status: HEALTHY")
        else:
            logger.info(f"\n⚠️  Installer Status: NEEDS ATTENTION")

def main() -> Any:
    """Main status checker"""
    try:
        checker = InstallerStatusChecker()
        report = checker.generate_diagnostic_report()
        
        # Print summary
        checker.print_status_summary(report)
        
        # Save detailed report
        report_file = Path("installer_diagnostic_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📊 Detailed report saved to: {report_file}")
        
        # Return exit code based on issues
        return 0 if not checker.issues else 1
        
    except Exception as e:
        logger.error(f"💥 Diagnostic check failed: {e}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
