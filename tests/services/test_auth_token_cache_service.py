"""Tests for app/services/auth_token_cache_service.py - Authentication token cache service"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.auth_token_cache_service import (
    AuthTokenCacheService,
    get_auth_token_cache_service
)


@pytest.fixture
def cache_service():
    """Create a fresh AuthTokenCacheService instance for each test"""
    return AuthTokenCacheService()


@pytest.fixture
def mock_datetime():
    """Create a mock datetime that can be controlled in tests"""
    def _create_mock(current_time: datetime):
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            return mock_dt
    return _create_mock


class TestAuthTokenCacheServiceInitialization:
    """Test suite for service initialization"""
    
    def test_service_initialization(self, cache_service):
        """Test that service initializes correctly"""
        assert cache_service._token is None
        assert cache_service._expiration_time is None
        assert cache_service.logger is not None
        assert cache_service._lock is not None
    
    def test_singleton_pattern(self):
        """Test that get_auth_token_cache_service returns singleton instance"""
        service1 = get_auth_token_cache_service()
        service2 = get_auth_token_cache_service()
        
        assert service1 is service2


class TestAuthTokenCacheServiceSetToken:
    """Test suite for setting tokens"""
    
    def test_set_token_success(self, cache_service):
        """Test successfully setting a token"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("test_token_123", 3600)
            
            assert cache_service._token == "test_token_123"
            assert cache_service._expiration_time is not None
            # Should expire in 3600 - 300 (buffer) = 3300 seconds
            expected_expiration = current_time + timedelta(seconds=3300)
            assert cache_service._expiration_time == expected_expiration
    
    def test_set_token_with_buffer(self, cache_service):
        """Test that buffer is correctly applied to expiration time"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            with patch('app.services.auth_token_cache_service.settings') as mock_settings:
                current_time = datetime(2025, 1, 1, 12, 0, 0)
                mock_dt.utcnow.return_value = current_time
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                mock_settings.TOKEN_EXPIRATION_BUFFER_SECONDS = 600  # 10 minutes
                
                cache_service.set_token("token", 3600)
                
                # Should expire in 3600 - 600 = 3000 seconds
                expected_expiration = current_time + timedelta(seconds=3000)
                assert cache_service._expiration_time == expected_expiration
    
    def test_set_token_zero_expires_in(self, cache_service):
        """Test setting token with zero expires_in"""
        cache_service.set_token("token", 0)
        
        # Token should not be cached
        assert cache_service._token is None
        assert cache_service._expiration_time is None
    
    def test_set_token_negative_expires_in(self, cache_service):
        """Test setting token with negative expires_in"""
        cache_service.set_token("token", -100)
        
        # Token should not be cached
        assert cache_service._token is None
        assert cache_service._expiration_time is None
    
    def test_set_token_expires_in_less_than_buffer(self, cache_service):
        """Test setting token when expires_in is less than buffer"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            with patch('app.services.auth_token_cache_service.settings') as mock_settings:
                current_time = datetime(2025, 1, 1, 12, 0, 0)
                mock_dt.utcnow.return_value = current_time
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                mock_settings.TOKEN_EXPIRATION_BUFFER_SECONDS = 300
                
                # Token expires in 200 seconds, buffer is 300
                cache_service.set_token("token", 200)
                
                # Should be considered expired immediately (effective_lifetime = 0)
                assert cache_service._token == "token"
                assert cache_service._expiration_time == current_time
    
    def test_set_token_replaces_existing(self, cache_service):
        """Test that setting a new token replaces the existing one"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("old_token", 3600)
            assert cache_service._token == "old_token"
            
            cache_service.set_token("new_token", 7200)
            assert cache_service._token == "new_token"


class TestAuthTokenCacheServiceGetToken:
    """Test suite for getting tokens"""
    
    def test_get_token_when_empty(self, cache_service):
        """Test getting token when cache is empty"""
        token = cache_service.get_token()
        assert token is None
    
    def test_get_token_when_valid(self, cache_service):
        """Test getting token when it's valid"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("valid_token", 3600)
            
            # Token should be valid
            token = cache_service.get_token()
            assert token == "valid_token"
    
    def test_get_token_when_expired(self, cache_service):
        """Test getting token when it's expired"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            # Set token at 12:00
            set_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = set_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("expired_token", 3600)
            
            # Move time forward past expiration (3300 seconds + 1)
            get_time = set_time + timedelta(seconds=3301)
            mock_dt.utcnow.return_value = get_time
            
            # Token should be expired
            token = cache_service.get_token()
            assert token is None
    
    def test_get_token_near_expiration(self, cache_service):
        """Test getting token when it's near expiration but still valid"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            # Set token at 12:00
            set_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = set_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("near_expiry_token", 3600)
            
            # Move time forward but not past expiration (3299 seconds)
            get_time = set_time + timedelta(seconds=3299)
            mock_dt.utcnow.return_value = get_time
            
            # Token should still be valid
            token = cache_service.get_token()
            assert token == "near_expiry_token"


