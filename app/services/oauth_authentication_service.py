"""
OAuth Authentication Service

This module provides the OAuthAuthenticationService for managing OAuth 2.0
Client Credentials flow authentication. The service orchestrates token
acquisition, caching, and automatic refresh for backend-to-backend
authentication.

The service acts as the main entry point for obtaining valid OAuth tokens,
coordinating between HTTPClientService for token requests and
AuthTokenCacheService for token storage.

Architecture:
    API/Services → OAuthAuthenticationService → HTTPClientService + AuthTokenCacheService

Classes:
    OAuthAuthenticationService: Service for OAuth token lifecycle management
    OAuthError: Custom exception for OAuth-related errors

Functions:
    get_oauth_authentication_service: Factory function returning singleton instance
"""

from typing import Optional, Dict, Any
import asyncio

from app.core.logging import get_logger
from app.core.config import settings  # Note: Global import for simplicity. See spec for DI alternative.
from app.services.http_client_service import (
    HTTPClientService,
    HTTPClientError,
    get_http_client_service
)
from app.services.auth_token_cache_service import (
    AuthTokenCacheService,
    get_auth_token_cache_service
)


class OAuthError(Exception):
    """
    Custom exception for OAuth authentication errors
    
    Attributes:
        message: Error message
        error_code: OAuth error code (if available)
        error_description: OAuth error description (if available)
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        error_description: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.error_description = error_description
        super().__init__(self.message)


class OAuthAuthenticationService:
    """
    Service for managing OAuth 2.0 Client Credentials authentication

    This service orchestrates the OAuth token lifecycle:
    1. Check cache for valid token
    2. Request new token if cache is empty or expired
    3. Store token in cache with expiration
    4. Provide automatic refresh before expiration

    The service uses dependency injection to coordinate between:
    - HTTPClientService: For making OAuth token requests
    - AuthTokenCacheService: For storing and retrieving tokens
    - Settings: For OAuth configuration (client ID, secret, token URL)

    Thread-safe for concurrent access using asyncio.Lock.

    Design Note - Settings Dependency:
    This service uses global settings import (from app.core.config import settings)
    rather than constructor injection for simplicity and FastAPI convention.
    For discussion of trade-offs and refactoring guidance, see:
    specs/oauth_authentication_token_management.md
    section "Settings Dependency: Global Import vs Dependency Injection"
    
    Attributes:
        http_client (HTTPClientService): HTTP client for token requests
        cache_service (AuthTokenCacheService): Token cache service
        settings: Application settings with OAuth configuration
        _refresh_lock (asyncio.Lock): Lock to prevent concurrent token refresh
        _max_retry_attempts (int): Maximum number of retry attempts for token requests
        logger: Structured logger instance

    Methods:
        get_valid_token: Get a valid token (from cache or by requesting new one)
        get_valid_token_async: Async version of get_valid_token
        clear_token: Clear the cached token
        clear_token_async: Async version of clear_token
        get_token_info: Get information about current token status
        request_token: Request a new token from OAuth provider (with retry logic)
    """

    def __init__(
        self,
        http_client: HTTPClientService,
        cache_service: AuthTokenCacheService
    ):
        """
        Initialize the OAuth authentication service

        Args:
            http_client: HTTPClientService instance for making token requests
            cache_service: AuthTokenCacheService instance for token storage
        """
        self.http_client = http_client
        self.cache_service = cache_service
        self.settings = settings
        self._refresh_lock: asyncio.Lock = asyncio.Lock()
        self._max_retry_attempts: int = 3  # Retry token requests up to 3 times
        self.logger = get_logger(__name__)

        self.logger.info(
            "OAuthAuthenticationService initialized",
            token_url=self.settings.OAUTH_TOKEN_URL,
            has_client_id=bool(self.settings.OAUTH_CLIENT_ID),
            has_client_secret=bool(self.settings.OAUTH_CLIENT_SECRET),
            max_retry_attempts=self._max_retry_attempts
        )
    
    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid OAuth token from cache (synchronous, no auto-refresh)

        Checks the cache and returns the cached token if it's still valid.
        Returns None if no token is cached or if the cached token is expired.

        ⚠️ IMPORTANT: This method does NOT automatically refresh expired tokens.
        For automatic token refresh, use get_valid_token_async() instead.

        Use this method when:
        - You only want to check if a valid token exists
        - You're in a synchronous context
        - You want to handle token refresh manually

        For most use cases, prefer get_valid_token_async() which handles
        automatic token refresh with thread-safe locking.

        Returns:
            str: Valid OAuth access token if available in cache
            None: If no valid token is cached (expired or missing)

        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> token = oauth_service.get_valid_token()
            >>> if token:
            ...     headers = {"Authorization": f"Bearer {token}"}
            ... else:
            ...     # Need to request new token manually
            ...     token = await oauth_service.request_token()
        """
        token = self.cache_service.get_token()

        if token:
            self.logger.debug("Valid token retrieved from cache")
        else:
            self.logger.debug("No valid token in cache")

        return token
    
    async def get_valid_token_async(self) -> str:
        """
        Get a valid OAuth token with automatic refresh (async, thread-safe)

        This method implements automatic token refresh:
        1. Check cache for valid token
        2. If valid token exists, return it
        3. If token is expired/missing, automatically request new token
        4. Use lock to prevent concurrent refresh requests
        5. Double-check after acquiring lock (another request may have refreshed)

        Thread-safe using asyncio.Lock to prevent multiple simultaneous
        token refresh requests in concurrent environments.

        Returns:
            str: Valid OAuth access token

        Raises:
            OAuthError: If token refresh fails

        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> token = await oauth_service.get_valid_token_async()
            >>> headers = {"Authorization": f"Bearer {token}"}
        """
        # First check: Try to get token from cache without lock
        token = await self.cache_service.get_token_async()

        if token:
            self.logger.debug("Valid token retrieved from cache")
            return token

        # Token is expired or missing, need to refresh
        self.logger.info("Token expired or missing, acquiring refresh lock")

        # Acquire lock to prevent concurrent refresh requests
        async with self._refresh_lock:
            # Double-check: Another request may have refreshed while we waited for lock
            token = await self.cache_service.get_token_async()

            if token:
                self.logger.info("Token was refreshed by another request")
                return token

            # Still no valid token, request new one
            self.logger.info("Requesting new token")
            try:
                token = await self.request_token()
                self.logger.info("Token refresh successful")
                return token
            except OAuthError as e:
                self.logger.error(
                    "Token refresh failed",
                    error_code=e.error_code,
                    error_message=e.message
                )
                raise
    
    def clear_token(self) -> None:
        """
        Clear the cached token (synchronous version)
        
        Removes the token from cache, forcing a new token request
        on the next get_valid_token() call.
        
        Useful for:
        - Forcing token refresh
        - Handling authentication errors
        - Logout/cleanup operations
        
        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> oauth_service.clear_token()
            >>> # Next call will need to request new token
        """
        self.cache_service.clear_token()
        self.logger.info("Token cleared from cache")
    
    async def clear_token_async(self) -> None:
        """
        Clear the cached token (async version with thread-safety)
        
        Thread-safe version that uses the cache service's async methods
        to ensure proper locking in concurrent environments.
        
        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> await oauth_service.clear_token_async()
        """
        await self.cache_service.clear_token_async()
        self.logger.info("Token cleared from cache (async)")
    
    async def request_token(self) -> str:
        """
        Request a new OAuth token from the OAuth provider

        Makes a POST request to the OAuth token endpoint using the
        Client Credentials flow. Stores the received token in the cache
        and returns it.

        OAuth 2.0 Client Credentials Flow:
        - POST to OAUTH_TOKEN_URL
        - Body: client_id, client_secret, grant_type=client_credentials
        - Response: access_token, token_type, expires_in

        Returns:
            str: The newly acquired access token

        Raises:
            OAuthError: If OAuth configuration is missing or invalid
            OAuthError: If token request fails (network, auth, server errors)
            OAuthError: If response is missing required fields

        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> token = await oauth_service.request_token()
            >>> print(f"Got token: {token[:20]}...")
        """
        # Validate OAuth configuration
        if not self.settings.OAUTH_CLIENT_ID:
            self.logger.error("OAuth client ID not configured")
            raise OAuthError(
                "OAuth client ID not configured",
                error_code="configuration_error"
            )

        if not self.settings.OAUTH_CLIENT_SECRET:
            self.logger.error("OAuth client secret not configured")
            raise OAuthError(
                "OAuth client secret not configured",
                error_code="configuration_error"
            )

        if not self.settings.OAUTH_TOKEN_URL:
            self.logger.error("OAuth token URL not configured")
            raise OAuthError(
                "OAuth token URL not configured",
                error_code="configuration_error"
            )

        self.logger.info(
            "Requesting new OAuth token",
            token_url=self.settings.OAUTH_TOKEN_URL,
            max_retry_attempts=self._max_retry_attempts
        )

        # Retry loop for token requests
        last_error = None
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                if attempt > 1:
                    self.logger.info(
                        "Retrying token request",
                        attempt=attempt,
                        max_attempts=self._max_retry_attempts
                    )

                # Make OAuth token request using Client Credentials flow
                response = await self.http_client.post(
                    url=self.settings.OAUTH_TOKEN_URL,
                    data={
                        "client_id": self.settings.OAUTH_CLIENT_ID,
                        "client_secret": self.settings.OAUTH_CLIENT_SECRET,
                        "grant_type": "client_credentials"
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

                # Extract response body
                response_body = response.get("body", {})

                # Validate required fields in response
                if "access_token" not in response_body:
                    self.logger.error(
                        "OAuth response missing access_token",
                        response_body=response_body,
                        attempt=attempt
                    )
                    raise OAuthError(
                        "OAuth response missing access_token field",
                        error_code="invalid_response"
                    )

                if "expires_in" not in response_body:
                    self.logger.error(
                        "OAuth response missing expires_in",
                        response_body=response_body,
                        attempt=attempt
                    )
                    raise OAuthError(
                        "OAuth response missing expires_in field",
                        error_code="invalid_response"
                    )

                # Extract token details
                access_token = response_body["access_token"]
                expires_in = response_body["expires_in"]
                token_type = response_body.get("token_type", "Bearer")

                # Store token in cache
                await self.cache_service.set_token_async(access_token, expires_in)

                self.logger.info(
                    "OAuth token acquired successfully",
                    token_type=token_type,
                    expires_in=expires_in,
                    attempt=attempt
                )

                return access_token

            except OAuthError as e:
                # Don't retry on configuration errors or invalid response format
                # These are not transient errors
                if e.error_code in ("configuration_error", "invalid_response"):
                    self.logger.error(
                        "Non-retryable OAuth error",
                        error_code=e.error_code,
                        attempt=attempt
                    )
                    raise

                # For other OAuth errors, save and potentially retry
                last_error = e
                self.logger.warning(
                    "OAuth error, may retry",
                    error_code=e.error_code,
                    error_message=e.message,
                    attempt=attempt,
                    will_retry=(attempt < self._max_retry_attempts)
                )

                if attempt >= self._max_retry_attempts:
                    raise

            except HTTPClientError as e:
                # Handle HTTP errors from OAuth provider
                self.logger.error(
                    "OAuth token request failed",
                    status_code=e.status_code,
                    error_message=e.message,
                    response_body=e.response_body,
                    attempt=attempt
                )

                # Try to extract OAuth error details from response
                error_code = None
                error_description = None

                if e.response_body:
                    try:
                        import json
                        error_data = json.loads(e.response_body)
                        error_code = error_data.get("error")
                        error_description = error_data.get("error_description")
                    except (json.JSONDecodeError, AttributeError):
                        pass

                # Don't retry on 4xx errors (except 429 rate limit)
                # These are client errors that won't be fixed by retrying
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    self.logger.error(
                        "Non-retryable HTTP client error",
                        status_code=e.status_code,
                        attempt=attempt
                    )
                    raise OAuthError(
                        f"OAuth token request failed: {e.message}",
                        error_code=error_code or "request_failed",
                        error_description=error_description
                    ) from e

                # For 5xx errors or network errors, save and potentially retry
                last_error = OAuthError(
                    f"OAuth token request failed: {e.message}",
                    error_code=error_code or "request_failed",
                    error_description=error_description
                )

                self.logger.warning(
                    "HTTP error, may retry",
                    status_code=e.status_code,
                    attempt=attempt,
                    will_retry=(attempt < self._max_retry_attempts)
                )

                if attempt >= self._max_retry_attempts:
                    raise last_error from e

            except Exception as e:
                # Handle unexpected errors
                self.logger.error(
                    "Unexpected error during token request",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    attempt=attempt
                )

                last_error = OAuthError(
                    f"Unexpected error during token request: {str(e)}",
                    error_code="unexpected_error"
                )

                self.logger.warning(
                    "Unexpected error, may retry",
                    attempt=attempt,
                    will_retry=(attempt < self._max_retry_attempts)
                )

                if attempt >= self._max_retry_attempts:
                    raise last_error from e

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise OAuthError(
            "Token request failed after all retry attempts",
            error_code="max_retries_exceeded"
        )

    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token status

        Returns detailed information about the cached token including
        expiration status, time until expiration, and configuration.

        Returns:
            dict: Token information including:
                - has_token: Whether a token is cached
                - is_expired: Whether the token is expired
                - expiration_time: ISO format expiration time
                - seconds_until_expiration: Seconds until expiration
                - current_time: Current time in ISO format
                - oauth_configured: Whether OAuth settings are configured
                - token_url: OAuth token endpoint URL

        Example:
            >>> oauth_service = get_oauth_authentication_service()
            >>> info = oauth_service.get_token_info()
            >>> print(f"Token expires in {info['seconds_until_expiration']} seconds")
        """
        cache_info = self.cache_service.get_expiration_info()

        # Add OAuth configuration status
        oauth_configured = bool(
            self.settings.OAUTH_CLIENT_ID and
            self.settings.OAUTH_CLIENT_SECRET and
            self.settings.OAUTH_TOKEN_URL
        )

        return {
            **cache_info,
            "oauth_configured": oauth_configured,
            "token_url": self.settings.OAUTH_TOKEN_URL
        }


# Singleton instance
_oauth_authentication_service_instance: Optional[OAuthAuthenticationService] = None


def get_oauth_authentication_service() -> OAuthAuthenticationService:
    """
    Get the singleton instance of OAuthAuthenticationService
    
    Factory function that creates and returns the singleton instance
    of OAuthAuthenticationService. The instance is created on first call
    and reused for all subsequent calls.
    
    The service is initialized with singleton instances of:
    - HTTPClientService (for making token requests)
    - AuthTokenCacheService (for token storage)
    
    Returns:
        OAuthAuthenticationService: Singleton service instance
    
    Example:
        >>> # In FastAPI endpoint
        >>> from fastapi import Depends
        >>> 
        >>> @app.get("/data")
        >>> async def get_data(
        ...     oauth_service: OAuthAuthenticationService = Depends(get_oauth_authentication_service)
        ... ):
        ...     token = await oauth_service.get_valid_token_async()
        ...     # Use token for authenticated requests
    """
    global _oauth_authentication_service_instance
    
    if _oauth_authentication_service_instance is None:
        http_client = get_http_client_service()
        cache_service = get_auth_token_cache_service()
        _oauth_authentication_service_instance = OAuthAuthenticationService(
            http_client=http_client,
            cache_service=cache_service
        )
    
    return _oauth_authentication_service_instance

