# OAuth Authentication Token Management Specification

**Version:** 1.0  
**Date:** 2025-10-06  
**Status:** Planning

## Overview

This specification outlines the implementation of OAuth 2.0 Client Credentials flow for backend-to-backend authentication. The system will manage authentication tokens with automatic caching, expiration tracking, and refresh capabilities.

## Goals

1. Implement OAuth 2.0 Client Credentials flow for service-to-service authentication
2. Create reusable HTTP client service for external API calls
3. Implement intelligent token caching with automatic expiration management
4. Provide automatic token refresh before expiration
5. Ensure thread-safe token management for concurrent requests
6. Provide comprehensive testing at each layer

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│                  /api/v1/auth/status                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OAuthAuthenticationService                     │
│  - get_valid_token()                                        │
│  - request_token()                                          │
│  - automatic refresh logic                                  │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│ AuthTokenCacheService    │  │   HTTPClientService          │
│ - set_token()            │  │   - post()                   │
│ - get_token()            │  │   - get()                    │
│ - is_expired()           │  │   - put()                    │
│ - clear_token()          │  │   - delete()                 │
└──────────────────────────┘  └──────────────────────────────┘
```

### Service Responsibilities

#### 1. HTTPClientService
- **Purpose:** Singleton service for all external HTTP/REST API calls
- **Location:** `app/services/http_client_service.py`
- **Responsibilities:**
  - Wrap httpx.AsyncClient for async HTTP operations
  - Provide methods: GET, POST, PUT, DELETE
  - Handle HTTP errors and timeouts
  - Structured logging for all requests
  - Connection pooling and reuse

#### 2. AuthTokenCacheService
- **Purpose:** In-memory storage for authentication tokens with expiration tracking
- **Location:** `app/services/auth_token_cache_service.py`
- **Responsibilities:**
  - Store token with expiration timestamp
  - Check token validity based on expiration
  - Implement expiration buffer (refresh before actual expiration)
  - Thread-safe token access
  - Clear/invalidate tokens

#### 3. OAuthAuthenticationService
- **Purpose:** Main service for OAuth authentication token lifecycle management
- **Location:** `app/services/oauth_authentication_service.py`
- **Responsibilities:**
  - Request tokens from OAuth provider
  - Manage token lifecycle (acquire, cache, refresh)
  - Automatic token refresh on expiration
  - Thread-safe token refresh (prevent duplicate requests)
  - Integration with HTTPClientService and AuthTokenCacheService

## Implementation Plan

### Phase 1: Foundation - HTTP Client (Milestones 1-2)

#### Milestone 1: Create HTTPClientService for external API calls
**File:** `app/services/http_client_service.py`

**Requirements:**
- Singleton pattern implementation
- Async methods: `get()`, `post()`, `put()`, `delete()`
- Parameters: url, headers, body, timeout
- Return structured response with status code, body, headers
- Error handling for network errors, timeouts, HTTP errors
- Structured logging with request/response details
- Proper resource cleanup (async context manager)

**Interface:**
```python
class HTTPClientService:
    async def post(
        self, 
        url: str, 
        data: dict = None, 
        headers: dict = None, 
        timeout: float = 30.0
    ) -> dict:
        """Make POST request and return response"""
        pass
    
    async def get(self, url: str, headers: dict = None, timeout: float = 30.0) -> dict:
        """Make GET request and return response"""
        pass
```

#### Milestone 2: Write tests for HTTPClientService
**File:** `tests/services/test_http_client_service.py`

**Test Cases:**
- Successful POST/GET/PUT/DELETE requests
- Request with custom headers
- Request timeout handling
- Network error handling
- HTTP error responses (4xx, 5xx)
- Response parsing
- Singleton behavior verification

### Phase 2: Token Storage & Caching (Milestones 3-4)

#### Milestone 3: Create AuthTokenCacheService for token storage
**File:** `app/services/auth_token_cache_service.py`

**Requirements:**
- In-memory token storage (class variable)
- Store token with expiration timestamp
- Expiration buffer: 5 minutes (configurable)
- Thread-safe operations using asyncio.Lock
- Methods: `set_token()`, `get_token()`, `is_expired()`, `clear_token()`

**Interface:**
```python
class AuthTokenCacheService:
    def set_token(self, token: str, expires_in: int) -> None:
        """Store token with expiration time in seconds"""
        pass
    
    def get_token(self) -> Optional[str]:
        """Get token if exists and not expired, else None"""
        pass
    
    def is_expired(self) -> bool:
        """Check if token is expired or near expiration (buffer)"""
        pass
    
    def clear_token(self) -> None:
        """Clear stored token"""
        pass
```

**Expiration Logic:**
- Store: `expiration_time = current_time + expires_in - buffer`
- Check: `is_expired = current_time >= expiration_time`

#### Milestone 4: Write tests for AuthTokenCacheService
**File:** `tests/services/test_auth_token_cache_service.py`

**Test Cases:**
- Set and retrieve valid token
- Token expiration detection
- Buffer logic (token expires before actual expiration)
- Get expired token returns None
- Clear token functionality
- No token stored scenario
- Invalid expiration times (negative, zero)
- Mock datetime for time-based tests

### Phase 3: OAuth Authentication Service - Token Management (Milestones 5-6)

#### Milestone 5: Create OAuthAuthenticationService with token management
**File:** `app/services/oauth_authentication_service.py`

**Requirements:**
- Singleton pattern
- Dependency injection: AuthTokenCacheService, Settings
- Method: `get_valid_token()` - returns cached token if valid, else None
- Method: `clear_token()` - clears cached token
- Structured logging for token operations

**Interface:**
```python
class OAuthAuthenticationService:
    def __init__(
        self, 
        cache_service: AuthTokenCacheService,
        settings: Settings
    ):
        pass
    
    async def get_valid_token(self) -> Optional[str]:
        """Get valid token from cache, return None if expired/missing"""
        pass
    
    def clear_token(self) -> None:
        """Clear cached token"""
        pass
