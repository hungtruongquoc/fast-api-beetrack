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

### Settings Dependency: Global Import vs Dependency Injection

**Current Implementation**: OAuthAuthenticationService uses global settings import

```python
from app.core.config import settings  # Module-level import

class OAuthAuthenticationService:
    def __init__(self, http_client, cache_service):
        self.settings = settings  # Uses global settings instance
```

**Trade-offs:**

**Pros (Current Approach):**
- ✅ Simple and straightforward
- ✅ Standard FastAPI pattern (common in FastAPI applications)
- ✅ Less boilerplate code
- ✅ Works well with FastAPI's dependency injection system
- ✅ Easy to understand and maintain

**Cons (Current Approach):**
- ❌ Tight coupling to project-specific settings
- ❌ Harder to test with different configurations (requires mocking)
- ❌ Not reusable across different projects without modification
- ❌ Implicit dependency (not visible in constructor signature)

**Alternative: Inject Settings as Constructor Parameter**

```python
from app.core.config import Settings  # Import class, not instance

class OAuthAuthenticationService:
    def __init__(
        self,
        http_client: HTTPClientService,
        cache_service: AuthTokenCacheService,
        settings: Settings  # Explicit dependency injection
    ):
        self.http_client = http_client
        self.cache_service = cache_service
        self.settings = settings
```

**Pros (Dependency Injection):**
- ✅ Loose coupling - no dependency on global state
- ✅ Easier to test - can inject mock settings directly
- ✅ Reusable - can use with different settings instances
- ✅ Explicit dependencies - clear what the service needs
- ✅ Better for unit testing without mocking modules

**Cons (Dependency Injection):**
- ❌ More verbose
- ❌ Requires updating factory function
- ❌ Requires updating all tests
- ❌ More boilerplate in dependency setup

**Decision for This Project**: Use global settings import

**Rationale**:
1. **FastAPI Convention**: Global settings are standard in FastAPI applications
2. **Project-Specific**: This service is designed specifically for this application
3. **Simplicity**: Reduces boilerplate and complexity
4. **Testing Works**: Mock-based testing is sufficient for our needs
5. **Pragmatic**: Balance between clean architecture and practical development

**When to Refactor to Dependency Injection**:
- When service needs to be extracted to a shared library
- When multiple settings configurations are needed in the same application
- When testing becomes difficult due to global state issues
- When the service needs to be reused across different projects

**Refactoring Checklist** (if needed in the future):
- [ ] Change constructor to accept `settings: Settings` parameter
- [ ] Update factory function `get_oauth_authentication_service()` to pass settings
- [ ] Update all test fixtures to inject settings
- [ ] Update any code that instantiates the service directly
- [ ] Consider making settings optional with default to maintain backward compatibility:
  ```python
  def __init__(
      self,
      http_client: HTTPClientService,
      cache_service: AuthTokenCacheService,
      settings: Optional[Settings] = None
  ):
      self.settings = settings or get_settings()
  ```

### Retry Mechanism for Token Requests

**Implementation**: OAuthAuthenticationService implements automatic retry logic for token requests to handle transient failures.

**Configuration:**
```python
class OAuthAuthenticationService:
    def __init__(self, http_client, cache_service):
        self._max_retry_attempts: int = 3  # Retry up to 3 times
```

**Retry Strategy:**

The `request_token()` method implements intelligent retry logic that distinguishes between transient and permanent errors:

**✅ WILL RETRY (Transient Errors):**
- **5xx Server Errors** (500, 502, 503, 504, etc.)
  - OAuth provider temporary unavailability
  - Server overload or maintenance
- **Network Errors**
  - Connection timeouts
  - Connection refused
  - DNS resolution failures
- **429 Rate Limit Errors**
  - Temporary rate limiting (should implement backoff in future)
- **Unexpected Errors**
  - Unknown exceptions that might be transient

