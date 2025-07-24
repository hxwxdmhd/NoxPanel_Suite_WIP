#!/usr/bin/env python3
"""
Test localhost vs 127.0.0.1 to identify DNS resolution delay
"""
import time
import requests

def test_localhost_vs_ip():
    print("Testing localhost vs 127.0.0.1 response times...")
    
    tests = [
        "http://localhost:5000/health",
        "http://127.0.0.1:5000/health"
    ]
    
    for url in tests:
        print(f"\nTesting {url}:")
        for i in range(3):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                print(f"  Request {i+1}: {response_time:.2f}ms (Status: {response.status_code})")
                
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

if __name__ == "__main__":
    test_localhost_vs_ip()
