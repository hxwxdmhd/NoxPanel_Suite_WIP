#!/usr/bin/env python3
"""
Minimal performance test to identify the 2-second delay
"""
import time
import requests

def test_response_speed():
    print("Testing response speed with multiple requests...")
    
    endpoints = [
        "http://localhost:5000/",
        "http://localhost:5000/health",
        "http://localhost:5000/performance"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}:")
        for i in range(3):
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=5)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                print(f"  Request {i+1}: {response_time:.2f}ms (Status: {response.status_code})")
                
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

if __name__ == "__main__":
    test_response_speed()