**❌ WON'T RETRY (Permanent Errors):**
- **4xx Client Errors** (except 429)
  - 401 Unauthorized - Invalid credentials
  - 403 Forbidden - Insufficient permissions
  - 400 Bad Request - Invalid request format
- **Configuration Errors**
  - Missing OAUTH_CLIENT_ID
  - Missing OAUTH_CLIENT_SECRET
  - Missing OAUTH_TOKEN_URL
- **Invalid Response Format**
  - Missing `access_token` field
  - Missing `expires_in` field
  - Malformed JSON response

**Retry Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│  request_token() called                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Attempt 1            │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Success?             │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  YES: Return token    │◄─── 90% of requests (happy path)
         └───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  NO: Check error type │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Retryable?           │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  NO: Raise error      │◄─── 4xx, config, invalid response
         └───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  YES: Attempt 2       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Success?             │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  YES: Return token    │◄─── Recovered from transient error
         └───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  NO: Attempt 3 (final)│
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Success?             │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  YES: Return token    │◄─── Recovered after 3 attempts
         └───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  NO: Raise error      │◄─── Max retries exceeded
         │  (max_retries_exceeded)│
         └───────────────────────┘
```

**Logging:**

Each retry attempt is logged with structured data for observability:

```python
# Initial request
logger.info("Requesting new OAuth token",
            token_url="https://oauth.example.com/token",
            max_retry_attempts=3)

# Retry attempt
logger.info("Retrying token request",
            attempt=2,
            max_attempts=3)

# Retry warning
logger.warning("HTTP error, may retry",
               status_code=500,
               attempt=2,
               will_retry=True)

# Non-retryable error
logger.error("Non-retryable HTTP client error",
             status_code=401,
             attempt=1)

# Success after retry
logger.info("OAuth token acquired successfully",
            token_type="Bearer",
            expires_in=3600,
            attempt=2)
```

**Benefits:**

1. **Resilience**: Automatically handles transient failures without manual intervention
2. **Efficiency**: Doesn't waste time retrying permanent errors
3. **Observability**: Comprehensive logging for debugging and monitoring
4. **Configurability**: `_max_retry_attempts` can be adjusted if needed
5. **Smart Logic**: Distinguishes between retryable and non-retryable errors

**Future Enhancements:**

1. **Exponential Backoff**: Add delay between retries (e.g., 1s, 2s, 4s)
2. **Jitter**: Add randomization to prevent thundering herd
3. **Configurable Retry Count**: Make `_max_retry_attempts` configurable via settings
4. **Circuit Breaker**: Stop retrying if OAuth provider is consistently down
5. **Retry Metrics**: Track retry rates and success/failure ratios

### Future Refactoring: Extensible Retry Mechanism

**Current State**: The retry logic is embedded directly in the `request_token()` method with hardcoded retry behavior.

**Limitation**: 
- Retry strategy is not configurable beyond changing `_max_retry_attempts`
- Backoff strategy is not implemented (immediate retries)
- Cannot easily test different retry behaviors
- Violates Open/Closed Principle for retry strategy extension

**Proposed Refactoring**: Extract retry logic into a Strategy Pattern implementation for better extensibility and testability.

#### Recommended Approach: Retry Strategy Abstraction

**Abstract Base Class:**
```python
from abc import ABC, abstractmethod
from typing import Optional
import asyncio

