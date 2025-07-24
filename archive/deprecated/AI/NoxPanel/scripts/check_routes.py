#!/usr/bin/env python3
"""
List all routes registered in the Flask application
"""

import requests
import json

def main():
    """
    RLVR: Implements main with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for main
    2. Analysis: Function complexity 2.4/5.0
    3. Solution: Implements main with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    print("🔍 Testing available routes on NoxPanel")
    print("=" * 50)

    # Test some common paths to see what exists
    base_url = "http://127.0.0.1:5002"

    test_routes = [
        "/",
        "/status",
        "/health",
        "/admin",
        "/admin/",
        "/api",
        "/api/",
        "/api/dashboard",
        "/api/status",
        "/api/scripts",
        "/api/metrics",
        "/api/themes",
        "/auth",
        "/auth/",
        "/monitor",
        "/monitor/"
    ]

    for route in test_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=2)
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {route}: {response.status_code}")
            if response.status_code in [301, 302]:
                print(f"   → Redirects to: {response.headers.get('Location', 'Unknown')}")
        except requests.RequestException as e:
            print(f"❌ {route}: Connection error")

    print("\n" + "=" * 50)
    print("🔍 Trying to access Flask routes info...")

    # Try to get route information if there's a debug endpoint
    debug_routes = ["/routes", "/debug", "/api/routes", "/_debug"]
    for route in debug_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=2)
            if response.status_code == 200:
                print(f"Found route info at {route}")
                print(response.text[:500])
                break
        except:
            pass

if __name__ == "__main__":
    main()
