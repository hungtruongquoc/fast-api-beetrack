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

## Design Decisions

### Why Three Separate Services?

**Decision**: Split functionality into HTTPClientService, AuthTokenCacheService, and OAuthAuthenticationService rather than a single monolithic service.

**Rationale**:
1. **Single Responsibility Principle**: Each service has one clear purpose
   - HTTPClientService: Make HTTP requests
   - AuthTokenCacheService: Store and retrieve tokens
   - OAuthAuthenticationService: Orchestrate OAuth flow

2. **Reusability**: HTTPClientService can be used for any HTTP calls, not just OAuth
   - Weather API calls
   - Payment gateway integrations
   - Any third-party API integration

3. **Testability**: Each service can be tested in isolation with mocked dependencies
   - Test HTTP client without needing OAuth logic
   - Test token cache without needing HTTP calls
   - Test OAuth service with mocked HTTP and cache

4. **Flexibility**: Different services can compose these building blocks differently
   - Some services need OAuth + HTTP
   - Some services only need HTTP
   - Some services only need token status

5. **Maintainability**: Changes to HTTP logic don't affect token caching and vice versa

### Why Not Inject Token Services into HTTPClientService?

**Decision**: HTTPClientService remains a generic HTTP utility without authentication knowledge.

**Rationale**:
1. **Generic Utility**: HTTPClientService should work for any HTTP call, authenticated or not
2. **Separation of Concerns**: HTTP transport layer shouldn't know about authentication mechanisms
3. **Multiple Auth Types**: Future authentication methods (API keys, JWT, etc.) can use the same HTTP client
4. **Explicit Control**: Calling code explicitly decides when and how to add authentication

**Alternative Considered**: Auto-inject tokens into all requests
- **Rejected because**: Not all HTTP calls need authentication; would create tight coupling

### Why Singleton Pattern?

**Decision**: Use singleton pattern for all three services.

**Rationale**:
1. **Shared State**: Token cache must be shared across the application
2. **Resource Efficiency**: Single HTTP client connection pool for all requests
3. **Consistency**: All parts of the application see the same token state
4. **FastAPI Compatibility**: Works well with FastAPI's dependency injection

### Why Configurable Expiration Buffer?

**Decision**: Make token expiration buffer configurable via environment variable.

**Rationale**:
1. **Proactive Refresh**: Prevents using tokens that are about to expire
2. **Network Latency**: Accounts for time taken to make API calls
3. **Environment-Specific**: Different environments may need different buffers
4. **Safety Margin**: Reduces risk of authentication failures mid-request

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

### Dependency Injection Strategy

**Key Principle: The calling service/application decides how to orchestrate these services based on its needs.**

#### Service Roles:

1. **HTTPClientService** - Generic HTTP utility (no authentication knowledge)
   - Purpose: Make HTTP requests to any external API
   - Dependencies: None (standalone utility)
   - Inject when: You need to make HTTP calls (authenticated or not)

2. **AuthTokenCacheService** - Token storage (internal use only)
   - Purpose: Store and retrieve tokens with expiration tracking
   - Dependencies: None (standalone storage)
   - Inject when: Typically NOT injected directly; used internally by OAuthAuthenticationService

3. **OAuthAuthenticationService** - Token lifecycle orchestrator
   - Purpose: Manage OAuth token acquisition, caching, and refresh
   - Dependencies: HTTPClientService + AuthTokenCacheService + Settings
   - Inject when: You need OAuth tokens for authenticated API calls

#### Orchestration Patterns:

**Pattern 1: Unauthenticated HTTP Calls**
```python
class WeatherService:
    def __init__(self, http_client: HTTPClientService):
        self.http_client = http_client

    async def get_weather(self, city: str):
        # Direct HTTP call - no authentication needed
        response = await self.http_client.get(
            f"https://api.weather.com/data?city={city}"
        )
        return response["body"]
```

**Pattern 2: Authenticated HTTP Calls (OAuth)**
```python
class BeeTrackAPIService:
    def __init__(
        self,
        http_client: HTTPClientService,
        oauth_service: OAuthAuthenticationService
    ):
        self.http_client = http_client
        self.oauth_service = oauth_service

    async def get_delivery_data(self, delivery_id: str):
        # Step 1: Get valid OAuth token
        token = await self.oauth_service.get_valid_token()

        # Step 2: Use token in authenticated HTTP call
        response = await self.http_client.get(
            f"https://api.beetrack.com/deliveries/{delivery_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response["body"]
```

**Pattern 3: Token Management Only**
```python
class AuthManagementService:
    def __init__(self, oauth_service: OAuthAuthenticationService):
        self.oauth_service = oauth_service

    async def get_auth_status(self):
        # Only need token status, no HTTP calls
        token = await self.oauth_service.get_valid_token()
        return {"authenticated": token is not None}
```

#### FastAPI Endpoint Examples:

```python
# Endpoint with authenticated external API call
@router.get("/deliveries/{delivery_id}")
async def get_delivery(
    delivery_id: str,
    http_client: HTTPClientService = Depends(get_http_client_service),
    oauth_service: OAuthAuthenticationService = Depends(get_oauth_authentication_service)
):
    token = await oauth_service.get_valid_token()
    response = await http_client.get(
        f"https://api.beetrack.com/deliveries/{delivery_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response["body"]

# Endpoint for auth status only
@router.get("/auth/status")
async def auth_status(
    oauth_service: OAuthAuthenticationService = Depends(get_oauth_authentication_service)
):
    cache_service = oauth_service.cache_service
    return cache_service.get_expiration_info()
```

#### Design Benefits:

1. **Separation of Concerns**: Each service has a single, well-defined responsibility
2. **Flexibility**: Services can be composed differently for different use cases
3. **Testability**: Each service can be tested independently with mocked dependencies
4. **Reusability**: HTTPClientService can be used for any HTTP calls, not just OAuth
5. **No Tight Coupling**: Services don't know about each other's internal implementation
6. **Clear Dependencies**: Dependency injection makes relationships explicit

### OAuthAuthenticationService Internal Structure

The OAuthAuthenticationService acts as the orchestrator that brings together HTTPClientService and AuthTokenCacheService:

```python
class OAuthAuthenticationService:
    def __init__(
        self,
        http_client: HTTPClientService,
        cache_service: AuthTokenCacheService,
        settings: Settings
    ):
        self.http_client = http_client        # For making OAuth token requests
        self.cache_service = cache_service    # For storing/retrieving tokens
        self.settings = settings              # For OAuth configuration

    async def get_valid_token(self) -> Optional[str]:
        # Check cache first
        token = self.cache_service.get_token()
        if token:
            return token

        # Token expired/missing, request new one
        return await self.request_token()

    async def request_token(self) -> str:
        # Use HTTPClientService to make OAuth request
        response = await self.http_client.post(
            self.settings.OAUTH_TOKEN_URL,
            data={
                "client_id": self.settings.OAUTH_CLIENT_ID,
                "client_secret": self.settings.OAUTH_CLIENT_SECRET,
                "grant_type": "client_credentials"
            }
        )

        # Store in cache using AuthTokenCacheService
        token = response["body"]["access_token"]
        expires_in = response["body"]["expires_in"]
        self.cache_service.set_token(token, expires_in)

        return token
```

**Why this design?**
- OAuthAuthenticationService doesn't make HTTP calls directly - it delegates to HTTPClientService
- OAuthAuthenticationService doesn't manage token storage - it delegates to AuthTokenCacheService
- This keeps each service focused and allows them to be reused independently

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

