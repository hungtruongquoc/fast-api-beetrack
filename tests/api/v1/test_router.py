"""Tests for app/api/v1/router.py - API v1 router configuration"""

import pytest
from fastapi.testclient import TestClient


def test_api_router_includes_items(client: TestClient):
    """Test that API router includes items endpoints"""
    response = client.get("/api/v1/items/")
    assert response.status_code == 200


def test_api_v1_prefix(client: TestClient):
    """Test that all v1 endpoints are under /api/v1 prefix"""
    # Items endpoint should be under /api/v1
    response = client.get("/api/v1/items/")
    assert response.status_code == 200
    
    # Without prefix should not work
    response = client.get("/items/")
    assert response.status_code == 404


def test_items_endpoint_has_tag(client: TestClient):
    """Test that items endpoints have proper tags in OpenAPI"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    openapi_schema = response.json()
    
    # Check that items endpoints have the "items" tag
    items_path = openapi_schema["paths"].get("/api/v1/items/")
    assert items_path is not None
    
    # Check GET method has items tag
    if "get" in items_path:
        assert "items" in items_path["get"].get("tags", [])

