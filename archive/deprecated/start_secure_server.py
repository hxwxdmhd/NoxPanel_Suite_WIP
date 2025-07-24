import subprocess
import sys
import os
import time

# Change to project directory
os.chdir("k:\\Project Heimnetz")

# Start the ultra-secure server
print("Starting Ultra-Secure Server...")
try:
    process = subprocess.Popen([sys.executable, "ultra_secure_server.py"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
    print(f"Server started with PID: {process.pid}")
    print("Server should be running on http://127.0.0.1:5000")
    
    # Give it a moment to start
    time.sleep(3)
    
    # Check if it's running
    import requests
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=2)
        print(f"Server responding: {response.status_code}")
        print("Ready for security testing!")
    except Exception as e:
        print(f"Connection test failed: {e}")
        stdout, stderr = process.communicate(timeout=1)
        if stderr:
            print(f"Server error: {stderr}")
        
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
