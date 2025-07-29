#!/usr/bin/env python3
"""
NoxSuite CLI - Command Line Interface for NoxSuite Management
Intelligent command-line tool for managing the complete NoxSuite ecosystem
"""

import os
import sys
import json
import click
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoxSuiteCLI:
    """NoxSuite command-line interface"""
    
    def __init__((self) -> None:
        self.config_path = self._find_config()
        self.config = self._load_config()
        
    def _find_config(self) -> Optional[Path]:
        """Find NoxSuite configuration file"""
        possible_paths = [
            Path.cwd() / "config" / "noxsuite.json",
            Path.home() / "noxsuite" / "config" / "noxsuite.json",
            Path.home() / "NoxSuite" / "config" / "noxsuite.json",
            Path("/opt/noxsuite/config/noxsuite.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
    
    def _load_config(self) -> Dict:
        """Load NoxSuite configuration"""
        if not self.config_path:
            return {"installation": {"directory": str(Path.cwd())}}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {"installation": {"directory": str(Path.cwd())}}
    
    @property
    def install_dir(self) -> Path:
        """Get installation directory"""
        return Path(self.config.get("installation", {}).get("directory", Path.cwd()))
    
    def run_docker_compose(self, command: str, services: List[str] = None, profiles: List[str] = None) -> bool:
        """Run docker-compose command"""
        compose_file = self.install_dir / "docker-compose.noxsuite.yml"
        if not compose_file.exists():
            click.echo("❌ Docker compose file not found. Run installation first.")
            return False
            
        cmd = ["docker-compose", "-f", str(compose_file)]
        
        if profiles:
            for profile in profiles:
                cmd.extend(["--profile", profile])
                
        cmd.extend(command.split())
        
        if services:
            cmd.extend(services)
            
        try:
            result = subprocess.run(cmd, cwd=self.install_dir, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Command failed: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """Get status of all services"""
        try:
            # Check core API
            api_status = self._check_endpoint("http://localhost:8000/api/health")
            ui_status = self._check_endpoint("http://localhost:3000")
            grafana_status = self._check_endpoint("http://localhost:3001")
            
            # Check AI services if enabled
            ai_status = {}
            if self.config.get("features", {}).get("ai_enabled", False):
                ai_status = {
                    "ollama": self._check_endpoint("http://localhost:11434/api/version"),
                    "langflow": self._check_endpoint("http://localhost:7860/health")
                }
            
            return {
                "core_services": {
                    "api": api_status,
                    "ui": ui_status,
                    "grafana": grafana_status
                },
                "ai_services": ai_status,
                "database": self._check_database(),
                "redis": self._check_redis()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _check_endpoint(self, url: str, timeout: int = 5) -> Dict:
        """Check if endpoint is responding"""
        try:
            response = requests.get(url, timeout=timeout)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException:
            return {"status": "unreachable"}
    
    def _check_database(self) -> Dict:
        """Check database connectivity"""
        try:
            # Simple docker exec to check postgres
            result = subprocess.run([
                "docker", "exec", "noxsuite-postgres", 
                "pg_isready", "-U", "postgres", "-d", "noxsuite"
            ], capture_output=True, text=True)
            
            return {
                "status": "healthy" if result.returncode == 0 else "unhealthy",
                "message": result.stdout.strip()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_redis(self) -> Dict:
        """Check Redis connectivity"""
        try:
            result = subprocess.run([
                "docker", "exec", "noxsuite-redis", 
                "redis-cli", "ping"
            ], capture_output=True, text=True)
            
            return {
                "status": "healthy" if "PONG" in result.stdout else "unhealthy",
                "message": result.stdout.strip()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# CLI Commands
@click.group()
@click.version_option(version="2.0.0", prog_name="NoxSuite CLI")
def cli() -> bool:
    """🧠 NoxSuite CLI - AI-Powered Infrastructure Management"""
    pass

@cli.command()
@click.option('--profile', '-p', multiple=True, help='Docker compose profiles to include')
@click.option('--detach', '-d', is_flag=True, default=True, help='Run in detached mode')
def start(profile, detach) -> bool:
    """🚀 Start NoxSuite services"""
    nox = NoxSuiteCLI()
    
    click.echo("🧠 Starting NoxSuite + AI Dev Infrastructure...")
    click.echo("=" * 50)
    
    profiles = list(profile) if profile else ['ai']
    
    if detach:
        success = nox.run_docker_compose("up -d", profiles=profiles)
    else:
        success = nox.run_docker_compose("up", profiles=profiles)
    
    if success:
        click.echo("\n✅ NoxSuite services starting...")
        click.echo("🌐 Web UI: http://localhost:3000")
        click.echo("🔧 API Docs: http://localhost:8000/api/docs")
        click.echo("📊 Grafana: http://localhost:3001")
        if 'ai' in profiles:
            click.echo("🤖 Langflow: http://localhost:7860")
            click.echo("🦙 Ollama: http://localhost:11434")
    else:
        click.echo("❌ Failed to start services")

@cli.command()
@click.option('--all', '-a', is_flag=True, help='Stop all services including volumes')
def stop(all) -> bool:
    """🛑 Stop NoxSuite services"""
    nox = NoxSuiteCLI()
    
    click.echo("🛑 Stopping NoxSuite services...")
    
    if all:
        success = nox.run_docker_compose("down -v")
        click.echo("🗑️  Removing volumes...")
    else:
        success = nox.run_docker_compose("stop")
    
    if success:
        click.echo("✅ NoxSuite services stopped")
    else:
        click.echo("❌ Failed to stop services")

@cli.command()
def restart() -> bool:
    """🔄 Restart NoxSuite services"""
    nox = NoxSuiteCLI()
    
    click.echo("🔄 Restarting NoxSuite services...")
    
    # Stop services
    nox.run_docker_compose("stop")
    time.sleep(2)
    
    # Start services with AI profile by default
    success = nox.run_docker_compose("up -d", profiles=['ai'])
    
    if success:
        click.echo("✅ NoxSuite services restarted")
        click.echo("⏳ Services are initializing, please wait...")
    else:
        click.echo("❌ Failed to restart services")

@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def status(output_json) -> bool:
    """📊 Show NoxSuite system status"""
    nox = NoxSuiteCLI()
    
    if not output_json:
        click.echo("🧠 NoxSuite System Status")
        click.echo("=" * 30)
    
    status_data = nox.get_service_status()
    
    if output_json:
        click.echo(json.dumps(status_data, indent=2))
        return
    
    # Core Services
    core = status_data.get("core_services", {})
    click.echo(f"🌐 Web UI: {_status_icon(core.get('ui', {}).get('status'))}")
    click.echo(f"🔧 API: {_status_icon(core.get('api', {}).get('status'))}")
    click.echo(f"📊 Grafana: {_status_icon(core.get('grafana', {}).get('status'))}")
    
    # Database
    db = status_data.get("database", {})
    click.echo(f"🗄️  Database: {_status_icon(db.get('status'))}")
    
    # Redis
    redis = status_data.get("redis", {})
    click.echo(f"⚡ Redis: {_status_icon(redis.get('status'))}")
    
    # AI Services
    ai_services = status_data.get("ai_services", {})
    if ai_services:
        click.echo("\n🤖 AI Services:")
        for service, status in ai_services.items():
            click.echo(f"   {service}: {_status_icon(status.get('status'))}")

def _status_icon(status) -> bool:
    """Get status icon"""
    icons = {
        "healthy": "✅ Healthy",
        "unhealthy": "⚠️  Unhealthy", 
        "unreachable": "❌ Unreachable",
        "error": "💥 Error"
    }
    return icons.get(status, "❓ Unknown")

@cli.command()
@click.argument('service')
def logs(service) -> bool:
    """📋 Show logs for a specific service"""
    nox = NoxSuiteCLI()
    
    click.echo(f"📋 Showing logs for {service}...")
    
    success = nox.run_docker_compose(f"logs -f", services=[service])
    if not success:
        click.echo(f"❌ Failed to show logs for {service}")

@cli.command()
def ps() -> bool:
    """📋 List running services"""
    nox = NoxSuiteCLI()
    
    click.echo("📋 NoxSuite Services:")
    nox.run_docker_compose("ps")

@cli.command()
@click.argument('model')
def install_model(model) -> bool:
    """🤖 Install AI model via Ollama"""
    click.echo(f"🤖 Installing AI model: {model}")
    
    try:
        # Pull model via Ollama container
        result = subprocess.run([
            "docker", "exec", "noxsuite-ollama",
            "ollama", "pull", model
        ], check=True)
        
        click.echo(f"✅ Model {model} installed successfully")
    except subprocess.CalledProcessError:
        click.echo(f"❌ Failed to install model {model}")

@cli.command()
def list_models() -> bool:
    """🤖 List installed AI models"""
    click.echo("🤖 Installed AI Models:")
    
    try:
        result = subprocess.run([
            "docker", "exec", "noxsuite-ollama",
            "ollama", "list"
        ], capture_output=True, text=True, check=True)
        
        click.echo(result.stdout)
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to list models (Ollama not running?)")

@cli.command()
@click.option('--backup-name', help='Name for the backup')
def backup(backup_name) -> bool:
    """💾 Backup NoxSuite data"""
    nox = NoxSuiteCLI()
    
    if not backup_name:
        backup_name = f"noxsuite-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    click.echo(f"💾 Creating backup: {backup_name}")
    
    backup_dir = nox.install_dir / "backups" / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup configuration
    config_backup = backup_dir / "config"
    config_backup.mkdir(exist_ok=True)
    
    # Copy config files
    config_files = ["config/noxsuite.json", ".env", "docker-compose.noxsuite.yml"]
    for config_file in config_files:
        src = nox.install_dir / config_file
        if src.exists():
            import shutil
            shutil.copy2(src, config_backup / src.name)
    
    # Database backup
    click.echo("📊 Backing up database...")
    try:
        subprocess.run([
            "docker", "exec", "noxsuite-postgres",
            "pg_dump", "-U", "postgres", "-d", "noxsuite",
            "-f", f"/tmp/{backup_name}.sql"
        ], check=True)
        
        subprocess.run([
            "docker", "cp", f"noxsuite-postgres:/tmp/{backup_name}.sql",
            str(backup_dir / "database.sql")
        ], check=True)
        
        click.echo(f"✅ Backup created: {backup_dir}")
    except subprocess.CalledProcessError:
        click.echo("❌ Database backup failed")

@cli.command()
@click.argument('backup_name')
def restore(backup_name) -> bool:
    """🔄 Restore NoxSuite from backup"""
    nox = NoxSuiteCLI()
    
    backup_dir = nox.install_dir / "backups" / backup_name
    if not backup_dir.exists():
        click.echo(f"❌ Backup {backup_name} not found")
        return
    
    click.echo(f"🔄 Restoring from backup: {backup_name}")
    
    # Restore database
    db_backup = backup_dir / "database.sql"
    if db_backup.exists():
        click.echo("📊 Restoring database...")
        try:
            subprocess.run([
                "docker", "cp", str(db_backup),
                "noxsuite-postgres:/tmp/restore.sql"
            ], check=True)
            
            subprocess.run([
                "docker", "exec", "noxsuite-postgres",
                "psql", "-U", "postgres", "-d", "noxsuite",
                "-f", "/tmp/restore.sql"
            ], check=True)
            
            click.echo("✅ Database restored")
        except subprocess.CalledProcessError:
            click.echo("❌ Database restore failed")

@cli.command()
def health() -> bool:
    """🏥 Run comprehensive health check"""
    nox = NoxSuiteCLI()
    
    click.echo("🏥 NoxSuite Health Check")
    click.echo("=" * 25)
    
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        click.echo("✅ Docker: Available")
    except:
        click.echo("❌ Docker: Not available")
        return
    
    # Check services
    status_data = nox.get_service_status()
    
    # Overall health score
    healthy_count = 0
    total_count = 0
    
    for category, services in status_data.items():
        if category == "error":
            continue
            
        if isinstance(services, dict):
            for service, status in services.items():
                total_count += 1
                if isinstance(status, dict) and status.get("status") == "healthy":
                    healthy_count += 1
    
    health_score = (healthy_count / total_count * 100) if total_count > 0 else 0
    
    click.echo(f"\n🎯 Overall Health Score: {health_score:.1f}%")
    
    if health_score >= 90:
        click.echo("🎉 System is healthy!")
    elif health_score >= 70:
        click.echo("⚠️  System has minor issues")
    else:
        click.echo("💥 System needs attention")

@cli.command()
def update() -> bool:
    """🔄 Update NoxSuite to latest version"""
    nox = NoxSuiteCLI()
    
    click.echo("🔄 Updating NoxSuite...")
    
    # Pull latest images
    click.echo("📦 Pulling latest Docker images...")
    if nox.run_docker_compose("pull"):
        click.echo("✅ Images updated")
        
        # Restart services
        click.echo("🔄 Restarting services...")
        if nox.run_docker_compose("up -d", profiles=['ai']):
            click.echo("✅ NoxSuite updated successfully")
        else:
            click.echo("❌ Failed to restart services")
    else:
        click.echo("❌ Failed to update images")

@cli.command()
@click.option('--output', '-o', help='Output file for report')
def report(output) -> bool:
    """📊 Generate system report"""
    nox = NoxSuiteCLI()
    
    click.echo("📊 Generating system report...")
    
    # Collect system information
    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "noxsuite_version": "2.0.0",
        "config": nox.config,
        "status": nox.get_service_status(),
        "docker_info": _get_docker_info(),
        "system_resources": _get_system_resources()
    }
    
    # Output report
    if output:
        with open(output, 'w') as f:
            json.dump(report_data, f, indent=2)
        click.echo(f"✅ Report saved to {output}")
    else:
        click.echo(json.dumps(report_data, indent=2))

def _get_docker_info() -> bool:
    """Get Docker system information"""
    try:
        result = subprocess.run(["docker", "system", "info", "--format", "json"], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except:
        return {"error": "Could not get Docker info"}

def _get_system_resources() -> bool:
    """Get system resource information"""
    try:
        # Get container stats
        result = subprocess.run(["docker", "stats", "--no-stream", "--format", 
                               "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"], 
                              capture_output=True, text=True)
        return {"docker_stats": result.stdout}
    except:
        return {"error": "Could not get system resources"}

if __name__ == '__main__':
    cli()
