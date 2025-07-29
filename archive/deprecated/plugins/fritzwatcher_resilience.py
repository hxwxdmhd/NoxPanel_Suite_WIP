"""
FRITZWATCHER Resilience Framework
=================================

Enhanced stability and recovery mechanisms for FRITZWATCHER plugin.
Implements retry logic, graceful failover, and temporary credential overrides.

Author: MSP-Aware Development Team
Date: July 19, 2025
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
import time
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass
class FailoverConfig:
    """Configuration for failover logic"""
    primary_router_timeout: float = 10.0
    secondary_router_delay: float = 5.0
    health_check_interval: float = 60.0
    max_consecutive_failures: int = 3

class RouterHealthMonitor:
    """Monitor router health and manage failover"""
    
    def __init__(self, config: FailoverConfig):
        self.config = config
        self.router_health: Dict[str, Dict[str, Any]] = {}
        self.primary_router: Optional[str] = None
        self.active_router: Optional[str] = None
        self.last_health_check = datetime.now()
        
    def update_router_health(self, router_id: str, is_healthy: bool, response_time: float = 0.0):
        """Update health status for a router"""
        if router_id not in self.router_health:
            self.router_health[router_id] = {
                'consecutive_failures': 0,
                'last_success': None,
                'last_failure': None,
                'average_response_time': 0.0,
                'total_requests': 0,
                'successful_requests': 0
            }
        
        health = self.router_health[router_id]
        health['total_requests'] += 1
        
        if is_healthy:
            health['consecutive_failures'] = 0
            health['last_success'] = datetime.now()
            health['successful_requests'] += 1
            
            # Update average response time
            if health['average_response_time'] == 0:
                health['average_response_time'] = response_time
            else:
                health['average_response_time'] = (
                    health['average_response_time'] * 0.8 + response_time * 0.2
                )
        else:
            health['consecutive_failures'] += 1
            health['last_failure'] = datetime.now()
            
        logger.debug(f"Router {router_id} health updated: {health}")
        
    def is_router_healthy(self, router_id: str) -> bool:
        """Check if a router is considered healthy"""
        if router_id not in self.router_health:
            return True  # Unknown routers are assumed healthy
            
        health = self.router_health[router_id]
        return health['consecutive_failures'] < self.config.max_consecutive_failures
        
    def get_best_router(self, available_routers: List[str]) -> Optional[str]:
        """Get the best available router based on health metrics"""
        healthy_routers = [r for r in available_routers if self.is_router_healthy(r)]
        
        if not healthy_routers:
            # All routers are unhealthy, return the least unhealthy one
            if available_routers:
                return min(available_routers, 
                          key=lambda r: self.router_health.get(r, {}).get('consecutive_failures', 0))
            return None
            
        # Sort by average response time (ascending)
        healthy_routers.sort(key=lambda r: self.router_health.get(r, {}).get('average_response_time', float('inf')))
        
        return healthy_routers[0]

class TemporaryCredentialManager:
    """Manage temporary credential overrides"""
    
    def __init__(self):
        self.temp_credentials: Dict[str, Dict[str, Any]] = {}
        self.credential_expires: Dict[str, datetime] = {}
        
    def set_temporary_credential(self, router_id: str, username: str, password: str, 
                               expires_in_minutes: int = 60):
        """Set temporary credentials for a router"""
        self.temp_credentials[router_id] = {
            'username': username,
            'password': password,
            'source': 'web_ui_override'
        }
        self.credential_expires[router_id] = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        logger.info(f"Set temporary credentials for router {router_id} (expires in {expires_in_minutes} minutes)")
        
    def get_credentials(self, router_id: str) -> Optional[Dict[str, str]]:
        """Get credentials for a router (temporary override > environment > KeePass)"""
        # Check temporary credentials first
        if router_id in self.temp_credentials:
            if datetime.now() < self.credential_expires.get(router_id, datetime.now()):
                return self.temp_credentials[router_id]
            else:
                # Expired, remove
                del self.temp_credentials[router_id]
                if router_id in self.credential_expires:
                    del self.credential_expires[router_id]
                logger.info(f"Temporary credentials for router {router_id} expired")
        
        # Check environment variables
        env_username = os.getenv(f'FRITZBOX_{router_id.upper()}_USERNAME')
        env_password = os.getenv(f'FRITZBOX_{router_id.upper()}_PASSWORD')
        
        if env_username and env_password:
            return {
                'username': env_username,
                'password': env_password,
                'source': 'environment'
            }
        
        # Check .env file
        env_file_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f'FRITZBOX_{router_id.upper()}_USERNAME='):
                            env_username = line.split('=', 1)[1].strip('"\'')
                        elif line.startswith(f'FRITZBOX_{router_id.upper()}_PASSWORD='):
                            env_password = line.split('=', 1)[1].strip('"\'')
                
                if env_username and env_password:
                    return {
                        'username': env_username,
                        'password': env_password,
                        'source': 'env_file'
                    }
            except Exception as e:
                logger.warning(f"Error reading .env file: {e}")
        
        return None

class ResilienceManager:
    """Main resilience manager combining retry, failover, and credential management"""
    
    def __init__(self, retry_config: RetryConfig = None, failover_config: FailoverConfig = None):
        self.retry_config = retry_config or RetryConfig()
        self.failover_config = failover_config or FailoverConfig()
        self.health_monitor = RouterHealthMonitor(self.failover_config)
        self.credential_manager = TemporaryCredentialManager()
        
    async def execute_with_retry(self, func: Callable, *args, router_id: str = None, **kwargs) -> Any:
        """Execute a function with retry logic and health monitoring"""
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                start_time = time.time()
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                
                if router_id:
                    self.health_monitor.update_router_health(router_id, True, response_time)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if router_id:
                    self.health_monitor.update_router_health(router_id, False)
                
                if attempt < self.retry_config.max_attempts - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                        self.retry_config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if self.retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Attempt {attempt + 1} failed for router {router_id}: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.retry_config.max_attempts} attempts failed for router {router_id}: {e}")
        
        raise last_exception
    
    async def execute_with_failover(self, func: Callable, router_list: List[str], *args, **kwargs) -> Any:
        """Execute a function with automatic failover between routers"""
        best_router = self.health_monitor.get_best_router(router_list)
        
        if best_router:
            # Try the best router first
            try:
                return await self.execute_with_retry(func, *args, router_id=best_router, **kwargs)
            except Exception as e:
                logger.warning(f"Primary router {best_router} failed: {e}")
                
                # Try other routers
                for router_id in router_list:
                    if router_id != best_router and self.health_monitor.is_router_healthy(router_id):
                        try:
                            logger.info(f"Attempting failover to router {router_id}")
                            return await self.execute_with_retry(func, *args, router_id=router_id, **kwargs)
                        except Exception as fe:
                            logger.warning(f"Failover to router {router_id} failed: {fe}")
                            continue
        
        # If all routers failed, try one last time with the original best router
        if best_router:
            logger.info(f"Final attempt with router {best_router}")
            return await self.execute_with_retry(func, *args, router_id=best_router, **kwargs)
        
        raise Exception("All routers failed and no fallback available")

# Global resilience manager instance
_resilience_manager = None

def get_resilience_manager() -> ResilienceManager:
    """Get the global resilience manager instance"""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = ResilienceManager()
    return _resilience_manager

def configure_resilience(retry_config: RetryConfig = None, failover_config: FailoverConfig = None):
    """Configure the global resilience manager"""
    global _resilience_manager
    _resilience_manager = ResilienceManager(retry_config, failover_config)

# Convenience decorators
def with_retry(router_id: str = None):
    """Decorator for adding retry logic to functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_resilience_manager()
            return await manager.execute_with_retry(func, *args, router_id=router_id, **kwargs)
        return wrapper
    return decorator

def with_failover(router_list: List[str]):
    """Decorator for adding failover logic to functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_resilience_manager()
            return await manager.execute_with_failover(func, router_list, *args, **kwargs)
        return wrapper
    return decorator
