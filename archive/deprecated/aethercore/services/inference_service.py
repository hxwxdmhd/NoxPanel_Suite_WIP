"""
AetherCore Inference Service
===========================

Inference service for processing model predictions and serving requests.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import uuid
import numpy as np
from .model_service import ModelService

logger = logging.getLogger(__name__)

class InferenceService:
    """
    Service for processing model inference requests
    """
    
    def __init__(self, model_service: Optional[ModelService] = None):
        self.model_service = model_service or ModelService()
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.processing_workers: List[asyncio.Task] = []
        
        # Start processing workers
        self._start_workers()
    
    def _start_workers(self, num_workers: int = 4):
        """Start background processing workers"""
        for i in range(num_workers):
            worker = asyncio.create_task(self._process_worker(f"worker-{i}"))
            self.processing_workers.append(worker)
    
    async def _process_worker(self, worker_id: str):
        """Background worker for processing requests"""
        while True:
            try:
                # Wait for request
                request_data = await self.request_queue.get()
                
                # Process request
                await self._process_request(request_data)
                
                # Mark task as done
                self.request_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_request(self, request_data: Dict[str, Any]):
        """Process a single inference request"""
        try:
            model_id = request_data["model_id"]
            inputs = request_data["inputs"]
            parameters = request_data.get("parameters", {})
            
            # Get model instance
            if model_id not in self.model_service.models:
                raise Exception(f"Model {model_id} not loaded")
            
            instance = self.model_service.models[model_id]
            
            # Process inference based on model type
            if instance.metadata.model_type.value == "transformer":
                outputs = await self._process_transformer_inference(instance, inputs, parameters)
            elif instance.metadata.model_type.value == "onnx":
                outputs = await self._process_onnx_inference(instance, inputs, parameters)
            elif instance.metadata.model_type.value == "pytorch":
                outputs = await self._process_pytorch_inference(instance, inputs, parameters)
            else:
                outputs = await self._process_mock_inference(instance, inputs, parameters)
            
            # Update instance statistics
            processing_time = request_data.get("processing_time_ms", 0)
            instance.update_stats(processing_time, success=True)
            
            # Store result
            request_data["outputs"] = outputs
            request_data["status"] = "success"
            
        except Exception as e:
            logger.error(f"Inference processing failed: {str(e)}")
            request_data["error"] = str(e)
            request_data["status"] = "error"
            
            # Update instance statistics
            model_id = request_data.get("model_id")
            if model_id and model_id in self.model_service.models:
                processing_time = request_data.get("processing_time_ms", 0)
                self.model_service.models[model_id].update_stats(processing_time, success=False)
    
    async def is_model_ready(self, model_id: str) -> bool:
        """Check if a model is ready for inference"""
        return await self.model_service.is_model_loaded(model_id)
    
    async def process_inference(
        self,
        model_id: str,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Process a single inference request"""
        start_time = time.time()
        
        # Validate model
        if not await self.is_model_ready(model_id):
            raise Exception(f"Model {model_id} is not ready")
        
        # Get model instance
        instance = self.model_service.models[model_id]
        
        try:
            # Process based on model type
            if instance.metadata.model_type.value == "transformer":
                outputs = await self._process_transformer_inference(instance, inputs, parameters)
            elif instance.metadata.model_type.value == "onnx":
                outputs = await self._process_onnx_inference(instance, inputs, parameters)
            elif instance.metadata.model_type.value == "pytorch":
                outputs = await self._process_pytorch_inference(instance, inputs, parameters)
            else:
                outputs = await self._process_mock_inference(instance, inputs, parameters)
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            instance.update_stats(processing_time, success=True)
            
            return outputs
            
        except Exception as e:
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            instance.update_stats(processing_time, success=False)
            raise e
    
    async def process_batch_inference(
        self,
        model_id: str,
        batch_inputs: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """Process a batch of inference requests"""
        if not await self.is_model_ready(model_id):
            raise Exception(f"Model {model_id} is not ready")
        
        # Process each input in the batch
        batch_outputs = []
        
        for inputs in batch_inputs:
            try:
                outputs = await self.process_inference(model_id, inputs, parameters, timeout_seconds)
                batch_outputs.append(outputs)
            except Exception as e:
                # Add error to batch
                batch_outputs.append({
                    "error": str(e),
                    "status": "error"
                })
        
        return batch_outputs
    
    async def quick_predict(self, model_id: str, text: str) -> Dict[str, Any]:
        """Quick prediction for simple text input"""
        inputs = {"text": text}
        return await self.process_inference(model_id, inputs)
    
    async def stream_inference(
        self,
        model_id: str,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream inference results"""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        if not await self.is_model_ready(model_id):
            yield {
                "request_id": request_id,
                "model_id": model_id,
                "error": f"Model {model_id} is not ready",
                "status": "error"
            }
            return
        
        # For demonstration, simulate streaming output
        chunk_count = 5
        for i in range(chunk_count):
            await asyncio.sleep(0.1)  # Simulate processing time
            
            yield {
                "request_id": request_id,
                "model_id": model_id,
                "chunk_id": i,
                "outputs": {
                    "chunk": f"Generated chunk {i + 1}",
                    "progress": (i + 1) / chunk_count
                },
                "is_final": i == chunk_count - 1,
                "processing_time_ms": (i + 1) * 100,
                "status": "success"
            }
    
    async def check_model_health(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Check model health for inference"""
        if model_id not in self.model_service.models:
            return None
        
        instance = self.model_service.models[model_id]
        
        # Perform health check
        health_status = "healthy"
        last_error = None
        
        try:
            # Test inference with dummy data
            dummy_inputs = {"text": "health check"}
            await self._process_mock_inference(instance, dummy_inputs, {})
            
        except Exception as e:
            health_status = "unhealthy"
            last_error = str(e)
        
        return {
            "model_id": model_id,
            "health_status": health_status,
            "status": instance.status.value,
            "last_error": last_error,
            "memory_usage_mb": instance.memory_usage_mb,
            "total_requests": instance.total_requests,
            "error_rate": instance.failed_requests / max(instance.total_requests, 1),
            "avg_response_time_ms": instance.avg_response_time_ms,
            "last_used": instance.last_used.isoformat() if instance.last_used else None
        }
    
    async def get_inference_stats(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get inference statistics for a model"""
        return await self.model_service.get_model_stats(model_id)
    
    async def _process_transformer_inference(
        self,
        instance,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process transformer model inference"""
        # Simulate transformer processing
        await asyncio.sleep(0.2)
        
        text = inputs.get("text", "")
        
        # Mock transformer outputs
        return {
            "predictions": [0.8, 0.15, 0.05],
            "labels": ["positive", "neutral", "negative"],
            "confidence": 0.8,
            "processed_text": text,
            "model_type": "transformer",
            "tokens": len(text.split())
        }
    
    async def _process_onnx_inference(
        self,
        instance,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process ONNX model inference"""
        # Simulate ONNX processing
        await asyncio.sleep(0.1)
        
        # Mock ONNX outputs
        return {
            "predictions": np.random.rand(3).tolist(),
            "confidence": 0.9,
            "model_type": "onnx",
            "processing_time_ms": 100
        }
    
    async def _process_pytorch_inference(
        self,
        instance,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process PyTorch model inference"""
        # Simulate PyTorch processing
        await asyncio.sleep(0.15)
        
        # Mock PyTorch outputs
        return {
            "predictions": np.random.rand(5).tolist(),
            "confidence": 0.85,
            "model_type": "pytorch",
            "processing_time_ms": 150
        }
    
    async def _process_mock_inference(
        self,
        instance,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process mock model inference"""
        # Simulate processing
        await asyncio.sleep(0.05)
        
        # Mock outputs based on input
        text = inputs.get("text", inputs.get("prompt", ""))
        
        return {
            "predictions": [0.7, 0.2, 0.1],
            "confidence": 0.75,
            "processed_input": text,
            "model_type": "mock",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": 50
        }
    
    async def cleanup(self):
        """Cleanup inference service"""
        # Cancel all workers
        for worker in self.processing_workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.processing_workers, return_exceptions=True)
        
        # Clear active requests
        self.active_requests.clear()
        
        logger.info("Inference service cleaned up")
