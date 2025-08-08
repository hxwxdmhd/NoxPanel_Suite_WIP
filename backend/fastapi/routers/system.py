"""
NoxSuite FastAPI - System Router
System management and monitoring endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def system_status():
    """Get system status"""
    return {"message": "System status endpoint - implementation pending"}

@router.get("/info")
async def system_info():
    """Get system information"""
    return {"message": "System info endpoint - implementation pending"}