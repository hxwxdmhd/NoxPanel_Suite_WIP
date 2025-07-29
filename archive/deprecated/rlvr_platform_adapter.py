#!/usr/bin/env python3
"""
RLVR Platform Adapter - Multi-Environment Support v11.0
=======================================================

Adaptive platform support for:
- Linux environments
- Windows environments
- Cloud deployments (AWS, Azure, GCP)
- Container environments (Docker, Kubernetes)
- CI/CD pipelines

Automatically detects and adapts to the current environment.
"""

import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

class PlatformAdapter:
    """Platform-specific adaptation system."""

    def __init__(self, workspace_path: str):
        """Initialize platform adapter."""
        self.workspace_path = Path(workspace_path)
        self.platform_info = self.detect_platform()
        self.setup_logging()

        print(f"Platform Adapter initialized for: {self.platform_info['platform']}")
        print(f"Environment: {self.platform_info['environment']}")
        print(f"Container: {self.platform_info['container']}")

    def setup_logging(self):
        """Set up platform-specific logging."""
        log_dir = self.workspace_path / "envs" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"platform_adapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('[PLATFORM-ADAPTER]')

    def detect_platform(self) -> Dict[str, Any]:
        """Detect current platform and environment."""
        platform_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "environment": "unknown",
            "container": "none",
            "cloud_provider": "none",
            "ci_cd": "none"
        }

        # Detect environment type
        if os.environ.get('DOCKER_CONTAINER'):
            platform_info["container"] = "docker"
            platform_info["environment"] = "container"
        elif os.environ.get('KUBERNETES_SERVICE_HOST'):
            platform_info["container"] = "kubernetes"
            platform_info["environment"] = "container"
        elif os.environ.get('CI'):
            platform_info["environment"] = "ci"

            # Detect CI/CD provider
            if os.environ.get('GITHUB_ACTIONS'):
                platform_info["ci_cd"] = "github_actions"
            elif os.environ.get('GITLAB_CI'):
                platform_info["ci_cd"] = "gitlab_ci"
            elif os.environ.get('JENKINS_URL'):
                platform_info["ci_cd"] = "jenkins"
        elif os.environ.get('PRODUCTION'):
            platform_info["environment"] = "production"
        else:
            platform_info["environment"] = "development"

        # Detect cloud provider
        if os.environ.get('AWS_REGION'):
            platform_info["cloud_provider"] = "aws"
        elif os.environ.get('AZURE_RESOURCE_GROUP'):
            platform_info["cloud_provider"] = "azure"
        elif os.environ.get('GOOGLE_CLOUD_PROJECT'):
            platform_info["cloud_provider"] = "gcp"

        return platform_info

    def generate_platform_configs(self) -> Dict[str, Any]:
        """Generate platform-specific configurations."""
        configs = {}

        # Linux configuration
        configs["linux"] = self.generate_linux_config()

        # Windows configuration
        configs["windows"] = self.generate_windows_config()

        # Docker configuration
        configs["docker"] = self.generate_docker_config()

        # Kubernetes configuration
        configs["kubernetes"] = self.generate_kubernetes_config()

        # Cloud configurations
        configs["aws"] = self.generate_aws_config()
        configs["azure"] = self.generate_azure_config()
        configs["gcp"] = self.generate_gcp_config()

        return configs

    def generate_linux_config(self) -> Dict[str, Any]:
        """Generate Linux-specific configuration."""
        return {
            "environment": "linux",
            "python_command": "python3",
            "package_manager": "apt" if shutil.which("apt") else "yum" if shutil.which("yum") else "pacman",
            "service_manager": "systemd" if shutil.which("systemctl") else "init",
            "shell": os.environ.get("SHELL", "/bin/bash"),
            "paths": {
                "python": "/usr/bin/python3",
                "pip": "/usr/bin/pip3",
                "home": os.path.expanduser("~"),
                "temp": "/tmp"
            },
            "dependencies": [
                "python3-pip",
                "python3-venv",
                "python3-dev",
                "build-essential"
            ],
            "install_commands": [
                "sudo apt update && sudo apt install -y python3-pip python3-venv python3-dev build-essential",
                "pip3 install -r requirements.txt"
            ]
        }

    def generate_windows_config(self) -> Dict[str, Any]:
        """Generate Windows-specific configuration."""
        return {
            "environment": "windows",
            "python_command": "python",
            "package_manager": "pip",
            "service_manager": "services",
            "shell": "powershell",
            "paths": {
                "python": sys.executable,
                "pip": "pip",
                "home": os.path.expanduser("~"),
                "temp": os.environ.get("TEMP", "C:\\temp")
            },
            "dependencies": [
                "pip",
                "virtualenv"
            ],
            "install_commands": [
                "pip install --upgrade pip",
                "pip install -r requirements.txt"
            ]
        }

    def generate_docker_config(self) -> Dict[str, Any]:
        """Generate Docker configuration."""
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "main.py"]
'''

        docker_compose_content = '''version: '3.8'

