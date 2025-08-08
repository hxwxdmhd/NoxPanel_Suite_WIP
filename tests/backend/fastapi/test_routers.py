"""
Tests for FastAPI Routers
Tests individual router functionality
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthRouter:
    """Test authentication router"""
    
    def test_login_endpoint_exists(self, test_client):
        """Test login endpoint is accessible"""
        response = test_client.post("/api/auth/login")
        # Should return 422 for missing data or 401 for invalid credentials
        assert response.status_code in [400, 401, 422]
    
    def test_logout_endpoint_exists(self, test_client):
        """Test logout endpoint is accessible"""
        response = test_client.post("/api/auth/logout")
        assert response.status_code in [200, 401, 405]
    
    def test_verify_endpoint_exists(self, test_client):
        """Test token verification endpoint is accessible"""
        response = test_client.get("/api/auth/verify")
        assert response.status_code in [200, 401]

class TestSystemRouter:
    """Test system management router"""
    
    def test_system_status_requires_auth(self, test_client):
        """Test system status endpoint requires authentication"""
        response = test_client.get("/api/system/status")
        assert response.status_code in [401, 403]
    
    def test_system_info_requires_auth(self, test_client):
        """Test system info endpoint requires authentication"""
        response = test_client.get("/api/system/info")
        assert response.status_code in [401, 403]

class TestNoxPanelRouter:
    """Test NoxPanel dashboard router"""
    
    def test_dashboard_requires_auth(self, test_client):
        """Test dashboard endpoint requires authentication"""
        response = test_client.get("/api/noxpanel/dashboard")
        assert response.status_code in [401, 403]

class TestNoxGuardRouter:
    """Test NoxGuard security router"""
    
    def test_security_status_requires_auth(self, test_client):
        """Test security status endpoint requires authentication"""
        response = test_client.get("/api/noxguard/security")
        assert response.status_code in [401, 403]

class TestAutoImportRouter:
    """Test AutoImport discovery router"""
    
    def test_auto_scan_requires_auth(self, test_client):
        """Test auto scan endpoint requires authentication"""
        response = test_client.get("/api/autoimport/scan")
        assert response.status_code in [401, 403]

class TestPowerLogRouter:
    """Test PowerLog monitoring router"""
    
    def test_logs_requires_auth(self, test_client):
        """Test logs endpoint requires authentication"""
        response = test_client.get("/api/powerlog/logs")
        assert response.status_code in [401, 403]

class TestLangflowHubRouter:
    """Test Langflow AI Hub router"""
    
    def test_workflows_requires_auth(self, test_client):
        """Test workflows endpoint requires authentication"""
        response = test_client.get("/api/langflow/workflows")
        assert response.status_code in [401, 403]

class TestAutoCleanerRouter:
    """Test AutoCleaner optimization router"""
    
    def test_clean_requires_auth(self, test_client):
        """Test clean endpoint requires authentication"""
        response = test_client.post("/api/autocleaner/clean")
        assert response.status_code in [401, 403]

class TestHeimnetzScannerRouter:
    """Test Heimnetz Scanner router"""
    
    def test_scan_requires_auth(self, test_client):
        """Test scan endpoint requires authentication"""
        response = test_client.post("/api/scanner/scan")
        assert response.status_code in [401, 403]

class TestAIModelsRouter:
    """Test AI Models router"""
    
    def test_models_requires_auth(self, test_client):
        """Test models endpoint requires authentication"""
        response = test_client.get("/api/ai/models")
        assert response.status_code in [401, 403]