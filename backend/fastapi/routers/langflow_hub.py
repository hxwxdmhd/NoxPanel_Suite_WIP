"""
NoxSuite FastAPI - Langflow Hub Router
AI workflow and Langflow integration endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/workflows")
async def get_workflows():
    """Get AI workflows"""
    return {"message": "AI workflows endpoint - implementation pending"}