"""
NoxSuite FastAPI - Metrics Middleware
Application metrics and monitoring middleware
"""
from fastapi import Request

async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware"""
    response = await call_next(request)
    return response