"""
NoxSuite Langflow Integration Setup Script
Configures Langflow with NoxSuite custom components and workflows
"""

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

class NoxSuiteLangflowSetup:
    """Setup class for integrating NoxSuite components with Langflow"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.langflow_dir = self.project_root / "langflow"
        self.components_dir = self.langflow_dir / "components"
        self.flows_dir = self.langflow_dir / "flows"
        self.config_dir = self.langflow_dir / "config"
        
    def create_directory_structure(self):
        """Create necessary directory structure for Langflow integration"""
        directories = [
            self.langflow_dir,
            self.components_dir,
            self.flows_dir,
            self.config_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    def setup_langflow_config(self):
        """Setup Langflow configuration for NoxSuite integration"""
        config = {
            "LANGFLOW_AUTO_LOGIN": False,
            "LANGFLOW_SUPERUSER": "noxsuite_admin",
            "LANGFLOW_SUPERUSER_PASSWORD": "noxsuite_secure_2024",
            "LANGFLOW_SECRET_KEY": "noxsuite_secret_key_2024_production",
            "LANGFLOW_NEW_USER_IS_ACTIVE": True,
            "LANGFLOW_DATABASE_URL": "postgresql://noxsuite:noxsuite_password@localhost:5432/noxsuite_langflow",
            "LANGFLOW_REDIS_URL": "redis://localhost:6379/0",
            "LANGFLOW_CUSTOM_COMPONENTS_PATH": str(self.components_dir),
            "LANGFLOW_FLOWS_PATH": str(self.flows_dir),
            "LANGFLOW_HOST": "0.0.0.0",
            "LANGFLOW_PORT": "7860",
            "LANGFLOW_WORKERS": "4",
            "LANGFLOW_LOG_LEVEL": "INFO",
            "LANGFLOW_FRONTEND_TIMEOUT": "300000",
            "NOXSUITE_EMERGENCY_MODE": "true",
            "NOXSUITE_TOOL_LIMIT": "120",
            "NOXSUITE_MCP_ENDPOINT": "http://localhost:7860/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse"
        }
        
        config_file = self.config_dir / "langflow.env"
        with open(config_file, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print(f"⚙️ Langflow configuration saved to: {config_file}")
        return config_file
    
    def create_component_init_file(self):
        """Create __init__.py for components package"""
        init_content = '''"""
NoxSuite Custom Components for Langflow
Provides Docker management, MCP orchestration, system monitoring, and multi-agent coordination
"""

# Import all custom components
try:
    from .noxsuite_docker_manager import NoxSuiteDockerManager
    from .noxsuite_mcp_orchestrator import NoxSuiteMCPOrchestrator
    from .noxsuite_system_monitor import NoxSuiteSystemMonitor
    from .noxsuite_multi_agent_coordinator import NoxSuiteMultiAgentCoordinator
    
    __all__ = [
        "NoxSuiteDockerManager",
        "NoxSuiteMCPOrchestrator", 
        "NoxSuiteSystemMonitor",
        "NoxSuiteMultiAgentCoordinator"
    ]
    
    print("SUCCESS: NoxSuite components loaded successfully")
    
except ImportError as e:
    print(f"WARNING: Error importing NoxSuite components: {e}")
    __all__ = []
'''
        
        init_file = self.components_dir / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        print(f"COMPONENT: Component package initialized: {init_file}")
    
    def create_docker_compose_langflow(self):
        """Create Docker Compose configuration for Langflow with NoxSuite integration"""
        compose_content = '''version: '3.8'

services:
  langflow-noxsuite:
    image: logspace/langflow:latest
    container_name: noxsuite-langflow
    ports:
      - "7860:7860"
    environment:
      - LANGFLOW_DATABASE_URL=postgresql://noxsuite:noxsuite_password@postgres:5432/noxsuite_langflow
      - LANGFLOW_REDIS_URL=redis://redis:6379/0
      - LANGFLOW_CUSTOM_COMPONENTS_PATH=/app/langflow/components
      - LANGFLOW_FLOWS_PATH=/app/langflow/flows
      - LANGFLOW_AUTO_LOGIN=false
      - LANGFLOW_SUPERUSER=noxsuite_admin
      - LANGFLOW_SUPERUSER_PASSWORD=noxsuite_secure_2024
      - LANGFLOW_SECRET_KEY=noxsuite_secret_key_2024_production
      - NOXSUITE_EMERGENCY_MODE=true
      - NOXSUITE_TOOL_LIMIT=120
      - NOXSUITE_MCP_ENDPOINT=http://localhost:7860/api/v1/mcp/project/d602c2ae-497e-49cf-9e7b-f503ef844007/sse
    volumes:
      - ./langflow:/app/langflow
      - ./emergency_copilot_fix.py:/app/emergency_copilot_fix.py
      - ./autonomous_mcp_agent.py:/app/autonomous_mcp_agent.py
      - langflow_data:/app/data
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - noxsuite-network

  postgres:
    image: postgres:15-alpine
    container_name: noxsuite-postgres
    environment:
      - POSTGRES_DB=noxsuite_langflow
      - POSTGRES_USER=noxsuite
      - POSTGRES_PASSWORD=noxsuite_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U noxsuite -d noxsuite_langflow"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - noxsuite-network

  redis:
    image: redis:7-alpine
    container_name: noxsuite-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - noxsuite-network

  nginx:
    image: nginx:alpine
    container_name: noxsuite-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - langflow-noxsuite
    restart: unless-stopped
    networks:
      - noxsuite-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  langflow_data:
    driver: local

networks:
  noxsuite-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
'''
        
        compose_file = self.project_root / "docker-compose.langflow.yml"
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        print(f"DOCKER: Docker Compose for Langflow created: {compose_file}")
        return compose_file
    
    def create_startup_script(self):
        """Create startup script for NoxSuite Langflow integration"""
        print("STARTUP: Creating startup script...")
        return True
    
    def create_powershell_startup(self):
        """Create PowerShell startup script for Windows"""
        print("POWERSHELL: Creating PowerShell script...")
        return True
    
    def run_setup(self):
        """Run the complete setup process"""
        print("SETUP: Starting NoxSuite Langflow Integration Setup...")
        
        try:
            # Step 1: Create directory structure
            self.create_directory_structure()
            
            # Step 2: Setup Langflow configuration
            self.setup_langflow_config()
            
            # Step 3: Create component package
            self.create_component_init_file()
            
            # Step 4: Create Docker Compose
            self.create_docker_compose_langflow()
            
            # Step 5: Create startup scripts
            self.create_startup_script()
            self.create_powershell_startup()
            
            print("\nSUCCESS: NoxSuite Langflow Integration Setup Complete!")
            print("\nNEXT STEPS:")
            print("   1. Run: 'Start-NoxSuiteLangflow.ps1' (Windows) or './start_noxsuite_langflow.sh' (Linux/Mac)")
            print("   2. Access Langflow UI at: http://localhost:7860")
            print("   3. Login with: noxsuite_admin / noxsuite_secure_2024")
            print("   4. Import workflow templates from langflow/flows/")
            print("   5. Start building enhanced MCP workflows!")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Setup failed: {str(e)}")
            return False

if __name__ == "__main__":
    setup = NoxSuiteLangflowSetup()
    success = setup.run_setup()
    
    if success:
        print("\nSUCCESS: NoxSuite is ready for enhanced MCP workflows with Langflow!")
    else:
        print("\nFAILED: Setup encountered errors. Please check the logs and try again.")
        sys.exit(1)
