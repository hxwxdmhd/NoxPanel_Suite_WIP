#!/usr/bin/env python3
"""
Docker Integration Fix and Test Script
Diagnoses and repairs Docker SDK issues for NoxSuite MCP Agent
"""
import subprocess
import sys
import os

def check_docker_daemon():
    """Check if Docker daemon is running"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker daemon is running")
            return True
        else:
            print("❌ Docker daemon not accessible")
            return False
    except FileNotFoundError:
        print("❌ Docker CLI not found")
        return False

def test_docker_sdk():
    """Test various Docker SDK methods"""
    try:
        # Try importing docker
        import docker
        print("✅ Docker module imported")
        
        # Try different client creation methods
        methods = [
            ("docker.from_env()", lambda: docker.from_env()),
            ("docker.DockerClient()", lambda: docker.DockerClient()),
            ("docker.client.from_env()", lambda: docker.client.from_env()),
        ]
        
        for method_name, method_func in methods:
            try:
                client = method_func()
                containers = client.containers.list()
                print(f"✅ {method_name} works! Found {len(containers)} containers")
                return client
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
        
        return None
        
    except ImportError as e:
        print(f"❌ Docker SDK import failed: {e}")
        return None

def install_correct_docker_sdk():
    """Install the correct Docker SDK"""
    print("🔧 Installing correct Docker SDK...")
    
    # Uninstall conflicting packages
    subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'docker', 'docker-py', 'docker-sdk'])
    
    # Install the correct package
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'docker==7.1.0'])
    
    if result.returncode == 0:
        print("✅ Docker SDK installed successfully")
        return True
    else:
        print("❌ Failed to install Docker SDK")
        return False

def create_docker_wrapper():
    """Create a Docker wrapper function for status monitoring"""
    wrapper_code = '''
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
'''
    
    with open('docker_status_utils.py', 'w') as f:
        f.write(wrapper_code)
    
    print("✅ Created Docker status utility")

def main():
    """Main diagnosis and repair function"""
    print("🐳 Docker Integration Diagnosis & Repair")
    print("=" * 50)
    
    # Check Docker daemon
    if not check_docker_daemon():
        print("⚠️ Cannot proceed without Docker daemon")
        return False
    
    # Test current SDK
    client = test_docker_sdk()
    
    if client is None:
        print("\n🔧 Attempting to fix Docker SDK...")
        if install_correct_docker_sdk():
            client = test_docker_sdk()
    
    if client:
        print("\n✅ DOCKER INTEGRATION SUCCESSFUL!")
        try:
            containers = client.containers.list()
            print(f"📊 Running containers: {len(containers)}")
            for container in containers:
                print(f"   - {container.name}: {container.status}")
        except Exception as e:
            print(f"⚠️ Could not list containers: {e}")
        
        create_docker_wrapper()
        return True
    else:
        print("\n❌ DOCKER INTEGRATION FAILED")
        print("💡 Recommendation: Use Docker CLI fallback for container operations")
        create_docker_wrapper()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
