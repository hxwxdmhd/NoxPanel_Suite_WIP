#!/usr/bin/env python3
"""
Memory Leak Detection System - Audit 3 Phase 2
==============================================

This system provides comprehensive memory leak detection:
- Real-time memory monitoring
- Leak pattern detection
- Memory profiling
- Automatic cleanup triggers
- Memory usage analytics

Essential for production stability and resource management
"""

import os
import gc
import sys
import time
import threading
import logging
import traceback
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import weakref
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    total_memory: int
    heap_memory: int
    stack_memory: int
    object_count: int
    gc_collections: int
    process_id: int
    thread_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_memory": self.total_memory,
            "heap_memory": self.heap_memory,
            "stack_memory": self.stack_memory,
            "object_count": self.object_count,
            "gc_collections": self.gc_collections,
            "process_id": self.process_id,
            "thread_id": self.thread_id
        }

@dataclass
class MemoryLeak:
    """Memory leak detection result"""
    plugin_name: str
    leak_type: str  # GRADUAL, SUDDEN, CYCLIC
    detected_at: datetime
    memory_increase: int
    leak_rate: float  # bytes per second
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    stack_trace: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "leak_type": self.leak_type,
            "detected_at": self.detected_at.isoformat(),
            "memory_increase": self.memory_increase,
            "leak_rate": self.leak_rate,
            "severity": self.severity,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "stack_trace": self.stack_trace
        }

class ObjectTracker:
    """
    Object lifecycle tracking for leak detection
    """
    
    def __init__(self):
        self.tracked_objects = weakref.WeakSet()
        self.object_counts = defaultdict(int)
        self.creation_times = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def track_object(self, obj: Any, obj_type: str = None) -> None:
        """Track an object for leak detection"""
        try:
            obj_type = obj_type or type(obj).__name__
            self.tracked_objects.add(obj)
            self.object_counts[obj_type] += 1
            self.creation_times[id(obj)] = time.time()
        except Exception as e:
            self.logger.error(f"Failed to track object: {e}")
    
    def get_object_statistics(self) -> Dict[str, Any]:
        """Get object tracking statistics"""
        stats = {
            "total_tracked": len(self.tracked_objects),
            "object_counts": dict(self.object_counts),
            "creation_times": len(self.creation_times)
        }
        return stats
    
    def find_long_lived_objects(self, max_age: int = 3600) -> List[Tuple[Any, float]]:
        """Find objects that have been alive for a long time"""
        current_time = time.time()
        long_lived = []
        
        for obj in self.tracked_objects:
            obj_id = id(obj)
            if obj_id in self.creation_times:
                age = current_time - self.creation_times[obj_id]
                if age > max_age:
                    long_lived.append((obj, age))
        
        return long_lived

