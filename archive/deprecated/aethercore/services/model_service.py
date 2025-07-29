"""
AetherCore Model Service
=======================

Model management service for loading, unloading, and managing AI models.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import psutil
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel, AutoConfig
import onnxruntime as ort
from pathlib import Path

from .model_metadata import ModelMetadata, ModelInstance, ModelType, ModelStatus, ModelFormat

logger = logging.getLogger(__name__)

class ModelService:
    """
    Service for managing AI models
    """
    
    def __init__(self):
        self.models: Dict[str, ModelInstance] = {}
        self.model_registry: Dict[str, ModelMetadata] = {}
        self.load_locks: Dict[str, asyncio.Lock] = {}
        
        # Initialize default models
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize default model registry"""
        default_models = [
            {
                "model_id": "text-classifier",
                "name": "Default Text Classifier",
                "model_type": ModelType.TRANSFORMER,
                "model_format": ModelFormat.HUGGINGFACE,
                "version": "1.0.0",
                "description": "Default text classification model",
                "input_schema": {
                    "text": {"type": "string", "required": True}
                },
                "output_schema": {
                    "label": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            },
            {
                "model_id": "text-generator",
                "name": "Default Text Generator",
                "model_type": ModelType.TRANSFORMER,
                "model_format": ModelFormat.HUGGINGFACE,
                "version": "1.0.0",
                "description": "Default text generation model",
                "input_schema": {
                    "prompt": {"type": "string", "required": True},
                    "max_length": {"type": "integer", "default": 100}
                },
                "output_schema": {
                    "generated_text": {"type": "string"}
                }
            }
        ]
        
        for model_config in default_models:
            metadata = ModelMetadata(
                model_id=model_config["model_id"],
                name=model_config["name"],
                model_type=model_config["model_type"],
                model_format=model_config["model_format"],
                version=model_config["version"],
                description=model_config["description"],
                input_schema=model_config["input_schema"],
                output_schema=model_config["output_schema"]
            )
            self.model_registry[model_config["model_id"]] = metadata
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        models = []
        
        for model_id, metadata in self.model_registry.items():
            model_info = {
                "model_id": model_id,
                "name": metadata.name,
                "model_type": metadata.model_type.value,
                "version": metadata.version,
                "description": metadata.description,
                "status": "unloaded"
            }
            
            # Check if model is loaded
            if model_id in self.models:
                instance = self.models[model_id]
                model_info.update({
                    "status": instance.status.value,
                    "memory_usage_mb": instance.memory_usage_mb,
                    "last_used": instance.last_used.isoformat() if instance.last_used else None,
                    "total_requests": instance.total_requests,
                    "avg_response_time_ms": instance.avg_response_time_ms,
                    "health_status": instance.get_health_status()
                })
            
            models.append(model_info)
        
        return models
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        if model_id not in self.model_registry:
            return None
        
        metadata = self.model_registry[model_id]
        info = metadata.to_dict()
        
        # Add runtime information if model is loaded
        if model_id in self.models:
            instance = self.models[model_id]
            info.update({
                "status": instance.status.value,
                "load_time_ms": instance.load_time_ms,
                "memory_usage_mb": instance.memory_usage_mb,
                "last_used": instance.last_used.isoformat() if instance.last_used else None,
                "error_message": instance.error_message,
                "error_count": instance.error_count,
                "total_requests": instance.total_requests,
                "successful_requests": instance.successful_requests,
                "failed_requests": instance.failed_requests,
                "avg_response_time_ms": instance.avg_response_time_ms,
                "health_status": instance.get_health_status()
            })
        else:
            info["status"] = ModelStatus.UNLOADED.value
        
        return info
    
    async def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded"""
        return model_id in self.models and self.models[model_id].status == ModelStatus.READY
    
    async def load_model(
        self,
        model_id: str,
        model_path: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Load a model into memory"""
        try:
            # Get or create lock for this model
            if model_id not in self.load_locks:
                self.load_locks[model_id] = asyncio.Lock()
            
            async with self.load_locks[model_id]:
                # Check if model is already loaded
                if model_id in self.models and self.models[model_id].status == ModelStatus.READY:
                    return True
                
                # Get model metadata
                if model_id not in self.model_registry:
                    logger.error(f"Model {model_id} not found in registry")
                    return False
                
                metadata = self.model_registry[model_id]
                
                # Create model instance
                instance = ModelInstance(
                    model_id=model_id,
                    metadata=metadata,
                    status=ModelStatus.LOADING
                )
                
                self.models[model_id] = instance
                
                logger.info(f"Loading model {model_id}...")
                start_time = time.time()
                
                # Load model based on type
                if metadata.model_type == ModelType.TRANSFORMER:
                    await self._load_transformer_model(instance, model_path, config)
                elif metadata.model_type == ModelType.ONNX:
                    await self._load_onnx_model(instance, model_path, config)
                elif metadata.model_type == ModelType.PYTORCH:
                    await self._load_pytorch_model(instance, model_path, config)
                else:
                    # Mock model for demonstration
                    await self._load_mock_model(instance, config)
                
                # Update load time
                instance.load_time_ms = (time.time() - start_time) * 1000
                instance.status = ModelStatus.READY
                
                # Update memory usage
                instance.memory_usage_mb = self._get_model_memory_usage(instance)
                
                logger.info(f"Model {model_id} loaded successfully in {instance.load_time_ms:.2f}ms")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            
            # Update instance with error
            if model_id in self.models:
                self.models[model_id].status = ModelStatus.ERROR
                self.models[model_id].error_message = str(e)
                self.models[model_id].error_count += 1
            
            return False
    
    async def _load_transformer_model(
        self,
        instance: ModelInstance,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Load a transformer model"""
        try:
            # For demonstration, create a mock transformer model
            instance.instance = {
                "type": "transformer",
                "model_name": instance.metadata.name,
                "config": config or {}
            }
            
            # Mock tokenizer
            instance.tokenizer = {
                "type": "mock_tokenizer",
                "vocab_size": 30000
            }
            
            await asyncio.sleep(1)  # Simulate loading time
            
        except Exception as e:
            raise Exception(f"Failed to load transformer model: {str(e)}")
    
    async def _load_onnx_model(
        self,
        instance: ModelInstance,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Load an ONNX model"""
        try:
            # For demonstration, create a mock ONNX model
            instance.instance = {
                "type": "onnx",
                "model_name": instance.metadata.name,
                "config": config or {}
            }
            
            await asyncio.sleep(0.5)  # Simulate loading time
            
        except Exception as e:
            raise Exception(f"Failed to load ONNX model: {str(e)}")
    
    async def _load_pytorch_model(
        self,
        instance: ModelInstance,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Load a PyTorch model"""
        try:
            # For demonstration, create a mock PyTorch model
            instance.instance = {
                "type": "pytorch",
                "model_name": instance.metadata.name,
                "config": config or {}
            }
            
            await asyncio.sleep(0.8)  # Simulate loading time
            
        except Exception as e:
            raise Exception(f"Failed to load PyTorch model: {str(e)}")
    
    async def _load_mock_model(
        self,
        instance: ModelInstance,
        config: Optional[Dict[str, Any]] = None
    ):
        """Load a mock model for testing"""
        instance.instance = {
            "type": "mock",
            "model_name": instance.metadata.name,
            "config": config or {},
            "version": instance.metadata.version
        }
        
        await asyncio.sleep(0.1)  # Simulate loading time
    
    def _get_model_memory_usage(self, instance: ModelInstance) -> float:
        """Get memory usage of a model"""
        # For demonstration, return a mock memory usage
        if instance.metadata.model_type == ModelType.TRANSFORMER:
            return 512.0  # MB
        elif instance.metadata.model_type == ModelType.ONNX:
            return 256.0  # MB
        else:
            return 128.0  # MB
    
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        try:
            if model_id not in self.models:
                return False
            
            instance = self.models[model_id]
            instance.status = ModelStatus.UNLOADING
            
            # Cleanup model resources
            instance.instance = None
            instance.tokenizer = None
            instance.config = None
            
            # Remove from loaded models
            del self.models[model_id]
            
            logger.info(f"Model {model_id} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {str(e)}")
            return False
    
    async def reload_model(self, model_id: str) -> bool:
        """Reload a model"""
        # Unload first
        await self.unload_model(model_id)
        
        # Load again
        return await self.load_model(model_id)
    
    async def get_model_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model status and health"""
        if model_id not in self.models:
            return None
        
        instance = self.models[model_id]
        return {
            "model_id": model_id,
            "status": instance.status.value,
            "health_status": instance.get_health_status(),
            "memory_usage_mb": instance.memory_usage_mb,
            "last_used": instance.last_used.isoformat() if instance.last_used else None,
            "error_message": instance.error_message,
            "error_count": instance.error_count,
            "uptime_seconds": (datetime.now() - instance.metadata.loaded_at).total_seconds() if instance.metadata.loaded_at else 0
        }
    
    async def get_model_stats(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model performance statistics"""
        if model_id not in self.models:
            return None
        
        instance = self.models[model_id]
        return {
            "model_id": model_id,
            "total_requests": instance.total_requests,
            "successful_requests": instance.successful_requests,
            "failed_requests": instance.failed_requests,
            "avg_response_time_ms": instance.avg_response_time_ms,
            "success_rate": instance.successful_requests / max(instance.total_requests, 1),
            "error_rate": instance.failed_requests / max(instance.total_requests, 1),
            "load_time_ms": instance.load_time_ms,
            "memory_usage_mb": instance.memory_usage_mb,
            "last_used": instance.last_used.isoformat() if instance.last_used else None
        }
    
    async def warmup_model(self, model_id: str) -> bool:
        """Warm up a model with dummy requests"""
        if model_id not in self.models or self.models[model_id].status != ModelStatus.READY:
            return False
        
        try:
            # Simulate warmup with dummy data
            for _ in range(3):
                await asyncio.sleep(0.1)
            
            logger.info(f"Model {model_id} warmed up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to warm up model {model_id}: {str(e)}")
            return False
