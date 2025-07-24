#!/usr/bin/env python3
"""
ContextForge Protocol Schemas
============================

Version-specific protocol schemas for Model Context Protocol (MCP) compliance.
Each version defines capabilities, message formats, and validation rules.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

class MessageType(str, Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class CapabilityLevel(str, Enum):
    """Protocol capability levels"""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"

@dataclass
class ProtocolCapability:
    """Protocol capability definition"""
    name: str
    level: CapabilityLevel
    description: str
    required_version: str
    optional: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPMessage:
    """Base MCP message structure"""
    version: str
    message_type: MessageType
    id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPRequest:
    """MCP request message"""
    version: str
    message_type: MessageType
    id: str
    method: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPResponse:
    """MCP response message"""
    version: str
    message_type: MessageType
    id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)

class ProtocolSchema:
    """Base protocol schema class"""
    
    def __init__(self, version: str):
        self.version = version
        self.capabilities: List[ProtocolCapability] = []
        self.methods: Dict[str, Dict[str, Any]] = {}
        self.message_formats: Dict[str, Dict[str, Any]] = {}
        self.validation_rules: Dict[str, Any] = {}
        
    def add_capability(self, capability: ProtocolCapability):
        """Add a capability to the schema"""
        self.capabilities.append(capability)
        
    def add_method(self, method_name: str, method_spec: Dict[str, Any]):
        """Add a method specification"""
        self.methods[method_name] = method_spec
        
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate a message against the schema"""
        # Basic validation implementation
        required_fields = ["version", "message_type", "id"]
        return all(field in message for field in required_fields)
        
    def get_schema_definition(self) -> Dict[str, Any]:
        """Get complete schema definition"""
        return {
            "version": self.version,
            "capabilities": [
                {
                    "name": cap.name,
                    "level": cap.level,
                    "description": cap.description,
                    "required_version": cap.required_version,
                    "optional": cap.optional,
                    "parameters": cap.parameters
                } for cap in self.capabilities
            ],
            "methods": self.methods,
            "message_formats": self.message_formats,
            "validation_rules": self.validation_rules
        }

class MCPv1_0(ProtocolSchema):
    """MCP Protocol Version 1.0 - Basic functionality"""
    
    def __init__(self):
        super().__init__("1.0")
        self.initialize_capabilities()
        self.initialize_methods()
        self.initialize_message_formats()
        self.initialize_validation_rules()
    
    def initialize_capabilities(self):
        """Initialize v1.0 capabilities"""
        capabilities = [
            ProtocolCapability(
                name="basic_prompt",
                level=CapabilityLevel.BASIC,
                description="Basic prompt processing",
                required_version="1.0",
                parameters={"max_tokens": 4000}
            ),
            ProtocolCapability(
                name="context_retrieval",
                level=CapabilityLevel.BASIC,
                description="Basic context retrieval",
                required_version="1.0",
                parameters={"max_context_items": 10}
            ),
            ProtocolCapability(
                name="simple_embedding",
                level=CapabilityLevel.BASIC,
                description="Simple embedding generation",
                required_version="1.0",
                parameters={"embedding_size": 512}
            )
        ]
        
        for cap in capabilities:
            self.add_capability(cap)
    
    def initialize_methods(self):
        """Initialize v1.0 methods"""
        methods = {
            "prompt": {
                "description": "Process a prompt request",
                "parameters": {
                    "prompt": {"type": "string", "required": True},
                    "context": {"type": "object", "required": False},
                    "max_tokens": {"type": "integer", "default": 1000}
                },
                "returns": {
                    "result": {"type": "string"},
                    "context_used": {"type": "array"}
                }
            },
            "context": {
                "description": "Retrieve context for a scope",
                "parameters": {
                    "scope": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 5}
                },
                "returns": {
                    "context_items": {"type": "array"},
                    "total_available": {"type": "integer"}
                }
            },
            "embedding": {
                "description": "Generate embeddings for text",
                "parameters": {
                    "text": {"type": "string", "required": True},
                    "model": {"type": "string", "default": "basic"}
                },
                "returns": {
                    "embedding": {"type": "array"},
                    "dimensions": {"type": "integer"}
                }
            }
        }
        
        for method_name, method_spec in methods.items():
            self.add_method(method_name, method_spec)
    
    def initialize_message_formats(self):
        """Initialize v1.0 message formats"""
        self.message_formats = {
            "request": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["request"], "required": True},
                "id": {"type": "string", "required": True},
                "method": {"type": "string", "required": True},
                "params": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            },
            "response": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["response"], "required": True},
                "id": {"type": "string", "required": True},
                "result": {"type": "object", "required": False},
                "error": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            }
        }
    
    def initialize_validation_rules(self):
        """Initialize v1.0 validation rules"""
        self.validation_rules = {
            "max_message_size": 10000,  # 10KB
            "max_context_items": 10,
            "max_embedding_size": 512,
            "timeout_seconds": 30,
            "required_fields": ["version", "message_type", "id"]
        }

