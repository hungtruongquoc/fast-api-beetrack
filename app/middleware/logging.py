"""
Logging middleware for request context injection

This middleware adds request-specific context to all log messages within
the request lifecycle, including unique request IDs, HTTP method, path,
and response timing information.

Features:
    - Generates unique request IDs for tracing
    - Injects request context into structured logs
    - Logs request start/completion with timing
    - Handles exceptions and error logging
    - Cleans up context after request completion

Usage:
    from app.middleware.logging import LoggingMiddleware
    
    app.add_middleware(LoggingMiddleware)
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import bind_request_context, clear_request_context, get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to structured logging
    
    This middleware automatically:
    1. Generates a unique request ID for each request
    2. Binds request context (ID, method, path) to log context
    3. Logs request start and completion with timing
    4. Handles exceptions and ensures context cleanup
    5. Includes response status codes and timing in logs
    
    The request context is automatically included in all subsequent
    log messages within the request lifecycle.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging context
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint in the chain
            
        Returns:
            HTTP response with logging context properly managed
        """
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        # Extract request information
        method = request.method
        path = str(request.url.path)
        query_params = str(request.url.query) if request.url.query else None
        
        # Bind request context for all subsequent logs
        bind_request_context(request_id, method, path)
        
        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            query_params=query_params,
            user_agent=request.headers.get("user-agent"),
            client_ip=self._get_client_ip(request)
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful completion
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # Add request ID to response headers for client tracking
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log exception with context
            logger.error(
                "Request failed with exception",
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
            
        finally:
            # Always clear context to prevent leakage between requests
            clear_request_context()
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request
        
        Checks for common proxy headers before falling back to
        the direct connection IP.
        
        Args:
            request: The HTTP request object
            
        Returns:
            Client IP address as string
        """
        # Check for forwarded IP (common with load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header (some proxies use this)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        if request.client:
            return request.client.host
        
        return "unknown"