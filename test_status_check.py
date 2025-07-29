#!/usr/bin/env python3
"""
Test script for NoxGuard System Status Check
"""
import os
import sys
import time
import subprocess
import threading
import json

def run_status_check():
    """Run the system status check script with various timeouts"""
    print("Running system status check with 30 second timeout...")
    
    # First try with 30 second timeout
    try:
        result = subprocess.run(
            [sys.executable, "system_status_check.py", "--timeout", "30"],
            capture_output=True,
            text=True,
            timeout=35  # Give a bit extra time for the timeout to take effect
        )
        
        print(f"Exit code: {result.returncode}")
        print("Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Check if we got a result file
        if os.path.exists("system_status.json"):
            print("\nChecking status file...")
            try:
                with open("system_status.json", "r") as f:
                    data = json.load(f)
                
                # Print key sections status
                sections = ["system_info", "docker_status", "copilot_tools", 
                           "agent_coordination", "resources"]
                
                for section in sections:
                    if section in data:
                        if "error" in data[section]:
                            print(f"❌ {section}: {data[section]['error']}")
                        else:
                            print(f"✅ {section}: OK")
                    else:
                        print(f"⚠️ {section}: Missing")
            except Exception as e:
                print(f"Error reading status file: {e}")
    except subprocess.TimeoutExpired:
        print("Test timed out - the script is likely still hanging")

if __name__ == "__main__":
    run_status_check()
