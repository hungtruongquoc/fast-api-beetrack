"""
Tests for logging middleware

This module tests the LoggingMiddleware functionality including
request context injection, timing, and error handling.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.middleware.logging import LoggingMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app with logging middleware"""
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=500, detail="Test error")
    
    @app.get("/exception")
    async def exception_endpoint():
        raise ValueError("Test exception")
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestLoggingMiddleware:
    """Test logging middleware functionality"""
    
    @patch('app.middleware.logging.get_logger')
    def test_successful_request_logging(self, mock_get_logger, client):
        """Test that successful requests are logged properly"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that request start was logged
        start_calls = [call for call in mock_logger.info.call_args_list 
                      if "Request started" in str(call)]
        assert len(start_calls) == 1
        
        # Check that request completion was logged
        complete_calls = [call for call in mock_logger.info.call_args_list 
                         if "Request completed" in str(call)]
        assert len(complete_calls) == 1
        
        # Check completion log contains status code and timing
        complete_call = complete_calls[0]
        assert "status_code" in str(complete_call)
        assert "process_time_ms" in str(complete_call)
    
    @patch('app.middleware.logging.get_logger')
    def test_request_id_header(self, mock_get_logger, client):
        """Test that response includes request ID header"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = client.get("/test")
        
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("req_")
    
    @patch('app.middleware.logging.get_logger')
    @patch('app.middleware.logging.bind_request_context')
    @patch('app.middleware.logging.clear_request_context')
    def test_context_management(self, mock_clear, mock_bind, mock_get_logger, client):
        """Test that request context is properly managed"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that context was bound
        mock_bind.assert_called_once()
        bind_args = mock_bind.call_args[0]
        assert bind_args[1] == "GET"  # method
        assert bind_args[2] == "/test"  # path
        assert bind_args[0].startswith("req_")  # request_id
        
        # Check that context was cleared
        mock_clear.assert_called_once()
    
    @patch('app.middleware.logging.get_logger')
    def test_error_response_logging(self, mock_get_logger, client):
        """Test that error responses are logged properly"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Should still log completion with error status
        complete_calls = [call for call in mock_logger.info.call_args_list 
                         if "Request completed" in str(call)]
        assert len(complete_calls) == 1
    
    @patch('app.middleware.logging.get_logger')
    def test_exception_logging(self, mock_get_logger, client):
        """Test that exceptions are logged properly"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # This should raise an internal server error
        with pytest.raises(Exception):
            client.get("/exception")
        
        # Check that exception was logged
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if "Request failed with exception" in str(call)]
        assert len(error_calls) == 1
        
        # Check error log contains exception details
        error_call = error_calls[0]
        assert "exception_type" in str(error_call)
        assert "exception_message" in str(error_call)
        assert "process_time_ms" in str(error_call)
    
    def test_get_client_ip_forwarded(self):
        """Test client IP extraction with X-Forwarded-For header"""
        middleware = LoggingMiddleware(None)
        
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "x-forwarded-for": "192.168.1.1, 10.0.0.1",
            "x-real-ip": None
        }.get(key)
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_real_ip(self):
        """Test client IP extraction with X-Real-IP header"""
        middleware = LoggingMiddleware(None)
        
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "x-forwarded-for": None,
            "x-real-ip": "192.168.1.2"
        }.get(key)
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.2"
    
    def test_get_client_ip_direct(self):
        """Test client IP extraction from direct connection"""
        middleware = LoggingMiddleware(None)
        
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.3"
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.3"
    
    def test_get_client_ip_unknown(self):
        """Test client IP extraction when no IP available"""
        middleware = LoggingMiddleware(None)
        
        request = MagicMock()
        request.headers.get.return_value = None
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "unknown"
    
    @patch('app.middleware.logging.get_logger')
    def test_request_timing(self, mock_get_logger, client):
        """Test that request timing is captured"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Add a small delay to ensure measurable processing time
        with patch('time.time', side_effect=[1000.0, 1000.1]):  # 100ms processing time
            response = client.get("/test")
        
        assert response.status_code == 200
        
        # Find the completion log call
        complete_calls = [call for call in mock_logger.info.call_args_list 
                         if "Request completed" in str(call)]
        assert len(complete_calls) == 1
        
        # The call should include timing information
        call_str = str(complete_calls[0])
        assert "process_time_ms" in call_str