class MemoryLeakDetector:
    """
    Advanced memory leak detection system
    """
    
    def __init__(self, check_interval: int = 30, history_size: int = 100):
        self.check_interval = check_interval
        self.history_size = history_size
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Memory tracking
        self.memory_history = deque(maxlen=history_size)
        self.plugin_memory = defaultdict(lambda: deque(maxlen=history_size))
        
        # Leak detection
        self.detected_leaks = []
        self.leak_callbacks: List[Callable] = []
        
        # Object tracking
        self.object_tracker = ObjectTracker()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Thresholds
        self.thresholds = {
            "gradual_leak_threshold": 10 * 1024 * 1024,  # 10MB
            "sudden_leak_threshold": 50 * 1024 * 1024,   # 50MB
            "leak_rate_threshold": 1024 * 1024,          # 1MB/s
            "min_samples": 10
        }
    
    def start_monitoring(self) -> None:
        """Start continuous memory monitoring"""
        if self.monitoring_active:
            self.logger.warning("Memory monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Memory leak monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Memory leak monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Take memory snapshot
                snapshot = self._take_memory_snapshot()
                self.memory_history.append(snapshot)
                
                # Check for leaks
                self._check_for_leaks()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def _take_memory_snapshot(self) -> MemorySnapshot:
        """Take a memory usage snapshot"""
        try:
            # Get basic memory info
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get Python-specific memory info
            gc.collect()  # Force garbage collection
            
            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory=memory_info.rss,
                heap_memory=memory_info.vms,
                stack_memory=0,  # Not easily available
                object_count=len(gc.get_objects()),
                gc_collections=sum(gc.get_stats()),
                process_id=os.getpid(),
                thread_id=threading.get_ident()
            )
            
            return snapshot
            
        except ImportError:
            # Fallback without psutil
            return MemorySnapshot(
                timestamp=datetime.now(),
                total_memory=0,
                heap_memory=0,
                stack_memory=0,
                object_count=len(gc.get_objects()),
                gc_collections=sum(gc.get_stats()),
                process_id=os.getpid(),
                thread_id=threading.get_ident()
            )
        except Exception as e:
            self.logger.error(f"Failed to take memory snapshot: {e}")
            return MemorySnapshot(
                timestamp=datetime.now(),
                total_memory=0,
                heap_memory=0,
                stack_memory=0,
                object_count=0,
                gc_collections=0,
                process_id=os.getpid(),
                thread_id=threading.get_ident()
            )
    
    def _check_for_leaks(self) -> None:
        """Check for memory leaks in the recent history"""
        if len(self.memory_history) < self.thresholds["min_samples"]:
            return
        
        # Convert to list for easier processing
        history = list(self.memory_history)
        
        # Check for gradual leaks
        self._check_gradual_leak(history)
        
        # Check for sudden leaks
        self._check_sudden_leak(history)
        
        # Check plugin-specific leaks
        self._check_plugin_leaks()
    
    def _check_gradual_leak(self, history: List[MemorySnapshot]) -> None:
        """Check for gradual memory leaks"""
        if len(history) < self.thresholds["min_samples"]:
            return
        
        # Calculate memory trend
        times = [(h.timestamp.timestamp(), h.total_memory) for h in history]
        
        # Simple linear regression to detect trend
        n = len(times)
        sum_x = sum(t[0] for t in times)
        sum_y = sum(t[1] for t in times)
        sum_xy = sum(t[0] * t[1] for t in times)
        sum_xx = sum(t[0] * t[0] for t in times)
        
        # Calculate slope (leak rate)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        
        # Check if slope indicates a leak
        if slope > self.thresholds["leak_rate_threshold"]:
            # Calculate total memory increase
            memory_increase = history[-1].total_memory - history[0].total_memory
            
            if memory_increase > self.thresholds["gradual_leak_threshold"]:
                leak = MemoryLeak(
                    plugin_name="system",
                    leak_type="GRADUAL",
                    detected_at=datetime.now(),
                    memory_increase=memory_increase,
                    leak_rate=slope,
                    severity=self._calculate_severity(memory_increase, slope),
                    snapshots=history[-5:],  # Last 5 snapshots
                    stack_trace=self._get_stack_trace()
                )
                
                self._report_leak(leak)
    
    def _check_sudden_leak(self, history: List[MemorySnapshot]) -> None:
        """Check for sudden memory spikes"""
        if len(history) < 2:
            return
        
        # Compare last two snapshots
        current = history[-1]
        previous = history[-2]
        
        memory_increase = current.total_memory - previous.total_memory
        
        if memory_increase > self.thresholds["sudden_leak_threshold"]:
            leak = MemoryLeak(
                plugin_name="system",
                leak_type="SUDDEN",
                detected_at=datetime.now(),
                memory_increase=memory_increase,
                leak_rate=memory_increase / self.check_interval,
                severity=self._calculate_severity(memory_increase, memory_increase / self.check_interval),
                snapshots=[previous, current],
                stack_trace=self._get_stack_trace()
            )
            
            self._report_leak(leak)
    
    def _check_plugin_leaks(self) -> None:
        """Check for plugin-specific memory leaks"""
        for plugin_name, plugin_history in self.plugin_memory.items():
            if len(plugin_history) < self.thresholds["min_samples"]:
                continue
            
            # Check for gradual increase in plugin memory
            history_list = list(plugin_history)
            if len(history_list) >= 2:
                memory_increase = history_list[-1].total_memory - history_list[0].total_memory
                
                if memory_increase > self.thresholds["gradual_leak_threshold"] // 2:  # Lower threshold for plugins
                    leak = MemoryLeak(
                        plugin_name=plugin_name,
                        leak_type="GRADUAL",
                        detected_at=datetime.now(),
                        memory_increase=memory_increase,
                        leak_rate=memory_increase / (len(history_list) * self.check_interval),
                        severity=self._calculate_severity(memory_increase, memory_increase / (len(history_list) * self.check_interval)),
                        snapshots=history_list[-3:],  # Last 3 snapshots
                        stack_trace=self._get_stack_trace()
                    )
                    
                    self._report_leak(leak)
    
    def _calculate_severity(self, memory_increase: int, leak_rate: float) -> str:
        """Calculate leak severity"""
        if memory_increase > 100 * 1024 * 1024 or leak_rate > 5 * 1024 * 1024:  # 100MB or 5MB/s
            return "CRITICAL"
        elif memory_increase > 50 * 1024 * 1024 or leak_rate > 2 * 1024 * 1024:  # 50MB or 2MB/s
            return "HIGH"
        elif memory_increase > 20 * 1024 * 1024 or leak_rate > 1024 * 1024:  # 20MB or 1MB/s
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_stack_trace(self) -> str:
        """Get current stack trace"""
        return traceback.format_stack()
    
    def _report_leak(self, leak: MemoryLeak) -> None:
        """Report a detected memory leak"""
        self.detected_leaks.append(leak)
        
        # Log the leak
        self.logger.warning(f"Memory leak detected: {leak.plugin_name} - {leak.leak_type} - {leak.severity}")
        self.logger.warning(f"Memory increase: {leak.memory_increase / 1024 / 1024:.2f}MB, Rate: {leak.leak_rate / 1024 / 1024:.2f}MB/s")
        
        # Call registered callbacks
        for callback in self.leak_callbacks:
            try:
                callback(leak)
            except Exception as e:
                self.logger.error(f"Leak callback error: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old data to prevent memory leaks in the detector itself"""
        # Remove old leak records (keep last 100)
        if len(self.detected_leaks) > 100:
            self.detected_leaks = self.detected_leaks[-100:]
        
        # Clean up object tracker
        self.object_tracker.creation_times = {
            k: v for k, v in self.object_tracker.creation_times.items()
            if time.time() - v < 3600  # Keep last hour
        }
    
    def track_plugin_memory(self, plugin_name: str, memory_usage: int) -> None:
        """Track memory usage for a specific plugin"""
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            total_memory=memory_usage,
            heap_memory=0,
            stack_memory=0,
            object_count=0,
            gc_collections=0,
            process_id=os.getpid(),
            thread_id=threading.get_ident()
        )
        
        self.plugin_memory[plugin_name].append(snapshot)
    
    def add_leak_callback(self, callback: Callable[[MemoryLeak], None]) -> None:
        """Add callback for leak detection"""
        self.leak_callbacks.append(callback)
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        stats = {
            "monitoring_active": self.monitoring_active,
            "history_size": len(self.memory_history),
            "detected_leaks": len(self.detected_leaks),
            "leak_by_severity": defaultdict(int),
            "plugin_memory_usage": {},
            "object_statistics": self.object_tracker.get_object_statistics()
        }
        
        # Count leaks by severity
        for leak in self.detected_leaks:
            stats["leak_by_severity"][leak.severity] += 1
        
        # Get plugin memory usage
        for plugin_name, plugin_history in self.plugin_memory.items():
            if plugin_history:
                latest = plugin_history[-1]
                stats["plugin_memory_usage"][plugin_name] = {
                    "current_memory": latest.total_memory,
                    "history_size": len(plugin_history)
                }
        
        return stats
    
    def generate_leak_report(self) -> str:
        """Generate comprehensive leak detection report"""
        report = []
        report.append("# MEMORY LEAK DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Monitoring Active: {self.monitoring_active}")
        report.append(f"Total Leaks Detected: {len(self.detected_leaks)}")
        report.append("")
        
        # Leak summary
        leak_summary = defaultdict(int)
        for leak in self.detected_leaks:
            leak_summary[leak.severity] += 1
        
        report.append("## LEAK SUMMARY")
        report.append("-" * 20)
        for severity, count in leak_summary.items():
            report.append(f"{severity}: {count}")
        report.append("")
        
        # Recent leaks
        recent_leaks = sorted(self.detected_leaks, key=lambda x: x.detected_at, reverse=True)[:10]
        report.append("## RECENT LEAKS (Last 10)")
        report.append("-" * 30)
        
        for leak in recent_leaks:
            report.append(f"Plugin: {leak.plugin_name}")
            report.append(f"Type: {leak.leak_type}")
            report.append(f"Severity: {leak.severity}")
            report.append(f"Memory Increase: {leak.memory_increase / 1024 / 1024:.2f}MB")
            report.append(f"Leak Rate: {leak.leak_rate / 1024 / 1024:.2f}MB/s")
            report.append(f"Detected: {leak.detected_at.isoformat()}")
            report.append("")
        
        # Memory statistics
        stats = self.get_memory_statistics()
        report.append("## MEMORY STATISTICS")
        report.append("-" * 25)
        report.append(f"History Size: {stats['history_size']}")
        report.append(f"Tracked Objects: {stats['object_statistics']['total_tracked']}")
        report.append("")
        
        return "\n".join(report)
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup and return statistics"""
        self.logger.info("Forcing memory cleanup")
        
        # Get initial memory usage
        initial_snapshot = self._take_memory_snapshot()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get final memory usage
        final_snapshot = self._take_memory_snapshot()
        
        # Calculate cleanup results
        memory_freed = initial_snapshot.total_memory - final_snapshot.total_memory
        objects_freed = initial_snapshot.object_count - final_snapshot.object_count
        
        cleanup_stats = {
            "memory_freed": memory_freed,
            "objects_freed": objects_freed,
            "gc_collected": collected,
            "initial_memory": initial_snapshot.total_memory,
            "final_memory": final_snapshot.total_memory,
            "cleanup_timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Cleanup completed: {memory_freed / 1024 / 1024:.2f}MB freed, {objects_freed} objects freed")
        
        return cleanup_stats

def main():
    """Main function for testing the memory leak detector"""
    try:
        # Initialize detector
        detector = MemoryLeakDetector(check_interval=2, history_size=20)
        
        # Add leak callback
        def leak_callback(leak: MemoryLeak):
            print(f"LEAK DETECTED: {leak.plugin_name} - {leak.leak_type} - {leak.severity}")
        
        detector.add_leak_callback(leak_callback)
        
        # Start monitoring
        detector.start_monitoring()
        
        print("Memory leak detector started. Running test...")
        
        # Simulate memory usage
        test_objects = []
        for i in range(10):
            # Create objects to simulate memory usage
            large_list = [j for j in range(1000)]
            test_objects.append(large_list)
            
            # Track plugin memory
            detector.track_plugin_memory("test_plugin", len(test_objects) * 1000 * 8)
            
            # Wait for detector to process
            time.sleep(3)
        
        # Get statistics
        stats = detector.get_memory_statistics()
        print("Memory Statistics:")
        print(json.dumps(stats, indent=2))
        
        # Generate report
        report = detector.generate_leak_report()
        print("\nLeak Detection Report:")
        print(report)
        
        # Force cleanup
        cleanup_stats = detector.force_cleanup()
        print("\nCleanup Statistics:")
        print(json.dumps(cleanup_stats, indent=2))
        
        # Stop monitoring
        detector.stop_monitoring()
        
    except Exception as e:
        print(f"Error testing memory leak detector: {e}")
        logger.error(f"Memory leak detector test error: {e}")

if __name__ == "__main__":
    main()
