"""
Tests for logging configuration and functionality

This module tests the structured logging setup, configuration,
and context management functionality.
"""

import io
import logging
import sys
from unittest.mock import patch

import pytest
import structlog

from app.core.logging import (
    add_log_level,
    add_timestamp,
    bind_request_context,
    clear_request_context,
    configure_logging,
    get_logger,
)


class TestLoggingProcessors:
    """Test logging processors"""
    
    def test_add_log_level(self):
        """Test that log level is added to event dict"""
        event_dict = {"message": "test"}
        result = add_log_level(None, "info", event_dict)
        
        assert result["level"] == "INFO"
        assert result["message"] == "test"
    
    def test_add_timestamp(self):
        """Test that timestamp is added to event dict"""
        event_dict = {"message": "test"}
        result = add_timestamp(None, "info", event_dict)
        
        assert "timestamp" in result
        assert result["timestamp"].endswith("Z")
        assert result["message"] == "test"


class TestLoggingConfiguration:
    """Test logging configuration"""
    
    @patch('app.core.logging.settings')
    def test_configure_logging_development(self, mock_settings):
        """Test logging configuration for development environment"""
        mock_settings.ENVIRONMENT = "development"
        mock_settings.LOG_LEVEL = "DEBUG"
        
        with patch('structlog.configure') as mock_configure:
            configure_logging()
            
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args[1]
            
            # Check that development uses ConsoleRenderer
            processors = call_args['processors']
            assert any('ConsoleRenderer' in str(p) for p in processors)
    
    @patch('app.core.logging.settings')
    def test_configure_logging_production(self, mock_settings):
        """Test logging configuration for production environment"""
        mock_settings.ENVIRONMENT = "production"
        mock_settings.LOG_LEVEL = "INFO"
        
        with patch('structlog.configure') as mock_configure:
            configure_logging()
            
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args[1]
            
            # Check that production uses JSONRenderer
            processors = call_args['processors']
            assert any('JSONRenderer' in str(p) for p in processors)
    
    def test_get_logger(self):
        """Test logger creation"""
        logger = get_logger("test_module")
        
        assert isinstance(logger, structlog.BoundLogger)


class TestRequestContext:
    """Test request context management"""
    
    def setUp(self):
        """Clear context before each test"""
        clear_request_context()
    
    def tearDown(self):
        """Clear context after each test"""
        clear_request_context()
    
    def test_bind_request_context(self):
        """Test binding request context"""
        request_id = "req_123"
        method = "GET"
        path = "/api/v1/items"
        
        bind_request_context(request_id, method, path)
        
        # Get context variables (this is internal structlog API)
        context_vars = structlog.contextvars._CONTEXT_VARS.get({})
        
        assert context_vars.get("request_id") == request_id
        assert context_vars.get("method") == method
        assert context_vars.get("path") == path
    
    def test_clear_request_context(self):
        """Test clearing request context"""
        # First bind some context
        bind_request_context("req_123", "GET", "/test")
        
        # Then clear it
        clear_request_context()
        
        # Context should be empty
        context_vars = structlog.contextvars._CONTEXT_VARS.get({})
        assert len(context_vars) == 0
    
    def test_context_isolation(self):
        """Test that context doesn't leak between operations"""
        # Bind context
        bind_request_context("req_123", "GET", "/test1")
        
        # Clear and bind new context
        clear_request_context()
        bind_request_context("req_456", "POST", "/test2")
        
        # Should only have new context
        context_vars = structlog.contextvars._CONTEXT_VARS.get({})
        assert context_vars.get("request_id") == "req_456"
        assert context_vars.get("method") == "POST"
        assert context_vars.get("path") == "/test2"


class TestLoggingIntegration:
    """Integration tests for logging"""
    
    def test_logger_with_context(self):
        """Test that logger includes bound context"""
        # Configure logging to capture output
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            configure_logging()
            logger = get_logger("test")
            
            # Bind context and log
            bind_request_context("req_789", "PUT", "/api/test")
            logger.info("Test message", extra_field="extra_value")
            
            # Check output contains context
            log_output = output.getvalue()
            assert "req_789" in log_output
            assert "PUT" in log_output
            assert "/api/test" in log_output
            assert "Test message" in log_output
            assert "extra_value" in log_output
        
        # Clean up
        clear_request_context()
    
    @patch('app.core.logging.settings')
    def test_log_level_filtering(self, mock_settings):
        """Test that log level filtering works"""
        mock_settings.ENVIRONMENT = "development"
        mock_settings.LOG_LEVEL = "WARNING"
        
        output = io.StringIO()
        
        with patch('sys.stdout', output):
            configure_logging()
            logger = get_logger("test")
            
            # These should not appear (below WARNING level)
            logger.debug("Debug message")
            logger.info("Info message")
            
            # This should appear
            logger.warning("Warning message")
            
            log_output = output.getvalue()
            assert "Debug message" not in log_output
            assert "Info message" not in log_output
            assert "Warning message" in log_output