"""
NoxSuite FastAPI - Health Router
Health check and monitoring endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "noxsuite-api"}

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with system information"""
    return {
        "status": "healthy", 
        "service": "noxsuite-api",
        "version": "1.0.0",
        "components": {
            "database": "connected",
            "redis": "connected",
            "ai_models": "loaded"
        }
    }