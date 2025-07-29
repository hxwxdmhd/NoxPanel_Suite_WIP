#!/usr/bin/env python3
"""
Heimnetz Enterprise CLI - Modern Interface
Enhanced command-line interface with rich formatting and async support
"""

import sys
import os
from pathlib import Path

# Add enterprise directory to path
enterprise_dir = Path(__file__).parent / "enterprise"
sys.path.insert(0, str(enterprise_dir))

try:
    # Import the modern CLI with rich formatting
    from heimnetz_cli_v2 import app
    
    def main():
        """Main entry point"""
        app()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Error importing modern CLI: {e}")
    print("Falling back to basic CLI...")
    
    # Fallback to basic CLI
    import asyncio
    import json
    import subprocess
    import sys
    import time
    from pathlib import Path
    from typing import Dict, Any, Optional, List
    import argparse
    import requests
    import os

    # Service URLs
    AETHERCORE_URL = "http://localhost:8001"
    CONTEXTFORGE_URL = "http://localhost:8000"

    class HeimnetzCLI:
        """Main CLI class for Heimnetz Enterprise"""
        
        def __init__(self):
            self.parser = argparse.ArgumentParser(
                description="Heimnetz Enterprise CLI"
            )
            self.setup_commands()
        
        def setup_commands(self):
            """Setup command structure"""
            subparsers = self.parser.add_subparsers(dest='command', help='Available commands')
            
            # System commands
            system_parser = subparsers.add_parser('system', help='System management')
            system_subparsers = system_parser.add_subparsers(dest='system_command')
            
            system_subparsers.add_parser('status', help='Show system status')
            system_subparsers.add_parser('health', help='Check system health')
            
            # AetherCore commands
            aethercore_parser = subparsers.add_parser('aethercore', help='AetherCore management')
            aethercore_subparsers = aethercore_parser.add_subparsers(dest='aethercore_command')
            
            aethercore_subparsers.add_parser('status', help='Show AetherCore status')
            aethercore_subparsers.add_parser('health', help='Check AetherCore health')
            
            models_parser = aethercore_subparsers.add_parser('models', help='Model management')
            models_subparsers = models_parser.add_subparsers(dest='models_command')
            
            models_subparsers.add_parser('list', help='List available models')
            
            load_parser = models_subparsers.add_parser('load', help='Load a model')
            load_parser.add_argument('model_id', help='Model ID to load')
            
            unload_parser = models_subparsers.add_parser('unload', help='Unload a model')
            unload_parser.add_argument('model_id', help='Model ID to unload')
            
            serve_parser = models_subparsers.add_parser('serve', help='Serve inference request')
            serve_parser.add_argument('model_id', help='Model ID to use')
            serve_parser.add_argument('--text', '-t', required=True, help='Text to process')
            
            # ContextForge commands
            contextforge_parser = subparsers.add_parser('contextforge', help='ContextForge management')
            contextforge_subparsers = contextforge_parser.add_subparsers(dest='contextforge_command')
            
            contextforge_subparsers.add_parser('status', help='Show ContextForge status')
            contextforge_subparsers.add_parser('health', help='Check ContextForge health')
            
            test_parser = contextforge_subparsers.add_parser('test', help='Run tests')
            test_parser.add_argument('test_name', help='Test name to run')
        
        def make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
            """Make HTTP request with error handling"""
            try:
                if method.upper() == "GET":
                    response = requests.get(url, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                return {"error": "Request timeout"}
            except requests.exceptions.ConnectionError:
                return {"error": "Connection failed"}
            except requests.exceptions.HTTPError as e:
                return {"error": f"HTTP {e.response.status_code}"}
            except Exception as e:
                return {"error": str(e)}
        
        def print_json(self, data: Dict[str, Any], indent: int = 2):
            """Pretty print JSON data"""
            print(json.dumps(data, indent=indent))
        
        def print_table(self, headers: List[str], rows: List[List[str]]):
            """Print formatted table"""
            # Calculate column widths
            widths = [len(header) for header in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    widths[i] = max(widths[i], len(str(cell)))
            
            # Print header
            header_line = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
            print(header_line)
            print("-" * len(header_line))
            
            # Print rows
            for row in rows:
                row_line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
                print(row_line)
        
        # System commands
        def system_status(self):
            """Show system status"""
            print("🖥️ System Status")
            print("=" * 50)
            
            # Check services
            services = [
                ("AetherCore", f"{AETHERCORE_URL}/health"),
                ("ContextForge", f"{CONTEXTFORGE_URL}/context/health")
            ]
            
            for name, url in services:
                result = self.make_request(url)
                status = "✅ Healthy" if "error" not in result else f"❌ {result.get('error', 'Unknown')}"
                print(f"{name}: {status}")
        
        def system_health(self):
            """Check system health"""
            print("🔍 System Health Check")
            print("=" * 50)
            
            all_healthy = True
            
            # Check AetherCore
            aethercore_health = self.make_request(f"{AETHERCORE_URL}/health")
            if "error" in aethercore_health:
                print(f"❌ AetherCore: {aethercore_health['error']}")
                all_healthy = False
            else:
                print(f"✅ AetherCore: {aethercore_health.get('status', 'unknown')}")
            
            # Check ContextForge
            contextforge_health = self.make_request(f"{CONTEXTFORGE_URL}/context/health")
            if "error" in contextforge_health:
                print(f"❌ ContextForge: {contextforge_health['error']}")
                all_healthy = False
            else:
                print(f"✅ ContextForge: {contextforge_health.get('status', 'unknown')}")
            
            if all_healthy:
                print("\n🎉 All services are healthy!")
            else:
                print("\n⚠️ Some services need attention!")
        
        # AetherCore commands
        def aethercore_status(self):
            """Show AetherCore status"""
            print("🤖 AetherCore Status")
            print("=" * 50)
            
            health = self.make_request(f"{AETHERCORE_URL}/health")
            if "error" in health:
                print(f"❌ Error: {health['error']}")
                return
            
            print(f"Status: {health.get('status', 'unknown')}")
            print(f"Version: {health.get('version', 'unknown')}")
            print(f"Uptime: {health.get('uptime_seconds', 0):.1f}s")
            print(f"Active Models: {health.get('active_models', 0)}")
            print(f"Total Requests: {health.get('total_requests', 0)}")
            
            # System info
            system_info = health.get('system_info', {})
            print(f"CPU: {system_info.get('cpu_percent', 0):.1f}%")
            print(f"Memory: {system_info.get('memory_percent', 0):.1f}%")
            print(f"GPU Available: {system_info.get('gpu_available', False)}")
        
        def aethercore_health(self):
            """Check AetherCore health"""
            health = self.make_request(f"{AETHERCORE_URL}/health")
            if "error" in health:
                print(f"❌ AetherCore is unhealthy: {health['error']}")
            else:
                status = health.get('status', 'unknown')
                if status == 'healthy':
                    print("✅ AetherCore is healthy")
                else:
                    print(f"⚠️ AetherCore status: {status}")
        
        def aethercore_models_list(self):
            """List available models"""
            print("📋 Available Models")
            print("=" * 50)
            
            models = self.make_request(f"{AETHERCORE_URL}/models")
            if "error" in models:
                print(f"❌ Error: {models['error']}")
                return
            
            if not models:
                print("No models available")
                return
            
            headers = ["Model ID", "Name", "Status", "Type", "Memory", "Requests"]
            rows = []
            
            for model in models:
                rows.append([
                    model.get("model_id", ""),
                    model.get("name", ""),
                    model.get("status", "unknown"),
                    model.get("model_type", ""),
                    f"{model.get('memory_usage_mb', 0):.1f}MB",
                    str(model.get("total_requests", 0))
                ])
            
            self.print_table(headers, rows)
        
        def aethercore_models_load(self, model_id: str):
            """Load a model"""
            print(f"🔄 Loading model: {model_id}")
            
            result = self.make_request(f"{AETHERCORE_URL}/models/{model_id}/load", method="POST")
            if "error" in result:
                print(f"❌ Error loading model: {result['error']}")
                return
            
            status = result.get("status", "unknown")
            if status == "loading":
                print(f"🔄 Loading model '{model_id}'...")
            elif status == "already_loaded":
                print(f"✅ Model '{model_id}' is already loaded")
            else:
                print(f"ℹ️ Model '{model_id}' status: {status}")
        
        def aethercore_models_unload(self, model_id: str):
            """Unload a model"""
            print(f"🔄 Unloading model: {model_id}")
            
            result = self.make_request(f"{AETHERCORE_URL}/models/{model_id}/unload", method="POST")
            if "error" in result:
                print(f"❌ Error unloading model: {result['error']}")
                return
            
            print(f"✅ Model '{model_id}' unloaded successfully")
        
        def aethercore_models_serve(self, model_id: str, text: str):
            """Serve inference request"""
            print(f"🎯 Serving inference for model: {model_id}")
            
            data = {
                "model_id": model_id,
                "inputs": {"text": text},
                "parameters": {}
            }
            
            result = self.make_request(f"{AETHERCORE_URL}/serve", method="POST", data=data)
            if "error" in result:
                print(f"❌ Error serving request: {result['error']}")
                return
            
            if result.get("status") == "success":
                print(f"✅ Inference completed in {result.get('processing_time_ms', 0):.2f}ms")
                
                # Display outputs
                outputs = result.get("outputs", {})
                if outputs:
                    print("\nOutputs:")
                    self.print_json(outputs)
            else:
                print(f"❌ Inference failed: {result.get('error', 'Unknown error')}")
        
        # ContextForge commands
        def contextforge_status(self):
            """Show ContextForge status"""
            print("🔍 ContextForge Status")
            print("=" * 50)
            
            health = self.make_request(f"{CONTEXTFORGE_URL}/context/health")
            if "error" in health:
                print(f"❌ Error: {health['error']}")
                return
            
            print(f"Status: {health.get('status', 'unknown')}")
            print(f"Version: {health.get('version', 'unknown')}")
            print(f"Uptime: {health.get('uptime_seconds', 0):.1f}s")
            print(f"Active Models: {health.get('active_models', 0)}")
            print(f"Total Requests: {health.get('total_requests', 0)}")
            
            # System info
            system_info = health.get('system_info', {})
            print(f"CPU: {system_info.get('cpu_percent', 0):.1f}%")
            print(f"Memory: {system_info.get('memory_percent', 0):.1f}%")
            print(f"GPU Available: {system_info.get('gpu_available', False)}")
        
        def contextforge_health(self):
            """Check ContextForge health"""
            health = self.make_request(f"{CONTEXTFORGE_URL}/context/health")
            if "error" in health:
                print(f"❌ ContextForge is unhealthy: {health['error']}")
            else:
                status = health.get('status', 'unknown')
                if status == 'healthy':
                    print("✅ ContextForge is healthy")
                else:
                    print(f"⚠️ ContextForge status: {status}")
        
        def contextforge_test(self, test_name: str):
            """Run ContextForge tests"""
            print(f"🧪 Running test: {test_name}")
            
            try:
                from context.service_integration import service_integration
                
                async def _run_test():
                    result = await service_integration.run_test(test_name)
                    return result
                
                result = asyncio.run(_run_test())
                
                if result.get('success', False):
                    print(f"✅ Test '{test_name}' passed")
                else:
                    print(f"❌ Test '{test_name}' failed: {result.get('error', 'Unknown error')}")
            except ImportError:
                print("❌ Service integration module not available")
        
        def run(self):
            """Run the CLI"""
            args = self.parser.parse_args()
            
            if args.command == 'system':
                if args.system_command == 'status':
                    self.system_status()
                elif args.system_command == 'health':
                    self.system_health()
                else:
                    print("Invalid system command")
            
            elif args.command == 'aethercore':
                if args.aethercore_command == 'status':
                    self.aethercore_status()
                elif args.aethercore_command == 'health':
                    self.aethercore_health()
                elif args.aethercore_command == 'models':
                    if args.models_command == 'list':
                        self.aethercore_models_list()
                    elif args.models_command == 'load':
                        self.aethercore_models_load(args.model_id)
                    elif args.models_command == 'unload':
                        self.aethercore_models_unload(args.model_id)
                    elif args.models_command == 'serve':
                        self.aethercore_models_serve(args.model_id, args.text)
                    else:
                        print("Invalid models command")
                else:
                    print("Invalid aethercore command")
            
            elif args.command == 'contextforge':
                if args.contextforge_command == 'status':
                    self.contextforge_status()
                elif args.contextforge_command == 'health':
                    self.contextforge_health()
                elif args.contextforge_command == 'test':
                    self.contextforge_test(args.test_name)
                else:
                    print("Invalid contextforge command")
            
            else:
                self.parser.print_help()

    if __name__ == "__main__":
        cli = HeimnetzCLI()
        cli.run()
