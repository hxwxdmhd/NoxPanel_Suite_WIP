"""
NoxSuite FastAPI - NoxPanel Router
Dashboard and panel management endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
async def dashboard():
    """Get dashboard data"""
    return {"message": "Dashboard endpoint - implementation pending"}