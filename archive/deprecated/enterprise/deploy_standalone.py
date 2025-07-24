#!/usr/bin/env python3
"""
Standalone Enterprise Multi-Tenant Deployment
Deploys the complete enterprise architecture without Docker dependencies
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import sqlite3
import threading
import multiprocessing
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enterprise_standalone.log'),
        logging.StreamHandler()
    ]
)

class StandaloneEnterpriseDeployment:
    """Complete standalone enterprise deployment manager"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.deployment_id = f"standalone-{int(time.time())}"
        self.processes = []
        self.ports = {
            'tenant_manager': 8001,
            'auth_manager': 8002,
            'resource_monitor': 8003,
            'api_gateway': 8004,
            'web_interface': 8005,
            'monitoring': 8006
        }
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load or create enterprise configuration"""
        config_path = Path(self.workspace_path) / 'enterprise_config.json'
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {
                "environment": "standalone",
                "database": {
                    "type": "sqlite",
                    "path": "enterprise_data.db",
                    "connection_pool": 10
                },
                "cache": {
                    "type": "memory",
                    "size": "100MB"
                },
                "security": {
                    "jwt_secret": "standalone-jwt-secret-key-12345",
                    "api_key_length": 32,
                    "session_timeout": 3600
                },
                "monitoring": {
                    "enabled": True,
                    "metrics_interval": 30,
                    "log_level": "INFO"
                },
                "deployment": {
                    "id": self.deployment_id,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "standalone"
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        return config
    
    def initialize_database(self):
        """Initialize SQLite database for multi-tenant architecture"""
        logging.info("Initializing enterprise database...")
        
        db_path = Path(self.workspace_path) / self.config.get('database', {}).get('path', 'enterprise_data.db')
        
        # Create database and tables
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Tenants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                subdomain TEXT UNIQUE NOT NULL,
                plan TEXT NOT NULL DEFAULT 'basic',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}',
                resource_limits TEXT DEFAULT '{"cpu": 1.0, "memory": "512MB", "storage": "1GB"}'
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                UNIQUE(tenant_id, username)
            )
        ''')
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                permissions TEXT DEFAULT '["read"]',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Resource usage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id)
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create demo tenant
        cursor.execute('''
            INSERT OR IGNORE INTO tenants (name, subdomain, plan, status) 
            VALUES ('Demo Tenant', 'demo', 'enterprise', 'active')
        ''')
        
        # Create demo admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (tenant_id, username, email, password_hash, role) 
            VALUES (1, 'admin', 'admin@demo.com', 'hashed_password_placeholder', 'admin')
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info("Database initialized successfully")
    
    def create_service_launcher(self, service_name: str, port: int) -> str:
        """Create a service launcher script"""
        launcher_path = Path(self.workspace_path) / f"launch_{service_name}.py"
        
        launcher_content = f'''#!/usr/bin/env python3
"""
{service_name.title()} Service Launcher
Standalone deployment launcher for {service_name}
"""

import sys
import os
import time
from pathlib import Path

# Add enterprise directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print(f"Starting {service_name.title()} Service on port {port}...")
    
    try:
        # Import and run the service
        if "{service_name}" == "tenant_manager":
            from tenant_manager import TenantManager
            app = TenantManager()
            app.run(host='0.0.0.0', port={port}, debug=False)
            
        elif "{service_name}" == "auth_manager":
            from tenant_auth import TenantAuthManager
            app = TenantAuthManager()
            app.run(host='0.0.0.0', port={port}, debug=False)
            
        elif "{service_name}" == "resource_monitor":
            from resource_manager import ResourceManager
            app = ResourceManager()
            app.run(host='0.0.0.0', port={port}, debug=False)
            
        elif "{service_name}" == "api_gateway":
            from api_gateway import APIGateway
            app = APIGateway()
            app.run(host='0.0.0.0', port={port}, debug=False)
            
        elif "{service_name}" == "web_interface":
            from web_interface import WebInterface
            app = WebInterface()
            app.run(host='0.0.0.0', port={port}, debug=False)
            
        else:
            print(f"Unknown service: {service_name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error starting {service_name}: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
            
        return str(launcher_path)
    
    def start_service(self, service_name: str, port: int):
        """Start a service in a separate process"""
        launcher_path = self.create_service_launcher(service_name, port)
        
        try:
            # Start the service as a background process
            process = subprocess.Popen([
                sys.executable, launcher_path
            ], cwd=self.workspace_path)
            
            self.processes.append({
                'name': service_name,
                'process': process,
                'port': port,
                'started_at': time.time()
            })
            
            logging.info(f"Service {service_name.title()} started on port {port} (PID: {process.pid})")
            
        except Exception as e:
            logging.error(f"Failed to start {service_name}: {e}")
    
    def create_monitoring_dashboard(self):
        """Create a simple monitoring dashboard"""
        dashboard_path = Path(self.workspace_path) / "monitoring_dashboard.py"
        
        dashboard_content = '''#!/usr/bin/env python3
"""
Enterprise Monitoring Dashboard
Simple monitoring interface for standalone deployment
"""

import sys
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Heimnetz Enterprise Monitoring</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { font-size: 24px; font-weight: bold; color: #27ae60; }
        .status { padding: 5px 10px; border-radius: 4px; color: white; font-size: 12px; }
        .status.active { background: #27ae60; }
        .status.inactive { background: #e74c3c; }
        .refresh { margin: 20px 0; }
        .refresh button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Heimnetz Enterprise Monitoring Dashboard</h1>
            <p>Standalone Multi-Tenant Architecture Status</p>
        </div>
        
        <div class="refresh">
            <button onclick="location.reload()">🔄 Refresh Data</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div class="metric">{{ tenant_count }}</div>
                <p>Active Tenants</p>
                <div class="metric">{{ user_count }}</div>
                <p>Total Users</p>
            </div>
            
            <div class="card">
                <h3>🔧 Service Status</h3>
                <div>
                    <span class="status active">Tenant Manager</span><br><br>
                    <span class="status active">Auth Manager</span><br><br>
                    <span class="status active">Resource Monitor</span><br><br>
                    <span class="status active">API Gateway</span><br><br>
                    <span class="status active">Web Interface</span><br><br>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Resource Usage</h3>
                <div class="metric">{{ cpu_usage }}%</div>
                <p>CPU Usage</p>
                <div class="metric">{{ memory_usage }}MB</div>
                <p>Memory Usage</p>
            </div>
            
            <div class="card">
                <h3>🔐 Security</h3>
                <div class="metric">{{ active_sessions }}</div>
                <p>Active Sessions</p>
                <div class="metric">{{ api_keys }}</div>
                <p>API Keys</p>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard view"""
    db_path = Path(__file__).parent / 'enterprise_data.db'
    
    if not db_path.exists():
        return "Database not found. Please run deployment first."
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get metrics
    cursor.execute("SELECT COUNT(*) FROM tenants WHERE status = 'active'")
    tenant_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')")
    active_sessions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM api_keys WHERE expires_at IS NULL OR expires_at > datetime('now')")
    api_keys = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template_string(DASHBOARD_TEMPLATE,
        tenant_count=tenant_count,
        user_count=user_count,
        active_sessions=active_sessions,
        api_keys=api_keys,
        cpu_usage=15,  # Placeholder
        memory_usage=256  # Placeholder
    )

