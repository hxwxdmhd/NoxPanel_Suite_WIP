#!/usr/bin/env python3
"""
ContextForge Test Suite
======================

Comprehensive test suite for ContextForge Model Context Protocol server.
Tests all components including protocol compliance, routing, and integration.
"""

import unittest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add context module to path
sys.path.append(str(Path(__file__).parent.parent))

from context.index import (
    ContextForge, ContextRequest, ModelType, AgentIntent, ProtocolVersion,
    ContextEmbedding, contextforge
)
from context.router import ContextRouter, RoutingStrategy, ModelEndpoint
from context.protocols.schema import (
    ProtocolRegistry, MCPv1_0, MCPv1_1, MCPv2_0, protocol_registry
)

class TestContextForge(unittest.TestCase):
    """Test suite for ContextForge core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.contextforge = ContextForge()
        self.test_request = ContextRequest(
            agent="TestAgent",
            model=ModelType.GPT4O,
            intent=AgentIntent.REFACTOR,
            project_scope="TestProject",
            prompt="Test prompt for refactoring"
        )
    
    def test_contextforge_initialization(self):
        """Test ContextForge initialization"""
        self.assertIsNotNone(self.contextforge.config)
        self.assertIsInstance(self.contextforge.embeddings_cache, dict)
        self.assertIsInstance(self.contextforge.protocol_registry, dict)
        self.assertEqual(len(self.contextforge.protocol_registry), 3)  # v1.0, v1.1, v2.0
    
    def test_context_request_creation(self):
        """Test ContextRequest creation and validation"""
        self.assertEqual(self.test_request.agent, "TestAgent")
        self.assertEqual(self.test_request.model, ModelType.GPT4O)
        self.assertEqual(self.test_request.intent, AgentIntent.REFACTOR)
        self.assertIsNotNone(self.test_request.metadata)
        self.assertIn("request_id", self.test_request.metadata)
        self.assertIn("timestamp", self.test_request.metadata)
        self.assertIn("compatibility_score", self.test_request.metadata)
    
    def test_request_validation(self):
        """Test request validation"""
        # Valid request
        self.assertTrue(self.contextforge.validate_request(self.test_request))
        
        # Invalid request - missing agent
        invalid_request = ContextRequest(
            agent="",
            model=ModelType.GPT4O,
            intent=AgentIntent.REFACTOR,
            project_scope="TestProject",
            prompt="Test prompt"
        )
        self.assertFalse(self.contextforge.validate_request(invalid_request))
    
    def test_protocol_schema_retrieval(self):
        """Test protocol schema retrieval"""
        # Test specific version
        schema_v1 = self.contextforge.get_protocol_schema(ProtocolVersion.V1_0)
        self.assertEqual(schema_v1["schema_version"], "1.0")
        
        # Test latest version
        schema_latest = self.contextforge.get_protocol_schema(ProtocolVersion.LATEST)
        self.assertEqual(schema_latest["schema_version"], "2.0")
    
    def test_complexity_calculation(self):
        """Test prompt complexity calculation"""
        simple_prompt = "Hello world"
        complex_prompt = "Refactor the authentication system with proper error handling, implement JWT tokens, add rate limiting, and ensure database connections are properly managed with connection pooling. Include comprehensive unit tests and integration tests."
        
        simple_score = self.contextforge.calculate_complexity(simple_prompt)
        complex_score = self.contextforge.calculate_complexity(complex_prompt)
        
        self.assertLess(simple_score, complex_score)
        self.assertGreaterEqual(simple_score, 0.0)
        self.assertLessEqual(complex_score, 1.0)
    
    def test_context_requirements_determination(self):
        """Test context requirements determination"""
        requirements = self.contextforge.determine_context_requirements(
            "Debug the database connection issue", 
            AgentIntent.DEBUG
        )
        
        self.assertIn("error_logs", requirements)
        self.assertIn("stack_traces", requirements)
        self.assertIn("code_context", requirements)
    
    def test_model_suggestions(self):
        """Test model suggestions for different intents"""
        refactor_suggestions = self.contextforge.suggest_models("Refactor code", AgentIntent.REFACTOR)
        debug_suggestions = self.contextforge.suggest_models("Debug error", AgentIntent.DEBUG)
        
        self.assertIn(ModelType.GPT4O, refactor_suggestions)
        self.assertIn(ModelType.COPILOT, debug_suggestions)
    
    def test_priority_calculation(self):
        """Test priority calculation for different intents"""
        security_priority = self.contextforge.calculate_priority(AgentIntent.SECURITY)
        documentation_priority = self.contextforge.calculate_priority(AgentIntent.DOCUMENTATION)
        
        self.assertGreater(security_priority, documentation_priority)
        self.assertEqual(security_priority, 1.0)
    
    def test_health_status(self):
        """Test health status reporting"""
        health = self.contextforge.get_health_status()
        
        self.assertEqual(health["status"], "healthy")
        self.assertIn("uptime", health)
        self.assertIn("active_sessions", health)
        self.assertIn("cached_embeddings", health)
        self.assertIn("protocol_versions", health)
        self.assertIn("supported_models", health)
    
    @patch('context.index.ContextForge.get_context_content')
    @patch('context.index.ContextForge.generate_embedding')
    async def test_context_embedding_generation(self, mock_generate_embedding, mock_get_context_content):
        """Test context embedding generation"""
        mock_get_context_content.return_value = "Test context content"
        mock_generate_embedding.return_value = [0.1] * 1536
        
        analysis = {"context_requirements": ["code_structure", "dependencies"]}
        embeddings = await self.contextforge.get_context_embeddings("TestProject", analysis)
        
        self.assertEqual(len(embeddings), 2)
        self.assertIsInstance(embeddings[0], ContextEmbedding)
        self.assertEqual(len(embeddings[0].embedding), 1536)

class TestContextRouter(unittest.TestCase):
    """Test suite for ContextRouter"""
    
    def setUp(self):
        """Set up test environment"""
        self.contextforge = ContextForge()
        self.router = ContextRouter(self.contextforge)
        self.test_request = ContextRequest(
            agent="TestAgent",
            model=ModelType.GPT4O,
            intent=AgentIntent.REFACTOR,
            project_scope="TestProject",
            prompt="Test routing request"
        )
    
    def test_router_initialization(self):
        """Test router initialization"""
        self.assertIsNotNone(self.router.endpoints)
        self.assertIsNotNone(self.router.routing_rules)
        self.assertGreater(len(self.router.endpoints), 0)
        self.assertGreater(len(self.router.routing_rules), 0)
    
    def test_endpoint_health_check(self):
        """Test endpoint health checking"""
        # Create test endpoint
        endpoint = ModelEndpoint(ModelType.GPT4O, "https://api.test.com", "test_key")
        
        # Test healthy endpoint
        self.assertTrue(endpoint.is_healthy())
        
        # Test unhealthy endpoint
        endpoint.health_score = 0.3
        self.assertFalse(endpoint.is_healthy())
    
    def test_load_factor_calculation(self):
        """Test load factor calculation"""
        endpoint = ModelEndpoint(ModelType.GPT4O, "https://api.test.com", "test_key")
        endpoint.current_load = 50
        endpoint.max_load = 100
        
        self.assertEqual(endpoint.get_load_factor(), 0.5)
    
    def test_endpoint_metrics_update(self):
        """Test endpoint metrics update"""
        endpoint = ModelEndpoint(ModelType.GPT4O, "https://api.test.com", "test_key")
        initial_success_rate = endpoint.success_rate
        
        # Update with successful response
        endpoint.update_metrics(2.0, True)
        self.assertGreaterEqual(endpoint.success_rate, initial_success_rate)
        
        # Update with failed response
        endpoint.update_metrics(5.0, False)
        self.assertLess(endpoint.success_rate, 1.0)
    
    def test_routing_rule_retrieval(self):
        """Test routing rule retrieval"""
        # Test existing rule
        security_rule = self.router.routing_rules.get(AgentIntent.SECURITY)
        self.assertIsNotNone(security_rule)
        self.assertEqual(security_rule["strategy"], RoutingStrategy.DIRECT)
        
        # Test default rule
        default_rule = self.router.get_default_routing_rule()
        self.assertEqual(default_rule["strategy"], RoutingStrategy.DIRECT)
    
    def test_least_loaded_endpoint_selection(self):
        """Test least loaded endpoint selection"""
        endpoints = [
            ModelEndpoint(ModelType.GPT4O, "https://api1.test.com", "key1"),
            ModelEndpoint(ModelType.GPT4O, "https://api2.test.com", "key2"),
            ModelEndpoint(ModelType.GPT4O, "https://api3.test.com", "key3")
        ]
        
        # Set different load levels
        endpoints[0].current_load = 10
        endpoints[1].current_load = 5
        endpoints[2].current_load = 15
        
        selected = self.router.select_least_loaded_endpoint(endpoints)
        self.assertEqual(selected, endpoints[1])  # Should select the one with load 5
    
    def test_highest_health_endpoint_selection(self):
        """Test highest health endpoint selection"""
        endpoints = [
            ModelEndpoint(ModelType.GPT4O, "https://api1.test.com", "key1"),
            ModelEndpoint(ModelType.GPT4O, "https://api2.test.com", "key2"),
            ModelEndpoint(ModelType.GPT4O, "https://api3.test.com", "key3")
        ]
        
        # Set different health scores
        endpoints[0].health_score = 0.8
        endpoints[1].health_score = 0.95
        endpoints[2].health_score = 0.7
        
        selected = self.router.select_highest_health_endpoint(endpoints)
        self.assertEqual(selected, endpoints[1])  # Should select the one with health 0.95
    
    def test_routing_stats(self):
        """Test routing statistics"""
        stats = self.router.get_routing_stats()
        
        self.assertIn("total_requests", stats)
        self.assertIn("successful_requests", stats)
        self.assertIn("success_rate", stats)
        self.assertIn("average_response_time", stats)
        self.assertIn("active_endpoints", stats)
        self.assertIn("healthy_endpoints", stats)

class TestProtocolSchemas(unittest.TestCase):
    """Test suite for Protocol Schemas"""
    
    def setUp(self):
        """Set up test environment"""
        self.registry = ProtocolRegistry()
    
    def test_protocol_registry_initialization(self):
        """Test protocol registry initialization"""
        self.assertEqual(len(self.registry.protocols), 3)
        self.assertIn("1.0", self.registry.protocols)
        self.assertIn("1.1", self.registry.protocols)
        self.assertIn("2.0", self.registry.protocols)
    
    def test_protocol_version_retrieval(self):
        """Test protocol version retrieval"""
        v1_0 = self.registry.get_protocol("1.0")
        self.assertIsNotNone(v1_0)
        self.assertEqual(v1_0.version, "1.0")
        
        latest = self.registry.get_latest_protocol()
        self.assertEqual(latest.version, "2.0")
    
    def test_protocol_capabilities(self):
        """Test protocol capabilities"""
        v1_0 = self.registry.get_protocol("1.0")
        v2_0 = self.registry.get_protocol("2.0")
        
        # v1.0 should have fewer capabilities than v2.0
        self.assertLess(len(v1_0.capabilities), len(v2_0.capabilities))
        
        # v2.0 should have advanced capabilities
        v2_0_cap_names = [cap.name for cap in v2_0.capabilities]
        self.assertIn("dynamic_routing", v2_0_cap_names)
        self.assertIn("streaming_processing", v2_0_cap_names)
    
    def test_protocol_methods(self):
        """Test protocol methods"""
        v1_0 = self.registry.get_protocol("1.0")
        v2_0 = self.registry.get_protocol("2.0")
        
        # Both should have basic methods
        self.assertIn("prompt", v1_0.methods)
        self.assertIn("context", v1_0.methods)
        self.assertIn("embedding", v1_0.methods)
        
        # v2.0 should have additional methods
        self.assertIn("stream", v2_0.methods)
        self.assertIn("batch", v2_0.methods)
    
    def test_message_validation(self):
        """Test message validation"""
        valid_message = {
            "version": "2.0",
            "message_type": "request",
            "id": "test-123",
            "method": "prompt",
            "params": {"prompt": "test"}
        }
        
        invalid_message = {
            "version": "2.0",
            "message_type": "request"
            # Missing required id field
        }
        
        self.assertTrue(self.registry.validate_message(valid_message))
        self.assertFalse(self.registry.validate_message(invalid_message))
    
    def test_supported_versions(self):
        """Test supported versions list"""
        versions = self.registry.get_supported_versions()
        self.assertEqual(len(versions), 3)
        self.assertIn("1.0", versions)
        self.assertIn("1.1", versions)
        self.assertIn("2.0", versions)
    
    def test_schema_definition_export(self):
        """Test schema definition export"""
        v2_0 = self.registry.get_protocol("2.0")
        schema_def = v2_0.get_schema_definition()
        
        self.assertIn("version", schema_def)
        self.assertIn("capabilities", schema_def)
        self.assertIn("methods", schema_def)
        self.assertIn("message_formats", schema_def)
        self.assertIn("validation_rules", schema_def)
        
        self.assertEqual(schema_def["version"], "2.0")

class TestIntegration(unittest.TestCase):
    """Integration tests for ContextForge components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.contextforge = ContextForge()
        self.router = ContextRouter(self.contextforge)
        self.test_request = ContextRequest(
            agent="IntegrationTest",
            model=ModelType.GPT4O,
            intent=AgentIntent.ANALYZE,
            project_scope="NoxPanel.Integration",
            prompt="Analyze the system architecture for optimization opportunities"
        )
    
    async def test_end_to_end_request_processing(self):
        """Test end-to-end request processing"""
        # Process request through ContextForge
        result = await self.contextforge.process_context_request(self.test_request)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("request_id", result)
        self.assertIn("routing", result)
        self.assertIn("context_embeddings", result)
        self.assertIn("analysis", result)
    
    async def test_router_integration(self):
        """Test router integration with ContextForge"""
        # Route request through router
        routing_result = await self.router.route_request(self.test_request)
        
        self.assertIn("status", routing_result)
        self.assertIn("request_id", routing_result)
        
        # Check routing statistics
        stats = self.router.get_routing_stats()
        self.assertGreaterEqual(stats["total_requests"], 1)
    
    def test_protocol_compatibility(self):
        """Test protocol compatibility across versions"""
        # Test message compatibility across different protocol versions
        test_message = {
            "version": "1.0",
            "message_type": "request",
            "id": "compat-test-123",
            "method": "prompt",
            "params": {"prompt": "test compatibility"}
        }
        
        # Should be valid for all versions
        for version in ["1.0", "1.1", "2.0"]:
            test_message["version"] = version
            self.assertTrue(protocol_registry.validate_message(test_message))
    
    def test_health_monitoring_integration(self):
        """Test health monitoring integration"""
        # Test ContextForge health
        contextforge_health = self.contextforge.get_health_status()
        self.assertEqual(contextforge_health["status"], "healthy")
        
        # Test router health
        router_stats = self.router.get_routing_stats()
        self.assertGreaterEqual(router_stats["active_endpoints"], 1)

