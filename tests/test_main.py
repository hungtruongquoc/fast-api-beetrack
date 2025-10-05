"""Tests for app/main.py - Main application endpoints"""

import pytest
from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to FastAPI Bee"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_health_check(client: TestClient):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_openapi_schema(client: TestClient):
    """Test that OpenAPI schema is accessible"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "FastAPI Bee"
    assert data["info"]["version"] == "0.1.0"


def test_docs_redirect(client: TestClient):
    """Test that docs endpoint is accessible"""
    response = client.get("/docs", follow_redirects=False)
    assert response.status_code in [200, 307]  # 200 OK or 307 Temporary Redirect


def test_cors_middleware_configured(client: TestClient):
    """Test that CORS middleware is properly configured"""
    response = client.options("/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    # The middleware should handle CORS
    assert response.status_code in [200, 204]

