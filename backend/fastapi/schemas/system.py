"""
NoxSuite FastAPI - System Schemas
System status and health check data models
"""
from pydantic import BaseModel
from typing import Dict, Any

class SystemStatus(BaseModel):
    """System status response model"""
    status: str
    uptime: int
    memory_usage: float
    cpu_usage: float

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    components: Dict[str, Any]