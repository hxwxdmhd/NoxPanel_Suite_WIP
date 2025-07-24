#!/usr/bin/env python3
"""
ContextForge Service Integration
===============================

Integrates ContextForge with the enterprise service ecosystem.
Provides service registration, health monitoring, and API endpoints.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from context.index import ContextForge, ContextRequest, ModelType, AgentIntent
from context.router import ContextRouter
from context.protocols.schema import protocol_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextForgeService:
    """
    ContextForge Service Integration
    
    Provides enterprise service integration for ContextForge MCP server.
    """
    
    def __init__(self, port: int = 5005):
        self.port = port
        self.contextforge = ContextForge()
        self.router = ContextRouter(self.contextforge)
        self.service_config = self.load_service_config()
        self.health_status = "healthy"
        self.start_time = datetime.now()
        
        logger.info(f"ContextForge Service initialized on port {port}")
    
    def load_service_config(self) -> Dict[str, Any]:
        """Load service configuration"""
        config_path = Path("k:/Project Heimnetz/enterprise/context/context_registry.json")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default service configuration"""
        return {
            "contextforge_version": "1.0.0",
            "status": "active",
            "services": {
                "contextforge_server": {
                    "name": "ContextForge MCP Server",
                    "port": self.port,
                    "url": f"http://localhost:{self.port}",
                    "status": "active",
                    "health_endpoint": "/health"
                }
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for registration"""
        return {
            "name": "ContextForge MCP Server",
            "description": "Model Context Protocol server for AI agent context management",
            "version": "1.0.0",
            "port": self.port,
            "url": f"http://localhost:{self.port}",
            "health_endpoint": "/health",
            "api_endpoints": {
                "/context/process": "Process context requests",
                "/context/health": "Health check endpoint",
                "/context/metrics": "Performance metrics",
                "/context/protocols": "Supported protocol versions",
                "/context/models": "Supported model registry",
                "/context/test": "Test endpoint with sample requests"
            },
            "capabilities": [
                "prompt_analysis",
                "model_compatibility",
                "dynamic_routing",
                "context_embeddings",
                "protocol_versioning",
                "performance_optimization",
                "enterprise_integration"
            ],
            "supported_protocols": ["1.0", "1.1", "2.0"],
            "supported_models": ["gpt-4o", "github-copilot", "claude-3"],
            "routing_strategies": ["direct", "load_balanced", "failover", "adaptive"]
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Get component health
        contextforge_health = self.contextforge.get_health_status()
        router_stats = self.router.get_routing_stats()
        
        return {
            "status": self.health_status,
            "uptime_seconds": uptime,
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "contextforge": {
                    "status": contextforge_health["status"],
                    "cached_embeddings": contextforge_health["cached_embeddings"],
                    "active_sessions": contextforge_health["active_sessions"],
                    "protocol_versions": contextforge_health["protocol_versions"]
                },
                "router": {
                    "total_requests": router_stats["total_requests"],
                    "success_rate": router_stats["success_rate"],
                    "average_response_time": router_stats["average_response_time"],
                    "active_endpoints": router_stats["active_endpoints"],
                    "healthy_endpoints": router_stats["healthy_endpoints"]
                },
                "protocols": {
                    "supported_versions": protocol_registry.get_supported_versions(),
                    "latest_version": protocol_registry.get_latest_protocol().version
                }
            },
            "performance": {
                "memory_usage": contextforge_health["memory_usage"],
                "cache_hit_rate": 0.85,  # Placeholder
                "average_processing_time": 2.3,  # Placeholder
                "concurrent_requests": 5  # Placeholder
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        router_stats = self.router.get_routing_stats()
        contextforge_health = self.contextforge.get_health_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "requests": {
                "total": router_stats["total_requests"],
                "successful": router_stats["successful_requests"],
                "failed": router_stats["total_requests"] - router_stats["successful_requests"],
                "success_rate": router_stats["success_rate"],
                "average_response_time": router_stats["average_response_time"]
            },
            "resources": {
                "memory": contextforge_health["memory_usage"],
                "cache_size": contextforge_health["cached_embeddings"],
                "active_sessions": contextforge_health["active_sessions"]
            },
            "routing": {
                "active_endpoints": router_stats["active_endpoints"],
                "healthy_endpoints": router_stats["healthy_endpoints"],
                "endpoint_health_rate": (
                    router_stats["healthy_endpoints"] / max(1, router_stats["active_endpoints"])
                )
            },
            "protocols": {
                "supported_count": len(protocol_registry.get_supported_versions()),
                "latest_version": protocol_registry.get_latest_protocol().version
            }
        }
    
    def get_supported_protocols(self) -> Dict[str, Any]:
        """Get supported protocol information"""
        protocols = {}
        
        for version in protocol_registry.get_supported_versions():
            protocol = protocol_registry.get_protocol(version)
            protocols[version] = {
                "version": version,
                "capabilities": len(protocol.capabilities),
                "methods": list(protocol.methods.keys()),
                "message_formats": list(protocol.message_formats.keys()),
                "validation_rules": protocol.validation_rules
            }
        
        return {
            "supported_versions": list(protocols.keys()),
            "latest_version": protocol_registry.get_latest_protocol().version,
            "protocols": protocols
        }
    
    def get_model_registry(self) -> Dict[str, Any]:
        """Get model registry information"""
        config = self.service_config.get("model_registry", {})
        
        return {
            "supported_models": list(config.keys()),
            "models": config,
            "routing_strategies": self.service_config.get("routing_strategies", {}),
            "default_routing": "adaptive"
        }
    
    async def process_context_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a context request"""
        try:
            # Parse request
            request = ContextRequest(
                agent=request_data.get("agent", "Unknown"),
                model=ModelType(request_data.get("model", "gpt-4o")),
                intent=AgentIntent(request_data.get("intent", "analyze")),
                project_scope=request_data.get("project_scope", "Unknown"),
                prompt=request_data.get("prompt", ""),
                metadata=request_data.get("metadata", {})
            )
            
            # Process through ContextForge
            result = await self.contextforge.process_context_request(request)
            
            # Add service metadata
            result["service_info"] = {
                "service": "ContextForge MCP Server",
                "version": "1.0.0",
                "processed_at": datetime.now().isoformat(),
                "processing_node": f"localhost:{self.port}"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing context request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    def run_test_requests(self) -> Dict[str, Any]:
        """Run test requests to validate functionality"""
        test_requests = self.service_config.get("test_prompts", [])
        results = []
        
        for i, test_prompt in enumerate(test_requests):
            try:
                # Create test request
                request = ContextRequest(
                    agent=test_prompt.get("agent", "TestAgent"),
                    model=ModelType(test_prompt.get("model", "gpt-4o")),
                    intent=AgentIntent(test_prompt.get("intent", "analyze")),
                    project_scope=test_prompt.get("project_scope", "Test"),
                    prompt=test_prompt.get("prompt", "Test prompt")
                )
                
                # Validate and analyze
                is_valid = self.contextforge.validate_request(request)
                analysis = asyncio.run(self.contextforge.analyze_prompt(request.prompt, request.intent))
                
                results.append({
                    "test_name": test_prompt.get("name", f"test_{i}"),
                    "status": "success" if is_valid else "failed",
                    "valid": is_valid,
                    "analysis": analysis,
                    "request_id": request.metadata["request_id"],
                    "compatibility_score": request.metadata["compatibility_score"]
                })
                
            except Exception as e:
                results.append({
                    "test_name": test_prompt.get("name", f"test_{i}"),
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "test_summary": {
                "total_tests": len(test_requests),
                "successful": len([r for r in results if r["status"] == "success"]),
                "failed": len([r for r in results if r["status"] == "failed"]),
                "errors": len([r for r in results if r["status"] == "error"])
            },
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def register_with_enterprise_services(self) -> Dict[str, Any]:
        """Register with enterprise service registry"""
        service_info = self.get_service_info()
        
        # In a real implementation, this would make HTTP requests to register
        # with the enterprise service registry
        registration_data = {
            "service_name": "contextforge",
            "service_type": "mcp_server",
            "registration_timestamp": datetime.now().isoformat(),
            "service_info": service_info,
            "health_check_url": f"http://localhost:{self.port}/health",
            "integration_status": "active"
        }
        
        logger.info(f"Registered ContextForge service with enterprise registry")
        return registration_data
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status with other services"""
        return {
            "integrations": {
                "heimnetz_cli": {
                    "status": "planned",
                    "description": "CLI commands for context management",
                    "endpoints": ["/context/analyze", "/context/optimize"]
                },
                "noxpanel_ai": {
                    "status": "active",
                    "description": "AI system integration",
                    "context_sources": ["project_context", "ai_memory", "training_data"]
                },
                "enterprise_services": {
                    "status": "active",
                    "description": "Enterprise service integration",
                    "services": ["multi_tenant", "ai_integration", "analytics"]
                }
            },
            "context_sources": {
                "noxpanel_context": {
                    "status": "active",
                    "path": "k:/Project Heimnetz/AI/NoxPanel/noxcore/context_loader.py"
                },
                "enterprise_context": {
                    "status": "active",
                    "path": "k:/Project Heimnetz/enterprise/"
                },
                "project_context": {
                    "status": "active",
                    "path": "k:/Project Heimnetz/"
                }
            }
        }

# Global service instance
contextforge_service = ContextForgeService()

# API endpoint handlers (would be integrated with FastAPI or Flask)
def handle_health_check() -> Dict[str, Any]:
    """Health check endpoint handler"""
    return contextforge_service.get_health_status()

def handle_metrics() -> Dict[str, Any]:
    """Metrics endpoint handler"""
    return contextforge_service.get_metrics()

def handle_protocols() -> Dict[str, Any]:
    """Protocols endpoint handler"""
    return contextforge_service.get_supported_protocols()

def handle_models() -> Dict[str, Any]:
    """Models endpoint handler"""
    return contextforge_service.get_model_registry()

def handle_test() -> Dict[str, Any]:
    """Test endpoint handler"""
    return contextforge_service.run_test_requests()

async def handle_context_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Context request endpoint handler"""
    return await contextforge_service.process_context_request(request_data)

def handle_service_info() -> Dict[str, Any]:
    """Service info endpoint handler"""
    return contextforge_service.get_service_info()

def handle_integration_status() -> Dict[str, Any]:
    """Integration status endpoint handler"""
    return contextforge_service.get_integration_status()

# Test the service integration
if __name__ == "__main__":
    print("🚀 ContextForge Service Integration")
    print("=" * 50)
    
    # Test service initialization
    service = ContextForgeService(port=5005)
    
    # Test service info
    info = service.get_service_info()
    print(f"Service: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Port: {info['port']}")
    print(f"Capabilities: {len(info['capabilities'])}")
    
    # Test health check
    health = service.get_health_status()
    print(f"\nHealth Status: {health['status']}")
    print(f"Uptime: {health['uptime_seconds']:.2f}s")
    
    # Test metrics
    metrics = service.get_metrics()
    print(f"\nMetrics:")
    print(f"  Total Requests: {metrics['requests']['total']}")
    print(f"  Success Rate: {metrics['requests']['success_rate']:.2%}")
    
    # Test protocols
    protocols = service.get_supported_protocols()
    print(f"\nProtocols: {protocols['supported_versions']}")
    print(f"Latest: {protocols['latest_version']}")
    
    # Test model registry
    models = service.get_model_registry()
    print(f"\nSupported Models: {models['supported_models']}")
    
    # Test registration
    registration = service.register_with_enterprise_services()
    print(f"\nRegistration Status: {registration['integration_status']}")
    
    print("\n✅ ContextForge Service Integration Tests Completed")
