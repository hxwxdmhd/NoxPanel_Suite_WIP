#!/usr/bin/env python3
"""
ContextForge Router - Dynamic Dispatch Engine
===========================================

Dynamic dispatch based on model/agent call routing for optimal context delivery.
Handles load balancing, failover, and optimization for different AI models.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .index import ContextRequest, ModelType, AgentIntent, ContextForge
from loguru import logger

class RoutingStrategy(str, Enum):
    """Routing strategies for context delivery"""
    DIRECT = "direct"
    LOAD_BALANCED = "load_balanced"
    FAILOVER = "failover"
    ADAPTIVE = "adaptive"
    BATCH = "batch"
    STREAMING = "streaming"

class ModelEndpoint:
    """Represents a model endpoint with health and performance metrics"""
    
    def __init__(self, model_type: ModelType, endpoint_url: str, api_key: str = None):
        self.model_type = model_type
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.health_score = 1.0
        self.response_time = 0.0
        self.success_rate = 1.0
        self.current_load = 0
        self.max_load = 100
        self.last_health_check = time.time()
        
    def is_healthy(self) -> bool:
        """Check if endpoint is healthy"""
        return self.health_score > 0.5 and self.current_load < self.max_load
    
    def get_load_factor(self) -> float:
        """Get current load factor (0.0 to 1.0)"""
        return self.current_load / self.max_load
    
    def update_metrics(self, response_time: float, success: bool):
        """Update performance metrics"""
        self.response_time = response_time
        if success:
            self.success_rate = min(1.0, self.success_rate + 0.01)
        else:
            self.success_rate = max(0.0, self.success_rate - 0.05)
        
        self.health_score = self.success_rate * (1.0 - self.get_load_factor())

class ContextRouter:
    """
    Dynamic router for context requests based on model capabilities,
    load balancing, and optimization strategies.
    """
    
    def __init__(self, contextforge: ContextForge):
        self.contextforge = contextforge
        self.endpoints: Dict[ModelType, List[ModelEndpoint]] = {}
        self.routing_rules: Dict[str, Dict] = {}
        self.performance_history: List[Dict] = []
        self.load_balancer_state: Dict[str, Any] = {}
        
        # Initialize endpoints
        self.initialize_endpoints()
        
        # Initialize routing rules
        self.initialize_routing_rules()
        
        logger.info("ContextRouter initialized with dynamic dispatch capabilities")
    
    def initialize_endpoints(self):
        """Initialize model endpoints"""
        # Default endpoints (would be configurable in production)
        default_endpoints = {
            ModelType.GPT4O: [
                ModelEndpoint(ModelType.GPT4O, "https://api.openai.com/v1/chat/completions", "api_key_1"),
                ModelEndpoint(ModelType.GPT4O, "https://api.openai.com/v1/chat/completions", "api_key_2")
            ],
            ModelType.COPILOT: [
                ModelEndpoint(ModelType.COPILOT, "https://api.github.com/copilot/chat/completions", "copilot_key"),
            ],
            ModelType.CLAUDE: [
                ModelEndpoint(ModelType.CLAUDE, "https://api.anthropic.com/v1/messages", "claude_key"),
            ]
        }
        
        self.endpoints = default_endpoints
        logger.info(f"Initialized {sum(len(v) for v in self.endpoints.values())} model endpoints")
    
    def initialize_routing_rules(self):
        """Initialize routing rules based on intent and model capabilities"""
        self.routing_rules = {
            # High-priority intents get direct routing
            AgentIntent.SECURITY: {
                "strategy": RoutingStrategy.DIRECT,
                "preferred_models": [ModelType.GPT4O, ModelType.CLAUDE],
                "timeout": 60,
                "retry_count": 3
            },
            AgentIntent.DEBUG: {
                "strategy": RoutingStrategy.FAILOVER,
                "preferred_models": [ModelType.COPILOT, ModelType.GPT4O],
                "timeout": 45,
                "retry_count": 2
            },
            AgentIntent.REFACTOR: {
                "strategy": RoutingStrategy.LOAD_BALANCED,
                "preferred_models": [ModelType.GPT4O, ModelType.COPILOT],
                "timeout": 30,
                "retry_count": 2
            },
            AgentIntent.ANALYZE: {
                "strategy": RoutingStrategy.ADAPTIVE,
                "preferred_models": [ModelType.GPT4O, ModelType.CLAUDE],
                "timeout": 45,
                "retry_count": 2
            },
            AgentIntent.GENERATE: {
                "strategy": RoutingStrategy.BATCH,
                "preferred_models": [ModelType.COPILOT, ModelType.GPT4O],
                "timeout": 60,
                "retry_count": 1
            },
            AgentIntent.OPTIMIZE: {
                "strategy": RoutingStrategy.STREAMING,
                "preferred_models": [ModelType.GPT4O, ModelType.COPILOT],
                "timeout": 90,
                "retry_count": 2
            }
        }
    
    async def route_request(self, request: ContextRequest) -> Dict[str, Any]:
        """
        Route context request to optimal endpoint based on current conditions
        
        Args:
            request: Context request to route
            
        Returns:
            Routing decision with endpoint selection and strategy
        """
        logger.info(f"Routing request {request.metadata['request_id']} with intent {request.intent}")
        
        # Get routing rule for this intent
        routing_rule = self.routing_rules.get(request.intent, self.get_default_routing_rule())
        
        # Select optimal endpoint
        endpoint = await self.select_endpoint(request, routing_rule)
        
        # Execute routing strategy
        result = await self.execute_routing_strategy(request, endpoint, routing_rule)
        
        # Update performance metrics
        await self.update_performance_metrics(request, result)
        
        return result
    
    def get_default_routing_rule(self) -> Dict[str, Any]:
        """Get default routing rule for unspecified intents"""
        return {
            "strategy": RoutingStrategy.DIRECT,
            "preferred_models": [ModelType.GPT4O],
            "timeout": 30,
            "retry_count": 1
        }
    
    async def select_endpoint(self, request: ContextRequest, routing_rule: Dict[str, Any]) -> ModelEndpoint:
        """
        Select optimal endpoint based on routing strategy and current conditions
        
        Args:
            request: Context request
            routing_rule: Routing rule to apply
            
        Returns:
            Selected model endpoint
        """
        preferred_models = routing_rule.get("preferred_models", [request.model])
        strategy = routing_rule.get("strategy", RoutingStrategy.DIRECT)
        
        # Find available endpoints for preferred models
        available_endpoints = []
        for model_type in preferred_models:
            if model_type in self.endpoints:
                available_endpoints.extend([
                    ep for ep in self.endpoints[model_type] if ep.is_healthy()
                ])
        
        # If no healthy endpoints, use fallback
        if not available_endpoints:
            logger.warning(f"No healthy endpoints for preferred models {preferred_models}")
            available_endpoints = self.get_fallback_endpoints()
        
        # Select endpoint based on strategy
        if strategy == RoutingStrategy.DIRECT:
            return available_endpoints[0] if available_endpoints else None
        
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            return self.select_least_loaded_endpoint(available_endpoints)
        
        elif strategy == RoutingStrategy.FAILOVER:
            return self.select_highest_health_endpoint(available_endpoints)
        
        elif strategy == RoutingStrategy.ADAPTIVE:
            return await self.select_adaptive_endpoint(available_endpoints, request)
        
        else:
            return available_endpoints[0] if available_endpoints else None
    
    def get_fallback_endpoints(self) -> List[ModelEndpoint]:
        """Get fallback endpoints when preferred ones are unavailable"""
        all_endpoints = []
        for endpoints in self.endpoints.values():
            all_endpoints.extend([ep for ep in endpoints if ep.is_healthy()])
        
        return all_endpoints
    
    def select_least_loaded_endpoint(self, endpoints: List[ModelEndpoint]) -> ModelEndpoint:
        """Select endpoint with lowest load"""
        if not endpoints:
            return None
        
        return min(endpoints, key=lambda ep: ep.get_load_factor())
    
    def select_highest_health_endpoint(self, endpoints: List[ModelEndpoint]) -> ModelEndpoint:
        """Select endpoint with highest health score"""
        if not endpoints:
            return None
        
        return max(endpoints, key=lambda ep: ep.health_score)
    
    async def select_adaptive_endpoint(self, endpoints: List[ModelEndpoint], request: ContextRequest) -> ModelEndpoint:
        """
        Select endpoint using adaptive algorithm based on request characteristics
        
        Args:
            endpoints: Available endpoints
            request: Context request
            
        Returns:
            Optimally selected endpoint
        """
        if not endpoints:
            return None
        
        # Calculate scores for each endpoint
        scores = []
        for endpoint in endpoints:
            score = await self.calculate_adaptive_score(endpoint, request)
            scores.append((endpoint, score))
        
        # Select endpoint with highest score
        return max(scores, key=lambda x: x[1])[0]
    
    async def calculate_adaptive_score(self, endpoint: ModelEndpoint, request: ContextRequest) -> float:
        """
        Calculate adaptive score for endpoint selection
        
        Args:
            endpoint: Model endpoint to score
            request: Context request
            
        Returns:
            Adaptive score (higher is better)
        """
        # Base score from health and performance
        base_score = endpoint.health_score * 0.4 + (1.0 - endpoint.get_load_factor()) * 0.3
        
        # Model compatibility score
        compatibility_score = request.metadata.get("compatibility_score", 0.7)
        
        # Intent-specific adjustments
        intent_bonus = 0.0
        if request.intent == AgentIntent.SECURITY and endpoint.model_type in [ModelType.GPT4O, ModelType.CLAUDE]:
            intent_bonus = 0.2
        elif request.intent == AgentIntent.DEBUG and endpoint.model_type == ModelType.COPILOT:
            intent_bonus = 0.2
        
        # Response time factor
        response_time_factor = max(0.0, 1.0 - (endpoint.response_time / 10.0))
        
        total_score = base_score + compatibility_score * 0.2 + intent_bonus + response_time_factor * 0.1
        
        return min(1.0, total_score)
    
    async def execute_routing_strategy(self, request: ContextRequest, endpoint: ModelEndpoint, 
                                     routing_rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the routing strategy for the selected endpoint
        
        Args:
            request: Context request
            endpoint: Selected endpoint
            routing_rule: Routing rule to apply
            
        Returns:
            Routing execution result
        """
        if not endpoint:
            return {
                "status": "error",
                "error": "No available endpoints",
                "request_id": request.metadata["request_id"]
            }
        
        strategy = routing_rule.get("strategy", RoutingStrategy.DIRECT)
        
        try:
            start_time = time.time()
            
            if strategy == RoutingStrategy.DIRECT:
                result = await self.execute_direct_routing(request, endpoint, routing_rule)
            elif strategy == RoutingStrategy.BATCH:
                result = await self.execute_batch_routing(request, endpoint, routing_rule)
            elif strategy == RoutingStrategy.STREAMING:
                result = await self.execute_streaming_routing(request, endpoint, routing_rule)
            else:
                result = await self.execute_direct_routing(request, endpoint, routing_rule)
            
            end_time = time.time()
            
            # Update endpoint metrics
            endpoint.update_metrics(end_time - start_time, result.get("status") == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing routing strategy {strategy}: {e}")
            endpoint.update_metrics(0.0, False)
            return {
                "status": "error",
                "error": str(e),
                "request_id": request.metadata["request_id"]
            }
    
    async def execute_direct_routing(self, request: ContextRequest, endpoint: ModelEndpoint, 
                                   routing_rule: Dict[str, Any]) -> Dict[str, Any]:
        """Execute direct routing strategy"""
        # Increment load
        endpoint.current_load += 1
        
        try:
            # Process request through ContextForge
            context_response = await self.contextforge.process_context_request(request)
            
            # Add routing information
            context_response.update({
                "routing_strategy": "direct",
                "selected_endpoint": {
                    "model_type": endpoint.model_type,
                    "endpoint_url": endpoint.endpoint_url,
                    "health_score": endpoint.health_score,
                    "load_factor": endpoint.get_load_factor()
                },
                "execution_time": time.time()
            })
            
            return context_response
            
        finally:
            # Decrement load
            endpoint.current_load = max(0, endpoint.current_load - 1)
    
    async def execute_batch_routing(self, request: ContextRequest, endpoint: ModelEndpoint, 
                                  routing_rule: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch routing strategy"""
        # For batch processing, we might split the request into smaller chunks
        batch_size = routing_rule.get("batch_size", 5)
        
        # Simulate batch processing
        result = await self.execute_direct_routing(request, endpoint, routing_rule)
        result["routing_strategy"] = "batch"
        result["batch_size"] = batch_size
        
        return result
    
    async def execute_streaming_routing(self, request: ContextRequest, endpoint: ModelEndpoint, 
                                      routing_rule: Dict[str, Any]) -> Dict[str, Any]:
        """Execute streaming routing strategy"""
        # For streaming, we process in chunks and return intermediate results
        result = await self.execute_direct_routing(request, endpoint, routing_rule)
        result["routing_strategy"] = "streaming"
        result["streaming_enabled"] = True
        
        return result
    
    async def update_performance_metrics(self, request: ContextRequest, result: Dict[str, Any]):
        """Update performance metrics for routing decisions"""
        metrics = {
            "request_id": request.metadata["request_id"],
            "intent": request.intent,
            "model": request.model,
            "status": result.get("status", "unknown"),
            "execution_time": result.get("execution_time", 0.0),
            "routing_strategy": result.get("routing_strategy", "unknown"),
            "timestamp": time.time()
        }
        
        # Add to performance history
        self.performance_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        logger.info(f"Updated performance metrics for request {request.metadata['request_id']}")
    
    async def health_check_endpoints(self):
        """Perform health check on all endpoints"""
        for model_type, endpoints in self.endpoints.items():
            for endpoint in endpoints:
                try:
                    # Simple health check (would be more sophisticated in production)
                    await self.check_endpoint_health(endpoint)
                except Exception as e:
                    logger.warning(f"Health check failed for {endpoint.endpoint_url}: {e}")
                    endpoint.health_score = max(0.0, endpoint.health_score - 0.1)
    
    async def check_endpoint_health(self, endpoint: ModelEndpoint):
        """Check health of a specific endpoint"""
        # Placeholder health check
        endpoint.last_health_check = time.time()
        
        # In production, this would make actual HTTP requests
        # For now, just maintain good health
        endpoint.health_score = min(1.0, endpoint.health_score + 0.05)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total_requests = len(self.performance_history)
        successful_requests = len([m for m in self.performance_history if m["status"] == "success"])
        
        avg_response_time = 0.0
        if total_requests > 0:
            avg_response_time = sum(m["execution_time"] for m in self.performance_history) / total_requests
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / max(1, total_requests),
            "average_response_time": avg_response_time,
            "active_endpoints": sum(len(endpoints) for endpoints in self.endpoints.values()),
            "healthy_endpoints": sum(len([ep for ep in endpoints if ep.is_healthy()]) 
                                   for endpoints in self.endpoints.values())
        }

# Test the router
if __name__ == "__main__":
    from .index import contextforge
    
    # Create router instance
    router = ContextRouter(contextforge)
    
    # Test routing
    test_request = ContextRequest(
        agent="Copilot",
        model=ModelType.GPT4O,
        intent=AgentIntent.REFACTOR,
        project_scope="NoxPanel.Security.Auth",
        prompt="Refactor authentication system"
    )
    
    print("🚀 ContextForge Router - Dynamic Dispatch Engine")
    print("=" * 50)
    print(f"Routing Stats: {router.get_routing_stats()}")
    print(f"Available Endpoints: {sum(len(v) for v in router.endpoints.values())}")
    print(f"Routing Rules: {len(router.routing_rules)}")