class TestAuthTokenCacheServiceIsExpired:
    """Test suite for checking expiration"""
    
    def test_is_expired_when_no_token(self, cache_service):
        """Test is_expired when no token is cached"""
        assert cache_service.is_expired() is True
    
    def test_is_expired_when_valid(self, cache_service):
        """Test is_expired when token is valid"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("valid_token", 3600)
            
            assert cache_service.is_expired() is False
    
    def test_is_expired_when_expired(self, cache_service):
        """Test is_expired when token is expired"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            # Set token at 12:00
            set_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = set_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("expired_token", 3600)
            
            # Move time forward past expiration
            check_time = set_time + timedelta(seconds=3301)
            mock_dt.utcnow.return_value = check_time
            
            assert cache_service.is_expired() is True
    
    def test_is_expired_exactly_at_expiration(self, cache_service):
        """Test is_expired exactly at expiration time"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            # Set token at 12:00
            set_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = set_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("token", 3600)
            
            # Move time to exactly expiration time (3300 seconds)
            check_time = set_time + timedelta(seconds=3300)
            mock_dt.utcnow.return_value = check_time
            
            # Should be expired (>= comparison)
            assert cache_service.is_expired() is True


class TestAuthTokenCacheServiceClearToken:
    """Test suite for clearing tokens"""
    
    def test_clear_token_when_exists(self, cache_service):
        """Test clearing token when one exists"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("token_to_clear", 3600)
            assert cache_service._token is not None
            
            cache_service.clear_token()
            
            assert cache_service._token is None
            assert cache_service._expiration_time is None
    
    def test_clear_token_when_empty(self, cache_service):
        """Test clearing token when cache is empty"""
        assert cache_service._token is None
        
        # Should not raise error
        cache_service.clear_token()
        
        assert cache_service._token is None
        assert cache_service._expiration_time is None


class TestAuthTokenCacheServiceExpirationInfo:
    """Test suite for getting expiration information"""
    
    def test_get_expiration_info_when_empty(self, cache_service):
        """Test getting expiration info when cache is empty"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            
            info = cache_service.get_expiration_info()
            
            assert info["has_token"] is False
            assert info["is_expired"] is True
            assert info["expiration_time"] is None
            assert info["seconds_until_expiration"] is None
            assert info["current_time"] == current_time.isoformat()
    
    def test_get_expiration_info_when_valid(self, cache_service):
        """Test getting expiration info when token is valid"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("valid_token", 3600)
            
            info = cache_service.get_expiration_info()
            
            assert info["has_token"] is True
            assert info["is_expired"] is False
            assert info["expiration_time"] is not None
            assert info["seconds_until_expiration"] == 3300  # 3600 - 300 buffer
    
    def test_get_expiration_info_when_expired(self, cache_service):
        """Test getting expiration info when token is expired"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            # Set token at 12:00
            set_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = set_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("expired_token", 3600)
            
            # Move time forward past expiration
            check_time = set_time + timedelta(seconds=3301)
            mock_dt.utcnow.return_value = check_time
            
            info = cache_service.get_expiration_info()
            
            assert info["has_token"] is True
            assert info["is_expired"] is True
            assert info["seconds_until_expiration"] is None


class TestAuthTokenCacheServiceAsync:
    """Test suite for async methods"""
    
    @pytest.mark.asyncio
    async def test_get_token_async(self, cache_service):
        """Test async get_token method"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("async_token", 3600)
            
            token = await cache_service.get_token_async()
            assert token == "async_token"
    
    @pytest.mark.asyncio
    async def test_set_token_async(self, cache_service):
        """Test async set_token method"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            await cache_service.set_token_async("async_token", 3600)
            
            assert cache_service._token == "async_token"
    
    @pytest.mark.asyncio
    async def test_clear_token_async(self, cache_service):
        """Test async clear_token method"""
        with patch('app.services.auth_token_cache_service.datetime') as mock_dt:
            current_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            cache_service.set_token("token", 3600)
            await cache_service.clear_token_async()
            
            assert cache_service._token is None