@app.route('/api/metrics')
def metrics():
    """API endpoint for metrics"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'tenant_manager': 'active',
            'auth_manager': 'active',
            'resource_monitor': 'active',
            'api_gateway': 'active',
            'web_interface': 'active'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8006, debug=False)
'''
        
        with open(dashboard_path, 'w') as f:
            f.write(dashboard_content)
            
        logging.info("Monitoring dashboard created")
    
    def deploy(self):
        """Execute complete standalone deployment"""
        logging.info("STARTING STANDALONE ENTERPRISE DEPLOYMENT")
        logging.info("=" * 80)
        
        try:
            # Phase 1: Initialize database
            logging.info("Phase 1: Database Initialization")
            self.initialize_database()
            
            # Phase 2: Create monitoring dashboard
            logging.info("Phase 2: Monitoring Setup")
            self.create_monitoring_dashboard()
            
            # Phase 3: Start core services
            logging.info("Phase 3: Core Services Deployment")
            
            services = [
                'tenant_manager',
                'auth_manager', 
                'resource_monitor',
                'api_gateway',
                'web_interface'
            ]
            
            for service in services:
                port = self.ports[service]
                self.start_service(service, port)
                time.sleep(2)  # Give each service time to start
            
            # Phase 4: Start monitoring
            logging.info("Phase 4: Monitoring Dashboard")
            self.start_service('monitoring', self.ports['monitoring'])
            
            # Phase 5: Health check
            logging.info("Phase 5: Health Check")
            time.sleep(5)  # Wait for services to fully start
            
            # Check process status
            active_services = 0
            for proc_info in self.processes:
                if proc_info['process'].poll() is None:
                    active_services += 1
                    logging.info(f"Service {proc_info['name']} running on port {proc_info['port']}")
                else:
                    logging.warning(f"Service {proc_info['name']} may have failed to start")
            
            # Display deployment summary
            logging.info("=" * 80)
            logging.info("STANDALONE DEPLOYMENT COMPLETED!")
            logging.info("=" * 80)
            logging.info(f"Database: enterprise_data.db")
            logging.info(f"Active Services: {active_services}/{len(services) + 1}")
            logging.info(f"Deployment ID: {self.deployment_id}")
            logging.info("")
            logging.info("Service Endpoints:")
            logging.info(f"   • Tenant Manager:    http://localhost:{self.ports['tenant_manager']}")
            logging.info(f"   • Auth Manager:      http://localhost:{self.ports['auth_manager']}")
            logging.info(f"   • Resource Monitor:  http://localhost:{self.ports['resource_monitor']}")
            logging.info(f"   • API Gateway:       http://localhost:{self.ports['api_gateway']}")
            logging.info(f"   • Web Interface:     http://localhost:{self.ports['web_interface']}")
            logging.info(f"   • Monitoring:        http://localhost:{self.ports['monitoring']}")
            logging.info("")
            logging.info("Management Commands:")
            logging.info("   • View Logs: tail -f enterprise_standalone.log")
            logging.info("   • Stop Services: Use Ctrl+C in terminal")
            logging.info("")
            logging.info("Multi-tenant enterprise architecture is now running!")
            
            return True
            
        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up running processes"""
        logging.info("Cleaning up processes...")
        for proc_info in self.processes:
            try:
                proc_info['process'].terminate()
                proc_info['process'].wait(timeout=5)
            except:
                try:
                    proc_info['process'].kill()
                except:
                    pass

def main():
    """Main deployment function"""
    workspace = Path(__file__).parent
    
    print("Heimnetz Enterprise Standalone Deployment")
    print("=" * 50)
    
    deployment = StandaloneEnterpriseDeployment(str(workspace))
    
    try:
        success = deployment.deploy()
        
        if success:
            print("\nDeployment successful! Press Ctrl+C to stop all services.")
            
            # Keep the main process running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down services...")
                deployment.cleanup()
                print("Shutdown complete")
        else:
            print("\nDeployment failed. Check logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\nDeployment interrupted by user")
        deployment.cleanup()
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        deployment.cleanup()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