services:
  rlvr-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - RLVR_COMPLIANCE_TARGET=98.0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  rlvr-guardian:
    build: .
    command: python rlvr_guardian.py
    environment:
      - ENVIRONMENT=production
      - GUARDIAN_MODE=monitoring
    volumes:
      - ./compliance:/app/compliance
      - ./monitoring:/app/monitoring
    depends_on:
      - rlvr-app
    restart: unless-stopped
'''

        return {
            "environment": "docker",
            "dockerfile": dockerfile_content,
            "docker_compose": docker_compose_content,
            "build_commands": [
                "docker build -t rlvr-app .",
                "docker-compose up -d"
            ]
        }

    def generate_kubernetes_config(self) -> Dict[str, Any]:
        """Generate Kubernetes configuration."""
        k8s_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "rlvr-app",
                "labels": {"app": "rlvr-app"}
            },
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": "rlvr-app"}},
                "template": {
                    "metadata": {"labels": {"app": "rlvr-app"}},
                    "spec": {
                        "containers": [{
                            "name": "rlvr-app",
                            "image": "rlvr-app:latest",
                            "ports": [{"containerPort": 8000}],
                            "env": [
                                {"name": "ENVIRONMENT", "value": "production"},
                                {"name": "RLVR_COMPLIANCE_TARGET", "value": "98.0"}
                            ],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "500m", "memory": "512Mi"}
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/health", "port": 8000},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 8000},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            }
                        }]
                    }
                }
            }
        }

        k8s_service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "rlvr-app-service"},
            "spec": {
                "selector": {"app": "rlvr-app"},
                "ports": [{"port": 80, "targetPort": 8000}],
                "type": "LoadBalancer"
            }
        }

        return {
            "environment": "kubernetes",
            "deployment": k8s_deployment,
            "service": k8s_service,
            "deploy_commands": [
                "kubectl apply -f k8s-deployment.yaml",
                "kubectl apply -f k8s-service.yaml"
            ]
        }

    def generate_aws_config(self) -> Dict[str, Any]:
        """Generate AWS-specific configuration."""
        return {
            "environment": "aws",
            "services": {
                "compute": "EC2",
                "container": "ECS",
                "serverless": "Lambda",
                "database": "RDS",
                "monitoring": "CloudWatch"
            },
            "terraform": {
                "provider": "aws",
                "region": "us-west-2",
                "instance_type": "t3.medium"
            }
        }

    def generate_azure_config(self) -> Dict[str, Any]:
        """Generate Azure-specific configuration."""
        return {
            "environment": "azure",
            "services": {
                "compute": "Virtual Machines",
                "container": "Container Instances",
                "serverless": "Functions",
                "database": "SQL Database",
                "monitoring": "Monitor"
            }
        }

    def generate_gcp_config(self) -> Dict[str, Any]:
        """Generate GCP-specific configuration."""
        return {
            "environment": "gcp",
            "services": {
                "compute": "Compute Engine",
                "container": "Cloud Run",
                "serverless": "Cloud Functions",
                "database": "Cloud SQL",
                "monitoring": "Cloud Monitoring"
            }
        }

    def adapt_to_current_platform(self) -> Dict[str, Any]:
        """Adapt configuration to current platform."""
        print(f"Adapting to {self.platform_info['platform']} platform...")

        configs = self.generate_platform_configs()
        current_platform = self.platform_info['platform'].lower()

        # Select appropriate configuration
        if current_platform == "linux":
            active_config = configs["linux"]
        elif current_platform == "windows":
            active_config = configs["windows"]
        else:
            active_config = configs["linux"]  # Default to Linux

        # Apply container-specific adaptations
        if self.platform_info['container'] == "docker":
            active_config.update(configs["docker"])
        elif self.platform_info['container'] == "kubernetes":
            active_config.update(configs["kubernetes"])

        # Apply cloud-specific adaptations
        cloud_provider = self.platform_info['cloud_provider']
        if cloud_provider in configs:
            active_config.update(configs[cloud_provider])

        # Save platform-specific configuration
        config_file = self.workspace_path / "envs" / f"{current_platform}_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(active_config, f, indent=2)

        # Generate platform-specific scripts
        self.generate_platform_scripts(active_config)

        adaptation_result = {
            "platform": self.platform_info['platform'],
            "environment": self.platform_info['environment'],
            "container": self.platform_info['container'],
            "cloud_provider": self.platform_info['cloud_provider'],
            "config_file": str(config_file),
            "adaptations_applied": list(active_config.keys()),
            "status": "success"
        }

        print(f"Platform adaptation completed: {adaptation_result['status']}")
        return adaptation_result

    def generate_platform_scripts(self, config: Dict[str, Any]):
        """Generate platform-specific deployment scripts."""
        scripts_dir = self.workspace_path / "envs" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Generate installation script
        if config.get("environment") == "linux":
            install_script = "#!/bin/bash\n"
            install_script += "echo 'Installing RLVR on Linux...'\n"
            for cmd in config.get("install_commands", []):
                install_script += f"{cmd}\n"
            install_script += "echo 'Installation completed successfully!'\n"

            script_file = scripts_dir / "install_linux.sh"
            script_file.write_text(install_script, encoding='utf-8')
            os.chmod(script_file, 0o755)

        elif config.get("environment") == "windows":
            install_script = "# Installing RLVR on Windows\n"
            install_script += "Write-Host 'Installing RLVR on Windows...'\n"
            for cmd in config.get("install_commands", []):
                install_script += f"{cmd}\n"
            install_script += "Write-Host 'Installation completed successfully!'\n"

            script_file = scripts_dir / "install_windows.ps1"
            script_file.write_text(install_script, encoding='utf-8')

        # Generate Docker files if needed
        if "dockerfile" in config:
            dockerfile = self.workspace_path / "envs" / "Dockerfile"
            dockerfile.write_text(config["dockerfile"], encoding='utf-8')

        if "docker_compose" in config:
            compose_file = self.workspace_path / "envs" / "docker-compose.yml"
            compose_file.write_text(config["docker_compose"], encoding='utf-8')

        # Generate Kubernetes files if needed
        if "deployment" in config:
            k8s_deployment = self.workspace_path / "envs" / "k8s-deployment.yaml"
            with open(k8s_deployment, 'w', encoding='utf-8') as f:
                import yaml
                yaml.dump(config["deployment"], f, default_flow_style=False)

        if "service" in config:
            k8s_service = self.workspace_path / "envs" / "k8s-service.yaml"
            with open(k8s_service, 'w', encoding='utf-8') as f:
                import yaml
                yaml.dump(config["service"], f, default_flow_style=False)

def main():
    """Main execution function."""
    try:
        workspace_path = Path.cwd()
        adapter = PlatformAdapter(str(workspace_path))

        # Generate all platform configurations
        configs = adapter.generate_platform_configs()

        # Adapt to current platform
        adaptation_result = adapter.adapt_to_current_platform()

        print("\n" + "="*60)
        print("PLATFORM ADAPTER COMPLETED")
        print("="*60)
        print(f"Platform: {adaptation_result['platform']}")
        print(f"Environment: {adaptation_result['environment']}")
        print(f"Container: {adaptation_result['container']}")
        print(f"Cloud Provider: {adaptation_result['cloud_provider']}")
        print(f"Config File: {adaptation_result['config_file']}")
        print(f"Adaptations: {len(adaptation_result['adaptations_applied'])}")
        print(f"Status: {adaptation_result['status']}")
        print("="*60)

        # Display available configurations
        print("\nAvailable Platform Configurations:")
        for platform, config in configs.items():
            print(f"  {platform}: {config.get('environment', 'N/A')}")

        print("\nPlatform adaptation completed successfully!")

    except Exception as e:
        print(f"Platform adapter error: {str(e)}")
        logging.error(f"Platform adapter error: {str(e)}")

if __name__ == "__main__":
    main()
