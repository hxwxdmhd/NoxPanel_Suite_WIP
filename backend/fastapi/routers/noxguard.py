"""
NoxSuite FastAPI - NoxGuard Router
Security and guard functionality endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/security")
async def security_status():
    """Get security status"""
    return {"message": "Security status endpoint - implementation pending"}