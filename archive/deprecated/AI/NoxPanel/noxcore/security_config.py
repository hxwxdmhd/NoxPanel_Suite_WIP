"""
NoxPanel v5.0 - Environment-Specific Security Configuration
Secure configuration management for different deployment environments
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration for different environments"""
    require_auth: bool = True
    rate_limit_auth: str = "5/minute"
    rate_limit_api: str = "100/minute" 
    rate_limiting_enabled: bool = True  # Added missing attribute for test compatibility
    ssl_required: bool = False
    secret_from_env: bool = True
    secret_key: str = "change-this-in-production"  # Added missing secret_key attribute
    session_timeout_hours: int = 24
    session_lifetime: int = 86400  # Added missing session_lifetime attribute (in seconds)
    session_cookie_secure: bool = False  # Added missing session_cookie_secure attribute
    session_cookie_httponly: bool = True  # Added for security
    session_cookie_samesite: str = "Lax"  # Added missing session_cookie_samesite attribute
    content_security_policy_enabled: bool = True  # Added missing CSP attribute
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_2fa: bool = False
    csrf_protection: bool = True
    secure_headers: bool = True

class EnvironmentSecurityManager:
    """Manages security configuration across environments"""
    
    SECURITY_PROFILES = {
        'production': SecurityConfig(
            require_auth=True,
            rate_limit_auth="3/minute",
            rate_limit_api="60/minute",
            rate_limiting_enabled=True,
            ssl_required=True,
            secret_from_env=True,
            secret_key="PRODUCTION-SECRET-REQUIRED",
            session_timeout_hours=8,
            session_lifetime=28800,  # 8 hours in seconds
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            content_security_policy_enabled=True,
            password_min_length=12,
            max_login_attempts=3,
            lockout_duration_minutes=30,
            enable_2fa=True,
            csrf_protection=True,
            secure_headers=True
        ),
        'staging': SecurityConfig(
            require_auth=True,
            rate_limit_auth="5/minute", 
            rate_limit_api="100/minute",
            rate_limiting_enabled=True,
            ssl_required=True,
            secret_from_env=True,
            secret_key="STAGING-SECRET-REQUIRED",
            session_timeout_hours=12,
            session_lifetime=43200,  # 12 hours in seconds
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            content_security_policy_enabled=True,
            password_min_length=10,
            max_login_attempts=5,
            lockout_duration_minutes=15,
            enable_2fa=False,
            csrf_protection=True,
            secure_headers=True
        ),
        'development': SecurityConfig(
            require_auth=True,  # SECURITY: No bypass even in dev
            rate_limit_auth="10/minute",
            rate_limit_api="200/minute", 
            rate_limiting_enabled=True,
            ssl_required=False,
            secret_from_env=True,
            secret_key="dev-secret-key-change-in-production",
            session_timeout_hours=24,
            session_lifetime=86400,  # 24 hours in seconds
            session_cookie_secure=False,
            session_cookie_httponly=True,
            session_cookie_samesite="Lax",
            content_security_policy_enabled=True,
            password_min_length=8,
            max_login_attempts=10,
            lockout_duration_minutes=5,
            enable_2fa=False,
            csrf_protection=True,
            secure_headers=False
        ),
        'testing': SecurityConfig(
            require_auth=False,  # Only for automated tests
            rate_limit_auth="1000/minute",
            rate_limit_api="1000/minute",
            rate_limiting_enabled=False,
            ssl_required=False, 
            secret_from_env=False,
            secret_key="test-secret-key-insecure",
            session_timeout_hours=1,
            session_lifetime=3600,  # 1 hour in seconds
            session_cookie_secure=False,
            session_cookie_httponly=False,
            session_cookie_samesite="None",
            content_security_policy_enabled=False,
            password_min_length=4,
            max_login_attempts=100,
            lockout_duration_minutes=1,
            enable_2fa=False,
            csrf_protection=False,
            secure_headers=False
        )
    }
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.config = self._load_security_config()
        logger.info(f"[SEC] Security profile loaded: {self.environment}")
    
    def _detect_environment(self) -> str:
        """Detect current environment from environment variables"""
        env = os.getenv("NOXPANEL_ENV", "development").lower()
        
        if env not in self.SECURITY_PROFILES:
            logger.warning(f"Unknown environment '{env}', defaulting to 'development'")
            env = "development"
            
        return env
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration for current environment"""
        config = self.SECURITY_PROFILES[self.environment]
        
        # Override with environment variables if specified
        force_auth = os.getenv("NOXPANEL_FORCE_AUTH")
        if force_auth:
            config.require_auth = force_auth.lower() == "true"
            
        ssl_required = os.getenv("NOXPANEL_SSL_REQUIRED")
        if ssl_required:
            config.ssl_required = ssl_required.lower() == "true"
            
        return config
    
    def get_config(self) -> SecurityConfig:
        """Get current security configuration"""
        return self.config
    
    def get_security_config(self, environment: Optional[str] = None) -> SecurityConfig:
        """Get security configuration for specified environment"""
        if environment:
            return self.SECURITY_PROFILES.get(environment.lower(), self.config)
        return self.config
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def get_secret_key(self) -> str:
        """Get secret key from environment or generate secure default"""
        if self.config.secret_from_env:
            secret = os.getenv("NOXPANEL_SECRET_KEY")
            if not secret:
                if self.is_production():
                    raise ValueError("NOXPANEL_SECRET_KEY environment variable required in production")
                else:
                    logger.warning("No NOXPANEL_SECRET_KEY set, using development fallback")
                    secret = "dev-secret-key-change-in-production"
            return secret
        else:
            # Only for testing environment
            return "test-secret-key"
    
    def get_rate_limits(self) -> Dict[str, str]:
        """Get rate limiting configuration"""
        return {
            'auth': self.config.rate_limit_auth,
            'api': self.config.rate_limit_api
        }
    
    def should_enforce_ssl(self) -> bool:
        """Check if SSL should be enforced"""
        return self.config.ssl_required
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers configuration"""
        if not self.config.secure_headers:
            return {}
            
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        if self.config.ssl_required:
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
        if self.config.csrf_protection:
            headers['X-CSRF-Protection'] = 'enabled'
            
        return headers

# Global security manager instance
security_manager = EnvironmentSecurityManager()

def get_security_config() -> SecurityConfig:
    """Get current security configuration"""
    return security_manager.get_config()

def is_production() -> bool:
    """Check if running in production"""
    return security_manager.is_production()

def get_secret_key() -> str:
    """Get application secret key"""
    return security_manager.get_secret_key()

def get_rate_limits() -> Dict[str, str]:
    """Get rate limiting configuration"""
    return security_manager.get_rate_limits()
