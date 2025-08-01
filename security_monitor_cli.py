#!/usr/bin/env python3
"""
Security Violation Detection CLI Tool
Command-line interface for the NoxPanel Security Monitoring System
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the NoxPanel directory to path
sys.path.insert(0, str(Path(__file__).parent / "NoxPanel"))

from noxcore.database_service import DatabaseService
from noxcore.security_monitor import SecurityViolationDetector, SecurityDashboard

def create_test_data(db_service):
    """Create some test security events for demonstration"""
    print("Creating test security events...")
    
    # Create test users
    user1_id = db_service.users.create_user('testuser1', 'password123', 'user1@example.com', 'user')
    user2_id = db_service.users.create_user('testuser2', 'password456', 'user2@example.com', 'user')
    
    # Simulate brute force attack
    print("  - Simulating brute force attack...")
    for i in range(7):
        db_service.audit.log_action(
            user_id=user1_id,
            action='auth_failed',
            ip_address='192.168.1.100',
            details={'attempt': i, 'reason': 'invalid_password'}
        )
    
    # Simulate data exfiltration
    print("  - Simulating data exfiltration...")
    for i in range(8):
        db_service.audit.log_action(
            user_id=user2_id,
            action='data_export',
            ip_address='10.0.0.50',
            details={'file_size': f'{i*500}MB', 'export_type': 'bulk_download'}
        )
    
    # Simulate privilege escalation
    print("  - Simulating privilege escalation...")
    for i in range(5):
        db_service.audit.log_action(
            user_id=user1_id,
            action='admin_access_attempt',
            ip_address='192.168.1.100',
            details={'resource': 'admin_panel', 'denied': True}
        )
    
    print("Test data created successfully!")

def main():
    parser = argparse.ArgumentParser(
        description='NoxPanel Security Violation Detection Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan                    # Run security scan
  %(prog)s monitor --interval 30   # Start monitoring with 30s intervals
  %(prog)s report --format html    # Generate HTML security report
  %(prog)s demo                    # Create demo data and run scan
        """
    )
    
    parser.add_argument('command', 
                       choices=['scan', 'monitor', 'report', 'demo', 'dashboard'],
                       help='Command to execute')
    
    parser.add_argument('--db-path', '-d',
                       default='data/security_demo.db',
                       help='Database path (default: data/security_demo.db)')
    
    parser.add_argument('--interval', '-i',
                       type=int, default=60,
                       help='Monitoring interval in seconds (default: 60)')
    
    parser.add_argument('--format', '-f',
                       choices=['json', 'html', 'text'],
                       default='text',
                       help='Report format (default: text)')
    
    parser.add_argument('--output', '-o',
                       help='Output file path')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup database
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Initializing NoxPanel Security Monitor...")
    print(f"Database: {db_path}")
    
    try:
        db_service = DatabaseService(str(db_path), auto_migrate=True)
        
        # Configuration for security monitoring
        config = {
            'scan_interval': args.interval,
            'normal_hours': {'start': 9, 'end': 17},
            'data_retention_days': 90
        }
        
        detector = SecurityViolationDetector(db_service, config)
        dashboard = SecurityDashboard(detector)
        
        if args.command == 'demo':
            create_test_data(db_service)
            print("\nRunning security scan on demo data...")
            args.command = 'scan'  # Continue to scan
        
        if args.command == 'scan':
            print("Running security violation scan...")
            detector._run_detection_cycle()
            
            violations = detector.get_recent_violations(24)
            print(f"\nSecurity Scan Results:")
            print(f"==========================================")
            print(f"Total violations found: {len(violations)}")
            
            if violations:
                for violation in violations:
                    print(f"\n[{violation.severity}] {violation.title}")
                    print(f"Category: {violation.category}")
                    print(f"Description: {violation.description}")
                    print(f"Time: {violation.timestamp}")
                    if violation.ip_address:
                        print(f"IP: {violation.ip_address}")
                    print(f"ID: {violation.id}")
                    print("-" * 50)
            else:
                print("No security violations detected.")
            
            # Generate compliance report
            report = detector.get_compliance_report()
            print(f"\nCompliance Status: {report['compliance_status']}")
            print(f"Severity breakdown: {report['severity_breakdown']}")
            
            if report['recommendations']:
                print("\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")
        
        elif args.command == 'monitor':
            print(f"Starting security monitoring (interval: {args.interval}s)")
            print("Press Ctrl+C to stop...")
            
            detector.start_monitoring()
            try:
                while True:
                    time.sleep(1)
                    violations = detector.get_recent_violations(1)  # Last hour
                    if violations and args.verbose:
                        print(f"[{datetime.now()}] New violations: {len(violations)}")
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                detector.stop_monitoring()
        
        elif args.command == 'report':
            print(f"Generating security report...")
            
            if args.format == 'json':
                report = detector.get_compliance_report()
                output = json.dumps(report, indent=2, default=str)
            elif args.format == 'html':
                output = dashboard.generate_html_report()
            else:  # text
                report = detector.get_compliance_report()
                violations = detector.get_recent_violations(24)
                
                output = f"""NoxPanel Security Report
Generated: {datetime.now()}
========================

Compliance Status: {report['compliance_status']}
Total Violations (24h): {report['total_violations_24h']}

Severity Breakdown:
"""
                for severity, count in report['severity_breakdown'].items():
                    output += f"  {severity}: {count}\n"
                
                output += f"\nCategory Breakdown:\n"
                for category, count in report['category_breakdown'].items():
                    output += f"  {category}: {count}\n"
                
                if violations:
                    output += f"\nRecent Violations:\n"
                    output += "=" * 50 + "\n"
                    for violation in violations[-10:]:  # Last 10
                        output += f"\n[{violation.severity}] {violation.title}\n"
                        output += f"Category: {violation.category}\n"
                        output += f"Description: {violation.description}\n"
                        output += f"Time: {violation.timestamp}\n"
                        if violation.ip_address:
                            output += f"IP: {violation.ip_address}\n"
                        output += f"ID: {violation.id}\n"
                        output += "-" * 30 + "\n"
                
                output += f"\nRecommendations:\n"
                for rec in report['recommendations']:
                    output += f"  - {rec}\n"
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Report saved to: {args.output}")
            else:
                print(output)
        
        elif args.command == 'dashboard':
            # Create a simple web dashboard file
            html_content = dashboard.generate_html_report()
            output_file = args.output or 'security_dashboard.html'
            
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            print(f"Security dashboard saved to: {output_file}")
            print(f"Open in browser: file://{Path(output_file).absolute()}")
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        try:
            db_service.close()
        except:
            pass

if __name__ == '__main__':
    main()