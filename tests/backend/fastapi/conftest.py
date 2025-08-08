"""
Test Configuration
Shared test configuration for FastAPI application tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch

# Create a test-specific app instance without TrustedHost middleware
def create_test_app():
    """Create FastAPI app configured for testing"""
    from fastapi import FastAPI
    from backend.fastapi.routers import health, auth
    
    test_app = FastAPI(title="NoxSuite API Test")
    
    # Add only essential routes for testing
    test_app.include_router(health.router, prefix="/api", tags=["Health"])
    test_app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    
    # Add a simple root endpoint
    @test_app.get("/")
    async def root():
        return {"name": "NoxSuite API", "version": "1.0.0", "status": "test"}
    
    return test_app

@pytest.fixture
def test_client():
    """Create test client for FastAPI application"""
    test_app = create_test_app()
    return TestClient(test_app)

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()