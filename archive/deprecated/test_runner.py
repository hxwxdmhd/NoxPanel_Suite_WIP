# 🧪 Test Runner Utility - NoxPanel/NoxGuard/Heimnetz Suite
# Command-line interface for Automated Testing Framework
# Quick test execution and reporting

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from automated_testing_framework import AutomatedTestingFramework, TestStatus

class TestRunner:
    """Command-line test execution utility"""
    
    def __init__(self):
        self.framework = AutomatedTestingFramework()
        
    async def list_test_suites(self):
        """List all available test suites"""
        print("🧪 Available Test Suites - NoxPanel/NoxGuard/Heimnetz Suite")
        print("=" * 65)
        
        for suite_id, suite in self.framework.test_suites.items():
            test_count = len(suite.test_cases)
            tags = ", ".join(suite.tags) if suite.tags else "general"
            
            print(f"📋 {suite.name}")
            print(f"   ID: {suite_id}")
            print(f"   Tests: {test_count}")
            print(f"   Tags: {tags}")
            print(f"   Description: {suite.description}")
            print()
    
    async def run_suite(self, suite_id: str):
        """Run a specific test suite"""
        print(f"🚀 Running Test Suite: {suite_id}")
        print("=" * 50)
        
        try:
            report = await self.framework.run_test_suite(suite_id)
            self._display_report_summary(report)
            return report.summary["success_rate_percent"] == 100
        except ValueError as e:
            print(f"❌ Error: {e}")
            return False
    
    async def run_all_suites(self, parallel: bool = False):
        """Run all test suites"""
        print("🔄 Running All Test Suites")
        print("=" * 50)
        
        reports = await self.framework.run_all_tests(parallel_suites=parallel)
        
        # Display summary for each suite
        for suite_id, report in reports.items():
            print(f"\n📊 {report.suite_name}")
            print(f"   Success Rate: {report.summary['success_rate_percent']}%")
            print(f"   Duration: {report.total_duration_seconds:.2f}s")
            print(f"   Tests: {report.summary['passed']}/{report.summary['total']} passed")
        
        # Overall summary
        total_tests = sum(r.summary['total'] for r in reports.values())
        total_passed = sum(r.summary['passed'] for r in reports.values())
        overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Results:")
        print(f"   Suites: {len(reports)}")
        print(f"   Total Tests: {total_tests}")
        print(f"   Success Rate: {overall_success:.1f}%")
        
        return overall_success == 100
    
    async def run_by_tag(self, tag: str):
        """Run test suites matching a specific tag"""
        matching_suites = [
            (suite_id, suite) for suite_id, suite in self.framework.test_suites.items()
            if tag in suite.tags
        ]
        
        if not matching_suites:
            print(f"❌ No test suites found with tag: {tag}")
            return False
        
        print(f"🏷️ Running Test Suites with tag: {tag}")
        print("=" * 50)
        
        all_passed = True
        for suite_id, suite in matching_suites:
            print(f"\n🧪 Running: {suite.name}")
            try:
                report = await self.framework.run_test_suite(suite_id)
                success = report.summary["success_rate_percent"] == 100
                status = "✅" if success else "❌"
                print(f"   {status} {report.summary['success_rate_percent']}% success rate")
                if not success:
                    all_passed = False
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def quick_health_check(self):
        """Run a quick health check with critical tests only"""
        print("⚡ Quick Health Check - Critical Tests Only")
        print("=" * 50)
        
        critical_tests_run = 0
        critical_tests_passed = 0
        
        for suite_id, suite in self.framework.test_suites.items():
            # Get critical test cases
            critical_cases = [tc for tc in suite.test_cases if tc.priority.value == "critical"]
            
            if critical_cases:
                print(f"\n🔍 Checking: {suite.name}")
                
                # Create a temporary suite with only critical tests
                from automated_testing_framework import TestSuite
                critical_suite = TestSuite(
                    id=f"{suite_id}_critical",
                    name=f"{suite.name} (Critical Only)",
                    description=f"Critical tests from {suite.name}",
                    test_cases=critical_cases,
                    tags=["critical", "health_check"]
                )
                
                try:
                    # Run critical tests quickly
                    from automated_testing_framework import TestExecutor, TestEnvironment
                    executor = TestExecutor()
                    
                    async with TestEnvironment(f"health_check_{suite_id}") as env:
                        results = []
                        for test_case in critical_cases:
                            result = await executor.execute_test_case(test_case, env)
                            results.append(result)
                            critical_tests_run += 1
                            if result.status == TestStatus.PASSED:
                                critical_tests_passed += 1
                    
                    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
                    total = len(results)
                    success_rate = (passed / total * 100) if total > 0 else 0
                    
                    status = "✅" if success_rate == 100 else "❌"
                    print(f"   {status} {passed}/{total} critical tests passed ({success_rate:.0f}%)")
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
        
        overall_success = (critical_tests_passed / critical_tests_run * 100) if critical_tests_run > 0 else 0
        
        print(f"\n🎯 Health Check Results:")
        print(f"   Critical Tests: {critical_tests_passed}/{critical_tests_run} passed")
        print(f"   Overall Health: {overall_success:.1f}%")
        
        if overall_success == 100:
            print("   🎉 System health is excellent!")
        elif overall_success >= 80:
            print("   ✅ System health is good")
        elif overall_success >= 60:
            print("   ⚠️ System health needs attention")
        else:
            print("   ❌ System health is critical - investigate immediately")
        
        return overall_success >= 80
    
    def _display_report_summary(self, report):
        """Display a formatted test report summary"""
        summary = report.summary
        
        print(f"📊 Test Results: {report.suite_name}")
        print(f"   Execution ID: {report.execution_id}")
        print(f"   Start Time: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration: {report.total_duration_seconds:.2f}s")
        print()
        
        print(f"   📈 Summary:")
        print(f"     Total Tests: {summary['total']}")
        print(f"     ✅ Passed: {summary['passed']}")
        print(f"     ❌ Failed: {summary['failed']}")
        print(f"     💥 Errors: {summary['error']}")
        print(f"     ⏭️ Skipped: {summary['skipped']}")
        print(f"     ⏰ Timeouts: {summary['timeout']}")
        print(f"     Success Rate: {summary['success_rate_percent']}%")
        print()
        
        # Display failed/error tests for investigation
        failed_tests = [r for r in report.test_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        if failed_tests:
            print("   🔍 Failed/Error Tests:")
            for result in failed_tests:
                print(f"     ❌ {result.test_case.name}: {result.error_message}")
            print()

def main():
    """Command-line interface for test execution"""
    parser = argparse.ArgumentParser(
        description="Automated Testing Framework - NoxPanel/NoxGuard/Heimnetz Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py --list                    # List all test suites
  python test_runner.py --suite plugin_framework_tests  # Run specific suite
  python test_runner.py --all                     # Run all test suites
  python test_runner.py --all --parallel          # Run all suites in parallel
  python test_runner.py --tag security            # Run security tests only
  python test_runner.py --health-check            # Quick health check
        """
    )
    
    parser.add_argument("--list", action="store_true",
                       help="List all available test suites")
    parser.add_argument("--suite", type=str,
                       help="Run a specific test suite by ID")
    parser.add_argument("--all", action="store_true",
                       help="Run all test suites")
    parser.add_argument("--parallel", action="store_true",
                       help="Run test suites in parallel (use with --all)")
    parser.add_argument("--tag", type=str,
                       help="Run test suites with specific tag")
    parser.add_argument("--health-check", action="store_true",
                       help="Run quick health check with critical tests only")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    runner = TestRunner()
    
    async def execute_command():
        success = True
        
        if args.list:
            await runner.list_test_suites()
        
        elif args.suite:
            success = await runner.run_suite(args.suite)
        
        elif args.all:
            success = await runner.run_all_suites(parallel=args.parallel)
        
        elif args.tag:
            success = await runner.run_by_tag(args.tag)
        
        elif args.health_check:
            success = await runner.quick_health_check()
        
        else:
            parser.print_help()
            return
        
        # Set exit code based on test results
        if not success:
            sys.exit(1)
    
    # Run the async command
    try:
        asyncio.run(execute_command())
    except KeyboardInterrupt:
        print("\n❌ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