class TestPerformance(unittest.TestCase):
    """Performance tests for ContextForge"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.contextforge = ContextForge()
        self.router = ContextRouter(self.contextforge)
    
    def test_request_processing_performance(self):
        """Test request processing performance"""
        request = ContextRequest(
            agent="PerformanceTest",
            model=ModelType.GPT4O,
            intent=AgentIntent.GENERATE,
            project_scope="Performance.Test",
            prompt="Generate performance test code"
        )
        
        start_time = time.time()
        
        # Process multiple requests
        for i in range(10):
            request.metadata["request_id"] = f"perf-test-{i}"
            self.contextforge.validate_request(request)
            self.contextforge.calculate_complexity(request.prompt)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 10 requests in less than 1 second
        self.assertLess(processing_time, 1.0)
    
    def test_memory_usage(self):
        """Test memory usage with cache"""
        initial_cache_size = len(self.contextforge.embeddings_cache)
        
        # Add items to cache
        for i in range(100):
            cache_key = f"test-key-{i}"
            self.contextforge.embeddings_cache[cache_key] = f"test-value-{i}"
        
        final_cache_size = len(self.contextforge.embeddings_cache)
        
        # Should have added 100 items
        self.assertEqual(final_cache_size - initial_cache_size, 100)
    
    def test_concurrent_request_handling(self):
        """Test concurrent request handling capability"""
        # Test that multiple requests can be processed simultaneously
        requests = []
        for i in range(5):
            request = ContextRequest(
                agent=f"ConcurrentTest{i}",
                model=ModelType.GPT4O,
                intent=AgentIntent.REFACTOR,
                project_scope=f"Concurrent.Test.{i}",
                prompt=f"Concurrent test prompt {i}"
            )
            requests.append(request)
        
        # Process all requests
        start_time = time.time()
        for request in requests:
            self.contextforge.validate_request(request)
        end_time = time.time()
        
        # Should process quickly
        self.assertLess(end_time - start_time, 0.1)

def run_tests():
    """Run all tests"""
    print("🧪 Running ContextForge Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestContextForge,
        TestContextRouter,
        TestProtocolSchemas,
        TestIntegration,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"🎯 Tests run: {result.testsRun}")
    print(f"✅ Successful: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