class MCPv1_1(ProtocolSchema):
    """MCP Protocol Version 1.1 - Enhanced functionality"""
    
    def __init__(self):
        super().__init__("1.1")
        self.initialize_capabilities()
        self.initialize_methods()
        self.initialize_message_formats()
        self.initialize_validation_rules()
    
    def initialize_capabilities(self):
        """Initialize v1.1 capabilities"""
        capabilities = [
            ProtocolCapability(
                name="enhanced_prompt",
                level=CapabilityLevel.STANDARD,
                description="Enhanced prompt processing with context",
                required_version="1.1",
                parameters={"max_tokens": 8000, "context_aware": True}
            ),
            ProtocolCapability(
                name="batch_processing",
                level=CapabilityLevel.STANDARD,
                description="Batch processing of requests",
                required_version="1.1",
                parameters={"max_batch_size": 10}
            ),
            ProtocolCapability(
                name="context_caching",
                level=CapabilityLevel.STANDARD,
                description="Context caching for performance",
                required_version="1.1",
                parameters={"cache_ttl": 3600}
            ),
            ProtocolCapability(
                name="advanced_embedding",
                level=CapabilityLevel.STANDARD,
                description="Advanced embedding with metadata",
                required_version="1.1",
                parameters={"embedding_size": 1024, "metadata_support": True}
            )
        ]
        
        for cap in capabilities:
            self.add_capability(cap)
    
    def initialize_methods(self):
        """Initialize v1.1 methods"""
        methods = {
            "prompt": {
                "description": "Process a prompt request with enhanced context",
                "parameters": {
                    "prompt": {"type": "string", "required": True},
                    "context": {"type": "object", "required": False},
                    "max_tokens": {"type": "integer", "default": 2000},
                    "temperature": {"type": "number", "default": 0.7}
                },
                "returns": {
                    "result": {"type": "string"},
                    "context_used": {"type": "array"},
                    "metadata": {"type": "object"}
                }
            },
            "batch": {
                "description": "Process multiple requests in batch",
                "parameters": {
                    "requests": {"type": "array", "required": True},
                    "parallel": {"type": "boolean", "default": True}
                },
                "returns": {
                    "results": {"type": "array"},
                    "processing_time": {"type": "number"}
                }
            },
            "context": {
                "description": "Retrieve context with caching",
                "parameters": {
                    "scope": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 10},
                    "use_cache": {"type": "boolean", "default": True}
                },
                "returns": {
                    "context_items": {"type": "array"},
                    "total_available": {"type": "integer"},
                    "cache_hit": {"type": "boolean"}
                }
            },
            "embedding": {
                "description": "Generate advanced embeddings",
                "parameters": {
                    "text": {"type": "string", "required": True},
                    "model": {"type": "string", "default": "advanced"},
                    "include_metadata": {"type": "boolean", "default": True}
                },
                "returns": {
                    "embedding": {"type": "array"},
                    "dimensions": {"type": "integer"},
                    "metadata": {"type": "object"}
                }
            }
        }
        
        for method_name, method_spec in methods.items():
            self.add_method(method_name, method_spec)
    
    def initialize_message_formats(self):
        """Initialize v1.1 message formats"""
        self.message_formats = {
            "request": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["request"], "required": True},
                "id": {"type": "string", "required": True},
                "method": {"type": "string", "required": True},
                "params": {"type": "object", "required": False},
                "context": {"type": "object", "required": False},
                "metadata": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            },
            "response": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["response"], "required": True},
                "id": {"type": "string", "required": True},
                "result": {"type": "object", "required": False},
                "error": {"type": "object", "required": False},
                "context": {"type": "object", "required": False},
                "metadata": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            },
            "batch_request": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["batch_request"], "required": True},
                "id": {"type": "string", "required": True},
                "requests": {"type": "array", "required": True},
                "batch_options": {"type": "object", "required": False}
            }
        }
    
    def initialize_validation_rules(self):
        """Initialize v1.1 validation rules"""
        self.validation_rules = {
            "max_message_size": 50000,  # 50KB
            "max_context_items": 25,
            "max_embedding_size": 1024,
            "timeout_seconds": 60,
            "max_batch_size": 10,
            "required_fields": ["version", "message_type", "id"]
        }

