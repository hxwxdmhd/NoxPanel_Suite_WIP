#!/usr/bin/env python3
"""
MariaDB Migration CLI Tool
Command-line interface for migrating NoxPanel database from SQLite to MariaDB
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the NoxPanel directory to path
sys.path.insert(0, str(Path(__file__).parent / "NoxPanel"))

from noxcore.database_service import DatabaseService
from noxcore.mariadb_migration import (
    DatabaseMigrator, DatabaseFactory, MARIADB_AVAILABLE,
    MariaDBDatabase
)

def load_config(config_path: str) -> dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def create_sample_config(output_path: str):
    """Create a sample configuration file"""
    config = {
        "source": {
            "type": "sqlite",
            "path": "data/noxpanel.db"
        },
        "target": {
            "type": "mariadb",
            "host": "localhost",
            "port": 3306,
            "user": "noxpanel",
            "password": "your_password_here",
            "database": "noxpanel",
            "pool_size": 10
        },
        "migration": {
            "batch_size": 1000,
            "validate_after": True,
            "backup_before": True
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Sample configuration created: {output_path}")
    print("Please edit the configuration file with your MariaDB credentials.")

def validate_prerequisites():
    """Validate that all prerequisites are met"""
    issues = []
    
    if not MARIADB_AVAILABLE:
        issues.append("PyMySQL is not installed. Install with: pip install pymysql")
    
    return issues

def test_mariadb_connection(config: dict) -> bool:
    """Test connection to MariaDB"""
    try:
        print("Testing MariaDB connection...")
        
        # Create temporary migrator to test connection
        sqlite_db = DatabaseService(':memory:', auto_migrate=True).db
        migrator = DatabaseMigrator(sqlite_db, config['target'])
        
        result = migrator.validate_mariadb_connection()
        if result:
            print("✓ MariaDB connection successful")
        else:
            print("✗ MariaDB connection failed")
        
        return result
    except Exception as e:
        print(f"✗ MariaDB connection error: {e}")
        return False

def perform_migration(config: dict, dry_run: bool = False) -> dict:
    """Perform the database migration"""
    print(f"{'DRY RUN: ' if dry_run else ''}Starting database migration...")
    print(f"Source: SQLite ({config['source']['path']})")
    print(f"Target: MariaDB ({config['target']['host']}:{config['target']['port']}/{config['target']['database']})")
    
    if dry_run:
        print("DRY RUN MODE: No actual migration will be performed")
        return {
            'dry_run': True,
            'would_migrate': True,
            'estimated_time': '5-10 minutes'
        }
    
    # Initialize source database
    source_db_service = DatabaseService(config['source']['path'], auto_migrate=False)
    
    # Initialize migrator
    migrator = DatabaseMigrator(source_db_service.db, config['target'])
    
    # Test connection
    if not migrator.validate_mariadb_connection():
        raise ConnectionError("Cannot connect to MariaDB")
    
    # Perform migration
    batch_size = config['migration'].get('batch_size', 1000)
    migration_stats = migrator.migrate_data(batch_size)
    
    # Validate if requested
    if config['migration'].get('validate_after', True):
        print("\nValidating migration...")
        validation_results = migrator.validate_migration()
        migration_stats['validation'] = validation_results
        
        if validation_results['validation_passed']:
            print("✓ Migration validation passed")
        else:
            print("✗ Migration validation failed")
    
    source_db_service.close()
    
    return migration_stats

def main():
    parser = argparse.ArgumentParser(
        description='NoxPanel MariaDB Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check                           # Check prerequisites
  %(prog)s sample-config migration.json   # Create sample config
  %(prog)s test-connection migration.json # Test MariaDB connection
  %(prog)s migrate migration.json         # Perform migration
  %(prog)s migrate migration.json --dry-run  # Test migration without changes
        """
    )
    
    parser.add_argument('command', 
                       choices=['check', 'sample-config', 'test-connection', 'migrate'],
                       help='Command to execute')
    
    parser.add_argument('config_file', 
                       nargs='?',
                       help='Configuration file path')
    
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Perform dry run without actual migration')
    
    parser.add_argument('--output', '-o',
                       help='Output file for reports')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'check':
            print("Checking prerequisites for MariaDB migration...")
            
            issues = validate_prerequisites()
            
            if issues:
                print("Issues found:")
                for issue in issues:
                    print(f"  ✗ {issue}")
                sys.exit(1)
            else:
                print("✓ All prerequisites met")
                print("✓ PyMySQL is available")
                print("Ready for MariaDB migration!")
        
        elif args.command == 'sample-config':
            if not args.config_file:
                config_path = 'mariadb_migration_config.json'
            else:
                config_path = args.config_file
            
            create_sample_config(config_path)
        
        elif args.command == 'test-connection':
            if not args.config_file:
                print("Error: Configuration file required")
                sys.exit(1)
            
            if not os.path.exists(args.config_file):
                print(f"Error: Configuration file not found: {args.config_file}")
                sys.exit(1)
            
            config = load_config(args.config_file)
            
            if test_mariadb_connection(config):
                print("Connection test successful! Ready for migration.")
            else:
                print("Connection test failed. Please check your configuration.")
                sys.exit(1)
        
        elif args.command == 'migrate':
            if not args.config_file:
                print("Error: Configuration file required")
                sys.exit(1)
            
            if not os.path.exists(args.config_file):
                print(f"Error: Configuration file not found: {args.config_file}")
                sys.exit(1)
            
            # Check prerequisites
            issues = validate_prerequisites()
            if issues:
                print("Prerequisites not met:")
                for issue in issues:
                    print(f"  ✗ {issue}")
                sys.exit(1)
            
            config = load_config(args.config_file)
            
            # Validate source database exists
            if not os.path.exists(config['source']['path']):
                print(f"Error: Source database not found: {config['source']['path']}")
                sys.exit(1)
            
            # Perform migration
            try:
                start_time = datetime.now()
                migration_stats = perform_migration(config, args.dry_run)
                end_time = datetime.now()
                
                if migration_stats.get('dry_run'):
                    print("\nDry run completed successfully!")
                    print("No changes were made to the database.")
                else:
                    print("\nMigration completed!")
                    
                    # Create report
                    migrator = DatabaseMigrator(None, config['target'])
                    report = migrator.create_migration_report(migration_stats)
                    
                    print("\n" + "="*50)
                    print(report)
                    
                    # Save report if requested
                    if args.output:
                        with open(args.output, 'w') as f:
                            f.write(report)
                            f.write(f"\nFull statistics:\n{json.dumps(migration_stats, indent=2, default=str)}")
                        print(f"\nDetailed report saved to: {args.output}")
                    
                    # Validation summary
                    if 'validation' in migration_stats:
                        validation = migration_stats['validation']
                        if validation['validation_passed']:
                            print("\n✓ Migration validation: PASSED")
                        else:
                            print("\n✗ Migration validation: FAILED")
                            print("Check the detailed report for more information.")
            
            except Exception as e:
                print(f"\nMigration failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()