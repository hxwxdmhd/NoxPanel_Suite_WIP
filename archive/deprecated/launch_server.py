import subprocess
import sys
import os

# Change to project directory
os.chdir("k:\\Project Heimnetz")

# Start the ultra-fast server
print("🚀 Launching Ultra-Fast Server...")
try:
    process = subprocess.Popen([sys.executable, "ultra_fast_server.py"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
    print(f"✅ Server started with PID: {process.pid}")
    print("🌐 Server should be running on http://localhost:5000")
    
    # Give it a moment to start
    import time
    time.sleep(2)
    
    # Check if it's running
    import requests
    try:
        response = requests.get("http://localhost:5000/health", timeout=1)
        print(f"✅ Server responding: {response.status_code}")
    except:
        print("⚠️ Server may still be starting...")
        
except Exception as e:
    print(f"❌ Error starting server: {e}")

print("🔄 You can now run the Gate 3 audit!")
