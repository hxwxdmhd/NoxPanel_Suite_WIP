#!/usr/bin/env python3
"""
Multi-Tenant Adapter - Workspace Separation and Isolation
=========================================================

POST-GATE-6 OBJECTIVE: Multi-tenant architecture with workspace separation
- Tenant isolation framework
- Resource allocation management
- Cross-tenant security policies
- Tenant-specific configurations
"""

import json
import os
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TenantType(Enum):
    """Tenant type enumeration."""
    ENTERPRISE = "enterprise"
    PROFESSIONAL = "professional"
    STANDARD = "standard"
    DEVELOPER = "developer"

@dataclass
class TenantConfig:
    """Tenant configuration."""
    tenant_id: str
    tenant_name: str
    tenant_type: TenantType
    resource_limits: Dict[str, int]
    security_policies: Dict[str, Any]
    created_date: datetime
    last_active: datetime
    is_active: bool = True

class MultiTenantAdapter:
    """Multi-tenant adapter for workspace separation."""

    def __init__(self, workspace_path: str):
        """Initialize multi-tenant adapter."""
        self.workspace_path = Path(workspace_path)
        self.setup_tenant_infrastructure()

        # Initialize tenant database
        self.tenant_db = self.workspace_path / "multi_tenant" / "tenant_database.db"
        self.init_tenant_database()

        # Load tenant configurations
        self.tenants = {}
        self.load_existing_tenants()

        print("Multi-Tenant Adapter - Workspace Separation")
        print(f"Active Tenants: {len(self.tenants)}")
        print("Tenant Isolation: ENABLED")
        print("Resource Management: OPERATIONAL")

    def setup_tenant_infrastructure(self):
        """Set up multi-tenant infrastructure."""
        directories = [
            self.workspace_path / "multi_tenant",
            self.workspace_path / "multi_tenant" / "tenants",
            self.workspace_path / "multi_tenant" / "shared_resources",
            self.workspace_path / "multi_tenant" / "templates",
            self.workspace_path / "multi_tenant" / "policies",
            self.workspace_path / "multi_tenant" / "logs"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def init_tenant_database(self):
        """Initialize tenant database."""
        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    tenant_name TEXT NOT NULL,
                    tenant_type TEXT NOT NULL,
                    resource_limits TEXT NOT NULL,
                    security_policies TEXT NOT NULL,
                    created_date TIMESTAMP NOT NULL,
                    last_active TIMESTAMP NOT NULL,
                    is_active BOOLEAN NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenant_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_name TEXT NOT NULL,
                    resource_usage INTEGER NOT NULL,
                    resource_limit INTEGER NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenant_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            ''')

            conn.commit()

    def create_tenant(self, tenant_name: str, tenant_type: TenantType,
                     custom_limits: Optional[Dict[str, int]] = None) -> str:
        """Create new tenant with isolation."""
        tenant_id = f"tenant_{hashlib.md5(tenant_name.encode()).hexdigest()[:8]}"

        # Default resource limits based on tenant type
        default_limits = {
            TenantType.ENTERPRISE: {
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 500,
                "concurrent_tasks": 50,
                "api_calls_per_hour": 10000
            },
            TenantType.PROFESSIONAL: {
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 250,
                "concurrent_tasks": 25,
                "api_calls_per_hour": 5000
            },
            TenantType.STANDARD: {
                "cpu_cores": 2,
                "memory_gb": 8,
                "storage_gb": 100,
                "concurrent_tasks": 10,
                "api_calls_per_hour": 1000
            },
            TenantType.DEVELOPER: {
                "cpu_cores": 1,
                "memory_gb": 4,
                "storage_gb": 50,
                "concurrent_tasks": 5,
                "api_calls_per_hour": 500
            }
        }

        resource_limits = custom_limits or default_limits[tenant_type]

        # Create tenant-specific security policies
        security_policies = {
            "isolation_level": "STRICT",
            "data_encryption": True,
            "access_logging": True,
            "resource_monitoring": True,
            "cross_tenant_access": False,
            "mfa_required": tenant_type in [TenantType.ENTERPRISE, TenantType.PROFESSIONAL]
        }

        # Create tenant configuration
        tenant_config = TenantConfig(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tenant_type=tenant_type,
            resource_limits=resource_limits,
            security_policies=security_policies,
            created_date=datetime.now(),
            last_active=datetime.now()
        )

        # Create tenant workspace
        tenant_workspace = self.workspace_path / "multi_tenant" / "tenants" / tenant_id
        tenant_workspace.mkdir(parents=True, exist_ok=True)

        # Create tenant subdirectories
        tenant_subdirs = [
            "data", "logs", "config", "plugins", "temp", "backup"
        ]

        for subdir in tenant_subdirs:
            (tenant_workspace / subdir).mkdir(parents=True, exist_ok=True)

        # Save tenant configuration
        config_file = tenant_workspace / "tenant_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({
                "tenant_id": tenant_config.tenant_id,
                "tenant_name": tenant_config.tenant_name,
                "tenant_type": tenant_config.tenant_type.value,
                "resource_limits": tenant_config.resource_limits,
                "security_policies": tenant_config.security_policies,
                "created_date": tenant_config.created_date.isoformat(),
                "last_active": tenant_config.last_active.isoformat(),
                "is_active": tenant_config.is_active
            }, f, indent=2)

        # Store in database
        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tenants
                (tenant_id, tenant_name, tenant_type, resource_limits, security_policies,
                 created_date, last_active, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id, tenant_name, tenant_type.value,
                json.dumps(resource_limits), json.dumps(security_policies),
                tenant_config.created_date.isoformat(),
                tenant_config.last_active.isoformat(),
                tenant_config.is_active
            ))
            conn.commit()

        # Store in memory
        self.tenants[tenant_id] = tenant_config

        # Log tenant creation
        self.log_tenant_access(tenant_id, "CREATE_TENANT", "tenant_system", True,
                              f"Created tenant: {tenant_name}")

        print(f"Created tenant: {tenant_name} (ID: {tenant_id}, Type: {tenant_type.value})")
        return tenant_id

    def get_tenant_workspace(self, tenant_id: str) -> Optional[Path]:
        """Get tenant workspace path."""
        if tenant_id not in self.tenants:
            return None

        return self.workspace_path / "multi_tenant" / "tenants" / tenant_id

    def validate_tenant_access(self, tenant_id: str, resource: str, action: str) -> bool:
        """Validate tenant access to resource."""
        if tenant_id not in self.tenants:
            self.log_tenant_access(tenant_id, action, resource, False, "Tenant not found")
            return False

        tenant = self.tenants[tenant_id]

        if not tenant.is_active:
            self.log_tenant_access(tenant_id, action, resource, False, "Tenant inactive")
            return False

        # Check security policies
        if not tenant.security_policies.get("cross_tenant_access", False):
            if "tenant_" in resource and tenant_id not in resource:
                self.log_tenant_access(tenant_id, action, resource, False,
                                     "Cross-tenant access denied")
                return False

        self.log_tenant_access(tenant_id, action, resource, True, "Access granted")
        return True

    def check_resource_usage(self, tenant_id: str, resource_type: str,
                           requested_amount: int) -> bool:
        """Check if tenant can use requested resources."""
        if tenant_id not in self.tenants:
            return False

        tenant = self.tenants[tenant_id]
        resource_limit = tenant.resource_limits.get(resource_type, 0)

        # Get current usage from database
        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT resource_usage FROM tenant_resources
                WHERE tenant_id = ? AND resource_type = ?
            ''', (tenant_id, resource_type))

            result = cursor.fetchone()
            current_usage = result[0] if result else 0

        return (current_usage + requested_amount) <= resource_limit

    def allocate_resources(self, tenant_id: str, resource_type: str,
                          resource_name: str, amount: int) -> bool:
        """Allocate resources to tenant."""
        if not self.check_resource_usage(tenant_id, resource_type, amount):
            return False

        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()

            # Check if resource allocation exists
            cursor.execute('''
                SELECT resource_usage FROM tenant_resources
                WHERE tenant_id = ? AND resource_type = ? AND resource_name = ?
            ''', (tenant_id, resource_type, resource_name))

            result = cursor.fetchone()

            if result:
                # Update existing allocation
                new_usage = result[0] + amount
                cursor.execute('''
                    UPDATE tenant_resources
                    SET resource_usage = ?, last_updated = ?
                    WHERE tenant_id = ? AND resource_type = ? AND resource_name = ?
                ''', (new_usage, datetime.now().isoformat(), tenant_id, resource_type, resource_name))
            else:
                # Create new allocation
                tenant = self.tenants[tenant_id]
                resource_limit = tenant.resource_limits.get(resource_type, 0)

                cursor.execute('''
                    INSERT INTO tenant_resources
                    (tenant_id, resource_type, resource_name, resource_usage, resource_limit, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (tenant_id, resource_type, resource_name, amount, resource_limit,
                     datetime.now().isoformat()))

            conn.commit()

        return True

    def load_existing_tenants(self):
        """Load existing tenants from database."""
        if not self.tenant_db.exists():
            return

        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tenant_id, tenant_name, tenant_type, resource_limits, security_policies,
                       created_date, last_active, is_active
                FROM tenants WHERE is_active = 1
            ''')

            for row in cursor.fetchall():
                tenant_id, tenant_name, tenant_type, resource_limits, security_policies, \
                created_date, last_active, is_active = row

                tenant_config = TenantConfig(
                    tenant_id=tenant_id,
                    tenant_name=tenant_name,
                    tenant_type=TenantType(tenant_type),
                    resource_limits=json.loads(resource_limits),
                    security_policies=json.loads(security_policies),
                    created_date=datetime.fromisoformat(created_date),
                    last_active=datetime.fromisoformat(last_active),
                    is_active=bool(is_active)
                )

                self.tenants[tenant_id] = tenant_config

    def log_tenant_access(self, tenant_id: str, action: str, resource: str,
                         success: bool, details: str = ""):
        """Log tenant access."""
        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tenant_access_logs
                (tenant_id, action, resource, timestamp, success, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tenant_id, action, resource, datetime.now().isoformat(), success, details))
            conn.commit()

    def get_tenant_statistics(self) -> Dict[str, Any]:
        """Get tenant statistics."""
        stats = {
            "total_tenants": len(self.tenants),
            "active_tenants": sum(1 for t in self.tenants.values() if t.is_active),
            "tenant_types": {},
            "resource_usage": {},
            "security_events": 0
        }

        # Count tenant types
        for tenant in self.tenants.values():
            tenant_type = tenant.tenant_type.value
            stats["tenant_types"][tenant_type] = stats["tenant_types"].get(tenant_type, 0) + 1

        # Get resource usage from database
        with sqlite3.connect(str(self.tenant_db)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT resource_type, SUM(resource_usage), SUM(resource_limit)
                FROM tenant_resources
                GROUP BY resource_type
            ''')

            for row in cursor.fetchall():
                resource_type, total_usage, total_limit = row
                stats["resource_usage"][resource_type] = {
                    "usage": total_usage,
                    "limit": total_limit,
                    "utilization": (total_usage / total_limit) * 100 if total_limit > 0 else 0
                }

            # Count security events (failed access attempts)
            cursor.execute('''
                SELECT COUNT(*) FROM tenant_access_logs WHERE success = 0
            ''')
            stats["security_events"] = cursor.fetchone()[0]

        return stats

    def generate_tenant_report(self) -> str:
        """Generate multi-tenant system report."""
        stats = self.get_tenant_statistics()

        report_content = f'''# Multi-Tenant System Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## System Overview
- **Total Tenants**: {stats["total_tenants"]}
- **Active Tenants**: {stats["active_tenants"]}
- **Security Events**: {stats["security_events"]}

## Tenant Distribution
'''

        for tenant_type, count in stats["tenant_types"].items():
            report_content += f"- **{tenant_type.title()}**: {count} tenants\n"

        report_content += '''
## Resource Utilization
'''

        for resource_type, usage_data in stats["resource_usage"].items():
            report_content += f'''
### {resource_type.replace("_", " ").title()}
- **Usage**: {usage_data["usage"]} / {usage_data["limit"]}
- **Utilization**: {usage_data["utilization"]:.1f}%
'''

        report_content += '''
## Tenant Details
'''

        for tenant_id, tenant in self.tenants.items():
            report_content += f'''
### {tenant.tenant_name}
- **ID**: {tenant_id}
- **Type**: {tenant.tenant_type.value}
- **Status**: {'Active' if tenant.is_active else 'Inactive'}
- **Created**: {tenant.created_date.strftime("%Y-%m-%d")}
- **Last Active**: {tenant.last_active.strftime("%Y-%m-%d")}
'''

        report_file = self.workspace_path / "multi_tenant" / "tenant_system_report.md"
        report_file.write_text(report_content, encoding='utf-8')

        return str(report_file)

def main():
    """Main multi-tenant adapter execution."""
    try:
        workspace_path = Path.cwd()
        adapter = MultiTenantAdapter(str(workspace_path))

        # Create sample tenants
        enterprise_tenant = adapter.create_tenant("Enterprise Corp", TenantType.ENTERPRISE)
        professional_tenant = adapter.create_tenant("Professional Team", TenantType.PROFESSIONAL)
        standard_tenant = adapter.create_tenant("Standard User", TenantType.STANDARD)

        # Test resource allocation
        adapter.allocate_resources(enterprise_tenant, "cpu_cores", "main_process", 4)
        adapter.allocate_resources(professional_tenant, "memory_gb", "cache", 8)

        # Test access validation
        print(f"Enterprise access to own resources: {adapter.validate_tenant_access(enterprise_tenant, f'tenant_{enterprise_tenant}/data', 'READ')}")
        print(f"Professional access to enterprise resources: {adapter.validate_tenant_access(professional_tenant, f'tenant_{enterprise_tenant}/data', 'READ')}")

        # Generate report
        report_file = adapter.generate_tenant_report()
        stats = adapter.get_tenant_statistics()

        print("\n" + "="*80)
        print("MULTI-TENANT SYSTEM RESULTS")
        print("="*80)
        print(f"Total Tenants: {stats['total_tenants']}")
        print(f"Active Tenants: {stats['active_tenants']}")
        print(f"Security Events: {stats['security_events']}")
        print(f"System Report: {report_file}")

        print("\nTenant Distribution:")
        for tenant_type, count in stats["tenant_types"].items():
            print(f"  {tenant_type.title()}: {count}")

        print("\n" + "="*80)
        print("MULTI-TENANT ADAPTER OPERATIONAL")
        print("Workspace Separation: ENABLED")
        print("="*80)

    except Exception as e:
        print(f"Multi-tenant adapter error: {str(e)}")

if __name__ == "__main__":
    main()
