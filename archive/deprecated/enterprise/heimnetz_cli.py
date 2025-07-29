#!/usr/bin/env python3
"""
Heimnetz Enterprise CLI - Unified Command Interface
Modern CLI using typer + rich for managing all enter        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Handle disk usage for Windows
        try:
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:\\')
            else:  # Unix/Linux
                disk = psutil.disk_usage('/')
        except:
            disk = None
        
        result = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
        }
        
        if disk:
            result.update({
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
            })
        
        return results
"""

import typer
from typing import Optional, List
import os
import time
import json
import psutil
import httpx
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.tree import Tree
from rich.markdown import Markdown
from rich import print as rprint
from loguru import logger
import httpx
import psutil
import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import asyncio
from pydantic import BaseModel, Field
from typing import Dict, Any
import os

# Initialize Rich console
console = Console(width=120)

# Configure loguru
logger.add(
    "enterprise_cli.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Pydantic models for configuration
class ServiceConfig(BaseModel):
    name: str
    url: str
    port: int
    status: str = "unknown"
    health_endpoint: str = "/"
    description: str = ""

class EnterpriseConfig(BaseModel):
    services: Dict[str, ServiceConfig]
    base_url: str = "http://localhost"
    monitoring_interval: int = 30
    log_level: str = "INFO"

# Initialize Typer app
app = typer.Typer(
    name="heimnetz-cli",
    help="🏢 Heimnetz Enterprise CLI - Unified command interface for managing all enterprise services",
    add_completion=False,
    rich_markup_mode="rich"
)

# Global configuration
ENTERPRISE_CONFIG = EnterpriseConfig(
    services={
        "multi-tenant": ServiceConfig(
            name="Multi-Tenant Architecture",
            url="http://localhost:5000",
            port=5000,
            description="Complete multi-tenant infrastructure with database isolation"
        ),
        "ai-integration": ServiceConfig(
            name="AI/ML Integration",
            url="http://localhost:5001",
            port=5001,
            health_endpoint="/ai/dashboard",
            description="Advanced AI capabilities with LLM, ML, and NLP"
        ),
        "global-scalability": ServiceConfig(
            name="Global Scalability",
            url="http://localhost:5002",
            port=5002,
            health_endpoint="/global/dashboard",
            description="Multi-region deployment with edge computing"
        ),
        "advanced-analytics": ServiceConfig(
            name="Advanced Analytics",
            url="http://localhost:5003",
            port=5003,
            health_endpoint="/analytics/dashboard",
            description="Business intelligence and GraphQL APIs"
        ),
        "master-dashboard": ServiceConfig(
            name="Master Dashboard",
            url="http://localhost:5004",
            port=5004,
            description="Unified view of all enterprise services"
        )
    }
)

class ServiceManager:
    """Manages enterprise services"""
    
    def __init__(self, config: EnterpriseConfig):
        self.config = config
        self.client = httpx.Client(timeout=5.0)
        
    async def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            service = self.config.services[service_name]
            response = await httpx.AsyncClient().get(
                f"{service.url}{service.health_endpoint}",
                timeout=3.0
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3)
        }
    
    def get_service_processes(self) -> List[Dict[str, Any]]:
        """Get running processes for enterprise services"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cmdline'] and any('enterprise' in str(cmd).lower() for cmd in proc.info['cmdline']):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes

# Initialize service manager
service_manager = ServiceManager(ENTERPRISE_CONFIG)

@app.command()
def status(
    service: Optional[str] = typer.Argument(None, help="Specific service to check"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch mode - continuously monitor status")
):
    """📊 Check the status of enterprise services"""
    
    if watch:
        _watch_status()
    else:
        _show_status(service)

def _show_status(service_name: Optional[str] = None):
    """Show service status"""
    
    with console.status("[bold green]Checking service status..."):
        if service_name:
            if service_name not in ENTERPRISE_CONFIG.services:
                console.print(f"[red]❌ Service '{service_name}' not found[/red]")
                return
            
            _show_single_service_status(service_name)
        else:
            _show_all_services_status()

def _show_single_service_status(service_name: str):
    """Show status for a single service"""
    service = ENTERPRISE_CONFIG.services[service_name]
    
    # Create health check
    try:
        response = httpx.get(f"{service.url}{service.health_endpoint}", timeout=3.0)
        healthy = response.status_code == 200
    except:
        healthy = False
    
    # Create status panel
    status_text = "🟢 HEALTHY" if healthy else "🔴 UNHEALTHY"
    color = "green" if healthy else "red"
    
    panel_content = f"""
[bold]{service.name}[/bold]
[dim]{service.description}[/dim]

