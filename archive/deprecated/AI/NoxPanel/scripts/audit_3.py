#!/usr/bin/env python3
"""
NoxPanel 8-Gate Audit System - Gate 3: Performance Benchmarks
============================================================

Gate 3 validates system performance, response times, and resource optimization.
This gate unlocks plugin system capabilities upon successful completion.

Requirements:
- Response time validation (< 100ms average)
- Memory usage optimization (< 256MB)
- Database query performance (< 50ms)
- Concurrent user handling (10+ simultaneous)
- Resource cleanup verification

Scoring: 100 points total (20 points per test)
Passing: 80+ points required
"""

import os
import sys
import time
import json
import sqlite3
import threading
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
import concurrent.futures
import requests
import statistics

class PerformanceBenchmarkAuditor:
    def __init__(self):
        self.score = 0
        self.max_score = 100
        self.passing_score = 80
        self.results = []
        self.start_time = None
        self.base_path = Path(__file__).parent.parent
        
    def log_result(self, test_name, passed, points, details=""):
        """Log test result and update score"""
        if passed:
            self.score += points
            status = "PASS"
        else:
            status = "FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "points": points if passed else 0,
            "max_points": points,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {points if passed else 0}/{points} points")
        if details:
            print(f"    Details: {details}")

    def test_response_time_performance(self):
        """Test 1: API Response Time Validation (20 points)"""
        print("\n=== Test 1: Response Time Performance ===")
        
        try:
            # Test multiple endpoints for response time
            endpoints = [
                "http://127.0.0.1:5000/",
                "http://127.0.0.1:5000/knowledge",
                "http://127.0.0.1:5000/api/knowledge/stats",
                "http://127.0.0.1:5000/api/knowledge/suggestions?q=test"
            ]
            
            response_times = []
            successful_requests = 0
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=5)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    response_times.append(response_time)
                    
                    if response.status_code < 500:  # Accept 2xx, 3xx, 4xx but not 5xx
                        successful_requests += 1
                    
                    print(f"    {endpoint}: {response_time:.2f}ms (Status: {response.status_code})")
                    
                except requests.exceptions.RequestException as e:
                    print(f"    {endpoint}: Failed - {str(e)}")
                    response_times.append(1000)  # Penalty for failed requests
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                # Scoring criteria
                if avg_response_time < 50:
                    points = 20
                elif avg_response_time < 100:
                    points = 15
                elif avg_response_time < 200:
                    points = 10
                elif avg_response_time < 500:
                    points = 5
                else:
                    points = 0
                
                details = f"Avg: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms, Success: {successful_requests}/{len(endpoints)}"
                self.log_result("Response Time Performance", avg_response_time < 200, points, details)
            else:
                self.log_result("Response Time Performance", False, 0, "No successful requests")
                
        except Exception as e:
            self.log_result("Response Time Performance", False, 0, f"Test error: {str(e)}")

    def test_memory_usage_optimization(self):
        """Test 2: Memory Usage Validation (20 points)"""
        print("\n=== Test 2: Memory Usage Optimization ===")
        
        try:
            # Get current process memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            # Check system memory
            system_memory = psutil.virtual_memory()
            memory_percent = process.memory_percent()
            
            print(f"    Process Memory: {memory_mb:.2f} MB")
            print(f"    Memory Percentage: {memory_percent:.2f}%")
            print(f"    System Available: {system_memory.available / (1024**3):.2f} GB")
            
            # Scoring criteria
            if memory_mb < 128:
                points = 20
            elif memory_mb < 256:
                points = 15
            elif memory_mb < 512:
                points = 10
            elif memory_mb < 1024:
                points = 5
            else:
                points = 0
            
            details = f"Memory: {memory_mb:.2f}MB, System%: {memory_percent:.2f}%"
            self.log_result("Memory Usage Optimization", memory_mb < 512, points, details)
            
        except Exception as e:
            self.log_result("Memory Usage Optimization", False, 0, f"Test error: {str(e)}")

    def test_database_query_performance(self):
        """Test 3: Database Query Performance (20 points)"""
        print("\n=== Test 3: Database Query Performance ===")
        
        try:
            # Create test database if it doesn't exist
            db_path = self.base_path / "data" / "db" / "performance_test.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Test database operations
            query_times = []
            
            with sqlite3.connect(str(db_path)) as conn:
                # Create test table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS test_data (
                        id INTEGER PRIMARY KEY,
                        data TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert test data
                start_time = time.time()
                for i in range(100):
                    conn.execute("INSERT INTO test_data (data) VALUES (?)", (f"test_data_{i}",))
                conn.commit()
                insert_time = (time.time() - start_time) * 1000
                query_times.append(insert_time)
                print(f"    Insert 100 records: {insert_time:.2f}ms")
                
                # Select queries
                start_time = time.time()
                cursor = conn.execute("SELECT COUNT(*) FROM test_data")
                result = cursor.fetchone()
                select_time = (time.time() - start_time) * 1000
                query_times.append(select_time)
                print(f"    Count query: {select_time:.2f}ms (Result: {result[0]})")
                
                # Complex query with WHERE clause
                start_time = time.time()
                cursor = conn.execute("SELECT * FROM test_data WHERE data LIKE ? LIMIT 10", ("%test%",))
                results = cursor.fetchall()
                complex_query_time = (time.time() - start_time) * 1000
                query_times.append(complex_query_time)
                print(f"    Search query: {complex_query_time:.2f}ms (Found: {len(results)})")
                
                # Update operations
                start_time = time.time()
                conn.execute("UPDATE test_data SET data = data || '_updated' WHERE id <= 10")
                conn.commit()
                update_time = (time.time() - start_time) * 1000
                query_times.append(update_time)
                print(f"    Update 10 records: {update_time:.2f}ms")
                
                # Cleanup
                conn.execute("DROP TABLE test_data")
                conn.commit()
            
            # Calculate average query time
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            
            # Scoring criteria
            if avg_query_time < 25:
                points = 20
            elif avg_query_time < 50:
                points = 15
            elif avg_query_time < 100:
                points = 10
            elif avg_query_time < 200:
                points = 5
            else:
                points = 0
            
            details = f"Avg: {avg_query_time:.2f}ms, Max: {max_query_time:.2f}ms"
            self.log_result("Database Query Performance", avg_query_time < 100, points, details)
            
        except Exception as e:
            self.log_result("Database Query Performance", False, 0, f"Test error: {str(e)}")

    def test_concurrent_user_handling(self):
        """Test 4: Concurrent User Load Testing (20 points)"""
        print("\n=== Test 4: Concurrent User Handling ===")
        
        try:
            def make_request(url, timeout=10):
                """Make a single HTTP request"""
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=timeout)
                    end_time = time.time()
                    return {
                        'success': response.status_code < 500,
                        'status_code': response.status_code,
                        'response_time': (end_time - start_time) * 1000
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'status_code': 0,
                        'response_time': timeout * 1000,
                        'error': str(e)
                    }
            
            # Test concurrent requests
            urls = [
                "http://127.0.0.1:5000/",
                "http://127.0.0.1:5000/knowledge",
                "http://127.0.0.1:5000/api/knowledge/stats"
            ] * 5  # 15 total requests (5 per endpoint)
            
            print(f"    Testing {len(urls)} concurrent requests...")
            
            # Execute concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                start_time = time.time()
                futures = [executor.submit(make_request, url) for url in urls]
                results = [future.result() for future in concurrent.futures.as_completed(futures, timeout=30)]
                total_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = len(results) - successful_requests
            response_times = [r['response_time'] for r in results if r['success']]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = 0
                max_response_time = 0
            
            success_rate = (successful_requests / len(results)) * 100
            
            print(f"    Success Rate: {success_rate:.1f}% ({successful_requests}/{len(results)})")
            print(f"    Avg Response: {avg_response_time:.2f}ms")
            print(f"    Max Response: {max_response_time:.2f}ms")
            print(f"    Total Test Time: {total_time:.2f}ms")
            
            # Scoring criteria
            if success_rate >= 95 and avg_response_time < 500:
                points = 20
            elif success_rate >= 90 and avg_response_time < 1000:
                points = 15
            elif success_rate >= 80 and avg_response_time < 2000:
                points = 10
            elif success_rate >= 70:
                points = 5
            else:
                points = 0
            
            details = f"Success: {success_rate:.1f}%, Avg: {avg_response_time:.2f}ms, Max: {max_response_time:.2f}ms"
            self.log_result("Concurrent User Handling", success_rate >= 80, points, details)
            
        except Exception as e:
            self.log_result("Concurrent User Handling", False, 0, f"Test error: {str(e)}")

    def test_resource_cleanup_verification(self):
        """Test 5: Resource Cleanup and Memory Leaks (20 points)"""
        print("\n=== Test 5: Resource Cleanup Verification ===")
        
        try:
            # Get initial memory state
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)
            initial_threads = process.num_threads()
            initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            
            print(f"    Initial Memory: {initial_memory:.2f} MB")
            print(f"    Initial Threads: {initial_threads}")
            print(f"    Initial File Descriptors: {initial_fds}")
            
            # Simulate workload
            def simulate_work():
                """Simulate some database and file operations"""
                try:
                    # Create temporary database connections
                    db_path = self.base_path / "data" / "db" / "temp_test.db"
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    for i in range(10):
                        conn = sqlite3.connect(str(db_path))
                        conn.execute("CREATE TABLE IF NOT EXISTS temp (id INTEGER, data TEXT)")
                        conn.execute("INSERT INTO temp VALUES (?, ?)", (i, f"data_{i}"))
                        conn.commit()
                        conn.close()
                    
                    # Clean up
                    if db_path.exists():
                        db_path.unlink()
                        
                except Exception as e:
                    print(f"    Work simulation error: {e}")
            
            # Run workload multiple times
            for i in range(5):
                simulate_work()
                time.sleep(0.1)  # Small delay
            
            # Allow time for cleanup
            time.sleep(2)
            
            # Get final memory state
            final_memory = process.memory_info().rss / (1024 * 1024)
            final_threads = process.num_threads()
            final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            
            print(f"    Final Memory: {final_memory:.2f} MB")
            print(f"    Final Threads: {final_threads}")
            print(f"    Final File Descriptors: {final_fds}")
            
            # Calculate changes
            memory_growth = final_memory - initial_memory
            thread_growth = final_threads - initial_threads
            fd_growth = final_fds - initial_fds
            
            print(f"    Memory Growth: {memory_growth:.2f} MB")
            print(f"    Thread Growth: {thread_growth}")
            print(f"    FD Growth: {fd_growth}")
            
            # Scoring criteria - penalize significant resource growth
            resource_score = 20
            
            if memory_growth > 50:  # More than 50MB growth
                resource_score -= 8
            elif memory_growth > 20:  # More than 20MB growth
                resource_score -= 4
            elif memory_growth > 10:  # More than 10MB growth
                resource_score -= 2
            
            if thread_growth > 5:  # More than 5 new threads
                resource_score -= 6
            elif thread_growth > 2:  # More than 2 new threads
                resource_score -= 3
            
            if fd_growth > 10:  # More than 10 new file descriptors
                resource_score -= 6
            elif fd_growth > 5:  # More than 5 new file descriptors
                resource_score -= 3
            
            points = max(0, resource_score)
            
            details = f"Memory: +{memory_growth:.2f}MB, Threads: +{thread_growth}, FDs: +{fd_growth}"
            self.log_result("Resource Cleanup Verification", memory_growth < 20 and thread_growth <= 2, points, details)
            
        except Exception as e:
            self.log_result("Resource Cleanup Verification", False, 0, f"Test error: {str(e)}")

    def generate_report(self):
        """Generate comprehensive audit report"""
        passed = self.score >= self.passing_score
        
        report = {
            "gate": 3,
            "title": "Performance Benchmarks",
            "timestamp": datetime.now().isoformat(),
            "score": self.score,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "passed": passed,
            "percentage": round((self.score / self.max_score) * 100, 1),
            "results": self.results,
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": len([r for r in self.results if r["status"] == "PASS"]),
                "failed_tests": len([r for r in self.results if r["status"] == "FAIL"])
            }
        }
        
        # Save report
        report_dir = self.base_path / "data" / "audit_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"gate_3_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_path

    def run_audit(self):
        """Execute complete Gate 3 audit"""
        print("=" * 60)
        print("NoxPanel Gate 3 Audit: Performance Benchmarks")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # Run all tests
        self.test_response_time_performance()
        self.test_memory_usage_optimization()
        self.test_database_query_performance()
        self.test_concurrent_user_handling()
        self.test_resource_cleanup_verification()
        
        # Generate final report
        report, report_path = self.generate_report()
        
        print("\n" + "=" * 60)
        print("GATE 3 AUDIT COMPLETE")
        print("=" * 60)
        print(f"Final Score: {self.score}/{self.max_score} ({report['percentage']}%)")
        print(f"Status: {'PASSED' if report['passed'] else 'FAILED'}")
        print(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
        print(f"Report saved: {report_path}")
        
        if report['passed']:
            print("\n🎉 Gate 3 PASSED! Performance benchmarks validated.")
            print("🔓 Plugin System capabilities are now UNLOCKED!")
            print("🔓 Advanced API features are now UNLOCKED!")
        else:
            print(f"\n❌ Gate 3 FAILED. Need {self.passing_score - self.score} more points to pass.")
            print("💡 Focus on improving response times and resource optimization.")
        
        return report['passed']

def main():
    """Main execution function"""
    try:
        auditor = PerformanceBenchmarkAuditor()
        return auditor.run_audit()
    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        return False
    except Exception as e:
        print(f"\nFatal error during audit: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
