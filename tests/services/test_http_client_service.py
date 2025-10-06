"""Tests for app/services/http_client_service.py - HTTP client service"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.http_client_service import (
    HTTPClientService,
    HTTPClientError,
    get_http_client_service
)


@pytest.fixture
def http_service():
    """Create a fresh HTTPClientService instance for each test"""
    return HTTPClientService()


@pytest.fixture
def mock_response():
    """Create a mock httpx.Response"""
    def _create_response(
        status_code: int = 200,
        json_data: dict = None,
        text_data: str = None,
        headers: dict = None
    ):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = headers or {}
        response.content = b"test content"
        
        if json_data is not None:
            response.json.return_value = json_data
        else:
            response.json.side_effect = ValueError("Not JSON")
        
        response.text = text_data or "test response"
        
        return response
    
    return _create_response


class TestHTTPClientServiceInitialization:
    """Test suite for service initialization and lifecycle"""
    
    def test_service_initialization(self, http_service):
        """Test that service initializes correctly"""
        assert http_service._client is None
        assert http_service.logger is not None
    
    def test_singleton_pattern(self):
        """Test that get_http_client_service returns singleton instance"""
        service1 = get_http_client_service()
        service2 = get_http_client_service()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_close_client(self, http_service):
        """Test closing the HTTP client"""
        # Create client first
        http_service._get_client()
        assert http_service._client is not None
        
        # Close it
        await http_service.close()
        assert http_service._client is None
    
    @pytest.mark.asyncio
    async def test_close_client_when_not_initialized(self, http_service):
        """Test closing client when it was never initialized"""
        assert http_service._client is None
        await http_service.close()  # Should not raise error
        assert http_service._client is None


class TestHTTPClientServiceGET:
    """Test suite for GET requests"""
    
    @pytest.mark.asyncio
    async def test_get_request_success_json(self, http_service, mock_response):
        """Test successful GET request with JSON response"""
        json_data = {"key": "value", "number": 42}
        response = mock_response(status_code=200, json_data=json_data)
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            result = await http_service.get("https://api.example.com/data")
            
            assert result["status_code"] == 200
            assert result["body"] == json_data
            assert "headers" in result
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_request_success_text(self, http_service, mock_response):
        """Test successful GET request with text response"""
        text_data = "Plain text response"
        response = mock_response(status_code=200, text_data=text_data)
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            result = await http_service.get("https://api.example.com/data")
            
            assert result["status_code"] == 200
            assert result["body"] == text_data
    
    @pytest.mark.asyncio
    async def test_get_request_with_headers(self, http_service, mock_response):
        """Test GET request with custom headers"""
        response = mock_response(status_code=200, json_data={"success": True})
        headers = {"Authorization": "Bearer token123", "Custom-Header": "value"}
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            await http_service.get("https://api.example.com/data", headers=headers)
            
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["headers"] == headers
    
    @pytest.mark.asyncio
    async def test_get_request_with_params(self, http_service, mock_response):
        """Test GET request with query parameters"""
        response = mock_response(status_code=200, json_data={"success": True})
        params = {"page": 1, "limit": 10}
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            await http_service.get("https://api.example.com/data", params=params)
            
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"] == params
    
    @pytest.mark.asyncio
    async def test_get_request_timeout(self, http_service):
        """Test GET request timeout handling"""
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.get("https://api.example.com/data", timeout=5.0)
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_request_network_error(self, http_service):
        """Test GET request network error handling"""
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Connection failed")
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.get("https://api.example.com/data")
            
            assert "network error" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_request_http_error_4xx(self, http_service, mock_response):
        """Test GET request with 4xx error response"""
        response = mock_response(status_code=404, json_data={"error": "Not found"})
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.get("https://api.example.com/data")
            
            assert exc_info.value.status_code == 404
            assert "404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_request_http_error_5xx(self, http_service, mock_response):
        """Test GET request with 5xx error response"""
        response = mock_response(status_code=500, json_data={"error": "Server error"})
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.get("https://api.example.com/data")
            
            assert exc_info.value.status_code == 500
            assert "500" in str(exc_info.value)


class TestHTTPClientServicePOST:
    """Test suite for POST requests"""
    
    @pytest.mark.asyncio
    async def test_post_request_success_json(self, http_service, mock_response):
        """Test successful POST request with JSON data"""
        json_data = {"result": "created", "id": 123}
        response = mock_response(status_code=201, json_data=json_data)
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = response
            
            result = await http_service.post(
                "https://api.example.com/data",
                json={"name": "test"}
            )
            
            assert result["status_code"] == 201
            assert result["body"] == json_data
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_request_with_form_data(self, http_service, mock_response):
        """Test POST request with form data"""
        response = mock_response(status_code=200, json_data={"success": True})
        form_data = {"username": "test", "password": "secret"}
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = response
            
            await http_service.post("https://api.example.com/login", data=form_data)
            
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["data"] == form_data
    
    @pytest.mark.asyncio
    async def test_post_request_with_headers(self, http_service, mock_response):
        """Test POST request with custom headers"""
        response = mock_response(status_code=200, json_data={"success": True})
        headers = {"Content-Type": "application/json", "X-API-Key": "key123"}
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = response
            
            await http_service.post(
                "https://api.example.com/data",
                json={"test": "data"},
                headers=headers
            )
            
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"] == headers
    
    @pytest.mark.asyncio
    async def test_post_request_timeout(self, http_service):
        """Test POST request timeout handling"""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.post("https://api.example.com/data", json={"test": "data"})
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_post_request_error_response(self, http_service, mock_response):
        """Test POST request with error response"""
        response = mock_response(status_code=400, json_data={"error": "Bad request"})
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = response
            
            with pytest.raises(HTTPClientError) as exc_info:
                await http_service.post("https://api.example.com/data", json={"test": "data"})
            
            assert exc_info.value.status_code == 400


class TestHTTPClientServicePUT:
    """Test suite for PUT requests"""
    
    @pytest.mark.asyncio
    async def test_put_request_success(self, http_service, mock_response):
        """Test successful PUT request"""
        json_data = {"result": "updated"}
        response = mock_response(status_code=200, json_data=json_data)
        
        with patch.object(httpx.AsyncClient, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = response
            
            result = await http_service.put(
                "https://api.example.com/data/123",
                json={"name": "updated"}
            )
            
            assert result["status_code"] == 200
            assert result["body"] == json_data
            mock_put.assert_called_once()


class TestHTTPClientServiceDELETE:
    """Test suite for DELETE requests"""
    
    @pytest.mark.asyncio
    async def test_delete_request_success(self, http_service, mock_response):
        """Test successful DELETE request"""
        response = mock_response(status_code=204, text_data="")
        
        with patch.object(httpx.AsyncClient, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = response
            
            result = await http_service.delete("https://api.example.com/data/123")
            
            assert result["status_code"] == 204
            mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_request_with_headers(self, http_service, mock_response):
        """Test DELETE request with custom headers"""
        response = mock_response(status_code=200, json_data={"success": True})
        headers = {"Authorization": "Bearer token123"}
        
        with patch.object(httpx.AsyncClient, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = response
            
            await http_service.delete("https://api.example.com/data/123", headers=headers)
            
            mock_delete.assert_called_once()
            call_kwargs = mock_delete.call_args.kwargs
            assert call_kwargs["headers"] == headers

