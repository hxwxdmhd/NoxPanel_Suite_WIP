"""
AetherCore API Routes - Model Serving
====================================

Model serving routes for inference requests and predictions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import asyncio
import time
import uuid
import logging
from ..models.model_metadata import ModelMetadata, ModelType, ModelStatus
from ..services.inference_service import InferenceService

router = APIRouter(prefix="/api/serve", tags=["serving"])

# Request/Response Models
class InferenceRequest(BaseModel):
    model_id: str
    inputs: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
    batch_size: int = Field(default=1, ge=1, le=32)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    stream: bool = False

class InferenceResponse(BaseModel):
    request_id: str
    model_id: str
    outputs: Dict[str, Any]
    processing_time_ms: float
    status: str = "success"
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchInferenceRequest(BaseModel):
    model_id: str
    batch_inputs: List[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None
    timeout_seconds: int = Field(default=60, ge=1, le=600)

class BatchInferenceResponse(BaseModel):
    request_id: str
    model_id: str
    batch_outputs: List[Dict[str, Any]]
    processing_time_ms: float
    total_processed: int
    status: str = "success"
    errors: Optional[List[str]] = None

class StreamingResponse(BaseModel):
    request_id: str
    model_id: str
    chunk_id: int
    outputs: Dict[str, Any]
    is_final: bool = False
    processing_time_ms: float

# Get inference service instance
def get_inference_service():
    return InferenceService()

@router.post("/inference", response_model=InferenceResponse)
async def serve_inference(
    request: InferenceRequest,
    service: InferenceService = Depends(get_inference_service)
):
    """Serve a single inference request"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Validate model availability
        if not await service.is_model_ready(request.model_id):
            raise HTTPException(
                status_code=503,
                detail=f"Model {request.model_id} is not ready"
            )
        
        # Process inference
        outputs = await service.process_inference(
            model_id=request.model_id,
            inputs=request.inputs,
            parameters=request.parameters,
            timeout_seconds=request.timeout_seconds
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return InferenceResponse(
            request_id=request_id,
            model_id=request.model_id,
            outputs=outputs,
            processing_time_ms=processing_time,
            status="success",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "batch_size": request.batch_size
            }
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        return InferenceResponse(
            request_id=request_id,
            model_id=request.model_id,
            outputs={},
            processing_time_ms=processing_time,
            status="error",
            error=str(e)
        )

@router.post("/batch", response_model=BatchInferenceResponse)
async def serve_batch_inference(
    request: BatchInferenceRequest,
    service: InferenceService = Depends(get_inference_service)
):
    """Serve a batch of inference requests"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Validate model availability
        if not await service.is_model_ready(request.model_id):
            raise HTTPException(
                status_code=503,
                detail=f"Model {request.model_id} is not ready"
            )
        
        # Process batch inference
        batch_outputs = await service.process_batch_inference(
            model_id=request.model_id,
            batch_inputs=request.batch_inputs,
            parameters=request.parameters,
            timeout_seconds=request.timeout_seconds
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchInferenceResponse(
            request_id=request_id,
            model_id=request.model_id,
            batch_outputs=batch_outputs,
            processing_time_ms=processing_time,
            total_processed=len(batch_outputs),
            status="success"
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        return BatchInferenceResponse(
            request_id=request_id,
            model_id=request.model_id,
            batch_outputs=[],
            processing_time_ms=processing_time,
            total_processed=0,
            status="error",
            errors=[str(e)]
        )

@router.get("/models/{model_id}/predict")
async def quick_predict(
    model_id: str,
    text: str = Query(..., description="Input text for prediction"),
    service: InferenceService = Depends(get_inference_service)
):
    """Quick prediction endpoint for simple text input"""
    try:
        # Validate model availability
        if not await service.is_model_ready(model_id):
            raise HTTPException(
                status_code=503,
                detail=f"Model {model_id} is not ready"
            )
        
        # Process quick prediction
        result = await service.quick_predict(model_id, text)
        
        return {
            "model_id": model_id,
            "input": text,
            "prediction": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/stream/{model_id}")
async def stream_inference(
    websocket,
    model_id: str,
    service: InferenceService = Depends(get_inference_service)
):
    """WebSocket endpoint for streaming inference"""
    await websocket.accept()
    request_id = str(uuid.uuid4())
    
    try:
        # Validate model availability
        if not await service.is_model_ready(model_id):
            await websocket.send_json({
                "error": f"Model {model_id} is not ready"
            })
            await websocket.close()
            return
        
        while True:
            # Receive input data
            data = await websocket.receive_json()
            
            if "inputs" not in data:
                await websocket.send_json({
                    "error": "Missing 'inputs' in request"
                })
                continue
            
            # Process streaming inference
            async for chunk in service.stream_inference(
                model_id=model_id,
                inputs=data["inputs"],
                parameters=data.get("parameters"),
                request_id=request_id
            ):
                await websocket.send_json(chunk)
                
    except Exception as e:
        await websocket.send_json({
            "error": str(e)
        })
        await websocket.close()

@router.get("/health/{model_id}")
async def check_model_health(
    model_id: str,
    service: InferenceService = Depends(get_inference_service)
):
    """Check model health and readiness for inference"""
    health_info = await service.check_model_health(model_id)
    
    if not health_info:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return health_info

@router.get("/stats/{model_id}")
async def get_inference_stats(
    model_id: str,
    service: InferenceService = Depends(get_inference_service)
):
    """Get inference statistics for a model"""
    stats = await service.get_inference_stats(model_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return stats
