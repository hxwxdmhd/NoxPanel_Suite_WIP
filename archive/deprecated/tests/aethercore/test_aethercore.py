"""
AetherCore MSP Server Tests
==========================

Comprehensive test suite for AetherCore Model Serving Protocol server.
"""

import asyncio
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

# Import AetherCore modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aethercore.index import app, aethercore_server
from aethercore.models.model_metadata import ModelMetadata, ModelType, ModelStatus, ModelFormat
from aethercore.services.model_service import ModelService
from aethercore.services.inference_service import InferenceService

# Test client
client = TestClient(app)

class TestAetherCoreServer:
    """Test AetherCore server functionality"""
    
    def test_heartbeat(self):
        """Test heartbeat endpoint"""
        response = client.get("/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "system_info" in data
    
    def test_list_models(self):
        """Test list models endpoint"""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check if we have default models
        if data:
            model = data[0]
            assert "model_id" in model
            assert "name" in model
            assert "status" in model
    
    def test_load_model(self):
        """Test load model endpoint"""
        response = client.post("/models/test-model/load")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["loading", "already_loaded"]
        assert data["model_id"] == "test-model"
    
    def test_serve_model(self):
        """Test model serving endpoint"""
        # First load a model
        client.post("/models/default-model/load")
        
        # Wait a moment for loading
        import time
        time.sleep(1)
        
        # Serve inference request
        request_data = {
            "model_id": "default-model",
            "inputs": {"text": "Hello world"},
            "parameters": {"temperature": 0.7}
        }
        
        response = client.post("/serve", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "default-model"
        assert "outputs" in data
        assert "processing_time_ms" in data
        assert "request_id" in data
    
    def test_metrics(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "total_models" in data
        assert "system_metrics" in data

class TestModelService:
    """Test model service functionality"""
    
    @pytest.fixture
    def model_service(self):
        """Create model service instance"""
        return ModelService()
    
    @pytest.mark.asyncio
    async def test_list_models(self, model_service):
        """Test listing models"""
        models = await model_service.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        
        # Check model structure
        model = models[0]
        assert "model_id" in model
        assert "name" in model
        assert "model_type" in model
        assert "status" in model
    
    @pytest.mark.asyncio
    async def test_load_model(self, model_service):
        """Test loading a model"""
        model_id = "test-model"
        
        # Load model
        success = await model_service.load_model(model_id)
        assert success
        
        # Check if model is loaded
        is_loaded = await model_service.is_model_loaded(model_id)
        assert is_loaded
        
        # Get model info
        info = await model_service.get_model_info(model_id)
        assert info is not None
        assert info["model_id"] == model_id
        assert info["status"] == ModelStatus.READY.value
    
    @pytest.mark.asyncio
    async def test_unload_model(self, model_service):
        """Test unloading a model"""
        model_id = "test-model"
        
        # Load model first
        await model_service.load_model(model_id)
        
        # Unload model
        success = await model_service.unload_model(model_id)
        assert success
        
        # Check if model is unloaded
        is_loaded = await model_service.is_model_loaded(model_id)
        assert not is_loaded
    
    @pytest.mark.asyncio
    async def test_model_stats(self, model_service):
        """Test getting model statistics"""
        model_id = "test-model"
        
        # Load model
        await model_service.load_model(model_id)
        
        # Get stats
        stats = await model_service.get_model_stats(model_id)
        assert stats is not None
        assert stats["model_id"] == model_id
        assert "total_requests" in stats
        assert "avg_response_time_ms" in stats
    
    @pytest.mark.asyncio
    async def test_warmup_model(self, model_service):
        """Test warming up a model"""
        model_id = "test-model"
        
        # Load model
        await model_service.load_model(model_id)
        
        # Warmup model
        success = await model_service.warmup_model(model_id)
        assert success

class TestInferenceService:
    """Test inference service functionality"""
    
    @pytest.fixture
    def inference_service(self):
        """Create inference service instance"""
        return InferenceService()
    
    @pytest.mark.asyncio
    async def test_process_inference(self, inference_service):
        """Test processing inference"""
        model_id = "test-model"
        
        # Load model first
        await inference_service.model_service.load_model(model_id)
        
        # Process inference
        inputs = {"text": "Hello world"}
        outputs = await inference_service.process_inference(model_id, inputs)
        
        assert outputs is not None
        assert "predictions" in outputs
        assert "confidence" in outputs
    
    @pytest.mark.asyncio
    async def test_batch_inference(self, inference_service):
        """Test batch inference processing"""
        model_id = "test-model"
        
        # Load model first
        await inference_service.model_service.load_model(model_id)
        
        # Process batch inference
        batch_inputs = [
            {"text": "Hello world"},
            {"text": "How are you?"},
            {"text": "Good morning"}
        ]
        
        batch_outputs = await inference_service.process_batch_inference(model_id, batch_inputs)
        
        assert len(batch_outputs) == 3
        for output in batch_outputs:
            assert "predictions" in output or "error" in output
    
    @pytest.mark.asyncio
    async def test_quick_predict(self, inference_service):
        """Test quick prediction"""
        model_id = "test-model"
        
        # Load model first
        await inference_service.model_service.load_model(model_id)
        
        # Quick predict
        result = await inference_service.quick_predict(model_id, "Test text")
        
        assert result is not None
        assert "predictions" in result
    
    @pytest.mark.asyncio
    async def test_model_health_check(self, inference_service):
        """Test model health check"""
        model_id = "test-model"
        
        # Load model first
        await inference_service.model_service.load_model(model_id)
        
        # Check health
        health = await inference_service.check_model_health(model_id)
        
        assert health is not None
        assert health["model_id"] == model_id
        assert "health_status" in health
        assert "status" in health
    
    @pytest.mark.asyncio
    async def test_stream_inference(self, inference_service):
        """Test streaming inference"""
        model_id = "test-model"
        
        # Load model first
        await inference_service.model_service.load_model(model_id)
        
        # Stream inference
        inputs = {"text": "Test streaming"}
        chunks = []
        
        async for chunk in inference_service.stream_inference(model_id, inputs):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert chunks[-1]["is_final"] is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, inference_service):
        """Test service cleanup"""
        # This should not raise any exceptions
        await inference_service.cleanup()

class TestModelMetadata:
    """Test model metadata functionality"""
    
    def test_model_metadata_creation(self):
        """Test creating model metadata"""
        metadata = ModelMetadata(
            model_id="test-model",
            name="Test Model",
            model_type=ModelType.TRANSFORMER,
            model_format=ModelFormat.HUGGINGFACE,
            version="1.0.0",
            description="Test model description",
            input_schema={"text": {"type": "string"}},
            output_schema={"label": {"type": "string"}}
        )
        
        assert metadata.model_id == "test-model"
        assert metadata.name == "Test Model"
        assert metadata.model_type == ModelType.TRANSFORMER
        assert metadata.version == "1.0.0"
    
    def test_model_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = ModelMetadata(
            model_id="test-model",
            name="Test Model",
            model_type=ModelType.TRANSFORMER,
            model_format=ModelFormat.HUGGINGFACE,
            version="1.0.0",
            description="Test model description",
            input_schema={"text": {"type": "string"}},
            output_schema={"label": {"type": "string"}}
        )
        
        data = metadata.to_dict()
        assert isinstance(data, dict)
        assert data["model_id"] == "test-model"
        assert data["model_type"] == "transformer"
        assert data["model_format"] == "huggingface"
    
    def test_model_metadata_from_dict(self):
        """Test creating metadata from dictionary"""
        data = {
            "model_id": "test-model",
            "name": "Test Model",
            "model_type": "transformer",
            "model_format": "huggingface",
            "version": "1.0.0",
            "description": "Test description",
            "input_schema": {"text": {"type": "string"}},
            "output_schema": {"label": {"type": "string"}},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        metadata = ModelMetadata.from_dict(data)
        assert metadata.model_id == "test-model"
        assert metadata.model_type == ModelType.TRANSFORMER
        assert metadata.model_format == ModelFormat.HUGGINGFACE

class TestIntegration:
    """Integration tests for AetherCore"""
    
    def test_full_model_lifecycle(self):
        """Test complete model lifecycle"""
        # Load model
        response = client.post("/models/integration-test/load")
        assert response.status_code == 200
        
        # Wait for loading
        import time
        time.sleep(2)
        
        # Check model status
        response = client.get("/models")
        assert response.status_code == 200
        models = response.json()
        
        # Find our model
        test_model = None
        for model in models:
            if model["model_id"] == "integration-test":
                test_model = model
                break
        
        if test_model:
            assert test_model["status"] == "ready"
        
        # Serve inference
        request_data = {
            "model_id": "integration-test",
            "inputs": {"text": "Integration test"},
            "parameters": {"temperature": 0.5}
        }
        
        response = client.post("/serve", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "outputs" in data
        
        # Unload model
        response = client.post("/models/integration-test/unload")
        assert response.status_code == 200
        assert response.json()["status"] == "unloaded"
    
    def test_error_handling(self):
        """Test error handling"""
        # Try to serve with non-existent model
        request_data = {
            "model_id": "non-existent-model",
            "inputs": {"text": "Test"},
        }
        
        response = client.post("/serve", json=request_data)
        assert response.status_code == 404
        
        # Try to unload non-existent model
        response = client.post("/models/non-existent/unload")
        assert response.status_code == 404
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        # Load model
        client.post("/models/concurrent-test/load")
        
        # Wait for loading
        import time
        time.sleep(1)
        
        # Send multiple concurrent requests
        import threading
        import requests
        
        responses = []
        
        def make_request():
            request_data = {
                "model_id": "concurrent-test",
                "inputs": {"text": "Concurrent test"},
            }
            
            # Use requests instead of test client for real concurrency
            resp = requests.post("http://localhost:8001/serve", json=request_data)
            responses.append(resp)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check responses (may fail if server not running)
        # This test requires the server to be running
        # assert len(responses) == 5
        # for resp in responses:
        #     assert resp.status_code == 200

class TestPerformance:
    """Performance tests for AetherCore"""
    
    def test_model_loading_performance(self):
        """Test model loading performance"""
        import time
        
        model_id = "performance-test"
        
        start_time = time.time()
        response = client.post(f"/models/{model_id}/load")
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 5.0  # Should load within 5 seconds
    
    def test_inference_latency(self):
        """Test inference latency"""
        # Load model
        client.post("/models/latency-test/load")
        
        # Wait for loading
        import time
        time.sleep(1)
        
        # Test inference latency
        request_data = {
            "model_id": "latency-test",
            "inputs": {"text": "Latency test"},
        }
        
        start_time = time.time()
        response = client.post("/serve", json=request_data)
        inference_time = time.time() - start_time
        
        assert response.status_code == 200
        assert inference_time < 1.0  # Should respond within 1 second
        
        # Check reported processing time
        data = response.json()
        assert data["processing_time_ms"] < 1000  # Should be under 1000ms
    
    def test_throughput(self):
        """Test request throughput"""
        # Load model
        client.post("/models/throughput-test/load")
        
        # Wait for loading
        import time
        time.sleep(1)
        
        # Send multiple requests and measure throughput
        num_requests = 10
        start_time = time.time()
        
        for i in range(num_requests):
            request_data = {
                "model_id": "throughput-test",
                "inputs": {"text": f"Throughput test {i}"},
            }
            
            response = client.post("/serve", json=request_data)
            assert response.status_code == 200
        
        total_time = time.time() - start_time
        throughput = num_requests / total_time
        
        assert throughput > 5.0  # Should handle at least 5 requests per second

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
