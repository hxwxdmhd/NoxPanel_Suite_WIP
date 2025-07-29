#!/usr/bin/env python3
"""
NoxSuite Docker Status Monitor
Provides Docker integration for the MCP Autonomous Agent
"""
import docker
import json
from datetime import datetime

def get_docker_status():
    """Get comprehensive Docker status"""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "docker_available": True,
            "containers": [],
            "running_count": 0,
            "stopped_count": 0,
            "total_count": len(containers),
            "system_info": {}
        }
        
        # Get system info
        try:
            info = client.info()
            status["system_info"] = {
                "containers_running": info.get('ContainersRunning', 0),
                "containers_paused": info.get('ContainersPaused', 0),
                "containers_stopped": info.get('ContainersStopped', 0),
                "images": info.get('Images', 0),
                "docker_version": info.get('ServerVersion', 'unknown')
            }
        except:
            pass
        
        # Get container details
        for container in containers:
            container_info = {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "ports": container.ports if hasattr(container, 'ports') else {},
                "labels": container.labels if hasattr(container, 'labels') else {}
            }
            status["containers"].append(container_info)
            
            if container.status == "running":
                status["running_count"] += 1
            else:
                status["stopped_count"] += 1
        
        return status
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "docker_available": False,
            "error": str(e),
            "containers": [],
            "running_count": 0,
            "stopped_count": 0,
            "total_count": 0
        }

def docker_health_check():
    """Quick Docker health check"""
    status = get_docker_status()
    
    if status["docker_available"]:
        print(f"✅ Docker Operational - {status['running_count']}/{status['total_count']} containers running")
        return True
    else:
        print(f"❌ Docker Issue: {status.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    status = get_docker_status()
    print(json.dumps(status, indent=2))
