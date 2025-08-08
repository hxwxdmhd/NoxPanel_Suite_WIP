"""
NoxSuite FastAPI - AI Models Router
AI model management and inference endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/models")
async def list_models():
    """List AI models"""
    return {"message": "AI models endpoint - implementation pending"}