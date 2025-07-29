#!/usr/bin/env python3
"""
ContextForge Deployment Script
Deploys the ContextForge MCP server with enterprise integration
Part of the Heimnetz Enterprise Suite
"""

import asyncio
import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

class ContextForgeDeployment:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.config_path = self.base_path / "context_registry.json"
        self.deployment_config = {
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "workers": 4,
            "log_level": "info",
            "reload": False,
            "health_check_interval": 30,
            "metrics_collection_interval": 60
        }
        
    async def pre_deployment_checks(self) -> bool:
        """
        Run pre-deployment validation checks
        """
        console.print("\n[bold blue]🔍 Running Pre-Deployment Checks[/bold blue]")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Configuration", self.check_configuration),
            ("Port Availability", self.check_port_availability),
            ("File Permissions", self.check_file_permissions),
            ("Service Registry", self.check_service_registry)
        ]
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for check_name, check_func in checks:
                task = progress.add_task(f"Checking {check_name}...", total=1)
                
                try:
                    result = await check_func()
                    results.append((check_name, result, "✅"))
                    progress.update(task, completed=1)
                except Exception as e:
                    results.append((check_name, str(e), "❌"))
                    progress.update(task, completed=1)
        
        # Display results
        table = Table(title="Pre-Deployment Check Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Result")
        
        all_passed = True
        for check_name, result, status in results:
            table.add_row(check_name, status, str(result))
            if status == "❌":
                all_passed = False
        
        console.print(table)
        
        if not all_passed:
            console.print("[bold red]❌ Some checks failed. Please resolve issues before deployment.[/bold red]")
            return False
        
        console.print("[bold green]✅ All pre-deployment checks passed![/bold green]")
        return True
    
    async def check_python_version(self) -> str:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return f"Python {version.major}.{version.minor}.{version.micro} (Compatible)"
        else:
            raise Exception(f"Python {version.major}.{version.minor}.{version.micro} not supported. Requires Python 3.8+")
    
    async def check_dependencies(self) -> str:
        """Check required dependencies"""
        required_packages = [
            "fastapi", "uvicorn", "pydantic", "httpx", 
            "rich", "typer", "loguru", "psutil"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            raise Exception(f"Missing packages: {', '.join(missing)}")
        
        return f"All {len(required_packages)} required packages available"
    
    async def check_configuration(self) -> str:
        """Check configuration file"""
        if not self.config_path.exists():
            raise Exception(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path) as f:
            config = json.load(f)
        
        required_keys = ["model_registry", "routing_strategies", "context_sources"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            raise Exception(f"Missing configuration keys: {', '.join(missing_keys)}")
        
        return "Configuration file valid"
    
    async def check_port_availability(self) -> str:
        """Check if deployment port is available"""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', self.deployment_config["api_port"]))
            sock.close()
            return f"Port {self.deployment_config['api_port']} available"
        except OSError:
            raise Exception(f"Port {self.deployment_config['api_port']} already in use")
    
    async def check_file_permissions(self) -> str:
        """Check file permissions"""
        required_files = [
            "context/index.py",
            "context/router.py", 
            "context/api_endpoints.py",
            "context/service_integration.py"
        ]
        
        for file_path in required_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                raise Exception(f"Required file not found: {file_path}")
            if not os.access(full_path, os.R_OK):
                raise Exception(f"Cannot read file: {file_path}")
        
        return "All required files accessible"
    
    async def check_service_registry(self) -> str:
        """Check service registry integration"""
        try:
            from context.service_integration import service_integration
            health = await service_integration.get_service_info()
            return f"Service registry operational: {health.get('status', 'unknown')}"
        except Exception as e:
            raise Exception(f"Service registry error: {str(e)}")
    
    async def deploy_contextforge(self) -> bool:
        """
        Deploy ContextForge MCP server
        """
        console.print("\n[bold blue]🚀 Deploying ContextForge MCP Server[/bold blue]")
        
        try:
            # Start the FastAPI server
            cmd = [
                sys.executable, "-m", "uvicorn",
                "context.api_endpoints:app",
                "--host", self.deployment_config["api_host"],
                "--port", str(self.deployment_config["api_port"]),
                "--workers", str(self.deployment_config["workers"]),
                "--log-level", self.deployment_config["log_level"]
            ]
            
            if self.deployment_config["reload"]:
                cmd.append("--reload")
            
            console.print(f"[bold green]Starting server with command:[/bold green]")
            console.print(f"[dim]{' '.join(cmd)}[/dim]")
            
            # Start server process
            process = subprocess.Popen(
                cmd,
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            # Check if server is running
            health_url = f"http://{self.deployment_config['api_host']}:{self.deployment_config['api_port']}/context/health"
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_url, timeout=10)
                    if response.status_code == 200:
                        console.print("[bold green]✅ ContextForge server started successfully![/bold green]")
                        return True
                    else:
                        console.print(f"[bold red]❌ Server health check failed: {response.status_code}[/bold red]")
                        return False
            except Exception as e:
                console.print(f"[bold red]❌ Cannot connect to server: {str(e)}[/bold red]")
                return False
                
        except Exception as e:
            console.print(f"[bold red]❌ Deployment failed: {str(e)}[/bold red]")
            return False
    
    async def post_deployment_validation(self) -> bool:
        """
        Run post-deployment validation
        """
        console.print("\n[bold blue]🔍 Running Post-Deployment Validation[/bold blue]")
        
        base_url = f"http://{self.deployment_config['api_host']}:{self.deployment_config['api_port']}"
        
        tests = [
            ("Health Check", f"{base_url}/context/health"),
            ("Metrics", f"{base_url}/context/metrics"),
            ("Models", f"{base_url}/context/models"),
            ("Protocols", f"{base_url}/context/protocols"),
            ("Configuration", f"{base_url}/context/config")
        ]
        
        results = []
        
        async with httpx.AsyncClient() as client:
            for test_name, url in tests:
                try:
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        results.append((test_name, "✅", "OK"))
                    else:
                        results.append((test_name, "❌", f"HTTP {response.status_code}"))
                except Exception as e:
                    results.append((test_name, "❌", str(e)))
        
        # Display results
        table = Table(title="Post-Deployment Validation Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Result")
        
        all_passed = True
        for test_name, status, result in results:
            table.add_row(test_name, status, result)
            if status == "❌":
                all_passed = False
        
        console.print(table)
        
        if not all_passed:
            console.print("[bold red]❌ Some validation tests failed.[/bold red]")
            return False
        
        console.print("[bold green]✅ All validation tests passed![/bold green]")
        return True
    
    async def display_deployment_summary(self):
        """
        Display deployment summary
        """
        panel_content = f"""
[bold green]🎉 ContextForge MCP Server Deployment Complete![/bold green]

[bold cyan]📊 Deployment Details:[/bold cyan]
• API Host: {self.deployment_config['api_host']}
• API Port: {self.deployment_config['api_port']}
• Workers: {self.deployment_config['workers']}
• Log Level: {self.deployment_config['log_level']}

[bold cyan]🔗 Available Endpoints:[/bold cyan]
• Health Check: /context/health
• Context Analysis: /context/analyze
• Model Compatibility: /context/compatibility
• Request Routing: /context/route
• Metrics: /context/metrics
• Models: /context/models
• Protocols: /context/protocols
• Configuration: /context/config

[bold cyan]🛠️ Management Commands:[/bold cyan]
• CLI: python heimnetz_cli.py context info
• Health: python heimnetz_cli.py context health
• Test: python heimnetz_cli.py context test <test_name>

[bold cyan]📖 Documentation:[/bold cyan]
• API Docs: http://localhost:{self.deployment_config['api_port']}/docs
• OpenAPI: http://localhost:{self.deployment_config['api_port']}/openapi.json
        """
        
        console.print(Panel(panel_content, title="🚀 ContextForge Deployment Summary", border_style="green"))
    
    async def run_deployment(self):
        """
        Run complete deployment process
        """
        console.print(Panel(
            "[bold blue]ContextForge MCP Server Deployment[/bold blue]\n"
            "Enterprise-grade Model Context Protocol server deployment",
            title="🚀 Deployment Starting",
            border_style="blue"
        ))
        
        # Pre-deployment checks
        if not await self.pre_deployment_checks():
            console.print("[bold red]❌ Deployment aborted due to failed checks.[/bold red]")
            return False
        
        # Deploy ContextForge
        if not await self.deploy_contextforge():
            console.print("[bold red]❌ Deployment failed.[/bold red]")
            return False
        
        # Post-deployment validation
        if not await self.post_deployment_validation():
            console.print("[bold yellow]⚠️ Deployment completed with warnings.[/bold yellow]")
        
        # Display summary
        await self.display_deployment_summary()
        
        console.print("[bold green]✅ ContextForge deployment completed successfully![/bold green]")
        return True

async def main():
    """
    Main deployment function
    """
    deployment = ContextForgeDeployment()
    
    try:
        success = await deployment.run_deployment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Deployment interrupted by user.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Deployment error: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
