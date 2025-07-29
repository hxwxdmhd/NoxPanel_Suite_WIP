#!/usr/bin/env python3
"""
Simple test to start ultra_fast_server.py with error handling
"""
import subprocess
import sys
import os
import time

print("🔧 Testing server startup...")

try:
    # Change to correct directory
    os.chdir("k:\\Project Heimnetz")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check if the server file exists
    if os.path.exists("ultra_fast_server.py"):
        print("✅ ultra_fast_server.py found")
    else:
        print("❌ ultra_fast_server.py not found")
        sys.exit(1)
    
    # Try to start the server
    print("🚀 Starting server...")
    process = subprocess.Popen(
        [sys.executable, "ultra_fast_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"🆔 Server PID: {process.pid}")
    
    # Wait a bit and check if it's still running
    time.sleep(3)
    
    if process.poll() is None:
        print("✅ Server appears to be running")
        
        # Test connection
        try:
            import requests
            response = requests.get("http://localhost:5000/health", timeout=2)
            print(f"🌐 Server responding: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Connection test failed: {e}")
            
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Server exited with code: {process.returncode}")
        print(f"📤 STDOUT: {stdout}")
        print(f"📤 STDERR: {stderr}")

except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Done")
