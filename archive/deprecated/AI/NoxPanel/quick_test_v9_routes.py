#!/usr/bin/env python3
"""
Quick test to check if v9.0 API routes are working
"""

import time
import subprocess
import requests
import sys

def test_webapp():
    print("🚀 Starting Ultimate Suite v9.0 for quick test...")
    
    # Start webapp
    process = subprocess.Popen([
        sys.executable, "launch_ultimate_suite_v9_fixed.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(8)
    
    try:
        # Test the new v9.0 routes
        base_url = "http://127.0.0.1:5000"
        
        print("🧪 Testing v9.0 API routes...")
        
        routes_to_test = [
            "/api/v9/system-metrics",
            "/api/v9/network-status", 
            "/api/v9/plugins/marketplace"
        ]
        
        for route in routes_to_test:
            try:
                response = requests.get(f"{base_url}{route}", timeout=5)
                print(f"✅ {route}: HTTP {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response: {type(data)} with {len(data)} fields")
                else:
                    print(f"   Error: {response.text[:100]}")
            except Exception as e:
                print(f"❌ {route}: {e}")
        
        # Test POST route
        try:
            response = requests.post(f"{base_url}/api/v9/copilot/analyze", 
                                   json={'description': 'Test issue'}, timeout=5)
            print(f"✅ /api/v9/copilot/analyze: HTTP {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Analysis: {data.get('category', 'N/A')}")
        except Exception as e:
            print(f"❌ /api/v9/copilot/analyze: {e}")
            
    finally:
        # Stop webapp
        try:
            process.terminate()
            process.wait(timeout=5)
            print("🛑 Webapp stopped")
        except:
            process.kill()
            print("🛑 Webapp force-stopped")

if __name__ == "__main__":
    test_webapp()
