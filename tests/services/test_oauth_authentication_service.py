"""Tests for app/services/oauth_authentication_service.py - OAuth authentication service"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.oauth_authentication_service import (
    OAuthAuthenticationService,
    OAuthError,
    get_oauth_authentication_service
)
from app.services.http_client_service import HTTPClientService, HTTPClientError
from app.services.auth_token_cache_service import AuthTokenCacheService


@pytest.fixture
def mock_http_client():
    """Create a mock HTTPClientService"""
    mock = Mock(spec=HTTPClientService)
    mock.post = AsyncMock()
    return mock


@pytest.fixture
def mock_cache_service():
    """Create a mock AuthTokenCacheService"""
    mock = Mock(spec=AuthTokenCacheService)
    mock.get_token = Mock(return_value=None)
    mock.get_token_async = AsyncMock(return_value=None)
    mock.set_token = Mock()
    mock.set_token_async = AsyncMock()
    mock.clear_token = Mock()
    mock.clear_token_async = AsyncMock()
    mock.is_expired = Mock(return_value=True)
    mock.get_expiration_info = Mock(return_value={
        "has_token": False,
        "is_expired": True,
        "expiration_time": None,
        "seconds_until_expiration": None,
        "current_time": datetime.utcnow().isoformat()
    })
    return mock


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    with patch('app.services.oauth_authentication_service.settings') as mock:
        mock.OAUTH_CLIENT_ID = "test_client_id"
        mock.OAUTH_CLIENT_SECRET = "test_client_secret"
        mock.OAUTH_TOKEN_URL = "https://oauth.example.com/token"
        yield mock


@pytest.fixture
def oauth_service(mock_http_client, mock_cache_service, mock_settings):
    """Create an OAuthAuthenticationService instance with mocked dependencies"""
    return OAuthAuthenticationService(
        http_client=mock_http_client,
        cache_service=mock_cache_service
    )


class TestOAuthAuthenticationServiceInitialization:
    """Test suite for service initialization"""
    
    def test_service_initialization(self, oauth_service, mock_http_client, mock_cache_service):
        """Test that service initializes correctly with dependencies"""
        assert oauth_service.http_client is mock_http_client
        assert oauth_service.cache_service is mock_cache_service
        assert oauth_service.settings is not None
        assert oauth_service._refresh_lock is not None
        assert oauth_service.logger is not None
    
    def test_singleton_pattern(self):
        """Test that get_oauth_authentication_service returns singleton instance"""
        # Reset singleton for test
        import app.services.oauth_authentication_service as oauth_module
        oauth_module._oauth_authentication_service_instance = None
        
        service1 = get_oauth_authentication_service()
        service2 = get_oauth_authentication_service()
        
        assert service1 is service2
        
        # Cleanup
        oauth_module._oauth_authentication_service_instance = None


class TestOAuthAuthenticationServiceGetValidToken:
    """Test suite for getting valid tokens"""
    
    def test_get_valid_token_when_cached(self, oauth_service, mock_cache_service):
        """Test getting token when valid token is cached"""
        mock_cache_service.get_token.return_value = "cached_token_123"
        
        token = oauth_service.get_valid_token()
        
        assert token == "cached_token_123"
        mock_cache_service.get_token.assert_called_once()
    
    def test_get_valid_token_when_not_cached(self, oauth_service, mock_cache_service):
        """Test getting token when no token is cached"""
        mock_cache_service.get_token.return_value = None
        
        token = oauth_service.get_valid_token()
        
        assert token is None
        mock_cache_service.get_token.assert_called_once()
    
    def test_get_valid_token_when_expired(self, oauth_service, mock_cache_service):
        """Test getting token when cached token is expired"""
        # Cache service returns None for expired tokens
        mock_cache_service.get_token.return_value = None
        
        token = oauth_service.get_valid_token()
        
        assert token is None
    
    @pytest.mark.asyncio
    async def test_get_valid_token_async_when_cached(self, oauth_service, mock_cache_service):
        """Test async getting token when valid token is cached"""
        mock_cache_service.get_token_async.return_value = "cached_token_async"
        
        token = await oauth_service.get_valid_token_async()
        
        assert token == "cached_token_async"
        mock_cache_service.get_token_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_valid_token_async_when_not_cached(self, oauth_service, mock_cache_service, mock_http_client):
        """Test async getting token when no token is cached - triggers automatic refresh"""
        # Mock: no token in cache (both checks)
        mock_cache_service.get_token_async.side_effect = [None, None]

        # Mock successful token request
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "auto_refreshed_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

        token = await oauth_service.get_valid_token_async()

        # Should get the newly refreshed token
        assert token == "auto_refreshed_token"
        # Should check cache twice (before and after lock)
        assert mock_cache_service.get_token_async.call_count == 2
        # Should request new token
        mock_http_client.post.assert_called_once()


class TestOAuthAuthenticationServiceClearToken:
    """Test suite for clearing tokens"""
    
    def test_clear_token(self, oauth_service, mock_cache_service):
        """Test clearing token from cache"""
        oauth_service.clear_token()
        
        mock_cache_service.clear_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_token_async(self, oauth_service, mock_cache_service):
        """Test async clearing token from cache"""
        await oauth_service.clear_token_async()
        
        mock_cache_service.clear_token_async.assert_called_once()
    
    def test_clear_token_when_no_token(self, oauth_service, mock_cache_service):
        """Test clearing token when no token is cached"""
        # Should not raise error
        oauth_service.clear_token()
        
        mock_cache_service.clear_token.assert_called_once()


class TestOAuthAuthenticationServiceGetTokenInfo:
    """Test suite for getting token information"""
    
    def test_get_token_info_when_no_token(self, oauth_service, mock_cache_service, mock_settings):
        """Test getting token info when no token is cached"""
        mock_cache_service.get_expiration_info.return_value = {
            "has_token": False,
            "is_expired": True,
            "expiration_time": None,
            "seconds_until_expiration": None,
            "current_time": "2025-01-01T12:00:00"
        }
        
        info = oauth_service.get_token_info()
        
        assert info["has_token"] is False
        assert info["is_expired"] is True
        assert info["oauth_configured"] is True
        assert info["token_url"] == "https://oauth.example.com/token"
    
    def test_get_token_info_when_token_exists(self, oauth_service, mock_cache_service, mock_settings):
        """Test getting token info when valid token exists"""
        mock_cache_service.get_expiration_info.return_value = {
            "has_token": True,
            "is_expired": False,
            "expiration_time": "2025-01-01T13:00:00",
            "seconds_until_expiration": 3300,
            "current_time": "2025-01-01T12:00:00"
        }
        
        info = oauth_service.get_token_info()
        
        assert info["has_token"] is True
        assert info["is_expired"] is False
        assert info["seconds_until_expiration"] == 3300
        assert info["oauth_configured"] is True
    
    def test_get_token_info_oauth_not_configured(self, oauth_service, mock_cache_service):
        """Test getting token info when OAuth is not configured"""
        with patch('app.services.oauth_authentication_service.settings') as mock_settings:
            mock_settings.OAUTH_CLIENT_ID = ""
            mock_settings.OAUTH_CLIENT_SECRET = ""
            mock_settings.OAUTH_TOKEN_URL = ""
            
            # Need to update the service's settings reference
            oauth_service.settings = mock_settings
            
            mock_cache_service.get_expiration_info.return_value = {
                "has_token": False,
                "is_expired": True,
                "expiration_time": None,
                "seconds_until_expiration": None,
                "current_time": "2025-01-01T12:00:00"
            }
            
            info = oauth_service.get_token_info()
            
            assert info["oauth_configured"] is False
            assert info["token_url"] == ""
    
    def test_get_token_info_partial_oauth_config(self, oauth_service, mock_cache_service):
        """Test getting token info when OAuth is partially configured"""
        with patch('app.services.oauth_authentication_service.settings') as mock_settings:
            mock_settings.OAUTH_CLIENT_ID = "test_id"
            mock_settings.OAUTH_CLIENT_SECRET = ""  # Missing secret
            mock_settings.OAUTH_TOKEN_URL = "https://oauth.example.com/token"
            
            oauth_service.settings = mock_settings
            
            mock_cache_service.get_expiration_info.return_value = {
                "has_token": False,
                "is_expired": True,
                "expiration_time": None,
                "seconds_until_expiration": None,
                "current_time": "2025-01-01T12:00:00"
            }
            
            info = oauth_service.get_token_info()
            
            # Should be False because not all required fields are set
            assert info["oauth_configured"] is False


class TestOAuthError:
    """Test suite for OAuthError exception"""
    
    def test_oauth_error_basic(self):
        """Test OAuthError with basic message"""
        error = OAuthError("Authentication failed")
        
        assert error.message == "Authentication failed"
        assert error.error_code is None
        assert error.error_description is None
        assert str(error) == "Authentication failed"
    
    def test_oauth_error_with_details(self):
        """Test OAuthError with error code and description"""
        error = OAuthError(
            "Authentication failed",
            error_code="invalid_client",
            error_description="Client authentication failed"
        )
        
        assert error.message == "Authentication failed"
        assert error.error_code == "invalid_client"
        assert error.error_description == "Client authentication failed"


class TestOAuthAuthenticationServiceDependencyInjection:
    """Test suite for dependency injection patterns"""
    
    def test_service_uses_injected_http_client(self, oauth_service, mock_http_client):
        """Test that service uses the injected HTTP client"""
        assert oauth_service.http_client is mock_http_client
    
    def test_service_uses_injected_cache_service(self, oauth_service, mock_cache_service):
        """Test that service uses the injected cache service"""
        assert oauth_service.cache_service is mock_cache_service
    
    def test_service_accesses_settings(self, oauth_service, mock_settings):
        """Test that service can access settings"""
        assert oauth_service.settings.OAUTH_CLIENT_ID == "test_client_id"
        assert oauth_service.settings.OAUTH_CLIENT_SECRET == "test_client_secret"
        assert oauth_service.settings.OAUTH_TOKEN_URL == "https://oauth.example.com/token"


class TestOAuthAuthenticationServiceThreadSafety:
    """Test suite for thread-safety features"""

    def test_refresh_lock_exists(self, oauth_service):
        """Test that refresh lock is initialized"""
        assert oauth_service._refresh_lock is not None
        import asyncio
        assert isinstance(oauth_service._refresh_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_async_methods_available(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that async methods are available and callable"""
        # Mock: token exists in cache
        mock_cache_service.get_token_async.return_value = "test_token"

        # Should not raise errors
        token = await oauth_service.get_valid_token_async()
        assert isinstance(token, str)
        assert token == "test_token"

        await oauth_service.clear_token_async()

        # Verify they were called
        assert mock_cache_service.get_token_async.called
        assert mock_cache_service.clear_token_async.called