class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""
    
    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if should retry based on attempt number and error type"""
        pass
    
    @abstractmethod
    async def get_delay(self, attempt: int) -> float:
        """Calculate delay before next retry attempt in seconds"""
        pass
    
    @property
    @abstractmethod
    def max_attempts(self) -> int:
        """Maximum number of retry attempts"""
        pass
```

**Implementation Options:**

1. **SimpleRetryStrategy** (Current behavior - for backward compatibility)
   ```python
   class SimpleRetryStrategy(RetryStrategy):
       def __init__(self, max_attempts: int = 3):
           self._max_attempts = max_attempts
       
       def should_retry(self, attempt: int, error: Exception) -> bool:
           if attempt >= self._max_attempts:
               return False
           return self._is_retryable_error(error)
       
       async def get_delay(self, attempt: int) -> float:
           return 0.0  # No delay (current behavior)
       
       @property
       def max_attempts(self) -> int:
           return self._max_attempts
       
       def _is_retryable_error(self, error: Exception) -> bool:
           # Existing retry logic from request_token()
           if isinstance(error, OAuthError):
               return error.error_code not in ("configuration_error", "invalid_response")
           if isinstance(error, HTTPClientError):
               return not (400 <= error.status_code < 500 and error.status_code != 429)
           return True
   ```

2. **ExponentialBackoffRetryStrategy** (Recommended for production)
   ```python
   class ExponentialBackoffRetryStrategy(RetryStrategy):
       def __init__(
           self, 
           max_attempts: int = 3, 
           base_delay: float = 1.0, 
           max_delay: float = 60.0,
           backoff_factor: float = 2.0,
           jitter: bool = True
       ):
           self._max_attempts = max_attempts
           self.base_delay = base_delay
           self.max_delay = max_delay
           self.backoff_factor = backoff_factor
           self.jitter = jitter
       
       def should_retry(self, attempt: int, error: Exception) -> bool:
           if attempt >= self._max_attempts:
               return False
           return self._is_retryable_error(error)
       
       async def get_delay(self, attempt: int) -> float:
           # Exponential backoff: base_delay * (backoff_factor ^ (attempt - 1))
           delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
           delay = min(delay, self.max_delay)
           
           # Add jitter to prevent thundering herd
           if self.jitter:
               import random
               delay *= (0.5 + random.random() * 0.5)  # 50%-100% of calculated delay
           
           return delay
       
       @property
       def max_attempts(self) -> int:
           return self._max_attempts
   ```

3. **LinearBackoffRetryStrategy** (Alternative approach)
   ```python
   class LinearBackoffRetryStrategy(RetryStrategy):
       def __init__(self, max_attempts: int = 3, delay_increment: float = 1.0):
           self._max_attempts = max_attempts
           self.delay_increment = delay_increment
       
       async def get_delay(self, attempt: int) -> float:
           return attempt * self.delay_increment  # 1s, 2s, 3s...
   ```

**Updated OAuthAuthenticationService:**
```python
class OAuthAuthenticationService:
    def __init__(
        self,
        http_client: HTTPClientService,
        cache_service: AuthTokenCacheService,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.http_client = http_client
        self.cache_service = cache_service
        self.settings = settings
        self._refresh_lock: asyncio.Lock = asyncio.Lock()
        
        # Use injected retry strategy or default
        self.retry_strategy = retry_strategy or SimpleRetryStrategy(max_attempts=3)
        
        self.logger = get_logger(__name__)

    async def request_token(self) -> str:
        """Request a new OAuth token with configurable retry strategy"""
        
        # Validate configuration first (no retries for config errors)
        self._validate_oauth_config()
        
        self.logger.info(
            "Requesting new OAuth token",
            token_url=self.settings.OAUTH_TOKEN_URL,
            max_retry_attempts=self.retry_strategy.max_attempts,
            retry_strategy=type(self.retry_strategy).__name__
        )

        last_error = None
        for attempt in range(1, self.retry_strategy.max_attempts + 1):
            try:
                if attempt > 1:
                    delay = await self.retry_strategy.get_delay(attempt)
                    self.logger.info(
                        "Retrying token request",
                        attempt=attempt,
                        max_attempts=self.retry_strategy.max_attempts,
                        delay_seconds=delay
                    )
                    if delay > 0:
                        await asyncio.sleep(delay)

                # Make the actual token request
                token = await self._make_token_request()
                
                self.logger.info(
                    "OAuth token acquired successfully",
                    attempt=attempt
                )
                
                return token

            except Exception as e:
                # Check if we should retry this error
                should_retry = self.retry_strategy.should_retry(attempt, e)
                
                self.logger.warning(
                    "Token request failed",
                    attempt=attempt,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    should_retry=should_retry and attempt < self.retry_strategy.max_attempts
                )
                
                if not should_retry:
                    # Non-retryable error, raise immediately
                    raise
                
                last_error = e
                
                if attempt >= self.retry_strategy.max_attempts:
                    # Max retries exceeded
                    break

        # All retries exhausted
        if last_error:
            raise last_error
        raise OAuthError(
            "Token request failed after all retry attempts",
            error_code="max_retries_exceeded"
        )
```

**Configuration-Based Strategy Selection:**
```python
# In config.py
OAUTH_RETRY_STRATEGY: str = "simple"  # Options: simple, exponential, linear
OAUTH_MAX_RETRY_ATTEMPTS: int = 3
OAUTH_RETRY_BASE_DELAY: float = 1.0
OAUTH_RETRY_MAX_DELAY: float = 60.0
OAUTH_RETRY_BACKOFF_FACTOR: float = 2.0
OAUTH_RETRY_JITTER: bool = True

# In factory function
def get_oauth_authentication_service() -> OAuthAuthenticationService:
    # Create retry strategy based on configuration
    if settings.OAUTH_RETRY_STRATEGY == "exponential":
        retry_strategy = ExponentialBackoffRetryStrategy(
            max_attempts=settings.OAUTH_MAX_RETRY_ATTEMPTS,
            base_delay=settings.OAUTH_RETRY_BASE_DELAY,
            max_delay=settings.OAUTH_RETRY_MAX_DELAY,
            backoff_factor=settings.OAUTH_RETRY_BACKOFF_FACTOR,
            jitter=settings.OAUTH_RETRY_JITTER
        )
    elif settings.OAUTH_RETRY_STRATEGY == "linear":
        retry_strategy = LinearBackoffRetryStrategy(
            max_attempts=settings.OAUTH_MAX_RETRY_ATTEMPTS,
            delay_increment=settings.OAUTH_RETRY_BASE_DELAY
        )
    else:
        retry_strategy = SimpleRetryStrategy(
            max_attempts=settings.OAUTH_MAX_RETRY_ATTEMPTS
        )

    http_client = get_http_client_service()
    cache_service = get_auth_token_cache_service()
    
    return OAuthAuthenticationService(
        http_client=http_client,
        cache_service=cache_service,
        retry_strategy=retry_strategy
    )
```

#### Benefits of Refactoring

1. **Open/Closed Principle**: Can add new retry strategies without modifying existing code
2. **Single Responsibility**: Retry logic is separated from token request logic
3. **Testability**: Retry strategies can be tested independently
4. **Configurability**: Different environments can use different retry strategies
5. **Extensibility**: Easy to add features like circuit breakers, rate limiting
6. **Maintainability**: Retry logic is centralized and reusable

#### When to Implement

**Keep Current Implementation When:**
- ✅ Simple immediate retries are sufficient
- ✅ OAuth provider has very reliable uptime
- ✅ Token requests are not rate-limited
- ✅ Development/testing environment

**Migrate to Strategy Pattern When:**
- 🚀 OAuth provider has intermittent issues requiring backoff
- 🚀 Token requests are rate-limited (need exponential backoff)
- 🚀 Production environment with high availability requirements
- 🚀 Need different retry behaviors for different environments
- 🚀 Want to implement circuit breaker patterns

#### Implementation Checklist

- [ ] Define `RetryStrategy` abstract base class
- [ ] Implement `SimpleRetryStrategy` (refactor current code)
- [ ] Implement `ExponentialBackoffRetryStrategy` with jitter
- [ ] Add retry strategy configuration settings
- [ ] Update `OAuthAuthenticationService` to accept retry strategy
- [ ] Extract `_make_token_request()` method for cleaner separation
- [ ] Update factory function to select strategy based on config
- [ ] Add comprehensive tests for each retry strategy
- [ ] Add integration tests with various failure scenarios
- [ ] Update documentation with retry strategy options
- [ ] Monitor retry metrics in production

#### Estimated Effort

- **Design & Planning**: 2-3 hours
- **Implementation**: 6-8 hours  
- **Testing**: 4-6 hours
- **Documentation**: 2-3 hours
- **Total**: 14-20 hours

**Example Scenarios:**

```python
# Scenario 1: Success on first attempt (no retries)
POST /oauth/token → 200 OK
✅ Token acquired (1 attempt)

# Scenario 2: Transient error, success on retry
POST /oauth/token → 500 Internal Server Error (attempt 1)
POST /oauth/token → 200 OK (attempt 2)
✅ Token acquired (2 attempts)

# Scenario 3: Permanent error (no retries)
POST /oauth/token → 401 Unauthorized
❌ Error raised immediately (1 attempt, no retries)

# Scenario 4: Max retries exceeded
POST /oauth/token → 503 Service Unavailable (attempt 1)
POST /oauth/token → 503 Service Unavailable (attempt 2)
POST /oauth/token → 503 Service Unavailable (attempt 3)
❌ Error raised: max retries exceeded
```

**Testing:**

The retry mechanism is thoroughly tested with 7 dedicated test cases:
- ✅ Success on first attempt (no retries)
- ✅ Retries on 500 errors (up to 3 times)
- ✅ Fails after max retries
- ✅ No retry on 401 errors (client error)
- ✅ No retry on invalid response format
- ✅ Retries on network errors
- ✅ Max retry attempts property is set correctly

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

#### Milestone 7: Implement token acquisition in OAuthAuthenticationService ✅

**Requirements:**
- ✅ Add method: `request_token()` - requests new token from OAuth provider
- ✅ Use HTTPClientService for POST request to OAUTH_TOKEN_URL
- ✅ Request body: `client_id`, `client_secret`, `grant_type=client_credentials`
- ✅ Parse response: `access_token`, `token_type`, `expires_in`
- ✅ Store token in AuthTokenCacheService
- ✅ Error handling for OAuth errors
- ✅ Structured logging
- ✅ **Retry logic with up to 3 attempts**

**Implementation:**
- Method signature: `async def request_token(self) -> str`
- Validates OAuth configuration before making request
- POST to `OAUTH_TOKEN_URL` with form-encoded body
- Extracts `access_token`, `expires_in`, `token_type` from response
- Stores token using `cache_service.set_token_async()`
- Custom `OAuthError` exception for all OAuth-related errors
- **Retry Logic:**
  - Property: `_max_retry_attempts = 3` (configurable internally)
  - Retries on: 5xx errors, network errors, unexpected errors
  - No retry on: 4xx errors (except 429), configuration errors, invalid response
  - Logs each retry attempt with attempt number
  - Raises last error after max retries exceeded

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

**Tests Added (18 tests):**
- ✅ Successful token acquisition
- ✅ Token stored in cache after acquisition
- ✅ Configuration validation (missing client_id, client_secret, token_url)
- ✅ Response validation (missing access_token, expires_in)
- ✅ HTTP error handling (401, 500)
- ✅ Network error handling
- ✅ Unexpected error handling
- ✅ Default token_type handling
- ✅ **Retry: Succeeds on first attempt (no retries)**
- ✅ **Retry: Retries on 500 errors (up to 3 times)**
- ✅ **Retry: Fails after max retries**
- ✅ **Retry: No retry on 401 errors (client error)**
- ✅ **Retry: No retry on invalid response format**
- ✅ **Retry: Retries on network errors**
- ✅ **Retry: Max retry attempts property is set correctly**

#### Milestone 8: Implement automatic token refresh in OAuthAuthenticationService ✅

**Requirements:**
- ✅ Update `get_valid_token_async()` to automatically refresh expired tokens
- ✅ Thread-safe refresh using asyncio.Lock (prevent concurrent refreshes)
- ✅ Refresh logic: if token expired/missing, call `request_token()`
- ✅ Structured logging for refresh events
- ✅ Handle refresh failures gracefully
- ✅ Double-check pattern to prevent redundant refreshes

**Implementation:**
- Updated `get_valid_token_async()` to return `str` instead of `Optional[str]` (always returns token or raises error)
- Implements double-check locking pattern:
  1. Check cache without lock (fast path)
  2. If no token, acquire lock
  3. Check cache again (another request may have refreshed)
  4. If still no token, call `request_token()`
  5. Return token
- Updated `get_valid_token()` documentation to clarify it does NOT auto-refresh (use async version for that)
- Comprehensive logging for refresh events (acquiring lock, requesting token, success/failure)

**Flow:**
```
get_valid_token_async() called
  ├─> Check cache (first check, no lock)
  ├─> If valid: return token immediately
  └─> If expired/missing:
      ├─> Log: "Token expired or missing, acquiring refresh lock"
      ├─> Acquire lock (_refresh_lock)
      ├─> Double-check cache (another request may have refreshed)
      ├─> If token now exists: return it
      ├─> Log: "Requesting new token"
      ├─> Call request_token()
      ├─> Token stored in cache (by request_token)
      ├─> Release lock (automatic with async context manager)
      ├─> Log: "Token refresh successful"
      └─> Return new token
```

**Tests Added (7 tests):**
- ✅ Returns cached token when valid (no refresh)
- ✅ Automatically refreshes when token expired/missing
- ✅ Double-check pattern prevents redundant refreshes
- ✅ Raises OAuthError when refresh fails
- ✅ Concurrent requests only trigger one refresh (thread-safe)
- ✅ Synchronous `get_valid_token()` does NOT auto-refresh
- ✅ Refresh events are logged properly

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

### 1. Token Storage Backend Extensibility

**Current State**: AuthTokenCacheService uses in-memory storage (instance variables)

**Limitation**:
- Not scalable for multi-instance deployments
- Tokens lost on application restart
- Each instance has its own token cache

**Future Enhancement**: Implement pluggable storage backends using Strategy Pattern

#### Recommended Approach: Storage Backend Abstraction

**Abstract Base Class:**
```python
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class TokenStorageBackend(ABC):
    """Abstract base class for token storage backends"""

    @abstractmethod
    def set(self, key: str, token: str, expiration: datetime) -> None:
        """Store token with expiration"""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[tuple[str, datetime]]:
        """Get token and expiration, returns None if not found"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete token"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if token exists"""
        pass
```

**Implementation Options:**

1. **InMemoryTokenStorage** (Current - for development/single instance)
   ```python
   class InMemoryTokenStorage(TokenStorageBackend):
       def __init__(self):
           self._storage: dict[str, tuple[str, datetime]] = {}
   ```

2. **RedisTokenStorage** (Recommended for production)
   ```python
   class RedisTokenStorage(TokenStorageBackend):
       def __init__(self, redis_client):
           self.redis = redis_client

       def set(self, key: str, token: str, expiration: datetime) -> None:
           data = {"token": token, "expiration": expiration.isoformat()}
           ttl = int((expiration - datetime.utcnow()).total_seconds())
           self.redis.setex(key, ttl, json.dumps(data))
   ```

3. **DatabaseTokenStorage** (For persistent storage)
   ```python
   class DatabaseTokenStorage(TokenStorageBackend):
       def __init__(self, db_session):
           self.db = db_session
   ```

**Updated AuthTokenCacheService:**
```python
class AuthTokenCacheService:
    def __init__(self, storage_backend: TokenStorageBackend):
        self.storage = storage_backend  # Injected backend
        self.logger = get_logger(__name__)
        self._token_key = "oauth_access_token"

    def set_token(self, token: str, expires_in: int) -> None:
        # Calculate expiration with buffer
        expiration_time = datetime.utcnow() + timedelta(seconds=effective_lifetime)

        # Use injected storage backend
        self.storage.set(self._token_key, token, expiration_time)
```

**Configuration-Based Backend Selection:**
```python
# In config.py
TOKEN_STORAGE_BACKEND: str = "memory"  # Options: memory, redis, database

# In factory function
def get_auth_token_cache_service() -> AuthTokenCacheService:
    if settings.TOKEN_STORAGE_BACKEND == "redis":
        backend = RedisTokenStorage(redis_client)
    elif settings.TOKEN_STORAGE_BACKEND == "database":
        backend = DatabaseTokenStorage(db_session)
    else:
        backend = InMemoryTokenStorage()

    return AuthTokenCacheService(backend)
```

#### Python Packages for Distributed Caching

1. **[aiocache](https://pypi.org/project/aiocache/)** (Recommended)
   - Async-first (perfect for FastAPI)
   - Multiple backends: memory, Redis, Memcached
   - Built-in serialization and TTL support
   - Easy backend switching via configuration
   ```python
   from aiocache import Cache
   cache = Cache(Cache.REDIS, endpoint="localhost", port=6379)
   ```

2. **[redis-py](https://pypi.org/project/redis/)**
   - Official Redis client
   - Mature and well-tested
   - Requires manual serialization
   ```python
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   ```

3. **[cachetools](https://pypi.org/project/cachetools/)**
   - In-memory only with TTL
   - Good for single-instance with automatic expiration
   - No external dependencies
   ```python
   from cachetools import TTLCache
   cache = TTLCache(maxsize=100, ttl=3600)
   ```

4. **[diskcache](https://pypi.org/project/diskcache/)**
   - Disk-based persistent cache
   - Survives restarts
   - Good for single-instance with persistence needs

#### When to Implement

**Keep In-Memory Storage When:**
- ✅ Single-instance deployment
- ✅ Development/testing environment
- ✅ MVP/prototype phase
- ✅ Tokens can be re-acquired quickly
- ✅ Restart downtime is acceptable

**Migrate to Distributed Storage When:**
- 🚀 Horizontal scaling (multiple instances)
- 🚀 High availability requirements
- 🚀 Token acquisition is expensive/rate-limited
- 🚀 Need token persistence across restarts
- 🚀 Production deployment with load balancing

#### Implementation Checklist

- [ ] Define `TokenStorageBackend` abstract base class
- [ ] Implement `InMemoryTokenStorage` (refactor current code)
- [ ] Implement `RedisTokenStorage` with redis-py or aiocache
- [ ] Add `TOKEN_STORAGE_BACKEND` configuration setting
- [ ] Update `AuthTokenCacheService` to accept storage backend
- [ ] Update factory function to select backend based on config
- [ ] Add tests for each storage backend implementation
- [ ] Update documentation with deployment considerations
- [ ] Add Redis connection configuration (host, port, password)
- [ ] Implement connection pooling for Redis backend
- [ ] Add health checks for storage backend connectivity
- [ ] Monitor cache hit/miss rates

#### Estimated Effort

- **Design & Planning**: 2 hours
- **Implementation**: 4-6 hours
- **Testing**: 3-4 hours
- **Documentation**: 1-2 hours
- **Total**: 10-14 hours

### 2. Additional Future Enhancements

1. Token refresh with refresh_token (if provided by OAuth provider)
2. Multiple OAuth provider support
3. Token revocation endpoint
4. OAuth scope management
5. Rate limiting for token requests
6. Metrics and monitoring for token operations
7. Token encryption at rest
8. Audit logging for token access