class MCPv2_0(ProtocolSchema):
    """MCP Protocol Version 2.0 - Advanced functionality"""
    
    def __init__(self):
        super().__init__("2.0")
        self.initialize_capabilities()
        self.initialize_methods()
        self.initialize_message_formats()
        self.initialize_validation_rules()
    
    def initialize_capabilities(self):
        """Initialize v2.0 capabilities"""
        capabilities = [
            ProtocolCapability(
                name="dynamic_routing",
                level=CapabilityLevel.ADVANCED,
                description="Dynamic routing based on context and load",
                required_version="2.0",
                parameters={"routing_strategies": ["load_balanced", "failover", "adaptive"]}
            ),
            ProtocolCapability(
                name="streaming_processing",
                level=CapabilityLevel.ADVANCED,
                description="Streaming response processing",
                required_version="2.0",
                parameters={"chunk_size": 1000, "max_stream_duration": 300}
            ),
            ProtocolCapability(
                name="multi_modal_context",
                level=CapabilityLevel.ADVANCED,
                description="Multi-modal context processing",
                required_version="2.0",
                parameters={"supported_types": ["text", "code", "image", "audio"]}
            ),
            ProtocolCapability(
                name="predictive_caching",
                level=CapabilityLevel.ADVANCED,
                description="Predictive caching with AI",
                required_version="2.0",
                parameters={"prediction_models": ["usage_pattern", "context_similarity"]}
            ),
            ProtocolCapability(
                name="enterprise_security",
                level=CapabilityLevel.ENTERPRISE,
                description="Enterprise-grade security features",
                required_version="2.0",
                parameters={"encryption": "AES-256", "audit_logging": True}
            )
        ]
        
        for cap in capabilities:
            self.add_capability(cap)
    
    def initialize_methods(self):
        """Initialize v2.0 methods"""
        methods = {
            "prompt": {
                "description": "Advanced prompt processing with full context",
                "parameters": {
                    "prompt": {"type": "string", "required": True},
                    "context": {"type": "object", "required": False},
                    "max_tokens": {"type": "integer", "default": 4000},
                    "temperature": {"type": "number", "default": 0.7},
                    "routing_strategy": {"type": "string", "default": "adaptive"},
                    "stream": {"type": "boolean", "default": False}
                },
                "returns": {
                    "result": {"type": "string"},
                    "context_used": {"type": "array"},
                    "metadata": {"type": "object"},
                    "routing_info": {"type": "object"},
                    "performance_metrics": {"type": "object"}
                }
            },
            "stream": {
                "description": "Streaming response processing",
                "parameters": {
                    "request": {"type": "object", "required": True},
                    "chunk_size": {"type": "integer", "default": 1000},
                    "callback_url": {"type": "string", "required": False}
                },
                "returns": {
                    "stream_id": {"type": "string"},
                    "estimated_duration": {"type": "number"}
                }
            },
            "context": {
                "description": "Advanced context retrieval with prediction",
                "parameters": {
                    "scope": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 50},
                    "prediction_enabled": {"type": "boolean", "default": True},
                    "multi_modal": {"type": "boolean", "default": False}
                },
                "returns": {
                    "context_items": {"type": "array"},
                    "total_available": {"type": "integer"},
                    "predicted_relevance": {"type": "array"},
                    "cache_analytics": {"type": "object"}
                }
            },
            "embedding": {
                "description": "Enterprise-grade embedding generation",
                "parameters": {
                    "content": {"type": "string", "required": True},
                    "content_type": {"type": "string", "default": "text"},
                    "model": {"type": "string", "default": "enterprise"},
                    "security_level": {"type": "string", "default": "standard"}
                },
                "returns": {
                    "embedding": {"type": "array"},
                    "dimensions": {"type": "integer"},
                    "metadata": {"type": "object"},
                    "security_hash": {"type": "string"}
                }
            },
            "batch": {
                "description": "Advanced batch processing with optimization",
                "parameters": {
                    "requests": {"type": "array", "required": True},
                    "optimization_strategy": {"type": "string", "default": "adaptive"},
                    "priority_weights": {"type": "object", "required": False}
                },
                "returns": {
                    "results": {"type": "array"},
                    "processing_time": {"type": "number"},
                    "optimization_metrics": {"type": "object"}
                }
            }
        }
        
        for method_name, method_spec in methods.items():
            self.add_method(method_name, method_spec)
    
    def initialize_message_formats(self):
        """Initialize v2.0 message formats"""
        self.message_formats = {
            "request": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["request"], "required": True},
                "id": {"type": "string", "required": True},
                "method": {"type": "string", "required": True},
                "params": {"type": "object", "required": False},
                "context": {"type": "object", "required": False},
                "metadata": {"type": "object", "required": False},
                "routing_hints": {"type": "object", "required": False},
                "security_context": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            },
            "response": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["response"], "required": True},
                "id": {"type": "string", "required": True},
                "result": {"type": "object", "required": False},
                "error": {"type": "object", "required": False},
                "context": {"type": "object", "required": False},
                "metadata": {"type": "object", "required": False},
                "routing_info": {"type": "object", "required": False},
                "performance_metrics": {"type": "object", "required": False},
                "timestamp": {"type": "string", "format": "iso8601"}
            },
            "stream_chunk": {
                "version": {"type": "string", "required": True},
                "message_type": {"type": "string", "enum": ["stream_chunk"], "required": True},
                "stream_id": {"type": "string", "required": True},
                "chunk_index": {"type": "integer", "required": True},
                "data": {"type": "string", "required": True},
                "is_final": {"type": "boolean", "default": False}
            }
        }
    
    def initialize_validation_rules(self):
        """Initialize v2.0 validation rules"""
        self.validation_rules = {
            "max_message_size": 100000,  # 100KB
            "max_context_items": 100,
            "max_embedding_size": 2048,
            "timeout_seconds": 120,
            "max_batch_size": 50,
            "max_stream_duration": 300,
            "required_fields": ["version", "message_type", "id"],
            "security_validation": True,
            "audit_logging": True
        }