```

#### Milestone 6: Write tests for OAuthAuthenticationService token management
**File:** `tests/services/test_oauth_authentication_service.py`

**Test Cases:**
- Get valid cached token
- Get expired cached token returns None
- Get token when cache is empty returns None
- Clear token functionality
- Verify cache service interactions (mocked)

### Phase 4: Token Acquisition & Refresh (Milestones 7-10)

#### Milestone 7: Implement token acquisition in OAuthAuthenticationService

**Requirements:**
- Add method: `request_token()` - requests new token from OAuth provider
- Use HTTPClientService for POST request to OAUTH_TOKEN_URL
- Request body: `client_id`, `client_secret`, `grant_type=client_credentials`
- Parse response: `access_token`, `token_type`, `expires_in`
- Store token in AuthTokenCacheService
- Error handling for OAuth errors
- Structured logging

**OAuth Request:**
```python
POST {OAUTH_TOKEN_URL}
Content-Type: application/x-www-form-urlencoded

client_id={OAUTH_CLIENT_ID}
&client_secret={OAUTH_CLIENT_SECRET}
&grant_type=client_credentials
```

**OAuth Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Milestone 8: Implement automatic token refresh in OAuthAuthenticationService

**Requirements:**
- Update `get_valid_token()` to automatically refresh expired tokens
- Thread-safe refresh using asyncio.Lock (prevent concurrent refreshes)
- Refresh logic: if token expired/missing, call `request_token()`
- Structured logging for refresh events
- Handle refresh failures gracefully

**Flow:**
```
get_valid_token() called
  ├─> Check cache
  ├─> If valid: return token
  └─> If expired/missing:
      ├─> Acquire lock
      ├─> Double-check (another request may have refreshed)
      ├─> Call request_token()
      ├─> Store in cache
      ├─> Release lock
      └─> Return new token
```

#### Milestone 9: Write tests for OAuthAuthenticationService token acquisition

**Test Cases:**
- Successful token acquisition
- Token stored in cache after acquisition
- OAuth provider returns 401 (invalid credentials)
- OAuth provider returns 500 (server error)
- Network error during token request
- Invalid response format (missing fields)
- Timeout during token request

#### Milestone 10: Write tests for automatic token refresh

**Test Cases:**
- Expired token triggers automatic refresh
- Near-expiration token triggers refresh (buffer logic)
- Concurrent requests don't cause multiple refreshes (lock test)
- Refresh failure handling
- Token refresh success updates cache
- Mock time and HTTP calls for deterministic tests

### Phase 5: Integration & Testing (Milestones 11-12)

#### Milestone 11: Create authentication status endpoint for testing
**File:** `app/api/v1/endpoints/auth.py`

**Requirements:**
- Endpoint: `GET /api/v1/auth/status`
- Returns: token existence, expiration time, time until expiration
- Does NOT return actual token value (security)
- Use OAuthAuthenticationService dependency injection

**Response:**
```json
{
  "has_token": true,
  "expires_at": "2025-10-06T15:30:00Z",
  "expires_in_seconds": 3245,
  "is_valid": true
}
```

#### Milestone 12: OAuth authentication integration testing and documentation

**Requirements:**
- End-to-end integration tests
- Test complete flow: startup → token request → caching → reuse → expiration → refresh
- Test with mock OAuth server (or actual provider)
- Update README.md with:
  - OAuth configuration instructions
  - Environment variable setup
  - Usage examples for OAuthAuthenticationService
  - Architecture diagram
  - Troubleshooting guide

## Configuration

### Environment Variables

```env
# OAuth Configuration (Backend-to-Backend)
OAUTH_CLIENT_ID=your-client-id-here
OAUTH_CLIENT_SECRET=your-client-secret-here
OAUTH_TOKEN_URL=https://oauth-provider.com/oauth/token
```

### Settings Class

```python
class Settings(BaseSettings):
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""
    OAUTH_TOKEN_URL: str = ""
```

## Security Considerations

1. **Never log tokens** - Tokens should never appear in logs
2. **Secure storage** - Tokens stored in memory only, not persisted
3. **Environment variables** - Credentials loaded from .env file
4. **HTTPS only** - All OAuth requests must use HTTPS
5. **Token exposure** - API endpoints should never return actual token values

## Testing Strategy

1. **Unit Tests** - Test each service in isolation with mocked dependencies
2. **Integration Tests** - Test service interactions with mocked HTTP
3. **End-to-End Tests** - Test complete flow with mock OAuth server
4. **Time-based Tests** - Mock datetime for expiration scenarios
5. **Concurrency Tests** - Test thread-safe token refresh

## Success Criteria

- [ ] All services implemented with singleton pattern
- [ ] Token caching with expiration tracking working
- [ ] Automatic token refresh on expiration
- [ ] Thread-safe token management
- [ ] 100% test coverage for all services
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Integration tests passing

## Future Enhancements

1. Token refresh with refresh_token (if provided by OAuth provider)
2. Multiple OAuth provider support
3. Token persistence (Redis/database)
4. Token revocation endpoint
5. OAuth scope management
6. Rate limiting for token requests
7. Metrics and monitoring for token operations

