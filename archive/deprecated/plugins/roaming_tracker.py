#!/usr/bin/env python3
"""
Roaming Tracker for FRITZWATCHER
=================================

This module tracks device roaming patterns and handover history
across multiple Fritz!Box routers in a mesh or multi-router setup.

Features:
- Real-time roaming detection
- Handover history tracking
- Device mobility patterns
- Signal strength analysis
- Roaming event notifications
- Performance metrics

Author: MSP-Aware Development Team
Date: July 18, 2025
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
from collections import defaultdict, deque

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RoamingEvent:
    """Represents a device roaming event"""
    timestamp: datetime
    device_mac: str
    device_hostname: str
    device_ip: str
    from_router: str
    to_router: str
    event_type: str  # 'connect', 'disconnect', 'roam', 'handover'
    signal_strength_from: int = 0
    signal_strength_to: int = 0
    duration_at_previous: Optional[float] = None  # seconds
    trigger_reason: str = ""  # 'weak_signal', 'load_balancing', 'manual', 'unknown'
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoamingEvent':
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class DeviceSession:
    """Represents a device session on a specific router"""
    device_mac: str
    device_hostname: str
    device_ip: str
    router_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    signal_strength_history: List[Tuple[datetime, int]] = None
    data_transferred: int = 0  # bytes
    connection_type: str = "unknown"  # 'wifi', 'ethernet', 'guest'
    
    def __post_init__(self):
        if self.signal_strength_history is None:
            self.signal_strength_history = []
            
    def add_signal_measurement(self, strength: int):
        """Add signal strength measurement"""
        self.signal_strength_history.append((datetime.now(), strength))
        
        # Keep only last 100 measurements
        if len(self.signal_strength_history) > 100:
            self.signal_strength_history = self.signal_strength_history[-100:]
            
    def get_average_signal_strength(self) -> float:
        """Get average signal strength"""
        if not self.signal_strength_history:
            return 0.0
        return statistics.mean(strength for _, strength in self.signal_strength_history)
        
    def get_signal_trend(self) -> str:
        """Get signal strength trend"""
        if len(self.signal_strength_history) < 2:
            return "stable"
            
        recent = [s for _, s in self.signal_strength_history[-10:]]
        if len(recent) < 2:
            return "stable"
            
        # Simple trend analysis
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "degrading"
        else:
            return "stable"
            
    def close_session(self):
        """Close the session"""
        self.end_time = datetime.now()
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
            
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        
        # Convert signal history
        data['signal_strength_history'] = [
            (ts.isoformat(), strength) 
            for ts, strength in self.signal_strength_history
        ]
        
        return data


@dataclass
class DeviceProfile:
    """Device mobility profile"""
    mac_address: str
    hostname: str
    device_type: str = "unknown"
    mobility_pattern: str = "static"  # 'static', 'mobile', 'highly_mobile'
    preferred_routers: List[str] = None
    roaming_frequency: float = 0.0  # roams per hour
    average_session_duration: float = 0.0  # seconds
    signal_preference: str = "balanced"  # 'quality', 'coverage', 'balanced'
    
    def __post_init__(self):
        if self.preferred_routers is None:
            self.preferred_routers = []
            
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RoamingTracker:
    """Tracks device roaming across multiple routers"""
    
    def __init__(self, history_file: str = "roaming_history.json"):
        self.history_file = Path(history_file)
        self.events: List[RoamingEvent] = []
        self.active_sessions: Dict[str, DeviceSession] = {}
        self.device_profiles: Dict[str, DeviceProfile] = {}
        
        # Configuration
        self.max_history_days = 30
        self.roaming_threshold_seconds = 5  # Min time between roams
        self.weak_signal_threshold = 30  # dBm
        
        # Statistics
        self.stats = {
            'total_roams': 0,
            'total_devices': 0,
            'active_devices': 0,
            'roaming_devices': 0
        }
        
        # Load existing history
        self.load_history()
        
    def load_history(self):
        """Load roaming history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    
                # Load events
                for event_data in data.get('events', []):
                    event = RoamingEvent.from_dict(event_data)
                    self.events.append(event)
                    
                # Load device profiles
                for profile_data in data.get('device_profiles', []):
                    profile = DeviceProfile(**profile_data)
                    self.device_profiles[profile.mac_address] = profile
                    
                logger.info(f"Loaded {len(self.events)} roaming events and {len(self.device_profiles)} device profiles")
                
                # Update statistics
                self._update_statistics()
                
        except Exception as e:
            logger.error(f"Failed to load roaming history: {e}")
            
    def save_history(self):
        """Save roaming history to file"""
        try:
            # Clean old events
            cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
            self.events = [event for event in self.events if event.timestamp > cutoff_date]
            
            data = {
                'events': [event.to_dict() for event in self.events],
                'device_profiles': [profile.to_dict() for profile in self.device_profiles.values()],
                'statistics': self.stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.events)} roaming events")
            
        except Exception as e:
            logger.error(f"Failed to save roaming history: {e}")
            
    def update_device_locations(self, devices_by_router: Dict[str, List[Any]]):
        """Update device locations and detect roaming"""
        current_time = datetime.now()
        current_devices = {}
        
        # Build current device map
        for router_name, devices in devices_by_router.items():
            for device in devices:
                mac = device.mac_address
                current_devices[mac] = {
                    'router': router_name,
                    'device': device,
                    'timestamp': current_time
                }
                
        # Check for roaming events
        for mac, current_info in current_devices.items():
            device = current_info['device']
            current_router = current_info['router']
            
            # Check if device has active session
            if mac in self.active_sessions:
                active_session = self.active_sessions[mac]
                
                # Check if device has moved to different router
                if active_session.router_name != current_router:
                    # Device has roamed
                    self._handle_roaming_event(
                        device,
                        active_session.router_name,
                        current_router,
                        current_time
                    )
                else:
                    # Update existing session
                    active_session.add_signal_measurement(device.signal_strength)
                    
            else:
                # New device connection
                self._handle_device_connect(device, current_router, current_time)
                
        # Check for disconnected devices
        disconnected_devices = set(self.active_sessions.keys()) - set(current_devices.keys())
        for mac in disconnected_devices:
            self._handle_device_disconnect(mac, current_time)
            
        # Update statistics
        self._update_statistics()
        
    def _handle_device_connect(self, device: Any, router_name: str, timestamp: datetime):
        """Handle device connection"""
        mac = device.mac_address
        
        # Create new session
        session = DeviceSession(
            device_mac=mac,
            device_hostname=device.hostname,
            device_ip=device.ip_address,
            router_name=router_name,
            start_time=timestamp,
            connection_type=device.connection_type
        )
        
        session.add_signal_measurement(device.signal_strength)
        self.active_sessions[mac] = session
        
        # Create roaming event
        event = RoamingEvent(
            timestamp=timestamp,
            device_mac=mac,
            device_hostname=device.hostname,
            device_ip=device.ip_address,
            from_router="",
            to_router=router_name,
            event_type="connect",
            signal_strength_to=device.signal_strength
        )
        
        self.events.append(event)
        
        # Update device profile
        self._update_device_profile(mac, device.hostname, router_name)
        
        logger.info(f"Device {device.hostname} ({mac}) connected to {router_name}")
        
    def _handle_device_disconnect(self, mac: str, timestamp: datetime):
        """Handle device disconnection"""
        if mac in self.active_sessions:
            session = self.active_sessions[mac]
            session.close_session()
            
            # Create roaming event
            event = RoamingEvent(
                timestamp=timestamp,
                device_mac=mac,
                device_hostname=session.device_hostname,
                device_ip=session.device_ip,
                from_router=session.router_name,
                to_router="",
                event_type="disconnect",
                duration_at_previous=session.duration
            )
            
            self.events.append(event)
            
            # Remove active session
            del self.active_sessions[mac]
            
            logger.info(f"Device {session.device_hostname} ({mac}) disconnected from {session.router_name}")
            
    def _handle_roaming_event(self, device: Any, from_router: str, to_router: str, timestamp: datetime):
        """Handle device roaming between routers"""
        mac = device.mac_address
        
        # Close previous session
        if mac in self.active_sessions:
            old_session = self.active_sessions[mac]
            old_session.close_session()
            
            # Determine roaming trigger
            trigger_reason = self._determine_roaming_trigger(old_session, device.signal_strength)
            
            # Create roaming event
            event = RoamingEvent(
                timestamp=timestamp,
                device_mac=mac,
                device_hostname=device.hostname,
                device_ip=device.ip_address,
                from_router=from_router,
                to_router=to_router,
                event_type="roam",
                signal_strength_from=old_session.get_average_signal_strength(),
                signal_strength_to=device.signal_strength,
                duration_at_previous=old_session.duration,
                trigger_reason=trigger_reason
            )
            
            self.events.append(event)
            
            logger.info(f"Device {device.hostname} ({mac}) roamed from {from_router} to {to_router} ({trigger_reason})")
            
        # Create new session
        new_session = DeviceSession(
            device_mac=mac,
            device_hostname=device.hostname,
            device_ip=device.ip_address,
            router_name=to_router,
            start_time=timestamp,
            connection_type=device.connection_type
        )
        
        new_session.add_signal_measurement(device.signal_strength)
        self.active_sessions[mac] = new_session
        
        # Update device profile
        self._update_device_profile(mac, device.hostname, to_router)
        
    def _determine_roaming_trigger(self, old_session: DeviceSession, new_signal: int) -> str:
        """Determine why device roamed"""
        old_signal = old_session.get_average_signal_strength()
        signal_trend = old_session.get_signal_trend()
        
        if old_signal < self.weak_signal_threshold:
            return "weak_signal"
        elif signal_trend == "degrading":
            return "signal_degrading"
        elif new_signal > old_signal + 10:
            return "better_signal"
        elif old_session.duration and old_session.duration < 60:
            return "quick_handover"
        else:
            return "unknown"
            
    def _update_device_profile(self, mac: str, hostname: str, router_name: str):
        """Update device mobility profile"""
        if mac not in self.device_profiles:
            self.device_profiles[mac] = DeviceProfile(
                mac_address=mac,
                hostname=hostname
            )
            
        profile = self.device_profiles[mac]
        
        # Update preferred routers
        if router_name not in profile.preferred_routers:
            profile.preferred_routers.append(router_name)
            
        # Calculate roaming frequency
        device_events = [e for e in self.events if e.device_mac == mac and e.event_type == "roam"]
        if device_events:
            # Calculate roams per hour over last 24 hours
            recent_events = [e for e in device_events if e.timestamp > datetime.now() - timedelta(hours=24)]
            profile.roaming_frequency = len(recent_events) / 24.0
            
        # Update mobility pattern
        if profile.roaming_frequency > 2.0:
            profile.mobility_pattern = "highly_mobile"
        elif profile.roaming_frequency > 0.5:
            profile.mobility_pattern = "mobile"
        else:
            profile.mobility_pattern = "static"
            
        # Calculate average session duration
        device_sessions = [s for s in self.active_sessions.values() if s.device_mac == mac]
        if device_sessions:
            durations = [s.duration for s in device_sessions if s.duration]
            if durations:
                profile.average_session_duration = statistics.mean(durations)
                
    def _update_statistics(self):
        """Update tracking statistics"""
        self.stats['total_roams'] = len([e for e in self.events if e.event_type == "roam"])
        self.stats['total_devices'] = len(self.device_profiles)
        self.stats['active_devices'] = len(self.active_sessions)
        self.stats['roaming_devices'] = len([p for p in self.device_profiles.values() if p.roaming_frequency > 0])
        
    def get_roaming_events(self, hours: int = 24, device_mac: str = None) -> List[Dict[str, Any]]:
        """Get roaming events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        events = [
            event for event in self.events 
            if event.timestamp > cutoff_time
        ]
        
        if device_mac:
            events = [event for event in events if event.device_mac == device_mac]
            
        return [event.to_dict() for event in events]
        
    def get_device_profile(self, mac: str) -> Optional[Dict[str, Any]]:
        """Get device mobility profile"""
        if mac in self.device_profiles:
            return self.device_profiles[mac].to_dict()
        return None
        
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active device sessions"""
        return [session.to_dict() for session in self.active_sessions.values()]
        
    def get_router_statistics(self) -> Dict[str, Any]:
        """Get router-specific statistics"""
        router_stats = defaultdict(lambda: {
            'total_connections': 0,
            'active_connections': 0,
            'roaming_in': 0,
            'roaming_out': 0,
            'average_session_duration': 0.0
        })
        
        # Count connections and roaming
        for event in self.events:
            if event.event_type == "connect":
                router_stats[event.to_router]['total_connections'] += 1
            elif event.event_type == "roam":
                router_stats[event.from_router]['roaming_out'] += 1
                router_stats[event.to_router]['roaming_in'] += 1
                
        # Count active connections
        for session in self.active_sessions.values():
            router_stats[session.router_name]['active_connections'] += 1
            
        return dict(router_stats)
        
    def get_mobility_report(self) -> Dict[str, Any]:
        """Get comprehensive mobility report"""
        return {
            'statistics': self.stats,
            'device_profiles': {mac: profile.to_dict() for mac, profile in self.device_profiles.items()},
            'router_statistics': self.get_router_statistics(),
            'recent_events': self.get_roaming_events(hours=24),
            'active_sessions': self.get_active_sessions(),
            'generated_at': datetime.now().isoformat()
        }
        
    def cleanup_old_data(self):
        """Clean up old tracking data"""
        cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
        
        # Remove old events
        old_count = len(self.events)
        self.events = [event for event in self.events if event.timestamp > cutoff_date]
        
        # Remove inactive device profiles
        active_macs = set(self.active_sessions.keys())
        recent_macs = set(event.device_mac for event in self.events if event.timestamp > datetime.now() - timedelta(days=7))
        
        profiles_to_keep = active_macs.union(recent_macs)
        profiles_removed = 0
        
        for mac in list(self.device_profiles.keys()):
            if mac not in profiles_to_keep:
                del self.device_profiles[mac]
                profiles_removed += 1
                
        logger.info(f"Cleaned up {old_count - len(self.events)} old events and {profiles_removed} inactive profiles")
        
        self.save_history()