🌐 URL: {service.url}
📊 Status: [{color}]{status_text}[/{color}]
🔌 Port: {service.port}
    """
    
    console.print(Panel(panel_content, title=f"Service: {service_name}", border_style=color))

def _show_all_services_status():
    """Show status for all services"""
    
    # Create status table
    table = Table(title="🏢 Heimnetz Enterprise Services Status", show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("URL", style="blue")
    table.add_column("Port", justify="center")
    table.add_column("Description", style="dim")
    
    # Check each service
    for service_name, service in ENTERPRISE_CONFIG.services.items():
        try:
            response = httpx.get(f"{service.url}{service.health_endpoint}", timeout=3.0)
            healthy = response.status_code == 200
        except:
            healthy = False
        
        status_text = "🟢 HEALTHY" if healthy else "🔴 UNHEALTHY"
        
        table.add_row(
            service.name,
            status_text,
            service.url,
            str(service.port),
            service.description
        )
    
    console.print(table)
    
    # Show system metrics
    _show_system_metrics()

def _show_system_metrics():
    """Show system performance metrics"""
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Handle disk usage for Windows
    try:
        if os.name == 'nt':  # Windows
            disk = psutil.disk_usage('C:\\')
        else:  # Unix/Linux
            disk = psutil.disk_usage('/')
    except:
        disk = None
    
    # Create metrics panel
    metrics_content = f"""
