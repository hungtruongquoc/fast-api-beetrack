"""
Main FastAPI application entry point

This module initializes and configures the FastAPI application with:
- CORS middleware for cross-origin requests
- API router registration for versioned endpoints
- Root and health check endpoints
- Auto-generated OpenAPI documentation

The application follows a layered architecture:
- API Layer: Handles HTTP requests/responses (app/api/)
- Service Layer: Contains business logic (app/services/)
- Schema Layer: Pydantic models for validation (app/schemas/)
- Core Layer: Configuration and utilities (app/core/)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.middleware.logging import LoggingMiddleware

# Configure logging on startup
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Bee - API Backend",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add logging middleware (should be first to capture all requests)
app.add_middleware(LoggingMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    Root endpoint

    Returns basic information about the API including version and
    documentation URL.

    Returns:
        dict: API information with message, version, and docs URL

    Example Response:
        {
            "message": "Welcome to FastAPI Bee",
            "version": "0.1.0",
            "docs": "/docs"
        }
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to FastAPI Bee",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Simple endpoint to verify the API is running and responsive.
    Used by monitoring systems and load balancers.

    Returns:
        dict: Health status indicator

    Example Response:
        {
            "status": "healthy"
        }
    """
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}