class ProtocolRegistry:
    """Registry for all protocol versions"""
    
    def __init__(self):
        self.protocols: Dict[str, ProtocolSchema] = {}
        self.initialize_protocols()
    
    def initialize_protocols(self):
        """Initialize all protocol versions"""
        self.protocols = {
            "1.0": MCPv1_0(),
            "1.1": MCPv1_1(),
            "2.0": MCPv2_0()
        }
    
    def get_protocol(self, version: str) -> Optional[ProtocolSchema]:
        """Get protocol schema by version"""
        return self.protocols.get(version)
    
    def get_latest_protocol(self) -> ProtocolSchema:
        """Get the latest protocol version"""
        return self.protocols["2.0"]
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported protocol versions"""
        return list(self.protocols.keys())
    
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate message against appropriate protocol"""
        version = message.get("version", "2.0")
        protocol = self.get_protocol(version)
        
        if not protocol:
            return False
        
        return protocol.validate_message(message)
    
    def get_capabilities(self, version: str) -> List[Dict[str, Any]]:
        """Get capabilities for a specific version"""
        protocol = self.get_protocol(version)
        if not protocol:
            return []
        
        return [
            {
                "name": cap.name,
                "level": cap.level,
                "description": cap.description,
                "parameters": cap.parameters
            } for cap in protocol.capabilities
        ]
    
    def export_schemas(self, output_path: str):
        """Export all schemas to JSON files"""
        from pathlib import Path
        
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        for version, protocol in self.protocols.items():
            schema_file = output_dir / f"mcp_v{version.replace('.', '_')}.json"
            with open(schema_file, 'w') as f:
                json.dump(protocol.get_schema_definition(), f, indent=2, default=str)

# Global protocol registry
protocol_registry = ProtocolRegistry()

# Test the protocol schemas
if __name__ == "__main__":
    print("🚀 ContextForge Protocol Schemas")
    print("=" * 40)
    
    # Test all protocol versions
    for version in protocol_registry.get_supported_versions():
        protocol = protocol_registry.get_protocol(version)
        print(f"\n📋 Protocol v{version}:")
        print(f"  Capabilities: {len(protocol.capabilities)}")
        print(f"  Methods: {len(protocol.methods)}")
        print(f"  Message Formats: {len(protocol.message_formats)}")
        
        # Show sample capabilities
        for cap in protocol.capabilities[:2]:  # Show first 2
            print(f"  - {cap.name} ({cap.level}): {cap.description}")
    
    print(f"\n🎯 Latest Protocol: v{protocol_registry.get_latest_protocol().version}")
    print(f"📊 Total Protocols: {len(protocol_registry.protocols)}")