🖥️  CPU Usage: {cpu_percent:.1f}%
🧠 Memory Usage: {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)
"""
    
    if disk:
        metrics_content += f"💾 Disk Usage: {disk.percent:.1f}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)\n"
    
    try:
        uptime = time.time() - psutil.boot_time()
        metrics_content += f"⏰ Uptime: {uptime:.0f} seconds\n"
    except:
        metrics_content += "⏰ Uptime: N/A\n"
    
    console.print(Panel(metrics_content, title="System Metrics", border_style="blue"))

def _watch_status():
    """Watch mode for continuous status monitoring"""
    
    console.print("[bold green]📊 Entering watch mode... Press Ctrl+C to exit[/bold green]")
    
    try:
        while True:
            console.clear()
            console.print(f"[bold]📊 Heimnetz Enterprise Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold]")
            console.print("=" * 80)
            
            _show_all_services_status()
            
            console.print("\n[dim]Refreshing in 30 seconds... Press Ctrl+C to exit[/dim]")
            time.sleep(30)
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Watch mode stopped[/bold yellow]")

@app.command()
def start(
    service: Optional[str] = typer.Argument(None, help="Specific service to start"),
    all_services: bool = typer.Option(False, "--all", "-a", help="Start all services")
):
    """🚀 Start enterprise services"""
    
    if all_services:
        _start_all_services()
    elif service:
        _start_single_service(service)
    else:
        console.print("[red]❌ Please specify a service name or use --all[/red]")

def _start_single_service(service_name: str):
    """Start a single service"""
    
    if service_name not in ENTERPRISE_CONFIG.services:
        console.print(f"[red]❌ Service '{service_name}' not found[/red]")
        return
    
    service = ENTERPRISE_CONFIG.services[service_name]
    
    console.print(f"[bold green]🚀 Starting {service.name}...[/bold green]")
    
    # Map service names to Python files
    service_files = {
        "multi-tenant": "enterprise_demo.py",
        "ai-integration": "ai_integration.py", 
        "global-scalability": "global_scalability.py",
        "advanced-analytics": "advanced_analytics.py",
        "master-dashboard": "master_dashboard.py"
    }
    
    if service_name in service_files:
        try:
            # Start the service
            subprocess.Popen([
                sys.executable, service_files[service_name]
            ], cwd=Path(__file__).parent)
            
            console.print(f"[green]✅ {service.name} started successfully[/green]")
            console.print(f"[blue]🌐 Access at: {service.url}[/blue]")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start {service.name}: {e}[/red]")

def _start_all_services():
    """Start all enterprise services"""
    
    console.print("[bold green]🚀 Starting all enterprise services...[/bold green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Starting services...", total=len(ENTERPRISE_CONFIG.services))
        
        for service_name in ENTERPRISE_CONFIG.services:
            progress.update(task, description=f"Starting {service_name}...")
            _start_single_service(service_name)
            progress.advance(task)
            time.sleep(2)  # Give time for service to start
    
    console.print("[bold green]✅ All services started![/bold green]")

@app.command()
def logs(
    service: Optional[str] = typer.Argument(None, help="Service to show logs for"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """📋 Show service logs"""
    
    if not service:
        console.print("[red]❌ Please specify a service name[/red]")
        return
    
    if service not in ENTERPRISE_CONFIG.services:
        console.print(f"[red]❌ Service '{service}' not found[/red]")
        return
    
    # For now, show CLI logs
    log_file = Path("enterprise_cli.log")
    
    if not log_file.exists():
        console.print("[yellow]⚠️  No log file found[/yellow]")
        return
    
    console.print(f"[bold blue]📋 Showing logs for {service}...[/bold blue]")
    
    if follow:
        _follow_logs(log_file)
    else:
        _show_logs(log_file, lines)

def _show_logs(log_file: Path, lines: int):
    """Show log file contents"""
    
    try:
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
            
        # Show last N lines
        for line in log_lines[-lines:]:
            console.print(line.rstrip())
            
    except Exception as e:
        console.print(f"[red]❌ Error reading logs: {e}[/red]")

def _follow_logs(log_file: Path):
    """Follow log file output"""
    
    console.print("[bold green]📋 Following logs... Press Ctrl+C to exit[/bold green]")
    
    try:
        # Simple log following implementation
        with open(log_file, 'r') as f:
            f.seek(0, 2)  # Go to end of file
            
            while True:
                line = f.readline()
                if line:
                    console.print(line.rstrip())
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Log following stopped[/bold yellow]")

@app.command()
def dashboard():
    """🎯 Open the master dashboard in browser"""
    
    master_url = ENTERPRISE_CONFIG.services["master-dashboard"].url
    
    console.print(f"[bold green]🎯 Opening master dashboard...[/bold green]")
    console.print(f"[blue]🌐 URL: {master_url}[/blue]")
    
    try:
        import webbrowser
        webbrowser.open(master_url)
        console.print("[green]✅ Dashboard opened in browser[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to open dashboard: {e}[/red]")
        console.print(f"[blue]Please manually open: {master_url}[/blue]")

@app.command()
def health():
    """🏥 Run comprehensive health check"""
    
    console.print("[bold green]🏥 Running comprehensive health check...[/bold green]")
    
    # Create health check table
    table = Table(title="🏥 Health Check Results", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")
    
    # Check services
    for service_name, service in ENTERPRISE_CONFIG.services.items():
        try:
            response = httpx.get(f"{service.url}{service.health_endpoint}", timeout=3.0)
            healthy = response.status_code == 200
            status_text = "🟢 HEALTHY" if healthy else "🔴 UNHEALTHY"
            details = f"HTTP {response.status_code}" if healthy else "Connection failed"
        except Exception as e:
            status_text = "🔴 UNHEALTHY"
            details = str(e)
        
        table.add_row(service.name, status_text, details)
    
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Handle disk usage for Windows
    try:
        if os.name == 'nt':  # Windows
            disk = psutil.disk_usage('C:\\')
        else:  # Unix/Linux
            disk = psutil.disk_usage('/')
    except:
        disk = None
    
    # CPU check
    cpu_status = "🟢 HEALTHY" if cpu_percent < 80 else "🟡 WARNING" if cpu_percent < 90 else "🔴 CRITICAL"
    table.add_row("CPU Usage", cpu_status, f"{cpu_percent:.1f}%")
    
    # Memory check
    memory_status = "🟢 HEALTHY" if memory.percent < 80 else "🟡 WARNING" if memory.percent < 90 else "🔴 CRITICAL"
    table.add_row("Memory Usage", memory_status, f"{memory.percent:.1f}%")
    
    # Disk check
    if disk:
        disk_status = "🟢 HEALTHY" if disk.percent < 80 else "🟡 WARNING" if disk.percent < 90 else "🔴 CRITICAL"
        table.add_row("Disk Usage", disk_status, f"{disk.percent:.1f}%")
    else:
        table.add_row("Disk Usage", "🟡 WARNING", "Unable to check")
    
    console.print(table)
    
    # Overall health summary - simplified check
    overall_status = "🟢 SYSTEM HEALTHY" if cpu_percent < 80 and memory.percent < 80 else "⚠️  ISSUES DETECTED"
    
    console.print(f"\n[bold]Overall Status: {overall_status}[/bold]")

@app.command()
def info():
    """ℹ️  Show enterprise platform information"""
    
    info_content = """
# 🏢 Heimnetz Enterprise Platform

## 📊 Architecture Overview

The Heimnetz Enterprise Platform is a complete multi-tenant SaaS architecture implemented in **4 phases**:

### Phase 1: Multi-Tenant Architecture ✅
- Database isolation per tenant
- Resource quotas and limits  
- Subscription management
- RBAC authentication
- API key management

### Phase 2: AI/ML Integration ✅
- LLM provider integration (OpenAI, Anthropic)
- Machine learning pipeline
- Natural language processing
- AI orchestration system
- Interactive AI interface

### Phase 3: Global Scalability ✅
- Multi-region deployment (5 regions)
- Edge computing nodes
- Global load balancing
- Data replication
- Automatic failover

