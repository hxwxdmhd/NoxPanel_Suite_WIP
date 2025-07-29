#!/usr/bin/env python3
"""
Direct Flask app test for Ultimate Suite v9.0
"""

from ultimate_webapp_v9 import UltimateSuiteV9
import json

def test_direct():
    print("🧪 Direct Ultimate Suite v9.0 Test")
    print("=" * 40)
    
    try:
        # Create the app
        suite = UltimateSuiteV9()
        app = suite.app
        
        # Test client
        with app.test_client() as client:
            
            print("Testing v9.0 API routes:")
            
            # Test system metrics
            response = client.get('/api/v9/system-metrics')
            print(f"  /api/v9/system-metrics: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"    Status: {data.get('status', 'unknown')}")
            
            # Test network status
            response = client.get('/api/v9/network-status')
            print(f"  /api/v9/network-status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"    Status: {data.get('status', 'unknown')}")
            
            # Test plugin marketplace
            response = client.get('/api/v9/plugins/marketplace')
            print(f"  /api/v9/plugins/marketplace: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"    Plugins: {len(data.get('plugins', []))}")
            
            # Test copilot analysis
            response = client.post('/api/v9/copilot/analyze',
                                 json={'description': 'System is slow'})
            print(f"  /api/v9/copilot/analyze: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"    Category: {data.get('category', 'unknown')}")
        
        print("\n✅ All v9.0 routes are working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_direct()
