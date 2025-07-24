"""
FRITZWATCHER UX Customization Layer
===================================

Enhanced user experience features including device customization,
OUI-based device type detection, and ADHD-friendly theme support.

Author: MSP-Aware Development Team
Date: July 19, 2025
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

# OUI (Organizationally Unique Identifier) database for device type detection
DEVICE_OUI_MAP = {
    # Apple devices
    "00:03:93": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:16:CB": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:17:F2": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:19:E3": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:1B:63": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:1E:C2": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:21:E9": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:23:12": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:23:DF": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:25:00": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:25:4B": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:25:BC": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:26:08": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    "00:26:4A": {"type": "smartphone", "brand": "Apple", "icon": "📱"},
    "00:26:B0": {"type": "laptop", "brand": "Apple", "icon": "💻"},
    
    # Samsung devices
    "00:12:FB": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:15:99": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:16:32": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:17:C9": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:1A:8A": {"type": "laptop", "brand": "Samsung", "icon": "💻"},
    "00:1D:25": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:21:19": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:23:39": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    "00:26:37": {"type": "smartphone", "brand": "Samsung", "icon": "📱"},
    
    # Dell computers
    "00:08:74": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:0B:DB": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:0D:56": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:11:43": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:12:3F": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:13:72": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:14:22": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    "00:15:C5": {"type": "laptop", "brand": "Dell", "icon": "💻"},
    
    # HP devices
    "00:01:E6": {"type": "printer", "brand": "HP", "icon": "🖨️"},
    "00:04:EA": {"type": "laptop", "brand": "HP", "icon": "💻"},
    "00:08:02": {"type": "printer", "brand": "HP", "icon": "🖨️"},
    "00:0B:CD": {"type": "laptop", "brand": "HP", "icon": "💻"},
    "00:0E:7F": {"type": "laptop", "brand": "HP", "icon": "💻"},
    "00:10:E3": {"type": "printer", "brand": "HP", "icon": "🖨️"},
    "00:11:0A": {"type": "laptop", "brand": "HP", "icon": "💻"},
    "00:12:79": {"type": "laptop", "brand": "HP", "icon": "💻"},
    
    # Smart TV manufacturers
    "00:09:DF": {"type": "tv", "brand": "LG", "icon": "📺"},
    "00:0D:AE": {"type": "tv", "brand": "Samsung", "icon": "📺"},
    "00:26:E2": {"type": "tv", "brand": "Sony", "icon": "📺"},
    "3C:F0:11": {"type": "tv", "brand": "LG", "icon": "📺"},
    
    # Gaming consoles
    "00:13:12": {"type": "gaming", "brand": "Sony PlayStation", "icon": "🎮"},
    "00:15:5D": {"type": "gaming", "brand": "Microsoft Xbox", "icon": "🎮"},
    "00:17:AB": {"type": "gaming", "brand": "Nintendo", "icon": "🎮"},
    "00:19:FD": {"type": "gaming", "brand": "Sony PlayStation", "icon": "🎮"},
    "00:1B:EA": {"type": "gaming", "brand": "Microsoft Xbox", "icon": "🎮"},
    
    # Smart home devices
    "18:B4:30": {"type": "iot", "brand": "Nest", "icon": "🏠"},
    "50:F5:DA": {"type": "iot", "brand": "Ring", "icon": "🔔"},
    "68:64:4B": {"type": "iot", "brand": "Amazon Echo", "icon": "🔊"},
    "74:C2:46": {"type": "iot", "brand": "TP-Link", "icon": "💡"},
    "B4:E6:2D": {"type": "iot", "brand": "Philips Hue", "icon": "💡"},
}

@dataclass
class DeviceCustomization:
    """Device customization settings"""
    mac_address: str
    custom_name: str = ""
    custom_icon: str = ""
    device_type: str = ""
    brand: str = ""
    color: str = ""
    priority: int = 0
    notes: str = ""
    created_at: datetime = None
    updated_at: datetime = None

@dataclass 
class ThemeSettings:
    """Theme configuration for ADHD-friendly UX"""
    theme_name: str
    high_contrast: bool = False
    animated_elements: bool = False
    color_scheme: str = "default"
    font_size: str = "normal"
    motion_sensitivity: str = "normal"
    focus_indicators: bool = True
    sound_enabled: bool = False

class DeviceCustomizationManager:
    """Manage device customization and labeling"""
    
    def __init__(self, db_path: str = "fritzwatcher_customization.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the customization database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_customizations (
                    mac_address TEXT PRIMARY KEY,
                    custom_name TEXT,
                    custom_icon TEXT,
                    device_type TEXT,
                    brand TEXT,
                    color TEXT,
                    priority INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS theme_settings (
                    user_id TEXT PRIMARY KEY,
                    theme_name TEXT DEFAULT 'default',
                    high_contrast BOOLEAN DEFAULT FALSE,
                    animated_elements BOOLEAN DEFAULT FALSE,
                    color_scheme TEXT DEFAULT 'default',
                    font_size TEXT DEFAULT 'normal',
                    motion_sensitivity TEXT DEFAULT 'normal',
                    focus_indicators BOOLEAN DEFAULT TRUE,
                    sound_enabled BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing customization database: {e}")
    
    def get_device_info_from_oui(self, mac_address: str) -> Dict[str, str]:
        """Get device information from OUI (MAC address prefix)"""
        if not mac_address or len(mac_address) < 8:
            return {"type": "unknown", "brand": "Unknown", "icon": "❓"}
        
        # Extract OUI (first 3 octets)
        oui = mac_address.upper()[:8]  # XX:XX:XX format
        
        device_info = DEVICE_OUI_MAP.get(oui, {
            "type": "unknown", 
            "brand": "Unknown", 
            "icon": "❓"
        })
        
        return device_info
    
    def auto_detect_device_type(self, mac_address: str, hostname: str = "") -> Dict[str, str]:
        """Auto-detect device type using OUI and hostname hints"""
        # Start with OUI lookup
        device_info = self.get_device_info_from_oui(mac_address)
        
        # Enhance with hostname analysis
        hostname_lower = hostname.lower()
        
        # Smartphone indicators
        if any(word in hostname_lower for word in ['iphone', 'android', 'phone', 'mobile']):
            device_info.update({"type": "smartphone", "icon": "📱"})
        
        # Laptop/Computer indicators  
        elif any(word in hostname_lower for word in ['laptop', 'macbook', 'thinkpad', 'pc', 'desktop']):
            device_info.update({"type": "laptop", "icon": "💻"})
        
        # TV indicators
        elif any(word in hostname_lower for word in ['tv', 'roku', 'chromecast', 'appletv', 'firetv']):
            device_info.update({"type": "tv", "icon": "📺"})
        
        # Printer indicators
        elif any(word in hostname_lower for word in ['printer', 'print', 'hp-', 'canon', 'epson']):
            device_info.update({"type": "printer", "icon": "🖨️"})
        
        # Gaming console indicators
        elif any(word in hostname_lower for word in ['xbox', 'playstation', 'ps4', 'ps5', 'nintendo']):
            device_info.update({"type": "gaming", "icon": "🎮"})
        
        # Smart home indicators
        elif any(word in hostname_lower for word in ['echo', 'alexa', 'nest', 'ring', 'hue', 'smart']):
            device_info.update({"type": "iot", "icon": "🏠"})
        
        # Tablet indicators
        elif any(word in hostname_lower for word in ['ipad', 'tablet', 'surface']):
            device_info.update({"type": "tablet", "icon": "📟"})
        
        return device_info
    
    def save_device_customization(self, customization: DeviceCustomization):
        """Save device customization to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO device_customizations 
                (mac_address, custom_name, custom_icon, device_type, brand, color, priority, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                customization.mac_address,
                customization.custom_name,
                customization.custom_icon, 
                customization.device_type,
                customization.brand,
                customization.color,
                customization.priority,
                customization.notes
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved customization for device {customization.mac_address}")
            
        except Exception as e:
            logger.error(f"Error saving device customization: {e}")
    
    def get_device_customization(self, mac_address: str) -> Optional[DeviceCustomization]:
        """Get device customization from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM device_customizations WHERE mac_address = ?
            """, (mac_address,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return DeviceCustomization(
                    mac_address=row[0],
                    custom_name=row[1],
                    custom_icon=row[2],
                    device_type=row[3],
                    brand=row[4],
                    color=row[5],
                    priority=row[6],
                    notes=row[7],
                    created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting device customization: {e}")
            return None
    
    def get_enhanced_device_info(self, mac_address: str, hostname: str = "", ip_address: str = "") -> Dict[str, Any]:
        """Get enhanced device information with auto-detection and customization"""
        # Check for existing customization
        customization = self.get_device_customization(mac_address)
        
        if customization:
            # Use customized information
            return {
                "mac_address": mac_address,
                "hostname": hostname,
                "ip_address": ip_address,
                "display_name": customization.custom_name or hostname,
                "icon": customization.custom_icon,
                "device_type": customization.device_type,
                "brand": customization.brand,
                "color": customization.color,
                "priority": customization.priority,
                "notes": customization.notes,
                "is_customized": True
            }
        else:
            # Auto-detect device information
            auto_info = self.auto_detect_device_type(mac_address, hostname)
            
            return {
                "mac_address": mac_address,
                "hostname": hostname,
                "ip_address": ip_address,
                "display_name": hostname,
                "icon": auto_info.get("icon", "❓"),
                "device_type": auto_info.get("type", "unknown"),
                "brand": auto_info.get("brand", "Unknown"),
                "color": "",
                "priority": 0,
                "notes": "",
                "is_customized": False
            }

class ThemeManager:
    """Manage ADHD-friendly theme settings"""
    
    PREDEFINED_THEMES = {
        "spicy": ThemeSettings(
            theme_name="spicy",
            high_contrast=True,
            animated_elements=True,
            color_scheme="high_contrast",
            font_size="large",
            motion_sensitivity="high",
            focus_indicators=True,
            sound_enabled=True
        ),
        "steady": ThemeSettings(
            theme_name="steady",
            high_contrast=False,
            animated_elements=False,
            color_scheme="muted",
            font_size="normal",
            motion_sensitivity="low",
            focus_indicators=True,
            sound_enabled=False
        ),
        "default": ThemeSettings(
            theme_name="default",
            high_contrast=False,
            animated_elements=False,
            color_scheme="default",
            font_size="normal",
            motion_sensitivity="normal",
            focus_indicators=True,
            sound_enabled=False
        )
    }
    
    def __init__(self, db_path: str = "fritzwatcher_customization.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the theme database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS theme_settings (
                    user_id TEXT PRIMARY KEY,
                    theme_name TEXT DEFAULT 'default',
                    high_contrast BOOLEAN DEFAULT FALSE,
                    animated_elements BOOLEAN DEFAULT FALSE,
                    color_scheme TEXT DEFAULT 'default',
                    font_size TEXT DEFAULT 'normal',
                    motion_sensitivity TEXT DEFAULT 'normal',
                    focus_indicators BOOLEAN DEFAULT TRUE,
                    sound_enabled BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing theme database: {e}")
    
    def save_theme_settings(self, user_id: str, settings: ThemeSettings):
        """Save theme settings for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO theme_settings 
                (user_id, theme_name, high_contrast, animated_elements, color_scheme, 
                 font_size, motion_sensitivity, focus_indicators, sound_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                settings.theme_name,
                settings.high_contrast,
                settings.animated_elements,
                settings.color_scheme,
                settings.font_size,
                settings.motion_sensitivity,
                settings.focus_indicators,
                settings.sound_enabled
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved theme settings for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving theme settings: {e}")
    
    def get_theme_settings(self, user_id: str) -> ThemeSettings:
        """Get theme settings for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM theme_settings WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ThemeSettings(
                    theme_name=row[1],
                    high_contrast=bool(row[2]),
                    animated_elements=bool(row[3]),
                    color_scheme=row[4],
                    font_size=row[5],
                    motion_sensitivity=row[6],
                    focus_indicators=bool(row[7]),
                    sound_enabled=bool(row[8])
                )
            else:
                # Return default theme
                return self.PREDEFINED_THEMES["default"]
                
        except Exception as e:
            logger.error(f"Error getting theme settings: {e}")
            return self.PREDEFINED_THEMES["default"]
    
    def apply_theme_preset(self, user_id: str, theme_name: str):
        """Apply a predefined theme preset"""
        if theme_name in self.PREDEFINED_THEMES:
            settings = self.PREDEFINED_THEMES[theme_name]
            self.save_theme_settings(user_id, settings)
            return True
        return False
    
    def get_css_variables(self, settings: ThemeSettings) -> Dict[str, str]:
        """Generate CSS variables for theme application"""
        css_vars = {}
        
        # Color scheme
        if settings.color_scheme == "high_contrast":
            css_vars.update({
                "--primary-color": "#ffffff",
                "--secondary-color": "#000000", 
                "--background-color": "#000000",
                "--text-color": "#ffffff",
                "--border-color": "#ffffff",
                "--accent-color": "#ff0000"
            })
        elif settings.color_scheme == "muted":
            css_vars.update({
                "--primary-color": "#6b7280",
                "--secondary-color": "#9ca3af",
                "--background-color": "#f9fafb",
                "--text-color": "#374151",
                "--border-color": "#d1d5db",
                "--accent-color": "#4f46e5"
            })
        else:  # default
            css_vars.update({
                "--primary-color": "#3b82f6",
                "--secondary-color": "#6366f1",
                "--background-color": "#ffffff",
                "--text-color": "#1f2937",
                "--border-color": "#e5e7eb",
                "--accent-color": "#10b981"
            })
        
        # Font size
        font_multiplier = {"small": "0.8", "normal": "1.0", "large": "1.2", "xl": "1.4"}
        css_vars["--font-size-multiplier"] = font_multiplier.get(settings.font_size, "1.0")
        
        # Animation settings
        if settings.animated_elements:
            css_vars["--animation-duration"] = "0.3s"
            css_vars["--animation-easing"] = "ease-in-out"
        else:
            css_vars["--animation-duration"] = "0s"
            css_vars["--animation-easing"] = "linear"
        
        # Focus indicators
        if settings.focus_indicators:
            css_vars["--focus-outline"] = "2px solid var(--accent-color)"
            css_vars["--focus-shadow"] = "0 0 0 3px rgba(59, 130, 246, 0.1)"
        else:
            css_vars["--focus-outline"] = "none"
            css_vars["--focus-shadow"] = "none"
        
        return css_vars

# Global instances
_device_manager = None
_theme_manager = None

def get_device_manager() -> DeviceCustomizationManager:
    """Get the global device customization manager"""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceCustomizationManager()
    return _device_manager

def get_theme_manager() -> ThemeManager:
    """Get the global theme manager"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
