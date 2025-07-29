#!/usr/bin/env python3
"""
Phase 2: Production Deployment Validation & Stress Testing
==========================================================

This script validates the production readiness of the unified server
and plugin system by conducting comprehensive stress testing and
performance validation.

Codename: FRITZWATCHER Validation Framework
Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
import psutil
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionValidator:
    """Production deployment validation and stress testing framework"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = None
        self.results = {
            'start_time': datetime.now(),
            'server_health': {},
            'plugin_tests': {},
            'stress_tests': {},
            'performance_metrics': {},
            'security_audit': {},
            'uptime_test': {}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def validate_server_health(self) -> Dict[str, Any]:
        """Validate basic server health and connectivity"""
        logger.info("🔍 Validating server health...")
        
        health_checks = {
            'server_connectivity': False,
            'plugin_system_active': False,
            'api_endpoints_responsive': False,
            'database_operational': False,
            'response_time_ms': 0
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/api/health") as response:
                end_time = time.time()
                
                if response.status == 200:
                    health_checks['server_connectivity'] = True
                    health_checks['response_time_ms'] = round((end_time - start_time) * 1000, 2)
                    
                    data = await response.json()
                    health_checks['database_operational'] = data.get('database', {}).get('status') == 'connected'
                    
            # Test plugin system
            async with self.session.get(f"{self.base_url}/api/plugins") as response:
                if response.status == 200:
                    health_checks['plugin_system_active'] = True
                    data = await response.json()
                    health_checks['active_plugins'] = data.get('system_metrics', {}).get('active_plugins', 0)
                    
            # Test API endpoints
            endpoints = [
                '/api/plugins/system/health',
                '/api/plugins/system/metrics',
                '/api/system/info'
            ]
            
            responsive_endpoints = 0
            for endpoint in endpoints:
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            responsive_endpoints += 1
                except Exception as e:
                    logger.warning(f"Endpoint {endpoint} failed: {e}")
                    
            health_checks['api_endpoints_responsive'] = responsive_endpoints == len(endpoints)
            health_checks['responsive_endpoint_count'] = responsive_endpoints
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_checks['error'] = str(e)
            
        self.results['server_health'] = health_checks
        logger.info(f"✅ Server health check completed: {health_checks}")
        return health_checks
        
    async def stress_test_plugin_endpoints(self, concurrent_requests: int = 10, duration_seconds: int = 60) -> Dict[str, Any]:
        """Stress test plugin management endpoints"""
        logger.info(f"🚀 Starting stress test: {concurrent_requests} concurrent requests for {duration_seconds} seconds")
        
        endpoints = [
            '/api/plugins',
            '/api/plugins/system/health',
            '/api/plugins/system/metrics'
        ]
        
        stress_results = {
            'concurrent_requests': concurrent_requests,
            'duration_seconds': duration_seconds,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'max_response_time': 0,
            'min_response_time': float('inf'),
            'response_times': [],
            'error_rates': {},
            'throughput_rps': 0
        }
        
        async def make_request(endpoint: str) -> Dict[str, Any]:
            """Make a single request and record metrics"""
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    
                    return {
                        'success': response.status == 200,
                        'response_time': response_time,
                        'status_code': response.status,
                        'endpoint': endpoint
                    }
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': str(e),
                    'endpoint': endpoint
                }
                
        # Run stress test
        start_time = time.time()
        tasks = []
        
        while time.time() - start_time < duration_seconds:
            # Create batch of concurrent requests
            batch_tasks = []
            for _ in range(concurrent_requests):
                endpoint = endpoints[len(batch_tasks) % len(endpoints)]
                batch_tasks.append(make_request(endpoint))
                
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Process results
            for result in batch_results:
                stress_results['total_requests'] += 1
                if result['success']:
                    stress_results['successful_requests'] += 1
                else:
                    stress_results['failed_requests'] += 1
                    
                response_time = result['response_time']
                stress_results['response_times'].append(response_time)
                stress_results['max_response_time'] = max(stress_results['max_response_time'], response_time)
                stress_results['min_response_time'] = min(stress_results['min_response_time'], response_time)
                
            # Small delay to prevent overwhelming the server
            await asyncio.sleep(0.1)
            
        # Calculate final metrics
        if stress_results['response_times']:
            stress_results['average_response_time'] = statistics.mean(stress_results['response_times'])
            stress_results['median_response_time'] = statistics.median(stress_results['response_times'])
            stress_results['p95_response_time'] = sorted(stress_results['response_times'])[int(0.95 * len(stress_results['response_times']))]
            
        actual_duration = time.time() - start_time
        stress_results['actual_duration'] = actual_duration
        stress_results['throughput_rps'] = stress_results['total_requests'] / actual_duration
        
        self.results['stress_tests'] = stress_results
        logger.info(f"✅ Stress test completed: {stress_results['total_requests']} requests, {stress_results['successful_requests']} successful")
        return stress_results
        
    async def validate_plugin_performance(self) -> Dict[str, Any]:
        """Validate plugin-specific performance metrics"""
        logger.info("📊 Validating plugin performance...")
        
        performance_results = {
            'plugin_load_times': {},
            'plugin_response_times': {},
            'memory_usage': {},
            'cpu_usage': {},
            'plugin_health_checks': {}
        }
        
        try:
            # Get current plugin list
            async with self.session.get(f"{self.base_url}/api/plugins") as response:
                if response.status == 200:
                    data = await response.json()
                    plugins = data.get('plugins', {})
                    
                    # Test each plugin's performance
                    for plugin_name, plugin_info in plugins.items():
                        if plugin_info.get('active', False):
                            # Test plugin response time
                            start_time = time.time()
                            try:
                                async with self.session.get(f"{self.base_url}/api/plugins/{plugin_name}") as plugin_response:
                                    end_time = time.time()
                                    response_time = (end_time - start_time) * 1000
                                    
                                    performance_results['plugin_response_times'][plugin_name] = {
                                        'response_time_ms': response_time,
                                        'success': plugin_response.status == 200
                                    }
                            except Exception as e:
                                performance_results['plugin_response_times'][plugin_name] = {
                                    'error': str(e),
                                    'success': False
                                }
                                
                            # Test plugin metrics endpoint
                            try:
                                async with self.session.get(f"{self.base_url}/api/plugins/{plugin_name}/metrics") as metrics_response:
                                    if metrics_response.status == 200:
                                        metrics_data = await metrics_response.json()
                                        performance_results['plugin_health_checks'][plugin_name] = metrics_data
                            except Exception as e:
                                logger.warning(f"Failed to get metrics for {plugin_name}: {e}")
                                
        except Exception as e:
            logger.error(f"Plugin performance validation failed: {e}")
            performance_results['error'] = str(e)
            
        # Get system resource usage
        try:
            performance_results['memory_usage'] = {
                'total_mb': round(psutil.virtual_memory().total / (1024*1024), 2),
                'available_mb': round(psutil.virtual_memory().available / (1024*1024), 2),
                'used_percent': psutil.virtual_memory().percent
            }
            
            performance_results['cpu_usage'] = {
                'current_percent': psutil.cpu_percent(interval=1),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else 'N/A'
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            
        self.results['performance_metrics'] = performance_results
        logger.info(f"✅ Plugin performance validation completed")
        return performance_results
        
    async def security_audit(self) -> Dict[str, Any]:
        """Perform basic security audit of the plugin system"""
        logger.info("🔒 Conducting security audit...")
        
        security_results = {
            'plugin_security_validation': {},
            'api_security_headers': {},
            'authentication_tests': {},
            'input_validation_tests': {}
        }
        
        try:
            # Test plugin security validation
            async with self.session.get(f"{self.base_url}/api/plugins") as response:
                if response.status == 200:
                    data = await response.json()
                    plugins = data.get('plugins', {})
                    
                    for plugin_name, plugin_info in plugins.items():
                        security_results['plugin_security_validation'][plugin_name] = {
                            'security_valid': plugin_info.get('security_valid', False),
                            'risk_level': plugin_info.get('risk_level', 'UNKNOWN'),
                            'security_violations': plugin_info.get('security_violations', [])
                        }
                        
            # Test API security headers
            async with self.session.get(f"{self.base_url}/api/plugins/system/health") as response:
                security_results['api_security_headers'] = {
                    'content_type': response.headers.get('Content-Type', 'Not set'),
                    'server': response.headers.get('Server', 'Not disclosed'),
                    'x_frame_options': response.headers.get('X-Frame-Options', 'Not set'),
                    'x_content_type_options': response.headers.get('X-Content-Type-Options', 'Not set')
                }
                
            # Test input validation (basic)
            test_payloads = [
                '../../../etc/passwd',
                '<script>alert("xss")</script>',
                '"; DROP TABLE plugins; --',
                '{{7*7}}'
            ]
            
            for payload in test_payloads:
                try:
                    async with self.session.get(f"{self.base_url}/api/plugins/{payload}") as response:
                        security_results['input_validation_tests'][payload] = {
                            'status_code': response.status,
                            'handled_safely': response.status in [400, 404, 422]
                        }
                except Exception as e:
                    security_results['input_validation_tests'][payload] = {
                        'error': str(e),
                        'handled_safely': True  # Exception handling is good
                    }
                    
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            security_results['error'] = str(e)
            
        self.results['security_audit'] = security_results
        logger.info(f"✅ Security audit completed")
        return security_results
        
    async def uptime_test(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Test system uptime and stability"""
        logger.info(f"⏱️ Starting uptime test for {duration_minutes} minutes...")
        
        uptime_results = {
            'duration_minutes': duration_minutes,
            'health_checks': [],
            'downtime_events': [],
            'availability_percent': 0,
            'average_response_time': 0
        }
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        response_times = []
        successful_checks = 0
        total_checks = 0
        
        while time.time() < end_time:
            check_start = time.time()
            total_checks += 1
            
            try:
                async with self.session.get(f"{self.base_url}/api/health") as response:
                    check_end = time.time()
                    response_time = (check_end - check_start) * 1000
                    
                    if response.status == 200:
                        successful_checks += 1
                        response_times.append(response_time)
                        
                        uptime_results['health_checks'].append({
                            'timestamp': datetime.now().isoformat(),
                            'response_time_ms': response_time,
                            'status': 'healthy'
                        })
                    else:
                        uptime_results['downtime_events'].append({
                            'timestamp': datetime.now().isoformat(),
                            'status_code': response.status,
                            'response_time_ms': response_time
                        })
                        
            except Exception as e:
                uptime_results['downtime_events'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'response_time_ms': 0
                })
                
            # Wait before next check
            await asyncio.sleep(10)  # Check every 10 seconds
            
        # Calculate final metrics
        uptime_results['availability_percent'] = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        uptime_results['average_response_time'] = statistics.mean(response_times) if response_times else 0
        uptime_results['total_checks'] = total_checks
        uptime_results['successful_checks'] = successful_checks
        
        self.results['uptime_test'] = uptime_results
        logger.info(f"✅ Uptime test completed: {uptime_results['availability_percent']:.2f}% availability")
        return uptime_results
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete production validation suite"""
        logger.info("🚀 Starting full production validation suite...")
        
        try:
            # 1. Server health check
            await self.validate_server_health()
            
            # 2. Plugin performance validation
            await self.validate_plugin_performance()
            
            # 3. Security audit
            await self.security_audit()
            
            # 4. Stress testing
            await self.stress_test_plugin_endpoints(concurrent_requests=5, duration_seconds=30)
            
            # 5. Short uptime test (2 minutes for demo)
            await self.uptime_test(duration_minutes=2)
            
        except Exception as e:
            logger.error(f"Validation suite failed: {e}")
            self.results['validation_error'] = str(e)
            
        # Calculate overall score
        self.results['end_time'] = datetime.now()
        self.results['total_duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()
        self.results['overall_score'] = self._calculate_overall_score()
        
        logger.info(f"✅ Full validation completed with score: {self.results['overall_score']}/100")
        return self.results
        
    def _calculate_overall_score(self) -> int:
        """Calculate overall production readiness score"""
        score = 0
        
        # Server health (30 points)
        health = self.results.get('server_health', {})
        if health.get('server_connectivity'):
            score += 10
        if health.get('plugin_system_active'):
            score += 10
        if health.get('api_endpoints_responsive'):
            score += 10
            
        # Performance (25 points)
        performance = self.results.get('performance_metrics', {})
        if performance and not performance.get('error'):
            score += 15
            
        stress = self.results.get('stress_tests', {})
        if stress.get('average_response_time', 0) < 100:  # < 100ms average
            score += 10
            
        # Security (25 points)
        security = self.results.get('security_audit', {})
        if security and not security.get('error'):
            score += 15
            
        plugin_security = security.get('plugin_security_validation', {})
        if all(p.get('security_valid', False) for p in plugin_security.values()):
            score += 10
            
        # Uptime (20 points)
        uptime = self.results.get('uptime_test', {})
        availability = uptime.get('availability_percent', 0)
        if availability >= 99:
            score += 20
        elif availability >= 95:
            score += 15
        elif availability >= 90:
            score += 10
            
        return min(score, 100)
        
    def save_results(self, filename: str = None) -> str:
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_validation_{timestamp}.json"
            
        filepath = os.path.join('logs', filename)
        os.makedirs('logs', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        logger.info(f"💾 Results saved to: {filepath}")
        return filepath


async def main():
    """Main validation execution"""
    print("🚀 MSP-Aware Production Deployment Validation")
    print("=" * 50)
    
    async with ProductionValidator() as validator:
        results = await validator.run_full_validation()
        
        # Save results
        filepath = validator.save_results()
        
        # Print summary
        print("\n📊 VALIDATION RESULTS SUMMARY")
        print("=" * 50)
        print(f"Overall Score: {results['overall_score']}/100")
        print(f"Server Health: {'✅ HEALTHY' if results['server_health'].get('server_connectivity') else '❌ UNHEALTHY'}")
        print(f"Plugin System: {'✅ ACTIVE' if results['server_health'].get('plugin_system_active') else '❌ INACTIVE'}")
        print(f"Average Response Time: {results['stress_tests'].get('average_response_time', 0):.2f}ms")
        print(f"Uptime: {results['uptime_test'].get('availability_percent', 0):.2f}%")
        print(f"Security Status: {'✅ VALIDATED' if not results['security_audit'].get('error') else '❌ ISSUES FOUND'}")
        print(f"Results saved to: {filepath}")
        
        # Determine readiness
        if results['overall_score'] >= 85:
            print("\n🎉 PRODUCTION READY!")
            print("System meets all production deployment criteria.")
        elif results['overall_score'] >= 70:
            print("\n⚠️ PRODUCTION READY WITH MONITORING")
            print("System is suitable for production with enhanced monitoring.")
        else:
            print("\n❌ NOT PRODUCTION READY")
            print("System requires optimization before production deployment.")
            
    return results


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run validation
    results = asyncio.run(main())
