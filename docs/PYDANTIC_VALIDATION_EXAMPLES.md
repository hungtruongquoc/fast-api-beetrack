# Pydantic Validation in FastAPI Endpoints

This document shows how Pydantic is used for validation in FastAPI endpoints and provides advanced examples.

## 📋 Table of Contents

1. [Basic Validation (Already Implemented)](#basic-validation)
2. [Query Parameters Validation](#query-parameters-validation)
3. [Path Parameters Validation](#path-parameters-validation)
4. [Request Body Validation](#request-body-validation)
5. [Response Validation](#response-validation)
6. [Advanced Validation Examples](#advanced-validation-examples)

## Basic Validation (Already Implemented)

Your current endpoints already use Pydantic validation:

```python
from app.schemas.item import Item, ItemCreate, ItemUpdate

@router.post("/", response_model=Item, status_code=201)
async def create_item(
    item: ItemCreate,  # ← Pydantic validates request body
    item_service: ItemService = Depends(get_item_service),
):
    return item_service.create_item(item)
```

**What happens automatically:**
- ✅ Type validation (string, int, float, bool)
- ✅ Required fields checking
- ✅ Field constraints (min/max length, min/max value)
- ✅ Custom validators
- ✅ Automatic 422 error response for invalid data

## Query Parameters Validation

### Example 1: Simple Query Parameters

```python
from typing import Optional
from fastapi import Query

@router.get("/search/")
async def search_items(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    item_service: ItemService = Depends(get_item_service),
):
    """Search items with pagination"""
    # Implementation here
    pass
```

### Example 2: Query Parameters with Pydantic Model

```python
from pydantic import BaseModel, Field

class ItemSearchParams(BaseModel):
    q: Optional[str] = Field(None, min_length=1, max_length=100)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    is_available: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)

@router.get("/search/")
async def search_items(
    params: ItemSearchParams = Depends(),
    item_service: ItemService = Depends(get_item_service),
):
    """Search items with complex filters"""
    # Implementation here
    pass
```

## Path Parameters Validation

### Example: Validated Path Parameters

```python
from fastapi import Path

@router.get("/{item_id}")
async def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to get"),
    item_service: ItemService = Depends(get_item_service),
):
    """Get item with validated ID"""
    item = item_service.get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

## Request Body Validation

### Example 1: Multiple Body Parameters

```python
from pydantic import BaseModel

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

class UpdateMetadata(BaseModel):
    reason: str
    updated_by: str

@router.put("/{item_id}")
async def update_item_with_metadata(
    item_id: int,
    item: ItemUpdate,
    metadata: UpdateMetadata,
    item_service: ItemService = Depends(get_item_service),
):
    """Update item with metadata"""
    # Implementation here
    pass
```

### Example 2: Nested Models

```python
from typing import List

class Tag(BaseModel):
    name: str
    color: str

class ItemWithTags(BaseModel):
    name: str
    price: float
    tags: List[Tag]

@router.post("/with-tags/")
async def create_item_with_tags(
    item: ItemWithTags,
    item_service: ItemService = Depends(get_item_service),
):
    """Create item with nested tags"""
    # Implementation here
    pass
```

## Response Validation

### Example: Response Model with Validation

```python
from typing import List
from pydantic import BaseModel

class ItemListResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    page_size: int

@router.get("/paginated/", response_model=ItemListResponse)
async def get_items_paginated(
    skip: int = 0,
    limit: int = 10,
    item_service: ItemService = Depends(get_item_service),
):
    """Get paginated items"""
    items = item_service.get_all_items()[skip:skip+limit]
    return {
        "items": items,
        "total": item_service.get_items_count(),
        "page": skip // limit + 1,
        "page_size": limit,
    }
```

## Advanced Validation Examples

### Example 1: Custom Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class ItemCreate(BaseModel):
    name: str
    price: float
    discount_price: Optional[float] = None

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @model_validator(mode='after')
    def check_discount_price(self):
        if self.discount_price is not None:
            if self.discount_price >= self.price:
                raise ValueError('Discount price must be less than regular price')
        return self
```

### Example 2: Field Constraints

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0, le=1000000, description="Price in USD")
    quantity: int = Field(0, ge=0, description="Available quantity")
    sku: str = Field(..., pattern=r'^[A-Z]{3}-\d{6}$', description="SKU format: ABC-123456")
    website: Optional[HttpUrl] = None
    contact_email: Optional[EmailStr] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Example 3: Enum Validation

```python
from enum import Enum
from pydantic import BaseModel

class ItemCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"

class ItemStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ItemCreate(BaseModel):
    name: str
    price: float
    category: ItemCategory
    status: ItemStatus = ItemStatus.DRAFT
```

### Example 4: Conditional Validation

```python
from typing import Optional, Literal
from pydantic import BaseModel, model_validator

class ItemCreate(BaseModel):
    name: str
    price: float
    item_type: Literal["physical", "digital"]
    weight: Optional[float] = None
    download_url: Optional[str] = None

    @model_validator(mode='after')
    def validate_item_type_fields(self):
        if self.item_type == "physical" and self.weight is None:
            raise ValueError("Physical items must have a weight")
        if self.item_type == "digital" and self.download_url is None:
            raise ValueError("Digital items must have a download URL")
        return self
```

### Example 5: List Validation

```python
from typing import List
from pydantic import BaseModel, Field

class BulkItemCreate(BaseModel):
    items: List[ItemCreate] = Field(..., min_length=1, max_length=100)

@router.post("/bulk/")
async def create_items_bulk(
    bulk_data: BulkItemCreate,
    item_service: ItemService = Depends(get_item_service),
):
    """Create multiple items at once"""
    created_items = []
    for item_data in bulk_data.items:
        created_items.append(item_service.create_item(item_data))
    return created_items
```

### Example 6: Dependency Validation

```python
from fastapi import Depends, HTTPException

class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)

    @model_validator(mode='after')
    def validate_pagination(self):
        if self.skip > 10000:
            raise ValueError("Skip cannot exceed 10000")
        return self

def get_pagination_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

@router.get("/")
async def get_items(
    pagination: PaginationParams = Depends(get_pagination_params),
    item_service: ItemService = Depends(get_item_service),
):
    """Get items with validated pagination"""
    items = item_service.get_all_items()
    return items[pagination.skip:pagination.skip + pagination.limit]
```

## Error Handling

FastAPI automatically returns 422 Unprocessable Entity with detailed error messages:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

## Testing Validation

```python
def test_create_item_invalid_price(client):
    """Test that negative price is rejected"""
    response = client.post("/api/v1/items/", json={
        "name": "Test Item",
        "price": -10.0  # Invalid!
    })
    assert response.status_code == 422
    assert "price" in str(response.json())
```

## Best Practices

1. ✅ **Use Field() for constraints** - More readable than type hints alone
2. ✅ **Add descriptions** - They appear in OpenAPI docs
3. ✅ **Use Enums** - For fixed sets of values
4. ✅ **Custom validators** - For complex business logic
5. ✅ **Response models** - Validate output too
6. ✅ **Reuse models** - DRY principle
7. ✅ **Test validation** - Write tests for edge cases

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)

