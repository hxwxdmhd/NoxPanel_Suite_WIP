#!/usr/bin/env python3
"""
KeePass Database Selection Test
===============================

Interactive test for KeePass database selection functionality.
This script demonstrates the enhanced database selection feature.

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import os
import sys

# Add plugin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from keepass_helper import create_keepass_helper

def test_keepass_selection():
    """Test KeePass database selection"""
    print("🔐 KeePass Database Selection Test")
    print("=" * 40)
    
    # Create KeePass helper with interactive selection
    config = {
        'use_cli': False,
        'use_browser_integration': False,
        'database_path': None  # Force interactive selection
    }
    
    print("\n🔍 Testing KeePass database selection...")
    
    try:
        keepass_helper = create_keepass_helper(config)
        
        if keepass_helper.database_path:
            print(f"✅ Selected database: {keepass_helper.database_path}")
            print(f"   Database name: {os.path.basename(keepass_helper.database_path)}")
            print(f"   Database exists: {os.path.exists(keepass_helper.database_path)}")
            
            # Test credential retrieval (will prompt for password)
            print("\n🔑 Testing credential retrieval...")
            print("   (This will prompt for your master password)")
            
            credentials = keepass_helper.get_credentials("test_entry")
            if credentials:
                print(f"   ✅ Credentials retrieved successfully")
                print(f"   Username: {credentials.get('username', 'N/A')}")
                print(f"   Password: {'*' * len(credentials.get('password', ''))}")
            else:
                print("   ℹ️  No credentials found for 'test_entry' (this is expected)")
                
        else:
            print("❌ No database selected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_keepass_selection()
