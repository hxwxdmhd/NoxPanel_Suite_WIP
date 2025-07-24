#!/usr/bin/env python3
"""
Simple Performance Test - NoxPanel Optimization Validation
==========================================================
"""

import requests
import json
import time
from datetime import datetime

def test_performance_dashboard():
    """Test the performance dashboard endpoints"""
    
    print("🚀 Testing NoxPanel Performance Dashboard")
    print("=" * 50)
    
    server_url = 'http://localhost:5000'
    
    # Test endpoints
    endpoints = [
        '/',
        '/api/health',
        '/api/optimization/summary'
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔍 Testing {endpoint}...")
            start_time = time.time()
            
            response = requests.get(f"{server_url}{endpoint}", timeout=5)
            response_time = time.time() - start_time
            
            print(f"  ✅ Status: {response.status_code}")
            print(f"  ⏱️  Response Time: {response_time:.3f}s")
            
            if endpoint != '/':
                try:
                    data = response.json()
                    print(f"  📊 Data Keys: {list(data.keys())}")
                except:
                    print(f"  📄 Content Length: {len(response.text)} chars")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Performance Dashboard Test Complete!")
    print(f"🌐 Access full dashboard at: {server_url}")
    print("📊 Real-time metrics available")

if __name__ == '__main__':
    test_performance_dashboard()