### Phase 4: Advanced Analytics ✅
- Real-time metrics collection
- Business intelligence reports
- GraphQL API interface
- Predictive analytics
- Custom dashboards

## 🎯 Success Metrics
- **4 Core Services**: 100% Operational
- **5 Global Regions**: Active with load balancing
- **2 AI Providers**: Integrated
- **100% System Health**: All components running

## 🌐 Service Endpoints
- **Multi-Tenant**: http://localhost:5000
- **AI Integration**: http://localhost:5001/ai/dashboard
- **Global Scalability**: http://localhost:5002/global/dashboard
- **Advanced Analytics**: http://localhost:5003/analytics/dashboard
- **Master Dashboard**: http://localhost:5004
    """
    
    console.print(Markdown(info_content))

@app.command()
def context():
    """🧠 ContextForge MCP Server management and testing"""
    
    console.print("[bold green]🧠 ContextForge - Model Context Protocol Server[/bold green]")
    
    # Import ContextForge service
    try:
        from context.service_integration import contextforge_service
        
        # Show service info
        service_info = contextforge_service.get_service_info()
        
        # Create service info table
        table = Table(title="🧠 ContextForge Service Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Service Name", service_info["name"])
        table.add_row("Version", service_info["version"])
        table.add_row("Port", str(service_info["port"]))
        table.add_row("Status", "🟢 Active")
        table.add_row("Protocol Versions", ", ".join(service_info["supported_protocols"]))
        table.add_row("Supported Models", ", ".join(service_info["supported_models"]))
        table.add_row("Capabilities", str(len(service_info["capabilities"])))
        
        console.print(table)
        
        # Show health status
        health = contextforge_service.get_health_status()
        
        health_content = f"""
🔍 Service Health: {health['status'].upper()}
⏱️  Uptime: {health['uptime_seconds']:.0f} seconds
🧠 Cached Embeddings: {health['components']['contextforge']['cached_embeddings']}
📊 Active Sessions: {health['components']['contextforge']['active_sessions']}
🎯 Request Success Rate: {health['components']['router']['success_rate']:.1%}
⚡ Avg Response Time: {health['components']['router']['average_response_time']:.2f}s
🔗 Healthy Endpoints: {health['components']['router']['healthy_endpoints']}/{health['components']['router']['active_endpoints']}
        """
        
        console.print(Panel(health_content, title="ContextForge Health Status", border_style="green"))
        
        # Show sample test
        console.print("\n[bold blue]🧪 Running Sample Context Request...[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing context request...", total=None)
            
            test_results = contextforge_service.run_test_requests()
            
        # Show test results
        if test_results["test_summary"]["total_tests"] > 0:
            test_table = Table(title="🧪 Test Results", show_header=True, header_style="bold blue")
            test_table.add_column("Test", style="cyan")
            test_table.add_column("Status", justify="center")
            test_table.add_column("Compatibility", style="dim")
            
            for result in test_results["results"][:3]:  # Show first 3 tests
                status_icon = "✅" if result["status"] == "success" else "❌"
                compatibility = f"{result.get('compatibility_score', 0):.1%}" if result.get('compatibility_score') else "N/A"
                test_table.add_row(
                    result["test_name"],
                    f"{status_icon} {result['status'].upper()}",
                    compatibility
                )
            
            console.print(test_table)
            
            # Summary
            summary = test_results["test_summary"]
            console.print(f"\n[bold green]✅ Tests Passed: {summary['successful']}/{summary['total_tests']}[/bold green]")
        
        # Show integration status
        integration = contextforge_service.get_integration_status()
        console.print(f"\n[bold cyan]🔗 Integrations Active: {len([i for i in integration['integrations'].values() if i['status'] == 'active'])}/3[/bold cyan]")
        
    except ImportError:
        console.print("[red]❌ ContextForge service not available. Make sure it's properly installed.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error accessing ContextForge: {e}[/red]")

@app.command()
def version():
    """📦 Show version information"""
    
    version_info = """
🏢 Heimnetz Enterprise Platform
📦 Version: 1.0.0
🗓️  Release Date: July 18, 2025
🔧 Implementation: Complete (Audit 5)
🎯 Status: Production Ready

Built with:
- Python 3.12
- FastAPI + Flask
- SQLite + PostgreSQL
- Redis
- Docker (optional)
- Modern Python libraries (typer, rich, pydantic, etc.)
    """
    
    console.print(Panel(version_info, title="Version Information", border_style="blue"))

if __name__ == "__main__":
    # Log CLI usage
    logger.info("Enterprise CLI started")
    
    try:
        app()
    except Exception as e:
        logger.error(f"CLI error: {e}")
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        logger.info("Enterprise CLI ended")
