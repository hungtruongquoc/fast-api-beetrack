"""
HTTP Client Service for external API calls

This module provides a singleton HTTPClientService that wraps httpx.AsyncClient
for making REST API calls. It provides a consistent interface for all external
HTTP requests with proper error handling, logging, and resource management.

The service is designed to be reused across the application for any external
API communication needs, including OAuth token requests and other third-party
API integrations.

Architecture:
    Services → HTTPClientService → External APIs

Classes:
    HTTPClientService: Singleton service for HTTP operations
    HTTPClientError: Custom exception for HTTP errors

Functions:
    get_http_client_service: Factory function returning singleton instance
"""

from typing import Any, Dict, Optional
import httpx
from app.core.logging import get_logger
from app.core.config import settings


class HTTPClientError(Exception):
    """
    Custom exception for HTTP client errors
    
    Attributes:
        message: Error message
        status_code: HTTP status code (if available)
        response_body: Response body (if available)
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class HTTPClientService:
    """
    Singleton service for making HTTP requests to external APIs
    
    This service wraps httpx.AsyncClient to provide a consistent interface
    for all external HTTP operations. It includes proper error handling,
    structured logging, and resource management.
    
    The service supports common HTTP methods (GET, POST, PUT, DELETE) and
    handles timeouts, network errors, and HTTP error responses gracefully.
    
    Attributes:
        _client (Optional[httpx.AsyncClient]): The underlying httpx client
        logger: Structured logger instance
    
    Methods:
        HTTP Operations:
            - get: Make GET request
            - post: Make POST request
            - put: Make PUT request
            - delete: Make DELETE request
        
        Lifecycle:
            - close: Close the HTTP client and cleanup resources
    """
    
    def __init__(self):
        """
        Initialize the HTTP client service
        
        Creates a logger instance. The actual httpx.AsyncClient is created
        lazily on first use to ensure proper async context.
        """
        self._client: Optional[httpx.AsyncClient] = None
        self.logger = get_logger(__name__)
    
    def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create the httpx AsyncClient instance

        Lazily creates the client on first use to ensure it's created
        in the proper async context. Uses timeout from settings.

        Returns:
            httpx.AsyncClient: The HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=settings.HTTP_CLIENT_TIMEOUT,
                follow_redirects=True,
            )
            self.logger.debug(
                "HTTP client initialized",
                default_timeout=settings.HTTP_CLIENT_TIMEOUT
            )
        return self._client
    
    async def close(self) -> None:
        """
        Close the HTTP client and cleanup resources
        
        Should be called on application shutdown to properly close
        all connections and cleanup resources.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self.logger.debug("HTTP client closed")
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            params: Optional query parameters
            timeout: Request timeout in seconds (default: from settings.HTTP_CLIENT_TIMEOUT)
        
        Returns:
            Dict containing:
                - status_code: HTTP status code
                - body: Response body (parsed JSON or text)
                - headers: Response headers
        
        Raises:
            HTTPClientError: If request fails or returns error status
        """
        # Use settings default if timeout not specified
        if timeout is None:
            timeout = settings.HTTP_CLIENT_TIMEOUT

        self.logger.debug(
            "Making GET request",
            url=url,
            has_headers=headers is not None,
            has_params=params is not None,
            timeout=timeout
        )

        try:
            client = self._get_client()
            response = await client.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout
            )
            
            return await self._process_response(response, "GET", url)
            
        except httpx.TimeoutException as e:
            self.logger.error("GET request timeout", url=url, timeout=timeout)
            raise HTTPClientError(f"Request timeout after {timeout}s: {url}") from e
        except httpx.NetworkError as e:
            self.logger.error("GET request network error", url=url, error=str(e))
            raise HTTPClientError(f"Network error: {str(e)}") from e
        except httpx.HTTPError as e:
            self.logger.error("GET request HTTP error", url=url, error=str(e))
            raise HTTPClientError(f"HTTP error: {str(e)}") from e
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request

        Args:
            url: The URL to request
            data: Optional form data (application/x-www-form-urlencoded)
            json: Optional JSON data (application/json)
            headers: Optional HTTP headers
            timeout: Request timeout in seconds (default: from settings.HTTP_CLIENT_TIMEOUT)
        
        Returns:
            Dict containing:
                - status_code: HTTP status code
                - body: Response body (parsed JSON or text)
                - headers: Response headers
        
        Raises:
            HTTPClientError: If request fails or returns error status
        """
        # Use settings default if timeout not specified
        if timeout is None:
            timeout = settings.HTTP_CLIENT_TIMEOUT

        self.logger.debug(
            "Making POST request",
            url=url,
            has_data=data is not None,
            has_json=json is not None,
            has_headers=headers is not None,
            timeout=timeout
        )

        try:
            client = self._get_client()
            response = await client.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout
            )
            
            return await self._process_response(response, "POST", url)
            
        except httpx.TimeoutException as e:
            self.logger.error("POST request timeout", url=url, timeout=timeout)
            raise HTTPClientError(f"Request timeout after {timeout}s: {url}") from e
        except httpx.NetworkError as e:
            self.logger.error("POST request network error", url=url, error=str(e))
            raise HTTPClientError(f"Network error: {str(e)}") from e
        except httpx.HTTPError as e:
            self.logger.error("POST request HTTP error", url=url, error=str(e))
            raise HTTPClientError(f"HTTP error: {str(e)}") from e
    
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request

        Args:
            url: The URL to request
            data: Optional form data (application/x-www-form-urlencoded)
            json: Optional JSON data (application/json)
            headers: Optional HTTP headers
            timeout: Request timeout in seconds (default: from settings.HTTP_CLIENT_TIMEOUT)
        
        Returns:
            Dict containing:
                - status_code: HTTP status code
                - body: Response body (parsed JSON or text)
                - headers: Response headers
        
        Raises:
            HTTPClientError: If request fails or returns error status
        """
        # Use settings default if timeout not specified
        if timeout is None:
            timeout = settings.HTTP_CLIENT_TIMEOUT

        self.logger.debug(
            "Making PUT request",
            url=url,
            has_data=data is not None,
            has_json=json is not None,
            has_headers=headers is not None,
            timeout=timeout
        )

        try:
            client = self._get_client()
            response = await client.put(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout
            )
            
            return await self._process_response(response, "PUT", url)
            
        except httpx.TimeoutException as e:
            self.logger.error("PUT request timeout", url=url, timeout=timeout)
            raise HTTPClientError(f"Request timeout after {timeout}s: {url}") from e
        except httpx.NetworkError as e:
            self.logger.error("PUT request network error", url=url, error=str(e))
            raise HTTPClientError(f"Network error: {str(e)}") from e
        except httpx.HTTPError as e:
            self.logger.error("PUT request HTTP error", url=url, error=str(e))
            raise HTTPClientError(f"HTTP error: {str(e)}") from e
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            timeout: Request timeout in seconds (default: from settings.HTTP_CLIENT_TIMEOUT)
        
        Returns:
            Dict containing:
                - status_code: HTTP status code
                - body: Response body (parsed JSON or text)
                - headers: Response headers
        
        Raises:
            HTTPClientError: If request fails or returns error status
        """
        # Use settings default if timeout not specified
        if timeout is None:
            timeout = settings.HTTP_CLIENT_TIMEOUT

        self.logger.debug(
            "Making DELETE request",
            url=url,
            has_headers=headers is not None,
            timeout=timeout
        )

        try:
            client = self._get_client()
            response = await client.delete(
                url,
                headers=headers,
                timeout=timeout
            )
            
            return await self._process_response(response, "DELETE", url)
            
        except httpx.TimeoutException as e:
            self.logger.error("DELETE request timeout", url=url, timeout=timeout)
            raise HTTPClientError(f"Request timeout after {timeout}s: {url}") from e
        except httpx.NetworkError as e:
            self.logger.error("DELETE request network error", url=url, error=str(e))
            raise HTTPClientError(f"Network error: {str(e)}") from e
        except httpx.HTTPError as e:
            self.logger.error("DELETE request HTTP error", url=url, error=str(e))
            raise HTTPClientError(f"HTTP error: {str(e)}") from e
    
    async def _process_response(
        self,
        response: httpx.Response,
        method: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Process HTTP response and handle errors
        
        Args:
            response: The httpx Response object
            method: HTTP method used
            url: URL that was requested
        
        Returns:
            Dict containing status_code, body, and headers
        
        Raises:
            HTTPClientError: If response has error status code
        """
        status_code = response.status_code
        
        # Try to parse response body as JSON, fall back to text
        try:
            body = response.json()
        except Exception:
            body = response.text
        
        # Log response
        self.logger.debug(
            f"{method} request completed",
            url=url,
            status_code=status_code,
            response_size=len(response.content)
        )
        
        # Check for HTTP errors
        if status_code >= 400:
            self.logger.warning(
                f"{method} request returned error status",
                url=url,
                status_code=status_code,
                response_body=body if isinstance(body, str) else str(body)[:200]
            )
            raise HTTPClientError(
                f"HTTP {status_code} error for {method} {url}",
                status_code=status_code,
                response_body=body if isinstance(body, str) else str(body)
            )
        
        return {
            "status_code": status_code,
            "body": body,
            "headers": dict(response.headers)
        }


# Singleton instance for the application
_http_client_service_instance: Optional[HTTPClientService] = None


def get_http_client_service() -> HTTPClientService:
    """
    Get the singleton instance of HTTPClientService
    
    This function can be used as a FastAPI dependency or called directly
    from other services.
    
    Returns:
        HTTPClientService: The HTTP client service instance
    """
    global _http_client_service_instance
    if _http_client_service_instance is None:
        _http_client_service_instance = HTTPClientService()
    return _http_client_service_instance

