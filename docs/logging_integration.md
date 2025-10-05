# Logging Integration Plan

## Overview
This document outlines the plan to integrate structured logging using `structlog` into the FastAPI BeeTrack application.

## Phase 1: Setup & Configuration

### 1. Add structlog dependency
- Add `structlog` to pyproject.toml dependencies
- Install with Poetry

### 2. Create logging configuration
- Create `app/core/logging.py` with:
  - JSON formatting for production
  - Human-readable formatting for development
  - Log level configuration
  - Processor chain setup

### 3. Initialize structured logging
- Initialize logging in `app/main.py` on startup
- Configure based on environment settings

## Phase 2: Request Context

### 4. Add logging middleware
- Create middleware to inject request context:
  - Unique request IDs
  - HTTP method and path
  - User information (if available)
  - Response time and status

### 5. Update services to use structured logger
- Replace standard logging with structlog in services
- Add consistent context binding
- Use structured log events

## Phase 3: Environment & Testing

### 6. Environment-specific logging configuration
- Production: JSON format for log aggregation
- Development: Human-readable format for debugging
- Configure log levels per environment

### 7. Write tests for logging configuration
- Test logging setup and configuration
- Test middleware request context injection
- Verify log output formats

### 8. Update documentation
- Add logging usage examples to CLAUDE.md
- Document best practices for structured logging
- Include configuration options

## Expected Benefits

- **Request Tracing**: Unique IDs for tracking requests across services
- **Structured Data**: JSON logs perfect for analysis and monitoring
- **Development Experience**: Human-readable logs during development
- **Consistent Logging**: Unified logging approach across all services
- **Observability**: Easy integration with log aggregation tools (ELK, Datadog, etc.)

## Implementation Notes

- Use singleton pattern for logger configuration
- Leverage FastAPI's dependency injection for logger instances
- Ensure backwards compatibility with existing logging
- Consider performance impact of structured logging overhead

## Usage Examples

### Router/Endpoint Usage

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
import structlog

from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.services.item_service import ItemService, get_item_service

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.get("/", response_model=List[Item])
async def get_items(
    available_only: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    item_service: ItemService = Depends(get_item_service),
):
    logger.info(
        "Fetching items with filters",
        available_only=available_only,
        min_price=min_price,
        max_price=max_price,
        search=search
    )
    
    items = item_service.get_all_items()
    initial_count = len(items)
    
    # Apply filters with logging
    if available_only is not None and available_only:
        items = item_service.get_available_items()
        logger.debug("Applied availability filter", remaining_items=len(items))
    
    if min_price is not None and max_price is not None:
        items = item_service.get_items_by_price_range(min_price, max_price)
        logger.debug("Applied price range filter", remaining_items=len(items))
    elif min_price is not None:
        items = [item for item in items if item.price >= min_price]
        logger.debug("Applied minimum price filter", remaining_items=len(items))
    elif max_price is not None:
        items = [item for item in items if item.price <= max_price]
        logger.debug("Applied maximum price filter", remaining_items=len(items))
    
    if search is not None:
        items = item_service.search_items_by_name(search)
        logger.debug("Applied search filter", remaining_items=len(items))
    
    logger.info(
        "Items fetched successfully",
        initial_count=initial_count,
        filtered_count=len(items),
        filters_applied=sum([
            available_only is not None,
            min_price is not None,
            max_price is not None,
            search is not None
        ])
    )
    
    return items

@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: int = Path(..., gt=0),
    item_service: ItemService = Depends(get_item_service),
):
    logger.info("Fetching item by ID", item_id=item_id)
    
    item = item_service.get_item_by_id(item_id)
    if item is None:
        logger.warning("Item not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")
    
    logger.info("Item fetched successfully", item_id=item_id, item_name=item.name)
    return item

@router.post("/", response_model=Item, status_code=201)
async def create_item(
    item: ItemCreate,
    item_service: ItemService = Depends(get_item_service),
):
    logger.info("Creating new item", item_name=item.name, item_price=item.price)
    
    created_item = item_service.create_item(item)
    
    logger.info(
        "Item created successfully",
        item_id=created_item.id,
        item_name=created_item.name,
        item_price=created_item.price
    )
    
    return created_item

@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int = Path(..., gt=0),
    item_service: ItemService = Depends(get_item_service),
):
    logger.info("Deleting item", item_id=item_id)
    
    success = item_service.delete_item(item_id)
    if not success:
        logger.warning("Item deletion failed - item not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")
    
    logger.info("Item deleted successfully", item_id=item_id)
```

### Logging Best Practices

#### 1. Context Binding
- Include relevant parameters in log events using key-value pairs
- Use meaningful field names that are consistent across the application

#### 2. Log Levels
- **info**: Business operations, API calls, successful operations
- **debug**: Detailed flow information, filter applications, intermediate steps
- **warning**: Recoverable errors, not-found scenarios, invalid operations
- **error**: Unrecoverable errors, exceptions, system failures

#### 3. Structured Data
- Use key-value pairs instead of string formatting
- Keep field names consistent (e.g., always use `item_id`, not `id` or `itemId`)
- Include metrics like counts, durations, and status codes

#### 4. Operation Tracking
- Log start of operations with input parameters
- Log success/failure with relevant outcome data
- Include timing information for performance monitoring