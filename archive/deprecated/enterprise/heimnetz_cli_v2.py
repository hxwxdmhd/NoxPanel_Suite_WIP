#!/usr/bin/env python3
"""
Heimnetz Enterprise CLI - Unified Command Interface
Modern CLI using typer + rich for managing all enterprise services
"""

import asyncio
import httpx
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
import psutil

# Import service integrations
try:
    from context.service_integration import service_integration
except ImportError:
    service_integration = None

# Initialize CLI app and console
app = typer.Typer(help="Heimnetz Enterprise CLI - Unified command interface")
console = Console()

# API endpoints
AETHERCORE_URL = "http://localhost:8001"
CONTEXTFORGE_URL = "http://localhost:8000"

# Command groups
context_app = typer.Typer(help="ContextForge MCP Server management")
aethercore_app = typer.Typer(help="AetherCore MSP Server management")
system_app = typer.Typer(help="System monitoring and management")

app.add_typer(context_app, name="context")
app.add_typer(aethercore_app, name="aethercore")
app.add_typer(system_app, name="system")

# Utility functions
async def make_request(url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {"error": "Request timeout"}
    except httpx.ConnectError:
        return {"error": "Connection failed"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ContextForge commands
@context_app.command("info")
def context_info():
    """Show ContextForge service information"""
    async def _get_info():
        info = await make_request(f"{CONTEXTFORGE_URL}/context/health")
        return info
    
    result = asyncio.run(_get_info())
    
    if "error" in result:
        console.print(f"[bold red]❌ Error: {result['error']}[/bold red]")
        return
    
    # Display service information
    panel_content = f"""
[bold cyan]ContextForge MCP Server[/bold cyan]

[bold green]Status:[/bold green] {result.get('status', 'unknown').upper()}
[bold green]Version:[/bold green] {result.get('version', 'unknown')}
[bold green]Uptime:[/bold green] {result.get('uptime_seconds', 0):.1f}s
[bold green]Active Models:[/bold green] {result.get('active_models', 0)}
[bold green]Total Requests:[/bold green] {result.get('total_requests', 0)}

[bold blue]System Info:[/bold blue]
• CPU: {result.get('system_info', {}).get('cpu_percent', 0):.1f}%
• Memory: {result.get('system_info', {}).get('memory_percent', 0):.1f}%
• GPU Available: {result.get('system_info', {}).get('gpu_available', False)}
    """
    
    console.print(Panel(panel_content, title="🔍 ContextForge Service Info", border_style="blue"))

@context_app.command("health")
def context_health():
    """Check ContextForge health status"""
    async def _check_health():
        health = await make_request(f"{CONTEXTFORGE_URL}/context/health")
        return health
    
    result = asyncio.run(_check_health())
    
    if "error" in result:
        console.print(f"[bold red]❌ ContextForge is unhealthy: {result['error']}[/bold red]")
        return
    
    status = result.get('status', 'unknown')
    if status == 'healthy':
        console.print("[bold green]✅ ContextForge is healthy[/bold green]")
    else:
        console.print(f"[bold yellow]⚠️ ContextForge status: {status}[/bold yellow]")

@context_app.command("test")
def context_test(test_name: str = typer.Argument(..., help="Test name to run")):
    """Run ContextForge tests"""
    if not service_integration:
        console.print("[bold red]❌ Service integration module not available[/bold red]")
        return
    
    async def _run_test():
        result = await service_integration.run_test(test_name)
        return result
    
    result = asyncio.run(_run_test())
    
    if result.get('success', False):
        console.print(f"[bold green]✅ Test '{test_name}' passed[/bold green]")
    else:
        console.print(f"[bold red]❌ Test '{test_name}' failed: {result.get('error', 'Unknown error')}[/bold red]")

# AetherCore commands
@aethercore_app.command("info")
def aethercore_info():
    """Show AetherCore service information"""
    async def _get_info():
        health = await make_request(f"{AETHERCORE_URL}/health")
        models = await make_request(f"{AETHERCORE_URL}/models")
        metrics = await make_request(f"{AETHERCORE_URL}/metrics")
        
        return {
            "health": health,
            "models": models,
            "metrics": metrics
        }
    
    result = asyncio.run(_get_info())
    
    if "error" in result.get("health", {}):
        console.print(f"[bold red]❌ Error: {result['health']['error']}[/bold red]")
        return
    
    health = result.get("health", {})
    models = result.get("models", [])
    metrics = result.get("metrics", {})
    
    # Display service information
    panel_content = f"""
[bold cyan]AetherCore MSP Server[/bold cyan]

[bold green]Status:[/bold green] {health.get('status', 'unknown').upper()}
[bold green]Version:[/bold green] {health.get('version', 'unknown')}
[bold green]Uptime:[/bold green] {health.get('uptime_seconds', 0):.1f}s
[bold green]Active Models:[/bold green] {health.get('active_models', 0)}
[bold green]Total Requests:[/bold green] {health.get('total_requests', 0)}

[bold blue]System Info:[/bold blue]
• CPU: {health.get('system_info', {}).get('cpu_percent', 0):.1f}%
• Memory: {health.get('system_info', {}).get('memory_percent', 0):.1f}%
• GPU Available: {health.get('system_info', {}).get('gpu_available', False)}
• GPU Count: {health.get('system_info', {}).get('gpu_count', 0)}

[bold blue]Performance:[/bold blue]
• Avg Response Time: {metrics.get('avg_response_time_ms', 0):.2f}ms
• Memory Usage: {metrics.get('memory_usage_mb', 0):.1f}MB
• Successful Requests: {metrics.get('successful_requests', 0)}
• Failed Requests: {metrics.get('failed_requests', 0)}
    """
    
    console.print(Panel(panel_content, title="🤖 AetherCore Service Info", border_style="magenta"))

@aethercore_app.command("models")
def aethercore_models():
    """List available models in AetherCore"""
    async def _get_models():
        models = await make_request(f"{AETHERCORE_URL}/models")
        return models
    
    result = asyncio.run(_get_models())
    
    if "error" in result:
        console.print(f"[bold red]❌ Error: {result['error']}[/bold red]")
        return
    
    if not result:
        console.print("[bold yellow]No models available[/bold yellow]")
        return
    
    # Create table
    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Memory", style="magenta")
    table.add_column("Requests", style="white")
    
    for model in result:
        status_style = "green" if model.get("status") == "ready" else "red"
        table.add_row(
            model.get("model_id", ""),
            model.get("name", ""),
            f"[{status_style}]{model.get('status', 'unknown')}[/{status_style}]",
            model.get("model_type", ""),
            f"{model.get('memory_usage_mb', 0):.1f}MB",
            str(model.get("total_requests", 0))
        )
    
    console.print(table)

@aethercore_app.command("load")
def aethercore_load_model(model_id: str = typer.Argument(..., help="Model ID to load")):
    """Load a model in AetherCore"""
    async def _load_model():
        result = await make_request(f"{AETHERCORE_URL}/models/{model_id}/load", method="POST")
        return result
    
    result = asyncio.run(_load_model())
    
    if "error" in result:
        console.print(f"[bold red]❌ Error loading model: {result['error']}[/bold red]")
        return
    
    status = result.get("status", "unknown")
    if status == "loading":
        console.print(f"[bold yellow]🔄 Loading model '{model_id}'...[/bold yellow]")
    elif status == "already_loaded":
        console.print(f"[bold green]✅ Model '{model_id}' is already loaded[/bold green]")
    else:
        console.print(f"[bold blue]ℹ️ Model '{model_id}' status: {status}[/bold blue]")

@aethercore_app.command("unload")
def aethercore_unload_model(model_id: str = typer.Argument(..., help="Model ID to unload")):
    """Unload a model from AetherCore"""
    async def _unload_model():
        result = await make_request(f"{AETHERCORE_URL}/models/{model_id}/unload", method="POST")
        return result
    
    result = asyncio.run(_unload_model())
    
    if "error" in result:
        console.print(f"[bold red]❌ Error unloading model: {result['error']}[/bold red]")
        return
    
    console.print(f"[bold green]✅ Model '{model_id}' unloaded successfully[/bold green]")

@aethercore_app.command("serve")
def aethercore_serve(
    model_id: str = typer.Argument(..., help="Model ID to use"),
    text: str = typer.Option(..., "--text", "-t", help="Text to process")
):
    """Serve inference request to AetherCore"""
    async def _serve():
        data = {
            "model_id": model_id,
            "inputs": {"text": text},
            "parameters": {}
        }
        result = await make_request(f"{AETHERCORE_URL}/serve", method="POST", data=data)
        return result
    
    result = asyncio.run(_serve())
    
    if "error" in result:
        console.print(f"[bold red]❌ Error serving request: {result['error']}[/bold red]")
        return
    
    if result.get("status") == "success":
        console.print(f"[bold green]✅ Inference completed in {result.get('processing_time_ms', 0):.2f}ms[/bold green]")
        
        # Display outputs
        outputs = result.get("outputs", {})
        if outputs:
            console.print("\n[bold blue]Outputs:[/bold blue]")
            console.print(json.dumps(outputs, indent=2))
    else:
        console.print(f"[bold red]❌ Inference failed: {result.get('error', 'Unknown error')}[/bold red]")

@aethercore_app.command("health")
def aethercore_health():
    """Check AetherCore health status"""
    async def _check_health():
        health = await make_request(f"{AETHERCORE_URL}/health")
        return health
    
    result = asyncio.run(_check_health())
    
    if "error" in result:
        console.print(f"[bold red]❌ AetherCore is unhealthy: {result['error']}[/bold red]")
        return
    
    status = result.get('status', 'unknown')
    if status == 'healthy':
        console.print("[bold green]✅ AetherCore is healthy[/bold green]")
    else:
        console.print(f"[bold yellow]⚠️ AetherCore status: {status}[/bold yellow]")

# System commands
@system_app.command("status")
def system_status():
    """Show system status"""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Handle disk usage
    try:
        if sys.platform == "win32":
            disk = psutil.disk_usage('C:\\')
        else:
            disk = psutil.disk_usage('/')
    except:
        disk = None
    
    # Create system status panel
    panel_content = f"""
[bold cyan]System Status[/bold cyan]

[bold green]CPU Usage:[/bold green] {cpu_percent:.1f}%
[bold green]Memory Usage:[/bold green] {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)
"""
    
    if disk:
        panel_content += f"[bold green]Disk Usage:[/bold green] {disk.percent:.1f}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)\n"
    
    # Add service status
    panel_content += "\n[bold blue]Service Status:[/bold blue]\n"
    
    # Check services
    services = [
        ("AetherCore", f"{AETHERCORE_URL}/heartbeat"),
        ("ContextForge", f"{CONTEXTFORGE_URL}/context/health")
    ]
    
    async def _check_services():
        results = {}
        for name, url in services:
            result = await make_request(url)
            results[name] = "✅" if "error" not in result else "❌"
        return results
    
    service_results = asyncio.run(_check_services())
    
    for name, status in service_results.items():
        panel_content += f"• {name}: {status}\n"
    
    console.print(Panel(panel_content, title="🖥️ System Status", border_style="green"))

@system_app.command("services")
def system_services():
    """Show detailed service information"""
    async def _get_service_info():
        services = {}
        
        # AetherCore
        aethercore_health = await make_request(f"{AETHERCORE_URL}/health")
        services["AetherCore"] = aethercore_health
        
        # ContextForge
        contextforge_health = await make_request(f"{CONTEXTFORGE_URL}/context/health")
        services["ContextForge"] = contextforge_health
        
        return services
    
    result = asyncio.run(_get_service_info())
    
    table = Table(title="Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="blue")
    table.add_column("Uptime", style="yellow")
    table.add_column("CPU", style="magenta")
    table.add_column("Memory", style="white")
    
    for service_name, info in result.items():
        if "error" in info:
            table.add_row(
                service_name,
                "[red]❌ Error[/red]",
                "N/A",
                "N/A",
                "N/A",
                "N/A"
            )
        else:
            status = "✅ Healthy" if info.get("status") == "healthy" else f"⚠️ {info.get('status', 'Unknown')}"
            uptime = f"{info.get('uptime_seconds', 0):.1f}s"
            cpu = f"{info.get('system_info', {}).get('cpu_percent', 0):.1f}%"
            memory = f"{info.get('system_info', {}).get('memory_percent', 0):.1f}%"
            
            table.add_row(
                service_name,
                status,
                info.get("version", "Unknown"),
                uptime,
                cpu,
                memory
            )
    
    console.print(table)

# Main command
@app.command()
def status():
    """Show overall system status"""
    system_status()

@app.command()
def version():
    """Show version information"""
    console.print(Panel(
        "[bold cyan]Heimnetz Enterprise Suite[/bold cyan]\n"
        "[bold green]Version:[/bold green] 1.0.0\n"
        "[bold green]Components:[/bold green]\n"
        "• AetherCore MSP Server\n"
        "• ContextForge MCP Server\n"
        "• Enterprise CLI\n"
        "• Docker Integration\n"
        "• Monitoring Dashboard",
        title="🏠 Heimnetz Enterprise",
        border_style="blue"
    ))

if __name__ == "__main__":
    app()