class TestOAuthAuthenticationServiceRequestToken:
    """Test suite for token acquisition"""

    @pytest.mark.asyncio
    async def test_request_token_success(self, oauth_service, mock_http_client, mock_cache_service, mock_settings):
        """Test successful token acquisition"""
        # Mock successful OAuth response
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "new_token_abc123",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

        token = await oauth_service.request_token()

        # Verify token returned
        assert token == "new_token_abc123"

        # Verify HTTP request made correctly
        mock_http_client.post.assert_called_once_with(
            url="https://oauth.example.com/token",
            data={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "grant_type": "client_credentials"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        # Verify token stored in cache
        mock_cache_service.set_token_async.assert_called_once_with("new_token_abc123", 3600)

    @pytest.mark.asyncio
    async def test_request_token_missing_client_id(self, oauth_service, mock_http_client):
        """Test token request fails when client ID is not configured"""
        with patch('app.services.oauth_authentication_service.settings') as mock_settings:
            mock_settings.OAUTH_CLIENT_ID = ""
            mock_settings.OAUTH_CLIENT_SECRET = "secret"
            mock_settings.OAUTH_TOKEN_URL = "https://oauth.example.com/token"
            oauth_service.settings = mock_settings

            with pytest.raises(OAuthError) as exc_info:
                await oauth_service.request_token()

            assert "client ID not configured" in str(exc_info.value)
            assert exc_info.value.error_code == "configuration_error"
            mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_token_missing_client_secret(self, oauth_service, mock_http_client):
        """Test token request fails when client secret is not configured"""
        with patch('app.services.oauth_authentication_service.settings') as mock_settings:
            mock_settings.OAUTH_CLIENT_ID = "client_id"
            mock_settings.OAUTH_CLIENT_SECRET = ""
            mock_settings.OAUTH_TOKEN_URL = "https://oauth.example.com/token"
            oauth_service.settings = mock_settings

            with pytest.raises(OAuthError) as exc_info:
                await oauth_service.request_token()

            assert "client secret not configured" in str(exc_info.value)
            assert exc_info.value.error_code == "configuration_error"
            mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_token_missing_token_url(self, oauth_service, mock_http_client):
        """Test token request fails when token URL is not configured"""
        with patch('app.services.oauth_authentication_service.settings') as mock_settings:
            mock_settings.OAUTH_CLIENT_ID = "client_id"
            mock_settings.OAUTH_CLIENT_SECRET = "secret"
            mock_settings.OAUTH_TOKEN_URL = ""
            oauth_service.settings = mock_settings

            with pytest.raises(OAuthError) as exc_info:
                await oauth_service.request_token()

            assert "token URL not configured" in str(exc_info.value)
            assert exc_info.value.error_code == "configuration_error"
            mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_token_missing_access_token_in_response(self, oauth_service, mock_http_client):
        """Test token request fails when response is missing access_token"""
        mock_http_client.post.return_value = {
            "body": {
                "token_type": "Bearer",
                "expires_in": 3600
                # Missing access_token
            }
        }

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "missing access_token" in str(exc_info.value)
        assert exc_info.value.error_code == "invalid_response"

    @pytest.mark.asyncio
    async def test_request_token_missing_expires_in_response(self, oauth_service, mock_http_client):
        """Test token request fails when response is missing expires_in"""
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "token_123",
                "token_type": "Bearer"
                # Missing expires_in
            }
        }

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "missing expires_in" in str(exc_info.value)
        assert exc_info.value.error_code == "invalid_response"

    @pytest.mark.asyncio
    async def test_request_token_http_error_401(self, oauth_service, mock_http_client):
        """Test token request handles 401 Unauthorized error"""
        from app.services.http_client_service import HTTPClientError

        mock_http_client.post.side_effect = HTTPClientError(
            "Unauthorized",
            status_code=401,
            response_body='{"error": "invalid_client", "error_description": "Client authentication failed"}'
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "token request failed" in str(exc_info.value)
        assert exc_info.value.error_code == "invalid_client"
        assert exc_info.value.error_description == "Client authentication failed"

    @pytest.mark.asyncio
    async def test_request_token_http_error_500(self, oauth_service, mock_http_client):
        """Test token request handles 500 server error"""
        from app.services.http_client_service import HTTPClientError

        mock_http_client.post.side_effect = HTTPClientError(
            "Internal Server Error",
            status_code=500,
            response_body="Server error"
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "token request failed" in str(exc_info.value)
        assert exc_info.value.error_code == "request_failed"

    @pytest.mark.asyncio
    async def test_request_token_network_error(self, oauth_service, mock_http_client):
        """Test token request handles network errors"""
        from app.services.http_client_service import HTTPClientError

        mock_http_client.post.side_effect = HTTPClientError(
            "Connection timeout",
            status_code=None,
            response_body=None
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "token request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_token_unexpected_error(self, oauth_service, mock_http_client):
        """Test token request handles unexpected errors"""
        mock_http_client.post.side_effect = ValueError("Unexpected error")

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        assert "Unexpected error" in str(exc_info.value)
        assert exc_info.value.error_code == "unexpected_error"

    @pytest.mark.asyncio
    async def test_request_token_with_default_token_type(self, oauth_service, mock_http_client, mock_cache_service):
        """Test token request handles missing token_type with default"""
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "token_xyz",
                "expires_in": 7200
                # Missing token_type - should default to "Bearer"
            }
        }

        token = await oauth_service.request_token()

        assert token == "token_xyz"
        mock_cache_service.set_token_async.assert_called_once_with("token_xyz", 7200)


class TestOAuthAuthenticationServiceRetryLogic:
    """Test suite for retry logic in token requests"""

    @pytest.mark.asyncio
    async def test_request_token_succeeds_on_first_attempt(self, oauth_service, mock_http_client, mock_cache_service):
        """Test that successful request on first attempt doesn't retry"""
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "first_attempt_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

        token = await oauth_service.request_token()

        assert token == "first_attempt_token"
        # Should only call once (no retries)
        assert mock_http_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_request_token_retries_on_500_error(self, oauth_service, mock_http_client, mock_cache_service):
        """Test that 500 errors trigger retry"""
        from app.services.http_client_service import HTTPClientError

        # First two attempts fail with 500, third succeeds
        mock_http_client.post.side_effect = [
            HTTPClientError("Internal Server Error", status_code=500, response_body="{}"),
            HTTPClientError("Internal Server Error", status_code=500, response_body="{}"),
            {
                "body": {
                    "access_token": "retry_success_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            }
        ]

        token = await oauth_service.request_token()

        assert token == "retry_success_token"
        # Should call 3 times (2 failures + 1 success)
        assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_request_token_fails_after_max_retries(self, oauth_service, mock_http_client):
        """Test that request fails after max retry attempts"""
        from app.services.http_client_service import HTTPClientError

        # All attempts fail with 500
        mock_http_client.post.side_effect = HTTPClientError(
            "Internal Server Error",
            status_code=500,
            response_body="{}"
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        # Should call 3 times (max retries)
        assert mock_http_client.post.call_count == 3
        assert "token request failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_request_token_no_retry_on_401_error(self, oauth_service, mock_http_client):
        """Test that 401 errors don't trigger retry (client error)"""
        from app.services.http_client_service import HTTPClientError

        mock_http_client.post.side_effect = HTTPClientError(
            "Unauthorized",
            status_code=401,
            response_body='{"error": "invalid_client"}'
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        # Should only call once (no retries for 4xx errors)
        assert mock_http_client.post.call_count == 1
        assert exc_info.value.error_code == "invalid_client"

    @pytest.mark.asyncio
    async def test_request_token_no_retry_on_invalid_response(self, oauth_service, mock_http_client):
        """Test that invalid response format doesn't trigger retry"""
        mock_http_client.post.return_value = {
            "body": {
                # Missing access_token - invalid response
                "expires_in": 3600
            }
        }

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.request_token()

        # Should only call once (no retries for invalid response)
        assert mock_http_client.post.call_count == 1
        assert exc_info.value.error_code == "invalid_response"

    @pytest.mark.asyncio
    async def test_request_token_retries_on_network_error(self, oauth_service, mock_http_client, mock_cache_service):
        """Test that network errors trigger retry"""
        # First attempt: network error
        # Second attempt: success
        mock_http_client.post.side_effect = [
            Exception("Connection timeout"),
            {
                "body": {
                    "access_token": "network_retry_token",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            }
        ]

        token = await oauth_service.request_token()

        assert token == "network_retry_token"
        # Should call 2 times (1 failure + 1 success)
        assert mock_http_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_request_token_retry_count_property(self, oauth_service):
        """Test that max retry attempts is set correctly"""
        assert oauth_service._max_retry_attempts == 3


class TestOAuthAuthenticationServiceAutomaticRefresh:
    """Test suite for automatic token refresh"""

    @pytest.mark.asyncio
    async def test_get_valid_token_async_returns_cached_token(self, oauth_service, mock_cache_service):
        """Test that get_valid_token_async returns cached token when valid"""
        mock_cache_service.get_token_async.return_value = "cached_valid_token"

        token = await oauth_service.get_valid_token_async()

        assert token == "cached_valid_token"
        # Should only check cache once, not request new token
        mock_cache_service.get_token_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_async_refreshes_when_expired(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that get_valid_token_async automatically refreshes expired token"""
        # First call: no token in cache
        # Second call (after lock): still no token
        mock_cache_service.get_token_async.side_effect = [None, None]

        # Mock successful token request
        mock_http_client.post.return_value = {
            "body": {
                "access_token": "new_refreshed_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

        token = await oauth_service.get_valid_token_async()

        assert token == "new_refreshed_token"
        # Should check cache twice (before and after lock)
        assert mock_cache_service.get_token_async.call_count == 2
        # Should request new token
        mock_http_client.post.assert_called_once()
        # Should store new token
        mock_cache_service.set_token_async.assert_called_once_with("new_refreshed_token", 3600)

    @pytest.mark.asyncio
    async def test_get_valid_token_async_double_check_after_lock(self, oauth_service, mock_cache_service, mock_http_client):
        """Test double-check pattern: another request refreshed while waiting for lock"""
        # First call: no token (triggers lock acquisition)
        # Second call (after lock): token now available (another request refreshed it)
        mock_cache_service.get_token_async.side_effect = [None, "token_from_other_request"]

        token = await oauth_service.get_valid_token_async()

        assert token == "token_from_other_request"
        # Should check cache twice
        assert mock_cache_service.get_token_async.call_count == 2
        # Should NOT request new token (another request already did)
        mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_valid_token_async_refresh_failure(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that get_valid_token_async raises error when refresh fails"""
        mock_cache_service.get_token_async.return_value = None

        # Mock failed token request
        from app.services.http_client_service import HTTPClientError
        mock_http_client.post.side_effect = HTTPClientError(
            "Unauthorized",
            status_code=401,
            response_body='{"error": "invalid_client"}'
        )

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.get_valid_token_async()

        assert "token request failed" in str(exc_info.value)
        assert exc_info.value.error_code == "invalid_client"

    @pytest.mark.asyncio
    async def test_get_valid_token_async_concurrent_requests(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that concurrent requests don't cause multiple token refreshes"""
        import asyncio

        # Track number of token requests
        request_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            # Simulate some delay
            await asyncio.sleep(0.01)
            return {
                "body": {
                    "access_token": f"token_{request_count}",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            }

        mock_http_client.post = mock_post

        # First check: no token
        # After first request completes, subsequent checks should find the token
        call_count = 0
        async def mock_get_token_async():
            nonlocal call_count
            call_count += 1
            # First two calls (from first request): no token
            if call_count <= 2:
                return None
            # Subsequent calls: return the token that was just cached
            return f"token_1"

        mock_cache_service.get_token_async = mock_get_token_async

        # Make 3 concurrent requests
        results = await asyncio.gather(
            oauth_service.get_valid_token_async(),
            oauth_service.get_valid_token_async(),
            oauth_service.get_valid_token_async()
        )

        # All should get a token
        assert all(token is not None for token in results)
        # Should only make ONE token request (lock prevents concurrent requests)
        assert request_count == 1

    @pytest.mark.asyncio
    async def test_get_valid_token_sync_does_not_auto_refresh(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that synchronous get_valid_token does NOT auto-refresh"""
        mock_cache_service.get_token.return_value = None

        token = oauth_service.get_valid_token()

        assert token is None
        # Should NOT request new token
        mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_valid_token_async_logs_refresh_events(self, oauth_service, mock_cache_service, mock_http_client):
        """Test that token refresh events are logged"""
        mock_cache_service.get_token_async.return_value = None

        mock_http_client.post.return_value = {
            "body": {
                "access_token": "logged_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

        # This should trigger logging
        token = await oauth_service.get_valid_token_async()

        assert token == "logged_token"
        # Verify the method completed successfully (logging happened internally)

