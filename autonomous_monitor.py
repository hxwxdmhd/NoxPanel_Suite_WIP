#!/usr/bin/env python3
"""
NoxSuite MCP Autonomous Monitoring System
Continuous operation with 128-tools throttling
"""
import time
import json
from datetime import datetime
from emergency_copilot_fix import throttler

class AutonomousMonitor:
    def __init__(self):
        self.name = "NoxSuite MCP Autonomous Monitor"
        self.monitor_interval = 300  # 5 minutes
        self.is_monitoring = False
        self.status_log = []
        
    def quick_health_check(self) -> dict:
        """Lightweight health check to preserve tool usage"""
        def health_check():
            import requests
            import docker
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "langflow": "unknown",
                "docker": "unknown",
                "tool_usage": f"{throttler.tool_count}/120"
            }
            
            try:
                # Quick Langflow check
                response = requests.get("http://localhost:7860/health", timeout=3)
                status["langflow"] = "healthy" if response.status_code == 200 else "degraded"
            except:
                status["langflow"] = "unreachable"
                
            try:
                # Quick Docker check
                client = docker.from_env()
                containers = client.containers.list()
                running_noxsuite = sum(1 for c in containers if 'noxsuite' in c.name and c.status == 'running')
                status["docker"] = f"{running_noxsuite}_containers_running"
            except:
                status["docker"] = "unreachable"
                
            return status
        
        return throttler.execute_with_throttle(health_check)
    
    def log_status(self, status: dict):
        """Log status to memory and file"""
        self.status_log.append(status)
        
        # Keep only last 24 entries (2 hours of monitoring)
        if len(self.status_log) > 24:
            self.status_log = self.status_log[-24:]
        
        # Save to file
        with open('autonomous_monitor_log.json', 'w') as f:
            json.dump(self.status_log, f, indent=2)
    
    def generate_status_report(self):
        """Generate current status report"""
        if not self.status_log:
            return "No monitoring data available"
        
        latest = self.status_log[-1]
        
        report = f"""
🤖 NoxSuite MCP Autonomous Monitor - Status Report
⏰ Last Check: {latest['timestamp']}
🌐 Langflow: {latest['langflow']}
🐳 Docker: {latest['docker']}
🔧 Tool Usage: {latest['tool_usage']}
📊 Monitoring Sessions: {len(self.status_log)}
        """.strip()
        
        return report
    
    def start_monitoring(self, cycles: int = 12):  # 1 hour default
        """Start autonomous monitoring for specified cycles"""
        self.is_monitoring = True
        
        print(f"🚀 Starting autonomous monitoring for {cycles} cycles ({cycles * 5} minutes)")
        print(f"🔧 Current tool usage: {throttler.tool_count}/120")
        
        for cycle in range(cycles):
            if not self.is_monitoring:
                break
                
            print(f"\n🔄 Monitoring Cycle {cycle + 1}/{cycles}")
            
            # Perform health check
            status = self.quick_health_check()
            self.log_status(status)
            
            print(f"   Langflow: {status['langflow']}")
            print(f"   Docker: {status['docker']}")
            print(f"   Tools: {status['tool_usage']}")
            
            # Check for issues
            if status['langflow'] != 'healthy' or 'unreachable' in status['docker']:
                print("⚠️ Issues detected - would trigger emergency protocols")
            else:
                print("✅ All systems operational")
            
            # Wait for next cycle (unless last cycle)
            if cycle < cycles - 1:
                print(f"⏳ Sleeping {self.monitor_interval}s until next check...")
                time.sleep(self.monitor_interval)
        
        print(f"\n🏁 Monitoring cycle complete")
        print(self.generate_status_report())
        print(f"🔧 Final tool usage: {throttler.tool_count}/120")
        
        return self.status_log

def main():
    """Main autonomous monitoring function"""
    print("🎯 NoxSuite MCP Autonomous Monitor - INITIALIZING")
    
    monitor = AutonomousMonitor()
    
    # Quick initial check
    print("\n🔍 Initial system check...")
    initial_status = monitor.quick_health_check()
    monitor.log_status(initial_status)
    
    print(f"✅ Initial Status:")
    print(f"   Langflow: {initial_status['langflow']}")
    print(f"   Docker: {initial_status['docker']}")
    print(f"   Tool Usage: {initial_status['tool_usage']}")
    
    # Start continuous monitoring (reduced to 3 cycles for demo)
    monitoring_log = monitor.start_monitoring(cycles=3)
    
    print("\n🎯 AUTONOMOUS MONITORING MISSION ACCOMPLISHED")
    print(f"📊 Total monitoring sessions: {len(monitoring_log)}")
    print("💾 Monitor log saved: autonomous_monitor_log.json")
    
    return monitoring_log

if __name__ == "__main__":
    try:
        result = main()
        print("\n✅ Autonomous monitoring system operational")
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        print(f"🔧 Tool usage at error: {throttler.tool_count}/120")
