"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_item():
    """Sample item data for testing"""
    return {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 99.99,
        "is_available": True,
    }


@pytest.fixture
def sample_item_update():
    """Sample item update data for testing"""
    return {
        "name": "Updated Item",
        "price": 149.99,
        "is_available": False,
    }

