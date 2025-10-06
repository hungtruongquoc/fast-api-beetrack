"""
Authentication Token Cache Service

This module provides the AuthTokenCacheService for storing and managing
authentication tokens in memory with expiration tracking. The service
implements intelligent expiration logic with a configurable buffer to
ensure tokens are refreshed before they actually expire.

The cache is designed for OAuth access tokens but can be used for any
token-based authentication mechanism that provides expiration information.

Architecture:
    OAuthAuthenticationService → AuthTokenCacheService → In-Memory Storage

Classes:
    AuthTokenCacheService: Service for token caching with expiration tracking

Functions:
    get_auth_token_cache_service: Factory function returning singleton instance
"""

from typing import Optional
from datetime import datetime, timedelta
import asyncio

from app.core.logging import get_logger
from app.core.config import settings


class AuthTokenCacheService:
    """
    Service for caching authentication tokens with expiration tracking

    This service stores authentication tokens in memory along with their
    expiration timestamps. It implements a buffer mechanism to ensure
    tokens are considered expired before their actual expiration time,
    allowing for proactive token refresh.

    The service is thread-safe using asyncio.Lock for concurrent access
    protection in async environments.

    Current Implementation: In-memory storage (instance variables)

    FUTURE ENHANCEMENT: For production multi-instance deployments, consider
    implementing pluggable storage backends (Redis, database, etc.) using
    the Strategy Pattern. See specs/oauth_authentication_token_management.md
    section "Token Storage Backend Extensibility" for detailed design and
    implementation guidance.

    When to migrate:
    - Horizontal scaling (multiple app instances)
    - High availability requirements
    - Token persistence across restarts needed
    - Production deployment with load balancing
    
    Attributes:
        _token (Optional[str]): The cached authentication token
        _expiration_time (Optional[datetime]): When the token expires (with buffer applied)
        _lock (asyncio.Lock): Lock for thread-safe operations
        logger: Structured logger instance
    
    Methods:
        set_token: Store a token with expiration time
        get_token: Retrieve token if valid, None if expired/missing
        is_expired: Check if token is expired or near expiration
        clear_token: Clear the cached token
        get_expiration_info: Get detailed expiration information
    """
    
    def __init__(self):
        """
        Initialize the token cache service
        
        Creates empty cache storage and initializes the async lock
        for thread-safe operations.
        """
        self._token: Optional[str] = None
        self._expiration_time: Optional[datetime] = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self.logger = get_logger(__name__)
        
        self.logger.debug(
            "AuthTokenCacheService initialized",
            buffer_seconds=settings.TOKEN_EXPIRATION_BUFFER_SECONDS
        )
    
    def set_token(self, token: str, expires_in: int) -> None:
        """
        Store an authentication token with expiration time
        
        Calculates the expiration time by subtracting the buffer from
        the provided expires_in value. This ensures the token is
        considered expired before it actually expires, allowing time
        for refresh operations.
        
        Args:
            token: The authentication token to cache
            expires_in: Token lifetime in seconds from now
        
        Example:
            # Token expires in 3600 seconds (1 hour)
            # With 300 second buffer, will be considered expired after 3300 seconds
            cache_service.set_token("eyJhbGc...", 3600)
        """
        if expires_in <= 0:
            self.logger.warning(
                "Invalid expires_in value, token not cached",
                expires_in=expires_in
            )
            return
        
        # Calculate expiration time with buffer
        buffer_seconds = settings.TOKEN_EXPIRATION_BUFFER_SECONDS
        effective_lifetime = max(expires_in - buffer_seconds, 0)
        self._expiration_time = datetime.utcnow() + timedelta(seconds=effective_lifetime)
        self._token = token
        
        self.logger.info(
            "Token cached successfully",
            expires_in=expires_in,
            buffer_seconds=buffer_seconds,
            effective_lifetime=effective_lifetime,
            expiration_time=self._expiration_time.isoformat()
        )
    
    def get_token(self) -> Optional[str]:
        """
        Get the cached token if it exists and is not expired
        
        Returns the token only if it exists and has not reached its
        expiration time (including buffer). Returns None if the token
        is expired or doesn't exist.
        
        Returns:
            Optional[str]: The cached token if valid, None otherwise
        
        Example:
            token = cache_service.get_token()
            if token:
                # Use token for API call
                headers = {"Authorization": f"Bearer {token}"}
            else:
                # Token expired or missing, need to refresh
                pass
        """
        if self._token is None:
            self.logger.debug("No token in cache")
            return None
        
        if self.is_expired():
            self.logger.debug("Token in cache is expired")
            return None
        
        self.logger.debug("Returning valid token from cache")
        return self._token
    
    def is_expired(self) -> bool:
        """
        Check if the cached token is expired or near expiration
        
        Returns True if:
        - No token is cached
        - No expiration time is set
        - Current time has passed the expiration time (with buffer)
        
        Returns:
            bool: True if token is expired/missing, False if valid
        
        Example:
            if cache_service.is_expired():
                # Request new token
                new_token = await oauth_service.request_token()
        """
        if self._token is None or self._expiration_time is None:
            return True
        
        is_expired = datetime.utcnow() >= self._expiration_time
        
        if is_expired:
            self.logger.debug(
                "Token is expired",
                expiration_time=self._expiration_time.isoformat(),
                current_time=datetime.utcnow().isoformat()
            )
        
        return is_expired
    
    def clear_token(self) -> None:
        """
        Clear the cached token and expiration time
        
        Removes the token from cache. Useful for:
        - Logout operations
        - Forcing token refresh
        - Error recovery scenarios
        
        Example:
            # Force token refresh on next request
            cache_service.clear_token()
        """
        had_token = self._token is not None
        self._token = None
        self._expiration_time = None
        
        if had_token:
            self.logger.info("Token cleared from cache")
        else:
            self.logger.debug("Clear token called but no token was cached")
    
    def get_expiration_info(self) -> dict:
        """
        Get detailed information about token expiration
        
        Provides comprehensive information about the cached token's
        expiration status. Useful for monitoring, debugging, and
        status endpoints.
        
        Returns:
            dict: Dictionary containing:
                - has_token (bool): Whether a token is cached
                - is_expired (bool): Whether the token is expired
                - expiration_time (str|None): ISO format expiration time
                - seconds_until_expiration (int|None): Seconds until expiration
                - current_time (str): Current time in ISO format
        
        Example:
            info = cache_service.get_expiration_info()
            print(f"Token expires in {info['seconds_until_expiration']} seconds")
        """
        current_time = datetime.utcnow()
        
        info = {
            "has_token": self._token is not None,
            "is_expired": self.is_expired(),
            "expiration_time": self._expiration_time.isoformat() if self._expiration_time else None,
            "current_time": current_time.isoformat()
        }
        
        if self._expiration_time and not self.is_expired():
            time_remaining = self._expiration_time - current_time
            info["seconds_until_expiration"] = int(time_remaining.total_seconds())
        else:
            info["seconds_until_expiration"] = None
        
        return info
    
    async def get_token_async(self) -> Optional[str]:
        """
        Thread-safe async version of get_token
        
        Uses asyncio.Lock to ensure thread-safe access in concurrent
        environments. Use this method when multiple async tasks might
        access the cache simultaneously.
        
        Returns:
            Optional[str]: The cached token if valid, None otherwise
        """
        async with self._lock:
            return self.get_token()
    
    async def set_token_async(self, token: str, expires_in: int) -> None:
        """
        Thread-safe async version of set_token
        
        Uses asyncio.Lock to ensure thread-safe access in concurrent
        environments. Use this method when multiple async tasks might
        update the cache simultaneously.
        
        Args:
            token: The authentication token to cache
            expires_in: Token lifetime in seconds from now
        """
        async with self._lock:
            self.set_token(token, expires_in)
    
    async def clear_token_async(self) -> None:
        """
        Thread-safe async version of clear_token
        
        Uses asyncio.Lock to ensure thread-safe access in concurrent
        environments.
        """
        async with self._lock:
            self.clear_token()


# Singleton instance for the application
_auth_token_cache_service_instance: Optional[AuthTokenCacheService] = None


def get_auth_token_cache_service() -> AuthTokenCacheService:
    """
    Get the singleton instance of AuthTokenCacheService
    
    This function can be used as a FastAPI dependency or called directly
    from other services.
    
    Returns:
        AuthTokenCacheService: The token cache service instance
    
    Example:
        # As a dependency
        @app.get("/status")
        async def get_status(
            cache_service: AuthTokenCacheService = Depends(get_auth_token_cache_service)
        ):
            return cache_service.get_expiration_info()
        
        # Direct usage
        cache_service = get_auth_token_cache_service()
        cache_service.set_token("token123", 3600)
    """
    global _auth_token_cache_service_instance
    if _auth_token_cache_service_instance is None:
        _auth_token_cache_service_instance = AuthTokenCacheService()
    return _auth_token_cache_service_instance