# Test function
async def test_roaming_tracker():
    """Test roaming tracker functionality"""
    print("Testing Roaming Tracker")
    print("=" * 25)
    
    # Create tracker
    tracker = RoamingTracker("test_roaming.json")
    
    # Simulate device data
    from dataclasses import dataclass
    
    @dataclass
    class TestDevice:
        mac_address: str
        hostname: str
        ip_address: str
        signal_strength: int
        connection_type: str = "wifi"
        
    # Test devices
    devices = [
        TestDevice("aa:bb:cc:dd:ee:01", "laptop", "192.168.1.100", 75),
        TestDevice("aa:bb:cc:dd:ee:02", "phone", "192.168.1.101", 60),
        TestDevice("aa:bb:cc:dd:ee:03", "tablet", "192.168.1.102", 80)
    ]
    
    # Simulate initial connections
    devices_by_router = {
        "Main Router": devices[:2],
        "Guest Router": devices[2:]
    }
    
    tracker.update_device_locations(devices_by_router)
    print(f"✅ Initial connections: {len(tracker.active_sessions)} active sessions")
    
    # Simulate roaming
    await asyncio.sleep(0.1)
    devices_by_router = {
        "Main Router": devices[:1],
        "Guest Router": devices[1:]
    }
    
    tracker.update_device_locations(devices_by_router)
    print(f"✅ After roaming: {len(tracker.get_roaming_events())} roaming events")
    
    # Get reports
    mobility_report = tracker.get_mobility_report()
    print(f"📊 Mobility report: {len(mobility_report['device_profiles'])} device profiles")
    
    # Cleanup
    tracker.cleanup_old_data()
    Path("test_roaming.json").unlink(missing_ok=True)
    print("✅ Test completed")


if __name__ == "__main__":
    asyncio.run(test_roaming_tracker())
