"""
NoxSuite FastAPI - Heimnetz Scanner Router
Network scanning and discovery endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/scan")
async def network_scan():
    """Network scan"""
    return {"message": "Network scan endpoint - implementation pending"}