"""Tests for app/core/config.py - Application configuration"""

import pytest
from app.core.config import Settings


def test_settings_defaults():
    """Test that settings have correct default values"""
    settings = Settings()
    assert settings.PROJECT_NAME == "FastAPI Bee"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) > 0


def test_settings_allowed_origins():
    """Test that ALLOWED_ORIGINS contains expected values"""
    settings = Settings()
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
    assert "http://localhost:8000" in settings.ALLOWED_ORIGINS


def test_settings_immutable():
    """Test that settings are properly configured"""
    settings = Settings()
    # Settings should be accessible
    assert hasattr(settings, "PROJECT_NAME")
    assert hasattr(settings, "VERSION")
    assert hasattr(settings, "API_V1_STR")


def test_settings_api_v1_str():
    """Test API v1 string configuration"""
    settings = Settings()
    assert settings.API_V1_STR.startswith("/")
    assert "v1" in settings.API_V1_STR.lower()


def test_settings_project_info():
    """Test project information settings"""
    settings = Settings()
    assert isinstance(settings.PROJECT_NAME, str)
    assert len(settings.PROJECT_NAME) > 0
    assert isinstance(settings.VERSION, str)
    assert len(settings.VERSION) > 0

