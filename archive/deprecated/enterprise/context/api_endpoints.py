"""
ContextForge API Endpoints
FastAPI implementation for HTTP access to ContextForge services
Part of the Heimnetz Enterprise Suite
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
from .index import ContextForge
from .service_integration import service_integration
import json

# Initialize FastAPI app
app = FastAPI(
    title="ContextForge API",
    description="Model Context Protocol Server API",
    version="1.0.0"
)

# Initialize ContextForge instance
contextforge = ContextForge()

# Request/Response Models
class ContextRequest(BaseModel):
    prompt: str
    model_preference: Optional[str] = None
    complexity_threshold: Optional[float] = None
    context_sources: Optional[List[str]] = None
    max_context_length: Optional[int] = None

class ContextResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class ModelCompatibilityRequest(BaseModel):
    agent_call: str
    available_models: List[str]

class RouterRequest(BaseModel):
    request_type: str
    load_factor: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None

# API Endpoints
@app.post("/context/analyze", response_model=ContextResponse)
async def analyze_context(request: ContextRequest):
    """
    Analyze context and provide model recommendations
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Process context request
        result = await contextforge.process_context_request(request.dict())
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        return ContextResponse(
            success=True,
            data=result,
            processing_time=processing_time
        )
        
    except Exception as e:
        return ContextResponse(
            success=False,
            error=str(e)
        )

@app.post("/context/compatibility", response_model=ContextResponse)
async def check_model_compatibility(request: ModelCompatibilityRequest):
    """
    Check model compatibility for specific agent call
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Check compatibility
        result = await contextforge.check_model_compatibility(
            request.agent_call,
            request.available_models
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        return ContextResponse(
            success=True,
            data=result,
            processing_time=processing_time
        )
        
    except Exception as e:
        return ContextResponse(
            success=False,
            error=str(e)
        )

@app.post("/context/route", response_model=ContextResponse)
async def route_request(request: RouterRequest):
    """
    Route request through dynamic dispatch engine
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Route request
        result = await contextforge.router.route_request(
            request.request_type,
            request.load_factor,
            request.preferences
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        return ContextResponse(
            success=True,
            data=result,
            processing_time=processing_time
        )
        
    except Exception as e:
        return ContextResponse(
            success=False,
            error=str(e)
        )

@app.get("/context/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Get service health
        health_info = await service_integration.get_service_info()
        
        # Check ContextForge health
        contextforge_health = await contextforge.health_check()
        
        return {
            "status": "healthy",
            "contextforge": contextforge_health,
            "service_integration": health_info,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/context/metrics")
async def get_metrics():
    """
    Get performance metrics
    """
    try:
        metrics = await contextforge.get_metrics()
        return {
            "metrics": metrics,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/context/models")
async def list_available_models():
    """
    List available models and their capabilities
    """
    try:
        models = await contextforge.list_available_models()
        return {
            "models": models,
            "total_count": len(models)
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/context/protocols")
async def list_protocols():
    """
    List supported protocol versions
    """
    try:
        protocols = await contextforge.list_supported_protocols()
        return {
            "protocols": protocols,
            "active_version": contextforge.protocol_version
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/context/test")
async def run_test(test_name: str = Query(...)):
    """
    Run specific test
    """
    try:
        result = await service_integration.run_test(test_name)
        return {
            "test_name": test_name,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/context/config")
async def get_configuration():
    """
    Get current configuration
    """
    try:
        config = await contextforge.get_configuration()
        return {
            "configuration": config,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/context/config")
async def update_configuration(config: Dict[str, Any] = Body(...)):
    """
    Update configuration
    """
    try:
        result = await contextforge.update_configuration(config)
        return {
            "success": True,
            "updated_config": result,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# WebSocket endpoints for real-time updates
@app.websocket("/context/ws")
async def websocket_endpoint(websocket):
    """
    WebSocket endpoint for real-time updates
    """
    await websocket.accept()
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Process request
            if request_data.get("type") == "context_request":
                result = await contextforge.process_context_request(
                    request_data.get("payload", {})
                )
                await websocket.send_text(json.dumps({
                    "type": "context_response",
                    "result": result
                }))
                
            elif request_data.get("type") == "health_check":
                health = await contextforge.health_check()
                await websocket.send_text(json.dumps({
                    "type": "health_response",
                    "health": health
                }))
                
            elif request_data.get("type") == "metrics":
                metrics = await contextforge.get_metrics()
                await websocket.send_text(json.dumps({
                    "type": "metrics_response",
                    "metrics": metrics
                }))
                
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e)
        }))
        await websocket.close()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Initialize ContextForge on startup
    """
    await contextforge.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown
    """
    await contextforge.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
