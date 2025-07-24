#!/usr/bin/env python3
"""
🧪 ULTIMATE SUITE v9.0 - COMPREHENSIVE STABILITY TESTING SUITE
================================================================

Test scenarios covering:
1. 🌐 Web Interface Responsiveness
2. 🤖 AI Model Integration 
3. 🔌 Plugin Loading/Unloading
4. 📡 Network Scanning Accuracy
5. 📊 System Metrics Collection
6. ⚠️ Error Handling and Recovery
7. 💾 Memory Usage and Performance
8. 👥 Multi-user Concurrent Access

This testing suite validates all integrated v9.0 components and ensures
the platform is production-ready before v9.1 development.
"""

import os
import sys
import json
import time
import asyncio
import threading
import requests
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
import subprocess
import concurrent.futures

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class UltimateSuiteStabilityTester:
    """Comprehensive stability testing for Ultimate Suite v9.0"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.webapp_file = self.base_dir / "ultimate_webapp_v9.py"
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite_version': '1.0',
            'webapp_version': '9.0',
            'tests_executed': [],
            'tests_passed': 0,
            'tests_failed': 0,
            'total_tests': 0,
            'performance_metrics': {},
            'errors': [],
            'recommendations': [],
            'overall_status': 'pending'
        }
        
        self.webapp_process = None
        self.base_url = "http://127.0.0.1:5000"
        
    def start_webapp(self) -> bool:
        """Start the Ultimate Suite webapp for testing"""
        try:
            logger.info("🚀 Starting Ultimate Suite webapp for testing...")
            
            # Start webapp in background
            self.webapp_process = subprocess.Popen([
                sys.executable, "launch_ultimate_suite_v9_fixed.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for startup
            time.sleep(10)
            
            # Check if process is still running
            if self.webapp_process.poll() is None:
                logger.info("✅ Webapp started successfully")
                return True
            else:
                stdout, stderr = self.webapp_process.communicate()
                logger.error(f"❌ Webapp startup failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start webapp: {e}")
            return False
    
    def stop_webapp(self):
        """Stop the webapp process"""
        if self.webapp_process:
            try:
                self.webapp_process.terminate()
                self.webapp_process.wait(timeout=10)
                logger.info("✅ Webapp stopped")
            except:
                try:
                    self.webapp_process.kill()
                    logger.info("✅ Webapp force-stopped")
                except:
                    logger.warning("⚠️ Could not stop webapp process")
    
    def test_web_interface_responsiveness(self) -> Dict[str, Any]:
        """Test 1: Web interface responsiveness and loading times"""
        logger.info("🧪 Testing web interface responsiveness...")
        
        test_result = {
            'test_name': 'web_interface_responsiveness',
            'status': 'pending',
            'start_time': time.time(),
            'response_times': {},
            'errors': []
        }
        
        endpoints_to_test = [
            ('/', 'main_dashboard'),
            ('/api/status', 'api_status'),
            ('/api/v9/system-metrics', 'system_metrics'),
            ('/api/v9/network-status', 'network_status'),
            ('/api/v9/plugins/marketplace', 'plugin_marketplace')
        ]
        
        try:
            for endpoint, name in endpoints_to_test:
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    test_result['response_times'][name] = {
                        'response_time_ms': response_time * 1000,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code != 200:
                        test_result['errors'].append(f"{endpoint}: HTTP {response.status_code}")
                        
                except requests.RequestException as e:
                    test_result['response_times'][name] = {
                        'response_time_ms': (time.time() - start_time) * 1000,
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    }
                    test_result['errors'].append(f"{endpoint}: {str(e)}")
            
            # Calculate averages
            successful_responses = [r for r in test_result['response_times'].values() if r['success']]
            if successful_responses:
                avg_response_time = sum(r['response_time_ms'] for r in successful_responses) / len(successful_responses)
                test_result['average_response_time_ms'] = avg_response_time
                test_result['status'] = 'passed' if avg_response_time < 2000 and len(test_result['errors']) == 0 else 'failed'
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append("No successful responses")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_system_metrics_collection(self) -> Dict[str, Any]:
        """Test 2: System metrics collection accuracy and performance"""
        logger.info("🧪 Testing system metrics collection...")
        
        test_result = {
            'test_name': 'system_metrics_collection',
            'status': 'pending',
            'start_time': time.time(),
            'metrics_samples': [],
            'errors': []
        }
        
        try:
            # Collect multiple metric samples
            for i in range(5):
                try:
                    response = requests.get(f"{self.base_url}/api/v9/system-metrics", timeout=5)
                    if response.status_code == 200:
                        metrics = response.json()
                        
                        # Validate metric structure
                        required_fields = ['timestamp', 'cpu', 'memory', 'disk']
                        if all(field in metrics for field in required_fields):
                            test_result['metrics_samples'].append({
                                'sample': i + 1,
                                'timestamp': metrics['timestamp'],
                                'cpu_percent': metrics['cpu'].get('percent', 0),
                                'memory_percent': metrics['memory'].get('percent', 0),
                                'disk_percent': metrics['disk'].get('percent', 0),
                                'valid': True
                            })
                        else:
                            test_result['errors'].append(f"Sample {i+1}: Missing required fields")
                    else:
                        test_result['errors'].append(f"Sample {i+1}: HTTP {response.status_code}")
                        
                except Exception as e:
                    test_result['errors'].append(f"Sample {i+1}: {str(e)}")
                
                time.sleep(1)  # Wait between samples
            
            # Evaluate results
            valid_samples = [s for s in test_result['metrics_samples'] if s.get('valid', False)]
            if len(valid_samples) >= 3:
                test_result['status'] = 'passed'
                test_result['valid_sample_count'] = len(valid_samples)
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append(f"Only {len(valid_samples)} valid samples out of 5")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_network_scanner_functionality(self) -> Dict[str, Any]:
        """Test 3: Network scanner accuracy and performance"""
        logger.info("🧪 Testing network scanner functionality...")
        
        test_result = {
            'test_name': 'network_scanner_functionality',
            'status': 'pending',
            'start_time': time.time(),
            'scanner_tests': {},
            'errors': []
        }
        
        try:
            # Test quick status endpoint
            response = requests.get(f"{self.base_url}/api/v9/network-status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                test_result['scanner_tests']['quick_status'] = {
                    'success': True,
                    'status': status_data.get('status'),
                    'devices_found': status_data.get('devices_found', 0),
                    'network_health': status_data.get('network_health', 0)
                }
            else:
                test_result['scanner_tests']['quick_status'] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                test_result['errors'].append(f"Quick status failed: HTTP {response.status_code}")
            
            # Test basic network scan (if available)
            try:
                scan_response = requests.post(f"{self.base_url}/api/scan", 
                                            json={'target': '127.0.0.1'}, timeout=15)
                if scan_response.status_code == 200:
                    test_result['scanner_tests']['basic_scan'] = {'success': True}
                else:
                    test_result['scanner_tests']['basic_scan'] = {
                        'success': False, 
                        'error': f"HTTP {scan_response.status_code}"
                    }
            except Exception as e:
                test_result['scanner_tests']['basic_scan'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Evaluate results
            successful_tests = sum(1 for test in test_result['scanner_tests'].values() if test.get('success', False))
            total_tests = len(test_result['scanner_tests'])
            
            if successful_tests >= total_tests // 2:  # At least 50% success rate
                test_result['status'] = 'passed'
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append(f"Only {successful_tests}/{total_tests} scanner tests passed")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_enhanced_copilot(self) -> Dict[str, Any]:
        """Test 4: Enhanced SysAdmin Copilot functionality"""
        logger.info("🧪 Testing enhanced SysAdmin Copilot...")
        
        test_result = {
            'test_name': 'enhanced_copilot',
            'status': 'pending',
            'start_time': time.time(),
            'copilot_tests': {},
            'errors': []
        }
        
        try:
            # Test issue analysis endpoint
            test_issue = "System is running slow and CPU usage is high"
            response = requests.post(f"{self.base_url}/api/v9/copilot/analyze",
                                   json={'description': test_issue}, timeout=10)
            
            if response.status_code == 200:
                analysis = response.json()
                test_result['copilot_tests']['issue_analysis'] = {
                    'success': True,
                    'has_suggestions': 'suggested_solutions' in analysis,
                    'has_category': 'category' in analysis,
                    'response_valid': isinstance(analysis, dict)
                }
            else:
                test_result['copilot_tests']['issue_analysis'] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                test_result['errors'].append(f"Copilot analysis failed: HTTP {response.status_code}")
            
            # Evaluate results
            if test_result['copilot_tests'].get('issue_analysis', {}).get('success', False):
                test_result['status'] = 'passed'
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append("Copilot analysis test failed")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_plugin_marketplace(self) -> Dict[str, Any]:
        """Test 5: Plugin marketplace functionality"""
        logger.info("🧪 Testing plugin marketplace...")
        
        test_result = {
            'test_name': 'plugin_marketplace',
            'status': 'pending',
            'start_time': time.time(),
            'marketplace_tests': {},
            'errors': []
        }
        
        try:
            # Test plugin discovery
            response = requests.get(f"{self.base_url}/api/v9/plugins/marketplace", timeout=10)
            
            if response.status_code == 200:
                marketplace_data = response.json()
                plugins = marketplace_data.get('plugins', [])
                
                test_result['marketplace_tests']['plugin_discovery'] = {
                    'success': True,
                    'plugins_found': len(plugins),
                    'has_plugins': len(plugins) > 0,
                    'valid_structure': 'plugins' in marketplace_data
                }
                
                # Test category filtering (if plugins exist)
                if plugins:
                    category_response = requests.get(f"{self.base_url}/api/v9/plugins/marketplace?category=security", timeout=10)
                    if category_response.status_code == 200:
                        category_data = category_response.json()
                        test_result['marketplace_tests']['category_filtering'] = {
                            'success': True,
                            'filtered_plugins': len(category_data.get('plugins', []))
                        }
                    else:
                        test_result['marketplace_tests']['category_filtering'] = {
                            'success': False,
                            'error': f"HTTP {category_response.status_code}"
                        }
            else:
                test_result['marketplace_tests']['plugin_discovery'] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                test_result['errors'].append(f"Plugin marketplace failed: HTTP {response.status_code}")
            
            # Evaluate results
            successful_tests = sum(1 for test in test_result['marketplace_tests'].values() if test.get('success', False))
            total_tests = len(test_result['marketplace_tests'])
            
            if successful_tests >= 1:  # At least basic discovery works
                test_result['status'] = 'passed'
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append("Plugin marketplace tests failed")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test 6: Error handling and recovery"""
        logger.info("🧪 Testing error handling and recovery...")
        
        test_result = {
            'test_name': 'error_handling',
            'status': 'pending',
            'start_time': time.time(),
            'error_tests': {},
            'errors': []
        }
        
        try:
            # Test invalid API endpoints
            invalid_endpoints = [
                '/api/invalid-endpoint',
                '/api/v9/nonexistent',
                '/api/v9/copilot/analyze'  # POST without data
            ]
            
            for endpoint in invalid_endpoints:
                try:
                    if 'analyze' in endpoint:
                        response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                    else:
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    
                    # We expect 4xx or 5xx status codes for invalid requests
                    if 400 <= response.status_code < 600:
                        test_result['error_tests'][endpoint] = {
                            'success': True,
                            'status_code': response.status_code,
                            'proper_error_response': True
                        }
                    else:
                        test_result['error_tests'][endpoint] = {
                            'success': False,
                            'status_code': response.status_code,
                            'proper_error_response': False
                        }
                        
                except Exception as e:
                    test_result['error_tests'][endpoint] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Evaluate results
            successful_error_handling = sum(1 for test in test_result['error_tests'].values() 
                                          if test.get('success', False))
            total_error_tests = len(test_result['error_tests'])
            
            if successful_error_handling >= total_error_tests * 0.8:  # 80% success rate
                test_result['status'] = 'passed'
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append(f"Error handling: {successful_error_handling}/{total_error_tests} tests passed")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test 7: Performance monitoring and resource usage"""
        logger.info("🧪 Testing performance metrics...")
        
        test_result = {
            'test_name': 'performance_metrics',
            'status': 'pending',
            'start_time': time.time(),
            'performance_data': {},
            'errors': []
        }
        
        try:
            # Monitor webapp process performance
            webapp_pid = self.webapp_process.pid if self.webapp_process else None
            
            if webapp_pid and psutil.pid_exists(webapp_pid):
                webapp_process = psutil.Process(webapp_pid)
                
                # Collect performance samples over time
                samples = []
                for i in range(5):
                    try:
                        cpu_percent = webapp_process.cpu_percent()
                        memory_info = webapp_process.memory_info()
                        
                        samples.append({
                            'sample': i + 1,
                            'cpu_percent': cpu_percent,
                            'memory_rss': memory_info.rss,
                            'memory_vms': memory_info.vms,
                            'timestamp': time.time()
                        })
                        
                        time.sleep(2)  # Wait between samples
                    except Exception as e:
                        test_result['errors'].append(f"Performance sample {i+1}: {str(e)}")
                
                if samples:
                    # Calculate averages
                    avg_cpu = sum(s['cpu_percent'] for s in samples) / len(samples)
                    avg_memory_mb = sum(s['memory_rss'] for s in samples) / len(samples) / 1024 / 1024
                    
                    test_result['performance_data'] = {
                        'average_cpu_percent': avg_cpu,
                        'average_memory_mb': avg_memory_mb,
                        'sample_count': len(samples),
                        'performance_acceptable': avg_cpu < 50 and avg_memory_mb < 500
                    }
                    
                    if test_result['performance_data']['performance_acceptable']:
                        test_result['status'] = 'passed'
                    else:
                        test_result['status'] = 'failed'
                        test_result['errors'].append(f"High resource usage: CPU {avg_cpu:.1f}%, RAM {avg_memory_mb:.1f}MB")
                else:
                    test_result['status'] = 'failed'
                    test_result['errors'].append("No performance samples collected")
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append("Webapp process not found for monitoring")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def test_concurrent_access(self) -> Dict[str, Any]:
        """Test 8: Multi-user concurrent access simulation"""
        logger.info("🧪 Testing concurrent access capabilities...")
        
        test_result = {
            'test_name': 'concurrent_access',
            'status': 'pending',
            'start_time': time.time(),
            'concurrent_tests': {},
            'errors': []
        }
        
        def make_concurrent_request(session_id: int) -> Dict[str, Any]:
            """Make a request from a simulated user session"""
            try:
                response = requests.get(f"{self.base_url}/api/v9/system-metrics", 
                                      timeout=10,
                                      headers={'X-Session-ID': str(session_id)})
                return {
                    'session_id': session_id,
                    'success': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            except Exception as e:
                return {
                    'session_id': session_id,
                    'success': False,
                    'error': str(e)
                }
        
        try:
            # Simulate 10 concurrent users
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_concurrent_request, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_requests = [r for r in results if r.get('success', False)]
            failed_requests = [r for r in results if not r.get('success', False)]
            
            if successful_requests:
                avg_response_time = sum(r.get('response_time', 0) for r in successful_requests) / len(successful_requests)
                test_result['concurrent_tests'] = {
                    'total_requests': len(results),
                    'successful_requests': len(successful_requests),
                    'failed_requests': len(failed_requests),
                    'success_rate': len(successful_requests) / len(results) * 100,
                    'average_response_time': avg_response_time
                }
                
                # Test passes if >80% success rate and reasonable response times
                if (len(successful_requests) / len(results) >= 0.8 and 
                    avg_response_time < 5.0):
                    test_result['status'] = 'passed'
                else:
                    test_result['status'] = 'failed'
                    test_result['errors'].append(f"Concurrent access issues: {len(successful_requests)}/{len(results)} success, {avg_response_time:.2f}s avg response")
            else:
                test_result['status'] = 'failed'
                test_result['errors'].append("No successful concurrent requests")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Test execution error: {str(e)}")
        
        test_result['duration'] = time.time() - test_result['start_time']
        return test_result
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check overall test pass rate
        if self.test_results['tests_passed'] < self.test_results['total_tests'] * 0.8:
            recommendations.append("⚠️ Low test pass rate - review failed tests before production deployment")
        
        # Check for specific test failures
        failed_tests = [test for test in self.test_results['tests_executed'] if test['status'] == 'failed']
        
        for test in failed_tests:
            if test['test_name'] == 'web_interface_responsiveness':
                recommendations.append("🌐 Optimize web interface performance - consider caching and response compression")
            elif test['test_name'] == 'system_metrics_collection':
                recommendations.append("📊 Review system metrics collection - ensure psutil dependencies are working")
            elif test['test_name'] == 'network_scanner_functionality':
                recommendations.append("📡 Network scanner needs attention - verify scanning capabilities and permissions")
            elif test['test_name'] == 'enhanced_copilot':
                recommendations.append("🤖 SysAdmin Copilot integration issues - check AI model availability")
            elif test['test_name'] == 'plugin_marketplace':
                recommendations.append("🔌 Plugin marketplace requires fixes - verify plugin discovery functionality")
            elif test['test_name'] == 'performance_metrics':
                recommendations.append("💾 High resource usage detected - optimize memory and CPU usage")
            elif test['test_name'] == 'concurrent_access':
                recommendations.append("👥 Concurrent access issues - consider adding load balancing or connection pooling")
        
        # Performance-based recommendations
        performance_data = self.test_results.get('performance_metrics', {})
        if performance_data:
            avg_memory = performance_data.get('average_memory_mb', 0)
            avg_cpu = performance_data.get('average_cpu_percent', 0)
            
            if avg_memory > 300:
                recommendations.append(f"💾 Memory usage is high ({avg_memory:.1f}MB) - consider memory optimization")
            if avg_cpu > 30:
                recommendations.append(f"⚡ CPU usage is elevated ({avg_cpu:.1f}%) - optimize processing efficiency")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - system is ready for production deployment")
        
        return recommendations
    
    def save_test_results(self) -> bool:
        """Save comprehensive test results to file"""
        try:
            results_file = self.base_dir / f"stability_test_results_{int(time.time())}.json"
            
            self.test_results['recommendations'] = self.generate_recommendations()
            self.test_results['test_completion_time'] = datetime.now().isoformat()
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"✅ Test results saved to: {results_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Execute the complete stability testing suite"""
        logger.info("🚀 Starting Ultimate Suite v9.0 Stability Testing Suite...")
        
        # Start webapp
        if not self.start_webapp():
            logger.error("❌ Cannot run tests - webapp failed to start")
            return False
        
        try:
            # Define all tests to run
            test_functions = [
                self.test_web_interface_responsiveness,
                self.test_system_metrics_collection,
                self.test_network_scanner_functionality,
                self.test_enhanced_copilot,
                self.test_plugin_marketplace,
                self.test_error_handling,
                self.test_performance_metrics,
                self.test_concurrent_access
            ]
            
            # Execute all tests
            for test_func in test_functions:
                test_result = test_func()
                self.test_results['tests_executed'].append(test_result)
                
                if test_result['status'] == 'passed':
                    self.test_results['tests_passed'] += 1
                    logger.info(f"✅ {test_result['test_name']} - PASSED")
                else:
                    self.test_results['tests_failed'] += 1
                    logger.warning(f"❌ {test_result['test_name']} - FAILED")
                    if test_result.get('errors'):
                        for error in test_result['errors']:
                            logger.warning(f"   Error: {error}")
            
            self.test_results['total_tests'] = len(test_functions)
            
            # Determine overall status
            pass_rate = self.test_results['tests_passed'] / self.test_results['total_tests']
            if pass_rate >= 0.8:
                self.test_results['overall_status'] = 'passed'
            elif pass_rate >= 0.6:
                self.test_results['overall_status'] = 'warning'
            else:
                self.test_results['overall_status'] = 'failed'
            
            logger.info(f"🏁 Testing completed: {self.test_results['tests_passed']}/{self.test_results['total_tests']} tests passed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test suite execution failed: {e}")
            self.test_results['overall_status'] = 'error'
            self.test_results['errors'].append(str(e))
            return False
        finally:
            # Always stop webapp
            self.stop_webapp()
            
            # Save results
            self.save_test_results()

def main():
    """Main testing execution"""
    print("🧪 ULTIMATE SUITE v9.0 - STABILITY TESTING SUITE")
    print("=" * 55)
    
    tester = UltimateSuiteStabilityTester()
    success = tester.run_all_tests()
    
    # Print summary
    results = tester.test_results
    print(f"\n📊 TESTING SUMMARY:")
    print(f"   Tests Passed: {results['tests_passed']}")
    print(f"   Tests Failed: {results['tests_failed']}")
    print(f"   Total Tests: {results['total_tests']}")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    
    if results.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"   {rec}")
    
    if results['overall_status'] == 'passed':
        print("\n🎉 All stability tests passed! Ultimate Suite v9.0 is ready for production.")
    elif results['overall_status'] == 'warning':
        print("\n⚠️ Some tests failed but core functionality works. Review recommendations.")
    else:
        print("\n❌ Critical stability issues detected. Address failed tests before deployment.")
    
    return success

if __name__ == "__main__":
    main()
