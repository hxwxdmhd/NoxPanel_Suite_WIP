# NoxPanel Test Suite
"""
Comprehensive testing framework for NoxPanel system.

This test suite implements the multi-layered testing strategy defined in
docs/test-plan.md, with special focus on ADHD-friendly workflows and
enterprise-grade reliability.

Test Layers:
1. Unit/Component Tests (React Testing Library + Jest)
2. Accessibility Tests (axe-core + Cypress)
3. Backend API Tests (Pytest + FastAPI TestClient)
4. End-to-End Tests (Playwright + Cypress)
5. Performance Tests (Locust)

For contributing guidelines, see docs/contributing.md
For troubleshooting, see docs/troubleshooting.md
"""

__version__ = "1.0.0"
__author__ = "NoxPanel Development Team"
