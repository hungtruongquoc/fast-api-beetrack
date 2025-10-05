"""
Item schemas for request/response validation

This module defines Pydantic models for item data validation.
All models use Pydantic v2 features for automatic validation of:
- Data types
- Field constraints (min/max length, min/max value)
- Required vs optional fields
- Custom validation rules

Models:
    ItemBase: Base model with common fields
    ItemCreate: Model for creating new items (no ID)
    ItemUpdate: Model for updating items (all fields optional)
    Item: Complete item model with ID (for responses)
"""

from typing import Optional
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """
    Base item schema with common fields

    This is the base model that other item models inherit from.
    Contains all the common fields shared across create/update operations.

    Attributes:
        name (str): Item name, required, 1-100 characters
        description (Optional[str]): Item description, optional, max 500 characters
        price (float): Item price, required, must be greater than 0
        is_available (bool): Availability status, defaults to True

    Validation Rules:
        - name: Cannot be empty, max 100 characters
        - description: Optional, max 500 characters if provided
        - price: Must be a positive number (> 0)
        - is_available: Boolean value, defaults to True
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    is_available: bool = True


class ItemCreate(ItemBase):
    """
    Schema for creating an item

    Inherits all fields from ItemBase. Used for POST requests to create
    new items. The ID is not included as it will be auto-generated.

    Example:
        {
            "name": "New Item",
            "description": "Item description",
            "price": 29.99,
            "is_available": true
        }
    """
    pass


class ItemUpdate(BaseModel):
    """
    Schema for updating an item

    All fields are optional to support partial updates. Only provided
    fields will be updated, others remain unchanged.

    Attributes:
        name (Optional[str]): New item name, 1-100 characters if provided
        description (Optional[str]): New description, max 500 characters if provided
        price (Optional[float]): New price, must be > 0 if provided
        is_available (Optional[bool]): New availability status if provided

    Example (partial update):
        {
            "name": "Updated Name",
            "price": 39.99
        }
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None


class Item(ItemBase):
    """
    Schema for item with ID

    Complete item model including the auto-generated ID. Used for
    responses from GET, POST, and PUT endpoints.

    Attributes:
        id (int): Unique identifier, auto-generated
        (inherits all fields from ItemBase)

    Configuration:
        - from_attributes: Allows creation from ORM models
        - json_schema_extra: Provides example for OpenAPI docs

    Example:
        {
            "id": 1,
            "name": "Sample Item",
            "description": "This is a sample item",
            "price": 29.99,
            "is_available": true
        }
    """
    id: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Sample Item",
                "description": "This is a sample item",
                "price": 29.99,
                "is_available": True,
            }
        }
    }

