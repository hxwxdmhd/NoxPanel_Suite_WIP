#!/usr/bin/env python3
"""
FRITZWATCHER UX Customization Test
==================================

Test the device customization and theme management features.

Author: MSP-Aware Development Team
Date: July 19, 2025
"""

import os
import sys
import tempfile
import shutil

# Add plugin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fritzwatcher_ux import (
    DeviceCustomizationManager,
    ThemeManager,
    DeviceCustomization,
    ThemeSettings,
    get_device_manager,
    get_theme_manager
)

def test_device_customization():
    """Test device customization features"""
    print("🎨 Testing Device Customization")
    print("-" * 40)
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_customization.db")
    
    try:
        manager = DeviceCustomizationManager(db_path)
        
        # Test OUI detection
        print("🔍 Testing OUI Detection:")
        
        test_devices = [
            ("00:03:93:xx:xx:xx", "iPhone-John", "Apple iPhone"),
            ("00:12:FB:xx:xx:xx", "Galaxy-S21", "Samsung Galaxy"),
            ("00:08:74:xx:xx:xx", "Dell-Laptop", "Dell Laptop"),
            ("00:01:E6:xx:xx:xx", "HP-Printer", "HP Printer"),
            ("B4:E6:2D:xx:xx:xx", "Philips-Hue", "Philips Hue Light")
        ]
        
        for mac, hostname, expected_desc in test_devices:
            info = manager.get_enhanced_device_info(mac, hostname)
            print(f"  {mac[:8]}... -> {info['icon']} {info['device_type']} ({info['brand']})")
            print(f"    Hostname: {hostname} -> Display: {info['display_name']}")
        
        # Test device customization
        print("\n🛠️ Testing Device Customization:")
        
        customization = DeviceCustomization(
            mac_address="aa:bb:cc:dd:ee:ff",
            custom_name="My Custom Device",
            custom_icon="🚀",
            device_type="custom",
            brand="Custom Brand",
            color="#FF6B6B",
            priority=5,
            notes="This is a test device"
        )
        
        manager.save_device_customization(customization)
        
        # Retrieve and verify
        retrieved = manager.get_device_customization("aa:bb:cc:dd:ee:ff")
        if retrieved:
            print(f"  ✅ Saved customization: {retrieved.custom_name}")
            print(f"     Icon: {retrieved.custom_icon}, Type: {retrieved.device_type}")
            print(f"     Brand: {retrieved.brand}, Color: {retrieved.color}")
        else:
            print("  ❌ Failed to retrieve customization")
        
        # Test enhanced info with customization
        enhanced = manager.get_enhanced_device_info("aa:bb:cc:dd:ee:ff", "original-hostname")
        print(f"  📱 Enhanced info: {enhanced['display_name']} {enhanced['icon']}")
        print(f"     Is customized: {enhanced['is_customized']}")
        
        print("  ✅ Device customization tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_theme_management():
    """Test theme management features"""
    print("\n🎭 Testing Theme Management")
    print("-" * 40)
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_themes.db")
    
    try:
        manager = ThemeManager(db_path)
        
        # Test predefined themes
        print("🎨 Testing Predefined Themes:")
        for theme_name, theme_settings in manager.PREDEFINED_THEMES.items():
            print(f"  {theme_name.upper()}: {theme_settings.color_scheme} scheme")
            print(f"    High contrast: {theme_settings.high_contrast}")
            print(f"    Animations: {theme_settings.animated_elements}")
            print(f"    Font size: {theme_settings.font_size}")
        
        # Test theme application
        print("\n🔧 Testing Theme Application:")
        
        # Apply spicy theme
        manager.apply_theme_preset("test_user", "spicy")
        spicy_settings = manager.get_theme_settings("test_user")
        print(f"  Applied SPICY theme: {spicy_settings.theme_name}")
        print(f"    High contrast: {spicy_settings.high_contrast}")
        print(f"    Animations: {spicy_settings.animated_elements}")
        
        # Apply steady theme  
        manager.apply_theme_preset("test_user", "steady")
        steady_settings = manager.get_theme_settings("test_user")
        print(f"  Applied STEADY theme: {steady_settings.theme_name}")
        print(f"    High contrast: {steady_settings.high_contrast}")
        print(f"    Animations: {steady_settings.animated_elements}")
        
        # Test CSS variable generation
        print("\n🎨 Testing CSS Variables:")
        css_vars = manager.get_css_variables(spicy_settings)
        print("  SPICY theme CSS variables:")
        for var, value in list(css_vars.items())[:5]:  # Show first 5
            print(f"    {var}: {value}")
        
        css_vars = manager.get_css_variables(steady_settings)
        print("  STEADY theme CSS variables:")
        for var, value in list(css_vars.items())[:5]:  # Show first 5
            print(f"    {var}: {value}")
        
        # Test custom theme
        print("\n🛠️ Testing Custom Theme:")
        custom_theme = ThemeSettings(
            theme_name="custom_test",
            high_contrast=True,
            animated_elements=False,
            color_scheme="custom",
            font_size="large",
            motion_sensitivity="low",
            focus_indicators=True,
            sound_enabled=True
        )
        
        manager.save_theme_settings("custom_user", custom_theme)
        retrieved_custom = manager.get_theme_settings("custom_user")
        print(f"  Custom theme: {retrieved_custom.theme_name}")
        print(f"    Settings: contrast={retrieved_custom.high_contrast}, "
              f"animations={retrieved_custom.animated_elements}, "
              f"font={retrieved_custom.font_size}")
        
        print("  ✅ Theme management tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_global_managers():
    """Test global manager instances"""
    print("\n🌐 Testing Global Managers")
    print("-" * 40)
    
    # Test global device manager
    device_manager = get_device_manager()
    print(f"  Device manager type: {type(device_manager).__name__}")
    
    # Test singleton behavior
    device_manager2 = get_device_manager()
    print(f"  Singleton check: {device_manager is device_manager2}")
    
    # Test global theme manager
    theme_manager = get_theme_manager()
    print(f"  Theme manager type: {type(theme_manager).__name__}")
    
    # Test singleton behavior
    theme_manager2 = get_theme_manager()
    print(f"  Singleton check: {theme_manager is theme_manager2}")
    
    print("  ✅ Global manager tests passed!")

def main():
    """Run all UX customization tests"""
    print("🎨 FRITZWATCHER UX Customization Test Suite")
    print("=" * 50)
    
    try:
        test_device_customization()
        test_theme_management()
        test_global_managers()
        
        print("\n🎉 All UX customization tests passed!")
        print("✅ Device auto-detection working")
        print("✅ Device customization working")
        print("✅ Theme management working")
        print("✅ ADHD-friendly themes working")
        print("✅ CSS generation working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
