"""
AetherCore API Routes - Model Management
======================================

Model management routes for loading, unloading, and managing AI models.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging
from ..models.model_metadata import ModelMetadata, ModelType, ModelStatus
from ..services.model_service import ModelService

router = APIRouter(prefix="/api/models", tags=["models"])

# Request/Response Models
class LoadModelRequest(BaseModel):
    model_path: Optional[str] = None
    model_type: ModelType = ModelType.TRANSFORMER
    config: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    model_id: str
    status: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class ModelListResponse(BaseModel):
    models: List[Dict[str, Any]]
    total_count: int
    active_count: int

# Get model service instance
def get_model_service():
    return ModelService()

@router.get("/", response_model=ModelListResponse)
async def list_models(service: ModelService = Depends(get_model_service)):
    """List all available models"""
    models = await service.list_models()
    active_models = [m for m in models if m.get("status") == "ready"]
    
    return ModelListResponse(
        models=models,
        total_count=len(models),
        active_count=len(active_models)
    )

@router.get("/{model_id}")
async def get_model(model_id: str, service: ModelService = Depends(get_model_service)):
    """Get detailed information about a specific model"""
    model_info = await service.get_model_info(model_id)
    
    if not model_info:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model_info

@router.post("/{model_id}/load", response_model=ModelResponse)
async def load_model(
    model_id: str,
    request: LoadModelRequest,
    background_tasks: BackgroundTasks,
    service: ModelService = Depends(get_model_service)
):
    """Load a model into memory"""
    # Check if model is already loaded
    if await service.is_model_loaded(model_id):
        return ModelResponse(
            model_id=model_id,
            status="already_loaded",
            message="Model is already loaded and ready"
        )
    
    # Start loading in background
    background_tasks.add_task(
        service.load_model,
        model_id,
        request.model_path,
        request.model_type,
        request.config
    )
    
    return ModelResponse(
        model_id=model_id,
        status="loading",
        message="Model loading started"
    )

@router.post("/{model_id}/unload", response_model=ModelResponse)
async def unload_model(model_id: str, service: ModelService = Depends(get_model_service)):
    """Unload a model from memory"""
    success = await service.unload_model(model_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Model not found or already unloaded")
    
    return ModelResponse(
        model_id=model_id,
        status="unloaded",
        message="Model unloaded successfully"
    )

@router.post("/{model_id}/reload", response_model=ModelResponse)
async def reload_model(
    model_id: str,
    background_tasks: BackgroundTasks,
    service: ModelService = Depends(get_model_service)
):
    """Reload a model (unload and load again)"""
    # Unload first
    await service.unload_model(model_id)
    
    # Reload in background
    background_tasks.add_task(service.reload_model, model_id)
    
    return ModelResponse(
        model_id=model_id,
        status="reloading",
        message="Model reload started"
    )

@router.get("/{model_id}/status")
async def get_model_status(model_id: str, service: ModelService = Depends(get_model_service)):
    """Get model status and health"""
    status = await service.get_model_status(model_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return status

@router.get("/{model_id}/stats")
async def get_model_stats(model_id: str, service: ModelService = Depends(get_model_service)):
    """Get model performance statistics"""
    stats = await service.get_model_stats(model_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return stats

@router.post("/{model_id}/warmup")
async def warmup_model(model_id: str, service: ModelService = Depends(get_model_service)):
    """Warm up a model with dummy requests"""
    success = await service.warmup_model(model_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Model not found or not ready")
    
    return {
        "model_id": model_id,
        "status": "warmed_up",
        "message": "Model warmed up successfully"
    }
