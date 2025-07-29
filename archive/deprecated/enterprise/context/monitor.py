#!/usr/bin/env python3
"""
ContextForge Real-time Monitoring Dashboard
Real-time monitoring and metrics visualization for ContextForge MCP server
Part of the Heimnetz Enterprise Suite
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.align import Align
from rich.text import Text
import psutil
import threading
from collections import deque, defaultdict

console = Console()

class ContextForgeMonitor:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.metrics_history = deque(maxlen=100)
        self.health_history = deque(maxlen=50)
        self.request_history = deque(maxlen=200)
        self.error_history = deque(maxlen=100)
        self.performance_metrics = defaultdict(list)
        self.is_running = False
        self.update_interval = 2  # seconds
        
    async def fetch_health_data(self) -> Dict[str, Any]:
        """
        Fetch health data from ContextForge API
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/context/health", timeout=5)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def fetch_metrics_data(self) -> Dict[str, Any]:
        """
        Fetch metrics data from ContextForge API
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/context/metrics", timeout=5)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def fetch_models_data(self) -> Dict[str, Any]:
        """
        Fetch available models data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/context/models", timeout=5)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-level metrics
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "timestamp": time.time()
        }
    
    def create_health_panel(self, health_data: Dict[str, Any]) -> Panel:
        """
        Create health status panel
        """
        status = health_data.get("status", "unknown")
        
        if status == "healthy":
            status_text = "[bold green]🟢 HEALTHY[/bold green]"
            border_style = "green"
        elif status == "unhealthy":
            status_text = "[bold red]🔴 UNHEALTHY[/bold red]"
            border_style = "red"
        else:
            status_text = "[bold yellow]🟡 UNKNOWN[/bold yellow]"
            border_style = "yellow"
        
        # Health details
        contextforge_health = health_data.get("contextforge", {})
        service_health = health_data.get("service_integration", {})
        
        health_content = f"""
{status_text}

[bold cyan]ContextForge Core:[/bold cyan]
• Protocol Version: {contextforge_health.get('protocol_version', 'unknown')}
• Active Models: {contextforge_health.get('active_models', 0)}
• Request Queue: {contextforge_health.get('request_queue_size', 0)}
• Uptime: {contextforge_health.get('uptime', 'unknown')}

[bold cyan]Service Integration:[/bold cyan]
• Status: {service_health.get('status', 'unknown')}
• Services: {service_health.get('active_services', 0)}
• Last Check: {service_health.get('last_health_check', 'unknown')}
        """
        
        return Panel(
            health_content.strip(),
            title="🏥 Health Status",
            border_style=border_style
        )
    
    def create_metrics_panel(self, metrics_data: Dict[str, Any]) -> Panel:
        """
        Create metrics panel
        """
        metrics = metrics_data.get("metrics", {})
        
        # Request metrics
        total_requests = metrics.get("total_requests", 0)
        successful_requests = metrics.get("successful_requests", 0)
        failed_requests = metrics.get("failed_requests", 0)
        avg_response_time = metrics.get("average_response_time", 0)
        
        # Calculate success rate
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        metrics_content = f"""
[bold cyan]Request Metrics:[/bold cyan]
• Total Requests: {total_requests:,}
• Successful: {successful_requests:,}
• Failed: {failed_requests:,}
• Success Rate: {success_rate:.1f}%
• Avg Response Time: {avg_response_time:.2f}ms

[bold cyan]Performance:[/bold cyan]
• Requests/Second: {metrics.get('requests_per_second', 0):.1f}
• Queue Length: {metrics.get('queue_length', 0)}
• Active Connections: {metrics.get('active_connections', 0)}
• Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1f}%
        """
        
        return Panel(
            metrics_content.strip(),
            title="📊 Metrics",
            border_style="blue"
        )
    
    def create_system_panel(self, system_data: Dict[str, Any]) -> Panel:
        """
        Create system metrics panel
        """
        cpu_percent = system_data.get("cpu_percent", 0)
        memory_percent = system_data.get("memory_percent", 0)
        disk_usage = system_data.get("disk_usage", 0)
        
        # CPU status
        if cpu_percent < 70:
            cpu_status = "[green]●[/green]"
        elif cpu_percent < 90:
            cpu_status = "[yellow]●[/yellow]"
        else:
            cpu_status = "[red]●[/red]"
        
        # Memory status
        if memory_percent < 70:
            memory_status = "[green]●[/green]"
        elif memory_percent < 90:
            memory_status = "[yellow]●[/yellow]"
        else:
            memory_status = "[red]●[/red]"
        
        # Disk status
        if disk_usage < 80:
            disk_status = "[green]●[/green]"
        elif disk_usage < 95:
            disk_status = "[yellow]●[/yellow]"
        else:
            disk_status = "[red]●[/red]"
        
        system_content = f"""
[bold cyan]System Resources:[/bold cyan]
• CPU Usage: {cpu_status} {cpu_percent:.1f}%
• Memory Usage: {memory_status} {memory_percent:.1f}%
• Disk Usage: {disk_status} {disk_usage:.1f}%

[bold cyan]Network I/O:[/bold cyan]
• Bytes Sent: {system_data.get('network_io', {}).get('bytes_sent', 0):,}
• Bytes Received: {system_data.get('network_io', {}).get('bytes_recv', 0):,}
        """
        
        return Panel(
            system_content.strip(),
            title="🖥️ System",
            border_style="cyan"
        )
    
    def create_models_panel(self, models_data: Dict[str, Any]) -> Panel:
        """
        Create models status panel
        """
        models = models_data.get("models", [])
        total_models = models_data.get("total_count", 0)
        
        if "error" in models_data:
            models_content = f"[bold red]Error: {models_data['error']}[/bold red]"
        else:
            models_content = f"[bold cyan]Available Models:[/bold cyan] {total_models}\n\n"
            
            # Display first few models
            for i, model in enumerate(models[:5]):
                model_name = model.get("name", "unknown")
                model_type = model.get("type", "unknown")
                model_status = model.get("status", "unknown")
                
                status_icon = "🟢" if model_status == "active" else "🔴"
                models_content += f"• {status_icon} {model_name} ({model_type})\n"
            
            if len(models) > 5:
                models_content += f"• ... and {len(models) - 5} more models\n"
        
        return Panel(
            models_content.strip(),
            title="🤖 Models",
            border_style="magenta"
        )
    
    def create_recent_activity_panel(self) -> Panel:
        """
        Create recent activity panel
        """
        if not self.request_history:
            activity_content = "[dim]No recent activity[/dim]"
        else:
            activity_content = "[bold cyan]Recent Requests:[/bold cyan]\n\n"
            
            # Show last 10 requests
            for request in list(self.request_history)[-10:]:
                timestamp = datetime.fromtimestamp(request.get("timestamp", 0))
                status = request.get("status", "unknown")
                endpoint = request.get("endpoint", "unknown")
                response_time = request.get("response_time", 0)
                
                status_icon = "✅" if status == "success" else "❌"
                activity_content += f"{status_icon} {timestamp.strftime('%H:%M:%S')} {endpoint} ({response_time:.2f}ms)\n"
        
        return Panel(
            activity_content.strip(),
            title="📋 Recent Activity",
            border_style="white"
        )
    
    def create_performance_chart(self) -> Panel:
        """
        Create simple ASCII performance chart
        """
        if len(self.metrics_history) < 2:
            chart_content = "[dim]Collecting data...[/dim]"
        else:
            chart_content = "[bold cyan]Response Time Trend (last 20 samples):[/bold cyan]\n\n"
            
            # Get last 20 response times
            recent_metrics = list(self.metrics_history)[-20:]
            response_times = [m.get("metrics", {}).get("average_response_time", 0) for m in recent_metrics]
            
            if response_times:
                max_time = max(response_times) if response_times else 1
                min_time = min(response_times) if response_times else 0
                
                # Simple ASCII chart
                for i, rt in enumerate(response_times):
                    if max_time > 0:
                        bar_length = int((rt / max_time) * 30)
                        bar = "█" * bar_length + "░" * (30 - bar_length)
                        chart_content += f"{i+1:2d}: {bar} {rt:.1f}ms\n"
        
        return Panel(
            chart_content.strip(),
            title="📈 Performance Chart",
            border_style="green"
        )
    
    def create_dashboard_layout(self, health_data: Dict[str, Any], metrics_data: Dict[str, Any], 
                              models_data: Dict[str, Any], system_data: Dict[str, Any]) -> Layout:
        """
        Create dashboard layout
        """
        layout = Layout()
        
        # Split into top and bottom
        layout.split_column(
            Layout(name="top", size=12),
            Layout(name="bottom")
        )
        
        # Top section - status panels
        layout["top"].split_row(
            Layout(self.create_health_panel(health_data), name="health"),
            Layout(self.create_metrics_panel(metrics_data), name="metrics"),
            Layout(self.create_system_panel(system_data), name="system")
        )
        
        # Bottom section - models and activity
        layout["bottom"].split_row(
            Layout(self.create_models_panel(models_data), name="models"),
            Layout(self.create_recent_activity_panel(), name="activity"),
            Layout(self.create_performance_chart(), name="performance")
        )
        
        return layout
    
    async def collect_data(self):
        """
        Collect monitoring data
        """
        while self.is_running:
            try:
                # Fetch data from APIs
                health_data = await self.fetch_health_data()
                metrics_data = await self.fetch_metrics_data()
                models_data = await self.fetch_models_data()
                system_data = self.get_system_metrics()
                
                # Store in history
                current_time = time.time()
                self.health_history.append({
                    "timestamp": current_time,
                    "data": health_data
                })
                self.metrics_history.append({
                    "timestamp": current_time,
                    "data": metrics_data
                })
                
                # Simulate request activity (in real implementation, this would come from actual requests)
                if "metrics" in metrics_data:
                    self.request_history.append({
                        "timestamp": current_time,
                        "status": "success",
                        "endpoint": "/context/analyze",
                        "response_time": metrics_data["metrics"].get("average_response_time", 0)
                    })
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                console.print(f"[bold red]Error collecting data: {str(e)}[/bold red]")
                await asyncio.sleep(self.update_interval)
    
    async def run_dashboard(self):
        """
        Run the monitoring dashboard
        """
        self.is_running = True
        
        # Start data collection in background
        data_collection_task = asyncio.create_task(self.collect_data())
        
        try:
            with Live(console=console, refresh_per_second=1) as live:
                while self.is_running:
                    # Get latest data
                    health_data = self.health_history[-1]["data"] if self.health_history else {}
                    metrics_data = self.metrics_history[-1]["data"] if self.metrics_history else {}
                    models_data = await self.fetch_models_data()
                    system_data = self.get_system_metrics()
                    
                    # Create dashboard
                    dashboard = self.create_dashboard_layout(
                        health_data, metrics_data, models_data, system_data
                    )
                    
                    # Add header
                    header = Panel(
                        Align.center(
                            f"[bold blue]ContextForge Real-time Monitor[/bold blue]\n"
                            f"[dim]Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                            f"API: {self.api_url}[/dim]"
                        ),
                        border_style="blue"
                    )
                    
                    # Create full layout
                    full_layout = Layout()
                    full_layout.split_column(
                        Layout(header, size=4),
                        Layout(dashboard)
                    )
                    
                    live.update(full_layout)
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Monitoring stopped by user[/bold yellow]")
        finally:
            self.is_running = False
            data_collection_task.cancel()
            try:
                await data_collection_task
            except asyncio.CancelledError:
                pass

async def main():
    """
    Main monitoring function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="ContextForge Monitoring Dashboard")
    parser.add_argument("--url", default="http://localhost:8000", help="ContextForge API URL")
    parser.add_argument("--interval", type=int, default=2, help="Update interval in seconds")
    
    args = parser.parse_args()
    
    monitor = ContextForgeMonitor(api_url=args.url)
    monitor.update_interval = args.interval
    
    console.print(Panel(
        "[bold blue]ContextForge Real-time Monitoring Dashboard[/bold blue]\n"
        f"API URL: {args.url}\n"
        f"Update Interval: {args.interval}s\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        title="🔍 Monitor Starting",
        border_style="blue"
    ))
    
    try:
        await monitor.run_dashboard()
    except Exception as e:
        console.print(f"[bold red]Monitoring error: {str(e)}[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
