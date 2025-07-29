
def get_docker_status():
    """Get Docker container status with error handling"""
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        status = {
            "docker_available": True,
            "containers": [],
            "running_count": 0,
            "total_count": len(containers)
        }
        
        for container in containers:
            container_info = {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown"
            }
            status["containers"].append(container_info)
            if container.status == "running":
                status["running_count"] += 1
        
        return status
        
    except Exception as e:
        return {
            "docker_available": False,
            "error": str(e),
            "containers": [],
            "running_count": 0,
            "total_count": 0
        }
